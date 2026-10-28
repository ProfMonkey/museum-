"""V42 unified search: cross-category recall, ranking, facets and privacy.

Run locally: python -m pytest -q tests/test_search_v42.py
No GitHub Actions or external search service is needed.
"""
import sys

from test_multiuser import env, item


def publish(client, title, **kw):
    response = client.post("/api/exhibits", json=item(title=title, **kw))
    assert response.status_code == 201, response.text
    return response.json()["id"]


def search(client, **kwargs):
    response = client.get("/api/search", params=kwargs)
    assert response.status_code == 200, response.text
    return response.json()


def ids(data):
    return [x["id"] for x in data["items"]]


def test_same_keyword_across_very_different_domains_without_preselecting(env):
    alice, bob, visitor = env
    animal = publish(alice, "猴子的行为观察", domain="动物与生态",
                     category="动物观察", tags="灵长类,动物")
    game = publish(bob, "独立游戏：香蕉岛", domain="游戏与交互",
                   category="独立游戏", tags="猴子,游戏")
    meme = publish(alice, "网络热梗合集", domain="网络文化与热梗",
                   category="网络热梗", description="猴子表情包")
    original = publish(bob, "一个原创人物", domain="原创与个人创作",
                       category="个人创作", story="这里有一只原创猴子")
    hidden = publish(bob, "猴子个人笔记", visibility="private")
    found = search(visitor, q="猴子")
    assert set(ids(found)) == {animal, game, meme, original}
    assert hidden not in ids(found)
    assert found["total"] == 4
    assert found["items"][0]["id"] == animal  # Exact title prefix before tag/body.
    assert found["scope"].startswith("当前公开")
    matched = {x["id"]: x["matched_in"] for x in found["items"]}
    assert "标题" in matched[animal] and "标签" in matched[game]
    assert "简介" in matched[meme] and "正文" in matched[original]
    assert {"动物与生态", "游戏与交互", "网络文化与热梗", "原创与个人创作"}.issubset(
        {x["value"] for x in found["facets"]["domain"]})
    filtered = search(visitor, q="猴子", domain="游戏与交互")
    assert ids(filtered) == [game] and filtered["total"] == 1


def test_tokens_and_literal_punctuation_are_not_like_wildcards(env):
    alice, bob, visitor = env
    both = publish(alice, "猴子太空漫游", tags="太空,创作")
    other = publish(bob, "猴子公园")
    punct = publish(bob, "100%真实的游戏")
    assert ids(search(visitor, q="猴子 太空")) == [both]
    assert other in ids(search(visitor, q="猴子"))
    assert ids(search(visitor, q="%")) == [punct]
    assert ids(search(visitor, q="_")) == []


def test_selected_filters_and_sort_mode(env):
    alice, bob, visitor = env
    old = publish(alice, "米线笔记", category="饮食文化",
                  domain="食物与饮食", time_bucket="近30年", tags="云南")
    new = publish(bob, "好吃的米线", category="饮食文化",
                  domain="食物与饮食", time_bucket="最近一年", tags="云南")
    latest = search(visitor, q="米线", sort="latest")
    assert set(ids(latest)) == {old, new}
    by_time = search(visitor, q="米线", time_bucket="最近一年")
    assert ids(by_time) == [new]
    by_series = search(visitor, q="米线", series="民间奇趣")
    assert set(ids(by_series)) == {old, new}
    assert by_time["facets"]["time_bucket"]  # Counts before selected filters.
    assert visitor.get("/api/search", params={"domain": "不存在"}).status_code == 400
    assert visitor.get("/api/search", params={"sort": "unknown"}).status_code == 422


def test_withdrawn_upstream_studio_is_absent_from_results_and_facets(env):
    alice, bob, visitor = env
    visible = publish(alice, "公开猴子资料", domain="动物与生态",
                      category="动物观察")
    withdrawn = publish(bob, "私密工作室的猴子", domain="游戏与交互",
                        category="独立游戏")
    mod = sys.modules["wa_test_server"]
    with mod.db() as c:
        c.execute("""INSERT INTO creator_studio_projects
                  (owner_id,exhibit_id,kind,title,description,config_json,
                   visibility,created_at,updated_at)
                  VALUES ((SELECT id FROM users WHERE username='Bob'),
                           ?,'quiz','私人工作室','','{}','private','2026-01-01','2026-01-01')""",
                  (withdrawn,))
    result = search(visitor, q="猴子")
    assert ids(result) == [visible]
    assert result["total"] == 1
    assert not any(x["value"] == "游戏与交互" for x in result["facets"]["domain"])
    assert withdrawn not in ids(search(alice, q="猴子"))
    # Search is public by design, even to the curator who owns the private item.
    assert withdrawn not in ids(search(bob, q="猴子"))


def test_pagination_does_not_repeat_exhibits(env):
    alice, bob, visitor = env
    for i in range(20):
        publish(alice, f"连续测试藏品-{i:02d}")
    first = search(visitor, q="连续测试")
    second = search(visitor, q="连续测试", page=2)
    assert first["per_page"] == 16 and len(first["items"]) == 16
    assert first["has_more"] is True and first["total"] == 20
    assert len(second["items"]) == 4 and second["has_more"] is False
    assert set(ids(first)).isdisjoint(ids(second))


def test_search_is_wired_to_clearly_distinct_feature_directory():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    app = (root / "static/app.js").read_text(encoding="utf-8")
    html = (root / "static/index.html").read_text(encoding="utf-8")
    assert 'data-view="search"' in html
    assert 'data-view="catalog"' in html
    assert 'id="unifiedSearchForm"' in (root / "static/unified-search.js").read_text(encoding="utf-8")
    assert 'else if(S.view===\'search\')' in app
    assert 'WonderSearch.setQuery(S.q)' in app
