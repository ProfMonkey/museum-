"""V13 museum timeline and personal catalogue audit integration tests."""
import curation_api
from curation_api import age_bucket, classify_date, museum_records
from test_multiuser import env, item


def test_date_ranges_centuries_and_bce_are_conservative():
    assert classify_date('约 1830–1832')['era'] == '近千年'
    assert classify_date('14 世纪')['era'] == '近千年'
    assert classify_date('16 世纪')['era'] == '近千年'
    assert classify_date('约公元 1–4 世纪')['era'] == '千年至万年前'
    assert classify_date('约公元前 1427–1386 年')['era'] == '千年至万年前'
    assert classify_date('隋代（581–618）')['era'] == '千年至万年前'
    assert classify_date('未确定')['era'] == '时间不详'
    assert classify_date('约 1900–1950')['era'] == '跨越多个时期'
    assert age_bucket(2026, 2026) == '最近一年'
    assert age_bucket(2025, 2026) == '近30年' # age in years == 1
    assert classify_date('跨越多个历史阶段')['era'] == '时间不详'


def test_no_unlicensed_images_and_preserved_origin():
    items = [
        dict(id='met:1', title='Test A', museum='M1', date='1872', image_url='https://img', open_access=False),
        dict(id='met:2', title='Test B', museum='M2', date='公元前 1510', image_url='https://img2', open_access=True),
    ]
    works = museum_records(items)
    assert works[0]['image_url'] == ''
    assert works[1]['image_url'].startswith('https://')
    assert works[0]['origin'] == 'institutional_catalogue_not_user_post'
    assert works[1]['era'] == '千年至万年前'


def _mount_v13(env, monkeypatch):
    from fastapi import Depends
    a, b, visitor = env
    import sys
    # Each test_multiuser.env fixture creates a dynamic test server; keep its own db.
    from pathlib import Path
    # retrieve app through TestClient, then identify module from endpoints.
    app = a.app
    read = next(route.endpoint for route in app.routes if getattr(route, 'path', '') == '/api/my/exhibits')
    import inspect
    globs = read.__globals__
    db = globs['db']
    with db() as c:
        columns = {r['name'] for r in c.execute('PRAGMA table_info(exhibits)')}
        for key,typ in [('domain',"TEXT NOT NULL DEFAULT '其他'"),('time_bucket',"TEXT NOT NULL DEFAULT '时间不详'"),('time_basis',"TEXT NOT NULL DEFAULT '不详'"),('time_note',"TEXT NOT NULL DEFAULT ''")]:
            if key not in columns:c.execute('ALTER TABLE exhibits ADD COLUMN '+key+' '+typ)
    if not any(getattr(route, 'path', '') == '/api/curation/museum-eras' for route in app.routes):
        curation_api.mount_curation(app, db, globs['require_user'], globs['fail'])
    # Never call external network during unit/integration test.
    monkeypatch.setattr(curation_api, '_catalog', lambda: [
        {'id': 'met:45434', 'title': '神奈川冲浪里', 'museum': '大都会艺术博物馆', 'date': '约 1830–1832',
         'category':'亚洲艺术', 'source_url':'https://www.metmuseum.org/art/collection/search/45434', 'open_access': False},
        {'id': 'cma:130707','title':'测试作品','museum':'克利夫兰艺术博物馆','date':'约 1550–1650',
         'category':'宗教艺术','source_url':'https://www.clevelandart.org/', 'image_url':'https://source/image.jpg', 'open_access':True},
    ])
    return a, b, visitor, db


def test_catalogue_era_endpoint_does_not_inject_community_posts(env, monkeypatch):
    a,b,visitor,db = _mount_v13(env, monkeypatch)
    before = visitor.get('/api/stats').json()['exhibits']
    r = visitor.get('/api/curation/museum-eras')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['total'] == 2
    assert data['source'] == 'official_museum_seed_records'
    assert any(x['count'] == 2 for x in data['eras'])
    assert visitor.get('/api/stats').json()['exhibits'] == before
    assert visitor.get('/api/curation/museum-eras?museum=Random').status_code == 400
    assert visitor.get('/api/curation/museum-eras?category=不存在').status_code == 400
    met = next(y for x in data['eras'] for y in x['items'] if y['id']=='met:45434')
    assert met['image_url'] == ''


def test_private_audit_only_uses_signed_in_accounts(env, monkeypatch):
    a,b,visitor,db=_mount_v13(env, monkeypatch)
    source=a.post('/api/exhibits',json=item(title='我的古画',description='',source_url='',image_url='',visibility='private')).json()
    other=b.post('/api/exhibits',json=item(title='别人的私密收藏',description='',visibility='private')).json()
    assert visitor.get('/api/curation/me/quality').status_code == 401
    ra=a.get('/api/curation/me/quality')
    assert ra.status_code == 200, ra.text
    audit=ra.json()
    assert audit['total'] == 1
    assert [x['id'] for x in audit['items']] == [source['id']]
    assert '别人的私密收藏' not in str(audit)
    assert audit['items'][0]['missing'] > 0
    rb=b.get('/api/curation/me/quality').json()
    assert [x['id'] for x in rb['items']] == [other['id']]
    assert audit['scope'] == 'current_user_only'