"""V34: deterministic toy civilization histories, strictly sourced and private.

These tests are for LOCAL execution; they never run GitHub Actions.
"""
import sys
from test_multiuser import env, item


def exhibit(client, title, visibility="public"):
    r=client.post("/api/exhibits",json=item(title=title,visibility=visibility))
    assert r.status_code==201,r.text
    return r.json()["id"]


def create_world(alice,bob):
    a=exhibit(alice,"古代青铜鼓")
    b=exhibit(bob,"未来芯片")
    exotic=exhibit(bob,"宇宙望远镜")
    request={
       "left_id":a,"right_id":b,"law":"world_merge",
       "title":"青铜文明与电子信仰的碰撞",
       "premise":"在一个纯粹虚构的世界里，两件跨越万年的物品互相改变了文明的全部规则。",
       "choice_a":"研究陌生技术",
       "ending_a":"工匠从古老的文字里发现电子科技的秘密，城邦迎来新的发展。",
       "choice_b":"建立古老神殿",
       "ending_b":"人们将微芯片供奉在青铜神殿里，用祭司仪式解释它的用途。"
    }
    r=alice.post("/api/collisions",json=request)
    assert r.status_code==201,r.text
    wid=r.json()["id"]
    r=alice.post(f"/api/collisions/{wid}/publish")
    assert r.status_code==200,r.text
    return wid,a,b,exotic


def civ(alice,wid,seed,name="星辰与青铜的文明"):
    return alice.post("/api/civilizations",json={
        "world_id":wid,"seed_exhibit_id":seed,"name":name,
        "charter":"这个虚构文明因古代物件与现代科学的相遇而诞生，所有历史都由馆长亲自编写。"
    })


def turn(client,cid,policy="research",anomaly=None,chapter="初识天地的时代",narrative="文明第一次面对陌生世界，馆长记录了由这条决策导致的游戏故事。"):
    return client.post(f"/api/civilizations/{cid}/turns",json={
        "policy":policy,"anomaly_exhibit_id":anomaly,
        "chapter":chapter,"narrative":narrative
    })


def published_civ(alice,bob):
    wid,a,b,exotic=create_world(alice,bob)
    r=civ(alice,wid,a)
    assert r.status_code==201,r.text
    cid=r.json()["id"]
    r1=turn(alice,cid,"research")
    r2=turn(alice,cid,"diplomacy")
    assert r1.status_code==201,r1.text
    assert r2.status_code==201,r2.text
    publish=alice.post(f"/api/civilizations/{cid}/publish")
    assert publish.status_code==200,publish.text
    return cid,wid,a,b,exotic


def test_empty_real_public_gallery_and_explicit_model_contract(env):
    alice,bob,guest=env
    assert guest.get("/api/civilizations").json()["items"]==[]
    contract=guest.get("/api/civilizations/policies")
    assert contract.status_code==200
    info=contract.json()
    assert info["model_version"]==1
    assert info["initial"]=={k:50 for k in ("knowledge","supplies","ecology","cohesion","culture")}
    assert len(info["policies"])==6
    assert info["limits"]["per_world"]==6
    assert info["limits"]["max_turns"]==8
    assert guest.get("/api/civilizations/mine").status_code==401
    assert guest.get("/api/civilizations/worlds").status_code==401
    assert "游戏" in info["notice"]


def test_only_collision_world_owner_can_build_civilizations_and_only_current_sources(env):
    alice,bob,guest=env
    wid,a,b,exotic=create_world(alice,bob)
    assert bob.post("/api/civilizations",json={
        "world_id":wid,"seed_exhibit_id":a,"name":"不应被建造的文明",
        "charter":"虽然其中有公开的藏品，但是别人的世界并不授权非原作者建造文明。"}).status_code==404
    assert civ(alice,wid,exotic).status_code==422
    assert civ(alice,wid,a).status_code==201
    assert guest.get("/api/civilizations").json()["items"]==[]
    assert guest.get("/api/civilizations/1").status_code==404
    assert bob.get("/api/civilizations/1").status_code==404
    mine=alice.get("/api/civilizations/mine").json()["items"]
    assert mine[0]["name"]=="星辰与青铜的文明"
    available=alice.get("/api/civilizations/worlds").json()["items"]
    assert available[0]["id"]==wid
    assert available[0]["remaining"]==5


