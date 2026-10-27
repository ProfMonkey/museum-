"""V28 constellation voyages: live user-edge paths, privacy, and self-marked progress."""
from test_multiuser import env, item


def idea(client, title):
    response = client.post("/api/constellation/nodes",
                           json={"kind": "idea", "title": title})
    assert response.status_code == 201, response.text
    return response.json()["node"]["id"]


def exhibit_node(client, exhibit_id):
    response = client.post("/api/constellation/nodes",
                           json={"kind": "exhibit", "exhibit_id": exhibit_id})
    assert response.status_code == 201, response.text
    return response.json()["node"]["id"]


def link(client, a, b, note="我主动认为它们之间存在值得继续探索的联系。"):
    response = client.post("/api/constellation/edges", json={
        "from_node_id": a, "to_node_id": b, "kind": "personal", "note": note})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def preview(client, a, b):
    return client.post("/api/constellation/voyages/preview",
                       json={"start_node_id": a, "end_node_id": b})


def save(client, a, b, name="我的私密航线"):
    return client.post("/api/constellation/voyages", json={
        "start_node_id": a, "end_node_id": b, "name": name})


def test_login_is_required_and_routes_are_private(env):
    alice, bob, guest = env
    a, b = idea(alice, "我的起点"), idea(alice, "我的终点")
    link(alice, a, b)
    assert guest.get("/api/constellation/voyages").status_code == 401
    assert guest.post("/api/constellation/voyages/preview",
                      json={"start_node_id": a, "end_node_id": b}).status_code == 401
    result = save(alice, a, b, "私密之旅")
    assert result.status_code == 201, result.text
    rid = result.json()["voyage"]["id"]
    assert len(alice.get("/api/constellation/voyages").json()["items"]) == 1
    assert bob.get("/api/constellation/voyages").json()["items"] == []
    assert bob.get(f"/api/constellation/voyages/{rid}").status_code == 404
    assert guest.get(f"/api/constellation/voyages/{rid}").status_code == 401
    assert bob.put(f"/api/constellation/voyages/{rid}/checkpoints/{a}").status_code == 404
    assert bob.delete(f"/api/constellation/voyages/{rid}").status_code == 404


def test_only_saved_edges_count_not_taxonomy_suggestions(env):
    alice, bob, guest = env
    a = idea(alice, "米线")
    b = idea(alice, "茶马古道")
    c = idea(alice, "古代贸易")
    assert preview(alice, a, c).json()["connected"] is False
    assert save(alice, a, c).status_code == 409
    link(alice, a, b)
    assert preview(alice, a, c).json()["connected"] is False
    link(alice, b, c)
    route = preview(alice, a, c).json()
    assert route["connected"] is True
    assert [x["node_id"] for x in route["path"]] == [a, b, c]
    assert [e["source"] for e in route["legs"]] == ["user", "user"]
    assert all(not x["verified"] for x in route["legs"])
    assert "未" not in route["notice"] or "因果" in route["notice"]
    assert preview(alice, c, a).json()["connected"] is True


def test_shortest_path_and_deterministic_older_edge_tie_break(env):
    alice, bob, guest = env
    a, b, c, d = (idea(alice, title) for title in ("起点", "甲", "乙", "终点"))
    link(alice, a, b)
    link(alice, b, d)
    link(alice, a, c)
    link(alice, c, d)
    route = preview(alice, a, d).json()
    assert [x["node_id"] for x in route["path"]] == [a, b, d]
    link(alice, a, d)
    assert [x["node_id"] for x in preview(alice, a, d).json()["path"]] == [a, d]


def test_checkpoint_marking_can_be_undone_and_is_never_real_visit_proof(env):
    alice, bob, guest = env
    a, b = idea(alice, "起点"), idea(alice, "终点")
    link(alice, a, b)
    rid = save(alice, a, b).json()["voyage"]["id"]
    response = alice.put(f"/api/constellation/voyages/{rid}/checkpoints/{a}")
    assert response.status_code == 200
    assert "自行" in response.json()["notice"] or "私人" in response.json()["notice"]
    current = alice.get(f"/api/constellation/voyages/{rid}").json()
    assert current["marked_count"] == 1
    assert current["path"][0]["marked"] is True
    assert current["path"][1]["marked"] is False
    other = idea(alice, "游离星点")
    assert alice.put(f"/api/constellation/voyages/{rid}/checkpoints/{other}").status_code == 409
    assert alice.delete(f"/api/constellation/voyages/{rid}/checkpoints/{a}").status_code == 200
    assert alice.get(f"/api/constellation/voyages/{rid}").json()["marked_count"] == 0


