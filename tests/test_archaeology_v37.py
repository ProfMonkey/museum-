"""V37 independent real HTTP tests; execute locally only, not GitHub Actions."""
from test_multiuser import env, item
from test_embassies_v35 import setup
from test_collision_v33 import exhibit
import sys


def payload(cid, exhibit_id, **kw):
    base={
        "civilization_id":cid,"exhibit_id":exhibit_id,"era":2,
        "role":"sacred","title":"这块芯片被当作星辰之石",
        "introduction":"经过漫长虚构历史的考古纪元，一位馆长从城市遗址里发现不可理解的器物。",
        "surface":"表面布满密密麻麻的纹路，文明将它视为天空留下的一封信。",
        "inscription":"古人以神圣文字解释这件物品，甚至建立了一整套完全不存在的祭仪。",
        "interpretation":"馆长最终假说认为，这件来自现实世界的普通物品被架空文明误解为星辰的碎片。故事纯属虚构。"
    }
    base.update(kw)
    return base


def create(client,cid,exid,**kw):
    return client.post("/api/archaeology",json=payload(cid,exid,**kw))


def state(alice,bob):
    a,b,aw,bw,ax,bx,p=setup(alice,bob)
    return a,b,ax,bx


def test_public_empty_and_explanation_is_fictional(env):
    alice,bob,guest=env
    assert guest.get("/api/archaeology/public").json()["items"]==[]
    data=guest.get("/api/archaeology/roles").json()
    assert len(data["items"])==6
    assert data["limits"]["layers"]==3
    assert "不是" in data["notice"]
    assert guest.get("/api/archaeology/mine").status_code==401
    assert guest.get("/api/archaeology/civilizations").status_code==401
    assert guest.post("/api/archaeology",json=payload(1,2)).status_code==401


