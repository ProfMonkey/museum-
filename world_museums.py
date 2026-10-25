"""World-famous museum starter collection for Wonder Atlas.

The built-in catalogue is separate from user-generated community posts. Artwork
images are displayed only when the source API explicitly marks them as Public
Domain/Open Access (The Met), public domain (AIC), or CC0 (CMA). The museum
catalogue is read-only; collecting a work copies its metadata into the signed-in
user's own private exhibits and keeps a provenance link.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from fastapi import Depends, Query

CACHE_TTL = 6 * 60 * 60
_cache_lock = threading.Lock()
_refresh_state_lock = threading.Lock()
_refreshing = False
_cache: dict[str, object] = {"at": 0.0, "items": []}

MET_LICENSE = "https://www.metmuseum.org/policies/image-resources"
AIC_LICENSE = "https://api.artic.edu/docs/#images"
CMA_LICENSE = "https://www.clevelandart.org/open-access"

# These are curated seed records, not user posts. Metadata is enriched from each
# museum's own API at runtime; fallback text keeps the catalogue useful offline.
SEEDS = [
    {"id":"met:45434","provider":"met","external_id":"45434","title":"神奈川冲浪里","title_en":"Under the Wave off Kanagawa (The Great Wave)","artist":"葛饰北斋 Katsushika Hokusai","date":"约 1830–1832","medium":"木版画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"亚洲艺术","culture":"日本","source_url":"https://www.metmuseum.org/art/collection/search/45434","license_url":MET_LICENSE,"note":"巨浪与远处富士山形成强烈的尺度对照，是观察构图、节奏与自然力量的绝佳入口。","tags":["日本","浮世绘","木版画","海浪"]},
    {"id":"met:438817","provider":"met","external_id":"438817","title":"舞蹈课","title_en":"The Dance Class","artist":"埃德加·德加 Edgar Degas","date":"1874","medium":"布面油画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"绘画","culture":"法国","source_url":"https://www.metmuseum.org/art/collection/search/438817","license_url":MET_LICENSE,"note":"德加将目光放在芭蕾排练室里：舞者、老师和等待中的人物共同组成了画面。","tags":["法国","印象派","舞蹈","油画"]},
    {"id":"met:467642","provider":"met","external_id":"467642","title":"花园中的独角兽","title_en":"The Unicorn Rests in a Garden","artist":"法国设计、南尼德兰织造 French / South Netherlandish","date":"约 1495–1505","medium":"羊毛、丝、银线与镀金线织挂毯","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"织物与工艺","culture":"法国／南尼德兰","source_url":"https://www.metmuseum.org/art/collection/search/467642","license_url":MET_LICENSE,"note":"这件中世纪挂毯以独角兽为主题，密集的植物、动物和织物细节值得慢慢寻找。","tags":["中世纪","挂毯","神话","工艺"]},
    {"id":"met:11417","provider":"met","external_id":"11417","title":"华盛顿横渡特拉华河","title_en":"Washington Crossing the Delaware","artist":"伊曼纽尔·洛伊策 Emanuel Leutze","date":"1851","medium":"布面油画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"历史艺术","culture":"美国","source_url":"https://www.metmuseum.org/art/collection/search/11417","license_url":MET_LICENSE,"note":"这幅大型历史画以冰冷河面、船只和人物姿态营造出强烈的戏剧性。","tags":["美国","历史","油画","人物"]},
    {"id":"met:437881","provider":"met","external_id":"437881","title":"持水壶的少妇","title_en":"Young Woman with a Water Pitcher","artist":"约翰内斯·维米尔 Johannes Vermeer","date":"约 1662","medium":"布面油画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"绘画","culture":"荷兰","source_url":"https://www.metmuseum.org/art/collection/search/437881","license_url":MET_LICENSE,"note":"维米尔用安静的室内场景表现光线，窗边、器物与人物动作都值得细看。","tags":["荷兰","黄金时代","光线","油画"]},
    {"id":"met:435809","provider":"met","external_id":"435809","title":"收割者","title_en":"The Harvesters","artist":"老彼得·勃鲁盖尔 Pieter Bruegel the Elder","date":"1565","medium":"木板油画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"绘画","culture":"尼德兰","source_url":"https://www.metmuseum.org/art/collection/search/435809","license_url":MET_LICENSE,"note":"乡村劳动、树荫下的休息与远处的风景同时出现，画面像一个可以慢慢阅读的世界。","tags":["尼德兰","风景","日常生活","油画"]},
    {"id":"met:436535","provider":"met","external_id":"436535","title":"麦田与丝柏","title_en":"Wheat Field with Cypresses","artist":"文森特·梵高 Vincent van Gogh","date":"1889","medium":"布面油画","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"绘画","culture":"荷兰／法国","source_url":"https://www.metmuseum.org/art/collection/search/436535","license_url":MET_LICENSE,"note":"梵高用厚重、起伏的笔触表现普罗旺斯的天空、麦田与高耸的丝柏。","tags":["梵高","后印象派","风景","油画"]},
    {"id":"met:547855","provider":"met","external_id":"547855","title":"罗马时期的葬仪面具","title_en":"Funerary Mask","artist":"古代工匠（馆方记录）","date":"约公元 1–4 世纪","medium":"石膏、颜料","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"古代文明","culture":"埃及","source_url":"https://www.metmuseum.org/art/collection/search/547855","license_url":MET_LICENSE,"note":"这件来自埃及的葬仪面具让人看到古代社会如何用肖像与仪式面对死亡。","tags":["埃及","古代文明","葬仪","雕塑"]},
    {"id":"met:61778","provider":"met","external_id":"61778","title":"释迦牟尼佛像","title_en":"Buddha Shakyamuni","artist":"中国工匠（馆方记录）","date":"隋代（581–618）","medium":"大理石雕塑","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"雕塑","culture":"中国","source_url":"https://www.metmuseum.org/art/collection/search/61778","license_url":MET_LICENSE,"note":"隋代大理石佛像，以简洁的体量和姿态呈现早期中国佛教雕塑的面貌。","tags":["中国","隋代","佛教艺术","雕塑"]},
    {"id":"met:24671","provider":"met","external_id":"24671","title":"法国国王亨利二世的铠甲","title_en":"Armor of Henry II, King of France","artist":"让·库桑长者等设计者（馆方记录）","date":"约 1555 年","medium":"钢、金、银、皮革与纺织物","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"武备与工艺","culture":"法国","source_url":"https://www.metmuseum.org/art/collection/search/24671","license_url":MET_LICENSE,"note":"这套礼仪铠甲将金属工艺与密集的装饰图案结合，适合从器物设计角度欣赏。","tags":["法国","铠甲","金属工艺","文艺复兴"]},
    {"id":"met:53179","provider":"met","external_id":"53179","title":"释迦牟尼与菩萨、罗汉图","title_en":"Shaka (Shakyamuni), the Historical Buddha, with Two Attendant Bodhisattvas and Sixteen Arhats","artist":"日本画师（馆方记录）","date":"14 世纪","medium":"绢本挂轴，水墨、色彩与金","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"亚洲艺术","culture":"日本","source_url":"https://www.metmuseum.org/art/collection/search/53179","license_url":MET_LICENSE,"note":"日本佛教绘画以群像与金色细节组织画面，可从人物层次与宗教图像的安排入手。","tags":["日本","佛教艺术","挂轴","绢本"]},
    {"id":"met:553763","provider":"met","external_id":"553763","title":"建筑监工阿蒙霍特普的葬仪面具","title_en":"Funerary Mask of the Overseer of Builders Amenhotep","artist":"古埃及工匠（馆方记录）","date":"约公元前 1427–1386 年","medium":"彩绘纸塑（cartonnage）","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":"古代文明","culture":"古埃及","source_url":"https://www.metmuseum.org/art/collection/search/553763","license_url":MET_LICENSE,"note":"这件新王国时期的葬仪面具保存了古埃及工艺、色彩与丧葬观念的线索。","tags":["古埃及","新王国","葬仪","工艺"]},
    {"id":"aic:27992","provider":"aic","external_id":"27992","title":"大碗岛的星期日下午","title_en":"A Sunday on La Grande Jatte — 1884","artist":"乔治·修拉 Georges Seurat","date":"1884–1886","medium":"布面油画","museum":"芝加哥艺术博物馆","museum_en":"Art Institute of Chicago","category":"绘画","culture":"法国","source_url":"https://www.artic.edu/artworks/27992","license_url":AIC_LICENSE,"note":"修拉用大量细小色点组织公园中的人物与景色，站远一点和凑近看，会得到不同的视觉体验。","tags":["法国","点彩派","公园","油画"]},
    {"id":"aic:28560","provider":"aic","external_id":"28560","title":"卧室","title_en":"The Bedroom","artist":"文森特·梵高 Vincent van Gogh","date":"1889","medium":"布面油画","museum":"芝加哥艺术博物馆","museum_en":"Art Institute of Chicago","category":"绘画","culture":"荷兰／法国","source_url":"https://www.artic.edu/artworks/28560","license_url":AIC_LICENSE,"note":"梵高以鲜明色块和不寻常的透视描绘阿尔勒的卧室，让熟悉的日常空间变得陌生。","tags":["梵高","室内","后印象派","油画"]},
    {"id":"aic:16568","provider":"aic","external_id":"16568","title":"睡莲","title_en":"Water Lilies","artist":"克洛德·莫奈 Claude Monet","date":"1906","medium":"布面油画","museum":"芝加哥艺术博物馆","museum_en":"Art Institute of Chicago","category":"绘画","culture":"法国","source_url":"https://www.artic.edu/artworks/16568","license_url":AIC_LICENSE,"note":"莫奈反复描绘水面与睡莲，把倒影、色彩和光线变成画面的主角。","tags":["莫奈","印象派","睡莲","自然"]},
    {"id":"cma:160729","provider":"cma","external_id":"160729","title":"苞阳湖","title_en":"Baoyang Lake","artist":"宋旭 Song Xu","date":"16 世纪","medium":"绢本设色册页","museum":"克利夫兰艺术博物馆","museum_en":"Cleveland Museum of Art","category":"中国艺术","culture":"中国","source_url":"https://www.clevelandart.org/art/collection/search/160729","license_url":CMA_LICENSE,"note":"中国山水画册页以湖景为题材，可以从山形、留白与水面之间寻找观看节奏。","tags":["中国","山水画","明代","册页"]},
    {"id":"cma:130707","provider":"cma","external_id":"130707","title":"施洗者圣约翰之首","title_en":"Head of Saint John the Baptist","artist":"西班牙或意大利北部艺术家（馆方记录）","date":"约 1550–1650","medium":"布面油画","museum":"克利夫兰艺术博物馆","museum_en":"Cleveland Museum of Art","category":"宗教艺术","culture":"欧洲","source_url":"https://www.clevelandart.org/art/collection/search/130707","license_url":CMA_LICENSE,"note":"这件宗教题材绘画保留了馆方对年代、地域与媒材的研究记录。","tags":["欧洲","宗教艺术","油画","历史"]},
]


def _json(url: str, timeout: float = 3.2):
    req = Request(url, headers={"User-Agent": "WonderAtlas/5.0 (educational open-access collection)", "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("museum API returned a non-200 response")
        return json.loads(response.read().decode("utf-8"))


def _safe_image(url: str, provider: str) -> str:
    if not url or not isinstance(url, str):
        return ""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return ""
    host = parsed.hostname.lower()
    allowed = {
        "met": host == "images.metmuseum.org",
        "aic": host == "www.artic.edu",
        "cma": host.endswith("clevelandart.org"),
    }.get(provider, False)
    return url if allowed else ""


def _fallback(seed: dict) -> dict:
    return {**seed, "image_url": "", "open_access": False, "license": "尚未在线核验；请查看馆方原始记录", "credit_line": "", "department": ""}


def _load_met(seed: dict) -> dict:
    try:
        raw = _json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{seed['external_id']}")
        pd = raw.get("isPublicDomain") is True
        image = _safe_image(raw.get("primaryImageSmall", "") if pd else "", "met")
        title_en = raw.get("title") or seed["title_en"]
        return {**seed, "title_en": title_en, "artist": raw.get("artistDisplayName") or seed["artist"],
                "date": raw.get("objectDate") or seed["date"], "medium": raw.get("medium") or seed["medium"],
                "culture": raw.get("culture") or seed["culture"], "department": raw.get("department") or "",
                "image_url": image, "source_url": raw.get("objectURL") or seed["source_url"],
                "open_access": bool(pd and image), "license": "Public Domain / Open Access" if pd and image else "馆方未将该图像标记为开放访问",
                "credit_line": raw.get("creditLine") or ""}
    except Exception:
        return _fallback(seed)


def _load_aic(seed: dict) -> dict:
    try:
        fields = "id,title,artist_display,date_display,medium_display,department_title,is_public_domain,image_id,web_url,credit_line"
        url = f"https://api.artic.edu/api/v1/artworks/{seed['external_id']}?" + urlencode({"fields": fields})
        raw = _json(url).get("data", {})
        pd = raw.get("is_public_domain") is True
        image_id = raw.get("image_id") if pd else None
        image = _safe_image(f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg" if image_id else "", "aic")
        return {**seed, "title_en": raw.get("title") or seed["title_en"],
                "artist": raw.get("artist_display") or seed["artist"], "date": raw.get("date_display") or seed["date"],
                "medium": raw.get("medium_display") or seed["medium"], "department": raw.get("department_title") or "",
                "image_url": image, "source_url": raw.get("web_url") or seed["source_url"],
                "open_access": bool(pd and image), "license": "Public Domain" if pd and image else "馆方未将该图像标记为公有领域",
                "credit_line": raw.get("credit_line") or ""}
    except Exception:
        return _fallback(seed)


def _load_cma(seed: dict) -> dict:
    try:
        raw = _json(f"https://openaccess-api.clevelandart.org/api/artworks/{seed['external_id']}").get("data", {})
        cc0 = str(raw.get("share_license_status", "")).upper() == "CC0"
        images = raw.get("images") or {}
        image_record = images.get("web") or images.get("print") or {}
        image = _safe_image(image_record.get("url", "") if cc0 else "", "cma")
        creators = raw.get("creators") or []
        artist = ", ".join(x.get("description", "") for x in creators if x.get("description")) or seed["artist"]
        return {**seed, "title_en": raw.get("title") or seed["title_en"], "artist": artist,
                "date": raw.get("creation_date") or seed["date"], "medium": raw.get("technique") or seed["medium"],
                "culture": ", ".join(raw.get("culture") or []) or seed["culture"], "department": raw.get("department") or "",
                "image_url": image, "source_url": raw.get("url") or seed["source_url"],
                "open_access": bool(cc0 and image), "license": "CC0 开放访问" if cc0 and image else "馆方未将该图像标记为 CC0",
                "credit_line": raw.get("creditline") or ""}
    except Exception:
        return _fallback(seed)


def _build_catalog() -> list[dict]:
    loaders = {"met": _load_met, "aic": _load_aic, "cma": _load_cma}
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(loaders[s["provider"]], s): s for s in SEEDS}
        for future in as_completed(futures):
            seed = futures[future]
            try:
                results[seed["id"]] = future.result()
            except Exception:
                results[seed["id"]] = _fallback(seed)
    # Stable curated order regardless of network completion order.
    return [results.get(s["id"], _fallback(s)) for s in SEEDS]


def _refresh_worker():
    global _refreshing
    try:
        items = _build_catalog()
        has_open_images = any(x.get("open_access") and x.get("image_url") for x in items)
        with _cache_lock:
            _cache["items"] = items
            # If all APIs failed, retry after a short cooldown rather than freezing
            # a blank catalogue for six hours.
            _cache["at"] = time.time()  # retry a failed refresh after 60 seconds
    except Exception:
        with _cache_lock:
            _cache["at"] = time.time()  # retry after the short cooldown
    finally:
        with _refresh_state_lock:
            _refreshing = False


def _start_refresh():
    global _refreshing
    with _refresh_state_lock:
        if _refreshing:
            return
        _refreshing = True
    threading.Thread(target=_refresh_worker, name="wonder-museum-refresh", daemon=True).start()


def _catalog() -> list[dict]:
    now = time.time()
    should_refresh = False
    with _cache_lock:
        items = list(_cache["items"])
        age = now - float(_cache["at"])
        if not items:
            items = [_fallback(seed) for seed in SEEDS]
            _cache["items"] = items
            _cache["at"] = now
            should_refresh = True
        elif age >= CACHE_TTL:
            should_refresh = True
        elif not any(x.get("open_access") for x in items) and age > 60:
            should_refresh = True
    if should_refresh:
        _start_refresh()
    return items


def _item_by_id(catalog_id: str):
    return next((x for x in _catalog() if x["id"] == catalog_id), None)


def mount_world_museums(app, db, maybe_user, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS world_museum_imports(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          catalog_id TEXT NOT NULL,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          imported_at TEXT NOT NULL,
          PRIMARY KEY(user_id,catalog_id),
          UNIQUE(user_id,exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_world_museum_imports_user ON world_museum_imports(user_id,imported_at DESC);
        """)

    @app.get("/api/world-museums")
    def world_museum_catalog(q: str = Query("", max_length=120), museum: str = Query("全部", max_length=80), user=Depends(maybe_user)):
        items = _catalog()
        if q.strip():
            needle = q.strip().casefold()
            items = [x for x in items if needle in " ".join(str(x.get(k, "")) for k in ("title", "title_en", "artist", "date", "museum", "culture", "category", "tags")).casefold()]
        if museum and museum != "全部":
            items = [x for x in items if x["museum"] == museum]
        collected = set()
        if user:
            with db() as c:
                collected = {r[0] for r in c.execute("SELECT catalog_id FROM world_museum_imports WHERE user_id=?", (user["id"],)).fetchall()}
        safe_items = []
        for item in items:
            clean = {k:v for k,v in item.items() if k != "tags"}
            clean["tags"] = item.get("tags", [])
            clean["collected"] = item["id"] in collected
            safe_items.append(clean)
        return {"items": safe_items, "total": len(safe_items), "museums": sorted({x["museum"] for x in _catalog()}),
                "online_sources": ["The Met Open Access", "Art Institute of Chicago API", "Cleveland Museum of Art Open Access"],
                "catalog_updated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(float(_cache["at"] or time.time()))),
                "network_fallback": not any(x.get("open_access") for x in _catalog())}

    @app.post("/api/world-museums/{catalog_id}/collect", status_code=201)
    def collect_world_museum_work(catalog_id: str, user=Depends(require_user)):
        item = _item_by_id(catalog_id)
        if not item:
            fail(404, "这件馆藏不在当前精选目录中，请刷新页面后重试")
        with db() as c:
            existing = c.execute("SELECT exhibit_id FROM world_museum_imports WHERE user_id=? AND catalog_id=?", (user["id"], catalog_id)).fetchone()
            if existing:
                row = c.execute("SELECT id FROM exhibits WHERE id=? AND user_id=?", (existing["exhibit_id"], user["id"])).fetchone()
                if row:
                    return {"ok": True, "already_collected": True, "exhibit_id": row["id"], "title": item["title"]}
                c.execute("DELETE FROM world_museum_imports WHERE user_id=? AND catalog_id=?", (user["id"], catalog_id))
            title = str(item.get("title") or item.get("title_en") or "世界名馆馆藏")[:100]
            desc = str(item.get("note") or "来自世界名馆初始典藏。请打开馆方来源了解更多。")[:600]
            tags = ",".join(str(t)[:24] for t in item.get("tags", [])[:12])[:200]
            story = "\n".join([
                f"原文标题：{item.get('title_en','')}", f"作者／创作者：{item.get('artist','')}",
                f"年代：{item.get('date','')}", f"媒材：{item.get('medium','')}",
                f"所属机构：{item.get('museum','')}", f"开放许可状态：{item.get('license','')}",
                f"官方来源：{item.get('source_url','')}", f"许可说明：{item.get('license_url','')}",
                "说明：该副本为个人馆藏记录，图像仍由原馆服务器提供；若原馆调整链接，图片可能无法显示。"
            ])
            cur = c.execute("""INSERT INTO exhibits(user_id,title,description,story,category,tags,image_url,source_url,visibility,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (user["id"], title, desc, story, item.get("category", "艺术"), tags,
                item.get("image_url", ""), item.get("source_url", ""), "private", now(), now()))
            exhibit_id = cur.lastrowid
            c.execute("INSERT INTO world_museum_imports(user_id,catalog_id,exhibit_id,imported_at) VALUES(?,?,?,?)",
                      (user["id"], catalog_id, exhibit_id, now()))
        return {"ok": True, "already_collected": False, "exhibit_id": exhibit_id, "title": title, "visibility": "private"}

    @app.get("/api/world-museums/imported")
    def list_world_museum_imports(user=Depends(require_user)):
        with db() as c:
            rows = c.execute("""SELECT i.catalog_id,i.exhibit_id,i.imported_at,e.title
                FROM world_museum_imports i JOIN exhibits e ON e.id=i.exhibit_id
                WHERE i.user_id=? ORDER BY i.imported_at DESC""", (user["id"],)).fetchall()
            return {"items": [dict(r) for r in rows]}