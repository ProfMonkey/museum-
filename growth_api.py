"""Private world growth history, derived from actual member-owned data.

Does not store new browsing events or infer activity from another member's account.
The annual film selection is read-only: existing memory reels handle persistence.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import Depends, Query


def mount_growth(app, db, read_exhibit, require_user, now, fail):
    def excerpt(c, exhibit_id, user):
        try:
            return read_exhibit(c, exhibit_id, user)
        except Exception as exc:
            if getattr(exc, 'status_code', None) == 404:
                return None
            raise

    @app.get('/api/growth/overview')
    def overview(year: int = Query(None, ge=2000, le=2100), user=Depends(require_user)):
        current_year = datetime.now(timezone.utc).year
        if year is None:
            year = current_year
        if year > current_year:
            fail(422, '不能生成未来年度报告')
        start, end = f'{year}-01-01', f'{year+1}-01-01'
        user_id = user['id']
        with db() as c:
            registered = c.execute('SELECT created_at FROM users WHERE id=?', (user_id,)).fetchone()
            if not registered:
                fail(401, '账号已失效')
            if year < int(registered['created_at'][:4]):
                fail(422, '所选年份早于账号建立时间')
            # Each of these events has a persisted timestamp and belongs to the current user.
            exhibits = c.execute('''SELECT id,title,category,created_at,visibility FROM exhibits
                WHERE user_id=? AND created_at>=? AND created_at<?
                ORDER BY created_at,id''', (user_id,start,end)).fetchall()
            halls = c.execute('''SELECT id,name,created_at FROM halls
                WHERE user_id=? AND created_at>=? AND created_at<?
                ORDER BY created_at,id''',(user_id,start,end)).fetchall()
            first_views = c.execute('''SELECT exhibit_id,first_at,views FROM memory_views
                WHERE user_id=? AND first_at>=? AND first_at<?
                ORDER BY first_at,exhibit_id''',(user_id,start,end)).fetchall()
            films = c.execute('''SELECT id,title,created_at FROM memory_reels
                WHERE user_id=? AND created_at>=? AND created_at<?
                ORDER BY created_at,id''',(user_id,start,end)).fetchall()
            routes = c.execute('''SELECT id,title,created_at FROM atlas_saved_routes
                WHERE user_id=? AND created_at>=? AND created_at<?
                ORDER BY created_at,id''',(user_id,start,end)).fetchall()
            # Bookmarks are intentionally excluded: they have no timestamp in this schema.
            monthly = {str(m).zfill(2): {'month':m,'exhibits':0,'halls':0,'first_views':0,'films':0,'routes':0}
                       for m in range(1,13)}
            events = []
            first = registered['created_at']
            if first.startswith(str(year)):
                events.append({'at':first,'type':'joined','title':'你的世界开始了','detail':'创建了万物博物馆账号'})
            categories = Counter()
            for r in exhibits:
                monthly[r['created_at'][5:7]]['exhibits'] += 1
                categories[r['category']] += 1
                events.append({'at':r['created_at'],'type':'exhibit','title':'收藏了「'+r['title']+'」','detail':'一件属于自己的展品','exhibit_id':r['id']})
            for r in halls:
                monthly[r['created_at'][5:7]]['halls'] += 1
                events.append({'at':r['created_at'],'type':'hall','title':'开设展厅「'+r['name']+'」','detail':'世界中多了一间展厅'})
            # Viewing history is opt-in and only records first/last dates, not all dates.
            # We only count first-ever recorded visits for this year, never invent intermediate visits.
            candidate_dates = {}
            for r in first_views:
                monthly[r['first_at'][5:7]]['first_views'] += 1
                item = excerpt(c, r['exhibit_id'], user)
                if item:
                    candidate_dates.setdefault(r['exhibit_id'],r['first_at'])
                    events.append({'at':r['first_at'],'type':'visit','title':'第一次遇见「'+item['title']+'」','detail':'主动记录的观看足迹','exhibit_id':r['exhibit_id']})
            for r in films:
                monthly[r['created_at'][5:7]]['films'] += 1
                events.append({'at':r['created_at'],'type':'film','title':'剪辑影片「'+r['title']+'」','detail':'一部自己的回忆电影'})
            for r in routes:
                monthly[r['created_at'][5:7]]['routes'] += 1
                events.append({'at':r['created_at'],'type':'route','title':'保存路线「'+r['title']+'」','detail':'沿万物之间的联系继续出发'})
            for r in exhibits:
                candidate_dates[r['id']] = min(candidate_dates.get(r['id'],r['created_at']),r['created_at'])
            # Only include items currently accessible to this account. For other users'
            # exhibits, revoking public visibility must immediately remove it from output.
            reel_candidates=[]
            for exhibit_id, at in sorted(candidate_dates.items(),key=lambda x:(x[1],x[0])):
                item=excerpt(c, exhibit_id, user)
                if item:
                    reel_candidates.append({**item,'memory_date':at[:10]})
                if len(reel_candidates)>=40:
                    break
            events.sort(key=lambda x:(x['at'],x['type']), reverse=True)
            active_months=sum(1 for m in monthly.values() if any(m[k]>0 for k in ('exhibits','halls','first_views','films','routes')))
            return {
                'year':year,'available_years':list(range(current_year,int(first[:4])-1,-1)),
                'stats': {'exhibits':len(exhibits),'halls':len(halls),'first_views':len(first_views),
                    'films':len(films),'routes':len(routes),'active_months':active_months},
                'monthly':list(monthly.values()),
                'categories':[{'name':name,'count':count} for name,count in categories.most_common(8)],
                'milestones':events[:80],
                'milestone_total':len(events),
                'film_items':reel_candidates,
                'methodology':{
                    'created':'展品、展厅、影片和路线按实际创建时间归入年份；后来删除的内容无法计入。',
                    'views':'浏览足迹默认关闭；只计首次主动记录年份，不把跨年累计观看次数当成本年观看量。',
                    'private':'这份报告仅向当前登录用户开放，不会公开他人的私人藏品或已撤回作品。',
                    'film':'影片从本年自己创建或首次主动记录观看的当前可访问展品中选取，最多40幕；没有数据时不虚构回忆。'
                }
            }