"""V31 real HTTP tests: source-linked logs, no invented updates, watches and revocation."""
from datetime import datetime, timezone, timedelta
import sys

from test_multiuser import env, item


def create(client, title, **options):
    response=client.post("/api/exhibits",json=item(title=title,**options))
    assert response.status_code==201,response.text
    return response.json()["id"]

def payload(**options):
    d={"kind":"observation","headline":"观察到新的发展",
       "note":"馆长亲自观察到一个新的变化，需要持续收集证据。",
       "observed_on":"2026-10-20","source_url":"https://example.org/original/1"}
    d.update(options)
    return d

def record(client,eid,**options):
    return client.post(f"/api/living/exhibits/{eid}/entries",json=payload(**options))

def detail(client,eid):
    return client.get(f"/api/living/exhibits/{eid}")

def feed(client):
    return client.get("/api/living/feed").json()["items"]

def watches(client):
    return client.get("/api/living/watchlist")


def test_guest_public_is_real_and_no_fabricated_initial_updates(env):
    alice,bob,visitor=env
    x=create(alice,"公共科技年轮")
    assert feed(visitor)==[]
    assert visitor.get("/api/living/pulse").json()["recorded_changes_30d"]==0
    d=detail(visitor,x)
    assert d.status_code==200,d.text
    assert d.json()["entries"]==[] and d.json()["is_owner"] is False
    assert watches(visitor).status_code==401
    assert visitor.post(f"/api/living/exhibits/{x}/watch").status_code==401
    assert visitor.post(f"/api/living/exhibits/{x}/entries",json=payload()).status_code==401


def test_only_owner_records_and_source_label_is_honest(env):
    alice,bob,visitor=env
    x=create(alice,"公开火星探测器",domain="天文与航天")
    assert record(bob,x).status_code==404
    assert record(alice,999999).status_code==404
    r=record(alice,x,kind="discovery")
    assert r.status_code==201,r.text
    stored=r.json()["entry"]
    assert stored["source_url"]=="https://example.org/original/1"
    assert stored["source_label"]=="馆长提供来源链接（未经平台核验）"
    assert len(feed(visitor))==1
    assert feed(visitor)[0]["exhibit"]["title"]=="公开火星探测器"
    assert feed(visitor)[0]["entry"]["headline"]==stored["headline"]
    assert detail(bob,x).json()["entries"][0]["source_label"].endswith("未经平台核验）")
    no_source=record(alice,x,kind="correction",headline="修正一条旧认识",source_url="")
    assert no_source.status_code==201
    assert "自述" in no_source.json()["entry"]["source_label"]
    assert len(detail(visitor,x).json()["entries"])==2


def test_http_only_sources_and_future_date_rejected(env):
    alice,bob,visitor=env
    x=create(alice,"变化的城市")
    for url in ("javascript:alert(1)","file:///etc/passwd",
                "https://user:password@example.org/secret","data:text/plain,hello"):
        assert record(alice,x,source_url=url).status_code==422
    assert record(alice,x,observed_on="2999-01-01").status_code==422
    assert record(alice,x,headline=" ",source_url="").status_code==422
    assert record(alice,x,note="太短").status_code==422
    assert len(feed(visitor))==0


def test_watch_starts_at_latest_then_counts_only_new_entries(env):
    alice,bob,visitor=env
    x=create(alice,"无人机的演化史")
    record(alice,x,headline="第一次公开观察")
    r=bob.post(f"/api/living/exhibits/{x}/watch")
    assert r.status_code==200,r.text
    assert "以后" in r.json()["notice"]
    assert watches(bob).json()["items"][0]["unread"]==0
    assert bob.post(f"/api/living/exhibits/{x}/watch").status_code==200
    record(alice,x,headline="第二次公开观察")
    record(alice,x,headline="第三次公开观察")
    assert watches(bob).json()["items"][0]["unread"]==2
    assert detail(bob,x).json()["unread"]==2
    assert watches(bob).json()["unread"]==2
    assert bob.post(f"/api/living/exhibits/{x}/seen").status_code==200
    assert watches(bob).json()["unread"]==0
    record(alice,x,headline="第四次公开观察")
    assert watches(bob).json()["unread"]==1
    assert alice.post(f"/api/living/exhibits/{x}/seen").status_code==404
    assert bob.delete(f"/api/living/exhibits/{x}/watch").status_code==200
    assert watches(bob).json()["items"]==[]
    assert bob.delete(f"/api/living/exhibits/{x}/watch").status_code==200


def test_private_exhibit_logs_only_author_and_no_public_leak(env):
    alice,bob,visitor=env
    secret=create(alice,"未来才会发布的私人研究",visibility="private")
    r=record(alice,secret,headline="机密研究阶段",note="这是作者写在自己私密档案里的未发布观察。")
    assert r.status_code==201
    assert detail(alice,secret).status_code==200
    assert detail(bob,secret).status_code==404
    assert detail(visitor,secret).status_code==404
    assert bob.post(f"/api/living/exhibits/{secret}/watch").status_code==404
    assert bob.get(f"/api/living/compare?left_id={secret}&right_id=100").status_code==404
    assert "机密研究阶段" not in str(feed(visitor))
    assert "未来才会发布" not in str(visitor.get("/api/living/pulse").json())


