"""V35 local-only tests: no simulated envoys, bilateral consent and source privacy."""
from test_multiuser import env, item
from test_civilizations_v34 import origin, civ, turn, publish


def make_civ(owner,other,label):
    wid,x,y=origin(owner,other)
    r=civ(owner,wid,x,name=label)
    assert r.status_code==201,r.text
    cid=r.json()["id"]
    assert turn(owner,cid,"research").status_code==201
    assert turn(owner,cid,"arts","第二个文明时代开始").status_code==201
    assert publish(owner,cid).status_code==200
    return cid,wid,x,y


def setup(alice,bob):
    a,aw,ax,ay=make_civ(alice,bob,"真实的青铜文明")
    b,bw,bx,by=make_civ(bob,alice,"真正的机械文明")
    payload={"my_civ_id":a,"other_civ_id":b,
        "title":"青铜国与机械国第一次会盟",
        "preface":"这是两位独立真实馆长在虚构的两个文明之间共同创造的外交历史。"}
    return a,b,aw,bw,ax,bx,payload


def invite(alice,payload):
    return alice.post("/api/embassies",json=payload)


def accept(bob,eid):
    return bob.post(f"/api/embassies/{eid}/accept")


def letter(client,eid,subject):
    return client.post(f"/api/embassies/{eid}/letters",json={
        "subject":subject,
        "message":"我作为这一座虚构文明的真正馆长，亲笔记录我们如何与另一国相遇、沟通与交流。"})


def detail(client,eid):
    return client.get(f"/api/embassies/{eid}")


def approve(client,eid):
    return client.post(f"/api/embassies/{eid}/approve")


def test_no_fake_diplomats_or_public_archives_without_real_members(env):
    alice,bob,guest=env
    assert guest.get("/api/embassies/public").json()["items"]==[]
    assert guest.get("/api/embassies/mine").status_code==401
    assert guest.post("/api/embassies",json={
        "my_civ_id":1,"other_civ_id":2,
        "title":"不应出现的邀请","preface":"未登录的匿名用户不可冒充任何文明馆长。" }).status_code==401
    assert guest.get("/api/embassies/1").status_code==404


