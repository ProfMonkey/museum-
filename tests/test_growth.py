"""V8 annual growth: only truthful data from authenticated member records."""
from datetime import datetime, timezone
from test_multiuser import env, item


def current_year():
    return datetime.now(timezone.utc).year


def test_private_growth_and_truthful_empty_year(env):
    alice, bob, visitor = env
    year = current_year()
    assert visitor.get('/api/growth/overview').status_code == 401
    empty = alice.get(f'/api/growth/overview?year={year}').json()
    assert empty['year']==year
    assert empty['stats']['exhibits']==0
    assert empty['stats']['first_views']==0
    assert empty['stats']['films']==0
    assert empty['film_items']==[]
    assert empty['milestone_total'] >= 1  # account creation + starter hall
    assert alice.get(f'/api/growth/overview?year={year+1}').status_code==422
    assert alice.get(f'/api/growth/overview?year=1999').status_code==422
    assert alice.get(f'/api/growth/overview?year=2000').status_code==422
    # A different authenticated user also sees only their own records.
    assert bob.get(f'/api/growth/overview?year={year}').json()['stats']['exhibits']==0


def test_growth_creations_visits_and_annual_reel_reuses_existing_storage(env):
    a,b,visitor=env
    y=current_year()
    own=a.post('/api/exhibits',json=item(title='我的黄金藏品',category='古董与珠宝',visibility='private')).json()['id']
    public=b.post('/api/exhibits',json=item(title='来自另一座博物馆的画作',category='绘画与书画')).json()['id']
    assert a.get('/api/exhibits/'+str(public)).status_code==200
    data=a.get(f'/api/growth/overview?year={y}').json()
    assert data['stats']['exhibits']==1
    assert data['stats']['first_views']==0  # Reading alone does not track
    assert data['categories']==[{'name':'古董与珠宝','count':1}]
    assert [x['id'] for x in data['film_items']]==[own]
    assert a.post('/api/memories/seen/'+str(public)).status_code==200
    data=a.get(f'/api/growth/overview?year={y}').json()
    assert data['stats']['first_views']==1
    assert {x['id'] for x in data['film_items']}=={own,public}
    assert all(x['memory_date'].startswith(str(y)) for x in data['film_items'])
    assert b.get(f'/api/growth/overview?year={y}').json()['stats']['first_views']==0
    # The annual editor calls the existing /memories/reels endpoint, not a duplicate film store.
    film=a.post('/api/memories/reels',json={'title':f'{y} · 我的世界回忆','exhibit_ids':[own,public],'music':'piano'})
    assert film.status_code==201, film.text
    assert a.get(f'/api/growth/overview?year={y}').json()['stats']['films']==1
    assert len(a.get('/api/memories/reels').json())==1
    assert b.get('/api/memories/reels').json()==[]


def test_growth_does_not_leak_others_revoked_or_deleted_content(env):
    a,b,visitor=env
    year=current_year()
    shared=b.post('/api/exhibits',json=item(title='曾经公开的珍贵藏品')).json()['id']
    private=b.post('/api/exhibits',json=item(title='永远私密的日记',visibility='private')).json()['id']
    assert a.post('/api/memories/seen/'+str(shared)).status_code==200
    assert a.post('/api/memories/seen/'+str(private)).status_code==404
    assert shared in [x['id'] for x in a.get(f'/api/growth/overview?year={year}').json()['film_items']]
    assert b.patch('/api/exhibits/'+str(shared),json={'title':'曾经公开的珍贵藏品','visibility':'private'}).status_code==200
    result=a.get(f'/api/growth/overview?year={year}').json()
    assert shared not in [x['id'] for x in result['film_items']]
    assert not any('曾经公开的珍贵藏品' in m['title'] for m in result['milestones'])
    assert all(private!=x['id'] for x in result['film_items'])
    # This is a scoped statistic about A's own history, not other users' archive content.
    assert result['stats']['exhibits']==0


def test_month_counts_and_saved_exploration_routes_are_not_fake(env):
    a,b,visitor=env
    y=current_year()
    start=a.get(f'/api/growth/overview?year={y}').json()
    assert start['stats']['routes']==0
    e=a.post('/api/exhibits',json=item(title='开拓古今未来')).json()
    now_month=datetime.now(timezone.utc).month
    result=a.get(f'/api/growth/overview?year={y}').json()
    month=result['monthly'][now_month-1]
    assert month['exhibits']==1
    assert result['stats']['active_months']>=1
    assert result['stats']['routes']==0
    # Counts of bookmarks should not be assigned a fake date (they lack timestamps).
    assert a.post(f'/api/exhibits/{e["id"]}/bookmark').status_code==200
    later=a.get(f'/api/growth/overview?year={y}').json()
    assert later['stats']==result['stats']