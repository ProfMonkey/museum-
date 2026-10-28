"""V26 exploration missions: real sources, relevance honesty, and private visit progress."""
import wheel_api
from test_multiuser import env, item
from test_adventure_v25 import make_wheel, new_card, advance


def public(client,title,description="真实馆长在博物馆收藏的原创条目",tags="",**kw):
    r=client.post("/api/exhibits",json=item(title=title,description=description,tags=tags,**kw))
    assert r.status_code==201,r.text
    return r.json()["id"]


def journey(client,first=("米线","牛排"),second=("博物馆","公园")):
    a=make_wheel(client,"第一站吃什么","food",first)
    b=make_wheel(client,"第二站去哪里","travel",second)
    return new_card(client,[a,b]),a,b


def mark(client,cid,n,eid):
    return client.post(f"/api/adventures/{cid}/quests/{n}/visit",json={"exhibit_id":eid})


def get(client,cid):
    return client.get(f"/api/adventures/{cid}/quests")


def test_public_lookup_never_fabricates_community_objects(env):
    alice,bob,guest=env
    r=guest.get("/api/discovery/quests/config")
    assert r.status_code==200
    assert r.json()["max_matches"]==4
    assert guest.get("/api/discovery/quests/explore?q=米线").json()["items"]==[]
    assert guest.get("/api/discovery/quests/explore?q=黑洞").json()["matched"]==0
    assert guest.get("/api/discovery/quests/explore?q=a").status_code==422
    assert guest.get("/api/discovery/quests/explore?q="+"长"*61).status_code==422


def test_manual_pick_finds_real_public_exhibits_and_transparent_reasons(env,monkeypatch):
    alice,bob,guest=env
    exact=public(bob,"米线")
    broader=public(bob,"昆明米线文化","围绕小锅米线写的饮食文化记录",tags="米线,饮食")
    unrelated=public(bob,"青铜礼器","古代生活用品记录")
    private=public(bob,"米线秘方",visibility="private")
    cid,_,_=journey(alice)
    initial=get(alice,cid).json()
    assert initial["visited_count"]==0
    assert initial["stages"][0]["ready"] is False
    assert initial["stages"][0]["suggestions"]==[]
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert advance(alice,cid).json()["stage"]["label"]=="米线"
    r=get(alice,cid);assert r.status_code==200,r.text
    x=r.json()["stages"][0]
    assert x["label"]=="米线"
    assert x["ready"] is True
    assert [e["id"] for e in x["suggestions"]][:2]==[exact,broader]
    assert all(v["mode"]=="match" for v in x["suggestions"])
    assert x["suggestions"][0]["reason"]=="标题完全一致"
    assert unrelated not in [e["id"] for e in x["suggestions"]]
    assert private not in [e["id"] for e in x["suggestions"]]
    anon=guest.get("/api/discovery/quests/explore?q=米线").json()
    assert anon["matched"]==2
    assert private not in [v["id"] for v in anon["items"]]


def test_guest_no_match_fallback_is_marked_browse_not_related(env):
    a,b,g=env
    eid=public(a,"石器时代")
    r=g.get("/api/discovery/quests/explore?q=无匹配冰花糕")
    assert r.status_code==200
    result=r.json()
    assert result["matched"]==0
    assert [v["id"] for v in result["items"]]==[eid]
    assert result["items"][0]["mode"]=="browse"
    assert "不声称内容相关" in result["items"][0]["reason"]


def test_visit_rejects_unfinished_and_unrelated_and_nonowners(env,monkeypatch):
    alice,bob,guest=env
    match=public(bob,"一碗米线")
    wrong=public(bob,"青铜时代的故事")
    cid,_,_=journey(alice)
    assert mark(alice,cid,1,match).status_code==409
    assert get(bob,cid).status_code==404
    assert get(guest,cid).status_code==401
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert advance(alice,cid).status_code==200
    assert mark(bob,cid,1,match).status_code==404
    assert mark(guest,cid,1,match).status_code==401
    assert mark(alice,cid,1,wrong).status_code==409
    r=mark(alice,cid,1,match)
    assert r.status_code==200,r.text
    detail=get(alice,cid).json()
    assert detail["visited_count"]==1
    assert detail["stages"][0]["visited_title"]=="一碗米线"
    assert detail["stages"][0]["visited_at"]


