"""Wonder Atlas V6: broad museum directory, live curiosity radar, and privacy-minimal product insights.

External sources are links or live metadata only. This module does not scrape pages or
re-host external copyrighted media. Usage analytics store feature/action labels only;
no search queries, exhibit IDs, page text, or IP addresses are stored.
"""
from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator

from world_museums import _json, _load_met, _load_aic, _load_cma, MET_LICENSE, AIC_LICENSE, CMA_LICENSE

MUSEUM_DIRECTORY = [
    # Art, paintings, antiquities and jewellery
    {"id":"met","name":"大都会艺术博物馆","en":"The Metropolitan Museum of Art","group":"绘画、古董与珠宝","url":"https://www.metmuseum.org/art/collection","kind":"开放馆藏 API","note":"跨文明绘画、雕塑、古代器物、珠宝、服饰与武备；提供 CC0 开放数据。"},
    {"id":"louvre","name":"卢浮宫","en":"Musée du Louvre","group":"绘画、古董与珠宝","url":"https://collections.louvre.fr/en/","kind":"官方馆藏目录","note":"绘画、珠宝、钱币、武器、家具、古代器物与雕塑。"},
    {"id":"british","name":"大英博物馆","en":"The British Museum","group":"绘画、古董与珠宝","url":"https://www.britishmuseum.org/collection","kind":"官方馆藏目录","note":"跨越六大洲的考古、历史与文化藏品，可按器物和文明探索。"},
    {"id":"rijks","name":"荷兰国立博物馆","en":"Rijksmuseum","group":"绘画、古董与珠宝","url":"https://www.rijksmuseum.nl/en/collection","kind":"开放数据服务","note":"荷兰黄金时代绘画、装饰艺术与历史器物；提供无 API key 的搜索 API。"},
    {"id":"vam","name":"维多利亚与阿尔伯特博物馆","en":"Victoria and Albert Museum","group":"绘画、古董与珠宝","url":"https://www.vam.ac.uk/collections","kind":"官方在线目录","note":"珠宝、服装、纺织品、家具、摄影、建筑、工艺和现代设计。"},
    {"id":"aic","name":"芝加哥艺术博物馆","en":"Art Institute of Chicago","group":"绘画、古董与珠宝","url":"https://www.artic.edu/collection","kind":"开放馆藏 API","note":"绘画、版画、雕塑与装饰艺术；开放数据中有公有领域图像标记。"},
    {"id":"cma","name":"克利夫兰艺术博物馆","en":"Cleveland Museum of Art","group":"绘画、古董与珠宝","url":"https://www.clevelandart.org/art/collection","kind":"CC0 开放馆藏 API","note":"覆盖全球艺术史的绘画、雕塑、器物与珠宝，提供 CC0 数据与部分图像。"},
    {"id":"moma","name":"纽约现代艺术博物馆","en":"MoMA","group":"现代艺术与设计","url":"https://www.moma.org/collection/","kind":"官方馆藏目录","note":"现代与当代艺术、摄影、建筑、设计、电影与媒体艺术。"},
    {"id":"nga","name":"美国国家美术馆","en":"National Gallery of Art","group":"绘画、古董与珠宝","url":"https://www.nga.gov/collection.html","kind":"官方馆藏目录","note":"欧洲与美国绘画、雕塑、版画及开放数据资源。"},
    {"id":"getty","name":"盖蒂博物馆","en":"Getty Museum","group":"绘画、古董与珠宝","url":"https://www.getty.edu/art/collection/","kind":"官方馆藏目录","note":"欧洲绘画、古代艺术、摄影、手稿与艺术史资料。"},
    {"id":"tate","name":"泰特美术馆","en":"Tate","group":"现代艺术与设计","url":"https://www.tate.org.uk/art","kind":"官方艺术目录","note":"英国艺术、现代与当代艺术、艺术家档案与展览。"},
    {"id":"uffizi","name":"乌菲兹美术馆","en":"Uffizi Galleries","group":"绘画、古董与珠宝","url":"https://www.uffizi.it/en/artworks","kind":"官方艺术目录","note":"文艺复兴绘画、古典雕塑与意大利艺术史。"},
    {"id":"prado","name":"普拉多博物馆","en":"Museo del Prado","group":"绘画、古董与珠宝","url":"https://www.museodelprado.es/en/the-collection","kind":"官方馆藏目录","note":"西班牙与欧洲古典绘画的重要馆藏。"},
    {"id":"orsay","name":"奥赛博物馆","en":"Musée d'Orsay","group":"绘画、古董与珠宝","url":"https://www.musee-orsay.fr/en/collections","kind":"官方馆藏目录","note":"印象派、后印象派、雕塑、摄影与十九世纪艺术。"},
    {"id":"nationalgalleryuk","name":"英国国家美术馆","en":"The National Gallery","group":"绘画、古董与珠宝","url":"https://www.nationalgallery.org.uk/paintings","kind":"官方绘画目录","note":"欧洲绘画史中的经典作品与艺术家资料。"},
    {"id":"vatican","name":"梵蒂冈博物馆","en":"Vatican Museums","group":"绘画、古董与珠宝","url":"https://www.museivaticani.va/content/museivaticani/en/collezioni.html","kind":"官方馆藏目录","note":"古典雕塑、宗教艺术、壁画、地图与历史收藏。"},
    {"id":"smithsonian","name":"史密森尼开放访问","en":"Smithsonian Open Access","group":"综合与数字典藏","url":"https://www.si.edu/openaccess","kind":"开放数据/API","note":"数百万件 2D/3D 数字藏品，包含珠宝、艺术、历史、自然与科技。"},
    {"id":"asianart","name":"史密森尼国家亚洲艺术博物馆","en":"National Museum of Asian Art","group":"亚洲艺术与历史","url":"https://asia.si.edu/explore-art-culture/collections/search/","kind":"官方馆藏目录","note":"中国、日本、韩国、南亚、东南亚、伊斯兰艺术、绘画、玉器与珠宝。"},
    # China and Asia
    {"id":"palacemuseum","name":"故宫博物院","en":"The Palace Museum","group":"亚洲艺术与历史","url":"https://www.dpm.org.cn/","kind":"官方网站","note":"宫廷书画、陶瓷、玉器、钟表、金银器、服饰与古代工艺。"},
    {"id":"chnmuseum","name":"中国国家博物馆","en":"National Museum of China","group":"亚洲艺术与历史","url":"https://en.chnmuseum.cn/","kind":"官方网站","note":"古代中国、钱币、青铜器、服饰、书画、历史与科技专题。"},
    {"id":"shanghai","name":"上海博物馆","en":"Shanghai Museum","group":"亚洲艺术与历史","url":"https://www.shanghaimuseum.net/","kind":"官方网站","note":"中国古代青铜、陶瓷、书画、玉器、钱币与雕塑。"},
    {"id":"sxhm","name":"陕西历史博物馆","en":"Shaanxi History Museum","group":"亚洲艺术与历史","url":"https://www.sxhm.com/","kind":"官方网站","note":"周秦汉唐文物、金银器、壁画、陶俑与丝路历史。"},
    {"id":"hubei","name":"湖北省博物馆","en":"Hubei Provincial Museum","group":"亚洲艺术与历史","url":"https://www.hbww.org/","kind":"官方网站","note":"曾侯乙编钟、楚文化、青铜器、漆木器与古代乐器。"},
    {"id":"geologychina","name":"中国地质博物馆","en":"Geological Museum of China","group":"自然、矿物与化石","url":"https://www.gmc.org.cn/","kind":"官方网站","note":"矿物晶体、宝石、化石、地球历史与地质标本。"},
    {"id":"dunhuang","name":"数字敦煌","en":"Digital Dunhuang","group":"亚洲艺术与历史","url":"https://www.e-dunhuang.com/","kind":"数字化文化遗产","note":"敦煌石窟、壁画、彩塑与可交互的数字文化遗产。"},
    {"id":"mplus","name":"香港 M+ 博物馆","en":"M+ Museum","group":"现代艺术与设计","url":"https://www.mplus.org.hk/en/collection/","kind":"官方馆藏目录","note":"视觉艺术、设计与建筑、影像、流行文化与当代创作。"},
    {"id":"acm","name":"新加坡亚洲文明博物馆","en":"Asian Civilisations Museum","group":"亚洲艺术与历史","url":"https://www.nhb.gov.sg/acm/collections","kind":"官方馆藏目录","note":"亚洲跨文化交流、珠宝、陶瓷、纺织品与贸易历史。"},
    {"id":"nusmuseum","name":"新加坡国立大学博物馆","en":"NUS Museum","group":"亚洲艺术与历史","url":"https://collectionsonline.nus.edu.sg/home","kind":"在线藏品目录","note":"中国书画、古代青铜、玉器、南亚与东南亚艺术。"},
    {"id":"chinascience","name":"中国科学技术馆","en":"China Science and Technology Museum","group":"科技、工程与未来","url":"https://www.cstm.org.cn/","kind":"官方网站","note":"科学展览、工程原理、互动实验与科技教育。"},
    {"id":"shanghaiscience","name":"上海科技馆","en":"Shanghai Science and Technology Museum","group":"科技、工程与未来","url":"https://www.sstm.org.cn/","kind":"官方网站","note":"自然科学、机器人、生态、航天与互动科技展项。"},
    {"id":"museumcn","name":"中博网 · 全球博物馆目录","en":"China Museum Network","group":"博物馆导航与地图","url":"https://exhibition.museum.cn/museum","kind":"博物馆目录","note":"可按地区、类型、性质、特色与费用查找博物馆。"},
    # Natural history, science and technology
    {"id":"nhmuk","name":"伦敦自然历史博物馆","en":"Natural History Museum","group":"自然、矿物与化石","url":"https://www.nhm.ac.uk/discover/collections.html","kind":"官方馆藏目录","note":"恐龙、化石、矿物、动物、植物与地球科学。"},
    {"id":"amnh","name":"美国自然历史博物馆","en":"American Museum of Natural History","group":"自然、矿物与化石","url":"https://www.amnh.org/research/collections","kind":"研究与馆藏目录","note":"恐龙、陨石、古生物、人类学与自然历史标本。"},
    {"id":"smithsoniannatural","name":"史密森尼自然历史博物馆","en":"National Museum of Natural History","group":"自然、矿物与化石","url":"https://naturalhistory.si.edu/collections","kind":"官方馆藏目录","note":"动物、矿物、陨石、化石与自然科学标本。"},
    {"id":"sciencemuseum","name":"英国科学博物馆集团","en":"Science Museum Group Collection","group":"科技、工程与未来","url":"https://collection.sciencemuseumgroup.org.uk/","kind":"在线馆藏目录","note":"科技、工程、医学、交通、通信、媒体与工业史。"},
    {"id":"computerhistory","name":"计算机历史博物馆","en":"Computer History Museum","group":"科技、工程与未来","url":"https://computerhistory.org/collections/","kind":"数字馆藏与档案","note":"计算机、芯片、软件、互联网与个人计算机发展史。"},
    {"id":"deutsches","name":"德意志博物馆","en":"Deutsches Museum","group":"科技、工程与未来","url":"https://www.deutsches-museum.de/en/collections","kind":"官方馆藏目录","note":"工程、航空、能源、交通、通信、天文与科学仪器。"},
    {"id":"tnmoc","name":"英国国家计算博物馆","en":"The National Museum of Computing","group":"科技、工程与未来","url":"https://www.tnmoc.org/","kind":"官方网站","note":"早期计算机、密码破译、计算机体系结构与软件史。"},
    {"id":"eastman","name":"乔治·伊士曼博物馆","en":"George Eastman Museum","group":"摄影、电影与影像","url":"https://www.eastman.org/collections-online","kind":"在线馆藏目录","note":"摄影史、摄影器材、电影与影像技术。"},
    {"id":"mitmuseum","name":"麻省理工学院博物馆","en":"MIT Museum","group":"科技、工程与未来","url":"https://mitmuseum.mit.edu/collections","kind":"官方馆藏目录","note":"工程原型、机器人、科技艺术与创新历史。"},
    {"id":"exploratorium","name":"旧金山探索馆","en":"Exploratorium","group":"科技、工程与未来","url":"https://www.exploratorium.edu/","kind":"互动科学展览","note":"把物理、感知、艺术与交互装置做成可以亲手体验的展品。"},
    {"id":"cern","name":"CERN 科学与粒子物理","en":"CERN","group":"科技、工程与未来","url":"https://home.cern/science","kind":"科学研究与展览","note":"粒子物理、加速器、宇宙起源与大型科学设施。"},
    {"id":"nasaimages","name":"NASA 图像与视频库","en":"NASA Image and Video Library","group":"科技、工程与未来","url":"https://images.nasa.gov/","kind":"官方多媒体搜索/API","note":"航天器、行星、地球、天文与任务影像。"},
    {"id":"esa","name":"欧洲航天局多媒体","en":"ESA Multimedia","group":"科技、工程与未来","url":"https://www.esa.int/ESA_Multimedia/Images","kind":"官方多媒体目录","note":"卫星、空间任务、地球观测与深空图像。"},
    {"id":"jpl","name":"NASA 喷气推进实验室影像","en":"JPL Photojournal","group":"科技、工程与未来","url":"https://photojournal.jpl.nasa.gov/","kind":"官方任务影像","note":"火星、土星、木星、太阳系探测器与行星科学图像。"},
    # Photography, books and digital culture
    {"id":"loc","name":"美国国会图书馆数字馆藏","en":"Library of Congress Digital Collections","group":"摄影、电影与影像","url":"https://www.loc.gov/collections/","kind":"数字图书馆","note":"历史照片、海报、地图、手稿、录音与历史文献。"},
    {"id":"bl","name":"大英图书馆数字资源","en":"British Library","group":"书籍、手稿与档案","url":"https://www.bl.uk/collection-guides","kind":"数字馆藏导航","note":"古籍、手稿、地图、音乐、档案与印刷史。"},
    {"id":"europeana","name":"Europeana 欧洲数字文化遗产","en":"Europeana","group":"书籍、手稿与档案","url":"https://www.europeana.eu/en/collections","kind":"跨机构聚合平台/API","note":"聚合欧洲数千家机构的艺术品、照片、报纸、自然史和 3D 内容。"},
    {"id":"internetarchive","name":"互联网档案馆","en":"Internet Archive","group":"书籍、手稿与档案","url":"https://archive.org/","kind":"数字档案馆","note":"书籍、电影、音频、软件、网页与数字文化记录。"},
    {"id":"googlearts","name":"Google Arts & Culture","en":"Google Arts & Culture","group":"博物馆导航与地图","url":"https://artsandculture.google.com/","kind":"跨馆数字展览","note":"跨博物馆专题展、艺术家故事、超高分辨率作品与虚拟参观。"},
    {"id":"dpla","name":"Digital Public Library of America","en":"DPLA","group":"书籍、手稿与档案","url":"https://dp.la/","kind":"数字文化聚合","note":"美国图书馆、档案馆、博物馆的数字文化遗产。"},
    {"id":"cooperhewitt","name":"库珀·休伊特设计博物馆","en":"Cooper Hewitt Smithsonian Design Museum","group":"现代艺术与设计","url":"https://collection.cooperhewitt.org/","kind":"设计馆藏目录","note":"产品设计、家具、平面设计、装饰艺术与创新物件。"},
    # Live curiosity sources: clearly not museum collections
    {"id":"githubtrending","name":"GitHub Trending","en":"Trending open-source projects","group":"当代流行与新奇","url":"https://github.com/trending","kind":"实时趋势入口","note":"正在受到关注的开源软件、开发工具和新奇项目。"},
    {"id":"huggingface","name":"Hugging Face 热门模型","en":"Hugging Face Trending Models","group":"当代流行与新奇","url":"https://huggingface.co/models?sort=trending","kind":"实时趋势入口","note":"新模型、开源 AI 与机器学习社区项目。"},
    {"id":"hfspaces","name":"Hugging Face Spaces","en":"Interactive AI Demos","group":"当代流行与新奇","url":"https://huggingface.co/spaces?sort=trending","kind":"互动项目入口","note":"可直接体验的 AI 小工具、生成式应用与交互演示。"},
    {"id":"hackernews","name":"Hacker News 热榜","en":"Hacker News","group":"当代流行与新奇","url":"https://news.ycombinator.com/","kind":"实时科技社区","note":"技术、创业、研究与新产品讨论；本站另提供可选实时摘要。"},
    {"id":"producthunt","name":"Product Hunt","en":"New products and launches","group":"当代流行与新奇","url":"https://www.producthunt.com/","kind":"新产品发现","note":"新发布的应用、消费产品、AI 工具与独立开发项目。"},
    {"id":"arxivai","name":"arXiv 人工智能最新论文","en":"arXiv cs.AI recent","group":"当代流行与新奇","url":"https://arxiv.org/list/cs.AI/recent","kind":"科研论文入口","note":"AI、智能体、机器学习与相关研究的最新预印本。"},
]

