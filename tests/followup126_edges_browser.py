"""Focused follow-up ownership, boundary-clock and nested-return cases."""
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import followup126_browser as f126
import followup126_phone_browser as phone
base=phone.base
base.fixture.HOOK+='''window.edge126={
 todo:()=>{follow126.home();const plan=mealPlans[0],entry=getDisplayedWeekdayMealsForPlan(plan)[0],date=n=>{const d=new Date();d.setDate(d.getDate()+n);return cookingLocalDate(d)};renderTodayTodo([[-1,'Overdue task'],[0,'Due today task'],[1,'Future task']].map(([n,description])=>({plan,entry,key:JSON.stringify([rotationOccurrenceKey({...entry,planId:plan.id}),date(1),'',description]),task:{id:description,description,daysBefore:1-n},due:date(7),scheduled:date(1),complete:false})))},
 repeat:()=>{phone126.primaryOnly();phone126.copy();const m=meals.find(m=>m.id===2);m.serveWithEntriesV1=[{id:'veg',type:'rotating',groupIds:[groupIdentity('Potatoes',true)],always:true}];persist();follow126.home();const p=mealPlans[0],entries=getDisplayedWeekdayMealsForPlan(p);return entries.filter(e=>!e.linkedTo&&!e.servingParentId).map(e=>servingSides(p,e,entries)[0].mealId)},
 direct:()=>{const e=getDisplayedWeekdayMealsForPlan(mealPlans[0]).find(e=>e.day==='Wednesday'&&e.meal.id===2);return directServingRecipes(e.meal,cookingContext('original',e.day,e.cat,e.meal)).map(m=>m.id)},
 session:()=>!!servingSideSession
};'''
def run(browser,name):
 c,p,errors,prefix=base.setup(browser,name);p.set_default_timeout(15000)
 # The owning card's unified recipe editor can save a current-only simple side.
 p.evaluate('phone126.editTarget()');serve=p.locator('details[data-editor-section="serve"]');serve.locator('summary').first.click();f126.add_simple(p,serve,'Fresh lime wedges');serve.get_by_role('switch').uncheck();p.locator('#save').click();p.wait_for_timeout(200);assert p.evaluate('follow126.sides()[0].name')=='Fresh lime wedges';assert not p.evaluate('serving126.rules(2).serveWithEntriesV1||[]');assert not p.evaluate('serving126.sides(1).sides')
 # Same flow ON creates a real future default; next-week edit stays on its owner.
 p.evaluate('follow126.seed();phone126.editTarget()');serve=p.locator('details[data-editor-section="serve"]');serve.locator('summary').first.click();f126.add_simple(p,serve,'Lime');assert serve.get_by_role('switch').is_checked();p.locator('#save').click();p.wait_for_timeout(200);assert p.evaluate('serving126.rules(2).serveWithEntriesV1[0].name')=='Lime'
 p.evaluate('follow126.home(1)');card=p.locator('.preview-plan-card[data-meal-id="3"]');card.locator('.meal-actions-toggle').click();card.get_by_role('button',name='Edit recipe',exact=True).click();serve=p.locator('details[data-editor-section="serve"]');serve.locator('summary').first.click();f126.add_simple(p,serve,'Next week garnish');serve.get_by_role('switch').uncheck();p.locator('#save').click();p.wait_for_timeout(200);assert p.evaluate('serving126.sides(1).sides[0].name')=='Next week garnish';assert p.evaluate('follow126.sides()[0].name')=='Lime'
 # Linked scaling follows the frozen serving, not a newer default on another copy.
 p.evaluate('follow126.seed();follow126.rules();phone126.copy()');expected={int(s['mealId']) for s in p.evaluate('phone126.otherSides()') if s['type']!='simple'};p.evaluate("serving126.save([{id:'new',type:'fixed',recipeId:'12',mealId:'12',always:true}])");direct=p.evaluate('edge126.direct()');assert set(direct)==expected,direct
 # Each scheduled serving rotates within a side group, without render advancement.
 p.evaluate('follow126.seed()');choices=p.evaluate('edge126.repeat()');assert choices==['10','11'],choices;assert p.evaluate('edge126.repeat()')==choices
 # Nested viewer Back restores the pending inline editor and its return position.
 p.evaluate('follow126.seed();follow126.rules()');card=p.locator('.plan-meal-card[data-meal-id="2"]');card.locator('.meal-actions-toggle').click();card.get_by_role('button',name='Add or edit sides',exact=True).click();before=p.evaluate('follow126.state()');row=card.locator('.inline-side-row').first;row.locator('.inline-side-name').scroll_into_view_if_needed();return_y=p.evaluate('scrollY');row.locator('.inline-side-name').click();assert p.locator('#recipeViewer').is_visible();p.go_back();p.wait_for_timeout(200);assert abs(p.evaluate('scrollY')-return_y)<3;assert p.evaluate('edge126.session()');row.get_by_role('button',name='Side actions',exact=False).click();row.get_by_role('button',name='Edit recipe',exact=True).click();p.locator('#cancel').click();p.wait_for_timeout(200);assert p.evaluate('edge126.session()');assert card.get_by_role('button',name='Close sides',exact=True).is_visible();card.get_by_role('button',name='Close sides',exact=True).click();p.wait_for_timeout(200);assert p.evaluate('follow126.state()')==before
 # Empty/resume uses the same inline actions in both weeks and persists separately.
 for week,selector in [(0,'.plan-meal-card'),(1,'.preview-plan-card')]:
  p.evaluate('follow126.seed()');p.evaluate('w=>follow126.home(w)',week);card=p.locator(selector+'[data-meal-id="'+str(2 if week==0 else 3)+'"]');card.locator('.meal-actions-toggle').click();card.get_by_role('button',name='Leave this meal empty',exact=True).click();p.wait_for_timeout(200);empty=p.locator(selector+'.empty-plan-card[data-schedule-day="Tuesday"]');assert empty.get_attribute('data-date')==('2026-11-24' if week else '2026-11-17');empty.locator('.meal-actions-toggle').click();resume=p.get_by_role('button',name='Resume planned meal',exact=True);assert resume.count()==1;resume.click();p.wait_for_timeout(200);assert p.locator(selector+'[data-meal-id="'+str(2 if week==0 else 3)+'"]').count()==1
 # Explicitly replacing a reviewed legacy side creates a new source identity.
 p.evaluate('follow126.seed();follow126.legacy();serving126.weekday()');d=p.get_by_role('dialog',name='Choose Tuesday’s meal groups',exact=True);d.get_by_role('radio',name='Main dish Chili-Garlic Broth Bowls',exact=True).check();d.get_by_role('checkbox',name='Keep other listed dishes as sides for this serving',exact=True).check();d.get_by_role('button',name='Save meal groups',exact=True).click();card=p.locator('.plan-meal-card[data-meal-id="2"]');card.locator('.meal-actions-toggle').click();card.get_by_role('button',name='Add or edit sides',exact=True).click();row=card.locator('.inline-side-row').first;f126.open_side(row);row.get_by_role('button',name='Choose a different side',exact=True).click();d=p.get_by_role('dialog',name='Choose a side',exact=True);d.get_by_role('searchbox',name='Search side recipes',exact=True).fill('Green');d.locator('[data-meal-id="12"]').click();d.get_by_role('button',name='Choose this side',exact=True).click();card.get_by_role('button',name='Close sides',exact=True).click();p.wait_for_timeout(200);side=p.evaluate('follow126.sides()[0]');assert side['mealId']=='12' and 'sourceOccurrence' not in side,side
 # Actual local Sunday/Monday boundaries ignore the Tuesday saved planning anchor.
 for instant in [datetime(2026,11,16,7,59,tzinfo=timezone.utc),datetime(2026,11,16,8,1,tzinfo=timezone.utc)]:
  p.clock.set_fixed_time(instant);p.evaluate('follow126.seed();edge126.todo()');text=p.locator('#todaysTodo').inner_text();assert 'Due today task' in text and 'Overdue task' in text and 'Future task' not in text,text
 assert not errors,errors
 c.close();print('PASS',name,'follow126 editor serving ownership/defaults, repeated-serving side rotation, nested Back/cancel, empty/resume both weeks, local Sunday/Monday due boundaries',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
