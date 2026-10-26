"""Wonder Atlas V7: transparent cross-domain journeys.

Three node kinds: curator themes (editorial navigation, not verified evidence),
read-only seeded museum works, and *public* member exhibits. Explanations
specify whether a link was curated, owner-confirmed, or keyword-suggested.
All routes are computed from visible nodes; revoked/private posts are absent.
"""
from __future__ import annotations

import json
from collections import deque, defaultdict
from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from world_museums import _catalog

# Label, category, description, official further-reading link, relevant keywords.
TOPICS = {
 'jewels':('古董珠宝','古代工艺','从冠冕、宝石到装饰品，观察首饰中的工艺与文化。','https://www.metmuseum.org/art/collection',['首饰','珠宝','项链','戒指','宝石','gold','jewelry']),
 'metal':('金属工艺','古代工艺','金属加工是古代器物与现代工程都使用的技术领域。','https://www.metmuseum.org/art/collection',['铠甲','金属','青铜','冶炼','黄金','钢','metal']),
 'materials':('材料科学','现代科技','从材质的微观结构认识现代工程。','https://www.nist.gov/materials-science-and-engineering-division',['材料','合金','半导体材料','material']),
 'chips':('芯片与半导体','现代科技','探索现代电子器件及集成电路。','https://www.computerhistory.org/',['芯片','半导体','集成电路','晶体管','chip','semiconductor']),
 'computing':('计算机历史','现代科技','从早期计算装置通向数字系统。','https://www.computerhistory.org/',['计算机','程序','计算','电脑','computer']),
 'ai':('人工智能','未来世界','探索 AI 模型、算法与当代应用。','https://huggingface.co/',['人工智能','机器学习','ai','模型','神经网络','机器人']),
 'painting':('古老绘画','艺术与文明','用色彩与图像保存时代中的场景。','https://www.artic.edu/collection',['油画','绘画','山水','水彩','painting','浮世绘','版画']),
 'pigments':('颜料与色彩','艺术与文明','研究艺术中的颜料、媒介与颜色。','https://www.nationalgallery.org.uk/',['颜料','色彩','彩绘','点彩','颜色','pigment']),
 'light':('光学与成像','自然科学','从光、色和透镜继续探索图像技术。','https://www.si.edu/spotlight/optics',['光学','透镜','成像','反射','激光','光线','optics']),
 'imaging':('数字图像','现代科技','比较传统图像与现代数字影像技术。','https://www.loc.gov/pictures/',['摄影','图像','数码','照相','digital image']),
 'time':('钟表与计时','古代工艺','人们用不同器具记录时间、测量运动。','https://www.nist.gov/pml/time-and-frequency-division',['钟表','时间','怀表','计时','clock','timekeeping']),
 'measurement':('精密测量','现代科技','测量工具让人类更准确地描述世界。','https://www.nist.gov/',['测量','尺度','计量','精密','measurement']),
 'quantum':('量子科学','未来世界','了解当代量子研究；与古物的联系仅是主题导览。','https://quantum.nist.gov/',['量子','quantum','量子芯片']),
 'navigation':('地图与航海','艺术与文明','人们在不同年代记录方向与空间。','https://www.loc.gov/maps/',['海浪','航海','地图','地图集','地图学','船舶','navigation']),
 'astronomy':('天文观测','自然科学','从早期观测器具看人类理解星空的努力。','https://science.nasa.gov/universe/',['天文','星空','星象','宇宙','望远镜','astronomy']),
 'space':('航天探索','未来世界','探索飞行器与人类的太空研究。','https://science.nasa.gov/',['航天','火箭','宇航','太空','nasa','space']),
 'textile':('纺织与织造','古代工艺','观察织物结构、染色及工艺发展。','https://www.vam.ac.uk/collections/textiles-and-fashion',['纺织','丝织','织物','挂毯','服装','绢本','textile']),
 'algorithm':('编织与算法','现代科技','从重复结构联想到算法与计算规则；属于策展类比。','https://www.computerhistory.org/',['算法','编程','代码','程序','algorithm']),
 'nature':('自然与化石','自然科学','从动植物、化石和生态系统理解自然史。','https://naturalhistory.si.edu/',['自然','蝴蝶','化石','生态','生物','fossil','biology']),
 'biotech':('生物技术','未来世界','从生命研究进入生物工程与技术应用。','https://www.nih.gov/',['生物技术','基因','dna','生物工程','biotech']),
 'manuscripts':('古籍与手稿','艺术与文明','探索知识如何在书籍、文字与绘画中传承。','https://www.loc.gov/collections/',['古籍','书画','文字','手稿','挂轴','册页','book','manuscript']),
 'digital_archive':('数字档案','现代科技','让公开文化资料能被长期整理与检索。','https://www.loc.gov/collections/',['数字化','档案','文献','存档','archive'])
}
# Undirected *editorial thematic* connections; a theme is NOT proof of historical causality.
THEME_EDGES = [
 ('jewels','metal','从宝石镶嵌延伸到金属工艺'),('metal','materials','从传统材料处理到现代材料科学'),
 ('materials','chips','材料性能与半导体元件'),('chips','computing','芯片是现代计算机的重要组件'),
 ('computing','ai','从计算机发展探索人工智能'),('chips','quantum','从经典芯片延伸阅读量子研究'),
 ('painting','pigments','绘画中的颜色与材料'),('pigments','light','从颜色表现探索光学现象'),
 ('light','imaging','光学与图像记录'),('imaging','computing','数字图像与计算技术'),
 ('painting','manuscripts','绘画与书写都可保存文化记忆'),('manuscripts','digital_archive','纸本文献与数字馆藏'),
 ('digital_archive','computing','数字档案通过计算系统组织'),('textile','algorithm','织造规律与算法的策展类比'),
 ('textile','jewels','古代服饰与装饰工艺'),('time','measurement','计时属于测量活动'),
 ('measurement','quantum','当代精密测量与量子研究'),('time','astronomy','早期计时和天文观测的交汇'),
 ('navigation','astronomy','航海定位与天文观测的联系'),('astronomy','space','从观测天体到航天探索'),
 ('nature','biotech','自然科学与生命技术'),('nature','painting','自然也成为绘画题材'),
 ('navigation','painting','海与远方也成为艺术主题'),('biotech','ai','生物研究与计算方法交汇'),
 ('measurement','light','光学也是精密测量的工具'),('metal','time','钟表中的金属机械结构')]
