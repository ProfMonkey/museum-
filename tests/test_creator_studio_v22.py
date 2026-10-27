"""V22 user-created playable exhibits: privacy, safe templates, consent and regression."""
from test_multiuser import env, item


def quiz(**override):
    data={"kind":"quiz","title":"神奇化石挑战",
          "description":"四选一关于发现化石的互动问题",
          "config":{"question":"考古学和古生物学中，哪一项更像是化石的直接记录？",
                    "options":["岩层里的遗迹","未来星际小说","电脑游戏角色","随手画的图案"],
                    "answer":0,
                    "explanation":"化石和它所在的地层关系为古生物研究提供了可以分析的具体证据。"}}
    data.update(override)
    return data


def ecology(**kw):
    return {"kind":"ecology","title":"一座虚拟岛屿",
            "description":"通过简化模型观察种群的长期变化",
            "config":{"population":120,"capacity":500,"growth":.2,"loss":.02,"steps":40,**kw}}


def music(**kw):
    return {"kind":"music","title":"八度星际音乐",
            "description":"可以改变音符的十六格声音实验",
            "config":{"bpm":120,"notes":[0,-1,2,-1,4,-1,7,-1,5,-1,4,-1,2,-1,0,-1],**kw}}


def create(client,content=None):
    res=client.post("/api/play/studio",json=content or quiz())
    assert res.status_code==201,res.text
    return res.json()


def publish(client,pid,value="public"):
    return client.patch(f"/api/play/studio/{pid}/visibility",json={"visibility":value})


def test_config_and_no_fake_content(env):
    alice,bob,guest=env
    config=guest.get("/api/play/studio/config")
    assert config.status_code==200
    assert {x["kind"] for x in config.json()["templates"]}=={"quiz","ecology","music"}
    assert len(config.json()["defaults"]["music"]["notes"])==16
    assert guest.get("/api/play/studio").json()["items"]==[]
    assert guest.get("/api/play/studio?scope=mine").status_code==401
    assert guest.post("/api/play/studio",json=quiz()).status_code==401
    assert guest.get("/api/play/studio/1").status_code==404
    assert guest.get("/api/play/studio?scope=other").status_code==422


def test_creation_private_museum_post_and_no_answers_in_backing(env):
    alice,bob,guest=env
    created=create(alice)
    pid,eid=created["id"],created["exhibit_id"]
    assert created["visibility"]=="private"
    details=alice.get(f"/api/play/studio/{pid}").json()
    assert details["is_owner"] and details["config"]["answer"]==0
    assert guest.get(f"/api/play/studio/{pid}").status_code==404
    assert bob.get(f"/api/play/studio/{pid}").status_code==404
    assert guest.get("/api/play/studio").json()["items"]==[]
    assert guest.get(f"/api/exhibits/{eid}").status_code==404
    backing=alice.get(f"/api/exhibits/{eid}").json()
    assert backing["title"]=="互动展品｜神奇化石挑战"
    assert backing["visibility"]=="private"
    assert backing["domain"]=="游戏与交互"
    assert "岩层里的遗迹" not in backing["story"] and "correct" not in backing["story"]
    assert alice.get("/api/my/exhibits").json()[0]["id"]==eid


def test_quiz_published_only_by_owner_answer_checked_server_side(env):
    alice,bob,guest=env
    created=create(alice)
    pid=created["id"]
    assert bob.patch(f"/api/play/studio/{pid}/visibility",
         json={"visibility":"public"}).status_code==404
    assert publish(alice,pid).status_code==200
    data=guest.get(f"/api/play/studio/{pid}")
    assert data.status_code==200,data.text
    detail=data.json()
    assert detail["config"]["question"] and "answer" not in detail["config"]
    assert detail["public"] is True and detail["is_owner"] is False
    assert guest.get(f"/api/exhibits/{created['exhibit_id']}").status_code==200
    assert len(guest.get("/api/play/studio").json()["items"])==1
    wrong=guest.post(f"/api/play/studio/{pid}/answer",json={"answer":2})
    assert wrong.status_code==200 and not wrong.json()["correct"]
    assert wrong.json()["correct_answer"]==0
    right=bob.post(f"/api/play/studio/{pid}/answer",json={"answer":0})
    assert right.status_code==200 and right.json()["correct"]
    assert "化石" in right.json()["explanation"]
    assert guest.post(f"/api/play/studio/{pid}/answer",json={"answer":4}).status_code==422
    assert publish(alice,pid,"private").status_code==200
    assert guest.get(f"/api/play/studio/{pid}").status_code==404
    assert guest.get(f"/api/exhibits/{created['exhibit_id']}").status_code==404


