"""Compare chooser order/colors/badges with actual Meal Groups mobile rows."""
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import state,definitions,compose
fixture.HOOK+='''window.highlightTest={
 prepare:(tabs,active)=>{meals.find(m=>m.id===2).rotation=false;meals.find(m=>m.id===11).rotation=false;for(const m of meals.filter(m=>m.cat==='Rice'))m.name='Rice recipe '+m.id;const lunch=mealPlans.find(p=>p.id==='lunch');lunch.weekdayCategories={Wednesday:['Rice'],Thursday:['Sides']};lunch.weekdayMealOverrides={'Wednesday::Rice':'3','Thursday::Sides':'12'};lunch.cycleRetainedSlots={...lunch.weekdayMealOverrides};showMealPlanTabs=tabs;persist();saveActiveMealPlan();if(active!==activePlanId)loadMealPlan(active);renderList()},
 groups:()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);renderList()},
 my:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(false);renderList()},
 open:()=>{const day=activePlanId==='original'?'Tuesday':'Wednesday';const current=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat==='Rice');openWeekdayMealChooser(day,'Rice',current.meal)},
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
def compare(p):
 d=chooser(p);expected=master(p);actual=choose_rows(d)
 for cat,rows in expected.items():
  assert [r['id'] for r in actual[cat]]==[r['id'] for r in rows],(cat,actual[cat],rows)
  for a,b in zip(actual[cat],rows):
   assert a['days']==b['days'] and a['title']==b['title'],(a,b)
   assert a['color']==b['color'] if b['days'] else a['color']=='rgb(255, 255, 255)',(a,b)
 return actual

def run(browser,filename,width,tabs,active):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_default_timeout(8000);p.evaluate('([tabs,active])=>highlightTest.prepare(tabs,active)',[tabs,active]);p.evaluate('slotTest.seed()');base=state(p)
 p.evaluate('highlightTest.groups()');expected=master(p)
 assert [r['id'] for r in expected['Rice']]==['1','3','2']
 byid={r['id']:r for rows in expected.values() for r in rows}
 assert byid['1']['days']==('TUE · FRI' if tabs or active=='original' else '')
 assert byid['3']['days']==('WED' if tabs or active=='lunch' else '')
 if byid['1']['days']:assert byid['1']['color']=='rgb(209, 222, 192)' and 'Dinner' in byid['1']['title']
 if byid['3']['days']:assert byid['3']['color']=='rgb(246, 222, 170)' and 'Lunch' in byid['3']['title']
 p.evaluate('highlightTest.open()');d=chooser(p);expand(d);compare(p)
 storage=p.evaluate('slotTest.storage()');schedule=compose(p)
 # The temporary selection never overrides scheduled weekday colors.
 d.locator('[data-meal-id="2"]').tap();compare(p)
 r=d.locator('[data-meal-id="2"]');assert r.get_attribute('aria-pressed')=='true' and r.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
 assert r.evaluate('(e)=>getComputedStyle(e).borderTopWidth')=='0px'
 selected=d.locator('[data-meal-id="1"]')
 assert d.locator('.weekday-meal-choice').evaluate_all('(rows)=>rows.every(e=>getComputedStyle(e).padding==="5px 8px")')
 assert selected.evaluate('(e)=>{const x=e.getBoundingClientRect().x;return [...e.querySelectorAll("span")].every(text=>Math.abs(text.getBoundingClientRect().x-x-8)<1)}')
 assert selected.evaluate('(e)=>getComputedStyle(e).borderRadius')=='8px'
 line=selected.evaluate('(e)=>{const s=getComputedStyle(e,"::after");return {left:s.left,right:s.right,height:s.height,radius:s.borderRadius,color:s.backgroundColor}}')
 assert line=={'left':'0px','right':'0px','height':'1px','radius':'0px','color':'rgb(238, 238, 238)'},line
 assert selected.evaluate('(e)=>getComputedStyle(e).borderWidth')=='0px'

 d.locator('[data-meal-id="3"]').tap();compare(p)
 assert d.locator('[data-meal-id="3"]').get_attribute('aria-pressed')=='true'
 d.get_by_role('button',name='Search recipes',exact=True).tap();search=d.get_by_role('searchbox');search.fill('recipe rice')
 assert d.locator('.weekday-meal-choice').evaluate_all('(es)=>es.map(e=>e.dataset.mealId)')==['1','3','2']
 for item in d.locator('.weekday-meal-choice').all():
  exp=byid[item.get_attribute('data-meal-id')]
  assert item.evaluate('(e)=>getComputedStyle(e).backgroundColor')==(exp['color'] if exp['days'] else 'rgb(255, 255, 255)')
 search.fill('');compare(p);d.get_by_role('button',name='Cancel',exact=True).tap()
 assert compose(p)==schedule and p.evaluate('slotTest.storage()')==storage and definitions(state(p))==definitions(base)
 # Use the actual Meal Groups Up action. The chooser must follow its manual order.
 card=p.locator('#list .master-category-card[data-category=Rice]');card.locator('.master-category-meal[data-meal-id="3"] .move').first.tap()
 expected=master(p);assert [r['id'] for r in expected['Rice']]==['3','1','2']
 p.evaluate('highlightTest.open()');d=chooser(p);expand(d);compare(p);d.locator('[data-meal-id="2"]').tap()
 # A live visibility/schedule update re-renders the chooser without losing the pending pick.
 p.evaluate('highlightTest.tabs',not tabs);p.wait_for_timeout(150);compare(p)
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

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:
     for active in ['original','lunch']:run(b,filename,width,tabs,active)
   for tabs in [True,False]:occasional(b,filename,tabs)
  b.close()
