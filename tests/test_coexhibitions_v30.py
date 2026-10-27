"""V30 bilateral exhibition integration: approval revisions, live sources, stamps, tours."""
import pytest
from test_multiuser import env, item
from test_parallel_v29 import exhibit, invite, accept


def joint(client, bridge_id, title="两个世界的联合展览", intro="两位馆长共同策划与讲解。"):
    return client.post("/api/coexhibitions",
                       json={"bridge_id":bridge_id,"title":title,"introduction":intro})


def contribute(client, exhibition_id, exhibit_id, commentary="这是我亲自贡献的公开展品，带大家进入不同世界。"):
    return client.post(f"/api/coexhibitions/{exhibition_id}/items",
                       json={"exhibit_id":exhibit_id,"commentary":commentary})


def setup_pair(alice, bob):
    a=exhibit(alice,"甲的古代交通",tags="云南,交通")
    b=exhibit(bob,"乙的茶马古道",tags="云南,历史")
    bid=invite(alice,"Bob",a).json()["id"]
    accepted=accept(bob,bid,b)
    assert accepted.status_code==200,accepted.text
    result=joint(alice,bid)
    assert result.status_code==201,result.text
    return result.json()["exhibition"]["id"],a,b,bid


def detail(client, ident):
    return client.get(f"/api/coexhibitions/{ident}")


def approve(client, ident):
    return client.post(f"/api/coexhibitions/{ident}/approve")


def test_requires_real_bilateral_v29_consent_and_private_drafts(env):
    alice,bob,guest=env
    a=exhibit(alice,"真实公开甲")
    b=exhibit(bob,"真实公开乙")
    bid=invite(alice,"Bob",a).json()["id"]
    assert joint(alice,bid).status_code==409
    assert joint(bob,bid).status_code==409
    assert joint(guest,bid).status_code==401
    assert accept(bob,bid,b).status_code==200
    created=joint(alice,bid)
    assert created.status_code==201,created.text
    eid=created.json()["exhibition"]["id"]
    assert created.json()["exhibition"]["state"]=="draft"
    assert joint(alice,bid).status_code==409
    assert detail(guest,eid).status_code==404
    assert alice.get("/api/coexhibitions/mine").json()["items"][0]["id"]==eid
    assert bob.get("/api/coexhibitions/mine").json()["items"][0]["id"]==eid
    assert guest.get("/api/coexhibitions/mine").status_code==401
    assert guest.get("/api/coexhibitions/public").json()["items"]==[]


def test_publish_requires_each_owner_contribution_and_both_same_revision(env):
    alice,bob,guest=env
    eid,a,b,bid=setup_pair(alice,bob)
    assert approve(alice,eid).status_code==409
    r=contribute(alice,eid,a)
    assert r.status_code==201,r.text
    assert approve(alice,eid).status_code==409
    assert detail(guest,eid).status_code==404
    assert contribute(bob,eid,a).status_code==404
    assert contribute(alice,eid,b).status_code==404
    assert contribute(bob,eid,b).status_code==201
    first=approve(alice,eid)
    assert first.status_code==200
    state=first.json()["exhibition"]
    assert state["state"]=="draft"
    assert state["approved"]=={"a":True,"b":False}
    assert detail(guest,eid).status_code==404
    second=approve(bob,eid)
    assert second.status_code==200,second.text
    state=second.json()["exhibition"]
    assert state["state"]=="public"
    assert state["approved"]=={"a":True,"b":True}
    public=detail(guest,eid)
    assert public.status_code==200
    assert public.json()["title"]=="两个世界的联合展览"
    assert [x["exhibit"]["id"] for x in public.json()["items"]]==[a,b]
    assert [x["curator"] for x in public.json()["items"]]==["Alice","Bob"]
    assert "平台" not in str(public.json()["items"])  # Only curator commentary, no forged ratings
    assert guest.get("/api/coexhibitions/public").json()["items"][0]["count"]==2


def test_edit_retracts_both_approvals_hides_public_until_reapproved(env):
    alice,bob,guest=env
    eid,a,b,_=setup_pair(alice,bob)
    contribute(alice,eid,a);contribute(bob,eid,b);approve(alice,eid);approve(bob,eid)
    r=alice.put(f"/api/coexhibitions/{eid}",json={
        "title":"文明的交流与变迁","introduction":"公开前要让双方重新审核内容。"})
    assert r.status_code==200,r.text
    state=r.json()["exhibition"]
    assert state["state"]=="draft"
    assert state["approved"]=={"a":False,"b":False}
    assert state["revision"]>3
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/coexhibitions/public").json()["items"]==[]
    assert approve(alice,eid).status_code==200
    assert detail(guest,eid).status_code==404
    assert approve(bob,eid).status_code==200
    assert detail(guest,eid).json()["title"]=="文明的交流与变迁"
    retracted=bob.post(f"/api/coexhibitions/{eid}/retract")
    assert retracted.status_code==200
    assert retracted.json()["exhibition"]["state"]=="draft"
    assert detail(guest,eid).status_code==404


