"""V18 civilization timeline regression tests using actual SQLite and FastAPI routes.

The minimal auth fixture supplies named test identities. The full deployed app
continues to use server.py's normal authenticated session cookies.
"""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.testclient import TestClient
import pytest
from fantasy_api import mount_fantasy
from diplomacy_api import mount_diplomacy
from evolution_api import mount_evolution, evolve, INITIAL


def _setup(tmp_path):
    path = tmp_path / 'worlds.sqlite3'

    @contextmanager
    def db():
        con = sqlite3.connect(path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    with db() as c:
        c.executescript('''
            CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT NOT NULL);
            INSERT INTO users(id,username) VALUES(1,'Alice'),(2,'Bob'),(3,'Carol');
            CREATE TABLE exhibits(
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT, description TEXT, story TEXT, category TEXT,
                series TEXT,domain TEXT,time_bucket TEXT,time_basis TEXT,time_note TEXT,
                tags TEXT,image_url TEXT,source_url TEXT,visibility TEXT,
                created_at TEXT,updated_at TEXT
            );
        ''')
    app=FastAPI()

    def maybe_user(x_demo_user:str|None=Header(default=None)):
        # For isolated permission contract tests only; not production authentication.
        if not x_demo_user:
            return None
        with db() as c:
            raw=c.execute('SELECT * FROM users WHERE username=?',(x_demo_user,)).fetchone()
            return dict(raw) if raw else None

    def require_user(u=Depends(maybe_user)):
        if not u:
            raise HTTPException(401,detail='please log in')
        return u

    def fail(status,msg):
        raise HTTPException(status,detail=msg)

    mount_fantasy(app,db,require_user,maybe_user,lambda:'2026-10-26T00:00:00+00:00',fail)
    mount_diplomacy(app,db,require_user,maybe_user,lambda:'2026-10-26T00:00:00+00:00',fail)
    mount_evolution(app,db,require_user,maybe_user,lambda:'2026-10-26T00:00:00+00:00',fail)
    return app,db


@pytest.fixture()
def lab(tmp_path):
    app,db=_setup(tmp_path)
    with TestClient(app) as guest,TestClient(app,headers={'X-Demo-User':'Alice'}) as alice,TestClient(app,headers={'X-Demo-User':'Bob'}) as bob,TestClient(app,headers={'X-Demo-User':'Carol'}) as carol:
        yield guest,alice,bob,carol,db


def world(name, theme='星河仙庭', law='灵气必须守恒', visibility='public'):
    return {'name':name,'theme':theme,'law':law,'visibility':visibility,'intro':'这是共同创作的虚构宇宙'}


def make_pair(alice,bob):
    a=alice.post('/api/fantasy/worlds',json=world('九霄炼器庭'))
    b=bob.post('/api/fantasy/worlds',json=world('梦潮帝国','梦境荒原','时间由梦供养'))
    assert a.status_code==201 and b.status_code==201,(a.text,b.text)
    return a.json()['id'],b.json()['id']


def make_civilization(alice, visibility='public', world_visibility='public', name='天机城邦'):
    world_id=alice.post('/api/fantasy/worlds',json=world('浮光天界',visibility=world_visibility)).json()['id']
    payload={'world_id':world_id,'name':name,'capital':'浮光城',
             'ethos':'万物演变皆有代价','style':'机械城邦','visibility':visibility}
    response=alice.post('/api/fantasy/council/civilizations',json=payload)
    assert response.status_code==201,response.text
    return world_id,response.json()['id']


def start(alice,cid,name='星火纪元'):
    response=alice.post('/api/fantasy/evolution/timelines',
                        json={'civilization_id':cid,'name':name})
    assert response.status_code==201,response.text
    return response.json()['id']


def advance(alice,tid,policy='求知'):
    return alice.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
                      json={'policy':policy})


def test_config_empty_and_no_fabricated_years(lab):
    guest,alice,bob,carol,db=lab
    conf=guest.get('/api/fantasy/evolution/config')
    assert conf.status_code==200 and conf.json()['max_year']==100
    assert len(conf.json()['policies'])==4
    assert guest.get('/api/fantasy/evolution/civilizations?scope=public').json()['items']==[]
    assert guest.get('/api/fantasy/evolution/civilizations?scope=mine').status_code==401
    assert guest.post('/api/fantasy/evolution/timelines',
                      json={'civilization_id':1,'name':'不能创建'}).status_code==401


def test_ownership_and_year_snapshot_is_immutable(lab):
    guest,alice,bob,carol,db=lab
    wid,cid=make_civilization(alice,visibility='private')
    tid=start(alice,cid)
    assert bob.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    assert bob.post('/api/fantasy/evolution/timelines',
                    json={'civilization_id':cid,'name':'他人的世界'}).status_code==404
    assert bob.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
                    json={'policy':'开垦'}).status_code==404
    first=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()
    assert first['current']['stats']==INITIAL and len(first['years'])==1
    result=advance(alice,tid,'开垦')
    assert result.status_code==201,result.text
    second=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()
    assert [r['year'] for r in second['years']]==[0,1]
    assert second['years'][0]==first['years'][0]
    assert second['current']['stats']!=INITIAL
    assert second['law']=='灵气必须守恒'


