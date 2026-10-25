"""World museum seed catalogue, attribution and per-account import isolation."""
from test_multiuser import env
import world_museums


def sample_work():
    return {
        "id": "met:45434", "provider": "met", "external_id": "45434",
        "title": "神奈川冲浪里", "title_en": "The Great Wave", "artist": "葛饰北斋",
        "date": "约 1830–1832", "medium": "木版画", "museum": "大都会艺术博物馆",
        "museum_en": "The Metropolitan Museum of Art", "category": "亚洲艺术", "culture": "日本",
        "source_url": "https://www.metmuseum.org/art/collection/search/45434",
        "license_url": world_museums.MET_LICENSE, "note": "一幅著名的日本木版画。", "tags": ["日本", "木版画"],
        "image_url": "https://images.metmuseum.org/test.jpg", "open_access": True,
        "license": "Public Domain / Open Access", "credit_line": "", "department": "Asian Art"
    }


def test_public_catalog_filters_and_source_metadata(env, monkeypatch):
    a, b, visitor = env
    monkeypatch.setattr(world_museums, "_catalog", lambda: [sample_work()])
    data = visitor.get('/api/world-museums').json()
    assert data['total'] == 1
    assert data['items'][0]['title'] == '神奈川冲浪里'
    assert data['items'][0]['source_url'].startswith('https://www.metmuseum.org/')
    assert data['items'][0]['open_access'] is True
    assert visitor.get('/api/world-museums?q=北斋').json()['total'] == 1
    assert visitor.get('/api/world-museums?q=不存在的词').json()['total'] == 0


def test_collect_creates_private_exhibit_once_and_isolated_per_user(env, monkeypatch):
    alice, bob, visitor = env
    monkeypatch.setattr(world_museums, "_catalog", lambda: [sample_work()])
    assert visitor.post('/api/world-museums/met:45434/collect').status_code == 401
    first = alice.post('/api/world-museums/met:45434/collect')
    assert first.status_code == 201, first.text
    result = first.json()
    assert result['visibility'] == 'private' and result['already_collected'] is False
    my_items = alice.get('/api/my/exhibits').json()
    assert len(my_items) == 1 and my_items[0]['title'] == '神奈川冲浪里'
    assert my_items[0]['visibility'] == 'private'
    assert '官方来源：https://www.metmuseum.org/' in my_items[0]['story']
    assert visitor.get('/api/feed').json()['items'] == []
    assert bob.get('/api/my/exhibits').json() == []
    assert bob.get('/api/world-museums').json()['items'][0]['collected'] is False
    second = alice.post('/api/world-museums/met:45434/collect')
    assert second.status_code == 201 and second.json()['already_collected'] is True
    assert len(alice.get('/api/my/exhibits').json()) == 1
    assert bob.post('/api/world-museums/unknown:1/collect').status_code == 404


def test_safe_image_host_allowlist():
    assert world_museums._safe_image('https://images.metmuseum.org/a.jpg', 'met')
    assert world_museums._safe_image('https://evil.example/a.jpg', 'met') == ''
    assert world_museums._safe_image('javascript:alert(1)', 'aic') == ''
    assert world_museums._safe_image('http://www.artic.edu/a.jpg', 'aic') == ''
    assert world_museums._safe_image('https://openaccess-cdn.clevelandart.org/a.jpg', 'cma')