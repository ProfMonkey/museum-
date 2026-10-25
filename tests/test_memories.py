"""Memory privacy, access revocation, multiple accounts and explicit recording."""
from test_multiuser import env


def signup(client, username):
    r = client.post('/api/auth/register', json={'username': username, 'password':'strong-pass-123'})
    assert r.status_code in (200, 201), r.text


def put(client, title, visibility='public'):
    r = client.post('/api/exhibits', json={'title':title, 'visibility':visibility})
    assert r.status_code == 201, r.text
    return r.json()['id']


def test_recording_is_opt_in_and_user_isolated(env):
    a,b,visitor = env
    ida=put(a,'在星空下看过的东西')
    # Reading public API does not record history; only explicit /seen does.
    assert a.get(f'/api/exhibits/{ida}').status_code==200
    assert a.get('/api/memories/history').json()['items']==[]
    assert a.post(f'/api/memories/seen/{ida}').json()['recorded']
    assert a.post(f'/api/memories/seen/{ida}').status_code==200
    hist = a.get('/api/memories/history').json()['items']
    assert len(hist)==1 and hist[0]['view_count']==2

    assert b.get('/api/memories/history').json()['items']==[]
    assert b.post(f'/api/memories/seen/{ida}').status_code==200
    assert len(b.get('/api/memories/history').json()['items'])==1
    assert a.delete('/api/memories/history').status_code==200
    assert a.get('/api/memories/history').json()['items']==[]
    assert len(b.get('/api/memories/history').json()['items'])==1


def test_reels_skip_revoked_content_without_leaks(env):
    a,b,visitor=env
    ida=put(a,'过去的旅程')

    assert b.post(f'/api/memories/seen/{ida}').status_code==200
    film=b.post('/api/memories/reels',json={'title':'我的金色电影','exhibit_ids':[ida], 'music':'starlight'})
    assert film.status_code==201, film.text
    rid=film.json()['id']
    assert len(film.json()['items'])==1
    assert a.get('/api/memories/reels').json()==[]
    payload={'title':'过去的旅程','visibility':'private'}
    assert a.patch(f'/api/exhibits/{ida}',json=payload).status_code==200
    assert b.get('/api/memories/history').json()['items']==[]
    recorded=b.get('/api/memories/reels').json()
    assert len(recorded)==1 and recorded[0]['items']==[]
    assert b.post(f'/api/memories/seen/{ida}').status_code==404
    assert b.post('/api/memories/reels',json={'title':'非法影片','exhibit_ids':[ida]}).status_code==404
    assert b.delete(f'/api/memories/reels/{rid}').status_code==200
    assert b.get('/api/memories/reels').json()==[]


def test_reel_constraints_and_unauthenticated_access(env):
    a,b,visitor=env
    assert visitor.get('/api/memories/history').status_code==401
    assert visitor.post('/api/memories/seen/1').status_code==401
    own=put(a,'我的私密记录','private')
    assert a.post(f'/api/memories/seen/{own}').status_code==200
    assert a.post('/api/memories/reels',json={'title':' ','exhibit_ids':[own]}).status_code==422
    assert a.post('/api/memories/reels',json={'title':'A'*61,'exhibit_ids':[own]}).status_code==422
    assert a.post('/api/memories/reels',json={'title':'valid','exhibit_ids':[]}).status_code==422
    assert a.delete('/api/memories/reels/999999').status_code==404