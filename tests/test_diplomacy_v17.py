"""V17 isolated contract tests: actual FastAPI routers and SQLite permissions.

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


def proposal(a,b,kind='法则碰撞'):
    return {'from_world_id':a,'to_world_id':b,'kind':kind,
            'proposal':'邀请你的史官与我们共同记录两种天律相逢时的星门寓言。'}


def chapter():
    return {'title':'失落的九次日落','story':'星门开启的第九天，造物师带着一本没有封面的典籍，来到边界之上的无人国度。'}


def test_empty_council_does_not_fake_users_or_history(lab):
    guest,alice,bob,_,_=lab
    conf=guest.get('/api/fantasy/council/config')
    assert conf.status_code==200
    assert len(conf.json()['styles'])==6
    assert guest.get('/api/fantasy/council/worlds').json()['public']==[]
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]
    assert guest.get('/api/fantasy/council/encounters?scope=mine').status_code==401


def test_original_civilization_is_private_by_default_and_world_gates_it(lab):
    guest,alice,bob,_,_=lab
    private=alice.post('/api/fantasy/worlds',json=world('沉睡界',visibility='private')).json()['id']
    draft={'world_id':private,'name':'玉京诗史院','capital':'星尘阶','ethos':'任何天律都必须有代价。','style':'星图史官'}
    create=alice.post('/api/fantasy/council/civilizations',json=draft)
    assert create.status_code==201,create.text
    civ=create.json()['id']
    assert bob.get(f'/api/fantasy/council/civilizations/{private}').status_code==404
    assert guest.get(f'/api/fantasy/council/civilizations/{private}').status_code==404
    own=alice.get(f'/api/fantasy/council/civilizations/{private}').json()
    assert own['civilizations'][0]['visibility']=='private'
    assert alice.patch(f'/api/fantasy/council/civilizations/{civ}/visibility',json={'visibility':'public'}).status_code==409
    assert bob.delete(f'/api/fantasy/council/civilizations/{civ}').status_code==404
    alice.patch(f'/api/fantasy/worlds/{private}/visibility',json={'visibility':'public'})
    assert guest.get(f'/api/fantasy/council/civilizations/{private}').json()['civilizations']==[]
    assert alice.patch(f'/api/fantasy/council/civilizations/{civ}/visibility',json={'visibility':'public'}).status_code==200
    visible=guest.get(f'/api/fantasy/council/civilizations/{private}').json()['civilizations']
    assert visible[0]['name']=='玉京诗史院'
    alice.patch(f'/api/fantasy/worlds/{private}/visibility',json={'visibility':'private'})
    assert guest.get(f'/api/fantasy/council/civilizations/{private}').status_code==404


def test_invitation_two_sided_consent_and_fictional_rule_collision(lab):
    guest,alice,bob,carol,_=lab
    a,b=make_pair(alice,bob)
    assert guest.post('/api/fantasy/council/encounters',json=proposal(a,b)).status_code==401
    assert bob.post('/api/fantasy/council/encounters',json=proposal(a,b)).status_code==404
    assert alice.post('/api/fantasy/council/encounters',json=proposal(a,a)).status_code==422
    created=alice.post('/api/fantasy/council/encounters',json=proposal(a,b))
    assert created.status_code==201,created.text
    eid=created.json()['id']
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]
    assert carol.get(f'/api/fantasy/council/encounters/{eid}').status_code==404
    assert alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).status_code==409
    assert alice.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'}).status_code==403
    assert carol.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'}).status_code==403
    accepted=bob.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'})
    assert accepted.status_code==200,accepted.text
    story=accepted.json()['chronicle']
    assert '纯虚构' in story and '九霄炼器庭' in story and '梦潮帝国' in story
    assert '灵气必须守恒' in story and '时间由梦供养' in story
    assert len(guest.get('/api/fantasy/council/encounters').json()['items'])==1
    assert bob.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'}).status_code==409
    assert guest.get(f'/api/fantasy/council/encounters/{eid}').json()['encounter']['chronicle']==story


def test_declined_and_withdrawn_invitations_are_not_public(lab):
    guest,alice,bob,_,_=lab
    a,b=make_pair(alice,bob)
    first=alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).json()['id']
    assert alice.patch(f'/api/fantasy/council/encounters/{first}',json={'action':'withdraw'}).status_code==200
    assert bob.patch(f'/api/fantasy/council/encounters/{first}',json={'action':'accept'}).status_code==409
    second=alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).json()['id']
    assert bob.patch(f'/api/fantasy/council/encounters/{second}',json={'action':'decline'}).status_code==200
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]
    assert guest.get(f'/api/fantasy/council/encounters/{second}').status_code==404
    assert len(alice.get('/api/fantasy/council/encounters?scope=mine').json()['items'])==2


def test_chapters_need_opposite_creator_approval_and_never_autopublish(lab):
    guest,alice,bob,carol,_=lab
    a,b=make_pair(alice,bob)
    eid=alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).json()['id']
    assert bob.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'}).status_code==200
    added=alice.post(f'/api/fantasy/council/encounters/{eid}/chapters',json=chapter())
    assert added.status_code==201,added.text
    cid=added.json()['id']
    assert guest.get(f'/api/fantasy/council/encounters/{eid}').json()['chapters']==[]
    assert alice.get(f'/api/fantasy/council/encounters/{eid}').json()['chapters'][0]['status']=='pending'
    assert alice.patch(f'/api/fantasy/council/chapters/{cid}',json={'action':'approve'}).status_code==403
    assert carol.patch(f'/api/fantasy/council/chapters/{cid}',json={'action':'approve'}).status_code==403
    assert bob.patch(f'/api/fantasy/council/chapters/{cid}',json={'action':'approve'}).status_code==200
    ch=guest.get(f'/api/fantasy/council/encounters/{eid}').json()['chapters']
    assert len(ch)==1 and ch[0]['title']==chapter()['title'] and ch[0]['status']=='approved'
    assert bob.patch(f'/api/fantasy/council/chapters/{cid}',json={'action':'approve'}).status_code==409
    rejected=bob.post(f'/api/fantasy/council/encounters/{eid}/chapters',json=chapter()).json()['id']
    assert alice.patch(f'/api/fantasy/council/chapters/{rejected}',json={'action':'reject'}).status_code==200
    assert len(guest.get(f'/api/fantasy/council/encounters/{eid}').json()['chapters'])==1


def test_private_world_close_hides_every_public_encounter_and_civilization(lab):
    guest,alice,bob,_,_=lab
    a,b=make_pair(alice,bob)
    e=alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).json()['id']
    bob.patch(f'/api/fantasy/council/encounters/{e}',json={'action':'accept'})
    draft={'world_id':a,'name':'三十三重天宫','capital':'金乌台','ethos':'此界一切因果都需要留下证据。','visibility':'public'}
    assert alice.post('/api/fantasy/council/civilizations',json=draft).status_code==201
    alice.patch(f'/api/fantasy/worlds/{a}/visibility',json={'visibility':'private'})
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]
    assert guest.get(f'/api/fantasy/council/encounters/{e}').status_code==404
    assert bob.get(f'/api/fantasy/council/encounters/{e}').status_code==404
    assert guest.get(f'/api/fantasy/council/civilizations/{a}').status_code==404
    assert alice.get(f'/api/fantasy/council/civilizations/{a}').status_code==200
    alice.delete(f'/api/fantasy/worlds/{a}')
    alice.patch(f'/api/fantasy/worlds/{a}/visibility',json={'visibility':'public'})
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]


def test_text_not_interpreted_as_html_and_limits(lab):
    _,alice,bob,_,_=lab
    a,b=make_pair(alice,bob)
    bad=proposal(a,b);bad['proposal']='    '
    assert alice.post('/api/fantasy/council/encounters',json=bad).status_code==422
    draft={'world_id':a,'name':'<script>bad</script>','capital':'云顶','ethos':'所有梦境都有记账规则。'}
    assert alice.post('/api/fantasy/council/civilizations',json=draft).status_code==201
    assert alice.get(f'/api/fantasy/council/civilizations/{a}').json()['civilizations'][0]['name']=='<script>bad</script>'
    # Frontend uses escape(), so this will be visible as literal text, not HTML.
    assert alice.post('/api/fantasy/council/civilizations',json={**draft,'name':'x'}).status_code==422
    assert alice.post('/api/fantasy/council/civilizations',json={**draft,'world_id':b}).status_code==404


def test_reopening_does_not_restore_retired_meeting_or_civilization(lab):
    guest,alice,bob,_,_=lab
    a,b=make_pair(alice,bob)
    cv=alice.post('/api/fantasy/council/civilizations',json={'world_id':a,'name':'星尘游牧庭','capital':'玄镜台','ethos':'每次传递记忆都必须保留一份副本。','visibility':'public'}).json()['id']
    eid=alice.post('/api/fantasy/council/encounters',json=proposal(a,b)).json()['id']
    bob.patch(f'/api/fantasy/council/encounters/{eid}',json={'action':'accept'})
    assert len(guest.get('/api/fantasy/council/encounters').json()['items'])==1
    alice.patch(f'/api/fantasy/worlds/{a}/visibility',json={'visibility':'private'})
    alice.patch(f'/api/fantasy/worlds/{a}/visibility',json={'visibility':'public'})
    assert guest.get('/api/fantasy/council/encounters').json()['items']==[]
    assert guest.get(f'/api/fantasy/council/civilizations/{a}').json()['civilizations']==[]
    own=alice.get(f'/api/fantasy/council/civilizations/{a}').json()['civilizations']
    assert own[0]['id']==cv and own[0]['visibility']=='private'
    assert alice.get('/api/fantasy/council/encounters?scope=mine').json()['items'][0]['status']=='withdrawn'