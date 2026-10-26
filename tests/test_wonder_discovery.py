"""V6 tests: official-source directory, private link collection and aggregate product insights."""
from test_multiuser import env, item


def test_museum_directory_is_broad_and_grouped(env):
    a, b, visitor = env
    data = visitor.get('/api/wonder/museums').json()
    assert data['total'] >= 45
    groups = set(data['groups'])
    assert '绘画、古董与珠宝' in groups
    assert '科技、工程与未来' in groups
    assert '当代流行与新奇' in groups
    jewellery = visitor.get('/api/wonder/museums?q=珠宝').json()['items']
    assert any(x['id'] == 'vam' for x in jewellery)
    tech = visitor.get('/api/wonder/museums?group=科技、工程与未来').json()['items']
    assert any(x['id'] == 'nasaimages' for x in tech)
    assert all(x['url'].startswith('https://') for x in data['items'])


def test_feature_analytics_and_votes_are_aggregated_and_isolated(env):
    a, b, visitor = env
    assert visitor.post('/api/insights/event', json={'feature':'tech_radar','action':'open'}).status_code == 401
    assert a.post('/api/insights/event', json={'feature':'tech_radar','action':'open'}).status_code == 201
    assert a.post('/api/insights/event', json={'feature':'tech_radar','action':'collect'}).status_code == 201
    assert b.post('/api/insights/event', json={'feature':'tech_radar','action':'open'}).status_code == 201
    assert a.post('/api/insights/event', json={'feature':'not-a-feature','action':'open'}).status_code == 422
    assert a.post('/api/insights/vote', json={'feature':'tech_radar','sentiment':'love'}).status_code == 200
    assert b.post('/api/insights/vote', json={'feature':'tech_radar','sentiment':'improve'}).status_code == 200
    summary_a = a.get('/api/insights/summary?days=30').json()
    summary_b = b.get('/api/insights/summary?days=30').json()
    radar_a = next(x for x in summary_a['items'] if x['key'] == 'tech_radar')
    radar_b = next(x for x in summary_b['items'] if x['key'] == 'tech_radar')
    assert radar_a['opens'] == 2 and radar_a['actions'] == 1 and radar_a['active_users'] == 2
    assert radar_a['love_votes'] == 1 and radar_a['improve_votes'] == 1
    assert radar_a['my_vote'] == 'love' and radar_b['my_vote'] == 'improve'
    assert '不记录搜索词' in summary_a['privacy']
    assert visitor.get('/api/insights/summary').status_code == 200


def test_external_discovery_links_are_private_and_safe(env):
    a, b, visitor = env
    payload = {
        'title':'一件很有意思的技术展品',
        'description':'来自公开的技术发现入口',
        'source_url':'https://github.com/trending',
        'category':'科技与发明',
        'tags':['万物雷达','开源'],
    }
    result = a.post('/api/wonder/collect-link', json=payload)
    assert result.status_code == 201, result.text
    exhibit_id = result.json()['exhibit_id']
    assert result.json()['visibility'] == 'private'
    assert a.get(f'/api/exhibits/{exhibit_id}').status_code == 200
    assert b.get(f'/api/exhibits/{exhibit_id}').status_code == 404
    assert visitor.get('/api/feed?q=很有意思的技术展品').json()['items'] == []
    repeated = a.post('/api/wonder/collect-link', json=payload)
    assert repeated.status_code == 201 and repeated.json()['already_collected'] is True
    bad_image = {**payload, 'title':'不安全图片', 'image_url':'https://example.com/not-verified.jpg'}
    assert a.post('/api/wonder/collect-link', json=bad_image).status_code == 422
    bad_source = {**payload, 'title':'不安全来源', 'source_url':'javascript:alert(1)'}
    assert a.post('/api/wonder/collect-link', json=bad_source).status_code == 422