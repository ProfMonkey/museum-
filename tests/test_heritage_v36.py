"""V36 real HTTP boundaries: V35 consent, two-owned gifts and private notes.

Tests are run by developers LOCALLY; GitHub Actions automatic triggers are off.
"""
from test_multiuser import env, item
from test_embassies_v35 import setup, invite, accept, letter, approve
from test_collision_v33 import exhibit


def embassy_ready(alice,bob):
    a,b,aw,bw,ax,bx,p=setup(alice,bob)
    created=invite(alice,p)
    assert created.status_code==201,created.text
    eid=created.json()["id"]
    assert accept(bob,eid).status_code==200
    assert letter(alice,eid,"由青铜文明亲自写下的第一封外交信").status_code==201
    assert letter(bob,eid,"来自机械文明的独立外交正式国书").status_code==201
    assert approve(alice,eid).status_code==200
    assert approve(bob,eid).status_code==200
    return eid,ax,bx


def draft(alice,eid,ax,bx):
    return alice.post("/api/heritage",json={
        "embassy_id":eid,"a_exhibit_id":ax,"b_exhibit_id":bx,
        "title":"古代藏品与未来科技相遇",
        "premise":"两位真实馆长使用各自真正公开的原始馆藏，共同建立一项象征性的跨世界文化礼物。"
    })


def note(client,x,text):
    return client.put(f"/api/heritage/{x}/note",json={"text":text})


def ready_public(alice,bob):
    eid,ax,bx=embassy_ready(alice,bob)
    r=draft(alice,eid,ax,bx)
    assert r.status_code==201,r.text
    x=r.json()["id"]
    assert note(alice,x,"这件藏品记录了我们的文化记忆，也象征两个文明对彼此的尊重。").status_code==200
    assert note(bob,x,"我愿分享另一件公开藏品背后的故事，但原始藏品所有权仍在我手中。").status_code==200
    assert alice.post(f"/api/heritage/{x}/approve").status_code==200
    second=bob.post(f"/api/heritage/{x}/approve")
    assert second.status_code==200 and second.json()["published"],second.text
    return x,eid,ax,bx


def test_no_fake_public_exchanges_or_forged_anonymous_participation(env):
    alice,bob,guest=env
    assert guest.get("/api/heritage/public").json()["items"]==[]
    assert guest.get("/api/heritage/mine").status_code==401
    assert guest.get("/api/heritage/embassies").status_code==401
    assert guest.get("/api/heritage/sources?embassy_id=1").status_code==401
    assert guest.post("/api/heritage",json={"embassy_id":1}).status_code==401
    assert guest.get("/api/heritage/123").status_code==404