def test_only_real_civilization_author_may_create_and_era_checked(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    assert create(bob,a,ax).status_code==404
    assert create(alice,b,ax).status_code==404
    secret=exhibit(bob,"私人秘密芯片",visibility="private")
    assert create(alice,a,secret).status_code==404
    assert create(alice,a,999999).status_code==404
    assert create(alice,a,ax,era=8).status_code==422
    assert create(alice,a,ax,role="fake_scholarly_status").status_code==422
    assert create(alice,a,ax,interpretation="太短").status_code==422
    created=create(alice,a,ax)
    assert created.status_code==201,created.text
    assert created.json()["status"]=="draft"
    assert create(alice,a,ax).status_code==409
    assert bob.get(f"/api/archaeology/{created.json()['id']}").status_code==404


def test_source_picker_visibility_and_no_false_content(env):
    alice,bob,guest=env
    good=exhibit(alice,"公开机械望远镜")
    secret=exhibit(bob,"私人机械望远镜",visibility="private")
    r=guest.get("/api/archaeology/sources?q=机械望远镜")
    assert r.status_code==200,r.text
    assert [x["id"] for x in r.json()["items"]]==[good]
    assert secret not in str(r.json())
    assert "interpretation" not in str(r.json())


def test_three_layer_exploration_is_author_text_and_private_progress(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,ax).json()["id"]
    assert alice.get(f"/api/archaeology/{rid}").json()["surface"].startswith("表面")
    assert guest.get(f"/api/archaeology/{rid}/layer/1").status_code==404
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==200
    public=guest.get(f"/api/archaeology/{rid}")
    assert public.status_code==200,public.text
    assert public.json()["status"]=="public"
    assert "surface" not in public.json()
    assert "interpretation" not in public.json()
    assert public.json()["exhibit"]["id"]==ax
    assert len(guest.get("/api/archaeology/public").json()["items"])==1
    assert bob.get(f"/api/archaeology/{rid}/layer/2").status_code==409
    first=bob.get(f"/api/archaeology/{rid}/layer/1")
    assert first.status_code==200
    assert first.json()["content"].startswith("表面")
    assert first.json()["my_layer"]==1
    assert bob.get(f"/api/archaeology/{rid}").json()["my_layer"]==1
    second=bob.get(f"/api/archaeology/{rid}/layer/2")
    assert second.status_code==200 and second.json()["my_layer"]==2
    assert bob.get(f"/api/archaeology/{rid}/layer/3").json()["my_layer"]==3
    assert alice.get(f"/api/archaeology/{rid}").json()["my_layer"]==0
    assert guest.get(f"/api/archaeology/{rid}/layer/2").status_code==200  # guest has no saved progress
    assert guest.get(f"/api/archaeology/{rid}/layer/4").status_code==422


def test_same_real_exhibit_has_distinct_fake_roles_across_real_civilizations(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    first=create(alice,a,ax,role="sacred",title="钟楼作为神圣遗物").json()["id"]
    second=create(bob,b,ax,role="tool",title="钟楼作为科学工具").json()["id"]
    alice.post(f"/api/archaeology/{first}/publish")
    bob.post(f"/api/archaeology/{second}/publish")
    result=guest.get(f"/api/archaeology/exhibit/{ax}/echoes")
    assert result.status_code==200,result.text
    data=result.json()
    assert data["exhibit"]["id"]==ax
    assert {x["id"] for x in data["items"]}=={first,second}
    assert data["unique_roles"]==2
    assert {x["author"] for x in data["items"]}=={"Alice","Bob"}
    assert {x["role"] for x in data["items"]}=={"sacred","tool"}
    assert "馆长" in data["notice"] or "文明" in data["notice"]


def test_visitor_cannot_modify_and_publish_retraction_clears_progress(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,ax).json()["id"]
    assert bob.post(f"/api/archaeology/{rid}/publish").status_code==404
    alice.post(f"/api/archaeology/{rid}/publish")
    bob.get(f"/api/archaeology/{rid}/layer/1")
    assert bob.get(f"/api/archaeology/{rid}").json()["my_layer"]==1
    assert bob.put(f"/api/archaeology/{rid}",json=payload(a,ax)).status_code==404
    assert bob.post(f"/api/archaeology/{rid}/close").status_code==404
    modified=alice.put(f"/api/archaeology/{rid}",json=payload(a,ax,
       interpretation="新版本解释：这座架空文明其实将古老原物误认为一种能够储存过去梦境的透明材料，其故事完全虚构。"))
    assert modified.status_code==200,modified.text
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    alice.post(f"/api/archaeology/{rid}/publish")
    assert bob.get(f"/api/archaeology/{rid}").json()["my_layer"]==0
    assert alice.post(f"/api/archaeology/{rid}/retract").status_code==200
    assert guest.get("/api/archaeology/public").json()["items"]==[]
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==200


def test_retracted_original_source_cannot_silently_restore_and_needs_rebase(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,bx).json()["id"]
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==200
    changed=bob.patch(f"/api/exhibits/{bx}",json=item(title="云南米线",visibility="private"))
    assert changed.status_code==200,changed.text
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert guest.get("/api/archaeology/public").json()["items"]==[]
    masked=alice.get(f"/api/archaeology/{rid}").json()
    assert masked["available"] is False
    assert masked["exhibit"] is None and masked["civilization"] is None
    assert masked["title"]=="来源已撤回或文明历史改变"
    assert "云南米线" not in str(masked)
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==409
    back=bob.patch(f"/api/exhibits/{bx}",json=item(title="云南米线",visibility="public"))
    assert back.status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert alice.post(f"/api/archaeology/{rid}/rebase").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==200


def test_changed_v34_parent_requires_author_revalidation_and_new_publication(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,ax).json()["id"]
    alice.post(f"/api/archaeology/{rid}/publish")
    assert guest.get(f"/api/archaeology/{rid}").status_code==200
    assert alice.post(f"/api/civilizations/{a}/unpublish").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert alice.post(f"/api/civilizations/{a}/publish").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert alice.post(f"/api/archaeology/{rid}/rebase").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==200


def test_archiving_keeps_originals_and_old_dossier_hidden(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,ax).json()["id"]
    alice.post(f"/api/archaeology/{rid}/publish")
    assert alice.post(f"/api/archaeology/{rid}/close").status_code==200
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert guest.get("/api/archaeology/public").json()["items"]==[]
    assert alice.post(f"/api/archaeology/{rid}/publish").status_code==409
    assert alice.get(f"/api/exhibits/{ax}").status_code==200
    assert alice.get(f"/api/civilizations/{a}").status_code==200


def test_parent_creator_studio_privacy_blocks_current_public_archaeology(env):
    alice,bob,guest=env
    a,b,ax,bx=state(alice,bob)
    rid=create(alice,a,ax).json()["id"]
    alice.post(f"/api/archaeology/{rid}/publish")
    module=sys.modules["wa_test_server"]
    with module.db() as c:
        c.execute("""INSERT INTO creator_studio_projects
              (owner_id,exhibit_id,title,kind,visibility,config_json,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?)""",(1,ax,"私密考古来源","quiz","private","{}",module.now(),module.now()))
    assert guest.get(f"/api/archaeology/{rid}").status_code==404
    assert guest.get("/api/archaeology/public").json()["items"]==[]
    assert guest.get(f"/api/archaeology/exhibit/{ax}/echoes").status_code==404


def test_v37_assets_and_version(env):
    alice,bob,guest=env
    assert guest.get("/api/health").json()["version"]=="39.0"
    html=guest.get("/").text
    assert "WORLD 39" in html
    assert "万物文明考古局" in html
    for asset in ("archaeology.js","archaeology.css"):
        assert f"/static/{asset}" in html
        assert guest.get(f"/static/{asset}").status_code==200
    assert "WonderArchaeology.render()" in guest.get("/static/app.js").text
