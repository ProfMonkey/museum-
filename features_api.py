"""Wonder Atlas feature extension: shared, permission-checked multi-user workflows.

V3.0 intentionally builds on the V2 SQLite service. Feature content is not
seeded with fake users. New public content is made by registered users.
"""
from fastapi import Depends
from pydantic import BaseModel, Field
from typing import Literal
from urllib.parse import urlsplit
import json, secrets


class PerspectiveIn(BaseModel):
    angle: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=2, max_length=1500)

class LinkIn(BaseModel):
    destination_id: int
    relation: str = Field(min_length=2, max_length=40)
    reason: str = Field(min_length=4, max_length=300)

class PassportIn(BaseModel):
    origin: str = Field(default='', max_length=200)
    attribution: str = Field(default='', max_length=100)
    license: str = Field(default='未说明', max_length=100)
    note: str = Field(default='', max_length=300)

class CaseIn(BaseModel):
    exhibit_id: int
    question: str = Field(min_length=5, max_length=400)

class ClueIn(BaseModel):
    kind: Literal['evidence','hypothesis']
    body: str = Field(min_length=4, max_length=1000)
    source_url: str = Field(default='', max_length=500)

class StateIn(BaseModel):
    state: Literal['待解答','有线索','待核验','已解决','存争议']
    reason: str = Field(min_length=3, max_length=250)

class EventIn(BaseModel):
    happened_at: str = Field(min_length=4, max_length=32)
    description: str = Field(min_length=4, max_length=800)
    source_url: str = Field(default='', max_length=500)

