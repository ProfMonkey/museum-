"""V39: eight-choice decision station and real-source privacy, local only."""
from test_multiuser import env, item
from test_wheel_v24 import wheel, museum, create, manual, source


def test_v39_eight_topics_visible_without_login(env):
    alice,bob,guest=env
    r=guest.get("/api/wheels/config")
    assert r.status_code==200
    topics={x["key"] for x in r.json()["topics"]}
    assert topics=={"food","travel","watch","read","study","exercise","activity","custom"}
    for kind in topics:
        wid=create(alice,topic=kind,title="选择"+kind)
        assert alice.get(f"/api/wheels/{wid}").json()["topic"]==kind


def test_scene_wheels_do_not_mix_or_write_guest_choices_to_account(env):
    alice,bob,guest=env
    read_id=create(alice,topic="read",title="读什么")
    exercise_id=create(alice,topic="exercise",title="怎么运动")
    assert manual(alice,read_id,"一本故事书").status_code==201
    assert manual(alice,exercise_id,"跑步五公里").status_code==201
    assert [x["label"] for x in alice.get(f"/api/wheels/{read_id}").json()["items"]]==["一本故事书"]
    assert [x["label"] for x in alice.get(f"/api/wheels/{exercise_id}").json()["items"]]==["跑步五公里"]
    draw=guest.post("/api/wheels/preview",json={"options":["读小说","看电影"]})
    assert draw.status_code==200
    assert len(alice.get("/api/wheels").json()["items"])==2


def test_guest_original_resolver_never_exposes_private_or_removed_exhibits(env):
    alice,bob,guest=env
    pub=museum(alice,"公开的昆明米线")
    hidden=museum(bob,"只在私密世界里的剧本",visibility="private")
    res=guest.get(f"/api/wheels/resolve?ids={pub},{hidden}")
    assert res.status_code==200,res.text
    assert res.json()["items"]==[{"id":pub,"title":"公开的昆明米线"}]
    assert "只在私密世界" not in res.text
    for ids in ("-1","abc",",".join(["1"]*25),str(10**30)):
        assert guest.get("/api/wheels/resolve",params={"ids":ids}).status_code==422
    changed=alice.patch(f"/api/exhibits/{pub}",json=item(title="公开的昆明米线",visibility="private"))
    assert changed.status_code==200,changed.text
    assert guest.get(f"/api/wheels/resolve?ids={pub}").json()["items"]==[]


def test_wheel_regular_sources_still_guard_privacy_and_track_live_titles(env):
    alice,bob,guest=env
    public=museum(bob,"一件原创漫画",category="生活发现",domain="日常生活与奇物")
    hidden=museum(bob,"不该进入抽取的秘密电影",visibility="private")
    wid=create(alice,topic="watch",title="周末看什么")
    assert source(alice,wid,public).status_code==201
    assert source(alice,wid,hidden).status_code==404
    assert guest.get("/api/wheels/sources?q=秘密电影").json()["items"]==[]
    assert alice.get(f"/api/wheels/{wid}").json()["items"][0]["exhibit_id"]==public


def test_v39_ui_assets_and_every_genre_action(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="39.0"
    html=guest.get("/").text
    assert "WORLD 39" in html
    assert 'data-view="wheels"><span>🎡</span> 万物转盘' in html
    app=guest.get("/static/app.js").text
    wheel=guest.get("/static/wheel.js").text
    fmap=guest.get("/static/feature-map.js").text
    assert "suggestWheelTopic" in app and "wheelActions" in app
    for label in ("读什么","学什么","怎么运动","看什么","去哪玩"):
        assert label in app and label in wheel
    assert "setGuestTopic" in wheel
    assert "wonder-wheel-v39" in wheel
    assert "W.pending?.auto" in wheel
    assert "verifyGuestSources" in wheel
    assert "featureRecent" in fmap
