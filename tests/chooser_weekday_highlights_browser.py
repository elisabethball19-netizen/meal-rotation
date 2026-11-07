"""Compare chooser order/colors/badges with actual Meal Groups mobile rows."""
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import state,definitions,compose
fixture.HOOK+='''window.highlightTest={
 prepare:(tabs,active)=>{meals.find(m=>m.id===2).rotation=false;meals.find(m=>m.id===11).rotation=false;for(const m of meals.filter(m=>m.cat==='Rice'))m.name='Rice recipe '+m.id;const lunch=mealPlans.find(p=>p.id==='lunch');lunch.weekdayCategories={Wednesday:['Rice'],Thursday:['Sides']};lunch.weekdayMealOverrides={'Wednesday::Rice':'3','Thursday::Sides':'12'};lunch.cycleRetainedSlots={...lunch.weekdayMealOverrides};showMealPlanTabs=tabs;localStorage.setItem('mealRotationShowPlanTabsV1',String(tabs));persist();saveActiveMealPlan();if(active!==activePlanId)loadMealPlan(active);renderList()},
 manual:()=>{manualRecipeOrdering=true;saveManualRecipeOrdering();renderList()},
 groups:()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);renderList()},
 my:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(false);renderList()},
 open:()=>{const day=activePlanId==='original'?'Tuesday':'Wednesday';const current=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat==='Rice');openWeekdayMealChooser(day,'Rice',current.meal)},
 friday:()=>{meals.find(m=>m.id===2).name='Carne Asada';persist();const current=getDisplayedWeekdayMeals().find(x=>x.day==='Friday'&&x.cat==='Rice');openWeekdayMealChooser('Friday','Rice',current.meal)},
 empty:()=>openWeekdayMealChooser('Monday',null,null,true),
 data:()=>({planId:activePlanId,day:activePlanId==='original'?'Tuesday':'Wednesday',days:orderedDays(),colors:Object.fromEntries(orderedDays().map(day=>[day,colorForDay(day)])),entries:scheduledRecipeHighlights().scheduledEntries.map(x=>({id:String(x.meal.id),day:x.day,cat:x.cat,planId:x.planId,planName:x.planName}))}),
 tabs:value=>{showMealPlanTabs=value;renderList()},
 once:()=>{const plan=mealPlans.find(p=>p.id===activePlanId);plan.occasionalMeals={Monday:'2'};saveActiveMealPlan();renderList()},
 schedule:()=>{const day=activePlanId==='original'?'Tuesday':'Wednesday';applyManualWeekdayMeal(day,'Rice',meals.find(m=>m.id===2))}
};'''
def master(p):
 return p.locator('#list .master-category-card[data-category]').evaluate_all('''cards=>Object.fromEntries(cards.map(card=>[card.dataset.category,[...card.querySelectorAll('.master-category-meal')].map(row=>({id:row.dataset.mealId,color:getComputedStyle(row).backgroundColor,days:row.querySelector('.master-meal-weekdays')?.textContent||'',title:row.querySelector('.master-meal-weekdays')?.title||''}))]))''')
def chooser(p):return p.locator('.weekday-meal-picker')
def choose_rows(d):
 return d.locator('[data-group]').evaluate_all('''cards=>Object.fromEntries(cards.map(card=>[card.dataset.group,[...card.querySelectorAll('.weekday-meal-choice')].map(row=>({id:row.dataset.mealId,color:getComputedStyle(row).backgroundColor,days:row.querySelector('.master-meal-weekdays')?.textContent||'',title:row.querySelector('.master-meal-weekdays')?.title||''}))]))''')
def expand(d):
 while d.locator('.master-category-title[aria-expanded=false]').count():d.locator('.master-category-title[aria-expanded=false]').first.tap()
def compare(p,pending=None):
 d=chooser(p);expected=master(p);actual=choose_rows(d);data=p.evaluate('highlightTest.data()');entries=data['entries']
 if pending is not None:
  # Expected UI: move only this plan's edited weekday; keep every other occurrence.
  entries=[dict(e,id=str(pending)) if e['planId']==data['planId'] and e['day']==data['day'] and e['cat']=='Rice' else e for e in entries]
 for cat,rows in expected.items():
  assert [r['id'] for r in actual[cat]]==[r['id'] for r in rows],(cat,actual[cat],rows)
  for a,b in zip(actual[cat],rows):
   used=[e for e in entries if e['id']==a['id']];days=[day for day in data['days'] if any(e['day']==day for e in used)]
   assert a['days']==' · '.join(day[:3].upper() for day in days),(a,days)
   if used:
    color=data['colors'][used[0]['day']];rgb=tuple(int(color[n:n+2],16) for n in (1,3,5));want='rgb'+str(rgb)
   else:want='rgb(255, 255, 255)'
   assert a['color']==want,(a,want)
   if pending is None:
    visible=[e for e in used if e['planId']==data['planId']]
    visible_days=[day for day in data['days'] if any(e['day']==day for e in visible)]
    assert b['days']==' · '.join(day[:3].upper() for day in visible_days),(b,visible_days)
    assert all(e['planName'] in b['title'] for e in visible),(b,visible)
    assert bool(b['title'])==bool(visible),(b,visible)
 return actual

