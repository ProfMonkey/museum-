"""V25 multi-stage destiny relay, privacy, unbiased picks and revocable sharing."""
import re

import pytest
import wheel_api
from test_multiuser import env, item


def make_wheel(client,title,topic="food",choices=("米线","菌子火锅","牛排")):
    create=client.post("/api/wheels",json={
        "title":title,"topic":topic,"theme":"amber","no_repeat":True})
    assert create.status_code==201,create.text
    wid=create.json()["id"]
    for label in choices:
        res=client.post(f"/api/wheels/{wid}/items",
            json={"kind":"manual","label":label})
        assert res.status_code==201,res.text
    return wid


def new_card(client,ids,title="今日命运接力"):
    r=client.post("/api/adventures",json={"title":title,"wheel_ids":ids})
    assert r.status_code==201,r.text
    return r.json()["id"]


def advance(client,card_id):
    return client.post(f"/api/adventures/{card_id}/advance")


def publish(client,card_id,visibility="public"):
    return client.patch(f"/api/adventures/{card_id}/visibility",
        json={"visibility":visibility})


def test_config_and_true_empty_start(env):
    a,b,guest=env
    cfg=guest.get("/api/adventures/config")
    assert cfg.status_code==200
    assert cfg.json()["stages_min"]==2 and cfg.json()["stages_max"]==5
    assert cfg.json()["max_cards"]==30
    assert guest.get("/api/adventures").status_code==401
    assert a.get("/api/adventures").json()["items"]==[]
    assert guest.post("/api/adventures",json={
        "title":"今日奇遇","wheel_ids":[1,2]}).status_code==401
    assert guest.get("/api/adventures/share/"+"a"*36).status_code==404


def test_create_2_to_5_stages_and_private_owner_detail(env):
    alice,bob,guest=env
    names=[("今晚吃什么","food"),("去哪里走走","travel"),
           ("做什么事情","activity"),("探索什么","custom"),("今天看什么","watch")]
    ids=[make_wheel(alice,x,t) for x,t in names]
    cid=new_card(alice,ids,title="五重命运")
    data=alice.get(f"/api/adventures/{cid}").json()
    assert data["stage_count"]==5 and data["completed_count"]==0
    assert data["finished"] is False
    assert data["visibility"]=="private" and data["share_path"] is None
    assert [x["topic"] for x in data["stages"]]==[x[1] for x in names]
    assert all(not x["completed"] and x["label"] is None for x in data["stages"])
    assert len(alice.get("/api/adventures").json()["items"])==1
    assert bob.get("/api/adventures").json()["items"]==[]
    assert bob.get(f"/api/adventures/{cid}").status_code==404
    assert guest.get(f"/api/adventures/{cid}").status_code==401


def test_creation_requires_owned_distinct_populated_wheels(env):
    alice,bob,guest=env
    x=make_wheel(alice,"早餐","food")
    y=make_wheel(bob,"另一个人的早餐","food")
    empty=alice.post("/api/wheels",json={
        "title":"空转盘","topic":"custom","theme":"rose","no_repeat":True}).json()["id"]
    bad=[[x,x],[x,y],[x,empty],[x],[x]*6,[x,99999]]
    for ids in bad:
        r=alice.post("/api/adventures",json={"title":"今日奇遇","wheel_ids":ids})
        assert r.status_code in (404,409,422),(ids,r.text)
    assert alice.get("/api/adventures").json()["items"]==[]


def test_stage_by_stage_draw_and_shared_wheel_history(env,monkeypatch):
    a,b,guest=env
    first=make_wheel(a,"早餐","food")
    second=make_wheel(a,"去玩哪里","travel",("博物馆","公园"))
    cid=new_card(a,[first,second])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    r1=advance(a,cid)
    assert r1.status_code==200,r1.text
    d=r1.json()
    assert d["stage"]["label"]=="米线"
    assert d["stage_number"]==1 and d["chance_denominator"]==3
    assert d["card"]["completed_count"]==1
    assert d["card"]["stages"][1]["completed"] is False
    assert a.get(f"/api/wheels/{first}").json()["history"][0]["label"]=="米线"
    r2=advance(a,cid)
    assert r2.status_code==200 and r2.json()["stage_number"]==2
    assert r2.json()["stage"]["label"]=="博物馆"
    assert r2.json()["card"]["finished"] is True
    assert advance(a,cid).status_code==409
    assert a.get(f"/api/wheels/{second}").json()["history"][0]["label"]=="博物馆"
    # The next ordinary V24 draw from that wheel still honors no-repeat.
    again=a.post(f"/api/wheels/{second}/spin")
    assert again.status_code==200 and again.json()["winner"]["label"]=="公园"