def test_revoked_public_source_hides_old_title_and_watchlist_unread(env):
    alice,bob,visitor=env
    x=create(alice,"千万不能泄露的旧标题")
    assert bob.post(f"/api/living/exhibits/{x}/watch").status_code==200
    record(alice,x,headline="敏感的原创调查说明",note="需要由本人控制是否继续公开发布。")
    assert watches(bob).json()["unread"]==1
    out=alice.patch(f"/api/exhibits/{x}",json=item(
        title="千万不能泄露的旧标题",visibility="private"))
    assert out.status_code==200,out.text
    assert detail(bob,x).status_code==404
    assert detail(visitor,x).status_code==404
    assert visitor.get("/api/living/feed").json()["items"]==[]
    assert visitor.get("/api/living/pulse").json()["recorded_changes_30d"]==0
    w=watches(bob).json()
    assert w["unread"]==0
    assert w["items"][0]["available"] is False
    assert w["items"][0]["exhibit"] is None
    assert "千万不能泄露的旧标题" not in str(w)
    assert "敏感的原创调查说明" not in str(w)
    assert bob.post(f"/api/living/exhibits/{x}/seen").status_code==404
    assert bob.post(f"/api/living/exhibits/{x}/watch").status_code==404
    assert bob.delete(f"/api/living/exhibits/{x}/watch").status_code==200
    assert detail(alice,x).json()["entries"][0]["headline"]=="敏感的原创调查说明"


def test_entry_withdrawal_is_owner_only_hidden_from_all_public(env):
    alice,bob,visitor=env
    x=create(alice,"活体植物的发芽故事")
    ev=record(alice,x,headline="叶片数量增加").json()["entry"]["id"]
    assert bob.post(f"/api/living/entries/{ev}/withdraw").status_code==404
    assert visitor.post(f"/api/living/entries/{ev}/withdraw").status_code==401
    assert alice.post(f"/api/living/entries/{ev}/withdraw").status_code==200
    assert alice.post(f"/api/living/entries/{ev}/withdraw").status_code==409
    assert detail(alice,x).json()["entries"]==[]
    assert detail(visitor,x).json()["entries"]==[]
    assert feed(visitor)==[]
    assert visitor.get("/api/living/pulse").json()["recorded_changes_30d"]==0


def test_comparison_only_current_public_sources_no_fabricated_causality(env):
    alice,bob,visitor=env
    a=create(alice,"昆明菌子图鉴",tags="云南,菌子")
    b=create(bob,"云南高原天气观察",tags="云南,天气")
    secret=create(bob,"不公开的报告",visibility="private")
    record(alice,a,headline="新的菌子摄影记录")
    record(bob,b,kind="milestone",headline="进入雨季的观察阶段")
    c=visitor.get(f"/api/living/compare?left_id={a}&right_id={b}")
    assert c.status_code==200,c.text
    data=c.json()
    assert data["left"]["exhibit"]["title"]=="昆明菌子图鉴"
    assert data["right"]["entries"][0]["kind"]=="milestone"
    assert "不推断因果" in data["notice"]
    assert visitor.get(f"/api/living/compare?left_id={a}&right_id={a}").status_code==400
    assert visitor.get(f"/api/living/compare?left_id={a}&right_id={secret}").status_code==404
    assert visitor.get(f"/api/living/compare?left_id={a}&right_id=999999").status_code==404


def test_pulse_counts_only_public_manual_records(env):
    alice,bob,visitor=env
    a=create(alice,"公开植物",domain="动物与生态")
    b=create(bob,"公开鸟类",domain="动物与生态")
    c=create(alice,"私人研究",domain="天文与航天",visibility="private")
    record(alice,a);record(alice,a,headline="第二篇手动记录")
    record(bob,b)
    record(alice,c)
    p=visitor.get("/api/living/pulse").json()
    assert p["recorded_changes_30d"]==3,p
    assert p["active_exhibits_30d"]==2
    assert p["domains"]==[{"domain":"动物与生态","count":3}]
    assert "不是" in p["notice"]


def test_studio_project_private_blocks_public_living_views(env):
    alice,bob,visitor=env
    x=create(alice,"工作室内部藏品观察")
    record(alice,x,headline="不应该在公开观察室出现的内容")
    module=sys.modules["wa_test_server"]
    with module.db() as c:
        c.execute("""INSERT INTO creator_studio_projects
          (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?)""",
          (1,x,"仍未公开的互动作品","quiz","private","{}",module.now(),module.now()))
    assert detail(visitor,x).status_code==404
    assert detail(bob,x).status_code==404
    assert "不应该" not in str(feed(visitor))
    assert visitor.get("/api/living/pulse").json()["recorded_changes_30d"]==0
    assert detail(alice,x).status_code==200


def test_v31_assets_and_integrity(env):
    alice,bob,visitor=env
    assert visitor.get("/api/health").json()["version"]=="36.0"
    html=visitor.get("/").text
    assert "万物活体博物馆" in html
    assert "WONDER ATLAS · WORLD " in html
    for f in ("living.js","living.css"):
        assert f"/static/{f}" in html
        assert visitor.get(f"/static/{f}").status_code==200
    assert "WonderLiving.render" in visitor.get("/static/app.js").text
