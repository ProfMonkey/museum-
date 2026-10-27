"""V32 museum mystery expeditions: owner-built clue trails, no public source leaks.

Run locally when desired with:
  python -m pytest -q tests/test_mysteries_v32.py
This file is deliberately not executed through GitHub Actions.
"""
import sys
from test_multiuser import env, item


def create_exhibit(client, title, visibility="public", **kwargs):
    r=client.post("/api/exhibits",json=item(title=title,visibility=visibility,**kwargs))
    assert r.status_code==201,r.text
    return r.json()["id"]


def create_trail(client,title="从米线到天空的藏宝图"):
    r=client.post("/api/mysteries",json={
        "title":title,
        "premise":"有两把钥匙隐藏在真实馆藏之中，只有认真思考的探险者才能开启终点。"})
    assert r.status_code==201,r.text
    return r.json()["id"]


def add_stage(client,trail_id,answer,distractors,clue="沿着真相的痕迹前进，猜一猜哪件真实藏品是这一站的答案？"):
    return client.post(f"/api/mysteries/{trail_id}/stages",json={
        "clue":clue,
        "hint":"它在真实馆藏中拥有一条可以打开的原始页面。",
        "answer_exhibit_id":answer,"distractor_ids":distractors})


def publish(client,trail_id):
    return client.post(f"/api/mysteries/{trail_id}/publish")


def ready_pair(alice,bob):
    a=create_exhibit(alice,"云南米线",tags="云南,食物")
    b=create_exhibit(bob,"火星探测器",tags="太空,探索")
    c=create_exhibit(alice,"青铜古钟",tags="文物,古代")
    d=create_exhibit(bob,"菌子图鉴",tags="蘑菇,观察")
    e=create_exhibit(alice,"风景摄影集",tags="旅行,风景")
    t=create_trail(alice)
    p=add_stage(alice,t,a,[b,c])
    q=add_stage(alice,t,b,[d,e])
    assert p.status_code==201,p.text
    assert q.status_code==201,q.text
    return t,(a,b,c,d,e)


def test_empty_public_gallery_and_guest_requires_login_to_play(env):
    alice,bob,guest=env
    assert guest.get("/api/mysteries").status_code==200
    assert guest.get("/api/mysteries").json()["items"]==[]
    assert guest.get("/api/mysteries/random").json()["trail"] is None
    assert guest.get("/api/mysteries/mine").status_code==401
    assert guest.post("/api/mysteries",json={
        "title":"假的藏宝图","premise":"未登录访客不允许创建真正的谜案内容。"}).status_code==401
    assert guest.get("/api/mysteries/123/play").status_code==401


def test_authority_source_validations_and_unique_answer(env):
    alice,bob,guest=env
    own=create_exhibit(alice,"龙宫珍珠")
    other=create_exhibit(bob,"龙宫珊瑚")
    third=create_exhibit(alice,"秘密手稿",visibility="private")
    fourth=create_exhibit(bob,"日晷")
    fifth=create_exhibit(alice,"帝王史")
    t=create_trail(alice)
    assert add_stage(alice,t,third,[own,other]).status_code==404
    assert add_stage(alice,t,own,[third,other]).status_code==404
    assert add_stage(alice,t,own,[own,other]).status_code==422
    assert add_stage(bob,t,own,[other,fourth]).status_code==404
    assert add_stage(guest,t,own,[other,fourth]).status_code==401
    assert publish(alice,t).status_code==409
    assert add_stage(alice,t,own,[other,fourth]).status_code==201
    assert add_stage(alice,t,own,[other,fifth]).status_code==409
    assert publish(bob,t).status_code==404
    assert publish(alice,t).status_code==409
    assert add_stage(alice,t,other,[fourth,fifth]).status_code==201
    assert publish(alice,t).status_code==200


