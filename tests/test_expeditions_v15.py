from datetime import date
"""V15 official archive routes, safe transformations, private collection."""
import pytest
import expeditions_v15 as e
from test_multiuser import env


NASA_ITEM={'data':[{'nasa_id':'GSFC_2026_0001','title':'Earth from orbit','media_type':'image',
                    'description':'View of the Earth','date_created':'2024-10-21T16:02:00Z',
                    'center':'Goddard','keywords':['Earth','orbit']}],
           'links':[{'href':'https://images-assets.nasa.gov/123.jpg','render':'image'}]}
LOC_ITEM={'id':'http://www.loc.gov/item/2014717546/','title':'Telegraph apparatus in 1900',
          'description':['Historic telegraph device.'],'date':'1900','creator':['Archive photographer'],
          'image_url':['https://tile.loc.gov/123.jpg']}

@pytest.fixture(autouse=True)
def clear_cache():
    e._cache.clear()
    e._last_call.update({'nasa':0.0,'loc':0.0})
    yield
    e._cache.clear()


def test_routes_are_real_source_queries_and_not_fabricated():
    response=e.catalog()
    assert len(response['routes'])==6
    assert all(len(route['steps'])==3 for route in response['routes'])
    assert {s['provider'] for r in response['routes'] for s in r['steps']}=={'met','nhm','loc','nasa'}
    assert '历史因果' in response['notice']
    for r in response['routes']:
        for s in r['steps']:
            assert s['query']
            assert s['source_url'].startswith('https://')


def test_nasa_records_preserve_date_and_hide_unverified_images():
    r=e.nasa_record(NASA_ITEM)
    assert r['source_url']=='https://images.nasa.gov/details/GSFC_2026_0001'
    assert r['title']=='Earth from orbit'
    assert r['image_url']=='' and r['license_verified_for_image'] is False
    assert '2024-10-21' in r['date_note']
    assert r['time_basis']=='制作/创作'
    assert e.nasa_record({'data':[{'nasa_id':'../evil','media_type':'image','title':'bad'}]}) is None
    assert e.nasa_record({'data':[{'nasa_id':'REAL','media_type':'video','title':'video'}]}) is None


def test_loc_sanitizes_http_records_and_refuses_other_domains():
    r=e.loc_record(LOC_ITEM)
    assert r['source_url']=='https://www.loc.gov/item/2014717546/'
    assert r['description']=='Historic telegraph device.'
    assert r['image_url']==''
    assert e.loc_record({**LOC_ITEM,'id':'https://not-loc.gov/item/2014717546/'}) is None
    assert e.loc_record({**LOC_ITEM,'id':'https://www.loc.gov/search/?q=foo'}) is None


def test_official_search_parsing_limits_and_no_real_network(monkeypatch):
    called=[]
    def fake(url):
        called.append(url)
        if url.startswith(e.NASA_ENDPOINT):
            return {'collection':{'items':[NASA_ITEM],'metadata':{'total_hits':77}}}
        if url.startswith(e.LOC_ENDPOINT):
            return {'results':[LOC_ITEM],'pagination':{'total':22}}
        raise AssertionError('unexpected endpoint')
    monkeypatch.setattr(e,'_fetch_json',fake)
    nasa=e.search('nasa','Earth orbit',limit=2)
    assert len(nasa['items'])==1 and nasa['matched_total']==77
    assert nasa['unavailable'] is False
    again=e.search('nasa','Earth orbit',limit=2)
    assert again['cached'] is True
    loc=e.search('loc','telegraph',limit=3)
    assert loc['matched_total']==22 and loc['items'][0]['provider']=='loc'
    assert len(called)==2
    assert all(x.startswith('https://') for x in called)
    with pytest.raises(ValueError): e.search('other','wormhole')
    with pytest.raises(ValueError): e.search('nasa','a')


def test_throttle_blocks_rapid_unique_queries(monkeypatch):
    monkeypatch.setattr(e,'_fetch_json',lambda url:{'collection':{'items':[],'metadata':{'total_hits':0}}})
    assert e.search('nasa','spacecraft')['unavailable'] is False
    outcome=e.search('nasa','moon lander')
    assert outcome['unavailable'] and outcome['limited']