def test_manual_exhibit_privacy_revocation_never_reactivates_implicitly(env):
    alice,bob,guest=env
    created=create(alice);pid,eid=created["id"],created["exhibit_id"]
    assert publish(alice,pid).status_code==200
    assert guest.get(f"/api/play/studio/{pid}").status_code==200
    hidden=alice.patch(f"/api/exhibits/{eid}",
                       json=item(title="我先暂停互动展品的展出",visibility="private"))
    assert hidden.status_code==200,hidden.text
    detail=alice.get(f"/api/play/studio/{pid}").json()
    assert detail["visibility"]=="private" and detail["public"] is False
    assert guest.get(f"/api/play/studio/{pid}").status_code==404
    # Even republishing the backing card from the legacy edit screen cannot
    # silently re-open studio authorization: requires a fresh studio publish.
    assert alice.patch(f"/api/exhibits/{eid}",
        json=item(title="我先暂停互动展品的展出",visibility="public")).status_code==200
    assert guest.get(f"/api/play/studio/{pid}").status_code==404
    assert publish(alice,pid).status_code==200
    assert guest.get(f"/api/play/studio/{pid}").status_code==200


def test_update_owned_project_syncs_backing_and_blocks_other_users(env):
    alice,bob,guest=env
    created=create(alice);pid=created["id"]
    new=quiz(title="陨石与流星",config={**quiz()["config"],
              "question":"当我们看到一块陨石样本时，下面哪一种描述较为合理？",
              "answer":3})
    assert bob.put(f"/api/play/studio/{pid}",json=new).status_code==404
    result=alice.put(f"/api/play/studio/{pid}",json=new)
    assert result.status_code==200,result.text
    data=alice.get(f"/api/play/studio/{pid}").json()
    assert data["title"]=="陨石与流星"
    assert data["config"]["answer"]==3
    backing=alice.get(f"/api/exhibits/{created['exhibit_id']}").json()
    assert backing["title"]=="互动展品｜陨石与流星"
    assert backing["visibility"]=="private"


def test_quiz_rejects_injected_keys_ambiguous_choices_and_short_text(env):
    alice,bob,guest=env
    base=quiz()
    bad=[
      {**base,"config":{**base["config"],"answer":4}},
      {**base,"config":{**base["config"],"answer":-1}},
      {**base,"config":{**base["config"],"options":["一样"]*4}},
      {**base,"config":{**base["config"],"options":["a","b","c"]}},
      {**base,"config":{**base["config"],"script":"alert('x')"}},
      {**base,"config":{**base["config"],"explanation":"过短"}},
      {**base,"config":{**base["config"],"question":"太短"}},
      {**base,"kind":"arbitrary"},
      {**base,"unknown_source":"https://attacker.test"},
    ]
    for draft in bad:
        response=alice.post("/api/play/studio",json=draft)
        assert response.status_code==422,(draft,response.text)
    assert guest.get("/api/play/studio").json()["items"]==[]


