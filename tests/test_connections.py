"""V11: privacy-safe, source-labelled exhibit relation graph integration tests."""
from test_multiuser import env, item


def post(client, title, tags, **kwargs):
    response = client.post('/api/exhibits', json=item(title=title, tags=tags, **kwargs))
    assert response.status_code == 201, response.text
    return response.json()


def test_classification_path_and_explainable_suggestions(env):
    alice, bob, visitor = env
    a = post(alice, '古画之海', '海浪,绘画', category='绘画与书画')
    b = post(bob, '另一件海浪作品', '海浪,油画', category='绘画与书画')
    other = post(bob, '完全无关的机械', '金属,机器', category='科技与发明')
    response = visitor.get(f"/api/exhibits/{a['id']}/connections")
    assert response.status_code == 200, response.text
    graph = response.json()
    assert graph['focus']['id'] == a['id']
    assert graph['path']['collection'][-1] == '绘画与书画'
    assert graph['path']['time'] == ['时间不详', '不详']
    assert graph['path']['source_status'] == '尚未附来源链接'
    suggestion = [e for e in graph['edges'] if e['source'] == 'suggestion']
    assert any(e['to'] == b['id'] for e in suggestion)
    assert all('共同标签' in e['explanation'] or '同属' in e['explanation'] for e in suggestion)
    assert other['id'] not in [x['id'] for x in graph['nodes']]


def test_manual_link_has_author_explanation_and_unverified_label(env):
    alice, bob, visitor = env
    a = post(alice, '古代金属工艺', '金属,工艺')
    b = post(bob, '现代芯片制造', '芯片,工业')
    new = alice.post(f"/api/exhibits/{a['id']}/connections", json={
        'target_id': b['id'], 'kind': 'materials',
        'explanation': '这是馆长提出的比较：二者都涉及材料加工工艺。',
    })
    assert new.status_code == 201, new.text
    link_id = new.json()['id']
    assert '未经过平台事实核验' in new.json()['notice']
    graph = visitor.get(f"/api/exhibits/{a['id']}/connections").json()
    curated = [e for e in graph['edges'] if e['source'] == 'curator']
    assert len(curated) == 1
    assert curated[0]['id'] == link_id
    assert curated[0]['author'] == 'Alice'
    assert curated[0]['label'] == '材料或工艺'
    assert curated[0]['editable'] is False
    assert graph['disclaimer']
    assert bob.delete(f"/api/exhibits/{a['id']}/connections/{link_id}").status_code == 403
    assert alice.delete(f"/api/exhibits/{a['id']}/connections/{link_id}").status_code == 200
    after = visitor.get(f"/api/exhibits/{a['id']}/connections").json()
    assert not any(e['source'] == 'curator' for e in after['edges'])


def test_private_exhibit_never_leaks_to_strangers(env):
    alice, bob, visitor = env
    public = post(alice, '公开的研究记录', '研究,文档', visibility='public')
    private = post(alice, '私密研究笔记', '研究,文档', visibility='private')
    foreign_private = post(bob, 'Bob 的私密草稿', '研究,文档', visibility='private')
    added = alice.post(f"/api/exhibits/{public['id']}/connections", json={
        'target_id': private['id'], 'kind': 'same_topic',
        'explanation': '我的私人草稿与公开研究记录有关。',
    })
    assert added.status_code == 201
    assert alice.post(f"/api/exhibits/{public['id']}/connections", json={
        'target_id': foreign_private['id'], 'kind': 'same_topic',
        'explanation': '不应该看到别人没有公开的私人笔记。',
    }).status_code == 404
    for c in (bob, visitor):
        graph = c.get(f"/api/exhibits/{public['id']}/connections?depth=2").json()
        ids = [n['id'] for n in graph['nodes']]
        assert private['id'] not in ids
        if c is visitor:
            assert foreign_private['id'] not in ids
        assert all(e['from'] != private['id'] and e['to'] != private['id'] for e in graph['edges'])
        assert c.get(f"/api/exhibits/{private['id']}/connections").status_code == 404
    own = alice.get(f"/api/exhibits/{public['id']}/connections").json()
    assert private['id'] in [n['id'] for n in own['nodes']]
    assert alice.get(f"/api/exhibits/{private['id']}/connections").status_code == 200


def test_link_authorship_validation_and_depth_limits(env):
    alice, bob, visitor = env
    a = post(alice, 'A', 'one', visibility='public')
    b = post(bob, 'B', 'two', visibility='public')
    candidate = {'target_id': b['id'], 'kind': 'influence', 'explanation': '馆长在这里描述了两个对象之间的启发联系。'}
    assert visitor.post(f"/api/exhibits/{a['id']}/connections",json=candidate).status_code == 401
    assert bob.post(f"/api/exhibits/{a['id']}/connections",json=candidate).status_code == 403
    assert alice.post(f"/api/exhibits/{a['id']}/connections", json={**candidate,'target_id':a['id']}).status_code == 400
    assert alice.post(f"/api/exhibits/{a['id']}/connections", json={**candidate,'explanation':'短'}).status_code == 422
    assert alice.post(f"/api/exhibits/{a['id']}/connections", json=candidate).status_code == 201
    assert alice.post(f"/api/exhibits/{a['id']}/connections", json=candidate).status_code == 409
    assert visitor.get(f"/api/exhibits/{a['id']}/connections?depth=3").status_code == 422
    graph = visitor.get(f"/api/exhibits/{a['id']}/connections?depth=2").json()
    assert len(graph['nodes']) <= 32
    ids = {n['id'] for n in graph['nodes']}
    assert all(e['from'] in ids and e['to'] in ids for e in graph['edges'])


def test_ui_entry_and_routes_are_live(env):
    visitor = env[2]
    page = visitor.get('/')
    assert '/static/connections.js' in page.text
    assert '/static/connections.css' in page.text
    assert '分类与关联图' in visitor.get('/static/app.js').text
    assert '馆长关联' in visitor.get('/static/connections.js').text
    assert visitor.get('/static/connections.css').status_code == 200


def test_v10_fields_surface_as_independent_classification_paths(env):
    import sys
    from test_multiuser import item
    alice, bob, visitor = env
    original = post(alice, '一份古老的玉器档案', '玉器,工艺', category='古董与珠宝', source_url='https://www.metmuseum.org/art/collection')
    module = sys.modules['wa_test_server']
    # V9 fixture has no faceted columns; recreate just the fields introduced by V10.
    with module.db() as conn:
        existing = {row['name'] for row in conn.execute('PRAGMA table_info(exhibits)')}
        for name in ('series','domain','time_bucket','time_basis','time_note'):
            if name not in existing:
                conn.execute('ALTER TABLE exhibits ADD COLUMN ' + name + ' TEXT NOT NULL DEFAULT \'\'')
        conn.execute("""UPDATE exhibits SET series='藏品系列', domain='古董与收藏',
            time_bucket='近千年', time_basis='制作/创作', time_note='明代，具体年代待核' WHERE id=?""",(original['id'],))
    result = visitor.get(f"/api/exhibits/{original['id']}/connections")
    assert result.status_code == 200, result.text
    path = result.json()['path']
    assert path['collection'] == ['藏品系列','古董与收藏','古董与珠宝']
    assert path['time'] == ['近千年','制作/创作']
    assert path['time_note'] == '明代，具体年代待核'
    assert path['source_status'] == '附有来源链接'