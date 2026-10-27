"""V34 civilization engine integration: bounded deterministic fictional history.

Locally runnable without GitHub Actions:
  python -m pytest -q tests/test_civilizations_v34.py
"""
import sys
from test_multiuser import env, item
from test_collision_v33 import exhibit, idea, create as collision, publish as publish_collision
from civilization_engine import INITIAL, POLICIES, apply_turn


def origin(alice, bob, law="memory_trade"):
    x=exhibit(alice,"古老钟楼")
    y=exhibit(bob,"云南米线")
    world=collision(alice,x,y,law=law)
    assert world.status_code==201, world.text
    wid=world.json()["id"]
    pub=publish_collision(alice,wid)
    assert pub.status_code==200,pub.text
    return wid,x,y


def civ(client,world,seed,name="记忆时代文明"):
    return client.post("/api/civilizations",json={
        "world_id":world,"seed_exhibit_id":seed,"name":name,
        "charter":"我们来自一个完全虚构的宇宙，所有重大变化都由自己写下的故事决定。"})


def turn(client,cid,policy="research",chapter="第一轮历史的起源"):
    return client.post(f"/api/civilizations/{cid}/turns",json={
        "policy":policy,"chapter":chapter,
        "narrative":"虚构世界的人们以新的方式理解原始物件，开始书写属于自己的文明历史。" })


def publish(client,cid):
    return client.post(f"/api/civilizations/{cid}/publish")


def detail(client,cid):
    return client.get(f"/api/civilizations/{cid}")


def make_published(alice,bob):
    wid,a,b=origin(alice,bob)
    r=civ(alice,wid,a)
    assert r.status_code==201,r.text
    cid=r.json()["id"]
    assert turn(alice,cid,"research").status_code==201
    assert turn(alice,cid,"harvest","第二轮重大文明抉择").status_code==201
    assert publish(alice,cid).status_code==200
    return cid,wid,a,b


def test_rule_engine_clamping_and_replay_without_randomness():
    first=apply_turn(INITIAL,"research","memory_trade")
    assert first==apply_turn(INITIAL,"research","memory_trade")
    assert first["after"]=={"knowledge":63,"supplies":44,"ecology":46,"cohesion":46,"culture":51}
    assert first["delta"]["cohesion"]==-4
    assert first["modifier"]=={"stat":"cohesion","adjustment":-3,
           "reason":"所选虚构世界法则的显式游戏规则加成"}
    assert first["model_version"]==1
    frozen={k:100 for k in INITIAL}
    cap=apply_turn(frozen,"harvest","world_merge")
    assert cap["after"]["supplies"]==100
    assert cap["delta"]["supplies"]==0
    assert set(POLICIES)=={"research","harvest","diplomacy","restore","arts","fortify"}


def test_empty_gallery_and_policy_descriptions_are_transparent(env):
    alice,bob,guest=env
    public=guest.get("/api/civilizations")
    assert public.status_code==200
    assert public.json()["items"]==[]
    assert "真实作者" in public.json()["notice"]
    policy=guest.get("/api/civilizations/policies")
    assert policy.status_code==200
    assert len(policy.json()["policies"])==6
    assert policy.json()["model_version"]==1
    assert policy.json()["limits"]["per_world"]==6
    assert policy.json()["limits"]["max_turns"]==8
    assert guest.get("/api/civilizations/mine").status_code==401
    assert guest.get("/api/civilizations/worlds").status_code==401


