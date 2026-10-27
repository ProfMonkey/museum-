"""V20 integration tests: real collection sources, private future letters and daily discovery."""
from datetime import datetime, timedelta, timezone
from test_multiuser import env, item
from test_fantasy_v16 import world, relic


def album(title="奇迹图鉴", style="星际档案"):
    return {"title":title,"description":"从自然到未来的跨界藏品","style":style}


def post_album(client, **kwargs):
    r=client.post("/api/lab/albums",json=album(**kwargs))
    assert r.status_code==201,r.text
    return r.json()["id"]


def insert(client, aid,kind,source_id):
    return client.post(f"/api/lab/albums/{aid}/entries",
                       json={"kind":kind,"source_id":source_id})


def visibility(client,aid,value):
    return client.patch(f"/api/lab/albums/{aid}/visibility",
                        json={"visibility":value})


def future(days):
    return (datetime.now(timezone.utc).date()+timedelta(days=days)).isoformat()


def capsule(title="给未来",days=100,body="这是今天留下的万物收藏感想，希望未来我依然好奇。"):
    return {"title":title,"body":body,"unlock_date":future(days)}


def test_config_empty_and_no_fabricated_artifacts(env):
    alice,bob,guest=env
    c=guest.get("/api/lab/config")
    assert c.status_code==200 and c.json()["max_albums"]==12
    assert len(c.json()["domains"])>25
    assert guest.get("/api/lab/albums").json()["items"]==[]
    assert guest.get("/api/lab/surprise").json()["item"] is None
    assert guest.get("/api/lab/albums?scope=mine").status_code==401
    assert guest.get("/api/lab/capsules").status_code==401
    assert guest.get("/api/lab/stamps").status_code==401
    assert guest.post("/api/lab/albums",json=album()).status_code==401


def test_albums_are_private_by_default_and_permissioned(env):
    alice,bob,guest=env
    aid=post_album(alice)
    assert bob.get(f"/api/lab/albums/{aid}").status_code==404
    assert guest.get(f"/api/lab/albums/{aid}").status_code==404
    assert guest.get("/api/lab/albums").json()["items"]==[]
    assert len(alice.get("/api/lab/albums?scope=mine").json()["items"])==1
    assert insert(bob,aid,"exhibit",1).status_code==404
    assert visibility(bob,aid,"public").status_code==404
    assert bob.delete(f"/api/lab/albums/{aid}").status_code==404
    assert alice.post("/api/lab/albums",json={"title":"  ","style":"星际档案"}).status_code==422
    assert alice.post("/api/lab/albums",json={"title":"有效标题","style":"非法风格"}).status_code==422


def test_public_gallery_only_after_private_source_removed(env):
    alice,bob,guest=env
    secret=alice.post("/api/exhibits",json=item(title="私人小宇宙",visibility="private")).json()["id"]
    public=alice.post("/api/exhibits",json=item(title="公开化石")).json()["id"]
    aid=post_album(alice)
    private_entry=insert(alice,aid,"exhibit",secret)
    assert private_entry.status_code==201,private_entry.text
    assert insert(alice,aid,"exhibit",public).status_code==201
    assert insert(alice,aid,"exhibit",public).status_code==409
    assert insert(bob,aid,"exhibit",secret).status_code==404
    assert visibility(alice,aid,"public").status_code==409
    eid=private_entry.json()["id"]
    assert alice.delete(f"/api/lab/albums/{aid}/entries/{eid}").status_code==200
    assert visibility(alice,aid,"public").status_code==200
    result=guest.get(f"/api/lab/albums/{aid}").json()
    assert result["is_owner"] is False
    assert [x["title"] for x in result["items"]]==["公开化石"]
    assert all(x["public"] for x in result["items"])
    assert visibility(alice,aid,"private").status_code==200
    assert guest.get(f"/api/lab/albums/{aid}").status_code==404


def test_revoked_exhibit_is_hidden_from_other_curators_and_public_album(env):
    alice,bob,guest=env
    eid=alice.post("/api/exhibits",json=item(title="昨日已公开的奇物")).json()["id"]
    aid=post_album(bob)
    assert insert(bob,aid,"exhibit",eid).status_code==201
    assert visibility(bob,aid,"public").status_code==200
    assert len(guest.get(f"/api/lab/albums/{aid}").json()["items"])==1
    private=item(title="昨日已公开的奇物",visibility="private")
    assert alice.patch(f"/api/exhibits/{eid}",json=private).status_code==200
    result=guest.get(f"/api/lab/albums/{aid}").json()
    assert result["items"]==[]
    assert bob.get(f"/api/lab/albums/{aid}").json()["items"]==[]
    assert guest.get("/api/lab/surprise?kind=exhibit").json()["item"] is None