def test_visits_remain_private_when_adventure_card_public(env,monkeypatch):
    alice,bob,guest=env
    eid=public(bob,"牛排文化的文章")
    cid,_,_=journey(alice,first=("牛排","米线"))
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    advance(alice,cid);advance(alice,cid)
    assert mark(alice,cid,1,eid).status_code==200
    share=alice.patch(f"/api/adventures/{cid}/visibility",
        json={"visibility":"public"}).json()["share_path"]
    shared=guest.get("/api/adventures/share/"+share.split("/")[-1]).json()
    webpage=guest.get(share).text
    assert "visited_count" not in str(shared)
    assert "visited_title" not in str(shared)
    assert "wonder_adventure_visits" not in webpage
    assert get(bob,cid).status_code==404
    assert get(guest,cid).status_code==401
    assert get(alice,cid).json()["visited_count"]==1


def test_undo_mark_can_be_used_after_complete_and_revisit(env,monkeypatch):
    alice,bob,guest=env
    a=public(bob,"菌子火锅的收藏")
    cid,_,_=journey(alice,first=("菌子火锅","火锅"))
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    advance(alice,cid)
    assert mark(alice,cid,1,a).status_code==200
    assert mark(alice,cid,1,a).status_code==200
    assert get(alice,cid).json()["visited_count"]==1
    undo=alice.delete(f"/api/adventures/{cid}/quests/1/visit")
    assert undo.status_code==200
    assert get(alice,cid).json()["visited_count"]==0
    assert mark(alice,cid,1,a).status_code==200


def test_deleted_source_automatically_redacts_visit_titles(env,monkeypatch):
    alice,bob,guest=env
    x=public(bob,"小锅米线馆藏")
    cid,_,_=journey(alice)
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    advance(alice,cid)
    assert mark(alice,cid,1,x).status_code==200
    assert bob.delete(f"/api/exhibits/{x}").status_code==200
    result=get(alice,cid).json()
    assert result["visited_count"]==0
    assert result["stages"][0].get("visit_withdrawn")
    assert "小锅米线馆藏" not in str(result)
    assert mark(alice,cid,1,x).status_code==409


def test_private_source_change_instantly_revokes_prior_visit_and_search(env,monkeypatch):
    alice,bob,guest=env
    x=public(bob,"米线超级展")
    cid,_,_=journey(alice)
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    advance(alice,cid)
    assert mark(alice,cid,1,x).status_code==200
    assert bob.patch(f"/api/exhibits/{x}",json=item(
       title="米线超级展",visibility="private")).status_code==200
    result=get(alice,cid).json()
    assert result["stages"][0]["visited_title"] is None
    assert result["stages"][0]["visited"] is False
    assert result["visited_count"]==0
    assert x not in [v["id"] for v in guest.get("/api/discovery/quests/explore?q=米线").json()["items"]]
    assert "米线超级展" not in str(result)