def run(browser,filename,width,tabs,active):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_default_timeout(8000);p.evaluate('([tabs,active])=>highlightTest.prepare(tabs,active)',[tabs,active]);p.evaluate('slotTest.seed()');base=state(p)
 p.evaluate('highlightTest.groups()');expected=master(p)
 assert [r['id'] for r in expected['Rice']]==(['3','1','2'] if not tabs and active=='lunch' else ['1','3','2'])
 byid={r['id']:r for rows in expected.values() for r in rows}
 assert byid['1']['days']==('TUE · FRI' if active=='original' else '')
 assert byid['3']['days']==('WED' if active=='lunch' else '')
 if byid['1']['days']:assert byid['1']['color']=='rgb(209, 222, 192)' and 'Dinner' in byid['1']['title']
 if byid['3']['days']:assert byid['3']['color']=='rgb(246, 222, 170)' and 'Lunch' in byid['3']['title']
 p.evaluate('highlightTest.open()');d=chooser(p);expand(d);compare(p)
 storage=p.evaluate('slotTest.storage()');schedule=compose(p)
 # Pending choices immediately move only the edited weekday color/badge.
 d.locator('[data-meal-id="2"]').tap();compare(p,2)
 r=d.locator('[data-meal-id="2"]');assert r.get_attribute('aria-pressed')=='true' and ('TUE' if active=='original' else 'WED') in r.locator('.master-meal-weekdays').inner_text()
 assert r.evaluate('(e)=>getComputedStyle(e).borderTopWidth')=='0px'
 selected=d.locator('[data-meal-id="1"]')
 assert d.locator('.weekday-meal-choice').evaluate_all('(rows)=>rows.every(e=>(getComputedStyle(e).padding===((e.querySelector(".master-meal-weekdays"))?"5px 8px 5px 13px":"5px 8px")))')
 assert selected.evaluate('(e)=>{const x=e.getBoundingClientRect().x;return [...e.querySelectorAll("span")].every(text=>Math.abs(text.getBoundingClientRect().x-x-parseFloat(getComputedStyle(e).paddingLeft))<1)}')
 assert selected.evaluate('(e)=>getComputedStyle(e).borderRadius')=='8px'
 line=selected.evaluate('(e)=>{const s=getComputedStyle(e,"::after");return {left:s.left,right:s.right,height:s.height,radius:s.borderRadius,color:s.backgroundColor}}')
 assert line=={'left':'0px','right':'0px','height':'1px','radius':'0px','color':'rgb(238, 238, 238)'},line
 assert selected.evaluate('(e)=>getComputedStyle(e).borderWidth')=='0px'

 d.locator('[data-meal-id="3"]').tap();compare(p,3)
 assert d.locator('[data-meal-id="3"]').get_attribute('aria-pressed')=='true'
 d.get_by_role('button',name='Search recipes',exact=True).tap();search=d.get_by_role('searchbox');search.fill('recipe rice')
 assert d.locator('.weekday-meal-choice').evaluate_all('(es)=>es.map(e=>e.dataset.mealId)')==[r['id'] for r in expected['Rice']]
 # Search must keep the same pending weekday feedback as grouped rows.
 row=d.locator('[data-meal-id="3"]');assert ('TUE' if active=='original' else 'WED') in row.locator('.master-meal-weekdays').inner_text()
 search.fill('');compare(p,3);d.get_by_role('button',name='Cancel',exact=True).tap()
 assert compose(p)==schedule and p.evaluate('slotTest.storage()')==storage and definitions(state(p))==definitions(base)
 # Use the actual Meal Groups Up action. The chooser must follow its manual order.
 p.evaluate('highlightTest.manual()')
 card=p.locator('#list .master-category-card[data-category=Rice]');card.locator('.master-category-meal[data-meal-id="3"] .move').first.tap()
 expected=master(p);assert [r['id'] for r in expected['Rice']]==['3','1','2']
 p.evaluate('highlightTest.open()');d=chooser(p);expand(d);compare(p);d.locator('[data-meal-id="2"]').tap()
 # A live visibility/schedule update re-renders the chooser without losing the pending pick.
 p.evaluate('highlightTest.tabs',not tabs);p.wait_for_timeout(150);compare(p,2)
 assert d.locator('[data-meal-id="2"]').get_attribute('aria-pressed')=='true'
 p.evaluate('highlightTest.schedule()');p.wait_for_timeout(150);actual=compare(p)
 assert next(r for r in actual['Rice'] if r['id']=='2')['days']
 assert d.locator('[data-meal-id="2"]').get_attribute('aria-pressed')=='true'
 assert d.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 for row in d.locator('.weekday-meal-choice').all():assert row.bounding_box()['height']>=44
 if filename.startswith('meal-') and width==360 and tabs and active=='original':p.screenshot(path='/tmp/chooser-weekday-highlights.png')
 d.get_by_role('button',name='Cancel',exact=True).tap()
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,tabs,active,'actual Meal Groups order/color/badge parity, manual Up, multi-day labels, search, borderless selection, live visibility/schedule refresh and cancel',flush=True);ctx.close()
def occasional(browser,filename,tabs):
 ctx,p,errors,_=fixture.setup(browser,filename,320,linked=True,duplicate=True,multi=True);p.evaluate('([tabs,active])=>highlightTest.prepare(tabs,active)',[tabs,'original']);p.evaluate('highlightTest.once()');p.evaluate('highlightTest.groups()');before=p.evaluate('slotTest.storage()');expected=master(p)
 p.evaluate('highlightTest.open()');d=chooser(p);expand(d);actual=compare(p);row=d.locator('[data-meal-id="2"]')
 assert row.locator('.master-meal-weekdays').inner_text()=='MON' and row.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(209, 220, 234)'
 assert [r['id'] for r in actual['Rice']]==['1','3','2']
 row.tap();assert row.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(209, 220, 234)'
 d.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('slotTest.storage()')==before and not errors,errors
 print('PASS',filename,320,tabs,'scheduled one-time Idea uses weekday color/badge without changing tier order or data',flush=True);ctx.close()

