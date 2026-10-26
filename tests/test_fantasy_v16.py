"""V16: real persistence, provenance, world permissions, and fictional generator."""
from test_multiuser import env, item


def world(name='九天藏阁', theme='机械修真', law='记忆可以抵押', visibility='private'):
    return dict(name=name,theme=theme,law=law,visibility=visibility,intro='不存在于现实的幻想宇宙')


def relic(a='星尘', b='龙鳞', visibility='private', inspiration_id=None, nonce=31):
    return dict(ingredient_a=a, ingredient_b=b, visibility=visibility,
                inspiration_id=inspiration_id,nonce=nonce)


def test_config_and_preview_are_public_deterministic_fictional(env):
    alice,bob,visitor=env
    config=visitor.get('/api/fantasy/config')
    assert config.status_code==200
    assert len(config.json()['themes'])==6
    assert len(config.json()['materials'])>=16
    craft=dict(theme='机械修真',law='记忆可以抵押',ingredient_a='星尘',ingredient_b='龙鳞',nonce=31)
    a=visitor.post('/api/fantasy/preview',json=craft)
    b=visitor.post('/api/fantasy/preview',json=craft)
    assert a.status_code==200 and a.json()==b.json()
    assert a.json()['fictional'] is True and '虚构' in a.json()['notice']
    assert a.json()['price'] and a.json()['taboo'] and a.json()['ability']
    assert visitor.post('/api/fantasy/preview',json={**craft,'ingredient_b':'星尘'}).status_code==422
    assert visitor.post('/api/fantasy/preview',json={**craft,'ingredient_b':'煤炭'}).status_code==422
    assert visitor.get('/api/feed').json()['items']==[]


def test_fantasy_worlds_start_private_and_require_login(env):
    alice,bob,visitor=env
    assert visitor.post('/api/fantasy/worlds',json=world()).status_code==401
    r=alice.post('/api/fantasy/worlds',json=world())
    assert r.status_code==201,r.text
    wid=r.json()['id']
    assert alice.get('/api/fantasy/worlds?scope=mine').json()['items'][0]['id']==wid
    assert bob.get('/api/fantasy/worlds?scope=mine').json()['items']==[]
    assert visitor.get('/api/fantasy/worlds?scope=mine').status_code==401
    assert visitor.get('/api/fantasy/worlds').json()['items']==[]
    assert visitor.get(f'/api/fantasy/worlds/{wid}').status_code==404
    assert bob.get(f'/api/fantasy/worlds/{wid}').status_code==404
    assert alice.get(f'/api/fantasy/worlds/{wid}').json()['is_owner'] is True


def test_forge_creates_real_private_exhibit_with_fiction_flag(env):
    alice,bob,visitor=env
    wid=alice.post('/api/fantasy/worlds',json=world()).json()['id']
    r=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic())
    assert r.status_code==201,r.text
    eid=r.json()['exhibit_id']
    e=alice.get(f'/api/exhibits/{eid}').json()
    assert e['title'].startswith(('机魂','磁霄','天工','量子'))
    assert e['series']=='民间奇趣' and e['domain']=='原创与个人创作'
    assert e['category']=='世界观设定' and e['time_bucket']=='时间不详'
    assert e['source_url']=='' and e['visibility']=='private'
    assert '虚构' in e['story']
    assert visitor.get(f'/api/exhibits/{eid}').status_code==404
    assert bob.get(f'/api/exhibits/{eid}').status_code==404
    assert eid not in [x['id'] for x in visitor.get('/api/feed').json()['items']]
    assert len(alice.get(f'/api/fantasy/worlds/{wid}').json()['relics'])==1


def test_private_world_cannot_publish_and_public_world_filters_private_relics(env):
    alice,bob,visitor=env
    wid=alice.post('/api/fantasy/worlds',json=world()).json()['id']
    assert alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(visibility='public')).status_code==409
    a=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic()).json()['exhibit_id']
    assert alice.patch(f'/api/fantasy/relics/{a}/visibility',json={'visibility':'public'}).status_code==409
    assert alice.patch(f'/api/fantasy/worlds/{wid}/visibility',json={'visibility':'public'}).status_code==200
    assert visitor.get(f'/api/fantasy/worlds/{wid}').json()['relics']==[]
    assert visitor.get('/api/fantasy/worlds').json()['items'][0]['relic_count']==0
    b=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(a='古画',b='青铜铃',visibility='public')).json()['exhibit_id']
    detail=visitor.get(f'/api/fantasy/worlds/{wid}').json()
    assert len(detail['relics'])==1 and detail['relics'][0]['exhibit_id']==b
    assert visitor.get(f'/api/exhibits/{b}').status_code==200
    assert visitor.get(f'/api/fantasy/relics/{a}/fate').status_code==404
    assert visitor.get(f'/api/fantasy/relics/{b}/fate').status_code==200
    assert bob.delete(f'/api/fantasy/relics/{b}').status_code==404
    assert alice.patch(f'/api/fantasy/worlds/{wid}/visibility',json={'visibility':'private'}).status_code==200
    assert visitor.get(f'/api/fantasy/worlds/{wid}').status_code==404
    assert visitor.get(f'/api/exhibits/{b}').status_code==404
    assert alice.get(f'/api/exhibits/{b}').json()['visibility']=='private'
    assert alice.patch(f'/api/fantasy/worlds/{wid}/visibility',json={'visibility':'public'}).status_code==200
    assert visitor.get(f'/api/exhibits/{b}').status_code==404