def test_only_own_live_v33_world_and_own_pair_seed(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    out=exhibit(alice,"另一个不在碰撞世界中的公开展品")
    assert civ(guest,wid,a).status_code==401
    assert civ(bob,wid,b).status_code==404
    assert civ(alice,wid,out).status_code==422
    assert civ(alice,999999,a).status_code==404
    created=civ(alice,wid,b)
    assert created.status_code==201,created.text
    cid=created.json()["id"]
    assert created.json()["status"]=="draft"
    assert detail(bob,cid).status_code==404
    assert detail(guest,cid).status_code==404
    assert detail(alice,cid).json()["seed"]["id"]==b
    worldlist=alice.get("/api/civilizations/worlds").json()["items"]
    assert worldlist[0]["remaining"]==5
    assert bob.get("/api/civilizations/worlds").json()["items"]==[]


def test_six_per_world_limit_and_source_author_not_silently_approved(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    for i in range(6):
        result=civ(alice,wid,a,name=f"文明第{i+1}纪")
        assert result.status_code==201,result.text
    assert civ(alice,wid,a,name="第七文明").status_code==409
    assert alice.get("/api/civilizations/worlds").json()["items"][0]["remaining"]==0
    assert guest.get("/api/civilizations").json()["items"]==[]


def test_publish_needs_two_real_author_chapters_and_private_during_new_turn(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    cid=civ(alice,wid,a).json()["id"]
    assert publish(alice,cid).status_code==409
    assert turn(bob,cid).status_code==404
    assert turn(guest,cid).status_code==401
    one=turn(alice,cid,"research")
    assert one.status_code==201,one.text
    assert one.json()["outcome"]["policy_label"]=="研究未知"
    assert publish(alice,cid).status_code==409
    assert turn(alice,cid,"wrong_policy").status_code==422
    assert turn(alice,cid,"harvest","产能与环境的冲突").status_code==201
    assert publish(bob,cid).status_code==404
    assert publish(alice,cid).status_code==200
    assert detail(guest,cid).status_code==200
    assert detail(guest,cid).json()["turns"][0]["narrative"].startswith("虚构世界")
    assert guest.get("/api/civilizations").json()["items"][0]["turn_count"]==2
    assert turn(alice,cid,"diplomacy","与邻国的第一次贸易").status_code==201
    assert detail(guest,cid).status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    assert publish(alice,cid).status_code==200
    assert len(detail(guest,cid).json()["turns"])==3


def test_counterfactual_exact_replay_and_no_write_to_original_history(env):
    alice,bob,guest=env
    cid,wid,a,b=make_published(alice,bob)
    baseline=detail(guest,cid).json()
    before=baseline["turns"]
    assert len(before)==2
    same=guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=research")
    assert same.status_code==200,same.text
    assert set(same.json()["difference"].values())=={0}
    replacement=guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=restore")
    assert replacement.status_code==200,replacement.text
    new=replacement.json()
    first=apply_turn(INITIAL,"restore","memory_trade")
    second=apply_turn(first["after"],"harvest","memory_trade")
    assert new["alternative_final"]==second["after"]
    assert new["actual_final"]==baseline["final"]
    assert new["difference"]=={k:second["after"][k]-baseline["final"][k] for k in INITIAL}
    assert len(new["alternative_history"])==2
    assert new["alternative_history"][0]["policy"]=="restore"
    assert new["alternative_history"][1]["policy"]=="harvest"
    assert "不写入数据库" in new["notice"]
    assert detail(guest,cid).json()["turns"]==before
    assert guest.get(f"/api/civilizations/{cid}/counterfactual?turn=3&policy=arts").status_code==422
    assert guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=fake").status_code==422


def test_delete_turn_and_explicit_unpublish_respects_owner(env):
    alice,bob,guest=env
    cid,wid,a,b=make_published(alice,bob)
    assert bob.delete(f"/api/civilizations/{cid}/turns/latest").status_code==404
    assert alice.delete(f"/api/civilizations/{cid}/turns/latest").status_code==200
    assert detail(guest,cid).status_code==404
    d=detail(alice,cid).json()
    assert d["status"]=="draft"
    assert len(d["turns"])==1
    assert publish(alice,cid).status_code==409
    assert alice.post(f"/api/civilizations/{cid}/unpublish").status_code==200
    assert bob.delete(f"/api/civilizations/{cid}").status_code==404
    assert alice.delete(f"/api/civilizations/{cid}").status_code==200
    assert alice.get("/api/civilizations/mine").json()["items"]==[]
    assert alice.get(f"/api/collisions/{wid}").status_code==200



def test_author_may_revise_charter_but_every_public_change_requires_approval(env):
    alice,bob,guest=env
    cid,wid,a,b=make_published(alice,bob)
    payload={"name":"新的金色文明","charter":"在作者修改历史宣言后，全体游客都必须在再次发布以后才能查看新内容。"}
    assert bob.put(f"/api/civilizations/{cid}",json=payload).status_code==404
    assert guest.put(f"/api/civilizations/{cid}",json=payload).status_code==401
    bad=alice.put(f"/api/civilizations/{cid}",json={"name":" ","charter":"不足字数"})
    assert bad.status_code==422
    edited=alice.put(f"/api/civilizations/{cid}",json=payload)
    assert edited.status_code==200,edited.text
    assert edited.json()["status"]=="draft"
    assert detail(guest,cid).status_code==404
    assert detail(alice,cid).json()["name"]=="新的金色文明"
    assert publish(alice,cid).status_code==200
    assert detail(guest,cid).json()["name"]=="新的金色文明"


def test_max_eight_turns_is_finite_and_comparable(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    cid=civ(alice,wid,a).json()["id"]
    choices=list(POLICIES)
    for i in range(8):
        assert turn(alice,cid,choices[i%len(choices)],f"文明历史第{i+1}次抉择").status_code==201
    assert turn(alice,cid).status_code==409
    assert publish(alice,cid).status_code==200
    d=detail(guest,cid).json()
    assert len(d["turns"])==8
    assert all(0<=v<=100 for v in d["final"].values())
    whatif=guest.get(f"/api/civilizations/{cid}/counterfactual?turn=4&policy=arts")
    assert whatif.status_code==200
    assert len(whatif.json()["alternative_history"])==5


def test_v33_unpublish_world_revision_and_source_revocation_blocks_leaks(env):
    alice,bob,guest=env
    cid,wid,a,b=make_published(alice,bob)
    assert bob.get(f"/api/civilizations/{cid}").status_code==200
    # V33 parent world becomes private: the child civilization also disappears.
    assert alice.post(f"/api/collisions/{wid}/unpublish").status_code==200
    assert detail(guest,cid).status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    mine=alice.get("/api/civilizations/mine").json()["items"][0]
    assert mine["available"] is False and mine["seed"] is None
    assert mine["name"]=="原始来源已不可用"
    assert turn(alice,cid).status_code==409
    assert publish_collision(alice,wid).status_code==200
    # V33 revision changed, old civilization cannot silently republish.
    assert detail(guest,cid).status_code==404
    assert alice.delete(f"/api/civilizations/{cid}").status_code==200
    cid2=civ(alice,wid,a).json()["id"]
    assert turn(alice,cid2).status_code==201
    assert turn(alice,cid2,"arts","第二时代的文化繁荣").status_code==201
    assert publish(alice,cid2).status_code==200
    assert bob.patch(f"/api/exhibits/{b}",json=item(title="云南米线",visibility="private")).status_code==200
    assert detail(guest,cid2).status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    mine=alice.get("/api/civilizations/mine").json()["items"][0]
    assert "米线" not in str(mine)
    assert mine["name"]=="原始来源已不可用"
    assert bob.get(f"/api/civilizations/{cid2}/counterfactual?turn=1&policy=harvest").status_code==404
    assert alice.delete(f"/api/civilizations/{cid2}").status_code==200


def test_private_studio_parent_prevents_seed_and_show(env):
    alice,bob,guest=env
    cid,wid,a,b=make_published(alice,bob)
    module=sys.modules["wa_test_server"]
    with module.db() as conn:
        conn.execute("""INSERT INTO creator_studio_projects
            (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (1,a,"私有衍生作品","quiz","private","{}",module.now(),module.now()))
    assert detail(guest,cid).status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    assert alice.get("/api/civilizations/worlds").json()["items"]==[]
    assert "古老钟楼" not in str(alice.get("/api/civilizations/mine").json())
    assert publish(alice,cid).status_code==409



def test_foreign_artifact_shock_is_real_opt_in_and_replay_preserves_it(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    incoming=exhibit(bob,"来自外部的神秘计算机",tags="计算机,未来")
    private=exhibit(alice,"绝不公开的禁忌仪器",visibility="private")
    cid=civ(alice,wid,a).json()["id"]
    query=guest.get("/api/civilizations/relics?q=计算机")
    assert query.status_code==200,query.text
    assert query.json()["items"][0]["id"]==incoming
    assert private not in [x["id"] for x in guest.get("/api/civilizations/relics").json()["items"]]
    payload={
        "policy":"research","chapter":"神秘机器坠落在古代王国",
        "narrative":"文明获得了完全不理解的神秘机器；这只是作者自创的虚构冲击事件。",
        "anomaly_exhibit_id":incoming}
    assert alice.post(f"/api/civilizations/{cid}/turns",json={
        **payload,"anomaly_exhibit_id":a}).status_code==422
    assert alice.post(f"/api/civilizations/{cid}/turns",json={
        **payload,"anomaly_exhibit_id":private}).status_code==404
    first=alice.post(f"/api/civilizations/{cid}/turns",json=payload)
    assert first.status_code==201,first.text
    expected=apply_turn(INITIAL,"research","memory_trade",True)
    assert first.json()["outcome"]["after"]==expected["after"]
    assert expected["after"]=={
        "knowledge":68,"supplies":44,"ecology":46,"cohesion":43,"culture":55}
    assert first.json()["outcome"]["anomaly"] is True
    assert turn(alice,cid,"restore","第二时代的资源修复").status_code==201
    assert publish(alice,cid).status_code==200
    d=detail(guest,cid).json()
    assert d["turns"][0]["anomaly"]["title"]=="来自外部的神秘计算机"
    assert d["turns"][0]["anomaly_effect"]=={"knowledge":5,"culture":4,"cohesion":-3}
    assert d["turns"][1]["anomaly"] is None
    alt=guest.get(f"/api/civilizations/{cid}/counterfactual?turn=1&policy=arts")
    assert alt.status_code==200,alt.text
    a1=apply_turn(INITIAL,"arts","memory_trade",True)
    a2=apply_turn(a1["after"],"restore","memory_trade")
    assert alt.json()["alternative_final"]==a2["after"]
    assert alt.json()["alternative_history"][0]["anomaly"]["id"]==incoming
    assert detail(guest,cid).json()["final"]==d["final"]
    assert guest.get("/api/civilizations/policies").json()["anomaly_effect"]=={
        "knowledge":5,"culture":4,"cohesion":-3}


def test_withdrawn_or_deleted_foreign_artifact_invalidates_public_civilization(env):
    alice,bob,guest=env
    wid,a,b=origin(alice,bob)
    outsider=exhibit(bob,"不能曝光的外来机械",tags="机械,外星")
    cid=civ(alice,wid,a).json()["id"]
    payload={
        "policy":"diplomacy","chapter":"陌生世界向此国开放",
        "narrative":"一件来自外界的机械突然降临，我们决定让它改变文化结构。",
        "anomaly_exhibit_id":outsider}
    assert alice.post(f"/api/civilizations/{cid}/turns",json=payload).status_code==201
    assert turn(alice,cid,"arts","第二次文化变迁").status_code==201
    assert publish(alice,cid).status_code==200
    assert detail(guest,cid).status_code==200
    assert bob.patch(f"/api/exhibits/{outsider}",json=item(
        title="不能曝光的外来机械",visibility="private")).status_code==200
    assert detail(guest,cid).status_code==404
    assert guest.get("/api/civilizations").json()["items"]==[]
    safe=alice.get("/api/civilizations/mine").json()
    assert "不能曝光的外来机械" not in str(safe)
    assert "陌生世界向此国开放" not in str(safe)
    assert publish(alice,cid).status_code==409
    assert bob.patch(f"/api/exhibits/{outsider}",json=item(
        title="不能曝光的外来机械",visibility="public")).status_code==200
    assert detail(guest,cid).status_code==200
    assert bob.delete(f"/api/exhibits/{outsider}").status_code==200
    assert detail(guest,cid).status_code==404
    assert alice.delete(f"/api/civilizations/{cid}").status_code==200


def test_v34_frontend_assets_and_version(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="35.0"
    html=guest.get("/").text
    assert "WONDER ATLAS · WORLD " in html
    assert "万物文明演化实验室" in html
    for name in ("civilizations.js","civilizations.css"):
        assert f"/static/{name}" in html
        assert guest.get(f"/static/{name}").status_code==200
    assert "WonderCivilizations.render" in guest.get("/static/app.js").text
