"""Integration checks for real cross-account feature content and privacy."""
from test_multiuser import env,item


def test_passport_perspectives_wormhole_and_permission(env):
    a,b,guest=env
    e1=a.post('/api/exhibits',json=item(title='花园里的旧钟',category='科学',tags='时间,机械')).json()['id']
    e2=b.post('/api/exhibits',json=item(title='老式怀表',category='科学',tags='时间,机械')).json()['id']
    private=a.post('/api/exhibits',json=item(title='私人日记',visibility='private')).json()['id']
    assert guest.get(f'/api/features/exhibits/{private}/passport').status_code==404
    assert guest.get(f'/api/features/wormhole/{private}').status_code==404
    data={'origin':'校园观察','attribution':'Alice','license':'作者保留权利','note':'第一版现场记录'}
    assert b.put(f'/api/features/exhibits/{e1}/passport',json=data).status_code==403
    assert a.put(f'/api/features/exhibits/{e1}/passport',json=data).status_code==200
    passport=guest.get(f'/api/features/exhibits/{e1}/passport').json()
    assert passport['passport']['origin']=='校园观察'
    assert passport['history'][0]['editor']=='Alice'
    payload={'angle':'机械爱好者','text':'这块怀表与齿轮设计很有意思'}
    assert b.post(f'/api/features/exhibits/{e1}/perspectives',json=payload).status_code==200
    assert guest.get(f'/api/features/exhibits/{e1}/perspectives').json()[0]['author']=='Bob'
    link={'destination_id':e2,'relation':'历史演化','reason':'两件物品都涉及机械计时'}
    assert b.post(f'/api/features/wormhole/{e1}/links',json=link).status_code==403
    assert a.post(f'/api/features/wormhole/{e1}/links',json=link).status_code==200
    assert guest.get(f'/api/features/wormhole/{e1}').json()['links'][0]['destination_id']==e2
    assert a.post(f'/api/features/wormhole/{e1}/links',json={**link,'destination_id':private}).status_code==404


def test_cases_evidence_history_events_and_chains(env):
    a,b,guest=env
    e1=a.post('/api/exhibits',json=item(title='奇怪的老仪器')).json()['id']
    e2=b.post('/api/exhibits',json=item(title='古老零件')).json()['id']
    assert b.post('/api/features/cases',json={'exhibit_id':e1,'question':'这件仪器到底有什么用途呢？'}).status_code==403
    case=a.post('/api/features/cases',json={'exhibit_id':e1,'question':'这件仪器到底有什么用途呢？'}).json()['id']
    assert b.post(f'/api/features/cases/{case}/clues',json={'kind':'hypothesis','body':'可能是角度测量工具'}).status_code==200
    assert a.post(f'/api/features/cases/{case}/state',json={'state':'待核验','reason':'需要铭牌证据'}).status_code==200
    assert b.post(f'/api/features/cases/{case}/state',json={'state':'已解决','reason':'我猜对了'}).status_code==403
    result=guest.get(f'/api/features/cases/{case}').json()
    assert result['state']=='待核验' and result['clues'][0]['kind']=='hypothesis' and len(result['history'])==2
    payload={'happened_at':'1996-08-23','description':'家人在旧仓库发现这件东西'}
    assert b.post(f'/api/features/exhibits/{e1}/events',json=payload).status_code==200
    assert guest.get(f'/api/features/exhibits/{e1}/events').json()[0]['author']=='Bob'
    chain=a.post('/api/features/chains',json={'title':'旧物奇遇','exhibit_id':e1,'reason':'从一件老仪器说起'}).json()['id']
    assert a.post(f'/api/features/chains/{chain}/steps',json={'exhibit_id':e1,'reason':'我再接一次'}).status_code==409
    assert b.post(f'/api/features/chains/{chain}/steps',json={'exhibit_id':e2,'reason':'它与这件零件有关'}).status_code==200
    assert len(guest.get(f'/api/features/chains/{chain}').json()['steps'])==2


def test_interactive_story_city_and_realtime_room(env):
    a,b,guest=env
    e1=a.post('/api/exhibits',json=item(title='校园收藏')).json()['id']
    e2=b.post('/api/exhibits',json=item(title='月光标本')).json()['id']
    assert a.post('/api/features/places',json={'exhibit_id':e1,'city':'昆明','area':'呈贡区','note':'校园里的奇物'}).status_code==200
    assert guest.get('/api/features/places').json()[0]['city']=='昆明'
    story=a.post('/api/features/stories',json={'title':'选择你的路线','intro':'来到迷宫','branches':['左边','右边'],'endings':['看见钟表','看到月亮']})
    assert story.status_code==200
    assert guest.get('/api/features/stories').json()[0]['endings']==['看见钟表','看到月亮']
    room=a.post('/api/features/rooms',json={'exhibit_id':e1,'title':'一起看展'}).json()['code']
    assert guest.get(f'/api/features/rooms/{room}').status_code==401
    assert b.get(f'/api/features/rooms/{room}').status_code==200
    assert b.post(f'/api/features/rooms/{room}/chat',json={'text':'好有趣'}).status_code==200
    assert b.post(f'/api/features/rooms/{room}/advance',json={'exhibit_id':e2}).status_code==403
    assert a.post(f'/api/features/rooms/{room}/advance',json={'exhibit_id':e2}).status_code==200
    result=b.get(f'/api/features/rooms/{room}').json()
    assert result['exhibit_title']=='月光标本'
    assert result['messages'][-1]['body']=='好有趣'
    assert len(result['participants'])==2