def test_inspiration_access_checked_and_hidden_after_publishing(env):
    alice,bob,visitor=env
    src_private=bob.post('/api/exhibits',json=item(title='Bob的秘密代码',visibility='private')).json()['id']
    src_alice=alice.post('/api/exhibits',json=item(title='Alice私藏印记',visibility='private')).json()['id']
    src_pub=bob.post('/api/exhibits',json=item(title='公开古画')).json()['id']
    wid=alice.post('/api/fantasy/worlds',json=world(visibility='public')).json()['id']
    assert alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(inspiration_id=src_private)).status_code==404
    priv_inspire=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(inspiration_id=src_alice,visibility='public')).json()['exhibit_id']
    view=visitor.get(f'/api/fantasy/worlds/{wid}').json()['relics'][0]
    assert view['exhibit_id']==priv_inspire
    assert view['inspiration_id'] is None and view['inspiration_title'] is None
    own=alice.get(f'/api/fantasy/worlds/{wid}').json()['relics'][0]
    assert own['inspiration_title']=='Alice私藏印记'
    alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(a='古画',b='陨石',nonce=32,inspiration_id=src_pub,visibility='public'))
    rows=visitor.get(f'/api/fantasy/worlds/{wid}').json()['relics']
    assert any(x['inspiration_id']==src_pub and x['inspiration_title']=='公开古画' for x in rows)
    assert not any('Bob的秘密代码' in str(x) for x in rows)


def test_relic_fate_is_deterministic_and_does_not_persist(env):
    alice,bob,visitor=env
    wid=alice.post('/api/fantasy/worlds',json=world(visibility='public')).json()['id']
    eid=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(visibility='public')).json()['exhibit_id']
    a=visitor.get(f'/api/fantasy/relics/{eid}/fate?choice=守护')
    b=visitor.get(f'/api/fantasy/relics/{eid}/fate?choice=守护')
    c=visitor.get(f'/api/fantasy/relics/{eid}/fate?choice=献祭')
    assert a.status_code==200 and a.json()==b.json()
    assert c.status_code==200 and c.json()['opening']!=a.json()['opening']
    assert visitor.get(f'/api/fantasy/relics/{eid}/fate?choice=犯罪').status_code==422
    assert alice.get(f'/api/fantasy/worlds/{wid}').json()['relics'][0]['exhibit_id']==eid


def test_delete_relic_world_and_no_orphans(env):
    alice,bob,visitor=env
    wid=alice.post('/api/fantasy/worlds',json=world(visibility='public')).json()['id']
    eid=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(visibility='public')).json()['exhibit_id']
    assert bob.delete(f'/api/fantasy/worlds/{wid}').status_code==404
    assert bob.patch(f'/api/fantasy/worlds/{wid}/visibility',json={'visibility':'private'}).status_code==404
    assert bob.patch(f'/api/fantasy/relics/{eid}/visibility',json={'visibility':'private'}).status_code==404
    assert alice.delete(f'/api/fantasy/relics/{eid}').status_code==200
    assert visitor.get(f'/api/exhibits/{eid}').status_code==404
    eid2=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(visibility='public')).json()['exhibit_id']
    assert alice.delete(f'/api/fantasy/worlds/{wid}').status_code==200
    assert visitor.get(f'/api/exhibits/{eid2}').status_code==404
    assert visitor.get('/api/fantasy/worlds').json()['items']==[]


def test_invalid_fantasy_world_and_ingredient_refused(env):
    alice,bob,visitor=env
    assert alice.post('/api/fantasy/worlds',json=world(theme='现实世界')).status_code==422
    wid=alice.post('/api/fantasy/worlds',json=world()).json()['id']
    assert alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(a='不存在的神矿')).status_code==422
    assert alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(a='星尘',b='星尘')).status_code==422
    assert visitor.post(f'/api/fantasy/worlds/{wid}/forge',json=relic()).status_code==401


def test_generic_edit_cannot_turn_private_fiction_into_public_fact(env):
    alice,bob,visitor=env
    wid=alice.post('/api/fantasy/worlds',json=world()).json()['id']
    eid=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic()).json()['exhibit_id']
    attempt=alice.patch(f'/api/exhibits/{eid}',json=item(title='真实出土神器',story='绝对真实史料',source_url='https://example.com/',visibility='public'))
    assert attempt.status_code==409
    saved=alice.patch(f'/api/exhibits/{eid}',json=item(title='天工遗器',story='我写的玄幻故事',source_url='https://example.com/',visibility='private'))
    assert saved.status_code==200,saved.text
    assert saved.json()['category']=='世界观设定'
    assert '虚构' in saved.json()['story']
    assert saved.json()['source_url']==''
    assert visitor.get(f'/api/exhibits/{eid}').status_code==404


def test_fictional_artifacts_do_not_enter_factual_time_river(env):
    import pytest
    alice, bob, visitor = env
    wid=alice.post('/api/fantasy/worlds',json=world(visibility='public')).json()['id']
    eid=alice.post(f'/api/fantasy/worlds/{wid}/forge',json=relic(visibility='public')).json()['exhibit_id']
    assert visitor.get(f'/api/exhibits/{eid}').status_code==200  # Public fantasy showcase remains open.
    r=visitor.get('/api/cosmos/eras')
    if r.status_code==404:
        pytest.skip('Older local V15 base does not include cosmos; V16 GitHub does')
    assert r.status_code==200,r.text
    assert eid not in {e['id'] for era in r.json()['eras'] for e in era['items']}
    mine=alice.get('/api/cosmos/eras?scope=mine')
    assert mine.status_code==200,mine.text
    assert eid not in {e['id'] for era in mine.json()['eras'] for e in era['items']}