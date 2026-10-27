"""V24 turntable regression: user choice, museum origin, fairness and privacy."""
import wheel_api
from test_multiuser import env, item


def wheel(topic="food",title="今晚到底吃什么",theme="amber",no_repeat=True):
    return {"topic":topic,"title":title,"theme":theme,"no_repeat":no_repeat}


def create(client,**kwargs):
    r=client.post("/api/wheels",json=wheel(**kwargs))
    assert r.status_code==201,r.text
    return r.json()["id"]


def manual(client,wid,label):
    return client.post(f"/api/wheels/{wid}/items",json={"kind":"manual","label":label})


def source(client,wid,eid):
    return client.post(f"/api/wheels/{wid}/items",json={"kind":"exhibit","exhibit_id":eid})


def museum(client,title,visibility="public",**kw):
    r=client.post("/api/exhibits",json=item(title=title,visibility=visibility,**kw))
    assert r.status_code==201,r.text
    return r.json()["id"]


def test_no_fake_community_records_and_topics(env):
    alice,bob,guest=env
    cfg=guest.get("/api/wheels/config")
    assert cfg.status_code==200
    assert {x["key"] for x in cfg.json()["topics"]}=={"food","travel","watch","activity","custom"}
    assert cfg.json()["max_items"]==24
    assert cfg.json()["max_wheels"]==12
    assert guest.get("/api/wheels/sources?q=牛排").json()["items"]==[]
    assert guest.get("/api/wheels").status_code==401
    assert guest.post("/api/wheels",json=wheel()).status_code==401
    assert alice.get("/api/wheels").json()["items"]==[]


def test_guest_temporary_draw_does_not_store_an_account_wheel(env,monkeypatch):
    alice,bob,guest=env
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    payload={"options":["米线","火锅","牛排","烤鱼"],"no_repeat":True}
    r=guest.post("/api/wheels/preview",json=payload)
    assert r.status_code==200,r.text
    assert r.json()["index"]==0 and r.json()["label"]=="米线"
    assert r.json()["chance_denominator"]==4
    again=guest.post("/api/wheels/preview",json={**payload,"last_index":0})
    assert again.status_code==200
    assert again.json()["index"]==1
    assert again.json()["chance_denominator"]==3
    assert alice.get("/api/wheels").json()["items"]==[]
    assert guest.get("/api/wheels").status_code==401


def test_preview_cannot_receive_empty_or_duplicate_unbounded_inputs(env):
    a,b,g=env
    payloads=[
        {"options":["米线"]},
        {"options":["米线"]*3},
        {"options":["a"]*25},
        {"options":["","a"]},
        {"options":["A","a"]},
        {"options":["d"*76,"a"]},
        {"options":["a","b"],"last_index":-1},
        {"options":["a","b"],"do_sql":"DROP TABLE"},
    ]
    for payload in payloads:
        r=g.post("/api/wheels/preview",json=payload)
        assert r.status_code==422,(payload,r.text)


def test_created_wheel_persists_custom_meals_privately(env):
    alice,bob,guest=env
    wid=create(alice)
    assert manual(alice,wid,"米线").status_code==201
    assert manual(alice,wid,"菌子火锅").status_code==201
    assert manual(alice,wid,"牛排").status_code==201
    own=alice.get(f"/api/wheels/{wid}").json()
    assert own["topic"]=="food" and own["theme"]=="amber"
    assert [x["label"] for x in own["items"]]==["米线","菌子火锅","牛排"]
    assert len(own["history"])==0
    assert bob.get(f"/api/wheels/{wid}").status_code==404
    assert guest.get(f"/api/wheels/{wid}").status_code==401
    assert len(alice.get("/api/wheels").json()["items"])==1
    assert bob.get("/api/wheels").json()["items"]==[]
    assert guest.get("/api/feed").json()["items"]==[]


