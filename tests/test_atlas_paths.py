"""V7 route integration tests: paths must exist and never disclose private content."""
from test_multiuser import env, item


def test_featured_routes_are_explainable_without_fake_data(env):
    a, b, guest = env
    features = guest.get('/api/atlas/featured')
    assert features.status_code == 200, features.text
    data=features.json()['items']
    assert len(data) == 4
    assert all(x['hops'] and x['hops'] <= 8 and len(x['steps']) == x['hops'] for x in data)
    assert all(y['kind'] == '策展关联' and y['reason'] for x in data for y in x['steps'])
    assert any(node['kind']=='work' for x in data for node in x['items'])
    assert guest.get('/api/atlas/nodes?kind=topic').json()['total']>=18
    assert all(x['kind']=='topic' for x in guest.get('/api/atlas/nodes?kind=topic').json()['items'])


def test_path_from_old_painting_to_ai_is_real_and_preserves_attribution(env):
    a,b,guest=env
    result=guest.get('/api/atlas/path?start=work:aic:27992&target=topic:ai&max_hops=8')
    assert result.status_code==200,result.text
    out=result.json()
    assert out['found'] and out['items'][0]['title']=='大碗岛的星期日下午'
    assert out['items'][-1]['title']=='人工智能'
    assert out['hops']==len(out['steps'])
    assert all(step['kind'] in ('人工确认','策展关联','关键词建议') for step in out['steps'])
    assert guest.get('/api/atlas/path?start=topic:ai&target=topic:ai').json()['hops']==0
    assert guest.get('/api/atlas/path?start=topic:ai&target=bad-node').status_code==404


def test_private_user_exhibits_never_enter_graph_or_links(env):
    a,b,guest=env
    published=a.post('/api/exhibits',json=item(title='古老的机械钟表',tags='计时,齿轮',category='历史文物')).json()['id']
    secret=a.post('/api/exhibits',json=item(title='一个未公开的隐秘量子设备',tags='量子,晶体管',visibility='private')).json()['id']
    list_nodes=guest.get('/api/atlas/nodes?kind=post').json()['items']
    assert len(list_nodes)==1 and list_nodes[0]['id']==f'post:{published}'
    assert str(secret) not in str(list_nodes)
    result=guest.get('/api/atlas/path',params={'start':f'post:{published}','target':'topic:quantum','max_hops':8})
    assert result.status_code==200 and result.json()['found']
    assert guest.get('/api/atlas/recommend',params={'node_id':f'post:{secret}'}).status_code==404
    assert guest.get('/api/atlas/path',params={'start':'topic:quantum','target':f'post:{secret}'}).status_code==404
    a.patch(f'/api/exhibits/{published}',json={'title':'机械钟表','visibility':'private'})
    assert guest.get('/api/atlas/path',params={'start':f'post:{published}','target':'topic:time'}).status_code==404


def test_route_storage_and_owner_isolation_and_revocation(env):
    a,b,guest=env
    post=a.post('/api/exhibits',json=item(title='怀表',tags='钟表,计时',category='历史文物')).json()['id']
    ids=[f'post:{post}','topic:time','topic:measurement']
    data={'title':'怀表与现代测量','node_ids':ids}
    assert guest.post('/api/atlas/routes',json=data).status_code==401
    created=a.post('/api/atlas/routes',json=data)
    assert created.status_code==201,created.text
    assert created.json()['route']['hops']==2
    a_saved=a.get('/api/atlas/routes').json()['items']
    assert a_saved[0]['available'] and a_saved[0]['items'][0]['id']==f'post:{post}'
    assert b.get('/api/atlas/routes').json()['items']==[]
    assert b.delete('/api/atlas/routes/'+str(a_saved[0]['id'])).status_code==404
    assert a.post('/api/atlas/routes',json={**data,'title':'重命名'}).status_code==201
    assert len(a.get('/api/atlas/routes').json()['items'])==1
    bad=a.post('/api/atlas/routes',json={'title':'恶意跳转','node_ids':['topic:ai','topic:jewels']})
    assert bad.status_code==422
    assert a.post('/api/atlas/routes',json={'title':'重复','node_ids':['topic:ai','topic:ai']}).status_code==422
    assert b.get('/api/atlas/routes').json()['items']==[]
    a.patch(f'/api/exhibits/{post}',json={'title':'仅自己看见','visibility':'private'})
    redacted=a.get('/api/atlas/routes').json()['items'][0]
    assert not redacted['available'] and 'items' not in redacted
    assert guest.get('/api/atlas/nodes',params={'q':'仅自己看见'}).json()['items']==[]
    assert a.delete('/api/atlas/routes/'+str(a_saved[0]['id'])).status_code==200


def test_owner_confirmed_links_not_mistaken_for_machine_suggestions(env):
    a,b,guest=env
    src=a.post('/api/exhibits',json=item(title='旧书中的机械结构',tags='书籍',category='古籍与手稿')).json()['id']
    dst=b.post('/api/exhibits',json=item(title='海底奇物',tags='深海',category='自然与化石')).json()['id']
    posted=a.post(f'/api/features/wormhole/{src}/links',json={'destination_id':dst,'relation':'相似用途','reason':'馆主自己认为有启发性的对照'})
    assert posted.status_code==200,posted.text
    out=guest.get('/api/atlas/recommend',params={'node_id':f'post:{src}'}).json()
    manual=[x for x in out['items'] if x['node']['id']==f'post:{dst}']
    assert len(manual)==1
    assert manual[0]['kind']=='人工确认'
    assert '馆主自己认为' in manual[0]['reason']