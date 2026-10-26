"""V10 faceted classification integration tests."""
from test_multiuser import env, item


def test_taxonomy_endpoint_exposes_broad_domains_and_time_axes(env):
    client = env[2]
    data = client.get("/api/taxonomy").json()
    assert data["series"] == ["藏品系列", "民间奇趣"]
    assert len(data["domains"]) >= 30
    assert "自然史与化石" in data["domains"]
    assert "数码产品" in data["domains"]
    assert "网络文化与热梗" in data["domains"]
    assert "亿年前" in data["time_buckets"]
    assert "最近一年" in data["time_buckets"]
    assert "此刻/实时" in data["time_buckets"]
    assert "走红/传播" in data["time_bases"]


def test_exhibits_can_be_filtered_by_series_domain_and_time(env):
    alice, bob, visitor = env
    fossil = alice.post("/api/exhibits", json=item(
        title="约 1.2 亿年前的化石",
        category="化石与古生物",
        series="藏品系列",
        domain="自然史与化石",
        time_bucket="亿年前",
        time_basis="形成/演化",
        time_note="约 1.2 亿年前",
    )).json()
    meme = alice.post("/api/exhibits", json=item(
        title="今年流行的网络热梗",
        category="网络热梗",
        series="民间奇趣",
        domain="网络文化与热梗",
        time_bucket="最近一年",
        time_basis="走红/传播",
        time_note="2026 年传播",
    )).json()
    assert fossil["series"] == "藏品系列"
    assert fossil["domain"] == "自然史与化石"
    assert fossil["time_bucket"] == "亿年前"
    assert fossil["time_basis"] == "形成/演化"
    assert fossil["time_note"] == "约 1.2 亿年前"
    assert meme["series"] == "民间奇趣"
    found = visitor.get(
        "/api/feed",
        params={
            "series": "藏品系列",
            "domain": "自然史与化石",
            "category": "化石与古生物",
            "time_bucket": "亿年前",
        },
    ).json()["items"]
    assert [x["id"] for x in found] == [fossil["id"]]
    found_meme = visitor.get(
        "/api/feed",
        params={"series": "民间奇趣", "domain": "网络文化与热梗", "time_bucket": "最近一年"},
    ).json()["items"]
    assert [x["id"] for x in found_meme] == [meme["id"]]
    assert bob.get("/api/feed", params={"domain": "not-a-domain"}).status_code == 400


def test_taxonomy_fields_survive_edit_and_backup_restore(env):
    alice, bob, visitor = env
    saved = alice.post("/api/exhibits", json=item(
        title="模块化电脑",
        category="电脑与笔记本",
        series="藏品系列",
        domain="数码产品",
        time_bucket="近30年",
        time_basis="发明/发布",
        time_note="约 2000 年后逐步普及",
    )).json()
    changed = alice.patch(
        f"/api/exhibits/{saved['id']}",
        json=item(
            title="模块化电脑",
            category="电脑与笔记本",
            series="藏品系列",
            domain="数码产品",
            time_bucket="最近一年",
            time_basis="发明/发布",
            time_note="2026 年新版本",
        ),
    ).json()
    assert changed["time_bucket"] == "最近一年"
    assert changed["time_note"] == "2026 年新版本"
    backup = alice.get("/api/my/backup").json()
    result = bob.post("/api/import/v2", json=backup)
    assert result.status_code == 200, result.text
    imported = next(x for x in bob.get("/api/my/exhibits").json() if x["title"] == "模块化电脑")
    assert imported["series"] == "藏品系列"
    assert imported["domain"] == "数码产品"
    assert imported["time_bucket"] == "最近一年"
    assert imported["time_basis"] == "发明/发布"
    assert imported["time_note"] == "2026 年新版本"


def test_v10_taxonomy_script_is_loaded_before_app(env):
    client = env[2]
    page = client.get("/")
    assert page.status_code == 200
    assert page.text.index('/static/taxonomy.js') < page.text.index('/static/app.js')
    script = client.get("/static/taxonomy.js")
    assert script.status_code == 200
    assert "timeBuckets" in script.text
    assert "series: [\"藏品系列\",\"民间奇趣\"]" in script.text


def test_old_sqlite_exhibits_are_migrated_without_data_loss(tmp_path, monkeypatch):
    import importlib.util
    import os
    import sqlite3
    import sys
    from pathlib import Path

    data_dir = tmp_path / "legacy-data"
    data_dir.mkdir()
    database = data_dir / "wonder.db"
    conn = sqlite3.connect(database)
    conn.executescript("""
    CREATE TABLE users(
      id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password_hash TEXT NOT NULL, bio TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE exhibits(
      id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', story TEXT NOT NULL DEFAULT '',
      category TEXT NOT NULL DEFAULT '其他', tags TEXT NOT NULL DEFAULT '',
      image_url TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '',
      visibility TEXT NOT NULL CHECK(visibility IN ('public','private')) DEFAULT 'private',
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    """)
    conn.execute("INSERT INTO users(id,username,password_hash,bio,created_at) VALUES(1,'Legacy','unused','','2020-01-01')")
    conn.execute("INSERT INTO exhibits(id,user_id,title,category,visibility,created_at,updated_at) VALUES(1,1,'旧化石','自然与化石','private','2020-01-01','2020-01-01')")
    conn.commit()
    conn.close()

    monkeypatch.setenv("WONDER_DATA_DIR", str(data_dir))
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("wa_v10_legacy_migration_test", root / "server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    with module.db() as c:
        row = c.execute("SELECT title,category,series,domain,time_bucket,time_basis,time_note FROM exhibits WHERE id=1").fetchone()
    assert row["title"] == "旧化石"
    assert row["category"] == "自然与化石"
    assert row["series"] == "民间奇趣"
    assert row["domain"] == "自然史与化石"
    assert row["time_bucket"] == "时间不详"
    assert row["time_basis"] == "不详"
