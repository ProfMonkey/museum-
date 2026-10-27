"""V27 personal constellation: private nodes, source revocation, explainable links, and opt-in imports."""
import pytest
import wheel_api
from test_multiuser import env, item
from test_adventure_v25 import make_wheel, new_card, advance


def exhibit(client, title, tags="cosmos,curiosity", **kwargs):
    r=client.post("/api/exhibits",json=item(title=title,tags=tags,**kwargs))
    assert r.status_code==201,r.text
    return r.json()


def add_exhibit_node(client,eid,note=""):
    return client.post("/api/constellation/nodes",
        json={"kind":"exhibit","exhibit_id":eid,"note":note})


def add_idea(client,title,note=""):
    return client.post("/api/constellation/nodes",
        json={"kind":"idea","title":title,"note":note})


def graph(client):
    return client.get("/api/constellation")


def test_constellation_is_private_and_requires_login(env):
    alice,bob,guest=env
    assert guest.get("/api/constellation").status_code==401
    assert guest.post("/api/constellation/nodes",json={
        "kind":"idea","title":"访客的私密想法"}).status_code==401
    assert graph(alice).json()["nodes"]==[]
    node=add_idea(alice,"我的个人猜想","只是我暂时记下来的一个想法。")
    assert node.status_code==201,node.text
    payload=graph(alice).json()
    assert len(payload["nodes"])==1
    assert payload["nodes"][0]["title"]=="我的个人猜想"
    assert payload["nodes"][0]["visibility"]=="private"
    assert graph(bob).json()["nodes"]==[]
    assert "仅本人可见" in payload["notice"]


def test_exhibit_nodes_require_access_and_duplicate_is_rejected(env):
    alice,bob,guest=env
    public=exhibit(bob,"公开的远古星图")
    private=exhibit(bob,"不公开的私人日记",visibility="private")
    added=add_exhibit_node(alice,public["id"])
    assert added.status_code==201,added.text
    assert added.json()["node"]["title"]=="公开的远古星图"
    assert add_exhibit_node(alice,public["id"]).status_code==409
    assert add_exhibit_node(alice,private["id"]).status_code==404
    own_private=exhibit(alice,"只属于我的研究笔记",visibility="private")
    assert add_exhibit_node(alice,own_private["id"]).status_code==201
    titles=[x["title"] for x in graph(alice).json()["nodes"]]
    assert "不公开的私人日记" not in titles
    assert "只属于我的研究笔记" in titles


def test_user_can_create_and_remove_personal_links(env):
    alice,bob,guest=env
    a=add_idea(alice,"时间旅行","我想比较历史叙事与物理时间。").json()["node"]
    b=add_idea(alice,"历史小说","虚构故事如何借用真实年代？").json()["node"]
    body={"from_node_id":a["id"],"to_node_id":b["id"],
          "kind":"historical","note":"两者都讨论时间和历史叙事，但表达方式不同。"}
    created=alice.post("/api/constellation/edges",json=body)
    assert created.status_code==201,created.text
    assert "未经过平台事实核验" in created.json()["notice"]
    g=graph(alice).json()
    assert len(g["edges"])==1 and g["edges"][0]["verified"] is False
    assert g["edges"][0]["label"]=="历史脉络"
    assert alice.post("/api/constellation/edges",json=body).status_code==409
    assert alice.post("/api/constellation/edges",json={
        **body,"from_node_id":a["id"],"to_node_id":a["id"]}).status_code==400
    assert bob.delete(f"/api/constellation/edges/{created.json()['id']}").status_code==404
    assert alice.delete(f"/api/constellation/edges/{created.json()['id']}").status_code==200
    assert graph(alice).json()["edges"]==[]