# Curatorial tag labels match the actual preselected museum seeds (not arbitrary online search results).
MUSEUM_THEMES = {
 'met:45434':['painting','navigation'], 'met:438817':['painting','pigments'],
 'met:467642':['textile','jewels'], 'met:11417':['painting','navigation'],
 'met:437881':['painting','light'], 'met:435809':['painting','nature'],
 'met:436535':['painting','nature'], 'met:547855':['pigments','materials'],
 'met:61778':['materials','manuscripts'], 'met:24671':['metal','jewels'],
 'met:53179':['painting','manuscripts'], 'met:553763':['pigments','materials'],
 'aic:27992':['painting','pigments'], 'aic:28560':['painting','light'],
 'aic:16568':['painting','nature'], 'cma:160729':['painting','nature'],
 'cma:130707':['painting','manuscripts']
}

class RouteIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    node_ids: list[str] = Field(min_length=2, max_length=9)


def _add(edges, a, b, reason, kind, *, bidirectional=True):
    if a==b:return
    for p,q in ((a,b),(b,a)) if bidirectional else ((a,b),):
        # If both explicit and inferred exist, keep the strongest attribution.
        rank={'人工确认':3,'策展关联':2,'关键词建议':1}
        old=edges[p].get(q)
        if old is None or rank[kind]>rank[old['kind']]:
            edges[p][q]={'kind':kind,'reason':reason}


