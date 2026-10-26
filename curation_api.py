"""V13: source-preserving museum time catalogue and private collection audit.

Institutional objects are NOT user posts and are never inserted into public feed.
Age groups are coarse catalogue filters. No unverified copyright or exact year claims.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import Depends, Query
from world_museums import SEEDS, _catalog

ERAS = (
    ('亿年前', '深时与地球'), ('百万年前', '生命演化'),
    ('远古与史前', '漫长史前'), ('千年至万年前', '文明起源'),
    ('近千年', '历史文明'), ('近现代', '工业与现代'),
    ('近30年', '数字时代'), ('最近一年', '当代新作'),
    ('此刻/实时', '正在发生'), ('跨越多个时期', '长时段'),
    ('时间不详', '等待考证'),
)

YEAR = re.compile(r'(?<!\d)([1-2]\d{3}|[1-9]\d{2})(?!\d)')
CENTURY = re.compile(r'(?:公元)?\s*(\d{1,2})(?:\s*[–—\-至到]\s*(\d{1,2}))?\s*世纪')


def age_bucket(year: int | None, current_year: int = 2026) -> str:
    if year is None or year > current_year:
        return '时间不详'
    age = current_year - year
    if age >= 100_000_000:
        return '亿年前'
    if age >= 1_000_000:
        return '百万年前'
    if age >= 10_000:
        return '远古与史前'
    if age >= 1_000:
        return '千年至万年前'
    if age >= 100:
        return '近千年'
    if age >= 30:
        return '近现代'
    if age >= 1:
        return '近30年'
    return '最近一年'


def classify_date(date: str, current_year: int = 2026) -> dict:
    """Use only explicit dates/centuries; no inferred dynastic or cultural years."""
    raw = str(date or '').strip()
    if not raw:
        return {'era': '时间不详', 'approx_year': None, 'parse_status': 'unknown'}
    # Specific BCE ranges take priority over century match.
    bce = '公元前' in raw or 'BCE' in raw.upper() or re.search(r'\bBC\b', raw, re.I)
    cent = CENTURY.search(raw)
    if cent:
        start, end = int(cent.group(1)), int(cent.group(2) or cent.group(1))
        if not (1 <= start <= end <= 99):
            return {'era': '时间不详', 'approx_year': None, 'parse_status': 'unknown'}
        if bce:
            lo, hi = -(end * 100), -(start * 100 - 1)
        else:
            lo, hi = (start - 1) * 100 + 1, end * 100
        b1, b2 = age_bucket(lo, current_year), age_bucket(hi, current_year)
        return {'era': b1 if b1 == b2 else '跨越多个时期',
                'approx_year': None, 'parse_status': 'century_range'}
    years = [int(x) for x in YEAR.findall(raw)]
    if not years:
        return {'era': '时间不详', 'approx_year': None, 'parse_status': 'unknown'}
    if bce:
        years = [-x for x in years]
    first = min(years); last = max(years)
    eras = (age_bucket(first, current_year), age_bucket(last, current_year))
    return {'era': eras[0] if eras[0] == eras[1] else '跨越多个时期',
            'approx_year': round((first + last) / 2) if first == last else None,
            'parse_status': 'year' if first == last else 'year_range'}


def museum_records(items, current_year: int = 2026):
    """Only image URLs explicitly cleared by source API can be displayed."""
    result = []
    for item in items:
        year = classify_date(item.get('date', ''), current_year)
        result.append({
            'id': str(item['id']), 'title': str(item.get('title') or '未命名作品'),
            'museum': str(item.get('museum') or ''), 'artist': str(item.get('artist') or ''),
            'category': str(item.get('category') or ''), 'medium': str(item.get('medium') or ''),
            'date': str(item.get('date') or ''), 'era': year['era'],
            'parse_status': year['parse_status'], 'approx_year': year['approx_year'],
            'source_url': str(item.get('source_url') or ''),
            'image_url': str(item.get('image_url') or '') if item.get('open_access') is True else '',
            'open_access': item.get('open_access') is True,
            'license': str(item.get('license') or '等待馆方 API 核验'),
            'tags': list(item.get('tags') or [])[:12],
            'origin': 'institutional_catalogue_not_user_post',
        })
    return result


def audit_row(row):
    issues = []
    def warn(code, label, why):
        issues.append({'code': code, 'label': label, 'tip': why})
    get = lambda k, default='': (row.get(k, default) if isinstance(row, dict) else row[k]) or default
    if not str(get('description')).strip():
        warn('description', '缺少作品介绍', '补充一句具体描述，让参观者知道为什么值得收藏。')
    if not str(get('source_url')).strip():
        warn('source', '缺少来源链接', '如果是原创，写明创作背景；引用他人内容建议附原始出处。')
    elif not valid_http_url(str(get('source_url'))):
        warn('source_invalid', '来源地址格式异常', '仅使用有效的 http 或 https 资料链接。')
    if not str(get('image_url')).strip():
        warn('cover', '没有封面', '可上传原创照片，或使用来源明确允许展示的图片。')
    if get('domain', '其他') == '其他' or get('category', '其他') == '其他':
        warn('classification', '分类过于宽泛', '选择更具体的一级领域与细分类别。')
    if get('time_bucket', '时间不详') == '时间不详':
        warn('era', '时代未标注', '若来源能确定年代，可填写时间尺度；无法考证时保留未知即可。')
    if get('time_basis', '不详') == '不详':
        warn('basis', '时间依据未标注', '说明记录的是创作、发布、发现还是走红时间。')
    if get('time_bucket', '时间不详') != '时间不详' and not str(get('time_note')).strip():
        warn('date_note', '缺少年代原文', '建议保留来源中的原始年份或时期描述。')
    return {'id': row['id'], 'title': row['title'], 'issues': issues,
            'missing': len(issues), 'score': round((1 - len(issues) / 7) * 100)}


def valid_http_url(raw):
    try:
        parts = urlsplit(raw)
        return parts.scheme in ('http', 'https') and bool(parts.netloc)
    except ValueError:
        return False


def mount_curation(app, db, require_user, fail):
    @app.get('/api/curation/museum-eras')
    def museum_eras(museum: str = Query('全部', max_length=80),
                    category: str = Query('全部', max_length=50)):
        # Every record in this collection is drawn from source-linked curated seeds.
        # Live API enrichment affects images/rights only, not the existence of records.
        items = _catalog()
        works = museum_records(items, current_year=datetime.now(timezone.utc).year)
        institutions = sorted({x['museum'] for x in works})
        categories = sorted({x['category'] for x in works})
        if museum != '全部' and museum not in institutions:
            fail(400, '未知博物馆筛选条件')
        if category != '全部' and category not in categories:
            fail(400, '未知类别筛选条件')
        if museum != '全部': works = [x for x in works if x['museum'] == museum]
        if category != '全部': works = [x for x in works if x['category'] == category]
        years = [{'id': era, 'title': title, 'items': [w for w in works if w['era'] == era]}
                 for era, title in ERAS]
        for group in years: group['count'] = len(group['items'])
        return {'eras': years, 'total': len(works), 'all_total': len(SEEDS),
                'institutions': institutions, 'categories': categories,
                'source': 'official_museum_seed_records',
                'notice': '名馆馆藏与用户发布内容分开计数。年代是从馆藏文字中的明确年份/世纪推得的粗分段，不能代替馆方原始年代；图像仅在馆方接口核验开放访问后显示。'}

    @app.get('/api/curation/me/quality')
    def my_quality(user=Depends(require_user)):
        with db() as c:
            count = c.execute('SELECT COUNT(*) FROM exhibits WHERE user_id=?', (user['id'],)).fetchone()[0]
            rows = c.execute('''SELECT id,title,description,source_url,image_url,domain,category,
                time_bucket,time_basis,time_note FROM exhibits WHERE user_id=?
                ORDER BY updated_at DESC,id DESC LIMIT 500''', (user['id'],)).fetchall()
        audited = [audit_row(x) for x in rows]
        counts = Counter(i['code'] for a in audited for i in a['issues'])
        return {'items': audited, 'total': count, 'checked': len(audited),
                'issue_counts': [{'code': k, 'count': v} for k,v in counts.most_common()],
                'fully_described': sum(x['missing'] == 0 for x in audited),
                'scope': 'current_user_only',
                'notice': '这里是元数据完整性建议，不代表鉴定真伪或可靠性评分。缺少年代信息并不意味着数据错误，不会自动修改你的馆藏。'}