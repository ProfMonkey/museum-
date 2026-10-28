"""V41: real exhibit-centered exploration, explainable relationships, and privacy."""
import sys

from test_multiuser import env, item


def create(client, title, **kwargs):
    response = client.post("/api/exhibits", json=item(title=title, **kwargs))
    assert response.status_code == 201, response.text
    return response.json()["id"]


def hub(client, exhibit_id):
    return client.get(f"/api/exhibits/{exhibit_id}/hub")


def all_peers(body):
    return [v for entries in body["groups"].values() for v in entries]


def test_real_curator_statement_and_transparent_classification(env):
    alice, bob, guest = env
    source = create(alice, "史前海洋生物", category="化石与古生物",
                    domain="自然史与化石", tags="古海洋,化石", time_bucket="亿年前")
    comparison = create(bob, "贝壳化石", category="化石与古生物",
                        domain="自然史与化石", tags="古海洋,标本", time_bucket="亿年前")
    other_era = create(bob, "古代绘画手稿", category="绘画与书画",
                       domain="绘画与视觉艺术", tags="传统,画纸", time_bucket="亿年前")
    link = alice.post(f"/api/exhibits/{source}/connections", json={
        "target_id": comparison, "kind": "historical",
        "explanation": "两件馆藏均谈到古生物，具体年代仍需检查原始来源。"
    })
    assert link.status_code == 201, link.text
    result = hub(guest, source)
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["focus"]["id"] == source
    assert data["focus"]["is_public"] is True
    assert data["total"] <= 12
    claim = next(x for x in data["groups"]["curator"] if x["id"] == comparison)
    assert claim["author"] == "Alice"
    assert claim["kind"] == "历史脉络"
    assert claim["verified"] is False
    assert "未经平台核实" in data["notice"]
    assert any(x["id"] == other_era and "宽泛年代桶相同" in x["reason"]
               for x in data["groups"]["time"])


def test_metadata_has_specific_explanations_and_no_fake_causes(env):
    alice, bob, guest = env
    focus = create(alice, "电影海报甲", category="电影与电视",
                   domain="影视与动漫", tags="电影,科幻", time_bucket="近30年")
    matched = create(bob, "电影海报乙", category="电影与电视",
                     domain="影视与动漫", tags="电影,悬疑", time_bucket="最近一年")
    irrelevant = create(bob, "篮球赛事", category="体育与运动",
                        domain="体育与运动", tags="篮球,竞技", time_bucket="时间不详")
    data = hub(guest, focus).json()
    got = next(x for x in data["groups"]["metadata"] if x["id"] == matched)
    assert "共同标签" in got["reason"]
    assert "电影" in got["reason"]
    assert got["source"] == "metadata"
    assert got["verified"] is False
    assert irrelevant not in [x["id"] for x in all_peers(data)]


def test_current_visibility_and_owner_private_exhibit_access(env):
    alice, bob, guest = env
    focus = create(alice, "公开的米线资料", category="饮食文化",
                   domain="食物与饮食", tags="米线,云南")
    private = create(alice, "私人食谱", category="饮食文化",
                     domain="食物与饮食", tags="米线,云南", visibility="private")
    other_private = create(bob, "鲍勃的秘密食谱", category="饮食文化",
                           domain="食物与饮食", tags="米线,云南", visibility="private")
    link = alice.post(f"/api/exhibits/{focus}/connections", json={
        "target_id": private, "kind": "same_topic",
        "explanation": "我个人的私密食谱和这件公开内容存在主题关联。"
    })
    assert link.status_code == 201, link.text
    for visitor in (guest, bob):
        response = hub(visitor, focus)
        assert response.status_code == 200
        payload = response.json()
        assert private not in [x["id"] for x in all_peers(payload)]
        assert other_private not in [x["id"] for x in all_peers(payload)]
        assert hub(visitor, private).status_code == 404
    own = hub(alice, focus).json()
    assert private in [x["id"] for x in own["groups"]["curator"]]
    assert hub(alice, private).status_code == 200
    changed = alice.patch(f"/api/exhibits/{focus}", json=item(
        title="公开的米线资料", visibility="private", category="饮食文化",
        domain="食物与饮食", tags="米线,云南"))
    assert changed.status_code == 200
    assert hub(guest, focus).status_code == 404
    assert hub(bob, focus).status_code == 404
    assert hub(alice, focus).json()["focus"]["is_public"] is False