FEATURES = [
    ("discover", "发现广场", "浏览所有用户公开发布的奇物"),
    ("world_museums", "世界名馆", "浏览开放馆藏与名作"),
    ("museum_directory", "博物馆导航", "从不同机构继续探索"),
    ("tech_radar", "新奇雷达", "科技热榜、AI、航天与奇特发现"),
    ("memories", "回忆剧场", "重看足迹并制作带音乐的影片"),
    ("hall_builder", "个人展厅", "创建展厅、自由布展与沉浸参观"),
    ("random_journey", "随机奇遇", "随机探索未知内容"),
    ("wormhole", "万物虫洞", "沿着藏品关联继续探索"),
    ("mystery_cases", "奇物悬案", "围绕奇物共同提交线索"),
    ("interactive_exhibits", "交互式展览", "分支故事与互动藏品"),
    ("living_monkey", "网页活体猴", "可爱的网页猴子互动"),
    ("collaboration", "多人同行", "共同参观与接力创作"),
    ("personal_world", "个人世界", "建立自己的主题收藏世界"),
    ("perspectives", "不同角度看", "查看同一展品的不同观点"),
    ("timeline", "时光记录", "查看展品的时间变化"),
    ("real_world_museum", "身边的奇物", "记录现实世界的发现"),
    ("tour_guide", "小猴导览", "根据真实公开藏品组织导览"),
    ("interactive_lab", "动手玩展品", "体验参数与模型互动"),
    ("shared_visit", "一起逛博物馆", "多人同步参观与聊天"),
    ("provenance_passport", "藏品来源", "查看来源、署名与修订记录"),
    ("insights", "功能热度", "按真实使用与用户投票决定优先级"),
]
FEATURE_MAP = {x[0]: {"key":x[0], "name":x[1], "description":x[2]} for x in FEATURES}