class ChainIn(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    exhibit_id: int
    reason: str = Field(min_length=4, max_length=300)

class ChainStepIn(BaseModel):
    exhibit_id: int
    reason: str = Field(min_length=4, max_length=300)

class PlaceIn(BaseModel):
    exhibit_id: int
    city: str = Field(min_length=1, max_length=60)
    area: str = Field(default='', max_length=80)
    note: str = Field(default='', max_length=250)

class StoryIn(BaseModel):
    title: str = Field(min_length=2, max_length=90)
    intro: str = Field(default='', max_length=500)
    branches: list[str] = Field(min_length=2, max_length=3)
    endings: list[str] = Field(min_length=2, max_length=3)

class RoomIn(BaseModel):
    exhibit_id: int
    title: str = Field(min_length=2, max_length=80)

class RoomAdvance(BaseModel):
    exhibit_id: int

class RoomChat(BaseModel):
    text: str = Field(min_length=1, max_length=300)


def validate_http_link(v):
    if v and (urlsplit(v).scheme not in ('http','https') or not urlsplit(v).netloc):
        from fastapi import HTTPException
        raise HTTPException(status_code=422,detail='资料来源必须是有效的 http(s) 链接')


def mount_features(app, db, read_exhibit, maybe_user, require_user, now, fail):
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS feature_perspectives(
          id INTEGER PRIMARY KEY,exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          angle TEXT NOT NULL, body TEXT NOT NULL,created_at TEXT NOT NULL,
          UNIQUE(exhibit_id,user_id));
        CREATE TABLE IF NOT EXISTS feature_links(
          id INTEGER PRIMARY KEY,source_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          destination_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          relation TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(source_id,destination_id));
        CREATE TABLE IF NOT EXISTS feature_passports(
          exhibit_id INTEGER PRIMARY KEY REFERENCES exhibits(id) ON DELETE CASCADE,
          origin TEXT NOT NULL DEFAULT '',attribution TEXT NOT NULL DEFAULT '',
          license TEXT NOT NULL DEFAULT '未说明',note TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_passport_revisions(
          id INTEGER PRIMARY KEY,exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          editor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          snapshot TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_cases(
          id INTEGER PRIMARY KEY,exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          question TEXT NOT NULL,state TEXT NOT NULL DEFAULT '待解答',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_clues(
          id INTEGER PRIMARY KEY,case_id INTEGER NOT NULL REFERENCES feature_cases(id) ON DELETE CASCADE,
          author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL,body TEXT NOT NULL,source_url TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_case_history(
          id INTEGER PRIMARY KEY,case_id INTEGER NOT NULL REFERENCES feature_cases(id) ON DELETE CASCADE,
          actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          state TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_events(
          id INTEGER PRIMARY KEY,exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          happened_at TEXT NOT NULL,description TEXT NOT NULL,source_url TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_chains(
          id INTEGER PRIMARY KEY,title TEXT NOT NULL,creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_chain_steps(
          id INTEGER PRIMARY KEY,chain_id INTEGER NOT NULL REFERENCES feature_chains(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          reason TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_places(
          exhibit_id INTEGER PRIMARY KEY REFERENCES exhibits(id) ON DELETE CASCADE,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          city TEXT NOT NULL,area TEXT NOT NULL,note TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_stories(
          id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,intro TEXT NOT NULL,branches TEXT NOT NULL,endings TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_rooms(
          code TEXT PRIMARY KEY,host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feature_room_visits(
          room_code TEXT NOT NULL REFERENCES feature_rooms(code) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          seen_at TEXT NOT NULL,PRIMARY KEY(room_code,user_id));
        CREATE TABLE IF NOT EXISTS feature_room_chat(
          id INTEGER PRIMARY KEY,room_code TEXT NOT NULL REFERENCES feature_rooms(code) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          body TEXT NOT NULL,created_at TEXT NOT NULL);
        ''')

    def obj(c, eid, user=None, public=False):
        item=read_exhibit(c,eid,user)
        if public and item['visibility']!='public': fail(404,'该操作仅支持公开展品')
        return item

    def rows(c, query, args=()):
        return [dict(r) for r in c.execute(query,args).fetchall()]

    @app.get('/api/features/exhibits/{id}/perspectives')
    def perspectives(id:int, user=Depends(maybe_user)):
        with db() as c:
            obj(c,id,user)
            return rows(c,'''SELECT p.*,u.username author FROM feature_perspectives p JOIN users u ON p.user_id=u.id WHERE p.exhibit_id=? ORDER BY p.created_at DESC''',(id,))

    @app.post('/api/features/exhibits/{id}/perspectives')
    def write_perspective(id:int,data:PerspectiveIn,user=Depends(require_user)):
        with db() as c:
            obj(c,id,user,True)
            c.execute('''INSERT INTO feature_perspectives(exhibit_id,user_id,angle,body,created_at)
              VALUES(?,?,?,?,?) ON CONFLICT(exhibit_id,user_id) DO UPDATE SET angle=excluded.angle,body=excluded.body,created_at=excluded.created_at''',(id,user['id'],data.angle,data.text,now()))
        return {'ok':True}

    @app.get('/api/features/wormhole/{id}')
    def wormhole(id:int,user=Depends(maybe_user)):
        with db() as c:
            start=obj(c,id,user)
            explicit=rows(c,'''SELECT l.*,e.title destination_title,u.username owner
              FROM feature_links l JOIN exhibits e ON l.destination_id=e.id JOIN users u ON e.user_id=u.id
              WHERE l.source_id=? AND e.visibility='public' ORDER BY l.id DESC LIMIT 12''',(id,))
            # Suggestions are not claimed as verified links.
            candidates=rows(c,"SELECT id,title,category,tags,user_id FROM exhibits WHERE visibility='public' AND id<>? ORDER BY id DESC LIMIT 200",(id,))
            scored=[]
            for x in candidates:
                if any(e['destination_id']==x['id'] for e in explicit):continue
                shared=set(start['tags']).intersection(set(t for t in x['tags'].split(',') if t))
                rank=2*len(shared)+(1 if x['category']==start['category'] else 0)
                if rank:scored.append({'destination_id':x['id'],'destination_title':x['title'],'relation':'系统候选 · 待确认','reason':'共同标签：'+','.join(sorted(shared)) if shared else '同属'+x['category']+'类别','suggested':True,'rank':rank})
            scored.sort(key=lambda x:(-x['rank'],x['destination_id']))
            return {'start':start,'links':[dict(e,suggested=False) for e in explicit]+scored[:5]}

    @app.post('/api/features/wormhole/{id}/links')
    def link(id:int,data:LinkIn,user=Depends(require_user)):
        if id==data.destination_id:fail(422,'不能将展品关联到自身')
        with db() as c:
            src=obj(c,id,user,True);obj(c,data.destination_id,user,True)
            if src['user_id']!=user['id']:fail(403,'只有原展品馆主能确认关联')
            c.execute('''INSERT INTO feature_links(source_id,destination_id,user_id,relation,reason,created_at) VALUES(?,?,?,?,?,?)
              ON CONFLICT(source_id,destination_id) DO UPDATE SET relation=excluded.relation,reason=excluded.reason''',
              (id,data.destination_id,user['id'],data.relation,data.reason,now()))
        return {'ok':True}

    @app.get('/api/features/exhibits/{id}/passport')
    def passport(id:int,user=Depends(maybe_user)):
        with db() as c:
            item=obj(c,id,user)
            p=c.execute('SELECT * FROM feature_passports WHERE exhibit_id=?',(id,)).fetchone()
            history=rows(c,'SELECT r.id,r.created_at,u.username editor FROM feature_passport_revisions r JOIN users u ON u.id=r.editor_id WHERE exhibit_id=? ORDER BY r.id DESC LIMIT 12',(id,))
            return {'exhibit':item,'passport':dict(p) if p else None,'history':history}

    @app.put('/api/features/exhibits/{id}/passport')
    def update_passport(id:int,data:PassportIn,user=Depends(require_user)):
        with db() as c:
            item=obj(c,id,user)
            if item['user_id']!=user['id']:fail(403,'仅展品馆主可编辑来源')
            c.execute('''INSERT INTO feature_passports(exhibit_id,origin,attribution,license,note,updated_at) VALUES(?,?,?,?,?,?)
              ON CONFLICT(exhibit_id) DO UPDATE SET origin=excluded.origin,attribution=excluded.attribution,license=excluded.license,note=excluded.note,updated_at=excluded.updated_at''',
              (id,data.origin,data.attribution,data.license,data.note,now()))
            c.execute('INSERT INTO feature_passport_revisions(exhibit_id,editor_id,snapshot,created_at) VALUES(?,?,?,?)',
              (id,user['id'],data.model_dump_json(),now()))
        return {'ok':True}

    @app.get('/api/features/cases')
    def cases(user=Depends(maybe_user)):
        with db() as c:
            return rows(c,'''SELECT q.*,e.title exhibit_title,u.username owner,
              (SELECT count(*) FROM feature_clues x WHERE x.case_id=q.id) clue_count
              FROM feature_cases q JOIN exhibits e ON e.id=q.exhibit_id JOIN users u ON q.owner_id=u.id
              WHERE e.visibility='public' ORDER BY q.id DESC LIMIT 40''')

    @app.post('/api/features/cases')
    def create_case(data:CaseIn,user=Depends(require_user)):
        with db() as c:
            exhibit=obj(c,data.exhibit_id,user,True)
            if exhibit['user_id']!=user['id']:fail(403,'只能对自己的公开展品发起悬案')
            cur=c.execute('INSERT INTO feature_cases(exhibit_id,owner_id,question,state,created_at) VALUES(?,?,?,?,?)',
              (data.exhibit_id,user['id'],data.question,'待解答',now()))
            cid=cur.lastrowid
            c.execute('INSERT INTO feature_case_history(case_id,actor_id,state,reason,created_at) VALUES(?,?,?,?,?)',
              (cid,user['id'],'待解答','发起悬案',now()))
        return {'id':cid}

    def get_case(c,cid):
        q=c.execute('''SELECT a.*,e.visibility,e.title exhibit_title FROM feature_cases a
          JOIN exhibits e ON a.exhibit_id=e.id WHERE a.id=? AND e.visibility='public' ''',(cid,)).fetchone()
        if not q:fail(404,'悬案不存在')
        return dict(q)

    @app.get('/api/features/cases/{cid}')
    def case_detail(cid:int):
        with db() as c:
            q=get_case(c,cid)
            q['clues']=rows(c,'''SELECT x.*,u.username author FROM feature_clues x JOIN users u ON u.id=x.author_id WHERE x.case_id=? ORDER BY x.id DESC''',(cid,))
            q['history']=rows(c,'''SELECT h.*,u.username author FROM feature_case_history h JOIN users u ON u.id=h.actor_id WHERE h.case_id=? ORDER BY h.id DESC''',(cid,))
            return q

    @app.post('/api/features/cases/{cid}/clues')
    def add_clue(cid:int,data:ClueIn,user=Depends(require_user)):
        validate_http_link(data.source_url)
        with db() as c:
            get_case(c,cid)
            c.execute('INSERT INTO feature_clues(case_id,author_id,kind,body,source_url,created_at) VALUES(?,?,?,?,?,?)',
              (cid,user['id'],data.kind,data.body,data.source_url,now()))
        return {'ok':True}

    @app.post('/api/features/cases/{cid}/state')
    def change_state(cid:int,data:StateIn,user=Depends(require_user)):
        with db() as c:
            q=get_case(c,cid)
            if q['owner_id']!=user['id']:fail(403,'只有悬案发起人可以变更状态')
            c.execute('UPDATE feature_cases SET state=? WHERE id=?',(data.state,cid))
            c.execute('INSERT INTO feature_case_history(case_id,actor_id,state,reason,created_at) VALUES(?,?,?,?,?)',
              (cid,user['id'],data.state,data.reason,now()))
        return {'ok':True}

    @app.get('/api/features/exhibits/{id}/events')
    def events(id:int,user=Depends(maybe_user)):
        with db() as c:
            obj(c,id,user)
            return rows(c,'''SELECT e.*,u.username author FROM feature_events e JOIN users u ON u.id=e.author_id
              WHERE e.exhibit_id=? ORDER BY e.happened_at ASC,e.id ASC''',(id,))

    @app.post('/api/features/exhibits/{id}/events')
    def create_event(id:int,data:EventIn,user=Depends(require_user)):
        validate_http_link(data.source_url)
        with db() as c:
            obj(c,id,user,True)
            c.execute('INSERT INTO feature_events(exhibit_id,author_id,happened_at,description,source_url,created_at) VALUES(?,?,?,?,?,?)',
              (id,user['id'],data.happened_at,data.description,data.source_url,now()))
        return {'ok':True}

    @app.get('/api/features/chains')
    def chains():
        with db() as c:
            return rows(c,'''SELECT a.*,u.username creator,(SELECT count(*) FROM feature_chain_steps s JOIN exhibits e ON e.id=s.exhibit_id AND e.visibility='public' WHERE s.chain_id=a.id) steps
              FROM feature_chains a JOIN users u ON u.id=a.creator_id
              WHERE EXISTS (SELECT 1 FROM feature_chain_steps s JOIN exhibits e ON e.id=s.exhibit_id AND e.visibility='public' WHERE s.chain_id=a.id)
              ORDER BY a.id DESC LIMIT 40''')

    @app.get('/api/features/chains/{cid}')
    def chain_detail(cid:int):
        with db() as c:
            chain=c.execute('SELECT * FROM feature_chains WHERE id=?',(cid,)).fetchone()
            if not chain:fail(404,'接力不存在')
            steps=rows(c,'''SELECT s.*,e.title,u.username author FROM feature_chain_steps s
             JOIN exhibits e ON e.id=s.exhibit_id AND e.visibility='public' JOIN users u ON u.id=s.author_id
             WHERE s.chain_id=? ORDER BY s.id''',(cid,))
            return {'chain':dict(chain),'steps':steps}

    @app.post('/api/features/chains')
    def create_chain(data:ChainIn,user=Depends(require_user)):
        with db() as c:
            obj(c,data.exhibit_id,user,True)
            cur=c.execute('INSERT INTO feature_chains(title,creator_id,created_at) VALUES(?,?,?)',(data.title,user['id'],now()))
            c.execute('INSERT INTO feature_chain_steps(chain_id,exhibit_id,author_id,reason,created_at) VALUES(?,?,?,?,?)',
              (cur.lastrowid,data.exhibit_id,user['id'],data.reason,now()))
            return {'id':cur.lastrowid}

    @app.post('/api/features/chains/{cid}/steps')
    def append_chain(cid:int,data:ChainStepIn,user=Depends(require_user)):
        with db() as c:
            obj(c,data.exhibit_id,user,True)
            chain=c.execute('SELECT id FROM feature_chains WHERE id=?',(cid,)).fetchone()
            if not chain:fail(404,'接力不存在')
            last=c.execute('SELECT author_id FROM feature_chain_steps WHERE chain_id=? ORDER BY id DESC LIMIT 1',(cid,)).fetchone()
            if last and last['author_id']==user['id']:fail(409,'不能连续两次由同一人接力')
            c.execute('INSERT INTO feature_chain_steps(chain_id,exhibit_id,author_id,reason,created_at) VALUES(?,?,?,?,?)',
              (cid,data.exhibit_id,user['id'],data.reason,now()))
        return {'ok':True}

    @app.get('/api/features/places')
    def places():
        with db() as c:
            return rows(c,'''SELECT p.*,e.title,u.username owner FROM feature_places p JOIN exhibits e ON p.exhibit_id=e.id AND e.visibility='public'
             JOIN users u ON u.id=p.owner_id ORDER BY p.created_at DESC LIMIT 100''')

    @app.post('/api/features/places')
    def put_place(data:PlaceIn,user=Depends(require_user)):
        with db() as c:
            item=obj(c,data.exhibit_id,user,True)
            if item['user_id']!=user['id']:fail(403,'只能为自己的公开展品标注地点')
            c.execute('''INSERT INTO feature_places(exhibit_id,owner_id,city,area,note,created_at) VALUES(?,?,?,?,?,?)
              ON CONFLICT(exhibit_id) DO UPDATE SET city=excluded.city,area=excluded.area,note=excluded.note''',
              (data.exhibit_id,user['id'],data.city,data.area,data.note,now()))
        return {'ok':True}

    @app.get('/api/features/stories')
    def stories():
        with db() as c:
            out=rows(c,'''SELECT s.*,u.username owner FROM feature_stories s JOIN users u ON u.id=s.user_id ORDER BY s.id DESC LIMIT 50''')
            for x in out:
                x['branches']=json.loads(x['branches']);x['endings']=json.loads(x['endings'])
            return out

    @app.post('/api/features/stories')
    def make_story(data:StoryIn,user=Depends(require_user)):
        if len(data.branches)!=len(data.endings):fail(422,'分支与结局数量不匹配')
        if any(not s.strip() or len(s)>220 for s in data.branches+data.endings):fail(422,'分支或结局为空/过长')
        with db() as c:
            cur=c.execute('INSERT INTO feature_stories(user_id,title,intro,branches,endings,created_at) VALUES(?,?,?,?,?,?)',
              (user['id'],data.title,data.intro,json.dumps(data.branches,ensure_ascii=False),json.dumps(data.endings,ensure_ascii=False),now()))
        return {'id':cur.lastrowid}

    def room_check(c,code):
        r=c.execute('''SELECT r.*,u.username host FROM feature_rooms r JOIN users u ON u.id=r.host_id WHERE code=?''',(code,)).fetchone()
        if not r:fail(404,'参观房间不存在')
        x=c.execute('SELECT visibility FROM exhibits WHERE id=?',(r['exhibit_id'],)).fetchone()
        if not x or x['visibility']!='public':fail(404,'参观展品已不可公开')
        return dict(r)

    @app.post('/api/features/rooms')
    def new_room(data:RoomIn,user=Depends(require_user)):
        with db() as c:
            obj(c,data.exhibit_id,user,True)
            code=secrets.token_urlsafe(9)
            c.execute('INSERT INTO feature_rooms(code,host_id,title,exhibit_id,created_at) VALUES(?,?,?,?,?)',(code,user['id'],data.title,data.exhibit_id,now()))
            c.execute('INSERT INTO feature_room_visits(room_code,user_id,seen_at) VALUES(?,?,?)',(code,user['id'],now()))
            return {'code':code}

    @app.get('/api/features/rooms/{code}')
    def room(code:str,user=Depends(require_user)):
        with db() as c:
            r=room_check(c,code)
            c.execute('''INSERT INTO feature_room_visits(room_code,user_id,seen_at) VALUES(?,?,?) ON CONFLICT(room_code,user_id) DO UPDATE SET seen_at=excluded.seen_at''',(code,user['id'],now()))
            r['participants']=rows(c,'''SELECT u.username,v.seen_at FROM feature_room_visits v JOIN users u ON u.id=v.user_id WHERE v.room_code=? ORDER BY v.seen_at DESC LIMIT 40''',(code,))
            r['messages']=rows(c,'''SELECT x.body,x.created_at,u.username author FROM feature_room_chat x JOIN users u ON u.id=x.user_id WHERE x.room_code=? ORDER BY x.id DESC LIMIT 30''',(code,))[::-1]
            e=obj(c,r['exhibit_id'],user,True)
            r['exhibit_title']=e['title']
            return r

    @app.post('/api/features/rooms/{code}/advance')
    def advance_room(code:str,data:RoomAdvance,user=Depends(require_user)):
        with db() as c:
            r=room_check(c,code)
            if r['host_id']!=user['id']:fail(403,'只有主持人可以切换展品')
            obj(c,data.exhibit_id,user,True)
            c.execute('UPDATE feature_rooms SET exhibit_id=? WHERE code=?',(data.exhibit_id,code))
        return {'ok':True}

    @app.post('/api/features/rooms/{code}/chat')
    def chat_room(code:str,data:RoomChat,user=Depends(require_user)):
        with db() as c:
            room_check(c,code)
            c.execute('INSERT INTO feature_room_chat(room_code,user_id,body,created_at) VALUES(?,?,?,?)',(code,user['id'],data.text,now()))
        return {'ok':True}