"""V12 time river, explainable associations, private collection world map."""
import sys
from test_multiuser import env, item
from cosmos_api import compare, source_host


def post(client, title, **kw):
    r = client.post('/api/exhibits', json=item(title=title, **kw))
    assert r.status_code == 201, r.text
    return r.json()['id']


def tag(client, exhibit_id, **fields):
    module = sys.modules['wa_test_server']
    with module.db() as c:
        columns={row['name'] for row in c.execute('PRAGMA table_info(exhibits)')}
        for col in ('series','domain','time_bucket','time_basis','time_note'):
            if col not in columns:
                c.execute(f"ALTER TABLE exhibits ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
        q=','.join(f'{field}=?' for field in fields)
        c.execute('UPDATE exhibits SET '+q+' WHERE id=?', (*fields.values(),exhibit_id))


def test_time_river_separates_periods_and_public_access(env):
    alice,bob,visitor=env
    fossil=post(alice,'古老化石', tags='化石,地层', category='自然与化石')
    secret=post(alice,'自己的隐私旧物', visibility='private',tags='私密')
    meme=post(bob,'最新热梗',category='流行文化',tags='热梗')
    tag(alice,fossil,series='藏品系列',domain='自然史与化石',time_bucket='亿年前',time_basis='形成/演化',time_note='约一亿年前')
    tag(alice,secret,series='民间奇趣',domain='其他',time_bucket='亿年前',time_basis='不详')
    tag(bob,meme,series='民间奇趣',domain='网络文化与热梗',time_bucket='最近一年',time_basis='走红/传播')
    r=visitor.get('/api/cosmos/eras')
    assert r.status_code == 200,r.text
    buckets={e['id']:e for e in r.json()['eras']}
    assert buckets['亿年前']['count']==1
    assert [e['id'] for e in buckets['亿年前']['items']]==[fossil]
    assert buckets['最近一年']['count']==1
    assert [e['id'] for e in buckets['最近一年']['items']]==[meme]
    assert visitor.get('/api/cosmos/eras?scope=mine').status_code==401
    mine=alice.get('/api/cosmos/eras?scope=mine&series=民间奇趣').json()
    assert mine['total']==1
    assert [x['id'] for e in mine['eras'] for x in e['items']]==[secret]
    filtered=visitor.get('/api/cosmos/eras?domain=自然史与化石&series=藏品系列').json()
    assert filtered['total']==1
    assert visitor.get('/api/cosmos/eras?series=unknown').status_code==400
    assert visitor.get('/api/cosmos/eras?scope=unknown').status_code==422


def test_relation_ranking_and_evidence_not_causation(env):
    alice,bob,visitor=env
    focus=post(alice,'海浪摄影',category='摄影与影像',tags='海浪,海洋',source_url='https://museum.example.org/a')
    same=post(bob,'海浪照片',category='摄影与影像',tags='海浪,云彩',source_url='https://museum.example.org/b')
    only_host=post(bob,'不同主题',category='游戏',tags='赛车',source_url='https://museum.example.org/c')
    isolated=post(bob,'完全无关',category='技术',tags='芯片')
    tag(alice,focus,domain='绘画与视觉艺术',series='藏品系列',time_bucket='近30年')
    tag(bob,same,domain='绘画与视觉艺术',series='藏品系列',time_bucket='近30年')
    tag(bob,only_host,domain='游戏与交互',time_bucket='近30年')
    tag(bob,isolated,domain='计算机与人工智能',time_bucket='近30年')
    res=visitor.get(f'/api/cosmos/relations/{focus}')
    assert res.status_code==200,res.text
    payload=res.json()
    assert payload['focus']['id']==focus
    items={x['target']['id']:x for x in payload['recommendations']}
    assert same in items
    assert only_host not in items  # source hostname + era are not enough to infer relationship
    assert isolated not in items
    evid={e['kind'] for e in items[same]['evidence']}
    assert {'shared_tags','same_category','same_domain','same_era','same_host'} <= evid
    assert payload['notice'].find('不是事实可信度') != -1
    assert visitor.get(f'/api/cosmos/relations/{focus}?limit=0').status_code==422
    assert source_host('javascript:alert(1)')==''


def test_manual_claims_have_provenance_and_private_target_remains_hidden(env):
    alice,bob,visitor=env
    visible=post(alice,'公开的原创论文',tags='算法')
    hidden=post(alice,'未发表的草稿',visibility='private',tags='算法')
    strangers=post(bob,'他人的隐私记录',visibility='private',tags='算法')
    link=alice.post(f'/api/exhibits/{visible}/connections',json={'target_id':hidden,'kind':'influence','explanation':'这是我对这两个版本关系的个人解释。'})
    assert link.status_code==201,link.text
    assert bob.get(f'/api/cosmos/relations/{hidden}').status_code==404
    for c in [bob,visitor]:
        r=c.get(f'/api/cosmos/relations/{visible}')
        assert r.status_code==200,r.text
        text=r.text
        assert str(hidden) not in [str(x['target']['id']) for x in r.json()['recommendations']]
        assert hidden not in [x['target_id'] for x in r.json()['manual']]
        assert '未发表的草稿' not in text
        if c is visitor:
            assert '他人的隐私记录' not in text
    owner=alice.get(f'/api/cosmos/relations/{visible}').json()
    assert hidden in [x['target_id'] for x in owner['manual']]
    assert owner['manual'][0]['status']=='curator_claim_not_verified'
    assert strangers not in [x['target_id'] for x in owner['manual']]


def test_personal_world_is_account_isolated_and_hall_aware(env):
    alice,bob,visitor=env
    a=post(alice,'我的量子笔记',visibility='private',tags='量子,研究')
    b=post(alice,'我的古画收藏',tags='历史,绘画')
    foreign=post(bob,'Bob 的绝密藏宝图',visibility='private',tags='私密')
    tag(alice,a,domain='物理与数学',series='民间奇趣',time_bucket='最近一年')
    tag(alice,b,domain='绘画与视觉艺术',series='藏品系列',time_bucket='近千年')
    tag(bob,foreign,domain='历史与考古')
    hall=alice.get('/api/my/halls').json()[0]['id']
    assert alice.post(f'/api/halls/{hall}/items',json={'exhibit_id':b}).status_code in [200,201]
    assert alice.post(f'/api/exhibits/{a}/connections',json={'target_id':b,'kind':'contrast','explanation':'我在个人收藏里对比科学与艺术的表达方式。'}).status_code==201
    assert visitor.get('/api/cosmos/me/map').status_code==401
    m=alice.get('/api/cosmos/me/map')
    assert m.status_code==200,m.text
    d=m.json()
    assert d['scope']=='private_to_signed_in_user'
    assert {x['id'] for x in d['nodes']}=={a,b}
    assert any(x['from']==a and x['to']==b for x in d['edges'])
    assert any(x['exhibit_id']==b and x['hall_id']==hall for x in d['memberships'])
    assert any(x['id']=='物理与数学' for x in d['domains'])
    assert foreign not in [x['id'] for x in d['nodes']]
    bb=bob.get('/api/cosmos/me/map').json()
    assert [x['id'] for x in bb['nodes']]==[foreign]
    assert '我的量子笔记' not in str(bb)


def test_ui_resources_and_server_mount(env):
    page=env[2].get('/')
    assert page.status_code==200
    assert '/static/cosmos.js' in page.text
    assert '/static/cosmos.css' in page.text
    assert env[2].get('/static/cosmos.js').status_code==200
    assert env[2].get('/static/cosmos.css').status_code==200
    assert '世界时间长河' in env[2].get('/static/cosmos.js').text