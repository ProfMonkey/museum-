"""V23 integration tests for creator-owned time theatre and ideal circuit blocks."""
from test_multiuser import env,item


def circuit(mode="series",voltage=9,resistors=None):
    return {"mode":mode,"voltage":voltage,
            "resistors":resistors if resistors is not None else [100,200,300]}


def timeline():
    return {"events":[
        {"year":-65000000,"title":"古生物变迁","story":"地质与生物在地球历史中的长期变化。",
         "nature":"史料待核","source_url":""},
        {"year":1969,"title":"登月时代","story":"用公开资料探索太空飞行的历史节点。",
         "nature":"史料待核","source_url":"https://www.nasa.gov"},
        {"year":2200,"title":"天空之上的馆藏","story":"一座原创的虚构未来星际城市故事。",
         "nature":"原创虚构","source_url":""}
    ]}


def draft(kind="circuit",title="我的万物积木",config=None):
    return {"kind":kind,"title":title,
            "description":"由普通馆长用安全积木制作的互动博物馆展品。",
            "config":config if config is not None else (circuit() if kind=="circuit" else timeline())}


def create(client,body=None):
    response=client.post("/api/play/sandbox",json=body or draft())
    assert response.status_code==201,response.text
    return response.json()


def publish(client,pid,visibility="public"):
    return client.patch(f"/api/play/sandbox/{pid}/visibility",json={"visibility":visibility})


def test_no_fabricated_projects_and_config_public(env):
    a,b,guest=env
    cfg=guest.get("/api/play/sandbox/config")
    assert cfg.status_code==200
    assert {x["kind"] for x in cfg.json()["templates"]}=={"circuit","timeline"}
    assert cfg.json()["max_projects"]==12
    assert guest.get("/api/play/sandbox").json()["items"]==[]
    assert guest.get("/api/play/sandbox?scope=mine").status_code==401
    assert guest.post("/api/play/sandbox",json=draft()).status_code==401
    assert guest.get("/api/play/sandbox/1").status_code==404


def test_ideal_circuit_series_and_parallel_are_computed_not_mocked(env):
    a,b,guest=env
    series=guest.post("/api/play/sandbox/preview",json=circuit()).json()["result"]
    assert series["equivalent_ohms"]==600
    assert series["total_amperes"]==.015
    assert series["total_watts"]==.135
    assert sum(x["volts"] for x in series["branches"])==9
    parallel=guest.post("/api/play/sandbox/preview",
         json=circuit("parallel",12,[100,200]))
    assert parallel.status_code==200,parallel.text
    p=parallel.json()["result"]
    assert p["equivalent_ohms"]==66.666667
    assert p["total_amperes"]==.18
    assert p["total_watts"]==2.16
    assert [x["amperes"] for x in p["branches"]]==[.12,.06]
    assert [x["volts"] for x in p["branches"]]==[12,12]
    assert guest.post("/api/play/sandbox/preview",json=circuit()).json()["result"]==series


def test_circuit_bounds_and_script_payload_are_rejected(env):
    a,b,guest=env
    cases=[
        circuit(voltage=0),circuit(voltage=50),
        circuit(resistors=[10]),circuit(resistors=[10]*5),
        circuit(resistors=[0,10]),circuit(resistors=[10,1001]),
        circuit(resistors=[10,"NaN"]),
        {**circuit(),"unknownCode":"eval('bad')"},
        {**circuit(),"mode":"short"},
    ]
    for case in cases:
        r=guest.post("/api/play/sandbox/preview",json=case)
        assert r.status_code==422,(case,r.text)


def test_private_created_exhibit_and_public_consent(env):
    alice,bob,guest=env
    p=create(alice)
    pid,eid=p["id"],p["exhibit_id"]
    assert p["visibility"]=="private"
    assert bob.get(f"/api/play/sandbox/{pid}").status_code==404
    assert guest.get(f"/api/exhibits/{eid}").status_code==404
    assert len(alice.get("/api/play/sandbox?scope=mine").json()["items"])==1
    backing=alice.get(f"/api/exhibits/{eid}").json()
    assert backing["title"].startswith("万物沙盒｜")
    assert backing["domain"]=="工程与发明"
    assert backing["visibility"]=="private"
    assert bob.put(f"/api/play/sandbox/{pid}",json=draft()).status_code==404
    assert publish(bob,pid).status_code==404
    assert publish(alice,pid).status_code==200
    result=guest.get(f"/api/play/sandbox/{pid}").json()
    assert result["public"] is True and result["creator"]=="Alice"
    assert guest.get(f"/api/exhibits/{eid}").status_code==200
    assert len(guest.get("/api/play/sandbox").json()["items"])==1
    assert guest.post(f"/api/play/sandbox/{pid}/simulate",
        json=circuit("parallel",3,[100,100])).json()["result"]["total_amperes"]==.06
    assert publish(alice,pid,"private").status_code==200
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==404
    assert guest.post(f"/api/play/sandbox/{pid}/simulate",json=circuit()).status_code==404