def feedback(browser,filename,width,tabs):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.evaluate('([tabs,active])=>highlightTest.prepare(tabs,active)',[tabs,'original']);p.evaluate('highlightTest.groups()');p.evaluate('highlightTest.friday()');d=chooser(p);expand(d)
 saved=p.evaluate('slotTest.storage()');before=compose(p)
 def row(id):return d.locator('[data-meal-id="'+str(id)+'"]')
 def days(id):return row(id).locator('.master-meal-weekdays').inner_text() if row(id).locator('.master-meal-weekdays').count() else ''
 for id in [2,3,2,1,2]:
  row(id).tap();assert row(id).get_attribute('aria-pressed')=='true'
  assert 'FRI' in days(id)
  if id!=1:assert days(1)=='TUE' and row(1).evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(209, 222, 192)'
  if id==2:assert row(2).evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(237, 194, 179)' and days(3)==('WED' if tabs else '')
  if id==3:assert days(3)==('WED · FRI' if tabs else 'FRI') and days(2)==''
  assert p.evaluate('slotTest.storage()')==saved and compose(p)==before
 d.get_by_role('button',name='Search recipes',exact=True).tap();d.get_by_role('searchbox').fill('carne asada');assert days(2)=='FRI';d.get_by_role('searchbox').fill('');expand(d)
 assert d.locator('.weekday-meal-choice').evaluate_all('(es)=>es.every(e=>(getComputedStyle(e).padding===((e.querySelector(".master-meal-weekdays"))?"5px 8px 5px 13px":"5px 8px"))&&getComputedStyle(e).borderWidth==="0px")')
 if filename.startswith('meal-') and width==360 and tabs:p.screenshot(path='/tmp/chooser-selection-friday.png')
 d.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('slotTest.storage()')==saved and compose(p)==before
 # Save still commits only on the checkmark, and survives reopening/reload.
 p.evaluate('highlightTest.friday()');d=chooser(p);expand(d);row(2).tap();d.get_by_role('button',name='Save',exact=True).tap()
 assert next(r for r in p.evaluate('slotTest.rows()') if r['planId']=='original' and r['day']=='Friday' and r['cat']=='Rice')['id']==2
 p.reload();p.evaluate('highlightTest.groups()');p.evaluate('highlightTest.friday()');d=chooser(p);expand(d);assert days(2)=='FRI';saved=p.evaluate('slotTest.storage()')
 # A duplicate prompt's X cancels the new pick and restores the original visual choice.
 row(1).tap();assert days(1)=='TUE · FRI' and days(2)==''
 d.get_by_role('button',name='Save',exact=True).tap();p.get_by_role('dialog',name='Rice recipe 1 is already planned',exact=True).get_by_role('button',name='Close',exact=True).tap()
 assert row(2).get_attribute('aria-pressed')=='true' and days(2)=='FRI' and days(1)=='TUE'
 assert p.evaluate('slotTest.storage()')==saved;d.get_by_role('button',name='Cancel',exact=True).tap()
 # A new one-time meal uses Monday's existing color and all other day badges stay intact.
 p.evaluate('highlightTest.empty()');d=chooser(p);expand(d);saved=p.evaluate('slotTest.storage()');row(1).tap();assert days(1)=='MON · TUE' and row(1).evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(209, 220, 234)'
 row(3).tap();assert days(1)=='TUE' and days(3)==('MON · WED' if tabs else 'MON');d.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('slotTest.storage()')==saved
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,tabs,'Friday repeated choices, other-day highlights, search, unchanged styles/data, Save/reload, duplicate prompt X reset, empty one-time preview',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:
     for active in ['original','lunch']:run(b,filename,width,tabs,active)
   for tabs in [True,False]:occasional(b,filename,tabs)
   for width in [320,360]:
    for tabs in [True,False]:feedback(b,filename,width,tabs)
  b.close()
