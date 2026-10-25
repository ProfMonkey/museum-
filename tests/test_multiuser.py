"""Real HTTP-style integration tests, checking visibility and permission boundaries."""
import importlib.util
import io
import os
import sys

from fastapi.testclient import TestClient
from PIL import Image
import pytest


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("WONDER_DATA_DIR", str(tmp_path / "data"))
    sys.path.insert(0, str(__file__.rsplit('/tests/', 1)[0]))
    # New isolated module per test, each one gets a fresh SQLite database.
    p = os.path.join(sys.path[0], "server.py")
    spec = importlib.util.spec_from_file_location("wa_test_server", p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    a, b, visitor = TestClient(module.app), TestClient(module.app), TestClient(module.app)
    for client, name in ((a, "Alice"), (b, "Bob")):
        r = client.post("/api/auth/register", json={"username": name, "password": "secretpass123"})
        assert r.status_code == 201, r.text
    yield a, b, visitor
    a.close(); b.close(); visitor.close()


def item(**kw):
    d = dict(title="罕见的夜光石", description="在路边发现的石头", story="有趣的观察记录", category="自然", tags="石头,发光", image_url="", source_url="", visibility="public")
    d.update(kw)
    return d


def test_public_network_and_private_isolation(env):
    alice, bob, visitor = env
    e = alice.post('/api/exhibits', json=item()).json()
    assert e['id']
    assert visitor.get('/api/feed').json()['items'][0]['title'] == '罕见的夜光石'
    assert bob.get('/api/feed?q=石头').json()['items'][0]['id'] == e['id']
    assert bob.get('/api/users/Alice').json()['items'][0]['id'] == e['id']
    assert bob.get('/api/exhibits/'+str(e['id'])).status_code == 200
    private = alice.post('/api/exhibits', json=item(title='仅自己可见的日记',visibility='private')).json()
    assert alice.get('/api/exhibits/'+str(private['id'])).status_code == 200
    assert bob.get('/api/exhibits/'+str(private['id'])).status_code == 404
    assert visitor.get('/api/exhibits/'+str(private['id'])).status_code == 404
    assert private['id'] not in [x['id'] for x in visitor.get('/api/feed').json()['items']]
    assert private['id'] not in [x['id'] for x in bob.get('/api/users/Alice').json()['items']]
    assert bob.patch('/api/exhibits/'+str(e['id']),json=item(title='修改别人的展品')).status_code == 403
    assert bob.delete('/api/exhibits/'+str(e['id'])).status_code == 403
    assert bob.post('/api/halls/1/items',json={'exhibit_id':e['id']}).status_code == 403


def test_real_comments_likes_notifications_follows(env):
    alice, bob, visitor = env
    e=alice.post('/api/exhibits', json=item()).json()
    assert bob.post(f"/api/exhibits/{e['id']}/like").json()['liked'] is True
    assert bob.post(f"/api/exhibits/{e['id']}/bookmark").json()['bookmarked'] is True
    assert bob.post(f"/api/exhibits/{e['id']}/comments",json={'body':'我也见过！'}).status_code==201
    assert visitor.get(f"/api/exhibits/{e['id']}/comments").json()[0]['body']=='我也见过！'
    assert bob.post('/api/users/1/follow').json()['following'] is True
    n=alice.get('/api/notifications').json()
    assert n['unread']==3
    assert {x['kind'] for x in n['items']}=={'like','comment','follow'}
    assert alice.post('/api/notifications/read').status_code == 200
    assert alice.get('/api/notifications').json()['unread'] == 0
    assert bob.get('/api/my/saved').json()[0]['id'] == e['id']
    assert visitor.post(f"/api/exhibits/{e['id']}/like").status_code == 401
    assert bob.post(f"/api/exhibits/{e['id']}/like").json()['liked'] is False
    assert bob.post('/api/users/1/follow').json()['following'] is False


def test_halls_privacy_placement_and_layout(env):
    alice,bob,visitor=env
    visible=alice.post('/api/exhibits',json=item(title='展示用石头')).json()
    secret=alice.post('/api/exhibits',json=item(title='我的秘密',visibility='private')).json()
    hall=alice.get('/api/my/halls').json()[0]
    assert alice.post(f"/api/halls/{hall['id']}/items",json={'exhibit_id':visible['id']}).status_code==200
    assert alice.post(f"/api/halls/{hall['id']}/items",json={'exhibit_id':secret['id']}).status_code==200
    public_view=bob.get(f"/api/halls/{hall['id']}").json()
    assert [x['id'] for x in public_view['items']]==[visible['id']]
    assert len(alice.get(f"/api/halls/{hall['id']}").json()['items'])==2
    layout={'positions':[{'exhibit_id':visible['id'],'x':233,'y':120,'width':240}]}
    assert alice.patch(f"/api/halls/{hall['id']}/layout",json=layout).status_code==200
    assert bob.get(f"/api/halls/{hall['id']}").json()['items'][0]['x']==233
    assert bob.patch(f"/api/halls/{hall['id']}/layout",json=layout).status_code==403
    hall_payload={'name':'私密展厅','description':'秘密','theme':'gallery','visibility':'private'}
    private_hall=alice.post('/api/halls',json=hall_payload).json()['id']
    assert bob.get(f'/api/halls/{private_hall}').status_code==404
    assert visitor.get(f'/api/halls/{private_hall}').status_code==404


def test_legacy_import_image_and_validation(env):
    alice,bob,visitor=env
    backup={'kind':'wonder-atlas-backup','data':{'custom':[{'title':'过去的收藏','description':'来自本地','tags':['历史','兴趣'],'visibility':'public'}, {'title':''}]}}
    got=alice.post('/api/import/v1',json=backup)
    assert got.status_code==200 and got.json()['imported']==1
    assert alice.get('/api/my/exhibits').json()[0]['visibility']=='private'
    assert visitor.get('/api/feed').json()['items']==[]
    img=Image.new('RGB',(110,90),'#bba988');out=io.BytesIO();img.save(out,format='PNG')
    r=alice.post('/api/media',files={'file':('test.png',out.getvalue(),'image/png')})
    assert r.status_code==201,r.text
    path=r.json()['url'];assert path.startswith('/media/') and visitor.get(path).status_code==200
    assert alice.post('/api/exhibits',json=item(image_url='javascript:alert(1)')).status_code==422
    assert alice.post('/api/exhibits',json=item(title='')).status_code==422
    assert bob.post('/api/import/v1',json={'data':{'custom':[]}}).json()['imported']==0
    assert alice.post('/api/auth/logout').status_code==200
    assert alice.get('/api/me').json()['user'] is None


def test_origin_rejection_and_public_statistics(env):
    a,b,visitor=env
    assert a.post('/api/exhibits',headers={'Origin':'https://evil.example'},json=item()).status_code==403
    assert visitor.get('/api/health').json()['ok']
    assert visitor.get('/api/stats').json()['curators']==2
    assert visitor.get('/api/random').json() is None


def test_following_feed_related_and_v2_backup_restore(env):
    alice, bob, visitor = env
    one = alice.post('/api/exhibits', json=item(title='天文展品',category='科学',tags='星星,宇宙')).json()
    two = alice.post('/api/exhibits', json=item(title='银河展品',category='科学',tags='星星,星云')).json()
    bob_exhibit = bob.post('/api/exhibits', json=item(title='Bob的艺术品',category='艺术',tags='绘画')).json()
    assert alice.get('/api/exhibits/'+str(one['id'])+'/related').json()[0]['id'] == two['id']
    assert alice.get('/api/feed?following=true').json()['items'] == []
    assert alice.post('/api/users/'+str(bob_exhibit['user_id'])+'/follow').json()['following']
    assert [r['id'] for r in alice.get('/api/feed?following=true').json()['items']] == [bob_exhibit['id']]
    assert visitor.get('/api/feed?following=true').status_code == 401
    hall=alice.get('/api/my/halls').json()[0]
    assert alice.post(f"/api/halls/{hall['id']}/items",json={'exhibit_id':one['id']}).status_code==200
    assert alice.patch(f"/api/halls/{hall['id']}/layout",json={'positions':[{'exhibit_id':one['id'],'x':141,'y':77,'width':200}]}).status_code==200
    backup=alice.get('/api/my/backup').json()
    assert backup['format']=='wonder-atlas-network-v2'
    assert len(backup['exhibits'])==2
    assert backup['halls'][0]['items'][0]['x']==141
    result=bob.post('/api/import/v2',json=backup)
    assert result.status_code==200,result.text
    assert result.json()['mapped_exhibits']==2
    assert result.json()['created_halls']==0  # Both users already own the default-named hall; reuse it.
    assert len(bob.get('/api/my/exhibits').json())==3
    extra=bob.get('/api/my/halls').json()[-1]
    assert bob.get('/api/halls/'+str(extra['id'])).json()['items'][0]['x']==141
    # Restore is explicit: do not import someone else's accounts or private information.
    assert bob.get('/api/me').json()['user']['username']=='Bob'