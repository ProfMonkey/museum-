"""V14: read-only, source-attributed discovery across official museum collections.

Do not confuse specimens' cataloguing/collection year with a fossil's geological age.
Do not proxy or re-host images whose image license has not been verified by source.
Public network calls are bounded, cached, and restricted to fixed official endpoints.
"""
from __future__ import annotations

import json
import re
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import Depends, Query, HTTPException
from pydantic import BaseModel, Field

NHM_RESOURCE = "05ff2255-c38a-40c9-b657-4ccb55ab2feb"
NHM_DATASET = "https://data.nhm.ac.uk/dataset/collection-specimens"
NHM_SPECIMENS_API = "https://data.nhm.ac.uk/is/api/3/action/datastore_search"
MET_SEARCH_API = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
MET_OBJECT_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
MET_IMAGE_PREFIX = "https://images.metmuseum.org/"
CACHE_TTL = 600
_cache: dict[tuple[str, str, int], tuple[float, dict]] = {}
_lock = threading.Lock()

PROVIDERS = (
    {"id": "met", "name": "大都会艺术博物馆", "focus": "古董、珠宝、绘画、古代文明与艺术史",
     "source_url": "https://www.metmuseum.org/art/collection", "status": "official_api_search"},
    {"id": "nhm", "name": "伦敦自然历史博物馆", "focus": "化石、生物标本、矿物、古生物及自然史",
     "source_url": NHM_DATASET, "status": "official_specimen_api_search"},
)

DIRECTORIES = (
    {"name": "英国科学博物馆集团", "theme": "科技史、工业发明、计算机与科学仪器",
     "url": "https://collection.sciencemuseumgroup.org.uk/search/objects", "status": "official_directory_only"},
    {"name": "史密森尼开放访问", "theme": "自然史、航天、技术与文化，公开 API 需要自行申请密钥",
     "url": "https://www.si.edu/openaccess", "status": "official_directory_api_requires_key"},
    {"name": "伦敦自然历史博物馆标本数据门户", "theme": "生物标本与科研记录",
     "url": NHM_DATASET, "status": "official_api_search"},
    {"name": "Science Museum Group：早期计算机磁芯平面", "theme": "1951 年 Whirlwind 计算机的磁芯存储组件；馆方原始档案",
     "url": "https://collection.sciencemuseumgroup.org.uk/objects/co62424/core-plane-from-computer", "status": "verified_official_object_link"},
)

SUGGESTIONS = (
    {"name": "古代珠宝", "query": "necklace", "provider": "met", "note": "黄金首饰、项链和不同文明的装饰工艺"},
    {"name": "古老绘画", "query": "painting", "provider": "met", "note": "绘画、古画与馆方收藏记录"},
    {"name": "机械古董", "query": "clock", "provider": "met", "note": "古老时计、机械器物及工艺"},
    {"name": "恐龙与化石", "query": "fossil", "provider": "nhm", "note": "伦敦自然历史博物馆标本数据；不自动推断地质年龄"},
    {"name": "昆虫与蝴蝶", "query": "butterfly", "provider": "nhm", "note": "馆藏生物标本与物种标签"},
    {"name": "矿物晶体", "query": "quartz", "provider": "nhm", "note": "寻找矿物馆藏记录；部分搜索可能为空"},
)

# Basic aliases only. Do not attempt a full Chinese -> English translation model.
ALIASES = {
    "古董": "antique", "珠宝": "jewelry", "黄金": "gold", "项链": "necklace", "古画": "painting",
    "油画": "oil painting", "玉器": "jade", "盔甲": "armor", "古币": "coin", "瓷器": "porcelain",
    "恐龙": "dinosaur", "化石": "fossil", "蝴蝶": "butterfly", "矿物": "mineral", "石英": "quartz",
    "昆虫": "insect", "海洋": "marine", "鸟类": "bird", "哺乳动物": "mammal",
}


