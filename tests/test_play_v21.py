"""V21 API-level tests for bounded interactive simulations and consentful real-item relays."""
from test_multiuser import env, item


def experiment(kind="orbit",a=1,b=1,c=1,iterations=55):
    return {"kind":kind,"a":a,"b":b,"c":c,"iterations":iterations}


def new_exhibit(client, title, visibility="public", **kw):
    response=client.post("/api/exhibits",json=item(title=title,visibility=visibility,**kw))
    assert response.status_code==201,response.text
    return response.json()["id"]


def create_relay(client,eid,title="从石头到宇宙"):
    return client.post("/api/play/relays",json={"source_id":eid,"title":title})


def link(client,relay_id,eid,reason="从化石的地质年代联想到星体与时间的尺度。",
         relation="创意联想",source_url=""):
    return client.post(f"/api/play/relays/{relay_id}/steps",
                       json={"source_id":eid,"reason":reason,"relation":relation,
                             "source_url":source_url})


def test_models_are_real_calculations_not_claimed_measurements(env):
    alice,bob,guest=env
    cfg=guest.get("/api/play/config")
    assert cfg.status_code==200 and len(cfg.json()["models"])==3
    x=guest.post("/api/play/preview",json=experiment()).json()["result"]
    assert x["outcome"]["period_years"]==1
    assert 29<x["outcome"]["speed_kms"]<30
    assert "二体" in x["note"]
    assert guest.post("/api/play/preview",json=experiment()).json()["result"]==x
    gears=guest.post("/api/play/preview",json=experiment("gears",24,48,60))
    assert gears.status_code==200
    assert gears.json()["result"]["outcome"]["output_rpm"]==-30
    assert gears.json()["result"]["outcome"]["ideal_torque_ratio"]==2
    fractal=guest.post("/api/play/preview",json=experiment("fractal",-.6,0,2,70))
    assert fractal.status_code==200
    assert fractal.json()["result"]["outcome"]["max_iterations"]==70
    assert fractal.json()["result"]["outcome"]["window_width"]==1.7


def test_models_reject_invalid_scientific_parameters_and_fabricated_fields(env):
    a,b,visitor=env
    invalid=[
        experiment("orbit",0,1,1),experiment("orbit",1,0,1),
        experiment("orbit",1,1,2),experiment("gears",7,16,40),
        experiment("gears",8.5,16,40),experiment("gears",16,22,1),
        experiment("fractal",-3,0,1),experiment("fractal",0,0,8),
        experiment("fractal",0,0,1,91),
        {"kind":"orbit","a":"NaN","b":1,"c":1},
        {"kind":"orbit","a":1,"b":1,"c":1,"is_measured":True},
        {"kind":"oracle","a":1,"b":1,"c":1}
    ]
    for data in invalid:
        response=visitor.post("/api/play/preview",json=data)
        assert response.status_code==422,(data,response.text)


def test_saved_simulation_is_real_private_exhibit_and_never_public_by_default(env):
    alice,bob,visitor=env
    assert visitor.post("/api/play/records",json=experiment()).status_code==401
    r=alice.post("/api/play/records",json=experiment("gears",16,32,30))
    assert r.status_code==201,r.text
    eid=r.json()["id"]
    assert r.json()["visibility"]=="private"
    saved=alice.get(f"/api/exhibits/{eid}").json()
    assert saved["domain"]=="工程与发明"
    assert saved["category"]=="机械装置"
    assert saved["title"].startswith("互动实验｜")
    assert "非真实测量" in saved["story"] and "-15" in saved["story"]
    assert visitor.get(f"/api/exhibits/{eid}").status_code==404
    assert bob.get(f"/api/exhibits/{eid}").status_code==404
    assert visitor.get("/api/feed").json()["items"]==[]


def test_records_capacity_bounded_and_previous_exhibits_remain_intact(env):
    alice,bob,guest=env
    for i in range(30):
        r=alice.post("/api/play/records",json=experiment("orbit",a=.5+i*.1))
        assert r.status_code==201,r.text
    assert alice.post("/api/play/records",json=experiment()).status_code==429
    assert len(alice.get("/api/my/exhibits").json())==30
    assert guest.get("/api/feed").json()["items"]==[]


def test_no_fake_relays_and_auth_start_permission(env):
    alice,bob,guest=env
    assert guest.get("/api/play/relays").json()["items"]==[]
    assert guest.get("/api/play/sources").json()["items"]==[]
    assert guest.post("/api/play/relays",json={"source_id":1,"title":"匿名路线"}).status_code==401
    private_id=new_exhibit(alice,"我的私人化石",visibility="private")
    assert create_relay(alice,private_id).status_code==404
    assert guest.get("/api/play/sources?q=私人").json()["items"]==[]
    eid=new_exhibit(alice,"真正在馆中发布的陨石")
    assert [x["id"] for x in guest.get("/api/play/sources?q=陨石").json()["items"]]==[eid]
    assert create_relay(alice,eid,title=" ").status_code==422


