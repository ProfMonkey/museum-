"""V17: opt-in collaborative fiction between real owners of fictional worlds.

All interactions are deterministic writing prompts, not actual diplomatic or
historical events. No relic transfers, currency, or unilateral cross-world edits.
Each creator must consent before an encounter or chapter becomes public.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator

NOTICE = '【纯虚构／原创联动】以下文明、会盟、规则冲突和年代均属用户虚构世界观。'
KINDS = ('文明会盟', '天道辩论', '异界互市', '法则碰撞')
STYLES = ('星图史官', '山海游牧', '机械城邦', '深海帝国', '梦境行会', '古国秘社')
OUTCOMES = (
    '两界在裂隙边缘发现一座没有归属的灯塔，于是签署互不侵扰的观察约定。',
    '两套律法同时生效时，边界出现短暂的重影；两位史官将此现象封存在共同年历里。',
    '来访者只携带故事与图纸，双方同意用交换记忆的方法保存彼此的语言。',
    '一场没有胜负的辩论改变了星门的颜色，却未改变任何世界原有的法则。',
    '两位馆长决定在边界留下空白碑铭，等待后来的共同创作者书写下一章。',
    '奇物在相遇时彼此共鸣，但所有力量仍受各自世界的第一天律约束。',
)
KIND_OPENINGS = {
    '文明会盟': '使团在两界交汇处建立短暂的会盟庭，讨论彼此世界如何理解承诺。',
    '天道辩论': '两名史官对照各自的第一天律，把分歧写成尚待解答的寓言。',
    '异界互市': '星门下开设只有故事与设计稿的集市，不涉及真实财物或奇物所有权转移。',
    '法则碰撞': '两界法则在想象中的边界相遇，产生一场只存在于虚构年历里的共鸣。',
}


def _strip_value(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError('请填写非空内容')
    return value


class CivilizationDraft(BaseModel):
    world_id: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=50)
    capital: str = Field(min_length=1, max_length=60)
    ethos: str = Field(min_length=4, max_length=250)
    lore: str = Field(default='', max_length=600)
    style: Literal[STYLES] = '星图史官'
    visibility: Literal['private', 'public'] = 'private'

    @field_validator('name', 'capital', 'ethos')
    @classmethod
    def valid_nonempty(cls, value):
        return _strip_value(value)


class VisibilityDraft(BaseModel):
    visibility: Literal['private', 'public']


class EncounterDraft(BaseModel):
    from_world_id: int = Field(ge=1)
    to_world_id: int = Field(ge=1)
    kind: Literal[KINDS] = '文明会盟'
    proposal: str = Field(min_length=8, max_length=450)

    @field_validator('proposal')
    @classmethod
    def valid_proposal(cls, value):
        return _strip_value(value)


class AnswerDraft(BaseModel):
    action: Literal['accept', 'decline', 'withdraw']


class ChapterDraft(BaseModel):
    title: str = Field(min_length=2, max_length=75)
    story: str = Field(min_length=20, max_length=1200)

    @field_validator('title', 'story')
    @classmethod
    def valid_chapter(cls, value):
        return _strip_value(value)


class ChapterAnswer(BaseModel):
    action: Literal['approve', 'reject']


def collision_story(from_world, to_world, kind, encounter_id):
    """A reproducible fiction prompt, not an inference about real history."""
    law_a, law_b = from_world['law'], to_world['law']
    trace = f"{from_world['id']}:{law_a}|{to_world['id']}:{law_b}|{kind}|{encounter_id}"
    idx = sha256(trace.encode('utf-8')).digest()[0] % len(OUTCOMES)
    resonance = ('两界的天律相同，彼此的规则在故事中形成镜像。' if law_a == law_b
                 else f'「{law_a}」与「{law_b}」并未合并；双方各自保留世界的天律。')
    return (f"{NOTICE}\n《{from_world['name']}》与《{to_world['name']}》在虚构星门相遇。"
            f"{KIND_OPENINGS[kind]}{resonance}{OUTCOMES[idx]}")


def mount_diplomacy(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS fantasy_civilizations(
          id INTEGER PRIMARY KEY,
          world_id INTEGER NOT NULL REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          name TEXT NOT NULL, capital TEXT NOT NULL, ethos TEXT NOT NULL,
          lore TEXT NOT NULL DEFAULT '', style TEXT NOT NULL,
          visibility TEXT NOT NULL CHECK(visibility IN ('public','private')) DEFAULT 'private',
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_civilizations_world ON fantasy_civilizations(world_id,id DESC);
        CREATE TABLE IF NOT EXISTS fantasy_encounters(
          id INTEGER PRIMARY KEY,
          from_world_id INTEGER NOT NULL REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          to_world_id INTEGER NOT NULL REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          proposer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          responder_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, proposal TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('pending','accepted','declined','withdrawn')) DEFAULT 'pending',
          chronicle TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          CHECK(from_world_id != to_world_id)
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_encounters_users ON fantasy_encounters(proposer_id,responder_id,status,id DESC);
        CREATE TABLE IF NOT EXISTS fantasy_chapters(
          id INTEGER PRIMARY KEY,
          encounter_id INTEGER NOT NULL REFERENCES fantasy_encounters(id) ON DELETE CASCADE,
          author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL, story TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_chapters_encounter ON fantasy_chapters(encounter_id,id);
        ''')

    def _get_world(c, world_id):
        return c.execute('''SELECT w.*,u.username creator FROM fantasy_worlds w
            JOIN users u ON u.id=w.user_id WHERE w.id=?''', (world_id,)).fetchone()

    def _public_world(c, world_id):
        w = _get_world(c, world_id)
        if not w or w['visibility'] != 'public':
            fail(404, '这个世界未公开或不存在')
        return w

    def _own_world(c, world_id, user):
        w = _get_world(c, world_id)
        if not w or w['user_id'] != user['id']:
            fail(404, '不能管理此世界')
        return w

    def _can_see_world(c, world_id, user):
        w = _get_world(c, world_id)
        if not w or (w['visibility'] != 'public' and (not user or w['user_id'] != user['id'])):
            fail(404, '该世界不存在或尚未公开')
        return w

    def _encounter_join(c, encounter_id):
        return c.execute('''SELECT d.*,a.name from_name,a.law from_law,a.visibility from_visibility,
            b.name to_name,b.law to_law,b.visibility to_visibility,
            pa.username proposer,pb.username responder
            FROM fantasy_encounters d
            JOIN fantasy_worlds a ON a.id=d.from_world_id
            JOIN fantasy_worlds b ON b.id=d.to_world_id
            JOIN users pa ON pa.id=d.proposer_id JOIN users pb ON pb.id=d.responder_id
            WHERE d.id=?''', (encounter_id,)).fetchone()

    def _available(e):
        return bool(e and e['from_visibility']=='public' and e['to_visibility']=='public')

    def _accessible(e,user):
        return _available(e) and (e['status']=='accepted' or
            bool(user and user['id'] in (e['proposer_id'],e['responder_id'])))

    def _public_data(e):
        d = dict(e)
        d.pop('proposer_id',None);d.pop('responder_id',None)
        # Names are only public while BOTH authors still advertise their worlds.
        return {**d, 'fictional':True,'notice':NOTICE}

    def _chapter_data(c, encounter_id, user, allowed_public):
        where = '' if allowed_public else "AND ch.status='approved'"
        rows=c.execute('''SELECT ch.id,ch.title,ch.story,ch.status,ch.created_at,
                u.username author,ch.author_id FROM fantasy_chapters ch
                JOIN users u ON u.id=ch.author_id
                WHERE ch.encounter_id=? '''+where+' ORDER BY ch.id ASC LIMIT 100',(encounter_id,)).fetchall()
        return [dict(id=x['id'],title=x['title'],story=x['story'],status=x['status'],
                     created_at=x['created_at'],author=x['author'],
                     can_respond=bool(allowed_public and user and user['id']!=x['author_id'] and x['status']=='pending'))
                for x in rows]

    @app.get('/api/fantasy/council/config')
    def council_config():
        return {'styles':list(STYLES),'kinds':list(KINDS),'notice':NOTICE,
                'limits':{'civilizations_per_world':6,'pending_invitations':12,'chapters_per_encounter':40}}

    @app.get('/api/fantasy/council/worlds')
    def council_worlds(user=Depends(maybe_user)):
        with db() as c:
            public=c.execute('''SELECT w.id,w.name,w.theme,w.law,u.username creator,w.user_id
                FROM fantasy_worlds w JOIN users u ON u.id=w.user_id
                WHERE w.visibility='public' ORDER BY w.id DESC LIMIT 80''').fetchall()
            mine=c.execute('''SELECT id,name,theme,law,visibility FROM fantasy_worlds
                WHERE user_id=? ORDER BY id DESC LIMIT 30''',(user['id'],)).fetchall() if user else []
        return {'public':[{k:v for k,v in dict(x).items() if k!='user_id'} for x in public],
                'mine':[dict(x) for x in mine], 'fictional':True}

    @app.get('/api/fantasy/council/civilizations/{world_id}')
    def civilizations(world_id:int, user=Depends(maybe_user)):
        with db() as c:
            w=_can_see_world(c,world_id,user)
            owner=bool(user and user['id']==w['user_id'])
            visibility = '' if owner else " AND visibility='public'"
            rows=c.execute('''SELECT id,name,capital,ethos,lore,style,visibility,created_at
                FROM fantasy_civilizations WHERE world_id=? '''+visibility+' ORDER BY id DESC LIMIT 6',(world_id,)).fetchall()
        return {'world':{'id':w['id'],'name':w['name'],'theme':w['theme'],'law':w['law'],
                         'creator':w['creator'],'visibility':w['visibility']},
                'civilizations':[dict(x) for x in rows], 'is_owner':owner,'fictional':True,'notice':NOTICE}

    @app.post('/api/fantasy/council/civilizations', status_code=201)
    def create_civilization(draft:CivilizationDraft, user=Depends(require_user)):
        with db() as c:
            w=_own_world(c,draft.world_id,user)
            if draft.visibility=='public' and w['visibility']!='public':
                fail(409,'公开文明前须先开放世界')
            if c.execute('SELECT COUNT(*) FROM fantasy_civilizations WHERE world_id=?',(draft.world_id,)).fetchone()[0]>=6:
                fail(429,'每个世界最多六种文明')
            at=now()
            cur=c.execute('''INSERT INTO fantasy_civilizations(world_id,user_id,name,capital,ethos,lore,style,visibility,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)''',(w['id'],user['id'],draft.name,draft.capital,draft.ethos,
                                                draft.lore.strip(),draft.style,draft.visibility,at))
        return {'id':cur.lastrowid,'fictional':True,'visibility':draft.visibility}

    @app.patch('/api/fantasy/council/civilizations/{civilization_id}/visibility')
    def civilization_visibility(civilization_id:int,draft:VisibilityDraft,user=Depends(require_user)):
        with db() as c:
            row=c.execute('''SELECT cv.world_id FROM fantasy_civilizations cv
                WHERE cv.id=? AND cv.user_id=?''',(civilization_id,user['id'])).fetchone()
            if not row:fail(404,'无法管理此文明')
            w=_own_world(c,row['world_id'],user)
            if draft.visibility=='public' and w['visibility']!='public':fail(409,'请先开放所属世界')
            c.execute('UPDATE fantasy_civilizations SET visibility=? WHERE id=?',(draft.visibility,civilization_id))
            if draft.visibility=='private':
                from relations_api import revoke_civilization
                revoke_civilization(c,civilization_id,now())
            if draft.visibility=='private' and c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_evolution_timelines'").fetchone():
                # Withdrawing civilization publicity permanently revokes archive shares.
                c.execute("UPDATE fantasy_evolution_timelines SET visibility='private' WHERE civilization_id=?",(civilization_id,))
        return {'visibility':draft.visibility}

    @app.delete('/api/fantasy/council/civilizations/{civilization_id}')
    def delete_civilization(civilization_id:int,user=Depends(require_user)):
        with db() as c:
            row=c.execute('SELECT 1 FROM fantasy_civilizations WHERE id=? AND user_id=?',(civilization_id,user['id'])).fetchone()
            if not row:fail(404,'无法删除此文明')
            c.execute('DELETE FROM fantasy_civilizations WHERE id=?',(civilization_id,))
        return {'ok':True}

    @app.post('/api/fantasy/council/encounters', status_code=201)
    def propose(draft:EncounterDraft,user=Depends(require_user)):
        if draft.from_world_id == draft.to_world_id:fail(422,'不能邀请世界与自己相遇')
        with db() as c:
            source=_own_world(c,draft.from_world_id,user)
            if source['visibility']!='public':fail(409,'请先将自己的世界公开再邀请其他馆长')
            target=_public_world(c,draft.to_world_id)
            if target['user_id']==user['id']:fail(422,'万界会盟需要不同馆长共同创作')
            pending=c.execute("SELECT COUNT(*) FROM fantasy_encounters WHERE proposer_id=? AND status='pending'",(user['id'],)).fetchone()[0]
            if pending>=12:fail(429,'待回应邀请过多，请先等待对方回应')
            total=c.execute('SELECT COUNT(*) FROM fantasy_encounters WHERE proposer_id=?',(user['id'],)).fetchone()[0]
            if total>=150:fail(429,'已达到此账号的会盟邀约总量上限')
            pair_total=c.execute('''SELECT COUNT(*) FROM fantasy_encounters WHERE
                (from_world_id=? AND to_world_id=? OR from_world_id=? AND to_world_id=?)''',
                (source['id'],target['id'],target['id'],source['id'])).fetchone()[0]
            if pair_total>=6:fail(429,'两界之间的邀请过于频繁，请停止重复发送')
            dupe=c.execute('''SELECT id FROM fantasy_encounters WHERE
                (from_world_id=? AND to_world_id=? OR from_world_id=? AND to_world_id=?)
                AND status IN ('pending','accepted')''',(source['id'],target['id'],target['id'],source['id'])).fetchone()
            if dupe:fail(409,'两个世界已存在待回应或已成立的会盟')
            at=now()
            cur=c.execute('''INSERT INTO fantasy_encounters(from_world_id,to_world_id,proposer_id,responder_id,kind,proposal,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)''',(source['id'],target['id'],user['id'],target['user_id'],
                                              draft.kind,draft.proposal,at,at))
        return {'id':cur.lastrowid,'status':'pending','fictional':True,
                'notice':'已发送邀请；只有对方馆长同意后才会成为公开联动故事'}

    @app.get('/api/fantasy/council/encounters')
    def list_encounters(scope:Literal['public','mine']='public', user=Depends(maybe_user)):
        if scope=='mine' and not user:fail(401,'查看邀请需要登录')
        with db() as c:
            criteria=("d.status='accepted'" if scope=='public'
                      else '(d.proposer_id=? OR d.responder_id=?)')
            args=() if scope=='public' else (user['id'],user['id'])
            rows=c.execute('''SELECT d.id,d.from_world_id,d.to_world_id,d.proposer_id,d.responder_id,
                  d.kind,d.proposal,d.status,d.chronicle,d.created_at,d.updated_at,
                  a.name from_name,b.name to_name,a.visibility from_visibility,b.visibility to_visibility,
                  pa.username proposer,pb.username responder
                  FROM fantasy_encounters d
                  JOIN fantasy_worlds a ON a.id=d.from_world_id
                  JOIN fantasy_worlds b ON b.id=d.to_world_id
                  JOIN users pa ON pa.id=d.proposer_id JOIN users pb ON pb.id=d.responder_id
                  WHERE '''+criteria+" AND a.visibility='public' AND b.visibility='public' ORDER BY d.id DESC LIMIT 60",args).fetchall()
        return {'items':[_public_data(x) for x in rows], 'scope':scope,'fictional':True,'notice':NOTICE}

    @app.get('/api/fantasy/council/encounters/{encounter_id}')
    def encounter_detail(encounter_id:int,user=Depends(maybe_user)):
        with db() as c:
            enc=_encounter_join(c,encounter_id)
            if not _accessible(enc,user):fail(404,'会盟不存在或未公开')
            owner=bool(user and user['id'] in (enc['proposer_id'],enc['responder_id']))
            chapters=_chapter_data(c,encounter_id,user,owner)
        return {'encounter':_public_data(enc),'chapters':chapters,'can_write':owner and enc['status']=='accepted',
                'is_proposer':bool(user and user['id']==enc['proposer_id']),
                'is_responder':bool(user and user['id']==enc['responder_id']),
                'notice':NOTICE}

    @app.patch('/api/fantasy/council/encounters/{encounter_id}')
    def respond(encounter_id:int,draft:AnswerDraft,user=Depends(require_user)):
        with db() as c:
            enc=_encounter_join(c,encounter_id)
            if not _available(enc):fail(404,'会盟对应的世界已关闭或不存在')
            if enc['status']!='pending':fail(409,'邀请已处理，不可重复操作')
            if draft.action=='withdraw':
                if enc['proposer_id']!=user['id']:fail(403,'只有邀请者可以撤回')
                status='withdrawn'
            else:
                if enc['responder_id']!=user['id']:fail(403,'只有受邀馆长可以回复')
                status='accepted' if draft.action=='accept' else 'declined'
            story=''
            if status=='accepted':
                a={'id':enc['from_world_id'],'name':enc['from_name'],'law':enc['from_law']}
                b={'id':enc['to_world_id'],'name':enc['to_name'],'law':enc['to_law']}
                story=collision_story(a,b,enc['kind'],enc['id'])
            c.execute('''UPDATE fantasy_encounters SET status=?,chronicle=?,updated_at=?
                WHERE id=? AND status='pending' ''',(status,story,now(),encounter_id))
        return {'status':status,'fictional':True, 'chronicle':story}

    @app.post('/api/fantasy/council/encounters/{encounter_id}/chapters', status_code=201)
    def propose_chapter(encounter_id:int,draft:ChapterDraft,user=Depends(require_user)):
        with db() as c:
            enc=_encounter_join(c,encounter_id)
            if not _accessible(enc,user) or enc['status']!='accepted' or user['id'] not in (enc['proposer_id'],enc['responder_id']):
                fail(404,'无法共同编写此会盟')
            if c.execute('SELECT COUNT(*) FROM fantasy_chapters WHERE encounter_id=?',(encounter_id,)).fetchone()[0]>=40:
                fail(429,'每次会盟最多四十篇共创章节')
            pending=c.execute("SELECT COUNT(*) FROM fantasy_chapters WHERE encounter_id=? AND author_id=? AND status='pending'",(encounter_id,user['id'])).fetchone()[0]
            if pending>=8:fail(429,'你还有太多待审核的章节')
            at=now()
            cur=c.execute('''INSERT INTO fantasy_chapters(encounter_id,author_id,title,story,created_at,updated_at)
                VALUES(?,?,?,?,?,?)''',(encounter_id,user['id'],draft.title,draft.story,at,at))
        return {'id':cur.lastrowid,'status':'pending','fictional':True,
                'notice':'草稿已提交；对方馆长同意后才会展示在公共虚构年历'}

    @app.patch('/api/fantasy/council/chapters/{chapter_id}')
    def approve_chapter(chapter_id:int,draft:ChapterAnswer,user=Depends(require_user)):
        with db() as c:
            row=c.execute('''SELECT ch.*,e.proposer_id,e.responder_id,e.status encounter_status,
                a.visibility from_visibility,b.visibility to_visibility
                FROM fantasy_chapters ch JOIN fantasy_encounters e ON e.id=ch.encounter_id
                JOIN fantasy_worlds a ON a.id=e.from_world_id
                JOIN fantasy_worlds b ON b.id=e.to_world_id WHERE ch.id=?''',(chapter_id,)).fetchone()
            if not row or row['from_visibility']!='public' or row['to_visibility']!='public':
                fail(404,'章节不存在或世界已经关闭')
            if row['encounter_status']!='accepted' or row['status']!='pending':fail(409,'章节已处理')
            if user['id'] not in (row['proposer_id'],row['responder_id']) or row['author_id']==user['id']:
                fail(403,'只有另一位共创馆长可以审核此章节')
            status='approved' if draft.action=='approve' else 'rejected'
            c.execute("UPDATE fantasy_chapters SET status=?,updated_at=? WHERE id=?",(status,now(),chapter_id))
        return {'status':status,'fictional':True}