def test_network_failures_return_no_fabricated_records(monkeypatch):
    monkeypatch.setattr(e,'_fetch_json',lambda url: (_ for _ in ()).throw(TimeoutError('timeout')))
    response=e.search('loc','computers')
    assert response['unavailable'] and response['items']==[]
    assert e.search('loc','computers')['cached'] is True


def test_private_save_requires_search_and_isolated_by_user(monkeypatch,env):
    alice,bob,anon=env
    assert anon.get('/api/expeditions/catalog').status_code==200
    assert anon.post('/api/expeditions/save',json={'record_id':'nasa:GSFC_2026_0001'}).status_code==401
    assert alice.post('/api/expeditions/save',json={'record_id':'nasa:GSFC_2026_0001'}).status_code==404
    monkeypatch.setattr(e,'_fetch_json',lambda url:{'collection':{'items':[NASA_ITEM],'metadata':{'total_hits':1}}})
    outcome=anon.get('/api/expeditions/search',params={'provider':'nasa','q':'Earth from orbit'})
    assert outcome.status_code==200 and outcome.json()['items'][0]['id']=='nasa:GSFC_2026_0001'
    saved=alice.post('/api/expeditions/save',json={'record_id':'nasa:GSFC_2026_0001'})
    assert saved.status_code==201,saved.text
    assert saved.json()['visibility']=='private'
    again=alice.post('/api/expeditions/save',json={'record_id':'nasa:GSFC_2026_0001'})
    assert again.status_code==201 and again.json()['already_saved'] is True
    separate=bob.post('/api/expeditions/save',json={'record_id':'nasa:GSFC_2026_0001'})
    assert separate.status_code==201 and separate.json()['already_saved'] is False
    one=saved.json()['exhibit_id']; assert one != separate.json()['exhibit_id']
    assert anon.get(f'/api/exhibits/{one}').status_code==404
    assert bob.get(f'/api/exhibits/{one}').status_code==404
    assert alice.get(f'/api/exhibits/{one}').json()['image_url']==''
    assert anon.get('/api/feed').json()['items']==[]


def test_loc_private_save_uses_strict_allowlist(monkeypatch,env):
    alice,bob,anon=env
    monkeypatch.setattr(e,'_fetch_json',lambda url:{'results':[LOC_ITEM],'pagination':{'total':1}})
    assert anon.get('/api/expeditions/search',params={'provider':'loc','q':'telegraph'}).status_code==200
    saved=alice.post('/api/expeditions/save',json={'record_id':'loc:2014717546'})
    assert saved.status_code==201
    raw=alice.get('/api/exhibits/'+str(saved.json()['exhibit_id'])).json()
    assert raw['source_url']=='https://www.loc.gov/item/2014717546/'
    assert raw['visibility']=='private'
    assert raw['image_url']==''
    assert alice.post('/api/expeditions/save',json={'record_id':'loc:../etc/passwd'}).status_code==404


def test_static_expedition_panel_is_available(env):
    client=env[2]
    page=client.get('/')
    assert '/static/expeditions.js' in page.text
    assert '/static/expeditions.css' in page.text
    assert 'WONDER ATLAS · WORLD' in page.text
    assert 'WonderExpeditions?.renderPanel()' in client.get('/static/world-museums.js').text
    assert 'api(\'/expeditions/catalog\')' in client.get('/static/expeditions.js').text


def test_created_media_date_buckets_do_not_guess_geological_time():
    today=date(2026,10,26)
    assert e.dated_bucket('2026-10-20T00:00:00Z',exact_date=True,today=today)=='最近一年'
    assert e.dated_bucket('2023-02-01T00:00:00Z',exact_date=True,today=today)=='近30年'
    assert e.dated_bucket('1890',today=today)=='近千年'
    assert e.dated_bucket('1930',today=today)=='近现代'
    assert e.dated_bucket('2026',today=today)=='时间不详'
    assert e.dated_bucket('2028-01-01',exact_date=True,today=today)=='时间不详'
    assert e.dated_bucket('ca. 1800',today=today)=='时间不详'