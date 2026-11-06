"""Permanent Stage 1 correction regressions; synthetic, disposable browser storage.

MEAL_STAGE1_EXPECT_FAILURES=1 reproduces the review findings before correction.
"""
import copy
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage1_browser as stage
import occasional_meals_browser as legacy

stage.f.HOOK += '''window.correctionTest={
 select:(day,cat,id,occasional=false,replacing=null)=>applyManualWeekdayMeal(day,cat,meals.find(m=>m.id===id),replacing,occasional),
 edit:id=>{meals.find(m=>m.id===id).notes='Unrelated recipe edit after scheduling';persist()},
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 mark:(id,value=true)=>{for(const s of getGroceryContributions(true))if(String(s.mealId)===String(id))groceryOccurrenceChecks.checks[s.id]=value;saveGroceryOccurrenceChecks()},
 scale:id=>{for(const e of getDisplayedWeekdayMeals())if(String(e.meal.id)===String(id)){const context=cookingContext(activePlanId,e.day,e.cat,e.meal,e.linkedTo);occurrenceScales.occurrences[cookingOccurrenceKey(context)]={context,multiplier:3}}writeOccurrenceScales(occurrenceScales)},
 legacy:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;setDayCategories('Monday',['Sides']);renderList()},
 open:(day,cat,id)=>openTopMealActionMenu(day,cat,getDisplayedWeekdayMeals().find(e=>e.day===day&&String(e.meal.id)===String(id)).meal),
 checks:()=>groceryOccurrenceChecks,
 edits:()=>JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')
};'''

def setup(browser,name,**kw):return stage.setup(browser,name,**kw)
def sources(p):return {s['id']:s for s in p.evaluate('correctionTest.sources()')}
def progress(p):return {key:(s['checked'],s['line']) for key,s in sources(p).items()}
def clean(errors):assert not errors,errors

def undo_temporary(browser,name,kind):
 c,p,errors,_=setup(browser,name,multi=True)
 if kind=='once':p.evaluate('weekTest.once();weekTest.check()')
 else:p.evaluate('weekTest.check();weekTest.empty()')
 before=copy.deepcopy(stage.plan(p)['weekSchedule']);before_rows=stage.rows(p);before_checks=progress(p)
 p.evaluate('weekTest.manual();weekTest.undo()')
 assert stage.plan(p)['weekSchedule']==before,'Undo must recover the intact temporary descriptor and stable ID'
 assert stage.rows(p)==before_rows and progress(p)==before_checks,'Undo must recover groceries/quantities/checks and unrelated occurrences'
 clean(errors);c.close()

def choose_recipe(p,day,id):
 dialog=p.get_by_role('dialog',name=f"Choose {day}'s meal",exact=True)
 dialog.get_by_role('button',name='Search recipes',exact=True).click();dialog.get_by_role('searchbox').fill('Third Main')
 dialog.locator(f'[data-meal-id="{id}"]').click();dialog.get_by_role('button',name='Save',exact=True).click()

def unconfigured(browser,name):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.once(null,"Sunday");weekTest.my()')
 once=next(e for e in stage.rows(p) if e['day']=='Sunday');before=copy.deepcopy(stage.plan(p));queue=stage.queues(p)
 p.evaluate('e=>correctionTest.open(e.day,e.cat,e.id)',once)
 p.get_by_role('dialog',name='One-time meal options').get_by_role('button',name='Change meal',exact=True).click();choose_recipe(p,'Sunday',3)
 assert any(e['day']=='Sunday' and e['id']==3 for e in stage.rows(p)),'Unconfigured weekday must display the selected reusable recipe'
 assert any(s['day']=='Sunday' and s['mealId']==3 for s in sources(p).values())
 assert not stage.plan(p)['weekdayCategories'].get('Sunday') and stage.queues(p)==queue
 for field in ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices']:assert 'Sunday::@day' not in stage.plan(p).get(field,{})
 p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload()
 assert any(e['day']=='Sunday' and e['id']==3 for e in stage.rows(p))
 # Undo itself is intentionally in-memory; exercise a fresh transition after reload.
 p.evaluate('weekTest.once(null,"Sunday");correctionTest.select("Sunday",null,3,true);weekTest.undo()')
 assert any(e['day']=='Sunday' and str(e['id']).startswith('once-') for e in stage.rows(p))
 clean(errors);c.close()

def legacy_reorder(browser,name,mode):
 c,p,errors,_=setup(browser,name,width=320,linked=True,multi=True)
 p.evaluate('occasionalTest.prepare(true)');legacy.choose(p);p.evaluate('correctionTest.legacy()')
 def ids():return p.locator('.top-recipe-wrap[data-schedule-day=Monday] .meal').evaluate_all('(rows)=>rows.map(row=>row.dataset.mealId)')
 before=ids();assert before==['12','2'],before
 handle=p.get_by_role('button',name='Reorder Occasional curry within Monday',exact=True)
 if mode=='keyboard':handle.focus();p.keyboard.press('ArrowUp')
 else:
  start=handle.bounding_box();target=p.locator('.top-recipe-wrap[data-schedule-day=Monday]').first.bounding_box()
  p.mouse.move(start['x']+start['width']/2,start['y']+start['height']/2);p.mouse.down();p.wait_for_timeout(500)
  p.mouse.move(target['x']+target['width']-4,target['y']+2,steps=8);p.mouse.up()
 assert ids()==['2','12'],'Legacy occasional identity must match rendering, pointer and keyboard keys'
 p.reload();p.evaluate('weekTest.my()');assert ids()==['2','12']
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();p.evaluate('weekTest.my()');assert ids()==['2','12']
 clean(errors);c.close()

def hide_resume(browser,name):
 c,p,errors,_=setup(browser,name,multi=True)
 p.evaluate('weekTest.check();correctionTest.scale(1);correctionTest.scale(20)');before=progress(p);selections=p.evaluate('correctionTest.edits()')
 p.evaluate('weekTest.empty();weekTest.resume()')
 assert progress(p)==before,'Same-cycle Resume must retain hidden main/linked checks and scaled quantities'
 assert p.evaluate('correctionTest.edits()')==selections
 clean(errors);c.close()

if __name__=='__main__':
 reproduce=os.environ.get('MEAL_STAGE1_EXPECT_FAILURES')=='1'
 cases=[('R1 one-time Undo',lambda b,n:undo_temporary(b,n,'once')),('R1 empty Undo',lambda b,n:undo_temporary(b,n,'empty')),('R2 unconfigured Change Meal',unconfigured),('R3 keyboard',lambda b,n:legacy_reorder(b,n,'keyboard')),('R3 pointer',lambda b,n:legacy_reorder(b,n,'pointer')),('R4 same-cycle grocery Resume',hide_resume)]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for label,case in cases:
    try:case(browser,name)
    except AssertionError as error:
     if not reproduce:raise
     print('EXPECTED FAIL',name,label,str(error),flush=True)
    else:
     assert not reproduce,f'Expected unchanged source to reproduce {name}: {label}'
     print('PASS',name,label,flush=True)
  browser.close()
