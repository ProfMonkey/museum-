"""V29 parallel universes: bilateral consent, live public-only records, no private map leak."""
import sys

from test_multiuser import env, item


def exhibit(client, title, **kwargs):
    r = client.post("/api/exhibits", json=item(title=title, **kwargs))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def overview(client):
    return client.get("/api/parallel")


def invite(client, recipient, exhibit_id):
    return client.post("/api/parallel/invitations",
                       json={"recipient": recipient, "exhibit_id": exhibit_id})


def accept(client, invite_id, exhibit_id):
    return client.post(f"/api/parallel/invitations/{invite_id}/accept",
                       json={"exhibit_id": exhibit_id})


def test_privacy_guest_denied_and_no_spurious_public_graph_export(env):
    alice, bob, guest = env
    assert overview(guest).status_code == 401
    assert guest.get("/api/parallel/suggestions?exhibit_id=1").status_code == 401
    assert invite(guest, "Bob", 1).status_code == 401
    assert guest.get("/api/parallel/bridges/1").status_code == 401
    assert guest.put("/api/parallel/bridges/1/mark").status_code == 401
    assert overview(alice).json()["mine"] == []
    assert overview(bob).json()["incoming"] == []
    assert "星图" in overview(alice).json()["notice"]


def test_invitation_uses_only_senders_live_public_owned_exhibit(env):
    alice, bob, guest = env
    own = exhibit(alice, "公开的米线图谱", tags="云南,米线")
    private = exhibit(alice, "不能加入的私人日记", visibility="private")
    foreign = exhibit(bob, "鲍勃的珍贵图谱", tags="云南,风景")
    assert invite(alice, "Bob", private).status_code == 404
    assert invite(alice, "Bob", foreign).status_code == 404
    assert invite(alice, "Bob", 999999).status_code == 404
    assert invite(alice, "Nobody", own).status_code == 404
    assert invite(alice, "Alice", own).status_code == 400
    r = invite(alice, "bOb", own)
    assert r.status_code == 201, r.text
    assert r.json()["recipient"] == "Bob"
    iid = r.json()["id"]
    assert invite(alice, "Bob", own).status_code == 409
    received = overview(bob).json()["incoming"]
    assert len(received) == 1 and received[0]["id"] == iid
    assert received[0]["sender_exhibit"]["title"] == "公开的米线图谱"
    assert received[0]["recipient_exhibit"] is None
    assert overview(alice).json()["outgoing"][0]["id"] == iid
    assert overview(guest).status_code == 401


def test_recipient_must_consent_choose_owned_public_cannot_be_forged(env):
    alice, bob, guest = env
    a = exhibit(alice, "甲的公开藏品")
    b = exhibit(bob, "乙的公开藏品")
    secret = exhibit(bob, "乙的秘密", visibility="private")
    iid = invite(alice, "Bob", a).json()["id"]
    assert accept(alice, iid, a).status_code == 403
    assert accept(bob, iid, a).status_code == 404
    assert accept(bob, iid, secret).status_code == 404
    r = accept(bob, iid, b)
    assert r.status_code == 200, r.text
    bridge = r.json()["bridge"]
    assert bridge["status"] == "accepted"
    assert bridge["sender_exhibit"]["title"] == "甲的公开藏品"
    assert bridge["recipient_exhibit"]["title"] == "乙的公开藏品"
    assert bridge["clue"] is None
    assert accept(bob, iid, b).status_code == 409
    assert len(overview(alice).json()["bridges"]) == 1
    assert len(overview(bob).json()["bridges"]) == 1
    assert overview(alice).json()["incoming"] == []


def test_decline_cancel_and_authorization(env):
    alice, bob, guest = env
    a = exhibit(alice, "甲")
    exhibit(bob, "乙")
    iid = invite(alice, "Bob", a).json()["id"]
    assert bob.post(f"/api/parallel/invitations/{iid}/cancel").status_code == 403
    assert alice.post(f"/api/parallel/invitations/{iid}/decline").status_code == 403
    assert bob.post(f"/api/parallel/invitations/{iid}/decline").status_code == 200
    assert bob.post(f"/api/parallel/invitations/{iid}/decline").status_code == 409
    assert accept(bob, iid, 1).status_code == 409
    second = invite(alice, "Bob", a).json()["id"]
    assert alice.post(f"/api/parallel/invitations/{second}/cancel").status_code == 200
    assert alice.post(f"/api/parallel/invitations/{second}/cancel").status_code == 409
    assert overview(alice).json()["outgoing"] == []
    assert overview(bob).json()["incoming"] == []


def test_mark_each_independently_both_completion_and_close(env):
    alice, bob, guest = env
    a = exhibit(alice, "甲星")
    b = exhibit(bob, "乙星")
    iid = invite(alice, "Bob", a).json()["id"]
    assert accept(bob, iid, b).status_code == 200
    assert bob.get(f"/api/parallel/bridges/{iid}").status_code == 200
    assert guest.get(f"/api/parallel/bridges/{iid}").status_code == 401
    assert alice.put(f"/api/parallel/bridges/{iid}/mark").status_code == 200
    first = overview(alice).json()["bridges"][0]["progress"]
    assert first == {"mine": True, "partner": False, "both": False}
    assert overview(bob).json()["bridges"][0]["progress"] == {
        "mine": False, "partner": True, "both": False}
    assert bob.put(f"/api/parallel/bridges/{iid}/mark").status_code == 200
    assert overview(alice).json()["bridges"][0]["progress"]["both"]
    assert bob.delete(f"/api/parallel/bridges/{iid}/mark").status_code == 200
    assert not overview(alice).json()["bridges"][0]["progress"]["both"]
    assert bob.delete(f"/api/parallel/bridges/{iid}").status_code == 200
    assert overview(alice).json()["bridges"] == []
    assert overview(bob).json()["bridges"] == []
    assert alice.get(f"/api/parallel/bridges/{iid}").status_code == 404
    assert alice.put(f"/api/parallel/bridges/{iid}/mark").status_code == 409
    assert alice.get(f"/api/exhibits/{a}").status_code == 200


