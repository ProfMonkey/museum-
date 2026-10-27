"""V19 two-sided fictional exchange regression tests using actual SQLite and FastAPI routes.

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
from relations_api import mount_relations, KINDS


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
    mount_relations(app,db,require_user,maybe_user,lambda:'2026-10-26T00:00:00+00:00',fail)
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



def make_relation(alice,bob):
    _,aid=make_civilization(alice,name='天机城邦')
    _,bid=make_civilization(bob,name='深海龙国')
    return aid,bid


def invitation(source,target,kind='学术交流'):
    return {'source_id':source,'target_id':target,'kind':kind,
            'message':'我们希望在星门彼岸共同研究文明发展的另一种可能。'}


def send(alice,source,target,kind='学术交流'):
    result=alice.post('/api/fantasy/relations',json=invitation(source,target,kind))
    assert result.status_code==201,result.text
    return result.json()['id']


def accept(bob,rid):
    return bob.patch(f'/api/fantasy/relations/{rid}',json={'action':'accept'})


def test_empty_catalog_and_anonymous_permissions(lab):
    guest,alice,bob,carol,db=lab
    conf=guest.get('/api/fantasy/relations/config')
    assert conf.status_code==200 and len(conf.json()['kinds'])==4
    assert guest.get('/api/fantasy/relations/civilizations').json()['items']==[]
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    assert guest.get('/api/fantasy/relations?scope=mine').status_code==401
    assert guest.post('/api/fantasy/relations',json=invitation(1,2)).status_code==401
    assert guest.get('/api/fantasy/relations/available?timeline_id=1').status_code==401


def test_pair_requires_distinct_real_owners_and_public_civilizations(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    directory=guest.get('/api/fantasy/relations/civilizations').json()['items']
    assert len(directory)==2
    assert all(not c['mine'] for c in directory)
    assert bob.post('/api/fantasy/relations',json=invitation(a,b)).status_code==404
    assert alice.post('/api/fantasy/relations',json=invitation(a,a)).status_code==422
    _,own2=make_civilization(alice,name='天宫新城')
    assert alice.post('/api/fantasy/relations',json=invitation(a,own2)).status_code==422
    invalid=alice.post('/api/fantasy/relations',json=invitation(a,b,kind='真实贸易'))
    assert invalid.status_code==422
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM fantasy_civilization_relations').fetchone()[0]==0


def test_invitation_private_until_invitee_accepts(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    rid=send(alice,a,b)
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    assert carol.get('/api/fantasy/relations?scope=mine').json()['items']==[]
    assert bob.get('/api/fantasy/relations?scope=mine').json()['items'][0]['can_accept']
    assert alice.patch(f'/api/fantasy/relations/{rid}',json={'action':'accept'}).status_code==403
    assert carol.patch(f'/api/fantasy/relations/{rid}',json={'action':'accept'}).status_code==404
    assert alice.post('/api/fantasy/relations',json=invitation(b,a)).status_code==404
    assert bob.post('/api/fantasy/relations',json=invitation(b,a)).status_code==409
    result=accept(bob,rid)
    assert result.status_code==200,result.text
    assert len(guest.get('/api/fantasy/relations').json()['items'])==1
    assert accept(bob,rid).status_code==409


def test_influence_requires_explicit_choice_only_updates_own_future_year(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    aid=start(alice,a)
    bid=start(bob,b)
    rid=send(alice,a,b,'学术交流')
    assert alice.get(f'/api/fantasy/relations/available?timeline_id={aid}').json()['items']==[]
    assert alice.post(f'/api/fantasy/evolution/timelines/{aid}/advance',
                      json={'policy':'求知','relation_id':rid}).status_code==409
    assert accept(bob,rid).status_code==200
    assert bob.get(f'/api/fantasy/relations/available?timeline_id={aid}').status_code==404
    available=alice.get(f'/api/fantasy/relations/available?timeline_id={aid}').json()['items']
    assert [x['id'] for x in available]==[rid]
    result=alice.post(f'/api/fantasy/evolution/timelines/{aid}/advance',
                      json={'policy':'求知','relation_id':rid})
    assert result.status_code==201,result.text
    outcome=result.json()
    assert outcome['influence']=='学术交流'
    # The annual simulation uses only the one selected effect, with no other owner's mutation.
    predicted,_=evolve(INITIAL,'求知','灵气必须守恒',aid,1,KINDS['学术交流'])
    assert outcome['stats']==predicted
    assert bob.get(f'/api/fantasy/evolution/timelines/{bid}').json()['current']['year']==0
    assert alice.get(f'/api/fantasy/evolution/timelines/{aid}').json()['years'][1]['influence']=='学术交流'
    plain=advance(alice,aid,'守护')
    assert plain.status_code==201 and plain.json()['influence'] is None


def test_unrelated_civilization_cannot_borrow_other_people_influence(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    _,third=make_civilization(carol,name='异域第三城')
    rid=send(alice,a,b)
    assert accept(bob,rid).status_code==200
    tid=start(carol,third)
    assert carol.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
           json={'policy':'通商','relation_id':rid}).status_code==409
    assert alice.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
           json={'policy':'求知','relation_id':rid}).status_code==404
    assert carol.get(f'/api/fantasy/evolution/timelines/{tid}').json()['current']['year']==0


def test_revoke_prevents_future_influence_but_preserves_old_immutable_snapshot(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    tid=start(alice,a)
    rid=send(alice,a,b,'文化共鸣')
    assert accept(bob,rid).status_code==200
    first=alice.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
               json={'policy':'通商','relation_id':rid})
    assert first.status_code==201
    before=alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['years'][1]
    assert alice.patch(f'/api/fantasy/relations/{rid}',
               json={'action':'withdraw'}).status_code==200
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    assert alice.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
               json={'policy':'开垦','relation_id':rid}).status_code==409
    assert alice.get(f'/api/fantasy/evolution/timelines/{tid}').json()['years'][1]==before
    assert advance(alice,tid,'开垦').status_code==201
    assert bob.patch(f'/api/fantasy/relations/{rid}',json={'action':'withdraw'}).status_code==409


def test_close_world_revokes_consent_and_censors_private_partner_data(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    wa=alice.get('/api/fantasy/worlds?scope=mine').json()['items'][0]['id']
    wb=bob.get('/api/fantasy/worlds?scope=mine').json()['items'][0]['id']
    rid=send(alice,a,b)
    assert accept(bob,rid).status_code==200
    tid=start(alice,a)
    closed=bob.patch(f'/api/fantasy/worlds/{wb}/visibility',json={'visibility':'private'})
    assert closed.status_code==200
    rows=alice.get('/api/fantasy/relations?scope=mine').json()['items']
    assert rows[0]['status']=='withdrawn'
    assert rows[0]['target_name']=='已隐藏的文明'
    assert rows[0]['message'] is None
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    assert alice.get('/api/fantasy/relations/available?timeline_id='+str(tid)).json()['items']==[]
    bob.patch(f'/api/fantasy/worlds/{wb}/visibility',json={'visibility':'public'})
    bob.patch(f'/api/fantasy/council/civilizations/{b}/visibility',
              json={'visibility':'public'})
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    assert alice.post(f'/api/fantasy/evolution/timelines/{tid}/advance',
               json={'policy':'求知','relation_id':rid}).status_code==409


def test_civilization_privacy_revokes_pending_invitation_and_accepted_relations(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    rid=send(alice,a,b)
    bob.patch(f'/api/fantasy/council/civilizations/{b}/visibility',
              json={'visibility':'private'})
    assert accept(bob,rid).status_code==409
    bob.patch(f'/api/fantasy/council/civilizations/{b}/visibility',
              json={'visibility':'public'})
    assert bob.get('/api/fantasy/relations?scope=mine').json()['items'][0]['status']=='withdrawn'
    rid2=send(alice,a,b)
    assert accept(bob,rid2).status_code==200
    alice.patch(f'/api/fantasy/council/civilizations/{a}/visibility',
                json={'visibility':'private'})
    assert bob.get('/api/fantasy/relations?scope=mine').json()['items'][0]['status']=='withdrawn'


def test_world_delete_cascades_and_fork_is_independent(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    wb=bob.get('/api/fantasy/worlds?scope=mine').json()['items'][0]['id']
    rid=send(alice,a,b)
    assert accept(bob,rid).status_code==200
    tid=start(alice,a)
    advance(alice,tid,'守护')
    fork=alice.post(f'/api/fantasy/evolution/timelines/{tid}/fork',
                    json={'name':'另一种命运','year':1}).json()['id']
    with db() as c:
        initial=c.execute('SELECT COUNT(*) FROM fantasy_civilization_relations').fetchone()[0]
        assert initial==1
    bob.delete(f'/api/fantasy/worlds/{wb}')
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM fantasy_civilization_relations').fetchone()[0]==0
    assert alice.get(f'/api/fantasy/evolution/timelines/{fork}').status_code==200


def test_refuse_and_duplicate_rate_limited_without_fake_interactions(lab):
    guest,alice,bob,carol,db=lab
    a,b=make_relation(alice,bob)
    rid=send(alice,a,b)
    assert bob.patch(f'/api/fantasy/relations/{rid}',
           json={'action':'decline'}).status_code==200
    assert guest.get('/api/fantasy/relations').json()['items']==[]
    other=send(alice,a,b)
    assert alice.patch(f'/api/fantasy/relations/{other}',
           json={'action':'withdraw'}).status_code==200
    send(alice,a,b)
    sent=alice.post('/api/fantasy/relations',json=invitation(a,b))
    assert sent.status_code==409
    assert len(guest.get('/api/fantasy/relations').json()['items'])==0