def test_unfinished_cards_cannot_share_and_public_cards_become_immutable(env):
    a,b,guest=env
    x=make_wheel(a,"食物")
    y=make_wheel(a,"运动","activity")
    cid=new_card(a,[x,y])
    assert publish(a,cid).status_code==409
    assert advance(a,cid).status_code==200
    assert publish(a,cid).status_code==409
    assert advance(a,cid).status_code==200
    p=publish(a,cid)
    assert p.status_code==200,p.text
    path=p.json()["share_path"]
    assert path.startswith("/adventure/")
    pub=guest.get("/api/adventures/share/"+path.rsplit("/",1)[-1])
    assert pub.status_code==200 and pub.json()["finished"]
    assert pub.json()["stage_count"]==2
    assert pub.json()["title"]=="今日命运接力"
    assert "owner_id" not in pub.text and "wheel_id" not in pub.text
    assert "chosen_item_id" not in pub.text
    assert advance(a,cid).status_code==409
    assert publish(a,cid).json()["share_path"]==path


def test_unpublish_invalidates_old_links_new_publish_rotates(env):
    a,b,guest=env
    cid=new_card(a,[make_wheel(a,"早餐"),make_wheel(a,"去哪儿","travel")])
    advance(a,cid);advance(a,cid)
    path=publish(a,cid).json()["share_path"]
    assert guest.get(path).status_code==200
    assert guest.get("/api/adventures/share/"+path.split("/")[-1]).status_code==200
    assert publish(b,cid,"private").status_code==404
    off=publish(a,cid,"private")
    assert off.status_code==200 and off.json()["share_path"] is None
    assert guest.get(path).status_code==404
    assert guest.get("/api/adventures/share/"+path.split("/")[-1]).status_code==404
    later=publish(a,cid).json()["share_path"]
    assert later!=path
    assert guest.get(later).status_code==200
    assert guest.get(path).status_code==404


def test_withdrawn_museum_source_redacted_on_private_and_public_cards(env,monkeypatch):
    alice,bob,guest=env
    exhibit=bob.post("/api/exhibits",json=item(title="只在公开时可见的牛排藏品")).json()["id"]
    food=make_wheel(alice,"今天吃","food",("米线",))
    linked=alice.post(f"/api/wheels/{food}/items",json={
        "kind":"exhibit","exhibit_id":exhibit})
    assert linked.status_code==201,linked.text
    travel=make_wheel(alice,"去哪儿","travel")
    cid=new_card(alice,[food,travel])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    # Exclude the first manual choice by drawing it in V24 first.
    assert alice.post(f"/api/wheels/{food}/spin").status_code==200
    r=advance(alice,cid)
    assert r.status_code==200 and r.json()["stage"]["label"]=="只在公开时可见的牛排藏品"
    assert r.json()["stage"]["exhibit_id"]==exhibit
    advance(alice,cid)
    path=publish(alice,cid).json()["share_path"]
    assert "只在公开时可见的牛排藏品" in guest.get(path).text
    changed=bob.patch(f"/api/exhibits/{exhibit}",json=item(
        title="只在公开时可见的牛排藏品",visibility="private"))
    assert changed.status_code==200
    owner=alice.get(f"/api/adventures/{cid}").json()
    assert owner["stages"][0]["label"]=="已撤回的馆藏"
    assert owner["stages"][0]["exhibit_id"] is None
    public=guest.get(path)
    assert public.status_code==200
    assert "只在公开时可见的牛排藏品" not in public.text
    assert "已撤回的馆藏" in public.text
    js=guest.get("/api/adventures/share/"+path.split("/")[-1]).json()
    assert "只在公开时可见的牛排藏品" not in str(js)


def test_deleted_source_foreign_key_null_remains_redacted(env,monkeypatch):
    alice,bob,guest=env
    eid=bob.post("/api/exhibits",json=item(title="此展品稍后永久删除")).json()["id"]
    a=make_wheel(alice,"吃什么",choices=("米线",))
    assert alice.post(f"/api/wheels/{a}/items",
        json={"kind":"exhibit","exhibit_id":eid}).status_code==201
    b=make_wheel(alice,"去哪儿","travel")
    cid=new_card(alice,[a,b])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:0)
    assert alice.post(f"/api/wheels/{a}/spin").status_code==200
    advance(alice,cid);advance(alice,cid)
    path=publish(alice,cid).json()["share_path"]
    assert bob.delete(f"/api/exhibits/{eid}").status_code==200
    assert guest.get(path).status_code==200
    assert "此展品稍后永久删除" not in guest.get(path).text
    assert alice.get(f"/api/adventures/{cid}").json()["stages"][0]["available"] is False