def test_uniform_server_selection_and_no_repeat_lock(env,monkeypatch):
    alice,bob,guest=env
    wid=create(alice)
    for label in ("a","b","c"):
        assert manual(alice,wid,label).status_code==201
    observed=[]
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    for _ in range(5):
        res=alice.post(f"/api/wheels/{wid}/spin")
        assert res.status_code==200,res.text
        observed.append(res.json()["winner"]["label"])
        if len(observed)>1:
            assert observed[-1]!=observed[-2]
        assert res.json()["chance_denominator"]==(3 if len(observed)==1 else 2)
    assert observed==["a","b","a","b","a"]
    record=alice.get(f"/api/wheels/{wid}").json()["history"]
    assert [x["label"] for x in record][:2]==["a","b"]
    assert all(x["available"] for x in record)


def test_two_options_no_repeat_alternates_but_toggle_off_allows_repeat(env,monkeypatch):
    alice,bob,g=env
    wid=create(alice)
    manual(alice,wid,"coffee")
    manual(alice,wid,"tea")
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert alice.post(f"/api/wheels/{wid}/spin").json()["winner"]["label"]=="coffee"
    assert alice.post(f"/api/wheels/{wid}/spin").json()["winner"]["label"]=="tea"
    assert alice.patch(f"/api/wheels/{wid}",json=wheel(no_repeat=False)).status_code==200
    c=alice.post(f"/api/wheels/{wid}/spin").json()
    d=alice.post(f"/api/wheels/{wid}/spin").json()
    assert c["winner"]["label"]=="coffee"==d["winner"]["label"]
    assert c["chance_denominator"]==2


def test_search_real_public_exhibit_then_add_and_spin(env,monkeypatch):
    alice,bob,guest=env
    good=museum(bob,"昆明鲜花饼")
    hidden=museum(bob,"私人烤鱼",visibility="private")
    wid=create(alice)
    assert source(alice,wid,hidden).status_code==404
    assert [x["id"] for x in guest.get("/api/wheels/sources?q=鲜花饼").json()["items"]]==[good]
    r=source(alice,wid,good)
    assert r.status_code==201,r.text
    assert source(alice,wid,good).status_code==409
    assert manual(alice,wid,"米线").status_code==201
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    out=alice.post(f"/api/wheels/{wid}/spin").json()["winner"]
    assert out["kind"]=="exhibit" and out["exhibit_id"]==good
    assert out["label"]=="昆明鲜花饼"
    assert guest.get("/api/wheels/sources?q=烤鱼").json()["items"]==[]


def test_revoked_source_no_longer_drawn_and_history_title_redacted(env,monkeypatch):
    alice,bob,guest=env
    good=museum(bob,"只能在公开时看见的甜品")
    wid=create(alice)
    assert source(alice,wid,good).status_code==201
    assert manual(alice,wid,"米线").status_code==201
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    chosen=alice.post(f"/api/wheels/{wid}/spin").json()
    assert chosen["winner"]["label"]=="只能在公开时看见的甜品"
    assert bob.patch(f"/api/exhibits/{good}",json=item(title="只能在公开时看见的甜品",visibility="private")).status_code==200
    data=alice.get(f"/api/wheels/{wid}").json()
    assert data["unavailable_count"]==1
    assert len(data["items"])==1 and data["items"][0]["label"]=="米线"
    assert data["history"][0]["available"] is False
    assert "只能在公开时看见的甜品" not in str(data)
    assert alice.post(f"/api/wheels/{wid}/spin").status_code==409
    assert source(alice,wid,good).status_code==404


def test_deletion_does_not_keep_deleted_label_in_history(env,monkeypatch):
    alice,bob,guest=env
    eid=museum(bob,"不应在历史泄漏的菜")
    wid=create(alice)
    source(alice,wid,eid)
    manual(alice,wid,"米饭")
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert alice.post(f"/api/wheels/{wid}/spin").status_code==200
    assert bob.delete(f"/api/exhibits/{eid}").status_code==200
    data=alice.get(f"/api/wheels/{wid}").json()
    assert data["unavailable_count"]==1
    assert "不应在历史泄漏的菜" not in str(data)
    assert data["history"][0]["label"]=="已移除或撤回的选项"