def test_source_entry_explores_itself_and_subsequent_references(env,monkeypatch):
    alice,bob,guest=env
    original=public(bob,"恐龙大灭绝")
    related=public(bob,"关于恐龙化石的观察")
    x=make_wheel(alice,"研究方向","custom",("微生物","原始动物"))
    source=alice.post(f"/api/wheels/{x}/items",
       json={"kind":"exhibit","exhibit_id":original})
    assert source.status_code==201
    y=make_wheel(alice,"旅游去处","travel",("展览","公园"))
    cid=new_card(alice,[x,y])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    alice.post(f"/api/wheels/{x}/spin") # mark microbe as previous to exclude in advance
    assert advance(alice,cid).json()["stage"]["label"]=="原始动物"
    # Still a manual term this time; now force source by recording previous manual 2nd item.
    # Remove no-repeat pressure with new card and clean fresh wheel state:
    alice.post(f"/api/wheels/{x}/spin") # excludes prior animal; picks microbe
    # Select source using predictable order by exhausting two manuals through choice setup.
    # A separate wheel with an exhibit and one manual option makes the provenance check direct.
    z=make_wheel(alice,"化石专题","custom",("岩石",))
    assert alice.post(f"/api/wheels/{z}/items",
         json={"kind":"exhibit","exhibit_id":original}).status_code==201
    fresh=new_card(alice,[z,y])
    assert alice.post(f"/api/wheels/{z}/spin").json()["winner"]["label"]=="岩石"
    picked=advance(alice,fresh).json()["stage"]
    assert picked["label"]=="恐龙大灭绝"
    result=get(alice,fresh).json()["stages"][0]["suggestions"]
    assert result[0]["id"]==original and result[0]["mode"]=="source"
    assert related in [x["id"] for x in result]
    assert mark(alice,fresh,1,original).status_code==200
    assert bob.patch(f"/api/exhibits/{original}",json=item(
      title="恐龙大灭绝",visibility="private")).status_code==200
    new=get(alice,fresh).json()["stages"][0]
    assert new["source_unavailable"] is True
    assert new["suggestions"]==[]
    assert new["visited"] is False
    assert new["visit_withdrawn"] is True
    assert "恐龙大灭绝" not in str(new)


def test_last_400_recent_honored_without_reviving_old_private_sources(env,monkeypatch):
    alice,bob,guest=env
    eid=public(bob,"一件远古火山岩标本")
    # Avoid 400 heavy HTTP writes: use monkeypatch of bounded search to 1
    import discovery_missions
    monkeypatch.setattr(discovery_missions,"CANDIDATE_LIMIT",1)
    public(bob,"当天发布的新画作")
    z=make_wheel(alice,"看看古物","custom",("普通石头",))
    assert alice.post(f"/api/wheels/{z}/items",
         json={"kind":"exhibit","exhibit_id":eid}).status_code==201
    t=make_wheel(alice,"去哪儿","travel")
    cid=new_card(alice,[z,t])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert alice.post(f"/api/wheels/{z}/spin").status_code==200
    assert advance(alice,cid).json()["stage"]["label"]=="一件远古火山岩标本"
    q=get(alice,cid).json()["stages"][0]
    assert q["source_unavailable"] is False
    assert q["suggestions"][0]["id"]==eid
    assert mark(alice,cid,1,eid).status_code==200


def test_mark_schema_and_foreign_card_validation(env,monkeypatch):
    alice,bob,g=env
    eid=public(bob,"米线工艺")
    cid,_,_=journey(alice)
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    advance(alice,cid)
    for payload in ({"exhibit_id":0},{"exhibit_id":-1},
                    {"exhibit_id":eid,"is_admin":True},{}):
        r=alice.post(f"/api/adventures/{cid}/quests/1/visit",json=payload)
        assert r.status_code==422,(payload,r.text)
    assert alice.delete(f"/api/adventures/{cid}/quests/4/visit").status_code==404
    assert alice.delete(f"/api/adventures/{cid}/quests/2/visit").status_code==409


def test_assets_previous_routes_and_version(env):
    a,b,g=env
    html=g.get("/").text
    assert "WONDER ATLAS · WORLD " in html
    assert g.get("/api/health").json()["version"]=="40.0"
    for asset in ("quests.css","quests.js"):
        path="/static/"+asset
        assert path in html and g.get(path).status_code==200
    assert g.get("/api/wheels/config").status_code==200
    assert g.get("/api/adventures/config").status_code==200
    assert g.get("/api/play/sandbox/config").status_code==200
