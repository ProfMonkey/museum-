"""V33 integration tests for original two-item speculation (local only; never Actions)."""
from test_multiuser import env, item
import sys


def exhibit(client, name, visibility="public", **kwargs):
    r=client.post("/api/exhibits",json=item(title=name,visibility=visibility,**kwargs))
    assert r.status_code==201,r.text
    return r.json()["id"]


def idea(left,right,**changes):
    base=dict(left_id=left,right_id=right,law="memory_trade",
              title="当一只钟表失去时间记忆",
              premise="如果一只钟表突然与云南米线交换记忆，哪个世界能保留下原本的历史？",
              choice_a="保留钟表记忆",
              ending_a="文明失去了所有传统食谱，却发现了隐藏在每一个小时里的新地图。",
              choice_b="保留米线记忆",
              ending_b="时间变成一根可以吃掉的面条，历史从此沿着锅中的旋涡旋转。")
    base.update(changes)
    return base


def create(client,left,right,**changes):
    return client.post("/api/collisions",json=idea(left,right,**changes))


def detail(client,wid):
    return client.get(f"/api/collisions/{wid}")


def publish(client,wid):
    return client.post(f"/api/collisions/{wid}/publish")


def test_empty_gallery_laws_and_guest_preview_no_fake_worlds(env):
    alice,bob,guest=env
    assert guest.get("/api/collisions").json()["items"]==[]
    laws=guest.get("/api/collisions/laws").json()["items"]
    assert len(laws)==6
    assert all("prompt" in row for row in laws)
    a=exhibit(alice,"钟表馆藏")
    b=exhibit(bob,"云南米线")
    params=f"/api/collisions/preview?left_id={a}&right_id={b}&law=memory_trade"
    p=guest.get(params)
    assert p.status_code==200,p.text
    body=p.json()
    assert body["left"]["title"]=="钟表馆藏"
    assert body["right"]["title"]=="云南米线"
    assert "假设" in body["prompt"]
    assert "模板" in body["notice"]
    assert guest.get(params).json()["seed"]==body["seed"]
    assert guest.get(f"/api/collisions/preview?left_id={a}&right_id={a}").status_code==400
    assert guest.get(f"/api/collisions/preview?left_id={a}&right_id={b}&law=no_such_law").status_code==422
    assert guest.get("/api/collisions/sources?q=云南").json()["items"][0]["id"]==b
    assert guest.get("/api/collisions/mine").status_code==401


def test_real_source_validation_rejects_private_fake_self_and_future_bad_payload(env):
    alice,bob,guest=env
    a=exhibit(alice,"会讲故事的钟表")
    b=exhibit(bob,"记录神话的米线")
    secret=exhibit(bob,"不能被引用的私人日记",visibility="private")
    assert create(alice,a,secret).status_code==404
    assert create(alice,secret,b).status_code==404
    assert create(alice,a,a).status_code==422
    assert create(alice,a,999999).status_code==404
    assert create(guest,a,b).status_code==401
    assert create(alice,a,b,choice_a="保持",choice_b="保持").status_code==422
    assert create(alice,a,b,premise="不足字数").status_code==422
    assert create(alice,a,b,ending_a="失败").status_code==422


def test_private_draft_does_not_leak_and_owner_can_publish(env):
    alice,bob,guest=env
    a=exhibit(alice,"云南地图")
    b=exhibit(bob,"机械齿轮")
    created=create(alice,a,b)
    assert created.status_code==201,created.text
    wid=created.json()["id"]
    assert created.json()["status"]=="draft"
    assert detail(bob,wid).status_code==404
    assert detail(guest,wid).status_code==404
    assert detail(alice,wid).json()["title"]=="当一只钟表失去时间记忆"
    assert bob.get("/api/collisions/mine").json()["items"]==[]
    assert len(alice.get("/api/collisions/mine").json()["items"])==1
    assert guest.get("/api/collisions").json()["items"]==[]
    assert publish(bob,wid).status_code==404
    yes=publish(alice,wid)
    assert yes.status_code==200,yes.text
    assert yes.json()["world"]["status"]=="public"
    assert detail(guest,wid).status_code==200
    assert guest.get("/api/collisions").json()["items"][0]["id"]==wid
    assert guest.get("/api/collisions").json()["items"][0]["left"]["id"]==a


def test_two_branch_choice_one_vote_per_user_switching_and_guest(env):
    alice,bob,guest=env
    a=exhibit(alice,"现实时钟")
    b=exhibit(bob,"故事米线")
    wid=create(alice,a,b).json()["id"]
    assert bob.post(f"/api/collisions/{wid}/choose/a").status_code==404
    publish(alice,wid)
    assert guest.post(f"/api/collisions/{wid}/choose/a").status_code==401
    assert bob.post(f"/api/collisions/{wid}/choose/z").status_code==422
    first=bob.post(f"/api/collisions/{wid}/choose/a")
    assert first.status_code==200
    assert first.json()["votes"]=={"a":1,"b":0}
    assert bob.post(f"/api/collisions/{wid}/choose/a").json()["votes"]=={"a":1,"b":0}
    switched=bob.post(f"/api/collisions/{wid}/choose/b")
    assert switched.status_code==200
    assert switched.json()["votes"]=={"a":0,"b":1}
    assert detail(bob,wid).json()["my_choice"]=="b"
    assert detail(alice,wid).json()["my_choice"] is None
    assert detail(guest,wid).json()["my_choice"] is None
    assert alice.post(f"/api/collisions/{wid}/choose/a").json()["votes"]=={"a":1,"b":1}