def test_six_civilizations_per_world_limit(env):
    alice,bob,guest=env
    wid,a,b,exotic=create_world(alice,bob)
    for i in range(6):
        r=civ(alice,wid,a,name=f"青铜世界第{i+1}文明")
        assert r.status_code==201,r.text
    assert civ(alice,wid,b).status_code==409
    worlds=alice.get("/api/civilizations/worlds").json()["items"]
    assert worlds[0]["remaining"]==0


def test_turns_use_public_deterministic_values_and_privacy(env):
    alice,bob,guest=env
    wid,a,b,exotic=create_world(alice,bob)
    cid=civ(alice,wid,a).json()["id"]
    assert guest.post(f"/api/civilizations/{cid}/turns",json={
        "policy":"research","chapter":"外来初识","narrative":"游客绝不能私自替馆长修改原创历史内容。"}).status_code==401
    assert turn(bob,cid).status_code==404
    assert turn(alice,cid,policy="cheat").status_code==422
    assert turn(alice,cid,anomaly=a).status_code==422
    assert turn(alice,cid,anomaly=999999).status_code==404
    one=turn(alice,cid,"research")
    assert one.status_code==201,one.text
    outcome=one.json()["outcome"]
    # world_merge has no research modifier.
    assert outcome["after"]=={
        "knowledge":63,"supplies":44,"ecology":46,"cohesion":49,"culture":51}
    assert outcome["model_version"]==1
    assert outcome["after"]["knowledge"]-outcome["before"]["knowledge"]==13
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==409
    two=turn(alice,cid,"diplomacy")
    assert two.status_code==201,two.text
    assert two.json()["outcome"]["after"]["cohesion"]==62  # 49 + 10 + 3 world_merge
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==200
    public=guest.get(f"/api/civilizations/{cid}")
    assert public.status_code==200
    timeline=public.json()["turns"]
    assert timeline[0]["after"]==outcome["after"]
    assert timeline[1]["after"]==two.json()["outcome"]["after"]
    assert "科学预测" in public.json()["notice"]


def test_foreign_artifact_changes_numeric_rules_and_revocation_hides_all(env):
    alice,bob,guest=env
    wid,a,b,exotic=create_world(alice,bob)
    cid=civ(alice,wid,a).json()["id"]
    a1=turn(alice,cid,"research",anomaly=exotic)
    assert a1.status_code==201,a1.text
    out=a1.json()["outcome"]
    assert out["after"]["knowledge"]==68
    assert out["after"]["culture"]==55
    assert out["after"]["cohesion"]==46
    assert out["anomaly_effect"]=={"knowledge":5,"culture":4,"cohesion":-3}
    assert turn(alice,cid,"diplomacy").status_code==201
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==200
    assert guest.get(f"/api/civilizations/{cid}").json()["turns"][0]["anomaly"]["id"]==exotic
    old=bob.patch(f"/api/exhibits/{exotic}",json=item(title="宇宙望远镜",visibility="private"))
    assert old.status_code==200,old.text
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    mine=alice.get("/api/civilizations/mine").json()["items"][0]
    assert mine["available"] is False
    assert mine["name"]=="原始来源已不可用"
    assert "宇宙望远镜" not in str(mine)
    assert turn(alice,cid).status_code==409