def test_public_preview_never_leaks_correct_answer_or_hints(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    assert publish(alice,t).status_code==200
    listing=guest.get("/api/mysteries").json()["items"][0]
    assert listing["id"]==t
    assert listing["stages"]==2
    assert "answer_exhibit_id" not in str(listing)
    assert "distractor_ids" not in str(listing)
    assert "hint" not in str(listing)
    assert guest.get(f"/api/mysteries/{t}").status_code==200
    assert guest.get(f"/api/mysteries/{t}/play").status_code==401
    first=bob.get(f"/api/mysteries/{t}/play")
    assert first.status_code==200,first.text
    data=first.json()
    assert data["stage"]["index"]==1
    assert len(data["stage"]["options"])==3
    assert {r["id"] for r in data["stage"]["options"]}=={a,b,c}
    assert data["stage"]["hint"] is None
    assert "is_answer" not in str(data)
    assert "answer_exhibit_id" not in str(data)
    assert guest.get("/api/mysteries/sources").status_code==200


def test_wrong_guess_reveals_hint_correct_advances_only_this_player(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    publish(alice,t)
    wrong=bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":c})
    assert wrong.status_code==200,wrong.text
    assert wrong.json()["correct"] is False
    assert "真实馆藏" in wrong.json()["hint"]
    step=bob.get(f"/api/mysteries/{t}/play").json()
    assert step["wrong"]==1 and step["solved"]==0
    assert step["stage"]["hint"]
    assert bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":999999}).status_code==400
    solved=bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":a})
    assert solved.status_code==200 and solved.json()["correct"] is True
    assert solved.json()["revealed"]["id"]==a
    assert solved.json()["completed"] is False
    second=bob.get(f"/api/mysteries/{t}/play").json()
    assert second["stage"]["index"]==2
    assert second["stage"]["hint"] is None
    final=bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":b})
    assert final.status_code==200 and final.json()["completed"]
    assert final.json()["stars"]>=1
    completed=bob.get(f"/api/mysteries/{t}/play").json()
    assert completed["completed"] and len(completed["route"])==2
    assert bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":b}).status_code==409
    assert guest.get("/api/mysteries").json()["items"][0]["completions"]==1
    author_view=alice.get(f"/api/mysteries/{t}/play").json()
    assert author_view["solved"]==0 and not author_view["completed"]


def test_private_progress_restart_and_new_version_reset(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    publish(alice,t)
    bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":a})
    assert bob.get(f"/api/mysteries/{t}/play").json()["solved"]==1
    assert bob.post(f"/api/mysteries/{t}/restart").status_code==200
    assert bob.get(f"/api/mysteries/{t}/play").json()["solved"]==0
    bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":a})
    assert alice.post(f"/api/mysteries/{t}/unpublish").status_code==200
    assert guest.get(f"/api/mysteries/{t}").status_code==404
    assert bob.get(f"/api/mysteries/{t}/play").status_code==404
    assert publish(alice,t).status_code==200
    p=bob.get(f"/api/mysteries/{t}/play").json()
    assert p["solved"]==0 and p["wrong"]==0
    assert guest.get("/api/mysteries").json()["items"][0]["completions"]==0


def test_public_retraction_hides_entire_trail_and_stops_play(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    publish(alice,t)
    assert bob.get(f"/api/mysteries/{t}/play").status_code==200
    out=bob.patch(f"/api/exhibits/{b}",json=item(title="火星探测器",visibility="private"))
    assert out.status_code==200,out.text
    assert guest.get("/api/mysteries").json()["items"]==[]
    assert guest.get(f"/api/mysteries/{t}").status_code==404
    assert bob.get(f"/api/mysteries/{t}/play").status_code==404
    assert bob.post(f"/api/mysteries/{t}/guess",json={"exhibit_id":a}).status_code==404
    assert publish(alice,t).status_code==409
    mine=alice.get("/api/mysteries/mine").json()["items"][0]
    assert mine["available"] is False
    assert any(not option["available"] for stage in mine["stages"] for option in stage["options"])
    assert "火星探测器" not in str(mine["stages"])
    restored=bob.patch(f"/api/exhibits/{b}",json=item(title="火星探测器",visibility="public"))
    assert restored.status_code==200
    assert guest.get(f"/api/mysteries/{t}").status_code==200


def test_parent_private_studio_hides_entire_puzzle(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    publish(alice,t)
    module=sys.modules["wa_test_server"]
    with module.db() as conn:
        conn.execute("""INSERT INTO creator_studio_projects
            (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (1,a,"私人工作室展品","quiz","private","{}",module.now(),module.now()))
    assert guest.get(f"/api/mysteries/{t}").status_code==404
    assert guest.get("/api/mysteries").json()["items"]==[]
    assert bob.get(f"/api/mysteries/{t}/play").status_code==404


def test_author_only_stage_removal_and_private_transition(env):
    alice,bob,guest=env
    t,(a,b,c,d,e)=ready_pair(alice,bob)
    publish(alice,t)
    mine=alice.get("/api/mysteries/mine").json()["items"][0]
    sid=mine["stages"][0]["id"]
    assert bob.delete(f"/api/mysteries/{t}/stages/{sid}").status_code==404
    assert alice.delete(f"/api/mysteries/{t}/stages/999999").status_code==404
    assert alice.delete(f"/api/mysteries/{t}/stages/{sid}").status_code==200
    assert guest.get("/api/mysteries").json()["items"]==[]
    assert publish(alice,t).status_code==409
    assert alice.delete(f"/api/mysteries/{t}").status_code==200
    assert alice.get("/api/mysteries/mine").json()["items"]==[]


def test_real_source_picker_and_own_private_does_not_return(env):
    alice,bob,guest=env
    public=create_exhibit(alice,"人类的太空望远镜",tags="太空,航天")
    secret=create_exhibit(bob,"秘密太空望远镜",visibility="private",tags="太空,秘密")
    picker=guest.get("/api/mysteries/sources?q=太空")
    assert picker.status_code==200,picker.text
    assert [x["id"] for x in picker.json()["items"]]==[public]
    assert secret not in [x["id"] for x in picker.json()["items"]]
    assert "真实" in picker.json()["notice"]


def test_v32_frontend_assets_version_without_ci(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="33.0"
    html=guest.get("/").text
    assert "WONDER ATLAS · WORLD " in html
    assert "万物谜案馆" in html
    for name in ("mysteries.js","mysteries.css"):
        assert guest.get(f"/static/{name}").status_code==200
        assert f"/static/{name}" in html
    assert "WonderMysteries.render" in guest.get("/static/app.js").text