def test_legacy_private_change_revokes_independent_permission(env):
    alice,bob,guest=env
    p=create(alice);pid,eid=p["id"],p["exhibit_id"]
    assert publish(alice,pid).status_code==200
    assert alice.patch(f"/api/exhibits/{eid}",
        json=item(title="从外部编辑为私人",visibility="private")).status_code==200
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==404
    owner=alice.get(f"/api/play/sandbox/{pid}").json()
    assert owner["visibility"]=="private"
    assert alice.patch(f"/api/exhibits/{eid}",
        json=item(title="外部重新公开",visibility="public")).status_code==200
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==404
    assert publish(alice,pid).status_code==200
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==200


def test_history_timeline_marked_fiction_and_readonly_guest(env):
    alice,bob,guest=env
    p=create(alice,draft("timeline","跨越万年的时间剧场"))
    pid=p["id"]
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==404
    assert publish(alice,pid).status_code==200
    data=guest.get(f"/api/play/sandbox/{pid}").json()
    events=data["config"]["events"]
    assert [e["year"] for e in events]==[-65000000,1969,2200]
    assert events[-1]["nature"]=="原创虚构"
    assert events[0]["nature"]=="史料待核"
    assert events[1]["source_url"]=="https://www.nasa.gov"
    assert guest.post(f"/api/play/sandbox/{pid}/simulate",json=circuit()).status_code==409
    assert bob.put(f"/api/play/sandbox/{pid}",json=draft()).status_code==404
    assert guest.get(f"/api/exhibits/{p['exhibit_id']}").json()["domain"]=="历史与考古"


def test_history_validation_labels_order_bounds_and_https(env):
    alice,bob,guest=env
    base=timeline()
    invalid=[
       {"events":base["events"][:2]},
       {"events":base["events"]*4},
       {"events":[{**x,"year":0} if i==1 else x for i,x in enumerate(base["events"])]},
       {"events":base["events"][::-1]},
       {"events":[{**x,"nature":"未经标注"} if i==2 else x for i,x in enumerate(base["events"])]},
       {"events":[{**x,"source_url":"javascript:alert(1)"} if i==1 else x for i,x in enumerate(base["events"])]},
       {"events":[{**x,"source_url":"http://example.org"} if i==1 else x for i,x in enumerate(base["events"])]},
       {"events":[{**x,"source_url":"https://example.org"} if i==2 else x for i,x in enumerate(base["events"])]},
       {"events":[{**x,"year":-1000000000} if i==0 else x for i,x in enumerate(base["events"])]},
       {"events":[{**x,"script":"alert(1)"} if i==1 else x for i,x in enumerate(base["events"])]}
    ]
    for value in invalid:
        r=alice.post("/api/play/sandbox",json=draft("timeline",config=value))
        assert r.status_code==422,(value,r.text)


def test_updating_kind_and_deleting_does_not_modify_other_exhibits(env):
    alice,bob,guest=env
    unrelated=alice.post("/api/exhibits",json=item(title="先有的古董")).json()["id"]
    p=create(alice)
    pid,eid=p["id"],p["exhibit_id"]
    new=draft("timeline",title="新文明分镜")
    assert alice.put(f"/api/play/sandbox/{pid}",json=new).status_code==200
    d=alice.get(f"/api/play/sandbox/{pid}").json()
    assert d["kind"]=="timeline"
    assert d["title"]=="新文明分镜"
    assert alice.get(f"/api/exhibits/{eid}").json()["domain"]=="历史与考古"
    assert bob.delete(f"/api/play/sandbox/{pid}").status_code==404
    assert alice.delete(f"/api/play/sandbox/{pid}").status_code==200
    assert alice.get(f"/api/exhibits/{unrelated}").status_code==200
    assert alice.get(f"/api/exhibits/{eid}").status_code==404
    assert guest.get(f"/api/play/sandbox/{pid}").status_code==404


def test_project_limit_and_cascade_if_backing_deleted(env):
    alice,bob,guest=env
    for i in range(12):
        r=alice.post("/api/play/sandbox",json=draft(title=f"沙盒第{i+1}号"))
        assert r.status_code==201,(i,r.text)
    assert alice.post("/api/play/sandbox",json=draft()).status_code==429
    items=alice.get("/api/play/sandbox?scope=mine").json()["items"]
    assert len(items)==12
    first=items[0]
    assert publish(alice,first["id"]).status_code==200
    assert alice.delete(f"/api/exhibits/{first['exhibit_id']}").status_code==200
    assert guest.get("/api/play/sandbox").json()["items"]==[]
    assert alice.get(f"/api/play/sandbox/{first['id']}").status_code==404
    assert alice.post("/api/play/sandbox",json=draft()).status_code==201


def test_navigation_assets_and_both_old_studios_still_work(env):
    a,b,guest=env
    html=guest.get("/").text
    assert "WORLD 23" in html
    assert guest.get("/api/health").json()["version"]=="23.0"
    for file in ("sandbox.js","sandbox.css"):
        path="/static/"+file
        assert path in html and guest.get(path).status_code==200
    assert guest.get("/api/play/studio/config").status_code==200
    assert guest.get("/api/play/config").status_code==200
    assert guest.get("/api/lab/config").status_code==200