def test_system_clues_are_explainable_and_not_auto_saved(env):
    alice,bob,guest=env
    a=exhibit(alice,"古画中的星河","星河,古画,艺术",category="绘画与书画",domain="绘画与视觉艺术")
    b=exhibit(bob,"另一件星河作品","星河,绘画,艺术",category="绘画与书画",domain="绘画与视觉艺术")
    unrelated=exhibit(bob,"一台机械钟","齿轮,机械",category="科技与发明",domain="工程与发明")
    na=add_exhibit_node(alice,a["id"]).json()["node"]
    nb=add_exhibit_node(alice,b["id"]).json()["node"]
    nu=add_exhibit_node(alice,unrelated["id"]).json()["node"]
    payload=graph(alice).json()
    assert len(payload["edges"])==0
    pair=[x for x in payload["suggestions"]
          if {x["from_node_id"],x["to_node_id"]}=={na["id"],nb["id"]}]
    assert pair
    assert "共同标签" in pair[0]["reason"]
    assert not any({x["from_node_id"],x["to_node_id"]}=={na["id"],nu["id"]}
                   for x in payload["suggestions"])
    assert "需由你判断" in pair[0]["notice"]
    r=alice.post("/api/constellation/edges",json={
        "from_node_id":na["id"],"to_node_id":nb["id"],"kind":"same_topic",
        "note":pair[0]["reason"]+"；这是我确认保存的个人联想。"})
    assert r.status_code==201,r.text
    after=graph(alice).json()
    assert any(e["kind"]=="same_topic" for e in after["edges"])
    assert not any({x["from_node_id"],x["to_node_id"]}=={na["id"],nb["id"]}
                   for x in after["suggestions"])


def test_private_transition_redacts_old_exhibit_title_but_keeps_removable_node(env):
    alice,bob,guest=env
    source=exhibit(bob,"星河档案原始标题","星河,宇宙")
    n=add_exhibit_node(alice,source["id"]).json()["node"]
    idea=add_idea(alice,"我的观察","我想研究它与天文学的联系。").json()["node"]
    link=alice.post("/api/constellation/edges",json={
        "from_node_id":n["id"],"to_node_id":idea["id"],"kind":"curiosity",
        "note":"我曾在它的描述中看到值得追问的细节。"})
    assert link.status_code==201,link.text
    r=bob.patch(f"/api/exhibits/{source['id']}",json=item(
        title="星河档案原始标题",tags="星河,宇宙",visibility="private"))
    assert r.status_code==200,r.text
    payload=graph(alice).json()
    placeholder=next(x for x in payload["nodes"] if x["id"]==n["id"])
    assert placeholder["source_unavailable"] is True
    assert placeholder["title"]=="原始藏品已不可见"
    assert placeholder["exhibit_id"] is None
    assert "星河档案原始标题" not in str(payload)
    assert alice.post("/api/constellation/edges",json={
        "from_node_id":n["id"],"to_node_id":idea["id"],"kind":"personal",
        "note":"不能再使用这个失效的来源节点。"}).status_code==409
    assert alice.delete(f"/api/constellation/nodes/{n['id']}").status_code==200
    payload=graph(alice).json()
    assert all(x["id"]!=n["id"] for x in payload["nodes"])
    assert payload["edges"]==[]


def test_deleted_exhibit_does_not_leave_a_title_snapshot(env):
    alice,bob,guest=env
    source=exhibit(bob,"会消失的旧藏品")
    node=add_exhibit_node(alice,source["id"]).json()["node"]
    assert bob.delete(f"/api/exhibits/{source['id']}").status_code==200
    payload=graph(alice).json()
    dead=next(x for x in payload["nodes"] if x["id"]==node["id"])
    assert dead["source_unavailable"] is True
    assert dead["title"]=="原始藏品已不可见"
    assert "会消失的旧藏品" not in str(payload)


def test_import_is_opt_in_idempotent_and_respects_sources(env):
    alice,bob,guest=env
    own=exhibit(alice,"我自己的私人标本",visibility="private")
    saved=exhibit(bob,"我收藏的公开古画")
    history=exhibit(bob,"我自愿记录的浏览对象")
    assert alice.post(f"/api/exhibits/{saved['id']}/bookmark").status_code==200
    assert alice.post(f"/api/memories/seen/{history['id']}").status_code==200
    assert graph(alice).json()["nodes"]==[]
    first=alice.post("/api/constellation/import",json={})
    assert first.status_code==200,first.text
    data=first.json()
    assert data["added"]==3
    assert data["by_source"]["owned"]==1
    assert data["by_source"]["bookmarked"]==1
    assert data["by_source"]["history"]==1
    payload=graph(alice).json()
    by_title={x["title"]:x for x in payload["nodes"]}
    assert by_title["我自己的私人标本"]["visibility"]=="private"
    assert by_title["我收藏的公开古画"]["origin"]=="bookmarked"
    assert by_title["我自愿记录的浏览对象"]["origin"]=="history"
    second=alice.post("/api/constellation/import",json={})
    assert second.status_code==200
    assert second.json()["added"]==0
    assert len(graph(alice).json()["nodes"])==3