def test_world_sources_remain_distinct_from_reality(env):
    alice,bob,guest=env
    secret=alice.post("/api/fantasy/worlds",json=world()).json()["id"]
    aid=post_album(alice)
    assert insert(bob,aid,"world",secret).status_code==404
    assert insert(alice,aid,"world",secret).status_code==201
    assert visibility(alice,aid,"public").status_code==409
    assert alice.patch(f"/api/fantasy/worlds/{secret}/visibility",
                       json={"visibility":"public"}).status_code==200
    assert visibility(alice,aid,"public").status_code==200
    entry=guest.get(f"/api/lab/albums/{aid}").json()["items"][0]
    assert entry["fictional"] is True and entry["provenance"]=="原创虚构世界"
    assert guest.get("/api/lab/surprise?kind=world").json()["item"]["fictional"] is True
    alice.patch(f"/api/fantasy/worlds/{secret}/visibility",
                json={"visibility":"private"})
    assert guest.get(f"/api/lab/albums/{aid}").json()["items"]==[]


def test_add_private_item_to_public_album_fails(env):
    alice,bob,guest=env
    aid=post_album(alice)
    assert visibility(alice,aid,"public").status_code==200
    secret=alice.post("/api/exhibits",json=item(visibility="private")).json()["id"]
    assert insert(alice,aid,"exhibit",secret).status_code==409
    assert insert(alice,aid,"world",987654321).status_code==404
    assert insert(guest,aid,"exhibit",secret).status_code==401


def test_time_capsule_never_exposes_sealed_message(env):
    alice,bob,guest=env
    c=alice.post("/api/lab/capsules",json=capsule())
    assert c.status_code==201,c.text
    cid=c.json()["id"]
    for getter in (alice.get("/api/lab/capsules"),
                   alice.get(f"/api/lab/capsules/{cid}")):
        assert getter.status_code==200
        row=getter.json()["items"][0] if "items" in getter.json() else getter.json()
        assert row["sealed"] is True and row["body"] is None
    assert bob.get(f"/api/lab/capsules/{cid}").status_code==404
    assert guest.get(f"/api/lab/capsules/{cid}").status_code==401
    assert alice.post("/api/lab/capsules",json=capsule(days=0)).status_code==422
    assert alice.post("/api/lab/capsules",json=capsule(days=4000)).status_code==422
    assert alice.post("/api/lab/capsules",json=capsule(body="太短")).status_code==422
    assert bob.delete(f"/api/lab/capsules/{cid}").status_code==404
    assert alice.delete(f"/api/lab/capsules/{cid}").status_code==200
    assert alice.get("/api/lab/capsules").json()["items"]==[]


def test_daily_surprise_is_deterministic_and_source_based(env):
    alice,bob,guest=env
    eid=alice.post("/api/exhibits",json=item(title="一块真实投稿的岩石",
        category="岩石与地层",domain="地球与地质")).json()["id"]
    first=guest.get("/api/lab/surprise?domain=地球与地质")
    again=guest.get("/api/lab/surprise?domain=地球与地质")
    assert first.status_code==200 and first.json()==again.json()
    assert first.json()["item"]["id"]==eid
    assert first.json()["item"]["provenance"]=="社区投稿／未独立核验"
    assert guest.get("/api/lab/surprise?domain=不存在").status_code==422
    assert guest.get("/api/lab/surprise?kind=alien").status_code==422
    assert guest.get("/api/lab/surprise?kind=world").json()["item"] is None


def test_passport_one_real_discovery_per_day_and_revoked_hidden(env):
    alice,bob,guest=env
    eid=alice.post("/api/exhibits",json=item()).json()["id"]
    assert guest.post("/api/lab/stamps").status_code==401
    collected=bob.post("/api/lab/stamps")
    assert collected.status_code==201,collected.text
    assert collected.json()["item"]["id"]==eid
    assert bob.post("/api/lab/stamps").status_code==409
    assert len(bob.get("/api/lab/stamps").json()["items"])==1
    assert alice.get("/api/lab/stamps").json()["items"]==[]
    assert alice.patch(f"/api/exhibits/{eid}",
      json=item(visibility="private")).status_code==200
    stamp=bob.get("/api/lab/stamps").json()["items"][0]
    assert stamp["hidden"] is True and stamp["item"] is None
    assert guest.get("/api/lab/stamps").status_code==401


def test_ownership_and_source_deletion_cascade(env):
    alice,bob,guest=env
    eid=alice.post("/api/exhibits",json=item()).json()["id"]
    aid=post_album(bob)
    assert insert(bob,aid,"exhibit",eid).status_code==201
    alice.delete(f"/api/exhibits/{eid}")
    assert bob.get(f"/api/lab/albums/{aid}").json()["items"]==[]
    assert bob.delete(f"/api/lab/albums/{aid}").status_code==200
    assert bob.get(f"/api/lab/albums/{aid}").status_code==404


def test_static_assets_and_navigation_are_exposed(env):
    a,b,guest=env
    html=guest.get("/").text
    for asset in ["/static/everything-lab.css","/static/everything-lab.js"]:
        assert asset in html
        assert guest.get(asset).status_code==200
    assert 'data-view="lab"' in html
    assert "WONDER ATLAS · WORLD " in html  # release marker is version-agnostic