def _build(c):
    nodes={};edges=defaultdict(dict)
    for key,(title,category,description,source,keywords) in TOPICS.items():
        nodes['topic:'+key]={'id':'topic:'+key,'kind':'topic','title':title,'category':category,
                            'description':description,'source_url':source,'image_url':'','owner':'策展主题'}
    for seed in _catalog():
        sid=seed['id'];nodes['work:'+sid]={'id':'work:'+sid,'kind':'work','title':seed['title'],
              'category':seed['category'],'description':seed['note'],'source_url':seed['source_url'],
              'image_url':seed['image_url'] if seed.get('open_access') else '',
              'owner':seed['museum'],'artist':seed.get('artist',''),'license':seed.get('license','')}
    # The recommendation corpus is deliberately bounded; private items are excluded by SQL.
    public=c.execute("""SELECT e.id,e.title,e.description,e.tags,e.category,e.source_url,e.image_url,u.username
        FROM exhibits e JOIN users u ON e.user_id=u.id
        WHERE e.visibility='public' ORDER BY e.id DESC LIMIT 400""").fetchall()
    for row in public:
        ident=f'post:{row["id"]}'
        nodes[ident]={'id':ident,'kind':'post','title':row['title'], 'category':row['category'],
            'description':row['description'], 'source_url':row['source_url'],
            'image_url':row['image_url'],'owner':row['username'],'post_id':row['id']}
    for a,b,reason in THEME_EDGES:
        _add(edges,'topic:'+a,'topic:'+b,reason,'策展关联')
    for mid,keys in MUSEUM_THEMES.items():
        wid='work:'+mid
        if wid not in nodes:continue
        for key in keys:
            _add(edges,wid,'topic:'+key,'这件馆藏可作为「'+TOPICS[key][0]+'」的一个观察入口','策展关联')
    for row in public:
        pid=f'post:{row["id"]}'
        haystack=' '.join([row['title'],row['category'],row['tags'] or '']).casefold()
        for key,record in TOPICS.items():
            matched=[x for x in record[4] if len(x)>=2 and x.casefold() in haystack]
            if matched:
                _add(edges,pid,'topic:'+key,'可检索的共同关键词：'+', '.join(matched[:2]),'关键词建议')
    # Only owner-confirmed edges already registered in V3.0; respect source direction.
    for row in c.execute('SELECT source_id,destination_id,relation,reason FROM feature_links').fetchall():
        start=f'post:{row["source_id"]}';dest=f'post:{row["destination_id"]}'
        if start in nodes and dest in nodes:
            _add(edges,start,dest,f"馆主确认的{row['relation']}：{row['reason']}",'人工确认',bidirectional=False)
    return nodes,edges


def _shortest(edges,start,target,max_hops):
    if start==target:return [start]
    queue=deque([(start,[start])]);seen={start}
    while queue:
        node,path=queue.popleft()
        if len(path)>max_hops:continue
        # Prefer confirmed and curated links before machine-suggested ones.
        ranking={'人工确认':3,'策展关联':2,'关键词建议':1}
        for adj,meta in sorted(edges[node].items(),key=lambda t:(-ranking[t[1]['kind']],t[0])):
            if adj in seen:continue
            candidate=path+[adj]
            if adj==target:return candidate
            seen.add(adj)
            queue.append((adj,candidate))
    return None


def _shape(nodes,edges,path):
    items=[nodes[x] for x in path]
    steps=[{'from_id':a,'to_id':b,**edges[a][b]} for a,b in zip(path,path[1:])]
    return {'node_ids':path,'items':items,'steps':steps,'hops':len(steps)}