def test_studio_private_scope_masks_source_from_other_public_hubs(env):
    alice, bob, guest = env
    focus = create(alice, "公开海洋资料", category="化石与古生物",
                   domain="自然史与化石", tags="化石,古海洋")
    studio = create(bob, "带有私密制作记录的化石", category="化石与古生物",
                    domain="自然史与化石", tags="化石,古海洋")
    # A curator could have saved the item before the original author's
    # container was withdrawn. It should disappear from the saved view too.
    assert alice.post(f"/api/exhibits/{studio}/bookmark").status_code == 200
    # Directly set up an upstream private owner-controlled studio container.
    # The original exhibit itself remains marked public. PUBLIC_SCOPE must
    # still mask it from foreign callers and related results.
    mod = sys.modules["wa_test_server"]
    with mod.db() as c:
        c.execute("""INSERT INTO creator_studio_projects
                 (owner_id,exhibit_id,kind,title,description,config_json,
                  visibility,created_at,updated_at)
                 VALUES ((SELECT id FROM users WHERE username='Bob'),
                          ?,'quiz','私人化石实验','','{}','private','2026-01-01','2026-01-01')""",
                  (studio,))
    response = hub(guest, focus)
    assert response.status_code == 200, response.text
    assert studio not in [x["id"] for x in all_peers(response.json())]
    assert hub(guest, studio).status_code == 404
    assert hub(alice, studio).status_code == 404
    assert hub(bob, studio).status_code == 200
    # Neither the source dialog, feed, creator profile, saved collection, nor
    # classic quick recommendations can reveal a former public source.
    assert guest.get(f"/api/exhibits/{studio}").status_code == 404
    assert studio not in [x["id"] for x in guest.get("/api/feed").json()["items"]]
    assert studio not in [x["id"] for x in guest.get("/api/users/Bob").json()["items"]]
    assert studio not in [x["id"] for x in alice.get("/api/my/saved").json()]
    assert studio not in [x["id"] for x in guest.get(f"/api/exhibits/{focus}/related").json()]
    # The legacy V11 graph and manual-link writer must follow the SAME scope:
    legacy = guest.get(f"/api/exhibits/{focus}/connections")
    assert legacy.status_code == 200
    assert studio not in [n["id"] for n in legacy.json()["nodes"]]
    assert guest.get(f"/api/exhibits/{studio}/connections").status_code == 404
    blocked = alice.post(f"/api/exhibits/{focus}/connections", json={
        "target_id": studio, "kind": "same_topic",
        "explanation": "上游工作室已经私密，不允许对外建立新的关联。"
    })
    assert blocked.status_code == 404


def test_v41_html_and_js_integration_are_available(env):
    guest = env[2]
    assert guest.get("/api/health").json()["version"] == "41.0"
    index = guest.get("/")
    assert index.status_code == 200
    assert "WORLD 41" in index.text
    assert "/static/object-hub.js" in index.text
    assert "/static/object-hub.css" in index.text
    js = guest.get("/static/app.js").text
    hub_js = guest.get("/static/object-hub.js")
    assert hub_js.status_code == 200
    assert "hubDetail" in js and "hubBack" in js
    assert "'/hub'" in js
    assert "WONDER OBJECT HUB" not in hub_js.text  # preserve honest V41 label
    assert "馆长主动关联" in hub_js.text
    assert "元数据相似" not in js or "关联" in hub_js.text