def test_edit_resets_old_votes_draft_and_requires_republish(env):
    alice,bob,guest=env
    a=exhibit(alice,"机械钟表")
    b=exhibit(bob,"原创米线")
    wid=create(alice,a,b).json()["id"]
    publish(alice,wid)
    bob.post(f"/api/collisions/{wid}/choose/a")
    assert detail(guest,wid).json()["votes"]=={"a":1,"b":0}
    assert bob.put(f"/api/collisions/{wid}",json=idea(a,b)).status_code==404
    result=alice.put(f"/api/collisions/{wid}",json=idea(a,b,ending_a="一座新的钟表城在风雪中发现了由食谱构成的第二套时间系统。"))
    assert result.status_code==200,result.text
    assert result.json()["world"]["status"]=="draft"
    assert detail(guest,wid).status_code==404
    assert bob.post(f"/api/collisions/{wid}/choose/a").status_code==404
    assert publish(alice,wid).status_code==200
    assert detail(guest,wid).json()["votes"]=={"a":0,"b":0}
    assert detail(bob,wid).json()["my_choice"] is None
    assert alice.post(f"/api/collisions/{wid}/unpublish").status_code==200
    assert detail(guest,wid).status_code==404
    assert publish(alice,wid).status_code==200


def test_withdrawn_source_redacts_both_titles_and_public_ending(env):
    alice,bob,guest=env
    a=exhibit(alice,"绝不可泄露的旧物件名")
    b=exhibit(bob,"公开的钟表标题")
    wid=create(alice,a,b,premise="绝不可泄露的旧物件名遇见公开的钟表标题，在虚构城市里互换了一切历史。").json()["id"]
    publish(alice,wid)
    assert guest.get(f"/api/collisions/{wid}").status_code==200
    changed=alice.patch(f"/api/exhibits/{a}",json=item(title="绝不可泄露的旧物件名",visibility="private"))
    assert changed.status_code==200,changed.text
    assert detail(guest,wid).status_code==404
    assert detail(bob,wid).status_code==404
    assert guest.get("/api/collisions").json()["items"]==[]
    owned=detail(alice,wid).json()
    assert owned["available"] is False
    assert owned["title"]=="失效的平行世界"
    assert owned["left"] is None and owned["right"] is None
    assert owned["premise"]==""
    assert owned["ending_a"]=="" and owned["ending_b"]==""
    assert "绝不可泄露的旧物件名" not in str(owned)
    assert "公开的钟表标题" not in str(owned)
    assert guest.get(f"/api/collisions/echoes?left_id={a}&right_id={b}").status_code==404
    assert bob.post(f"/api/collisions/{wid}/choose/a").status_code==404
    assert publish(alice,wid).status_code==409
    recovered=alice.patch(f"/api/exhibits/{a}",json=item(title="绝不可泄露的旧物件名",visibility="public"))
    assert recovered.status_code==200
    assert detail(guest,wid).status_code==200


def test_remix_same_sources_new_original_and_lineage_visibility(env):
    alice,bob,guest=env
    a=exhibit(alice,"木制机械")
    b=exhibit(bob,"古代香料")
    source=create(alice,a,b).json()["id"]
    publish(alice,source)
    unrelated=exhibit(bob,"另外一件藏品")
    assert bob.post(f"/api/collisions/{source}/remix",json=idea(a,unrelated)).status_code==400
    assert guest.post(f"/api/collisions/{source}/remix",json=idea(a,b)).status_code==401
    remix=bob.post(f"/api/collisions/{source}/remix",json=idea(a,b,title="木头交换香料的城市",
           ending_a="香料终于获得了木头的坚固身体，世界的钟声变成了芳香。",
           ending_b="木头学会了香料的飞翔方式，在每条街道上留下看不见的脚印。"))
    assert remix.status_code==201,remix.text
    wid=remix.json()["id"]
    assert detail(guest,wid).status_code==404
    assert publish(bob,wid).status_code==200
    shown=detail(guest,wid).json()
    assert shown["parent_id"]==source
    assert shown["author"]=="Bob"
    echoes=guest.get(f"/api/collisions/echoes?left_id={a}&right_id={b}").json()["items"]
    assert {x["id"] for x in echoes}=={source,wid}
    assert alice.post(f"/api/collisions/{source}/unpublish").status_code==200
    assert detail(guest,wid).json()["parent_id"] is None
    assert {x["id"] for x in guest.get(f"/api/collisions/echoes?left_id={a}&right_id={b}").json()["items"]}=={wid}
    assert bob.delete(f"/api/collisions/{wid}").status_code==200
    assert detail(guest,wid).status_code==404
    assert detail(alice,source).status_code==200


def test_studio_parent_private_hides_collision_and_candidates(env):
    alice,bob,guest=env
    a=exhibit(alice,"共享的真实原展品")
    b=exhibit(bob,"另一个真实源")
    wid=create(alice,a,b).json()["id"]
    publish(alice,wid)
    module=sys.modules["wa_test_server"]
    with module.db() as c:
        c.execute("""INSERT INTO creator_studio_projects
            (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (1,a,"暂不公开的工作室作品","quiz","private","{}",module.now(),module.now()))
    assert detail(guest,wid).status_code==404
    assert guest.get("/api/collisions").json()["items"]==[]
    assert a not in [x["id"] for x in guest.get("/api/collisions/sources").json()["items"]]
    assert detail(alice,wid).json()["available"] is False


def test_v33_assets_navigation_version_and_manual_only_actions(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="34.0"
    html=guest.get("/").text
    assert "万物碰撞机" in html
    assert "WONDER ATLAS · WORLD " in html
    for filename in ("collision.js","collision.css"):
        assert f"/static/{filename}" in html
        assert guest.get(f"/static/{filename}").status_code==200
    assert "WonderCollision.render" in guest.get("/static/app.js").text