def _fetch_json(url: str) -> dict:
    """Bounded requests to hard-coded API hosts, never user-provided URLs."""
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "WonderAtlasMuseum/14.0 (educational catalogue reader)"})
    with urlopen(request, timeout=4.5) as response:
        if response.status != 200:
            raise ValueError("source_not_ok")
        body = response.read(2_500_001)
        if len(body) > 2_500_000:
            raise ValueError("source_response_too_large")
        parsed = json.loads(body.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("invalid_source_json")
        return parsed


def translate(query: str) -> str:
    clean = query.strip()
    return ALIASES.get(clean, clean)


def safe_nhm_record(r: dict) -> dict | None:
    """Darwin Core museum specimen metadata; source links are verified root only."""
    if not isinstance(r, dict):
        return None
    identifier = str(r.get("_id") or "").strip()
    if not identifier.isdigit():
        return None
    scientific = str(r.get("scientificName") or "").strip()
    common = str(r.get("vernacularName") or "").strip()
    label = scientific or common or "未标注物种的馆藏标本"
    catalog = str(r.get("catalogNumber") or r.get("registrationCode") or "").strip()
    collected = str(r.get("year") or "").strip()
    if collected and not re.fullmatch(r"\d{4}", collected):
        collected = ""
    record_url = f"{NHM_DATASET}/resource/{NHM_RESOURCE}/record/{identifier}/dwc"
    return {
        "id": f"nhm:{identifier}", "provider": "nhm", "title": label[:140],
        "subtitle": (f"藏品编号：{catalog}" if catalog else "自然历史标本"),
        "museum": "伦敦自然历史博物馆", "category": "自然标本",
        "description": " · ".join([s for s in [str(r.get("collectionCode") or ""),str(r.get("family") or ""),str(r.get("basisOfRecord") or "Specimen")] if s])[:400],
        "source_url": record_url, "source_name": "Natural History Museum Data Portal",
        "source_policy_url": NHM_DATASET,
        "license": "CC0-1.0（此标本数据集元数据）；媒体许可需另行核验",
        "license_verified_for_image": False,
        "image_url": "", "open_access_image": False,
        "date_note": (f"标本记录中的采集年份：{collected}（不是化石形成时间）" if collected else "标本年代资料未确认"),
        "time_bucket": "时间不详", "time_basis": "不详",
        "origin": "official_museum_record", "tags": [x for x in [str(r.get('kingdom') or ''),str(r.get('family') or '')] if x][:2],
    }


def safe_met_object(r: dict) -> dict | None:
    if not isinstance(r, dict):
        return None
    object_id = r.get("objectID")
    if not isinstance(object_id, int) or object_id <= 0:
        return None
    image = str(r.get("primaryImageSmall") or "")
    image_open = r.get("isPublicDomain") is True and image.startswith(MET_IMAGE_PREFIX)
    source = f"https://www.metmuseum.org/art/collection/search/{object_id}"
    return {
        "id": f"met:{object_id}", "provider": "met",
        "title": str(r.get("title") or "未命名馆藏作品")[:140],
        "subtitle": str(r.get("artistDisplayName") or r.get("culture") or "馆方未提供创作者")[:140],
        "museum": "大都会艺术博物馆", "category": str(r.get("classification") or "艺术与古董")[:72],
        "description": str(r.get("medium") or r.get("objectName") or "").strip()[:400],
        "source_url": source, "source_name": "The Metropolitan Museum of Art",
        "source_policy_url": "https://www.metmuseum.org/policies/image-resources",
        "license": "Public Domain / Open Access" if image_open else "未核验可公开复用的作品图像",
        "license_verified_for_image": image_open,
        "image_url": image if image_open else "", "open_access_image": image_open,
        "date_note": str(r.get("objectDate") or "馆方未提供年代")[:140],
        "time_bucket": "时间不详", "time_basis": "制作/创作",
        "origin": "official_museum_record", "tags": [],
    }


def search_nhm(query: str, limit: int):
    params = {"resource_id": NHM_RESOURCE, "q": translate(query), "limit": min(limit, 12)}
    data = _fetch_json(NHM_SPECIMENS_API + "?" + urlencode(params))
    if data.get("success") is not True or not isinstance(data.get("result"), dict):
        raise ValueError("nhm_search_failed")
    raw = data["result"]
    results = [x for item in (raw.get("records") or []) if (x := safe_nhm_record(item))]
    return results[:limit], max(0, int(raw.get("total") or len(results)))


def search_met(query: str, limit: int):
    data = _fetch_json(MET_SEARCH_API + "?" + urlencode({"q": translate(query), "limit": min(18, limit * 2), "offset": 0, "hasImages": "true"}))
    ids = [x for x in (data.get("objectIDs") or []) if isinstance(x, int) and 0 < x < 10_000_000][:min(limit, 8)]
    results = []
    # Sequential and bounded: prevent accidental bursts against the museum API.
    for oid in ids:
        try:
            row = safe_met_object(_fetch_json(MET_OBJECT_API + str(oid)))
            if row:
                results.append(row)
        except (ValueError, OSError, TimeoutError, json.JSONDecodeError):
            continue
    return results, max(0, int(data.get("total") or len(results)))


def search_provider(provider: str, query: str, limit: int = 8) -> dict:
    if provider not in ("met", "nhm"):
        raise ValueError("unsupported_provider")
    q = query.strip()
    if not 2 <= len(q) <= 60:
        raise ValueError("invalid_query_length")
    limit = max(1, min(limit, 10))
    key = (provider, q.casefold(), limit)
    with _lock:
        previous = _cache.get(key)
        if previous and time.monotonic() - previous[0] < CACHE_TTL:
            return {**previous[1], "cached": True}
    try:
        items, total = (search_met(q, limit) if provider == "met" else search_nhm(q, limit))
        result = {"provider": provider, "query": q, "items": items, "matched_total": total,
                  "shown": len(items), "unavailable": False, "cached": False,
                  "notice": "馆方数据为外部实时检索；若来源更新或网络不可用，条目数量会变化。"}
    except Exception:
        result = {"provider": provider, "query": q, "items": [], "matched_total": 0,
                  "shown": 0, "unavailable": True, "cached": False,
                  "notice": "馆方 API 当前无法访问；未使用虚构标本填充。可前往馆方官方网站继续查看。"}
    # Avoid caching arbitrary errors for extended periods; cap cache growth.
    with _lock:
        if len(_cache) >= 100:
            _cache.clear()
        _cache[key] = (time.monotonic() - (CACHE_TTL - 20 if result["unavailable"] else 0), result)
    return result


class SaveReference(BaseModel):
    object_id: str = Field(min_length=5, max_length=60)


def _find_cached_result(object_id: str) -> dict | None:
    # Select only previously returned, server-verified museum search records.
    with _lock:
        stamp_now = time.monotonic()
        for key, (stamp, response) in list(_cache.items()):
            if stamp_now - stamp >= CACHE_TTL or response.get('unavailable'):
                continue
            for record in response.get('items', []):
                if record['id'] == object_id:
                    return record.copy()
    return None


def mount_world_sources(app, db=None, require_user=None, now=None, fail=None):
    @app.get("/api/world-sources/providers")
    def list_providers():
        return {"providers": list(PROVIDERS), "directories": list(DIRECTORIES),
                "suggestions": list(SUGGESTIONS),
                "notice": "只有标明 API 搜索的机构才实际接入；史密森尼 API 需要密钥，本版不伪装为已接入。"}

    @app.get("/api/world-sources/search")
    def query_source(provider: str = Query("met", pattern="^(met|nhm)$"),
                     q: str = Query(..., min_length=2, max_length=60),
                     limit: int = Query(8, ge=1, le=10)):
        return search_provider(provider, q, limit)

    if db is not None and require_user is not None:
        @app.post('/api/world-sources/save', status_code=201)
        def save_museum_item(payload: SaveReference, user=Depends(require_user)):
            record = _find_cached_result(payload.object_id)
            if not record:
                raise HTTPException(status_code=404, detail='馆藏条目已过期，请重新查询馆方记录后收藏。')
            source = record['source_url']
            # The original URL was generated from allowlisted museum API metadata.
            if not (source.startswith('https://www.metmuseum.org/art/collection/search/')
                    or source.startswith(NHM_DATASET + '/resource/')):
                raise HTTPException(status_code=400, detail='来源地址不在官方允许列表')
            domain = '自然史与化石' if record['provider'] == 'nhm' else '古董与收藏'
            category = '自然标本' if record['provider'] == 'nhm' else '古董器物'
            story = '\n'.join((
                '馆藏机构：' + record['museum'],
                '馆方原始档案：' + source,
                '年代/采集说明：' + record.get('date_note', ''),
                '图像许可：' + record['license'],
                '这是一份用户私人收藏的馆方记录索引，不代表本站拥有该作品或图片。',
            ))
            with db() as connection:
                prior = connection.execute(
                    'SELECT id FROM exhibits WHERE user_id=? AND source_url=? LIMIT 1',
                    (user['id'], source)).fetchone()
                if prior:
                    return {'already_saved': True, 'exhibit_id': prior['id'], 'visibility': 'private'}
                cur = connection.execute(
                    '''INSERT INTO exhibits
                    (user_id,title,description,story,category,series,domain,time_bucket,time_basis,time_note,
                     tags,image_url,source_url,visibility,created_at,updated_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (user['id'],record['title'][:100],record['description'][:600],story[:5000],
                     category,'藏品系列',domain,'时间不详',record['time_basis'],record['date_note'][:100],
                     ','.join(str(t)[:24] for t in record['tags'])[:200],
                     record['image_url'] if record['license_verified_for_image'] else '',
                     source,'private',now(),now()),
                )
            return {'already_saved': False, 'exhibit_id': cur.lastrowid, 'visibility': 'private'}