def test_deleting_wheel_during_unfinished_route_fails_without_fake_completion(env):
    a,b,guest=env
    first=make_wheel(a,"吃点什么")
    second=make_wheel(a,"去哪儿","travel")
    cid=new_card(a,[first,second])
    assert advance(a,cid).status_code==200
    assert a.delete(f"/api/wheels/{second}").status_code==200
    result=advance(a,cid)
    assert result.status_code==409
    assert a.get(f"/api/adventures/{cid}").json()["completed_count"]==1
    assert a.get(f"/api/adventures/{cid}").json()["finished"] is False


def test_mutations_are_owner_only_and_guest_read_share_only(env):
    a,b,guest=env
    cid=new_card(a,[make_wheel(a,"吃点什么"),make_wheel(a,"出去玩","travel")])
    assert b.post(f"/api/adventures/{cid}/advance").status_code==404
    assert b.patch(f"/api/adventures/{cid}/visibility",
        json={"visibility":"public"}).status_code==404
    assert b.delete(f"/api/adventures/{cid}").status_code==404
    assert guest.delete(f"/api/adventures/{cid}").status_code==401
    assert guest.get(f"/api/adventures/{cid}").status_code==401
    assert a.get(f"/api/adventures/{cid}").status_code==200


def test_html_share_card_escapes_user_authored_markup(env):
    a,b,guest=env
    m=make_wheel(a,"甜品选择",choices=("<img src=x onerror=alert(1)>","米线"))
    n=make_wheel(a,"今天学习","activity")
    cid=new_card(a,[m,n],title="<script>alert(1)</script>好奇旅行")
    advance(a,cid);advance(a,cid)
    path=publish(a,cid).json()["share_path"]
    r=guest.get(path)
    assert r.status_code==200
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text
    assert "<img src=x onerror=alert(1)>" not in r.text
    assert "&lt;img src=x" in r.text
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"]=="no-store"


def test_limit_thirty_cards_independent_of_wheel_limit(env):
    alice,bob,guest=env
    x=make_wheel(alice,"吃什么")
    y=make_wheel(alice,"去哪里","travel")
    for i in range(30):
        r=alice.post("/api/adventures",
           json={"title":f"第{i+1}张奇遇","wheel_ids":[x,y]})
        assert r.status_code==201,(i,r.text)
    assert len(alice.get("/api/adventures").json()["items"])==30
    assert alice.post("/api/adventures",
       json={"title":"第三十一张","wheel_ids":[x,y]}).status_code==429
    target=alice.get("/api/adventures").json()["items"][0]["id"]
    assert alice.delete(f"/api/adventures/{target}").status_code==200
    assert alice.post("/api/adventures",
       json={"title":"替代新卡","wheel_ids":[x,y]}).status_code==201
    assert bob.get("/api/adventures").json()["items"]==[]


def test_real_wheel_source_revalidated_each_stage(env):
    alice,bob,guest=env
    source=bob.post("/api/exhibits",json=item(title="一件真实可见的甜品")).json()["id"]
    food=make_wheel(alice,"食物",choices=("米线",))
    assert alice.post(f"/api/wheels/{food}/items",
      json={"kind":"exhibit","exhibit_id":source}).status_code==201
    other=make_wheel(alice,"出去玩","travel")
    cid=new_card(alice,[other,food])
    assert advance(alice,cid).status_code==200
    assert bob.patch(f"/api/exhibits/{source}",json=item(
      title="一件真实可见的甜品",visibility="private")).status_code==200
    assert advance(alice,cid).status_code==409
    assert alice.get(f"/api/adventures/{cid}").json()["completed_count"]==1


def test_release_assets_and_original_wheel_still_works(env):
    a,b,guest=env
    html=guest.get("/").text
    assert "WORLD 25" in html
    assert guest.get("/api/health").json()["version"]=="25.0"
    assert 'data-view="adventure"' in html
    for asset in ("adventure.css","adventure.js"):
        path="/static/"+asset
        assert path in html and guest.get(path).status_code==200
    assert guest.get("/api/wheels/config").status_code==200
    assert guest.post("/api/wheels/preview",
       json={"options":["米线","火锅"]}).status_code==200
    assert guest.get("/api/play/studio/config").status_code==200