def test_invitation_is_not_enough_only_public_embassies_and_true_owners(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,bx,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    assert draft(alice,eid,ax,bx).status_code==404
    accept(bob,eid)
    assert draft(alice,eid,ax,bx).status_code==404
    letter(alice,eid,"青铜国的第一封独立外交书信")
    letter(bob,eid,"机械国的真实回应")
    approve(alice,eid)
    assert draft(alice,eid,ax,bx).status_code==404
    approve(bob,eid)
    assert draft(alice,eid,bx,ax).status_code==404
    secret=exhibit(alice,"秘密文物",visibility="private")
    assert draft(alice,eid,secret,bx).status_code==404
    assert draft(bob,eid,ax,bx).status_code==201
    assert alice.get("/api/heritage/embassies").json()["items"][0]["id"]==eid
    src=alice.get(f"/api/heritage/sources?embassy_id={eid}").json()
    assert any(e["id"]==ax for e in src["a"])
    assert any(e["id"]==bx for e in src["b"])
    assert all(e["id"]!=secret for e in src["a"])


def test_owner_signatures_and_both_approvals_version_exact(env):
    alice,bob,guest=env
    eid,ax,bx=embassy_ready(alice,bob)
    x=draft(alice,eid,ax,bx).json()["id"]
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert guest.get("/api/heritage/public").json()["items"]==[]
    assert alice.post(f"/api/heritage/{x}/approve").status_code==409
    assert note(alice,x,"青铜文明主动奉献这件公开藏品背后的象征故事，纯属文化交流而非产权移交。").status_code==200
    assert note(bob,x,"来自机械文明的自述告诉旅行者：这是艺术想象的外交礼物，不是现实物品交易。").status_code==200
    assert alice.get(f"/api/heritage/{x}").json()["approved"]=={"a":False,"b":False}
    first=alice.post(f"/api/heritage/{x}/approve")
    assert first.status_code==200 and first.json()["published"] is False
    assert guest.get(f"/api/heritage/{x}").status_code==404
    second=bob.post(f"/api/heritage/{x}/approve")
    assert second.status_code==200 and second.json()["published"] is True
    d=guest.get(f"/api/heritage/{x}").json()
    assert d["approved"]=={"a":True,"b":True}
    assert d["a_note"].startswith("青铜文明") and d["b_note"].startswith("来自机械文明")
    assert d["a"]["id"]==ax and d["b"]["id"]==bx
    assert "产权" in d["notice"]
    assert alice.get("/api/heritage/public").json()["items"][0]["id"]==x
    change=note(bob,x,"机械国改变了对这件原始文物的解读：它是一扇通往文明理解的大门，而非真正送出的实物。")
    assert change.status_code==200
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert alice.get(f"/api/heritage/{x}").json()["approved"]=={"a":False,"b":False}
    assert alice.post(f"/api/heritage/{x}/approve").json()["published"] is False
    assert guest.get("/api/heritage/public").json()["items"]==[]
    assert bob.post(f"/api/heritage/{x}/approve").json()["published"] is True


def test_each_author_only_edits_their_own_cultural_note(env):
    alice,bob,guest=env
    eid,ax,bx=embassy_ready(alice,bob)
    x=draft(alice,eid,ax,bx).json()["id"]
    assert note(alice,x,"我为这件真实原始文物写下自己的文化解释，绝不冒充另一位馆长。").status_code==200
    assert alice.get(f"/api/heritage/{x}").json()["b_note"]==""
    assert note(bob,x,"作为另一件公开藏品的真正馆长，我愿意以另一种方式讲述它的文化意义。").status_code==200
    r=alice.get(f"/api/heritage/{x}").json()
    assert r["a_note"].startswith("我为这件") and r["b_note"].startswith("作为另一件")
    assert guest.put(f"/api/heritage/{x}/note",json={"text":"匿名人不能篡改别人的稿件与内容"}).status_code==401
    assert note(alice,x,"很短").status_code==422


def test_single_real_visitor_stamp_per_version_and_revocation(env):
    alice,bob,guest=env
    x,eid,ax,bx=ready_public(alice,bob)
    assert guest.post(f"/api/heritage/{x}/passport").status_code==401
    r=alice.post(f"/api/heritage/{x}/passport")
    assert r.status_code==200,r.text
    assert r.json()["passports"]==1
    assert alice.post(f"/api/heritage/{x}/passport").json()["passports"]==1
    assert bob.post(f"/api/heritage/{x}/passport").json()["passports"]==2
    assert guest.get(f"/api/heritage/{x}").json()["passports"]==2
    assert alice.get(f"/api/heritage/{x}").json()["my_passport"] is True
    assert alice.post(f"/api/heritage/{x}/retract").status_code==200
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert alice.post(f"/api/heritage/{x}/approve").json()["published"] is False
    assert bob.post(f"/api/heritage/{x}/approve").json()["published"] is True
    assert guest.get(f"/api/heritage/{x}").json()["passports"]==0
    assert alice.get(f"/api/heritage/{x}").json()["my_passport"] is False


def test_withdrawn_source_exhibit_hides_all_descriptions_even_for_participant(env):
    alice,bob,guest=env
    x,eid,ax,bx=ready_public(alice,bob)
    changed=alice.patch(f"/api/exhibits/{ax}",json=item(title="古老钟楼",visibility="private"))
    assert changed.status_code==200,changed.text
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert guest.get("/api/heritage/public").json()["items"]==[]
    masked=bob.get(f"/api/heritage/{x}").json()
    assert masked["available"] is False
    assert masked["a"] is None and masked["b"] is None
    assert masked["a_note"]=="" and masked["b_note"]==""
    assert "古老钟楼" not in str(masked)
    assert "公开藏品" not in str(masked)
    assert bob.get("/api/heritage/mine").json()["items"][0]["available"] is False
    assert bob.post(f"/api/heritage/{x}/approve").status_code==409
    assert bob.post(f"/api/heritage/{x}/rebase").status_code==409


def test_v35_embassy_change_revokes_v36_until_rebased_and_both_reapprove(env):
    alice,bob,guest=env
    x,eid,ax,bx=ready_public(alice,bob)
    assert guest.get(f"/api/heritage/{x}").status_code==200
    assert bob.post(f"/api/embassies/{eid}/retract").status_code==200
    assert guest.get("/api/heritage/public").json()["items"]==[]
    assert alice.post(f"/api/heritage/{x}/rebase").status_code==409
    assert approve(alice,eid).status_code==200
    assert approve(bob,eid).status_code==200
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert alice.post(f"/api/heritage/{x}/approve").status_code==409
    rebase=bob.post(f"/api/heritage/{x}/rebase")
    assert rebase.status_code==200,rebase.text
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert alice.post(f"/api/heritage/{x}/approve").json()["published"] is False
    assert bob.post(f"/api/heritage/{x}/approve").json()["published"] is True
    assert guest.get(f"/api/heritage/{x}").status_code==200


def test_cancelling_exchange_preserves_both_real_source_exhibits(env):
    alice,bob,guest=env
    x,eid,ax,bx=ready_public(alice,bob)
    assert bob.post(f"/api/heritage/{x}/close").status_code==200
    assert guest.get(f"/api/heritage/{x}").status_code==404
    assert guest.get("/api/heritage/public").json()["items"]==[]
    assert alice.get(f"/api/exhibits/{ax}").status_code==200
    assert bob.get(f"/api/exhibits/{bx}").status_code==200
    assert alice.post(f"/api/heritage/{x}/rebase").status_code==409


def test_v36_frontend_and_version_with_no_automatic_actions(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="36.0"
    html=guest.get("/").text
    assert "万界遗产交换站" in html
    assert "WORLD 36" in html
    for f in ("heritage.js","heritage.css"):
        assert f"/static/{f}" in html
        assert guest.get(f"/static/{f}").status_code==200
    assert "WonderHeritage.render" in guest.get("/static/app.js").text