def test_privacy_revocation_redacts_both_endpoints_and_progress(env):
    alice, bob, guest = env
    a = exhibit(alice, "被撤回的甲方标题", tags="地理,文化")
    b = exhibit(bob, "乙方仍公开的标题", tags="地理,文化")
    iid = invite(alice, "Bob", a).json()["id"]
    accept(bob, iid, b)
    alice.put(f"/api/parallel/bridges/{iid}/mark")
    hidden = alice.patch(f"/api/exhibits/{a}", json=item(
        title="被撤回的甲方标题", tags="地理,文化", visibility="private"))
    assert hidden.status_code == 200
    for client in (alice, bob):
        v = client.get(f"/api/parallel/bridges/{iid}").json()
        assert v["available"] is False
        assert v["sender_exhibit"] is None and v["recipient_exhibit"] is None
        assert v["clue"] is None
        assert v["progress"]["both"] is False
        assert "被撤回的甲方标题" not in str(v)
        assert "乙方仍公开的标题" not in str(v)
        assert "被撤回的甲方标题" not in str(overview(client).json())
        assert "乙方仍公开的标题" not in str(overview(client).json())
    assert bob.put(f"/api/parallel/bridges/{iid}/mark").status_code == 409
    assert bob.delete(f"/api/parallel/bridges/{iid}/mark").status_code == 200
    restored = alice.patch(f"/api/exhibits/{a}", json=item(
        title="被撤回的甲方标题", tags="地理,文化", visibility="public"))
    assert restored.status_code == 200
    available = overview(bob).json()["bridges"][0]
    assert available["available"] is True
    assert available["sender_exhibit"]["title"] == "被撤回的甲方标题"


def test_pending_source_withdrawal_hides_title_and_blocks_accept(env):
    alice, bob, guest = env
    a = exhibit(alice, "待处理的旧秘密藏品")
    b = exhibit(bob, "受邀者的公开物件")
    iid = invite(alice, "Bob", a).json()["id"]
    assert alice.delete(f"/api/exhibits/{a}").status_code == 200
    incoming = overview(bob).json()["incoming"][0]
    assert incoming["available"] is False
    assert incoming["sender_exhibit"] is None
    assert "待处理的旧秘密藏品" not in str(incoming)
    assert accept(bob, iid, b).status_code == 409
    assert bob.post(f"/api/parallel/invitations/{iid}/decline").status_code == 200


def test_public_suggestions_exclude_private_and_show_exact_reasons(env):
    alice, bob, guest = env
    a = exhibit(alice, "古代米线", tags="云南,饮食",
                category="饮食文化", domain="生活方式")
    similar = exhibit(bob, "云南的茶文化", tags="云南,茶叶",
                      category="饮食文化", domain="生活方式")
    hidden = exhibit(bob, "秘密云南日记", tags="云南,饮食",
                     category="饮食文化", domain="生活方式", visibility="private")
    unrelated = exhibit(bob, "机械臂", tags="电机,电路",
                        category="科技与发明", domain="工程与发明")
    result = alice.get(f"/api/parallel/suggestions?exhibit_id={a}")
    assert result.status_code == 200, result.text
    cards = result.json()["items"]
    assert len(cards) == 1
    assert cards[0]["id"] == similar
    assert cards[0]["curator"] == "Bob"
    assert "共同标签" in cards[0]["reason"]
    assert hidden not in [x["id"] for x in cards]
    assert unrelated not in [x["id"] for x in cards]
    assert "不代表" in result.json()["notice"]
    assert bob.get(f"/api/parallel/suggestions?exhibit_id={a}").status_code == 404


def test_parent_studio_visibility_must_be_public(env):
    alice, bob, guest = env
    a = exhibit(alice, "外观公开但被私人项目遮蔽的展品", tags="关联,秘密")
    b = exhibit(bob, "常规公开物件", tags="关联")
    import sys
    module = sys.modules["wa_test_server"]
    with module.db() as c:
        # Model the public-exhibit / private-project mismatch explicitly.
        c.execute("""INSERT INTO creator_studio_projects
             (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
             VALUES(?,?,?,?,?,?,?,?)""",
             (1, a, "内部作品", "quiz", "private", "{}", module.now(), module.now()))
    assert invite(alice, "Bob", a).status_code == 404
    assert alice.get(f"/api/parallel/suggestions?exhibit_id={a}").status_code == 404


def test_v29_assets_version_and_navigation(env):
    alice, bob, guest = env
    assert guest.get("/api/health").json()["version"] == "29.0"
    html = guest.get("/").text
    assert "万物平行宇宙" in html
    assert "WONDER ATLAS · WORLD 29" in html
    for filename in ("parallel.js", "parallel.css"):
        assert f"/static/{filename}" in html
        assert guest.get(f"/static/{filename}").status_code == 200
    assert "WonderParallel.render" in guest.get("/static/app.js").text