def test_ecology_simulation_deterministic_and_strictly_bounded(env):
    alice,bob,guest=env
    created=create(alice,ecology());pid=created["id"]
    assert guest.post(f"/api/play/studio/{pid}/simulate",
           json=ecology()["config"]).status_code==404
    assert publish(alice,pid).status_code==200
    scenario=ecology()["config"]
    first=guest.post(f"/api/play/studio/{pid}/simulate",json=scenario)
    second=guest.post(f"/api/play/studio/{pid}/simulate",json=scenario)
    assert first.status_code==200,first.text
    assert first.json()==second.json()
    curve=first.json()["result"]
    assert len(curve["series"])==41
    assert curve["series"][0]==120
    assert curve["final"]>120
    assert all(0<=x<=1000 for x in curve["series"])
    revised=guest.post(f"/api/play/studio/{pid}/simulate",
      json={**scenario,"loss":.25})
    assert revised.status_code==200 and revised.json()["result"]["final"]<curve["final"]
    for bad in ({**scenario,"steps":500},{**scenario,"growth":"NaN"},
                {**scenario,"loss":-.1},{**scenario,"custom_code":"hello"}):
        assert guest.post(f"/api/play/studio/{pid}/simulate",json=bad).status_code==422
    assert guest.post(f"/api/play/studio/{pid}/answer",json={"answer":0}).status_code==409
    assert guest.get(f"/api/play/studio/{pid}").json()["kind"]=="ecology"


def test_music_sixteen_notes_and_client_audio_only(env):
    alice,bob,guest=env
    created=create(alice,music());pid=created["id"]
    assert publish(alice,pid).status_code==200
    data=guest.get(f"/api/play/studio/{pid}").json()
    assert data["config"]["bpm"]==120
    assert len(data["config"]["notes"])==16
    assert data["kind"]=="music"
    assert guest.post(f"/api/play/studio/{pid}/answer",json={"answer":0}).status_code==409
    assert guest.post(f"/api/play/studio/{pid}/simulate",json=ecology()["config"]).status_code==409
    for altered in [
       music(notes=[0,1,2]),
       music(notes=[0]*15+[8]),
       music(notes=[0]*15+[-2]),
       music(bpm=999),
       music(notes=[0]*15+["<script>"]),
    ]:
        assert alice.post("/api/play/studio",json=altered).status_code==422


def test_delete_owned_project_removes_only_its_created_backing(env):
    alice,bob,guest=env
    unrelated=alice.post("/api/exhibits",json=item(title="已有的私人外部藏品")).json()["id"]
    created=create(alice)
    pid,eid=created["id"],created["exhibit_id"]
    assert bob.delete(f"/api/play/studio/{pid}").status_code==404
    assert guest.delete(f"/api/play/studio/{pid}").status_code==401
    assert alice.delete(f"/api/play/studio/{pid}").status_code==200
    assert alice.get(f"/api/exhibits/{eid}").status_code==404
    assert alice.get(f"/api/exhibits/{unrelated}").status_code==200
    assert alice.get(f"/api/play/studio/{pid}").status_code==404


def test_deleting_backing_exhibit_cascades_without_leak(env):
    alice,bob,guest=env
    created=create(alice)
    assert publish(alice,created["id"]).status_code==200
    eid=created["exhibit_id"]
    assert alice.delete(f"/api/exhibits/{eid}").status_code==200
    assert alice.get(f"/api/play/studio/{created['id']}").status_code==404
    assert guest.get("/api/play/studio").json()["items"]==[]


def test_project_limit_per_user_is_enforced(env):
    alice,bob,guest=env
    for i in range(15):
        draft=quiz(title=f"作品第{i+1}件")
        r=alice.post("/api/play/studio",json=draft)
        assert r.status_code==201,(i,r.text)
    assert alice.post("/api/play/studio",json=quiz(title="第十六件作品")).status_code==429
    assert len(alice.get("/api/play/studio?scope=mine").json()["items"])==15
    assert bob.get("/api/play/studio?scope=mine").json()["items"]==[]
    assert len(alice.get("/api/my/exhibits").json())==15
    assert guest.get("/api/feed").json()["items"]==[]


def test_v22_static_and_previous_playable_routes_unchanged(env):
    alice,bob,guest=env
    html=guest.get("/").text
    assert "WONDER ATLAS · WORLD " in html
    assert guest.get("/api/health").json()["ok"] is True
    for asset in ("studio.js","studio.css"):
        path="/static/"+asset
        assert path in html and guest.get(path).status_code==200
    assert 'data-view="play"' in html
    assert guest.get("/api/play/config").status_code==200
    assert guest.get("/api/play/relays").status_code==200
    assert guest.post("/api/play/preview",
      json={"kind":"orbit","a":1.0,"b":1.0,"c":1.0}).status_code==200
