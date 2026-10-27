"""Original fantasy collection and deterministic relic forge for Wonder Atlas.

Explicit fictional provenance. Never treats stories, artifact ages or supernatural
claims as real-world museum records. User data is isolated by existing session auth.
"""
from __future__ import annotations

from hashlib import sha256
from pydantic import BaseModel, Field
from typing import Literal
from fastapi import Depends, Query

THEMES = {
    '星河仙庭': {'prefix': ('星坠', '九霄', '太虚', '夜航'), 'region': '悬于群星之外的云上仙庭', 'color': '#a5d8ff'},
    '洪荒秘境': {'prefix': ('苍古', '荒渊', '山海', '太初'), 'region': '群山尚有姓名的太古秘境', 'color': '#8ee2ae'},
    '机械修真': {'prefix': ('机魂', '磁霄', '天工', '量子'), 'region': '以机枢代替经脉的铁城', 'color': '#ffa977'},
    '深海龙宫': {'prefix': ('潮生', '龙渊', '沧溟', '月汐'), 'region': '万丈海渊之下的珊瑚王庭', 'color': '#71e0e0'},
    '梦境荒原': {'prefix': ('梦蚀', '无眠', '浮生', '镜渊'), 'region': '所有梦都留下脚印的荒原', 'color': '#c4a5ff'},
    '幽冥古国': {'prefix': ('冥烛', '忘川', '千魂', '黄泉'), 'region': '与时间相背而行的幽冥古国', 'color': '#e4b6e2'},
}
LAWS = {
    '灵气必须守恒': '每一份力量都要由别处归还',
    '记忆可以抵押': '施展神通时，必须舍弃一段珍贵的记忆',
    '因果可被倒写': '每次改变过去，未来便失去一种可能',
    '万物皆能修行': '器物也能拥有意志和自己的道',
    '名字蕴藏真形': '一旦真名被看见，器物便无法再撒谎',
    '时间由梦供养': '梦境越清晰，现实的一瞬便越短',
}
MATERIALS = (
    '星尘', '龙鳞', '玄铁', '月华', '古画', '流沙',
    '雷纹芯片', '千年古玉', '陨石', '昆虫琥珀', '幽海珍珠', '旧日钟表',
    '山海残卷', '机械心脏', '灵木', '冰晶', '青铜铃', '量子光核',
)
RARITIES = ('凡品', '灵器', '地宝', '天器', '禁忌圣物', '传说遗珍')
FORMS = ('命灯', '古剑', '星盘', '机关匣', '回音镜', '命书', '云舟', '玉珏', '灵印', '长琴')
ABILITIES = (
    '将一段失散的光重新引回故乡', '在星空中寻找被遗忘的道路',
    '让无声的金属说出它所经历的往事', '短暂看见另一种可能的人生',
    '记录每一场未曾落下的雨', '让两种互不相容的力量彼此和解',
    '从破碎器物中唤回最后一段回声', '将一瞬间折成可以打开的地图',
    '为迷路的灵魂点亮一扇门', '令古老的歌声化为可见的符文',
)
PRICES = (
    '失去一段关于故乡的记忆', '接下来七夜不能看见月亮',
    '必须替陌生人守护一个秘密', '每使用一次，名字便少一个笔画',
    '下一场雨中会忘记自己的影子', '必须交出一次尚未发生的告别',
    '自己的梦境会被星辰借走一夜', '需要将一件心爱之物还给原主',
)
TABOOS = (
    '不可在黎明时直呼其名', '不可与同源之物相互照见',
    '不可被第三个人同时触碰', '不可在无星的夜晚启动',
    '不可在自己的生辰打开', '不可对未曾许诺的人使用',
    '不可在镜中观看其真形', '不可用于交换真实的生命',
)
FATE_CHOICES = ('守护', '献祭', '封印')
FATE_RESULTS = {
    '守护': ('这件奇物为一座无名之城挡住了夜潮。', '守护使力量趋于稳定，却令守护者背负更漫长的等待。'),
    '献祭': ('奇物放出一道照亮整片天空的光。', '短暂的胜利让世界欠下一笔未来才会偿还的代价。'),
    '封印': ('奇物沉入无人知晓的地脉。', '灾厄暂时止息，但后人必须守住封印的秘密。'),
}
NOTICE = '【纯虚构／原创世界观】故事、能力与年代均为玄幻创作，不是真实馆藏或史实。'