TECH_LINKS = [
    {"name":"GitHub Trending", "url":"https://github.com/trending", "note":"开源软件与开发工具趋势"},
    {"name":"Hugging Face Models", "url":"https://huggingface.co/models?sort=trending", "note":"新模型与 AI 能力"},
    {"name":"Hugging Face Spaces", "url":"https://huggingface.co/spaces?sort=trending", "note":"可直接玩的 AI 交互演示"},
    {"name":"Product Hunt", "url":"https://www.producthunt.com/", "note":"新产品与独立开发者发布"},
    {"name":"arXiv · AI 最新论文", "url":"https://arxiv.org/list/cs.AI/recent", "note":"研究进展与新想法"},
    {"name":"NASA Images", "url":"https://images.nasa.gov/", "note":"太空与航天影像"},
]

RADAR_TOPICS = {
    "tech": {"label":"科技热榜", "hn_terms":None, "nasa":""},
    "ai": {"label":"AI 与智能体", "hn_terms":["ai","llm","agent","model","machine learning","openai","anthropic","inference","neural"], "nasa":""},
    "robotics": {"label":"机器人与具身智能", "hn_terms":["robot","robotics","humanoid","embodied","drone","autonomous"], "nasa":"robotics"},
    "chips": {"label":"芯片与硬件", "hn_terms":["chip","semiconductor","gpu","cpu","hardware","risc-v","silicon","fpga"], "nasa":""},
    "quantum": {"label":"量子与前沿科学", "hn_terms":["quantum","physics","particle","fusion","material","science"], "nasa":""},
    "biotech": {"label":"生命科学与生物技术", "hn_terms":["bio","biology","genome","protein","medical","biotech","crispr"], "nasa":""},
    "odd": {"label":"互联网奇物", "hn_terms":["weird","strange","fun","odd","simulation","experiment","interactive","game"], "nasa":""},
    "space": {"label":"航天与宇宙", "hn_terms":None, "nasa":"space telescope planet moon mars spacecraft"},
}
_RADAR_CACHE: dict[str, tuple[float, dict]] = {}
_RADAR_LOCK = threading.Lock()


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fetch_json(url: str, timeout: float = 3.5):
    request = Request(url, headers={"User-Agent":"WonderAtlas/6.0 (museum education and curiosity discovery)", "Accept":"application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("external source returned a non-200 response")
        return json.loads(response.read().decode("utf-8"))


def _hn_item(story_id: int):
    try:
        d = _fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{int(story_id)}.json", 2.0)
        if not d or d.get("type") != "story" or not d.get("title") or not d.get("url"):
            return None
        url = d["url"]
        if urlsplit(url).scheme not in ("http", "https") or not urlsplit(url).netloc:
            return None
        return {"id":str(d.get("id")), "title":d["title"][:240], "url":url, "score":int(d.get("score") or 0),
                "comments":int(d.get("descendants") or 0), "by":str(d.get("by") or "")[:80],
                "time":datetime.fromtimestamp(int(d.get("time") or 0), timezone.utc).isoformat(timespec="minutes"),
                "source":"Hacker News", "kind":"tech"}
    except Exception:
        return None


def _load_radar(topic: str) -> dict:
    cfg = RADAR_TOPICS.get(topic, RADAR_TOPICS["tech"])
    now = time.time()
    with _RADAR_LOCK:
        cached = _RADAR_CACHE.get(topic)
        if cached and now - cached[0] < 900:
            return cached[1]
    result = {"topic":topic, "label":cfg["label"], "items":[], "error":"", "updated_at":_utc_now(), "links":TECH_LINKS}
    try:
        if cfg["nasa"]:
            params = urlencode({"q":cfg["nasa"], "media_type":"image", "page_size":12})
            raw = _fetch_json("https://images-api.nasa.gov/search?" + params, 4.5)
            rows = (raw.get("collection") or {}).get("items") or []
            for row in rows:
                data = (row.get("data") or [{}])[0]
                links = row.get("links") or []
                preview = next((x.get("href","") for x in links if x.get("rel")=="preview"), "")
                if preview and not preview.startswith("https://images-assets.nasa.gov/"):
                    preview = ""
                nasa_id = str(data.get("nasa_id") or "")
                result["items"].append({"id":"nasa:"+nasa_id, "title":str(data.get("title") or "NASA 图像")[:240],
                    "description":re.sub(r"<[^>]*>", " ", str(data.get("description") or "")).strip()[:420],
                    "date":str(data.get("date_created") or "")[:40], "image_url":preview,
                    "url":"https://images.nasa.gov/details/"+nasa_id if nasa_id else "https://images.nasa.gov/",
                    "source":"NASA Image and Video Library", "score":None, "kind":"space"})
            result["items"] = result["items"][:12]
            if not result["items"]: result["error"] = "NASA 暂时没有返回匹配图像。"
        else:
            ids = _fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json", 3.0)[:30]
            with ThreadPoolExecutor(max_workers=12) as pool:
                rows = list(pool.map(_hn_item, ids))
            rows = [x for x in rows if x]
            terms = cfg["hn_terms"]
            if terms:
                matches = [x for x in rows if any(t in x["title"].casefold() for t in terms)]
                rows = matches[:15] if len(matches) >= 4 else rows[:15]
            else:
                rows = rows[:15]
            result["items"] = rows
            if not rows: result["error"] = "当前无法连接实时科技热榜。可使用下方官方入口继续探索。"
    except Exception:
        result["error"] = "当前无法连接外部实时数据；你仍可通过下方官方入口浏览。"
    with _RADAR_LOCK:
        _RADAR_CACHE[topic] = (now, result)
    return result


class UsageEvent(BaseModel):
    feature: str = Field(min_length=1, max_length=40)
    action: Literal["open", "complete", "save", "share", "play", "search", "detail", "collect", "like", "comment", "create", "revisit", "vote"] = "open"

    @field_validator("feature")
    @classmethod
    def feature_allowed(cls, value):
        if value not in FEATURE_MAP:
            raise ValueError("未知功能名称")
        return value


class FeatureVote(BaseModel):
    feature: str = Field(min_length=1, max_length=40)
    sentiment: Literal["love", "neutral", "improve"]

    @field_validator("feature")
    @classmethod
    def feature_allowed(cls, value):
        if value not in FEATURE_MAP:
            raise ValueError("未知功能名称")
        return value


class CollectLink(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=600)
    source_url: str = Field(min_length=8, max_length=500)
    image_url: str = Field(default="", max_length=500)
    category: str = Field(default="科技与发明", max_length=24)
    tags: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip(): raise ValueError("名称不能为空")
        return value.strip()

    @field_validator("source_url")
    @classmethod
    def valid_source(cls, value):
        p = urlsplit(value)
        if p.scheme not in ("http", "https") or not p.netloc: raise ValueError("来源必须是有效的 http(s) 链接")
        return value

    @field_validator("image_url")
    @classmethod
    def safe_image(cls, value):
        if not value: return value
        p = urlsplit(value)
        allowed = {"images-assets.nasa.gov", "images.nasa.gov", "images.metmuseum.org", "www.artic.edu", "openaccess-cdn.clevelandart.org", "www.clevelandart.org"}
        if p.scheme != "https" or not p.hostname or not any(p.hostname == x or p.hostname.endswith("."+x) for x in allowed):
            raise ValueError("只允许使用已知开放馆藏或 NASA 的 HTTPS 图像地址")
        return value


def mount_wonder_discovery(app, db, maybe_user, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS feature_usage_events(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          feature_key TEXT NOT NULL,
          action TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_feature_usage_time ON feature_usage_events(created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_feature_usage_key_time ON feature_usage_events(feature_key,created_at DESC);
        CREATE TABLE IF NOT EXISTS feature_feedback(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          feature_key TEXT NOT NULL,
          sentiment TEXT NOT NULL CHECK(sentiment IN ('love','neutral','improve')),
          updated_at TEXT NOT NULL,
          PRIMARY KEY(user_id,feature_key)
        );
        CREATE INDEX IF NOT EXISTS ix_feature_feedback_key ON feature_feedback(feature_key,sentiment);
        """)

    @app.get("/api/wonder/museums")
    def museum_directory(q: str = Query("", max_length=120), group: str = Query("全部", max_length=80)):
        rows = MUSEUM_DIRECTORY
        if group and group != "全部": rows = [x for x in rows if x["group"] == group]
        if q.strip():
            n = q.strip().casefold()
            rows = [x for x in rows if n in " ".join(str(v) for v in x.values()).casefold()]
        return {"items":rows, "total":len(rows), "groups":sorted({x["group"] for x in MUSEUM_DIRECTORY}), "updated_at":_utc_now()}

    @app.get("/api/wonder/radar")
    def live_radar(topic: str = Query("tech", max_length=20)):
        if topic not in RADAR_TOPICS: fail(400, "未知雷达主题")
        return _load_radar(topic)

    @app.post("/api/wonder/collect-link", status_code=201)
    def collect_discovery_link(payload: CollectLink, user=Depends(require_user)):
        # A link saved from the radar is always private. External image URLs are allowlisted.
        tags = ",".join(t.strip()[:24] for t in payload.tags if t.strip())[:200]
        story = "从万物雷达收入的外部发现。\n来源：" + payload.source_url + "\n说明：原始内容由来源网站托管；本馆保存链接与个人收藏记录。"
        with db() as c:
            existing = c.execute("SELECT id FROM exhibits WHERE user_id=? AND source_url=? AND title=?", (user["id"], payload.source_url, payload.title)).fetchone()
            if existing: return {"ok":True, "already_collected":True, "exhibit_id":existing["id"], "title":payload.title}
            cur = c.execute("""INSERT INTO exhibits(user_id,title,description,story,category,tags,image_url,source_url,visibility,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (user["id"],payload.title,payload.description,story,payload.category,tags,payload.image_url,payload.source_url,"private",now(),now()))
            return {"ok":True, "already_collected":False, "exhibit_id":cur.lastrowid, "title":payload.title, "visibility":"private"}

    @app.post("/api/insights/event", status_code=201)
    def record_feature_event(payload: UsageEvent, user=Depends(require_user)):
        with db() as c:
            recent = c.execute("SELECT COUNT(*) FROM feature_usage_events WHERE user_id=? AND created_at>=?", (user["id"], datetime.fromtimestamp(time.time()-60,timezone.utc).isoformat(timespec="seconds"))).fetchone()[0]
            if recent >= 40: fail(429, "操作太频繁，请稍后再试")
            c.execute("INSERT INTO feature_usage_events(user_id,feature_key,action,created_at) VALUES(?,?,?,?)", (user["id"],payload.feature,payload.action,now()))
        return {"ok":True}

    @app.post("/api/insights/vote")
    def vote_feature(payload: FeatureVote, user=Depends(require_user)):
        with db() as c:
            c.execute("""INSERT INTO feature_feedback(user_id,feature_key,sentiment,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(user_id,feature_key) DO UPDATE SET sentiment=excluded.sentiment,updated_at=excluded.updated_at""", (user["id"],payload.feature,payload.sentiment,now()))
        return {"ok":True,"feature":payload.feature,"sentiment":payload.sentiment}

    @app.get("/api/insights/summary")
    def insights_summary(days: int = Query(30, ge=7, le=90), user=Depends(maybe_user)):
        since = datetime.fromtimestamp(time.time()-days*86400, timezone.utc).isoformat(timespec="seconds")
        with db() as c:
            event_rows = c.execute("""SELECT feature_key,
                SUM(CASE WHEN action='open' THEN 1 ELSE 0 END) AS opens,
                SUM(CASE WHEN action!='open' THEN 1 ELSE 0 END) AS actions,
                COUNT(DISTINCT user_id) AS users
                FROM feature_usage_events WHERE created_at>=? GROUP BY feature_key""", (since,)).fetchall()
            vote_rows = c.execute("SELECT feature_key, sentiment, COUNT(*) AS n FROM feature_feedback GROUP BY feature_key,sentiment").fetchall()
            my_rows = c.execute("SELECT feature_key,sentiment FROM feature_feedback WHERE user_id=?", (user["id"],)).fetchall() if user else []
        events = {r["feature_key"]:r for r in event_rows}
        votes = {}
        for r in vote_rows: votes.setdefault(r["feature_key"],{})[r["sentiment"]]=r["n"]
        mine = {r["feature_key"]:r["sentiment"] for r in my_rows}
        items=[]
        for key, meta in FEATURE_MAP.items():
            e=events.get(key); v=votes.get(key,{})
            opens=int(e["opens"] or 0) if e else 0; actions=int(e["actions"] or 0) if e else 0; users=int(e["users"] or 0) if e else 0
            love=int(v.get("love",0)); neutral=int(v.get("neutral",0)); improve=int(v.get("improve",0))
            items.append({**meta,"opens":opens,"actions":actions,"active_users":users,"love_votes":love,"neutral_votes":neutral,"improve_votes":improve,"my_vote":mine.get(key),"votes":love+neutral+improve})
        items.sort(key=lambda x:(x["love_votes"],x["actions"],x["opens"]),reverse=True)
        return {"days":days,"items":items,"total_events":sum(x["opens"]+x["actions"] for x in items),"total_votes":sum(x["votes"] for x in items),
                "privacy":"只统计功能名与操作类型，不记录搜索词、展品内容、访问网址或 IP。仅聚合数据对外展示。"}

    @app.get("/api/wonder/collection-search")
    def open_collection_search(q: str = Query(..., min_length=2, max_length=100), source: str = Query("all", max_length=10)):
        """Search live museum APIs. Images are returned only when the source marks them open."""
        if source not in {"all", "met", "aic", "cma"}: fail(400, "未知馆藏来源")
        query = q.strip()
        if not query: fail(422, "请输入至少两个字符")
        api_query = _translate_collection_query(query)

        def search_met():
            raw = _fetch_json("https://collectionapi.metmuseum.org/public/collection/v1/search?" + urlencode({"hasImages":"true", "q":api_query}), 4.5)
            ids = (raw.get("objectIDs") or [])[:7]
            seeds = []
            for oid in ids:
                seeds.append({"id":f"met:{oid}","provider":"met","external_id":str(oid),"title":"","title_en":"","artist":"","date":"","medium":"","museum":"大都会艺术博物馆","museum_en":"The Metropolitan Museum of Art","category":_category_for(query),"culture":"","source_url":f"https://www.metmuseum.org/art/collection/search/{oid}","license_url":MET_LICENSE,"note":"来自大都会艺术博物馆官方馆藏搜索。","tags":[query]})
            with ThreadPoolExecutor(max_workers=7) as pool:
                return list(pool.map(_load_met, seeds))

        def search_aic():
            fields = "id,title,artist_display,date_display,medium_display,department_title,is_public_domain,image_id,web_url,credit_line"
            url = "https://api.artic.edu/api/v1/artworks/search?" + urlencode({"q":api_query,"limit":8,"fields":fields})
            raw = _fetch_json(url, 4.5)
            found = []
            for d in (raw.get("data") or []):
                seed = {"id":f"aic:{d.get('id')}","provider":"aic","external_id":str(d.get("id")),"title":d.get("title") or "未命名作品","title_en":d.get("title") or "","artist":d.get("artist_display") or "","date":d.get("date_display") or "","medium":d.get("medium_display") or "","museum":"芝加哥艺术博物馆","museum_en":"Art Institute of Chicago","category":_category_for(query),"culture":"","source_url":d.get("web_url") or f"https://www.artic.edu/artworks/{d.get('id')}","license_url":AIC_LICENSE,"note":"来自芝加哥艺术博物馆官方馆藏搜索。","tags":[query],"department":d.get("department_title") or ""}
                pd = d.get("is_public_domain") is True
                image_id = d.get("image_id") if pd else None
                image = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg" if image_id else ""
                seed.update({"image_url":image,"open_access":bool(pd and image),"license":"Public Domain" if pd and image else "未标记为公有领域图像","credit_line":d.get("credit_line") or ""})
                found.append(seed)
            return found

        def search_cma():
            url = "https://openaccess-api.clevelandart.org/api/artworks/?" + urlencode({"q":api_query,"limit":8,"has_image":1})
            raw = _fetch_json(url, 4.5)
            found = []
            for d in (raw.get("data") or []):
                cc0 = str(d.get("share_license_status") or "").upper() == "CC0"
                images = d.get("images") or {}; image_record = images.get("web") or images.get("print") or {}
                image = image_record.get("url", "") if cc0 else ""
                host = (urlsplit(image).hostname or "").lower() if image else ""
                if image and (urlsplit(image).scheme != "https" or not (host == "clevelandart.org" or host.endswith(".clevelandart.org"))): image = ""
                creators = ", ".join(x.get("description", "") for x in d.get("creators", []) if x.get("description"))
                found.append({"id":f"cma:{d.get('id')}","provider":"cma","external_id":str(d.get("id")),"title":d.get("title") or "未命名作品","title_en":d.get("title") or "","artist":creators,"date":d.get("creation_date") or "","medium":d.get("technique") or "","museum":"克利夫兰艺术博物馆","museum_en":"Cleveland Museum of Art","category":_category_for(query),"culture":", ".join(d.get("culture") or []),"source_url":d.get("url") or "https://www.clevelandart.org/art/collection","license_url":CMA_LICENSE,"note":"来自克利夫兰艺术博物馆官方馆藏搜索。","tags":[query],"image_url":image,"open_access":bool(cc0 and image),"license":"CC0 开放访问" if cc0 and image else "未标记为 CC0 图像","credit_line":d.get("creditline") or ""})
            return found

        funcs = {"met":search_met, "aic":search_aic, "cma":search_cma}
        providers = [source] if source != "all" else ["met", "aic", "cma"]
        results=[]; errors=[]
        with ThreadPoolExecutor(max_workers=len(providers)) as pool:
            futures = {pool.submit(funcs[key]):key for key in providers}
            for future in as_completed(futures):
                key = futures[future]
                try: results.extend(future.result())
                except Exception: errors.append({"met":"大都会艺术博物馆","aic":"芝加哥艺术博物馆","cma":"克利夫兰艺术博物馆"}[key])
        seen=set(); unique=[]
        for x in results:
            if x["id"] not in seen and x.get("title"):
                seen.add(x["id"]); unique.append(x)
        unique.sort(key=lambda x:(not bool(x.get("open_access")), x.get("museum", ""), x.get("title", "")))
        return {"query":query,"source":source,"items":unique[:20],"total":len(unique),"sources_failed":errors,
                "notice":"图像只在馆方 API 明确标记开放访问、公有领域或 CC0 时显示；每件作品均保留原馆链接。"}


def _translate_collection_query(query: str) -> str:
    text = query.strip()
    aliases = {
        "珠宝":"jewelry", "古董珠宝":"antique jewelry", "首饰":"jewelry", "项链":"necklace", "戒指":"ring", "耳环":"earrings",
        "古画":"painting", "古代绘画":"ancient painting", "书画":"painting", "油画":"oil painting", "水墨":"ink painting",
        "古币":"ancient coin", "钱币":"coin", "硬币":"coin", "玉器":"jade", "青铜器":"bronze", "瓷器":"porcelain",
        "花瓶":"vase", "盔甲":"armor", "铠甲":"armor", "刀剑":"sword", "古籍":"manuscript", "手稿":"manuscript",
        "化石":"fossil", "恐龙":"dinosaur fossil", "矿物":"mineral", "宝石":"gemstone", "机器人":"robot", "航天":"spacecraft"
    }
    return aliases.get(text.casefold(), aliases.get(text, text))


def _category_for(query: str) -> str:
    q=query.casefold()
    if any(k in q for k in ["jewel","necklace","ring","earring","brooch","珠宝","首饰","项链","戒指","耳环","冠冕"]): return "古董与珠宝"
    if any(k in q for k in ["coin","medal","currency","钱币","古币","硬币"]): return "古币与钱币"
    if any(k in q for k in ["painting","oil painting","画","书画","水墨","油画","landscape"]): return "绘画与书画"
    if any(k in q for k in ["armor","armour","weapon","sword","盔甲","铠甲","兵器","刀剑"]): return "历史文物"
    if any(k in q for k in ["ceramic","pottery","vase","porcelain","陶瓷","瓷器","玉器"]): return "陶瓷与器物"
    if any(k in q for k in ["book","manuscript","scroll","古籍","手稿","卷轴"]): return "古籍与手稿"
    if any(k in q for k in ["fossil","mineral","gem","dinosaur","化石","矿物","宝石","恐龙"]): return "自然与化石"
    return "古董与珠宝" if any(k in q for k in ["antique","ancient","古董","古代","artifact","artefact"]) else "绘画与书画"