def test_real_owner_to_owner_invitation_and_explicit_acceptance(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,by,p=setup(alice,bob)
    assert invite(bob,p).status_code==404
    created=invite(alice,p)
    assert created.status_code==201,created.text
    eid=created.json()["id"]
    assert created.json()["state"]=="pending"
    assert invite(alice,p).status_code==409
    assert detail(guest,eid).status_code==404
    assert detail(alice,eid).json()["is_member"] is True
    assert detail(bob,eid).json()["my_role"]=="b"
    assert approve(alice,eid).status_code==409
    assert alice.post(f"/api/embassies/{eid}/accept").status_code==409
    assert accept(bob,eid).status_code==200
    assert accept(bob,eid).status_code==409
    assert approve(alice,eid).status_code==409
    mine=bob.get("/api/embassies/mine").json()
    assert any(x["id"]==eid for x in mine["items"])
    assert any(x["id"]==b for x in mine["my_civilizations"])
    assert any(x["id"]==a for x in mine["other_civilizations"])


def test_two_real_letters_and_bilateral_same_revision_approval(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,by,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    assert accept(bob,eid).status_code==200
    assert letter(alice,eid,"第一封来自青铜国的亲笔信").status_code==201
    assert approve(alice,eid).status_code==409
    assert letter(bob,eid,"来自机械国的正式国书").status_code==201
    first=approve(alice,eid)
    assert first.status_code==200,first.text
    d=first.json()["embassy"]
    assert d["state"]=="accepted"
    assert d["approved"]=={"a":True,"b":False}
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/embassies/public").json()["items"]==[]
    second=approve(bob,eid)
    assert second.status_code==200,second.text
    d=second.json()["embassy"]
    assert d["state"]=="public"
    assert d["approved"]=={"a":True,"b":True}
    public=detail(guest,eid)
    assert public.status_code==200
    assert public.json()["title"]==p["title"]
    assert [x["curator"] for x in public.json()["letters"]]==["Alice","Bob"]
    assert guest.get("/api/embassies/public").json()["items"][0]["letters"]==2


def test_cannot_forge_another_curator_or_remove_other_letter(env):
    alice,bob,guest=env
    *_,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    assert accept(bob,eid).status_code==200
    ra=letter(alice,eid,"我的青铜外交来函")
    assert ra.status_code==201
    la=ra.json()["id"]
    assert bob.delete(f"/api/embassies/{eid}/letters/{la}").status_code==403
    assert guest.delete(f"/api/embassies/{eid}/letters/{la}").status_code==401
    assert bob.put(f"/api/embassies/{eid}",json={"title":"短","preface":"短"}).status_code==422
    assert alice.delete(f"/api/embassies/{eid}/letters/{la}").status_code==200
    assert detail(alice,eid).json()["letters"]==[]


def test_edit_and_retraction_hide_public_until_new_mutual_approval(env):
    alice,bob,guest=env
    *_,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    accept(bob,eid);letter(alice,eid,"首次外交来函");letter(bob,eid,"第二位馆长的独立来函")
    approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    changed=alice.put(f"/api/embassies/{eid}",json={
        "title":"修订后的国王会盟记录",
        "preface":"两位馆长重新研究了故事并决定让这一次虚构外交谈判有不同的叙事前言。"})
    assert changed.status_code==200
    assert detail(guest,eid).status_code==404
    d=detail(alice,eid).json()
    assert d["approved"]=={"a":False,"b":False}
    approve(alice,eid)
    assert detail(guest,eid).status_code==404
    approve(bob,eid)
    assert detail(guest,eid).status_code==200
    assert bob.post(f"/api/embassies/{eid}/retract").status_code==200
    assert detail(guest,eid).status_code==404
    approve(alice,eid);approve(bob,eid)
    new_letter=letter(bob,eid,"第三封外交书信改变历史")
    assert new_letter.status_code==201
    assert detail(guest,eid).status_code==404
    assert detail(alice,eid).json()["approved"]=={"a":False,"b":False}


def test_underlying_v34_change_invalidates_snapshots_until_refresh_and_reapprove(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,by,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    accept(bob,eid);letter(alice,eid,"真实馆长原版来函");letter(bob,eid,"对方原版独立来函")
    approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    changed=alice.put(f"/api/civilizations/{a}",json={
        "name":"更新后的青铜文明",
        "charter":"馆长修改了文明的设定，因此当时原先双方同意的外交纪事需要重新确认真实性。"})
    assert changed.status_code==200
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/embassies/public").json()["items"]==[]
    assert detail(alice,eid).json()["available"] is False
    assert "真实馆长原版来函" not in str(detail(alice,eid).json())
    assert bob.post(f"/api/embassies/{eid}/approve").status_code==409
    assert alice.post(f"/api/civilizations/{a}/publish").status_code==200
    assert detail(guest,eid).status_code==404
    refreshed=bob.post(f"/api/embassies/{eid}/refresh")
    assert refreshed.status_code==200,refreshed.text
    assert refreshed.json()["state"]=="accepted"
    assert detail(alice,eid).json()["available"] is True
    assert detail(guest,eid).status_code==404
    approve(alice,eid)
    assert detail(guest,eid).status_code==404
    approve(bob,eid)
    assert detail(guest,eid).status_code==200


def test_live_source_withdrawal_hides_all_public_and_member_text(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,by,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    accept(bob,eid);letter(alice,eid,"永不泄漏的双边秘密");letter(bob,eid,"第二封外交秘密")
    approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    private=bob.patch(f"/api/exhibits/{by}",json=item(
        title="古老钟楼",visibility="private"))
    assert private.status_code==200,private.text
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/embassies/public").json()["items"]==[]
    for client in (alice,bob):
        d=detail(client,eid).json()
        assert not d["available"]
        assert d["title"]=="来源已经更新或撤回"
        assert d["preface"]==""
        assert d["letters"]==[]
        assert d["a"] is None and d["b"] is None
        assert "永不泄漏的双边秘密" not in str(d)
    assert bob.post(f"/api/embassies/{eid}/approve").status_code==409


def test_real_recipient_can_decline_sender_can_cancel_and_either_close(env):
    alice,bob,guest=env
    *_,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    assert alice.post(f"/api/embassies/{eid}/decline").status_code==409
    assert bob.post(f"/api/embassies/{eid}/cancel").status_code==409
    assert bob.post(f"/api/embassies/{eid}/decline").status_code==200
    assert accept(bob,eid).status_code==409
    other=invite(alice,p).json()["id"]
    assert alice.post(f"/api/embassies/{other}/cancel").status_code==200
    assert accept(bob,other).status_code==409
    third=invite(alice,p).json()["id"]
    accept(bob,third)
    assert alice.post(f"/api/embassies/{third}/close").status_code==200
    assert detail(guest,third).status_code==404
    assert letter(bob,third,"迟到的外交书信").status_code==409


def test_content_validation_and_same_account_pairs(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,by,p=setup(alice,bob)
    assert invite(alice,{**p,"my_civ_id":a,"other_civ_id":a}).status_code==422
    assert invite(alice,{**p,"preface":"太短"}).status_code==422
    eid=invite(alice,p).json()["id"]
    assert letter(alice,eid,"尚未接受的来信").status_code==409
    accept(bob,eid)
    assert alice.post(f"/api/embassies/{eid}/letters",json={
        "subject":"短","message":"太短"}).status_code==422
    assert guest.get("/api/embassies/public").json()["items"]==[]


def test_v35_nav_version_and_manual_only_policy(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="39.0"
    html=guest.get("/").text
    assert "WORLD 35" in html
    assert "万界文明大使馆" in html
    for file in ("embassies.js","embassies.css"):
        assert f"/static/{file}" in html
        assert guest.get(f"/static/{file}").status_code==200
    assert "WonderEmbassies.render" in guest.get("/static/app.js").text

def test_same_second_private_to_public_still_invalidates_old_joint_approval(env):
    alice,bob,guest=env
    a,b,aw,bw,ax,bx,p=setup(alice,bob)
    eid=invite(alice,p).json()["id"]
    assert accept(bob,eid).status_code==200
    assert letter(alice,eid,"第一位馆长来函").status_code==201
    assert letter(bob,eid,"第二位馆长亲笔回复").status_code==201
    approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    assert bob.patch(f"/api/exhibits/{bx}",
        json=item(title="古老钟楼",visibility="private")).status_code==200
    assert bob.patch(f"/api/exhibits/{bx}",
        json=item(title="古老钟楼",visibility="public")).status_code==200
    assert detail(guest,eid).status_code==404
    assert detail(alice,eid).json()["available"] is False
    assert alice.post(f"/api/embassies/{eid}/refresh").status_code==200
    assert detail(guest,eid).status_code==404
    assert approve(bob,eid).status_code==200
    assert detail(guest,eid).status_code==404
    assert approve(alice,eid).status_code==200
    assert detail(guest,eid).status_code==200
