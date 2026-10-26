"""V15: real public museum journeys through NASA / Library of Congress records.

Each stop is an independent official-catalogue search, not a claim of historical
causation. External failures yield empty results and source links; never invented
items. Image reuse is disabled without per-asset rights verification.
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import date as Date, datetime, timezone
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field

NASA_ENDPOINT = "https://images-api.nasa.gov/search"
LOC_ENDPOINT = "https://www.loc.gov/photos/"
NASA_HOME = "https://images.nasa.gov/"
LOC_HOME = "https://www.loc.gov/photos/"
NASA_POLICY = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
LOC_POLICY = "https://www.loc.gov/free-to-use/"
TTL = 600
FAIL_TTL = 20
MAX_BODY = 1_500_000
_cache = {}
_lock = threading.Lock()
_last_call = {'nasa': 0.0, 'loc': 0.0}
_MIN_GAP = {'nasa': 1.5, 'loc': 3.2}  # under LoC guidance: 20 requests/minute

PROVIDERS = (
    {'id':'loc', 'name':'美国国会图书馆', 'kind':'官方数字照片档案', 'url':LOC_HOME,
     'focus':'电报、早期计算机、工业史、城市、航海地图与历史照片'},
    {'id':'nasa', 'name':'NASA Image and Video Library', 'kind':'官方航天影像目录', 'url':NASA_HOME,
     'focus':'地球观测、天文望远镜、航天器、火星与空间技术'},
)

# A route is an editorial series of searches, not a set of fabricated records.
ROUTES = (
    {'id':'materials','title':'从盔甲到航天器','subtitle':'古代材料工艺 → 工业机具 → 航天工程','icon':'⚙',
     'steps': [('met','armor','古代金属与铠甲'),('loc','industrial machinery','工业时代的机械'),('nasa','spacecraft','现代航天器')]},
    {'id':'vision','title':'从古画到太空摄影','subtitle':'风景绘画 → 航空摄影 → 地球遥感','icon':'◈',
     'steps':[('met','landscape painting','风景绘画'),('loc','aerial photography','航空影像史'),('nasa','Earth from space','太空中的地球')]},
    {'id':'life','title':'从化石到生命星球','subtitle':'古生物 → 现代标本 → 地球生态观测','icon':'✳',
     'steps':[('nhm','fossil','馆藏化石记录'),('nhm','butterfly','现代生物标本'),('nasa','Earth science','地球观测')]},
    {'id':'signals','title':'电报、计算机与深空通信','subtitle':'信息传递方式跨时代对比','icon':'⌘',
     'steps':[('loc','telegraph','电报时代'),('loc','early computers','早期计算机'),('nasa','Deep Space Network','深空通信')]},
    {'id':'optics','title':'从水晶到空间望远镜','subtitle':'自然晶体 → 光学器具 → 太空观测','icon':'◇',
     'steps':[('nhm','quartz','矿物晶体标本'),('loc','optical instruments','历史光学器具'),('nasa','James Webb Space Telescope','现代空间望远镜')]},
    {'id':'cartography','title':'从航海地图到月球地图','subtitle':'人类测绘方法的历史对照','icon':'⌖',
     'steps':[('loc','nautical maps','历史航海地图'),('loc','observatory','天文观测史'),('nasa','Moon mapping','月球测绘')]},
)
PROVIDER_URLS = {
    'met':'https://www.metmuseum.org/art/collection',
    'nhm':'https://data.nhm.ac.uk/dataset/collection-specimens',
    'loc':LOC_HOME,
    'nasa':NASA_HOME,
}


def catalog():
    return {'providers':list(PROVIDERS),
            'routes':[{**{k:v for k,v in route.items() if k != 'steps'},
                       'steps':[{'provider':p,'query':q,'caption':caption,'source_url':PROVIDER_URLS[p]}
                                for p,q,caption in route['steps']]} for route in ROUTES],
            'notice':'每站仅检索馆方真实档案。路线是探索问题而不是历史因果链，来源年、拍摄年与器物制造年不可混淆。'}


def _fetch_json(url: str) -> dict:
    req = Request(url,headers={'Accept':'application/json','User-Agent':'WonderAtlas/15.0 (museum research discovery)'})
    with urlopen(req,timeout=5.5) as res:
        if res.status != 200:
            raise ValueError('source_not_ok')
        raw=res.read(MAX_BODY+1)
        if len(raw)>MAX_BODY:
            raise ValueError('response_too_large')
        data=json.loads(raw.decode('utf-8'))
        if not isinstance(data,dict):
            raise ValueError('invalid_json')
        return data



def dated_bucket(raw_date: str, *, exact_date: bool=False, today: Date|None=None) -> str:
    """Only classify verifiable dates for the photographed/created media asset.

    A year with no month/day cannot safely be called "last 365 days".
    None of these buckets represents a specimen's geological age or an
    invention's original discovery date.
    """
    text=str(raw_date or '').strip()
    today=today or datetime.now(timezone.utc).date()
    if exact_date:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.*)?',text):return '时间不详'
        try:
            when=Date.fromisoformat(text[:10])
        except ValueError:
            return '时间不详'
        days=(today-when).days
        if days<0:return '时间不详'
        if days<=365:return '最近一年'
        years=days/365.2425
    else:
        if not re.fullmatch(r'\d{4}',text):return '时间不详'
        year=int(text)
        if year>today.year or year<1:return '时间不详'
        # A plain year may cover dates more than 365 days ago.
        years=today.year-year
        if years<1:return '时间不详'
    if years<=30:return '近30年'
    if years<=100:return '近现代'
    if years<=1000:return '近千年'
    if years<=10000:return '千年至万年前'
    return '时间不详'

def nasa_record(item: dict) -> dict | None:
    if not isinstance(item,dict) or not isinstance(item.get('data'),list) or not item['data']:
        return None
    raw=item['data'][0]
    if not isinstance(raw,dict) or raw.get('media_type') != 'image':
        return None
    id_=str(raw.get('nasa_id') or '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,100}',id_):
        return None
    title=str(raw.get('title') or '').strip()[:140]
    if not title:
        return None
    date=str(raw.get('date_created') or '')[:19]
    keywords=raw.get('keywords') or []
    if not isinstance(keywords,list):keywords=[]
    return {'id':'nasa:'+id_, 'provider':'nasa', 'title':title,
            'subtitle':str(raw.get('center') or 'NASA 影像馆藏')[:140],
            'museum':'NASA Image and Video Library','category':'航天与宇宙',
            'description':str(raw.get('description_508') or raw.get('description') or '')[:450],
            'source_url':'https://images.nasa.gov/details/'+id_,
            'source_name':'NASA Image and Video Library','source_policy_url':NASA_POLICY,
            'license':'NASA 媒体一般允许教育性使用，个别第三方内容可能有版权；需按作品核查',
            'license_verified_for_image':False,'image_url':'','open_access_image':False,
            'date_note':('NASA 记录日期：'+date+'；不是作品初次发明时间' if date else '未提供明确影像日期'),
            'time_bucket':dated_bucket(date,exact_date=True),
            'time_basis':'制作/创作' if dated_bucket(date,exact_date=True)!='时间不详' else '不详',
            'origin':'official_archive_record','tags':[str(v)[:24] for v in keywords if isinstance(v,str)][:6]}


def loc_record(raw: dict) -> dict | None:
    if not isinstance(raw,dict):return None
    src=str(raw.get('id') or '').strip()
    # The LoC API sometimes returns old http:// URLs. Normalize without following redirects.
    p=urlsplit(src)
    if p.scheme not in ('http','https') or p.hostname!='www.loc.gov':return None
    match=re.fullmatch(r'/item/([\w.-]{3,80})/?',p.path)
    if not match:return None
    id_=match.group(1)
    title=str(raw.get('title') or '').strip()[:140]
    if not title:return None
    date=str(raw.get('date') or '').strip()[:80]
    desc=raw.get('description') or []
    if isinstance(desc,list):desc=' '.join(str(x) for x in desc[:3])
    else:desc=str(desc)
    creator=raw.get('contributor') or raw.get('creator') or []
    if isinstance(creator,list):creator=', '.join(str(x) for x in creator[:2])
    return {'id':'loc:'+id_,'provider':'loc','title':title,
            'subtitle':str(creator or '国会图书馆数字馆藏')[:140],
            'museum':'美国国会图书馆','category':'历史影像与档案',
            'description':desc[:450],
            'source_url':'https://www.loc.gov/item/'+id_+'/',
            'source_name':'Library of Congress','source_policy_url':LOC_POLICY,
            'license':'馆藏图像权利各异：原馆记录可能仍受版权或其他限制；未逐项核验',
            'license_verified_for_image':False,'image_url':'','open_access_image':False,
            'date_note':('馆方编目年代：'+date+'（需查看原记录核验）' if date else '馆方未给出明确年代'),
            'time_bucket':dated_bucket(date),
            'time_basis':'制作/创作' if dated_bucket(date)!='时间不详' else '不详',
            'origin':'official_archive_record','tags':[]}


def search_nasa(q: str, limit: int):
    raw=_fetch_json(NASA_ENDPOINT+'?'+urlencode({'q':q,'media_type':'image','page_size':min(limit,6),'page':1}))
    col=raw.get('collection') or {}
    items=[obj for item in col.get('items',[]) if (obj:=nasa_record(item))]
    return items[:limit],int((col.get('metadata') or {}).get('total_hits') or len(items))


def search_loc(q: str, limit: int):
    raw=_fetch_json(LOC_ENDPOINT+'?'+urlencode({'fo':'json','q':q,'c':min(limit,6),'sp':1}))
    items=[obj for item in raw.get('results',[]) if (obj:=loc_record(item))]
    return items[:limit], int((raw.get('pagination') or {}).get('total') or len(items))


def search(provider: str, q: str, limit: int=6):
    if provider not in ('loc','nasa'):raise ValueError('invalid_provider')
    q=q.strip()
    if not 2<=len(q)<=60:raise ValueError('invalid_query')
    limit=max(1,min(int(limit),6))
    key=(provider,q.casefold(),limit)
    with _lock:
        previous=_cache.get(key)
        if previous and time.monotonic()-previous[0]<(FAIL_TTL if previous[1]['unavailable'] else TTL):
            return {**previous[1],'cached':True}
        # Only one outbound request per provider at a time window. LoC asks <=20/min.
        now_m=time.monotonic()
        if now_m-_last_call[provider] < _MIN_GAP[provider]:
            return {'provider':provider,'query':q,'items':[],'matched_total':0,
                    'unavailable':True,'limited':True,'cached':False,
                    'notice':'馆方请求节流中，请稍后重试，不显示猜测记录。'}
        _last_call[provider]=now_m
    try:
        items,total=(search_nasa(q,limit) if provider=='nasa' else search_loc(q,limit))
        result={'provider':provider,'query':q,'items':items,'matched_total':total,
                'unavailable':False,'limited':False,'cached':False,
                'notice':'真实馆方记录；开放数据不代表全部图片都有自由转载权。'}
    except (OSError,ValueError,TypeError,KeyError,TimeoutError,json.JSONDecodeError):
        result={'provider':provider,'query':q,'items':[],'matched_total':0,
                'unavailable':True,'limited':False,'cached':False,
                'notice':'当前无法访问馆方 API，请在官方目录继续查询；不会填入虚构展品。'}
    with _lock:
        if len(_cache)>=140:_cache.clear()
        _cache[key]=(time.monotonic(),result)
    return result


class SaveRecord(BaseModel):
    record_id: str = Field(min_length=7,max_length=120)


def find_cached(record_id: str):
    with _lock:
        for stamp,response in _cache.values():
            if response['unavailable'] or time.monotonic()-stamp>TTL:continue
            for item in response.get('items',[]):
                if item['id']==record_id:return dict(item)
    return None


def mount_expeditions(app,db,require_user,now):
    @app.get('/api/expeditions/catalog')
    def get_catalog():return catalog()

    @app.get('/api/expeditions/search')
    def query(provider: str=Query(...,pattern='^(nasa|loc)$'),
              q: str=Query(...,min_length=2,max_length=60),
              limit: int=Query(6,ge=1,le=6)):
        return search(provider,q,limit)

    @app.post('/api/expeditions/save',status_code=201)
    def save(payload:SaveRecord,user=Depends(require_user)):
        item=find_cached(payload.record_id)
        if item is None:raise HTTPException(404,'请先重新搜索该馆方记录后再收藏')
        # The cached record was built from an official fixed endpoint; never trust user URLs.
        source=item['source_url']
        is_nasa=item['provider']=='nasa' and re.fullmatch(r'https://images\.nasa\.gov/details/[A-Za-z0-9_-]{3,100}',source)
        is_loc=item['provider']=='loc' and re.fullmatch(r'https://www\.loc\.gov/item/[\w.-]{3,80}/',source)
        if not (is_nasa or is_loc):raise HTTPException(400,'原始档案链接无效')
        domain='天文与航天' if is_nasa else '历史与考古'
        category='航天与宇宙' if is_nasa else '历史文物'
        story='\n'.join([
            '官方来源：'+item['museum'],'档案原网址：'+source,
            '年代说明：'+item['date_note'],'图像权利状态：'+item['license'],
            '元数据索引由用户私人收藏，原始版权仍归各权利人；此处未自动复用图片。',
        ])
        with db() as conn:
            old=conn.execute('SELECT id FROM exhibits WHERE user_id=? AND source_url=?',
                             (user['id'],source)).fetchone()
            if old:return {'already_saved':True,'exhibit_id':old['id'],'visibility':'private'}
            columns={x['name'] for x in conn.execute('PRAGMA table_info(exhibits)')}
            field={'user_id':user['id'],'title':item['title'][:100],
                   'description':item['description'][:600],'story':story[:5000],
                   'category':category,'tags':','.join(item['tags'])[:200],
                   'image_url':'','source_url':source,'visibility':'private',
                   'created_at':now(),'updated_at':now()}
            additional={'series':'藏品系列','domain':domain,'time_bucket':item['time_bucket'],
                        'time_basis':item['time_basis'],'time_note':item['date_note'][:100]}
            field.update({k:v for k,v in additional.items() if k in columns})
            keys=list(field)
            cur=conn.execute('INSERT INTO exhibits('+','.join(keys)+') VALUES('+','.join('?' for _ in keys)+')',
                             [field[k] for k in keys])
            return {'already_saved':False,'exhibit_id':cur.lastrowid,'visibility':'private'}