def test_three_people_can_link_real_public_exhibits_without_modifying_others(env):
    alice,bob,guest=env
    start=new_exhibit(alice,"陨石")
    mid=new_exhibit(bob,"太阳系")
    end=new_exhibit(alice,"航天器")
    created=create_relay(alice,start)
    assert created.status_code==201,created.text
    rid=created.json()["id"]
    assert len(guest.get("/api/play/relays").json()["items"])==1
    assert guest.post(f"/api/play/relays/{rid}/steps",json={
        "source_id":mid,"reason":"无账号无法提交"}).status_code==401
    added=link(bob,rid,mid)
    assert added.status_code==201,added.text
    proof=link(alice,rid,end,relation="来源线索",
        source_url="https://example.org/planetary-exploration",
        reason="这里有人提供进一步阅读的外部链接，但本站尚未核验其证据质量。")
    assert proof.status_code==201,proof.text
    chain=guest.get(f"/api/play/relays/{rid}").json()
    assert chain["count"]==3
    assert chain["is_owner"] is False
    assert [x["title"] for x in chain["steps"]]==["陨石","太阳系","航天器"]
    assert [x["contributor"] for x in chain["steps"]]==["Alice","Bob","Alice"]
    assert chain["steps"][2]["relation"]=="来源线索"
    assert chain["steps"][2]["source_url"]=="https://example.org/planetary-exploration"
    assert guest.get("/api/play/relays").json()["items"][0]["last"]=="航天器"
    assert bob.get(f"/api/play/relays/{rid}").json()["is_owner"] is False
    assert alice.get(f"/api/play/relays/{rid}").json()["is_owner"] is True


def test_duplicate_bad_links_and_user_quota_are_rejected(env):
    alice,bob,guest=env
    first=new_exhibit(alice,"起点")
    second=new_exhibit(bob,"一号接力")
    third=new_exhibit(bob,"二号接力")
    fourth=new_exhibit(bob,"三号接力")
    fifth=new_exhibit(bob,"四号接力")
    rid=create_relay(alice,first).json()["id"]
    assert link(bob,rid,first).status_code==409
    assert link(bob,rid,second,reason="内容短").status_code==422
    assert link(bob,rid,second,relation="来源线索").status_code==422
    assert link(bob,rid,second,relation="来源线索",source_url="http://invalid.test").status_code==422
    assert link(bob,rid,second,relation="来源线索",source_url="javascript:alert(1)").status_code==422
    assert link(bob,rid,second,source_url="https://example.org").status_code==422
    for eid in (second,third,fourth):
        assert link(bob,rid,eid).status_code==201
    assert link(bob,rid,fifth).status_code==429
    assert bob.delete(f"/api/play/relays/{rid}").status_code==403


def test_owner_controls_finish_and_deletion(env):
    alice,bob,guest=env
    first=new_exhibit(alice,"起点")
    second=new_exhibit(bob,"终点")
    rid=create_relay(alice,first).json()["id"]
    assert bob.patch(f"/api/play/relays/{rid}",json={"open":False}).status_code==403
    assert alice.patch(f"/api/play/relays/{rid}",json={"open":False}).status_code==200
    assert link(bob,rid,second).status_code==409
    assert alice.patch(f"/api/play/relays/{rid}",json={"open":True}).status_code==200
    assert link(bob,rid,second).status_code==201
    assert guest.delete(f"/api/play/relays/{rid}").status_code==401
    assert alice.delete(f"/api/play/relays/{rid}").status_code==200
    assert guest.get(f"/api/play/relays/{rid}").status_code==404
    assert alice.get(f"/api/exhibits/{first}").status_code==200
    assert bob.get(f"/api/exhibits/{second}").status_code==200


def test_withdraw_root_censors_route_entirely_without_leaking_title(env):
    alice,bob,guest=env
    first=new_exhibit(alice,"从未公开的秘密将被撤回")
    next_id=new_exhibit(bob,"公开的星星")
    rid=create_relay(alice,first).json()["id"]
    assert link(bob,rid,next_id).status_code==201
    assert alice.patch(f"/api/exhibits/{first}",
                       json=item(title="从未公开的秘密将被撤回",visibility="private")).status_code==200
    assert guest.get("/api/play/relays").json()["items"]==[]
    assert guest.get(f"/api/play/relays/{rid}").status_code==404
    assert link(bob,rid,new_exhibit(bob,"新站点")).status_code==409


def test_withdraw_middle_clips_downstream_steps_and_locks_extensions(env):
    alice,bob,guest=env
    one=new_exhibit(alice,"最早的发现")
    two=new_exhibit(bob,"被隐藏的中间一站")
    three=new_exhibit(alice,"下一个线索")
    rid=create_relay(alice,one).json()["id"]
    assert link(bob,rid,two).status_code==201
    assert link(alice,rid,three).status_code==201
    assert bob.patch(f"/api/exhibits/{two}",
        json=item(title="被隐藏的中间一站",visibility="private")).status_code==200
    result=guest.get(f"/api/play/relays/{rid}").json()
    assert result["count"]==1 and [x["title"] for x in result["steps"]]==["最早的发现"]
    assert "被隐藏的中间一站" not in str(result)
    assert "下一个线索" not in str(result)
    assert link(bob,rid,new_exhibit(bob,"无法接在消失节点上")).status_code==409
    assert bob.delete(f"/api/exhibits/{two}").status_code==200
    assert guest.get(f"/api/play/relays/{rid}").json()["count"]==1


def test_main_nav_and_release_version(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="21.0"
    html=guest.get("/").text
    assert "WORLD 21" in html
    assert 'data-view="play"' in html
    for path in ("/static/play.js","/static/play.css"):
        assert path in html
        assert guest.get(path).status_code==200