def test_evolution_is_reproducible_and_resource_bounded(lab):
    guest,alice,bob,carol,db=lab
    _,cid=make_civilization(alice)
    tid=start(alice,cid)
    a=evolve(INITIAL,'求知','灵气必须守恒',tid,1)
    b=evolve(INITIAL,'求知','灵气必须守恒',tid,1)
    assert a==b
    for i in range(14):
        result=advance(alice,tid,['求知','开垦','通商','守护'][i%4])
        assert result.status_code==201,result.text
        state=result.json()['stats']
        assert 100<=state['population']<=10000000
        assert all(0<=v<=100 for k,v in state.items() if k!='population')
    assert len(alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['years'])==15
    assert advance(alice,tid,'not-a-policy').status_code==422


def test_branch_from_prior_year_preserves_parent_and_limits(lab):
    guest,alice,bob,carol,db=lab
    _,cid=make_civilization(alice)
    tid=start(alice,cid)
    advance(alice,tid,'求知')
    advance(alice,tid,'通商')
    state=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['years'][1]['stats']
    bad=alice.post(f'/api/fantasy/evolution/timelines/{tid}/fork',
                   json={'name':'错误年限','year':50})
    assert bad.status_code==422
    fork=alice.post(f'/api/fantasy/evolution/timelines/{tid}/fork',
                    json={'name':'平行纪元','year':1})
    assert fork.status_code==201,fork.text
    fork_id=fork.json()['id']
    snapshot=alice.get(f'/api/fantasy/evolution/timelines/{fork_id}').json()
    assert snapshot['years'][0]['year']==1
    assert snapshot['years'][0]['stats']==state
    assert snapshot['visibility']=='private'
    advance(alice,fork_id,'守护')
    assert alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['current']['year']==2
    start(alice,cid,'第三纪元')
    assert alice.post(f'/api/fantasy/evolution/timelines/{tid}/fork',
                      json={'name':'超额分支','year':0}).status_code==429
    assert alice.post('/api/fantasy/evolution/timelines',
                      json={'civilization_id':cid,'name':'第四纪元'}).status_code==429
    assert bob.delete(f'/api/fantasy/evolution/timelines/{fork_id}').status_code==404


def test_publication_requires_both_world_and_civilization(lab):
    guest,alice,bob,carol,db=lab
    wid,cid=make_civilization(alice,visibility='private')
    tid=start(alice,cid)
    assert alice.patch(f'/api/fantasy/evolution/timelines/{tid}/visibility',
                       json={'visibility':'public'}).status_code==409
    assert alice.patch(f'/api/fantasy/council/civilizations/{cid}/visibility',
                       json={'visibility':'public'}).status_code==200
    published=alice.patch(f'/api/fantasy/evolution/timelines/{tid}/visibility',
                          json={'visibility':'public'})
    assert published.status_code==200
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==200
    assert guest.get(f'/api/fantasy/evolution/timelines?civilization_id={cid}').json()['items'][0]['id']==tid
    assert guest.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
                      json={'policy':'求知'}).status_code==401
    assert bob.patch(f'/api/fantasy/evolution/timelines/{tid}/visibility',
                     json={'visibility':'private'}).status_code==404


def test_world_closed_revokes_archive_and_reopening_does_not_restore(lab):
    guest,alice,bob,carol,db=lab
    wid,cid=make_civilization(alice)
    tid=start(alice,cid)
    alice.patch(f'/api/fantasy/evolution/timelines/{tid}/visibility',
                json={'visibility':'public'})
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==200
    assert alice.patch(f'/api/fantasy/worlds/{wid}/visibility',
                       json={'visibility':'private'}).status_code==200
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    alice.patch(f'/api/fantasy/worlds/{wid}/visibility',json={'visibility':'public'})
    alice.patch(f'/api/fantasy/council/civilizations/{cid}/visibility',
                json={'visibility':'public'})
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    own=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()
    assert own['visibility']=='private'


def test_civilization_visibility_withdrawal_never_auto_republishes(lab):
    guest,alice,bob,carol,db=lab
    wid,cid=make_civilization(alice)
    tid=start(alice,cid)
    alice.patch(f'/api/fantasy/evolution/timelines/{tid}/visibility',
                json={'visibility':'public'})
    alice.patch(f'/api/fantasy/council/civilizations/{cid}/visibility',
                json={'visibility':'private'})
    alice.patch(f'/api/fantasy/council/civilizations/{cid}/visibility',
                json={'visibility':'public'})
    assert guest.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    assert alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['visibility']=='private'


def test_world_and_civilization_deletion_cascade(lab):
    guest,alice,bob,carol,db=lab
    wid,cid=make_civilization(alice)
    tid=start(alice,cid)
    assert alice.delete(f'/api/fantasy/council/civilizations/{cid}').status_code==200
    assert alice.get(f'/api/fantasy/evolution/timelines/{tid}').status_code==404
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM fantasy_evolution_years').fetchone()[0]==0
    _,other=make_civilization(alice,name='第二城邦')
    other_tid=start(alice,other)
    assert alice.delete(f'/api/fantasy/worlds/{wid}').status_code==200
    assert alice.get(f'/api/fantasy/evolution/timelines/{other_tid}').status_code==200


def test_one_hundred_year_hard_stop_and_snapshot_count(lab):
    guest,alice,bob,carol,db=lab
    _,cid=make_civilization(alice)
    tid=start(alice,cid)
    for _ in range(100):
        r=advance(alice,tid,'守护')
        assert r.status_code==201,r.text
    assert advance(alice,tid,'开垦').status_code==409
    years=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['years']
    assert years[0]['year']==0 and years[-1]['year']==100
    assert len(years)==101