def test_owner_only_removal_and_any_revision_change_resets_all_stamps(env):
    alice,bob,guest=env
    eid,a,b,_=setup_pair(alice,bob)
    x=contribute(alice,eid,a).json()["id"]
    y=contribute(bob,eid,b).json()["id"]
    approve(alice,eid);approve(bob,eid)
    assert alice.post(f"/api/coexhibitions/{eid}/stamp").status_code==200
    assert detail(alice,eid).json()["stamps"]==1
    assert alice.delete(f"/api/coexhibitions/{eid}/items/{y}").status_code==403
    assert bob.delete(f"/api/coexhibitions/{eid}/items/{x}").status_code==403
    assert guest.delete(f"/api/coexhibitions/{eid}/items/{x}").status_code==401
    assert alice.delete(f"/api/coexhibitions/{eid}/items/{x}").status_code==200
    assert detail(guest,eid).status_code==404
    assert detail(alice,eid).json()["stamps"]==0
    assert approve(bob,eid).status_code==409
    new_a=exhibit(alice,"再次贡献的汉代道路",tags="历史,道路")
    assert contribute(alice,eid,new_a).status_code==201
    approve(alice,eid);approve(bob,eid)
    assert detail(alice,eid).json()["stamps"]==0
    assert detail(alice,eid).json()["stamped"] is False


def test_stamps_are_login_only_idempotent_and_not_verified_visits(env):
    alice,bob,guest=env
    eid,a,b,_=setup_pair(alice,bob)
    contribute(alice,eid,a);contribute(bob,eid,b)
    assert guest.post(f"/api/coexhibitions/{eid}/stamp").status_code==401
    assert alice.post(f"/api/coexhibitions/{eid}/stamp").status_code==404
    approve(alice,eid);approve(bob,eid)
    x=alice.post(f"/api/coexhibitions/{eid}/stamp")
    assert x.status_code==200
    assert "自行" in x.json()["notice"]
    assert alice.post(f"/api/coexhibitions/{eid}/stamp").status_code==200
    assert detail(guest,eid).json()["stamps"]==1
    assert detail(alice,eid).json()["stamped"] is True
    assert detail(bob,eid).json()["stamped"] is False
    assert bob.post(f"/api/coexhibitions/{eid}/stamp").status_code==200
    assert detail(guest,eid).json()["stamps"]==2
    assert bob.delete(f"/api/coexhibitions/{eid}/stamp").status_code==200
    assert detail(guest,eid).json()["stamps"]==1


def test_revocation_redacts_both_original_titles_and_all_published_cards(env):
    alice,bob,guest=env
    eid,a,b,_=setup_pair(alice,bob)
    contribute(alice,eid,a,commentary="古代交通如何影响云南文化，是我的研究兴趣。")
    contribute(bob,eid,b,commentary="我希望游客看到茶马古道的不同角度。")
    approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    out=bob.patch(f"/api/exhibits/{b}",json=item(title="乙的茶马古道",tags="云南,历史",visibility="private"))
    assert out.status_code==200
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/coexhibitions/public").json()["items"]==[]
    for client in (alice,bob):
        d=detail(client,eid).json()
        assert d["available"] is False
        assert d["title"]=="原始展品已不可用"
        assert d["introduction"]==""
        assert all(x["exhibit"] is None and x["commentary"] is None for x in d["items"])
        assert "茶马古道" not in str(d)
    assert alice.post(f"/api/coexhibitions/{eid}/stamp").status_code==404
    restored=bob.patch(f"/api/exhibits/{b}",json=item(
        title="乙的茶马古道",tags="云南,历史",visibility="public"))
    assert restored.status_code==200
    assert detail(guest,eid).status_code==200


def test_bridge_close_hides_published_joint_show_without_leaks(env):
    alice,bob,guest=env
    eid,a,b,bridge=setup_pair(alice,bob)
    contribute(alice,eid,a);contribute(bob,eid,b);approve(alice,eid);approve(bob,eid)
    assert detail(guest,eid).status_code==200
    assert bob.delete(f"/api/parallel/bridges/{bridge}").status_code==200
    assert detail(guest,eid).status_code==404
    assert guest.get("/api/coexhibitions/public").json()["items"]==[]
    assert approve(alice,eid).status_code==409
    assert detail(alice,eid).json()["available"] is False


def test_close_by_either_creator_removes_show_and_originals_survive(env):
    alice,bob,guest=env
    eid,a,b,bridge=setup_pair(alice,bob)
    contribute(alice,eid,a);contribute(bob,eid,b);approve(alice,eid);approve(bob,eid)
    assert bob.delete(f"/api/coexhibitions/{eid}").status_code==200
    assert detail(guest,eid).status_code==404
    assert approve(alice,eid).status_code==409
    assert alice.delete(f"/api/coexhibitions/{eid}").status_code==409
    assert alice.get(f"/api/exhibits/{a}").status_code==200
    assert bob.get(f"/api/exhibits/{b}").status_code==200
    assert alice.get("/api/coexhibitions/mine").json()["items"]==[]
    assert joint(alice,bridge).status_code==409


def test_invalid_inputs_limits_and_no_forged_foreign_exhibits(env):
    alice,bob,guest=env
    eid,a,b,_=setup_pair(alice,bob)
    private=exhibit(alice,"不公开的私密作品",visibility="private")
    assert contribute(alice,eid,private).status_code==404
    assert contribute(alice,eid,a,commentary="短").status_code==422
    assert alice.put(f"/api/coexhibitions/{eid}",json={"title":" ","introduction":"内容"}).status_code==422
    first=contribute(alice,eid,a)
    assert first.status_code==201
    assert contribute(alice,eid,a).status_code==409
    assert detail(guest,eid).status_code==404


def test_assets_nav_and_version(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="32.0"
    html=guest.get("/").text
    assert "万物联合展厅" in html
    assert "WONDER ATLAS · WORLD " in html
    for f in ("coexhibitions.js","coexhibitions.css"):
        assert f"/static/{f}" in html
        assert guest.get(f"/static/{f}").status_code==200
    assert "WonderCoExhibitions.render" in guest.get("/static/app.js").text
