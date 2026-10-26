"""V14 official-source discovery: no image misattribution, no invented ages."""
import world_sources_v14 as v14
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from test_multiuser import env


def _client():
    app = FastAPI()
    v14.mount_world_sources(app)
    return TestClient(app)


def test_metadata_routes_and_clear_directory_status():
    c = _client()
    p = c.get('/api/world-sources/providers')
    assert p.status_code == 200
    data = p.json()
    assert {x['id'] for x in data['providers']} == {'met', 'nhm'}
    assert next(x for x in data['directories'] if '史密森尼' in x['name'])['status'] == 'official_directory_api_requires_key'
    assert c.get('/api/world-sources/search?provider=invalid&q=fossil').status_code == 422
    assert c.get('/api/world-sources/search?provider=nhm&q=x').status_code == 422


def test_nhm_data_parsing_never_conflates_collection_year_with_geological_age():
    result = v14.safe_nhm_record({'_id': 25799, 'scientificName': 'Tyrannosaurus rex', 'catalogNumber': 'R-555', 'collectionCode': 'PAL', 'family': 'Tyrannosauridae', 'year': 2010})
    assert result['title'] == 'Tyrannosaurus rex'
    assert result['id'] == 'nhm:25799'
    assert result['time_bucket'] == '时间不详'
    assert result['time_basis'] == '不详'
    assert '不是化石形成时间' in result['date_note']
    assert result['image_url'] == ''
    assert result['source_url'].startswith(v14.NHM_DATASET + '/resource/')
    assert v14.safe_nhm_record({'_id': '../../etc/passwd'}) is None


def test_met_only_uses_public_domain_and_expected_image_hostname():
    r = {'objectID': 300, 'title': 'Golden necklace', 'primaryImageSmall': 'https://images.metmuseum.org/a.jpg', 'isPublicDomain': False}
    assert v14.safe_met_object(r)['image_url'] == ''
    r['isPublicDomain'] = True
    assert v14.safe_met_object(r)['image_url'].startswith(v14.MET_IMAGE_PREFIX)
    r['primaryImageSmall'] = 'https://images.metmuseum.org.evil.test/image.jpg'
    assert v14.safe_met_object(r)['image_url'] == ''
    assert v14.safe_met_object({'title': 'Missing id'}) is None


def test_met_search_migrated_to_v1_1_pagination_and_bounded(monkeypatch):
    urls = []
    def fake(url):
        urls.append(url)
        if '/v1.1/search' in url:
            return {'total': 22, 'objectIDs': [20, 21, 22, 23]}
        return {'objectID': int(url.split('/')[-1]), 'title': 'Verified artwork', 'isPublicDomain': False}
    monkeypatch.setattr(v14, '_fetch_json', fake)
    got, total = v14.search_met('古画', 2)
    assert total == 22 and len(got) == 2
    assert '/public/collection/v1.1/search' in urls[0]
    assert 'limit=4' in urls[0]
    assert len(urls) == 3


def test_nhm_official_url_and_cache(monkeypatch):
    v14._cache.clear()
    urls = []
    def fake(url):
        urls.append(url)
        return {'success': True, 'result': {'total': 1, 'records': [{'scientificName': 'Test specimen','_id':1,'year':'1890'}]}}
    monkeypatch.setattr(v14, '_fetch_json', fake)
    c=_client()
    first=c.get('/api/world-sources/search?provider=nhm&q=fossil').json()
    second=c.get('/api/world-sources/search?provider=nhm&q=fossil').json()
    assert first['shown'] == 1 and second['cached'] is True
    assert len(urls) == 1 and urls[0].startswith('https://data.nhm.ac.uk/is/api/3/')
    assert 'resource_id=' in urls[0]


def test_offline_source_not_faked(monkeypatch):
    v14._cache.clear()
    monkeypatch.setattr(v14, '_fetch_json', lambda url: (_ for _ in ()).throw(OSError('offline')))
    r=v14.search_provider('nhm','unknown species')
    assert r['unavailable'] is True and r['items'] == []
    assert r['matched_total'] == 0


def test_official_record_saved_private_and_idempotent_per_account(env):
    """Source item is server-side cached; client cannot submit arbitrary data/URLs."""
    import time
    alice, bob, visitor = env
    # V14 works with the current schema; when run against a pre-V10 local fixture,
    # add missing columns to exercise the V14 module in isolation.
    app = alice.app
    endpoint = next(route.endpoint for route in app.routes if getattr(route,'path','')=='/api/exhibits')
    with endpoint.__globals__['db']() as db:
        columns={r['name'] for r in db.execute('PRAGMA table_info(exhibits)')}
        for name,decl in [('series',"TEXT NOT NULL DEFAULT '民间奇趣'"),('domain',"TEXT NOT NULL DEFAULT '其他'"),
                          ('time_bucket',"TEXT NOT NULL DEFAULT '时间不详'"),('time_basis',"TEXT NOT NULL DEFAULT '不详'"),
                          ('time_note',"TEXT NOT NULL DEFAULT ''")]:
            if name not in columns: db.execute('ALTER TABLE exhibits ADD COLUMN '+name+' '+decl)
    v14._cache.clear()
    record=v14.safe_nhm_record({'_id': 235612, 'scientificName':'Lepidoptera sp.', 'year':'1890', 'family':'Nymphalidae'})
    v14._cache[('nhm','butterfly',8)] = (time.monotonic(),{'items':[record],'unavailable':False})
    assert visitor.post('/api/world-sources/save',json={'object_id':record['id']}).status_code==401
    first=alice.post('/api/world-sources/save',json={'object_id':record['id']})
    assert first.status_code==201,first.text
    assert first.json()['visibility']=='private'
    assert alice.post('/api/world-sources/save',json={'object_id':record['id']}).json()['already_saved'] is True
    own=alice.get('/api/my/exhibits').json()
    assert len(own)==1 and own[0]['title']=='Lepidoptera sp.'
    assert own[0]['series']=='藏品系列'
    assert own[0]['domain']=='自然史与化石'
    assert own[0]['image_url']==''
    assert '不是化石形成时间' in own[0]['time_note']
    assert bob.get('/api/my/exhibits').json()==[]
    assert visitor.get('/api/feed').json()['items']==[]
    assert alice.post('/api/world-sources/save',json={'object_id':'met:evil'}).status_code==404
    second=bob.post('/api/world-sources/save',json={'object_id':record['id']})
    assert second.status_code==201 and second.json()['already_saved'] is False