def test_import_includes_only_owner_confirmed_quest_visits(env,monkeypatch):
    alice,bob,guest=env
    source=exhibit(bob,"奇遇里自标记的化石","化石,古生物")
    wheel=make_wheel(alice,"我的化石线索","custom",("手动选项",))
    r=alice.post(f"/api/wheels/{wheel}/items",json={
        "kind":"exhibit","exhibit_id":source["id"]})
    assert r.status_code==201,r.text
    other=make_wheel(alice,"另一站","travel",("博物馆","公园"))
    card=new_card(alice,[wheel,other])
    monkeypatch.setattr(wheel_api.secrets,"randbelow",lambda n:n-1)
    result=advance(alice,card)
    assert result.status_code==200,result.text
    assert result.json()["stage"]["label"]=="奇遇里自标记的化石"
    visit=alice.post(f"/api/adventures/{card}/quests/1/visit",
        json={"exhibit_id":source["id"]})
    assert visit.status_code==200,visit.text
    imported=alice.post("/api/constellation/import",json={}).json()
    assert imported["by_source"]["visited"]==1
    node=next(x for x in graph(alice).json()["nodes"] if x["exhibit_id"]==source["id"])
    assert node["origin"]=="visited"


def test_schema_validation_and_node_delete_permissions(env):
    alice,bob,guest=env
    assert add_idea(alice,"").status_code==422
    assert alice.post("/api/constellation/nodes",json={
        "kind":"idea","title":"错误节点","exhibit_id":1}).status_code==422
    assert alice.post("/api/constellation/nodes",json={
        "kind":"exhibit","title":"伪造标题"}).status_code==422
    a=add_idea(alice,"甲想法").json()["node"]
    b=add_idea(alice,"乙想法").json()["node"]
    assert alice.post("/api/constellation/edges",json={
        "from_node_id":a["id"],"to_node_id":b["id"],"kind":"personal",
        "note":"短"}).status_code==422
    assert bob.delete(f"/api/constellation/nodes/{a['id']}").status_code==404
    assert guest.delete(f"/api/constellation/nodes/{a['id']}").status_code==401
    assert alice.delete(f"/api/constellation/nodes/{a['id']}").status_code==200
    assert alice.delete(f"/api/constellation/nodes/{b['id']}").status_code==200


def test_assets_and_version_are_integrated(env):
    alice,bob,guest=env
    html=guest.get("/").text
    assert "万物星图" in html
    assert guest.get("/api/health").json()["version"]=="31.0"
    for asset in ("constellation.css","constellation.js"):
        assert f"/static/{asset}" in html
        assert guest.get(f"/static/{asset}").status_code==200
    assert graph(alice).status_code==200



def test_personal_idea_editing_never_changes_original_exhibit(env):
    alice,bob,guest=env
    idea=add_idea(alice,"旧想法","第一版笔记").json()["node"]
    edited=alice.patch(f"/api/constellation/nodes/{idea['id']}",json={
        "title":"更新后的想法","note":"经过思考，我想把这个问题重新表述。"})
    assert edited.status_code==200,edited.text
    assert edited.json()["node"]["title"]=="更新后的想法"
    assert edited.json()["node"]["note"]=="经过思考，我想把这个问题重新表述。"
    assert bob.patch(f"/api/constellation/nodes/{idea['id']}",json={
        "title":"试图修改别人节点"}).status_code==404
    original=exhibit(bob,"不可在星图中改名的藏品")
    node=add_exhibit_node(alice,original["id"]).json()["node"]
    assert alice.patch(f"/api/constellation/nodes/{node['id']}",json={
        "title":"伪造的新展品名称"}).status_code==400
    note=alice.patch(f"/api/constellation/nodes/{node['id']}",json={
        "note":"我个人认为它可以和别的展品对照。"})
    assert note.status_code==200,note.text
    assert note.json()["node"]["title"]=="不可在星图中改名的藏品"
    assert note.json()["node"]["note"]=="我个人认为它可以和别的展品对照。"