def mount_atlas(app,db,maybe_user,require_user,now,fail):
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS atlas_saved_routes(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL, node_ids TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(user_id,node_ids));
          CREATE INDEX IF NOT EXISTS ix_atlas_routes_user ON atlas_saved_routes(user_id,created_at DESC);
          ''')

    @app.get('/api/atlas/nodes')
    def nodes_query(q: Annotated[str,Query(max_length=80)]='',kind: Annotated[str,Query(pattern='^(all|topic|work|post)$')]='all'):
        with db() as c: nodes,_=_build(c)
        items=list(nodes.values())
        if kind!='all':items=[x for x in items if x['kind']==kind]
        if q.strip():
            token=q.strip().casefold()
            items=[x for x in items if any(token in str(x.get(k,'')).casefold() for k in ('title','category','owner','description'))]
        return {'items':items[:500],'total':len(items),'limited_public_exhibits':400,
                'notice':'主题关系由策展人员设计；标签关联属于候选提示，不是科学证明。公开投稿仅检索最近400件。'}

    @app.get('/api/atlas/path')
    def path(start:Annotated[str,Query(min_length=3,max_length=100)],
             target:Annotated[str,Query(min_length=3,max_length=100)],
             max_hops:Annotated[int,Query(ge=1,le=8)]=6):
        with db() as c:nodes,edges=_build(c)
        if start not in nodes or target not in nodes:fail(404,'起点或终点不存在，或相关展品已经不再公开')
        p=_shortest(edges,start,target,max_hops)
        if not p:return {'found':False,'start':nodes[start],'target':nodes[target],
                          'message':'在目前公开且可解释的关联中，没有找到限定步数内的路径。不会编造连接。'}
        return {'found':True,**_shape(nodes,edges,p)}

    @app.get('/api/atlas/recommend')
    def recommend(node_id:Annotated[str,Query(min_length=3,max_length=100)]):
        with db() as c:nodes,edges=_build(c)
        if node_id not in nodes:fail(404,'展品不存在，或已经不再公开')
        ranking={'人工确认':3,'策展关联':2,'关键词建议':1}
        matches=sorted(edges[node_id].items(),key=lambda x:(-ranking[x[1]['kind']],x[0]))[:16]
        return {'start':nodes[node_id],'items':[{'node':nodes[x],**meta} for x,meta in matches]}

    @app.get('/api/atlas/featured')
    def featured():
        examples=[('从古代金饰走到芯片','work:met:24671','topic:chips'),
                  ('从古画走到人工智能','work:aic:27992','topic:ai'),
                  ('从海浪走向宇宙','work:met:45434','topic:space'),
                  ('从挂毯想到算法','work:met:467642','topic:algorithm')]
        with db() as c:nodes,edges=_build(c)
        out=[]
        for title,start,target in examples:
            p=_shortest(edges,start,target,8)
            if p:out.append({'title':title,'start':start,'target':target,**_shape(nodes,edges,p)})
        return {'items':out,'note':'路线是主题探索/文化类比，不构成这些事物有直接因果关系的证据。'}

    @app.get('/api/atlas/routes')
    def list_routes(user=Depends(require_user)):
        with db() as c:
            nodes,edges=_build(c)
            saved=c.execute('SELECT * FROM atlas_saved_routes WHERE user_id=? ORDER BY id DESC LIMIT 60',(user['id'],)).fetchall()
            result=[]
            for row in saved:
                path=json.loads(row['node_ids'])
                if any(x not in nodes for x in path):
                    result.append({'id':row['id'],'title':row['title'],'available':False,'created_at':row['created_at']})
                else:
                    # If user content/confirmed links changed, no longer present route edges may disappear.
                    valid=all(b in edges[a] for a,b in zip(path,path[1:]))
                    result.append({'id':row['id'],'title':row['title'],'available':valid,'created_at':row['created_at'],
                                   **(_shape(nodes,edges,path) if valid else {})})
            return {'items':result}

    @app.post('/api/atlas/routes',status_code=201)
    def save_route(payload:RouteIn,user=Depends(require_user)):
        path=payload.node_ids
        if len(path)!=len(set(path)):fail(422,'路线不能重复访问同一站')
        with db() as c:
            nodes,edges=_build(c)
            if any(x not in nodes for x in path):fail(404,'存在已撤回或私密的展品')
            if any(b not in edges[a] for a,b in zip(path,path[1:])):fail(422,'路线包含没有关联依据的跳转')
            count=c.execute('SELECT COUNT(*) FROM atlas_saved_routes WHERE user_id=?',(user['id'],)).fetchone()[0]
            encoded=json.dumps(path,ensure_ascii=False,separators=(',',':'))
            old=c.execute('SELECT id FROM atlas_saved_routes WHERE user_id=? AND node_ids=?',(user['id'],encoded)).fetchone()
            if count>=60 and not old:fail(400,'最多保存60条路线')
            title=payload.title.strip()
            if not title:fail(422,'路线名称不能为空')
            c.execute('''INSERT INTO atlas_saved_routes(user_id,title,node_ids,created_at) VALUES(?,?,?,?)
                ON CONFLICT(user_id,node_ids) DO UPDATE SET title=excluded.title''',(user['id'],title,encoded,now()))
        return {'ok':True,'route':_shape(nodes,edges,path)}

    @app.delete('/api/atlas/routes/{route_id}')
    def delete_route(route_id:int,user=Depends(require_user)):
        with db() as c:
            cur=c.execute('DELETE FROM atlas_saved_routes WHERE id=? AND user_id=?',(route_id,user['id']))
            if not cur.rowcount:fail(404,'没有找到这条路线')
        return {'ok':True}