def test_deleted_edge_disconnects_without_fabricating_a_route(env):
    alice, bob, guest = env
    a, b, c = (idea(alice, x) for x in ("起点", "中转", "终点"))
    link(alice, a, b)
    last = link(alice, b, c)
    rid = save(alice, a, c, "不可变快照不能留").json()["voyage"]["id"]
    assert alice.put(f"/api/constellation/voyages/{rid}/checkpoints/{b}").status_code == 200
    assert alice.delete(f"/api/constellation/edges/{last}").status_code == 200
    gone = alice.get(f"/api/constellation/voyages/{rid}").json()
    assert gone["connected"] is False
    assert gone["path"] == [] and gone["legs"] == []
    assert gone["name"] == "航线暂不可用"
    assert gone["marked_count"] == 0
    assert alice.put(f"/api/constellation/voyages/{rid}/checkpoints/{b}").status_code == 409
    link(alice, b, c)
    recovered = alice.get(f"/api/constellation/voyages/{rid}").json()
    assert recovered["connected"] is True
    assert recovered["marked_count"] == 1
    assert alice.delete(f"/api/constellation/voyages/{rid}").status_code == 200
    assert alice.get(f"/api/constellation/voyages/{rid}").status_code == 404
    assert len(alice.get("/api/constellation").json()["nodes"]) == 3


def test_withdrawn_third_party_exhibit_cannot_leak_through_path(env):
    alice, bob, guest = env
    source = bob.post("/api/exhibits", json=item(title="被撤回的世界遗产",
                          tags="文化,历史")).json()
    start, bridge, end = idea(alice, "私人起点"), exhibit_node(alice, source["id"]), idea(alice, "私人终点")
    link(alice, start, bridge)
    link(alice, bridge, end)
    rid = save(alice, start, end, "涉及被撤回的世界遗产").json()["voyage"]["id"]
    visible = alice.get(f"/api/constellation/voyages/{rid}").json()
    assert "被撤回的世界遗产" in str(visible)
    changed = bob.patch(f"/api/exhibits/{source['id']}", json=item(
        title="被撤回的世界遗产", tags="文化,历史", visibility="private"))
    assert changed.status_code == 200, changed.text
    hidden = alice.get(f"/api/constellation/voyages/{rid}").json()
    assert hidden["connected"] is False and hidden["path"] == []
    assert "被撤回的世界遗产" not in str(hidden)
    assert "被撤回的世界遗产" not in str(alice.get("/api/constellation/voyages").json())
    assert preview(alice, start, end).json()["connected"] is False
    assert alice.put(f"/api/constellation/voyages/{rid}/checkpoints/{bridge}").status_code == 409
    changed = bob.patch(f"/api/exhibits/{source['id']}", json=item(
        title="被撤回的世界遗产", tags="文化,历史", visibility="public"))
    assert changed.status_code == 200
    assert alice.get(f"/api/constellation/voyages/{rid}").json()["connected"] is True


def test_other_users_nodes_are_unreachable_and_bad_requests_rejected(env):
    alice, bob, guest = env
    a, b = idea(alice, "甲起点"), idea(alice, "乙终点")
    foreign = idea(bob, "别人的秘密星点")
    assert preview(alice, a, foreign).json()["connected"] is False
    assert save(alice, a, foreign).status_code == 409
    assert save(alice, a, a).status_code == 422
    assert preview(alice, a, a).status_code == 422
    link(alice, a, b)
    assert save(alice, a, b, "  ").status_code == 422
    assert save(alice, a, b, "x"*61).status_code == 422


def test_v28_static_assets_server_version_and_nav(env):
    alice, bob, guest = env
    assert guest.get("/api/health").json()["version"] == "36.0"
    home = guest.get("/").text
    assert "万物星图" in home
    for asset in ("voyages.js", "voyages.css"):
        assert f"/static/{asset}" in home
        assert guest.get(f"/static/{asset}").status_code == 200
    scripts = guest.get("/static/constellation.js").text
    assert "WonderVoyages.render" in scripts
