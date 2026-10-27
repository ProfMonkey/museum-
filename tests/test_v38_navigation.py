"""V38 navigation and food-wheel wiring smoke tests; run locally, no remote CI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_sidebar_prioritizes_core_features_and_collapses_specialist_groups():
    html = read("static/index.html")
    assert 'class="nav-cap">核心功能</div>' in html
    assert 'class="nav-cap">探索发现</div>' in html
    assert 'class="nav-cap">创作与游玩</div>' in html
    assert html.count('class="nav-group"') == 3
    assert 'data-view="wheels"><span>🍜</span> 今天吃什么</button>' in html
    assert '本机预览 · 暂未公开发布' in html


def test_searchable_feature_map_is_loaded_and_routed():
    html = read("static/index.html")
    app = read("static/app.js")
    catalog = read("static/feature-map.js")
    assert 'src="/static/feature-map.js" defer' in html
    assert "S.view==='catalog'" in app
    assert 'id="featureSearch"' in catalog
    assert "data-feature-card" in catalog
    assert "function" not in catalog.lower() or "function render" in catalog.lower()
    assert "data-view=\"wheels\"" in catalog
    assert "命运接力" in catalog and "文明考古局" in catalog


def test_food_exhibit_can_open_food_wheel_and_keep_source_id_for_guests():
    app = read("static/app.js")
    wheel = read("static/wheel.js")
    api = read("wheel_api.py")
    assert "function isFoodExhibit(x)" in app
    assert "加入「今天吃什么」转盘" in app
    assert "queueExhibit(id,chosen?.title||'',topic)" in app
    assert "sourceIds[label]=Number(exhibitId)" in wheel
    assert "exhibit_id:W.guest.sourceIds?.[response.label]||null" in wheel
    assert "data-wheel=\"food-search\"" in wheel or "button('food-search'" in wheel
    assert "e.category LIKE ? OR e.domain LIKE ? OR e.tags LIKE ?" in api
