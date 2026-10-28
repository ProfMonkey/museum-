"""V40 information architecture and navigation smoke tests; run locally only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_sidebar_and_breadcrumbs_have_clear_hierarchy():
    html = read("static/index.html")
    assert 'class="nav-cap">发现与检索</div>' in html
    assert 'class="nav-cap">分类与关联探索</div>' in html
    assert 'class="nav-cap">收藏与创作</div>' in html
    assert 'class="nav-cap">互动与体验</div>' in html
    assert 'summary>世界与故事' in html
    assert 'summary>合作与交流' in html
    assert 'id="navBack"' in html and 'id="pageSection"' in html
    assert "WORLD 40" in html
    assert "本机预览 · 暂未公开发布" in html
    assert html.count('class="nav-group"') == 3


def test_feature_map_is_task_first_and_exposes_the_controlled_taxonomy():
    catalog = read("static/feature-map.js")
    taxonomy = read("static/taxonomy.js")
    app = read("static/app.js")
    assert "function taskShortcuts()" in catalog
    assert "function taxonomyBrowser()" in catalog
    assert "COLLECTION TAXONOMY" in catalog
    assert "function nextSteps(view)" in catalog
    assert "const RELATIONSHIPS=" in catalog
    assert "window.WonderTaxonomy" in catalog
    assert "timeBuckets" in taxonomy and "groups" in taxonomy
    assert '"用户上传系列"' in taxonomy
    assert 'series: ["藏品系列","民间奇趣"]' in taxonomy
    assert 'TAX.seriesLabels?.[v]||v' in app
    assert "用户上传系列" in catalog and "用户上传系列" in app
    assert "LEGACY_RECENT_KEY" in catalog
    for action in ("taxonomyDomain", "taxonomyCategory", "taxonomyTime", "taxonomySeries", "taxonomyClear"):
        assert f'data-action="{action}"' in catalog
        assert f"else if(a==='{action}')" in app


def test_main_features_have_contextual_next_steps():
    catalog = read("static/feature-map.js")
    app = read("static/app.js")
    views = [
        "discover", "world-museums", "saved", "museum", "cosmos", "wonder-radar",
        "culture", "journey", "constellation", "wheels", "virtual-gallery", "lab",
        "play", "adventure", "fantasy", "parallel", "coexhibitions", "living",
        "mysteries", "collision", "civilizations", "embassies", "heritage",
        "archaeology", "memories", "insights", "notifications", "profile", "catalog",
    ]
    assert "renderNextSteps(S.view)" in app
    assert "window.WonderFeatureMap?.nextSteps(view)" in app
    for view in views:
        assert f"{view}:[" in catalog or f'"{view}":[' in catalog, f"missing relationship path for {view}"


def test_exhibit_taxonomy_chips_open_filtered_discovery():
    app = read("static/app.js")
    assert 'data-action="filterDomain"' in app
    assert 'data-action="filterCategory"' in app
    assert 'data-action="filterTime"' in app
    assert 'data-action="filterSeries"' in app
    assert "S.domain=value" in app
    assert "S.cat=value" in app
    assert "S.timeBucket=value" in app
    assert "S.series=value" in app
    assert "data-value=" in app[app.index("function card(item)"):app.index("const WHEEL_CONTEXTS=")]


def test_back_button_uses_local_navigation_history():
    app = read("static/app.js")
    html = read("static/index.html")
    assert "navHistory:[]" in app
    assert "async function navBack()" in app
    assert "S.navHistory.push(S.view)" in app
    assert 'data-action="navBack"' in html
    assert "pageSection" in app