def test_counterfactual_read_only_replay_does_not_modify_history(env):
    alice,bob,guest=env
    cid,wid,a,b,exotic=published_civ(alice,bob)
    before=guest.get(f"/api/civilizations/{cid}").json()
    q=guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=harvest")
    assert q.status_code==200,q.text
    result=q.json()
    assert result["alternative_policy"]=="harvest"
    assert result["actual_policy"]=="research"
    assert len(result["alternative_history"])==2
    assert result["alternative_history"][1]["policy"]=="diplomacy"
    assert result["alternative_final"]!=result["actual_final"]
    assert any(result["difference"][k] for k in result["difference"])
    assert guest.get(f"/api/civilizations/{cid}").json()==before
    assert guest.get(f"/api/civilizations/{cid}/counterfactual?turn=7&policy=harvest").status_code==422
    assert guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=unknown").status_code==422


def test_later_edit_and_undo_retracts_public_and_requires_republish(env):
    alice,bob,guest=env
    cid,wid,a,b,exotic=published_civ(alice,bob)
    r=alice.put(f"/api/civilizations/{cid}",json={
        "name":"修订后的青铜文明",
        "charter":"馆长已经重新写下了这座虚构文明的世界宣言，因此旧版本需要下架重新批准。"})
    assert r.status_code==200,r.text
    assert r.json()["status"]=="draft"
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==200
    assert guest.get(f"/api/civilizations/{cid}").json()["name"]=="修订后的青铜文明"
    assert turn(alice,cid,"restore").status_code==201
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert alice.delete(f"/api/civilizations/{cid}/turns/latest").status_code==200
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==200
    assert bob.post(f"/api/civilizations/{cid}/unpublish").status_code==404
    assert alice.post(f"/api/civilizations/{cid}/unpublish").status_code==200
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert alice.delete(f"/api/civilizations/{cid}").status_code==200
    assert alice.get("/api/civilizations/mine").json()["items"]==[]


def test_v33_world_revision_revocation_invalidates_all_child_timelines(env):
    alice,bob,guest=env
    cid,wid,a,b,exotic=published_civ(alice,bob)
    assert guest.get(f"/api/civilizations/{cid}").status_code==200
    assert alice.post(f"/api/collisions/{wid}/unpublish").status_code==200
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    assert alice.post(f"/api/collisions/{wid}/publish").status_code==200
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    assert alice.post(f"/api/civilizations/{cid}/publish").status_code==409
    assert bob.get(f"/api/civilizations/{cid}").status_code==404


def test_source_privacy_retraction_hides_private_story_and_deletes_safely(env):
    alice,bob,guest=env
    cid,wid,a,b,exotic=published_civ(alice,bob)
    assert guest.get(f"/api/civilizations/{cid}").status_code==200
    bob.patch(f"/api/exhibits/{b}",json=item(title="未来芯片",visibility="private"))
    assert guest.get(f"/api/civilizations/{cid}").status_code==404
    mine=alice.get("/api/civilizations/mine").json()["items"][0]
    assert mine["available"] is False
    assert mine["seed"] is None
    assert mine["world_id"] is None
    assert "青铜" not in str(mine)
    assert alice.delete(f"/api/civilizations/{cid}").status_code==200
    assert alice.get("/api/civilizations/mine").json()["items"]==[]


def test_public_recent_gallery_only_real_author_and_frontend_assets(env):
    alice,bob,guest=env
    cid,wid,a,b,exotic=published_civ(alice,bob)
    listing=guest.get("/api/civilizations").json()["items"]
    assert len(listing)==1
    assert listing[0]["id"]==cid
    assert listing[0]["turn_count"]==2
    assert listing[0]["world_id"]==wid
    assert guest.get("/api/health").json()["version"]=="34.0"
    html=guest.get("/").text
    assert "WORLD 34" in html
    assert "万物文明演化实验室" in html
    for file in ("civilizations.js","civilizations.css"):
        assert f"/static/{file}" in html
        assert guest.get(f"/static/{file}").status_code==200
    assert "WonderCivilizations.render" in guest.get("/static/app.js").text