class WorldDraft(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    theme: Literal[tuple(THEMES)] = '星河仙庭'
    law: Literal[tuple(LAWS)] = '灵气必须守恒'
    intro: str = Field(default='', max_length=500)
    visibility: Literal['private', 'public'] = 'private'


class ForgeDraft(BaseModel):
    theme: Literal[tuple(THEMES)] = '星河仙庭'
    law: Literal[tuple(LAWS)] = '灵气必须守恒'
    ingredient_a: Literal[MATERIALS] = '星尘'
    ingredient_b: Literal[MATERIALS] = '龙鳞'
    nonce: int = Field(default=0, ge=0, le=999999)


class ForgedRelic(BaseModel):
    ingredient_a: Literal[MATERIALS]
    ingredient_b: Literal[MATERIALS]
    nonce: int = Field(default=0, ge=0, le=999999)
    inspiration_id: int | None = Field(default=None, ge=1)
    visibility: Literal['private', 'public'] = 'private'


class PublishDraft(BaseModel):
    visibility: Literal['private', 'public']


def forge(draft: ForgeDraft):
    if draft.ingredient_a == draft.ingredient_b:
        raise ValueError('请选两种不同的炼成材料')
    raw = ('|'.join((draft.theme, draft.law, draft.ingredient_a, draft.ingredient_b, str(draft.nonce)))).encode()
    digest = sha256(raw).digest()
    def choice(pool, i):
        return pool[digest[i] % len(pool)]
    title = f"{choice(THEMES[draft.theme]['prefix'],0)}·{choice(FORMS,1)}"
    place = THEMES[draft.theme]['region']
    ability, price, taboo = choice(ABILITIES, 3), choice(PRICES, 4), choice(TABOOS, 5)
    rarity = choice(RARITIES, 2)
    lore = (f'据《{draft.theme}异闻录》所载，铸师曾在{place}寻得「{draft.ingredient_a}」与「{draft.ingredient_b}」。'
            f'二者在「{draft.law}」的天道约束下重铸成{title}。'
            f'传闻此物能{ability}；然而{LAWS[draft.law]}，持有者终将{price}。'
            f'民间流传的禁令是：{taboo}。')
    return {
        'title': title, 'rarity': rarity, 'theme': draft.theme, 'law': draft.law,
        'ingredients': [draft.ingredient_a, draft.ingredient_b],
        'ability': ability, 'price': price, 'taboo': taboo, 'lore': lore,
        'sigil': f'{digest[6]:02x}{digest[7]:02x}{digest[8]:02x}',
        'color': THEMES[draft.theme]['color'],
        'fictional': True, 'notice': NOTICE,
    }


def mount_fantasy(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS fantasy_worlds(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          name TEXT NOT NULL, theme TEXT NOT NULL, law TEXT NOT NULL,
          intro TEXT NOT NULL DEFAULT '', visibility TEXT NOT NULL DEFAULT 'private'
            CHECK (visibility IN ('private','public')),
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_worlds_visible ON fantasy_worlds(visibility,id DESC);
        CREATE TABLE IF NOT EXISTS fantasy_relics(
          id INTEGER PRIMARY KEY,
          world_id INTEGER NOT NULL REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL UNIQUE REFERENCES exhibits(id) ON DELETE CASCADE,
          ingredient_a TEXT NOT NULL, ingredient_b TEXT NOT NULL, nonce INTEGER NOT NULL,
          rank TEXT NOT NULL, ability TEXT NOT NULL, price TEXT NOT NULL,
          taboo TEXT NOT NULL, sigil TEXT NOT NULL,
          inspiration_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_relics_world ON fantasy_relics(world_id,id DESC);
        ''')

    def see_world(c, world_id, user):
        w = c.execute('''SELECT w.*,u.username creator FROM fantasy_worlds w JOIN users u ON u.id=w.user_id WHERE w.id=?''', (world_id,)).fetchone()
        if w is None or (w['visibility'] != 'public' and (not user or user['id'] != w['user_id'])):
            fail(404, '这个世界不存在或尚未开放')
        return w

    def own_world(c, world_id, user):
        w = c.execute('SELECT * FROM fantasy_worlds WHERE id=? AND user_id=?', (world_id, user['id'])).fetchone()
        if not w:
            fail(404, '你没有管理这个世界的权限')
        return w

    def relic_to_dict(row, owner=False):
        info = dict(row)
        info['fictional'] = True
        info['notice'] = NOTICE
        # Only public inspirations can be displayed to non-owners (and never
        # cached into publicly visible text). The foreign-key id is private.
        if not owner and info.get('inspiration_visibility') != 'public':
            info['inspiration_id'] = None
            info['inspiration_title'] = None
        info.pop('inspiration_visibility', None)
        info.pop('user_id', None)
        return info

    def select_relics(c, world_id, is_owner):
        predicate = '' if is_owner else " AND e.visibility='public'"
        return c.execute('''SELECT f.id, f.world_id,f.exhibit_id,f.ingredient_a,f.ingredient_b,
          f.rank,f.ability,f.price,f.taboo,f.sigil,f.inspiration_id,
          e.title,e.description,e.story,e.visibility,e.created_at,
          i.title AS inspiration_title,i.visibility AS inspiration_visibility
          FROM fantasy_relics f JOIN exhibits e ON e.id=f.exhibit_id
          LEFT JOIN exhibits i ON i.id=f.inspiration_id WHERE f.world_id=?'''+predicate+
          ' ORDER BY f.id DESC LIMIT 120', (world_id,)).fetchall()

    @app.get('/api/fantasy/config')
    def config():
        return {'themes': [{'name': k,'region':v['region'],'color':v['color']} for k,v in THEMES.items()],
                'laws': [{'name': k,'description': v} for k,v in LAWS.items()],
                'materials': list(MATERIALS), 'disclaimer': NOTICE}

    @app.post('/api/fantasy/preview')
    def preview(draft: ForgeDraft):
        try:
            return forge(draft)
        except ValueError as e:
            fail(422, str(e))

    @app.post('/api/fantasy/worlds', status_code=201)
    def create_world(draft: WorldDraft, user=Depends(require_user)):
        with db() as c:
            if c.execute('SELECT COUNT(*) FROM fantasy_worlds WHERE user_id=?',(user['id'],)).fetchone()[0] >= 30:
                fail(429,'每个账号最多创建 30 个世界')
            current = now()
            cur=c.execute('''INSERT INTO fantasy_worlds(user_id,name,theme,law,intro,visibility,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)''',(user['id'],draft.name.strip(),draft.theme,draft.law,draft.intro.strip(),draft.visibility,current,current))
            return {'id':cur.lastrowid,'name':draft.name.strip(),'visibility':draft.visibility}

    @app.get('/api/fantasy/worlds')
    def worlds(scope: Literal['public','mine']='public', user=Depends(maybe_user)):
        if scope=='mine' and not user:fail(401,'请登录后查看自己的世界')
        with db() as c:
            cond="w.visibility='public'" if scope=='public' else 'w.user_id=?'
            args=() if scope=='public' else (user['id'],)
            rows=c.execute('''SELECT w.id,w.name,w.theme,w.law,w.intro,w.visibility,
              w.created_at,u.username creator,
              (SELECT COUNT(*) FROM fantasy_relics f JOIN exhibits e ON e.id=f.exhibit_id
                WHERE f.world_id=w.id AND '''+('1=1' if scope=='mine' else "e.visibility='public'")+''') relic_count
              FROM fantasy_worlds w JOIN users u ON u.id=w.user_id
              WHERE '''+cond+' ORDER BY w.id DESC LIMIT 60',args).fetchall()
        return {'items':[dict(x) for x in rows], 'scope':scope, 'fictional':True, 'notice':NOTICE}

    @app.get('/api/fantasy/worlds/{world_id}')
    def world_detail(world_id:int,user=Depends(maybe_user)):
        with db() as c:
            w=see_world(c,world_id,user)
            is_owner=bool(user and user['id']==w['user_id'])
            relics=[relic_to_dict(x,is_owner) for x in select_relics(c,world_id,is_owner)]
        world={k:v for k,v in dict(w).items() if k!='user_id'}
        return {'world':world,'relics':relics,'is_owner':is_owner,'fictional':True,'notice':NOTICE}

    @app.patch('/api/fantasy/worlds/{world_id}/visibility')
    def world_visibility(world_id:int,draft:PublishDraft,user=Depends(require_user)):
        with db() as c:
            own_world(c,world_id,user)
            c.execute('UPDATE fantasy_worlds SET visibility=?,updated_at=? WHERE id=?',(draft.visibility,now(),world_id))
            if draft.visibility=='private':
                c.execute('''UPDATE exhibits SET visibility='private',updated_at=? WHERE id IN
                    (SELECT exhibit_id FROM fantasy_relics WHERE world_id=?)''',(now(),world_id))
                # Revoke every accepted or pending inter-civilization link permanently.
                from relations_api import revoke_world
                revoke_world(c,world_id,now())
                # Withdraw collaboration and civilization publicity on closing a world.
                # Reopening never silently republishes consented content.
                if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_civilizations'").fetchone():
                    c.execute("UPDATE fantasy_civilizations SET visibility='private' WHERE world_id=?", (world_id,))
                # Revocation is persistent: reopening never republishes evolution archives.
                if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_evolution_timelines'").fetchone():
                    c.execute("""UPDATE fantasy_evolution_timelines SET visibility='private'
                        WHERE civilization_id IN (SELECT id FROM fantasy_civilizations WHERE world_id=?)""", (world_id,))
                if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_encounters'").fetchone():
                    c.execute("UPDATE fantasy_encounters SET status='withdrawn',updated_at=? WHERE status IN ('pending','accepted') AND (from_world_id=? OR to_world_id=?)",(now(),world_id,world_id))
        return {'visibility':draft.visibility, 'notice':'世界关闭时已同步隐藏全部奇物；重新开放世界不会自动公开奇物'}

    @app.delete('/api/fantasy/worlds/{world_id}')
    def remove_world(world_id:int,user=Depends(require_user)):
        with db() as c:
            own_world(c,world_id,user)
            # Deleting source exhibits cascades through existing comments/bookmarks;
            # no orphan public fantasy posts should survive removing the world.
            c.execute('DELETE FROM exhibits WHERE id IN (SELECT exhibit_id FROM fantasy_relics WHERE world_id=?)',(world_id,))
            c.execute('DELETE FROM fantasy_worlds WHERE id=?',(world_id,))
        return {'ok':True}

    @app.post('/api/fantasy/worlds/{world_id}/forge', status_code=201)
    def save_relic(world_id:int, draft:ForgedRelic,user=Depends(require_user)):
        with db() as c:
            world=own_world(c,world_id,user)
            count=c.execute('SELECT COUNT(*) FROM fantasy_relics WHERE world_id=?',(world_id,)).fetchone()[0]
            if count>=150:fail(429,'每个世界最多收藏 150 件奇物')
            if draft.visibility=='public' and world['visibility']!='public':
                fail(409,'请先公开这个世界，再公开奇物')
            if draft.inspiration_id is not None:
                source=c.execute('SELECT id,visibility,user_id FROM exhibits WHERE id=?',(draft.inspiration_id,)).fetchone()
                if source is None or (source['visibility']!='public' and source['user_id']!=user['id']):
                    fail(404,'灵感来源不存在或无权访问')
            try:
                result=forge(ForgeDraft(theme=world['theme'],law=world['law'],
                    ingredient_a=draft.ingredient_a,ingredient_b=draft.ingredient_b,nonce=draft.nonce))
            except ValueError as exc:
                fail(422,str(exc))
            current=now()
            info=f"【虚构奇物】{result['ability']}。代价：{result['price']}。"
            story=f"{NOTICE}\n{result['lore']}\n禁忌：{result['taboo']}\n灵感原料：{draft.ingredient_a}、{draft.ingredient_b}。"
            tags=','.join(('虚构','玄幻','世界观设定',draft.ingredient_a,draft.ingredient_b))[:200]
            # Use the same real exhibit system for showcases, comments, galleries
            # and collections; no fake official institution or provenance is added.
            cur=c.execute('''INSERT INTO exhibits(user_id,title,description,story,category,series,domain,
                time_bucket,time_basis,time_note,tags,image_url,source_url,visibility,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                  user['id'],result['title'],info,story,'世界观设定','民间奇趣','原创与个人创作',
                  '时间不详','不详','虚构世界纪年',tags,'','',draft.visibility,current,current))
            c.execute('''INSERT INTO fantasy_relics(world_id,user_id,exhibit_id,ingredient_a,ingredient_b,
                nonce,rank,ability,price,taboo,sigil,inspiration_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                world_id,user['id'],cur.lastrowid,draft.ingredient_a,draft.ingredient_b,draft.nonce,
                result['rarity'],result['ability'],result['price'],result['taboo'],result['sigil'],
                draft.inspiration_id,current))
            return {'id':cur.lastrowid,'exhibit_id':cur.lastrowid,'world_id':world_id,
                    'title':result['title'],'visibility':draft.visibility,'fictional':True}

    @app.patch('/api/fantasy/relics/{exhibit_id}/visibility')
    def relic_visibility(exhibit_id:int,draft:PublishDraft,user=Depends(require_user)):
        with db() as c:
            row=c.execute('''SELECT f.world_id FROM fantasy_relics f
                WHERE f.exhibit_id=? AND f.user_id=?''',(exhibit_id,user['id'])).fetchone()
            if not row:fail(404,'不能管理这件奇物')
            world=own_world(c,row['world_id'],user)
            if draft.visibility=='public' and world['visibility']!='public':
                fail(409,'请先开放整个世界')
            c.execute('UPDATE exhibits SET visibility=?,updated_at=? WHERE id=?', (draft.visibility,now(),exhibit_id))
        return {'visibility':draft.visibility}

    @app.delete('/api/fantasy/relics/{exhibit_id}')
    def remove_relic(exhibit_id:int,user=Depends(require_user)):
        with db() as c:
            row=c.execute('SELECT 1 FROM fantasy_relics WHERE exhibit_id=? AND user_id=?',(exhibit_id,user['id'])).fetchone()
            if not row:fail(404,'不能管理这件奇物')
            c.execute('DELETE FROM exhibits WHERE id=?',(exhibit_id,))
        return {'ok':True}

    @app.get('/api/fantasy/relics/{exhibit_id}/fate')
    def fate(exhibit_id:int,choice:Literal['守护','献祭','封印']=Query('守护'),user=Depends(maybe_user)):
        with db() as c:
            row=c.execute('''SELECT f.sigil,f.ability,f.price,f.taboo,f.world_id,
                w.law,w.visibility world_visibility,e.visibility,e.user_id
                FROM fantasy_relics f JOIN fantasy_worlds w ON w.id=f.world_id
                JOIN exhibits e ON e.id=f.exhibit_id WHERE f.exhibit_id=?''',(exhibit_id,)).fetchone()
            if not row or not (user and user['id']==row['user_id']) and (
                row['visibility']!='public' or row['world_visibility']!='public'):
                fail(404,'不存在或无法查看此奇物')
            idx=sha256((row['sigil']+'|'+choice).encode()).digest()[0]
            opening,outcome=FATE_RESULTS[choice]
            echoes=('余音流入了世间的每口井。','群山因此记住了一个陌生的名字。','天上落下一场倒着飘的雨。')
            return {'choice':choice,'opening':opening,'consequence':outcome,'echo':echoes[idx%len(echoes)],
                    'world_law':row['law'],'fictional':True,'notice':NOTICE}