def test_ownership_guards_mutations_no_cross_user_leaks(env):
    alice,bob,guest=env
    wid=create(alice)
    r=manual(alice,wid,"豆腐脑")
    assert r.status_code==201
    item_id=r.json()["id"]
    attempts=[
        bob.patch(f"/api/wheels/{wid}",json=wheel(title="别人篡改我的选项")),
        bob.delete(f"/api/wheels/{wid}"),
        bob.post(f"/api/wheels/{wid}/items",json={"kind":"manual","label":"偷偷加一个"}),
        bob.delete(f"/api/wheels/{wid}/items/{item_id}"),
        bob.post(f"/api/wheels/{wid}/spin")
    ]
    assert all(x.status_code==404 for x in attempts)
    assert guest.post(f"/api/wheels/{wid}/spin").status_code==401
    assert alice.get(f"/api/wheels/{wid}").json()["items"][0]["label"]=="豆腐脑"


def test_duplicate_whitespace_case_and_max_entries(env):
    alice,bob,guest=env
    wid=create(alice)
    assert manual(alice,wid,"  HotPot  ").status_code==201
    assert manual(alice,wid,"hotpot").status_code==409
    assert manual(alice,wid,"").status_code==422
    assert manual(alice,wid,"超"*76).status_code==422
    for i in range(23):
        assert manual(alice,wid,f"meal-{i}").status_code==201
    assert alice.get(f"/api/wheels/{wid}").json()["count"]==24
    assert manual(alice,wid,"第25道菜").status_code==429


def test_cap_private_wheels_and_theme_update_deletion(env):
    alice,bob,g=env
    ids=[create(alice,title=f"转盘{i}",topic="custom") for i in range(12)]
    assert alice.post("/api/wheels",json=wheel(title="第十三个")).status_code==429
    first=ids[0]
    changed=alice.patch(f"/api/wheels/{first}",json=wheel(title="明天去哪玩",topic="travel",theme="rose"))
    assert changed.status_code==200
    x=alice.get(f"/api/wheels/{first}").json()
    assert x["topic"]=="travel" and x["theme"]=="rose" and x["title"]=="明天去哪玩"
    assert alice.delete(f"/api/wheels/{first}").status_code==200
    assert alice.get(f"/api/wheels/{first}").status_code==404
    assert alice.post("/api/wheels",json=wheel(title="新一号")).status_code==201


def test_history_bounded_to_last_twenty(env,monkeypatch):
    alice,bob,g=env
    wid=create(alice,no_repeat=False)
    manual(alice,wid,"A")
    manual(alice,wid,"B")
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    for _ in range(25):
        assert alice.post(f"/api/wheels/{wid}/spin").status_code==200
    hist=alice.get(f"/api/wheels/{wid}").json()["history"]
    assert len(hist)==20
    assert all(x["label"]=="A" for x in hist)


def test_release_assets_and_old_play_features_survive(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["ok"] is True
    html=guest.get("/").text
    assert "WONDER ATLAS · WORLD " in html
    assert 'data-view="wheels"' in html
    for asset in ("/static/wheel.css","/static/wheel.js"):
        assert asset in html and guest.get(asset).status_code==200
    assert guest.get("/api/play/studio/config").status_code==200
    assert guest.get("/api/play/sandbox/config").status_code==200
    assert guest.get("/api/lab/config").status_code==200


def test_source_search_matches_food_category_domain_and_tags(env):
    alice,bob,guest=env
    tagged=museum(bob,"周末菜单",category="其他",domain="其他",tags="云南米线,早餐")
    by_tag=guest.get("/api/wheels/sources?q=云南米线")
    assert by_tag.status_code==200
    assert [x["id"] for x in by_tag.json()["items"]]==[tagged]
    by_category_id=museum(bob,"家常食谱",category="饮食文化",domain="食物与饮食",tags="家常")
    found=guest.get("/api/wheels/sources?q=饮食文化")
    assert found.status_code==200
    assert by_category_id in [x["id"] for x in found.json()["items"]]
