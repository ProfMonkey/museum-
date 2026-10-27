"""V10 frontend integration smoke tests."""
import re
from test_multiuser import env

def test_v9_shell_and_new_assets_are_served(env):
    client=env[0]
    page=client.get('/')
    assert page.status_code==200
    html=page.text
    assert '当代新奇' in html and '展厅工坊' in html
    assert '/static/culture.js' in html
    assert '/static/virtual-gallery.js' in html
    assert '/static/virtual-gallery-3d.js' in html
    assert re.search(r'WONDER ATLAS · WORLD \d+', html)
    assert '/static/evolution.js' in html
    assert '/static/evolution.css' in html
    for path, token in [
        ('/static/culture.js','cnmeme.wiki/api/v1/public/memes'),
        ('/static/culture.js','Hacker News'),
        ('/static/virtual-gallery.js','9 套平面图'),
        ('/static/virtual-gallery-3d.js','THREE.WebGLRenderer'),
        ('/static/culture.css','.culture-grid'),
        ('/static/virtual-gallery.css','.vg-3d-stage'),
    ]:
        r=client.get(path)
        assert r.status_code==200, path
        assert token in r.text, path

def test_health_version_matches_current_release(env):
    client=env[0]
    data=client.get('/api/health').json()
    assert data['ok'] is True
    assert data['version']=='20.0'