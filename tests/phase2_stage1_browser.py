"""Stage 1 synthetic regressions. No user storage, network or production writes."""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import scheduled_linked_slots_browser as f

f.HOOK += '''window.weekTest={
 empty:(cat='Rice',day='Tuesday',all=false)=>leaveWeekEmpty(day,cat,all),
 resume:(cat='Rice',day='Tuesday',all=false)=>resumeWeekSlot(day,cat,all),
 once:(cat='Rice',day='Tuesday',name='Potluck',items=['2 cups rice','3 apples'])=>saveOneTimeMeal(day,cat,name,items),
 editOnce:()=>openOneTimeMealEditor('Tuesday','Rice'),
 state:()=>JSON.parse(captureState()),persist:()=>persist(),
 favorite:()=>applyRecipeBulk(['2'],{favorite:true}),
 views:()=>{showTop=true;groceryTabActive=true;allMealsActive=false;renderList();groceryTabActive=false;allMealsActive=true;renderList()},
 rename:()=>{cats[cats.indexOf('Rice')]='Mains';for(const meal of meals)if(meal.cat==='Rice')meal.cat='Mains';for(const day of weekdays)if(Array.isArray(weekdayCategories[day]))weekdayCategories[day]=weekdayCategories[day].map(cat=>cat==='Rice'?'Mains':cat);updateOtherMealPlansForCategory('Rice','Mains');persist();renderList()},
 rotate:(slots=null,all=false)=>moveDisplayedMealsToBottom(slots===null?null:new Set(slots),all,false),
 back:keys=>keys?rotateSelectedBack(keys):rotateAllBack(),
 chooser:()=>openWeekdayMealChooser('Tuesday','Rice',getDisplayedWeekdayMeals().find(x=>x.day==='Tuesday'&&x.cat==='Rice')?.meal),
 menu:(cat='Rice')=>{const e=getDisplayedWeekdayMeals().find(x=>x.day==='Tuesday'&&x.cat===cat);openTopMealActionMenu(e.day,e.cat,e.meal)},
 displayed:()=>getDisplayedWeekdayMeals(),
 order:keys=>setWeekDisplayOrder('Tuesday',keys),
 keys:()=>reorderableWeekEntries().filter(x=>x.day==='Tuesday').map(scheduleDisplayKey),
 manual:()=>applyManualWeekdayMeal('Tuesday','Rice',meals.find(m=>m.id===3)),
 manualLinkedSetup:()=>{meals.find(m=>m.id===3).linkedMealIds=[12];meals.find(m=>m.id===12).rotation=false;persist();renderList()},
 my:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;render()},
 sources:()=>getGroceryContributions(true).map(source=>({...source,checked:grocerySourceChecked(source)})),
 check:()=>{for(const [key,item] of getMasterGroceryItems())setGroceryItemChecked(key,item,true)},
 storage:()=>captureBackupStorage(),
 restore:data=>{restoreBackupStorage(data);backupRestoreReloadPending=true},
 validate:data=>validateBackupStorage(data),
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))},
 pair:()=>{const p=mealPlans.find(p=>p.id===activePlanId);groupIdentity('Rice',true);groupIdentity('Sides',true);p.sideGroupPairs={Tuesday:{[groupIdentity('Sides')]:groupIdentity('Rice')}};persist();renderList()},
 remove:id=>applyRecipeBulk([String(id)],{delete:true}),
 editRecipe:()=>{meals.find(m=>m.id===1).notes='Edited after rotation';persist()},
 move:()=>openMoveMealChooser(),
 rows:()=>mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan).map(x=>({planId:plan.id,day:x.day,cat:x.cat,id:x.meal.id,parent:String(x.linkedTo??'')})))
};'''

def setup(browser,name,width=360,**kw):
 c,p,errors,prefix=f.setup(browser,name,width,**kw)
 p.set_default_timeout(7000)
 return c,p,errors,prefix

def definitions(p):return json.dumps(state(p)['meals'],sort_keys=True)
def queues(p):return [m['id'] for m in state(p)['meals']]
def rows(p):return p.evaluate('weekTest.rows()')
def state(p):return p.evaluate('weekTest.state()')
def plan(p):return next(x for x in state(p)['mealPlans'] if x['id']=='original')
def assert_clean(errors):assert not errors,errors

def empties(browser,name):
 for pair in [False,True]:
  c,p,errors,prefix=setup(browser,name,multi=True)
  if pair:p.evaluate('weekTest.pair()')
  before=definitions(p);old=copy.deepcopy(rows(p));assign=copy.deepcopy(plan(p)['weekdayCategories']);scores=copy.deepcopy(plan(p).get('favoriteRotationScores'))
  p.evaluate('weekTest.empty()')
  assert not any(x['planId']=='original' and x['day']=='Tuesday' and x['cat']=='Rice' for x in rows(p))
  assert any(x['planId']=='original' and x['day']=='Tuesday' and x['cat']=='Sides' for x in rows(p)),rows(p)
  assert all(x in rows(p) for x in old if x['planId']!='original')
  assert definitions(p)==before and plan(p)['weekdayCategories']==assign
  p.evaluate('weekTest.my()');assert p.locator('.weekday-heading[data-weekday=Tuesday]').evaluate('(el)=>el.nextElementSibling.textContent.includes("Rice · Empty this week")')
  p.reload();assert definitions(p)==before and 'Tuesday::Rice' in plan(p)['weekSchedule']['slots']
  backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.resume()');p.evaluate('weekTest.restore',backup);p.reload()
  assert definitions(p)==before and not any(x['planId']=='original' and x['cat']=='Rice' for x in rows(p))
  p.evaluate("weekTest.rotate(['Tuesday::Rice'])")
  assert definitions(p)==before and plan(p).get('favoriteRotationScores')==scores
  assert any(x['planId']=='original' and x['cat']=='Rice' for x in rows(p))
  p.evaluate("weekTest.back(['original||Tuesday::Rice'])")
  assert not any(x['planId']=='original' and x['cat']=='Rice' for x in rows(p)) and definitions(p)==before
  p.evaluate('weekTest.undo()');assert any(x['planId']=='original' and x['cat']=='Rice' for x in rows(p))
  assert_clean(errors);c.close()
 for all_tabs in [False,True]:
  c,p,errors,_=setup(browser,name,multi=True)
  before=definitions(p);old=rows(p);p.evaluate('weekTest.empty(null,"Tuesday",true)')
  assert not any(x['planId']=='original' and x['day']=='Tuesday' for x in rows(p))
  p.evaluate('weekTest.my()');assert p.locator('.empty-weekday-meal').filter(has_text='Empty this week').count()==len(plan(p)['weekSchedule']['slots'])
  p.evaluate('weekTest.my();weekTest.move()');dialog=p.get_by_role('heading',name='Select meals to rotate out').locator('..');assert dialog.get_by_role('checkbox').count()>=2
  dialog.get_by_role('button',name='Cancel',exact=True).click()
  p.evaluate('all=>weekTest.rotate(null,all)',all_tabs)
  if not all_tabs:assert definitions(p)==before
  assert not plan(p)['weekSchedule']['slots']
  p.evaluate('weekTest.back()');assert not any(x['planId']=='original' and x['day']=='Tuesday' for x in rows(p))
  assert plan(p)['weekdayCategories']=={'Tuesday':['Rice','Sides']};assert_clean(errors);c.close()
 print('PASS',name,'individual/day empty: groups, queues, linked/dependent sides, tabs, reload, backup, selected/full rotation, history, Undo',flush=True)

def temporary(browser,name):
 for cat,day in [('Rice','Tuesday'),(None,'Sunday')]:
  c,p,errors,prefix=setup(browser,name,multi=True);before=definitions(p);old=rows(p);p.evaluate('weekTest.check()');checks=p.evaluate('weekTest.sources()')
  p.evaluate('([cat,day])=>weekTest.once(cat,day)',[cat,day]);once=next(x for x in rows(p) if str(x['id']).startswith('once-'))
  assert definitions(p)==before and all(x in rows(p) for x in old if x['planId']!='original')
  sources=p.evaluate('weekTest.sources()');assert len([x for x in sources if x['mealId']==once['id']])==2
  assert all(x['checked'] for x in sources if x['id'] in {y['id'] for y in checks})
  p.reload();assert definitions(p)==before and once in rows(p)
  backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.resume(null,"Sunday",true);weekTest.resume(null,"Tuesday",true)');p.evaluate('weekTest.restore',backup);p.reload();assert once in rows(p)
  p.evaluate("weekTest.rotate(['Tuesday::Sides'])");assert once in rows(p),'unselected temporary entry must stay'
  order=queues(p);key=day+'::'+(cat or '@day');p.evaluate('key=>weekTest.rotate([key])',key)
  assert queues(p)==order and not any(str(x['id']).startswith('once-') for x in rows(p))
  assert not any(x['mealId']==once['id'] for x in p.evaluate('weekTest.sources()'))
  p.evaluate('keys=>weekTest.back(keys)',['original||'+key]);assert once in rows(p) and queues(p)==order
  p.evaluate('weekTest.editRecipe()');p.evaluate('weekTest.rotate()');p.evaluate('weekTest.back()')
  assert next(m for m in state(p)['meals'] if m['id']==1)['notes']=='Edited after rotation'
  assert once in rows(p);p.reload();assert once in rows(p)
  if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
  assert_clean(errors);c.close()
 print('PASS',name,'one-time meals/groceries stay outside recipes; occurrence checks; unconfigured day; reload/backup; selected/full expiration and history preserve recipe edits',flush=True)

def manual(browser,name):
 for linked in [False,True]:
  c,p,errors,_=setup(browser,name,multi=True)
  if linked:p.evaluate('weekTest.manualLinkedSetup()')
  before=definitions(p);p.evaluate('weekTest.manual()');assert definitions(p)==before
  p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();p.evaluate("weekTest.rotate(['Tuesday::Rice'])")
  assert definitions(p)==before,'manual substitution and its links must not consume recipe queues or promote Ideas'
  p.evaluate("weekTest.back(['original||Tuesday::Rice'])");assert definitions(p)==before
  assert any(x['planId']=='original' and x['cat']=='Rice' and x['id']==3 for x in rows(p));assert_clean(errors);c.close()
 print('PASS',name,'manual recipe substitution and linked Ideas do not alter normal queues/status through reload, backup/restore, selected rotation/back',flush=True)

def ui_and_reorder(browser,name,width):
 c,p,errors,_=setup(browser,name,width);p.evaluate('weekTest.my();weekTest.menu()');dialog=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True)
 labels=dialog.get_by_role('button').all_text_contents();assert labels.index('Leave Empty This Week')==labels.index('Skip This Meal')+1
 dialog.get_by_role('button',name='Leave Empty This Week',exact=True).click();p.locator('.empty-weekday-meal').filter(has_text='Rice · Empty this week').click()
 p.get_by_role('dialog',name='Empty meal options').get_by_role('button',name='Change meal',exact=True).click()
 p.get_by_role('dialog',name="Choose Tuesday's meal").get_by_role('button',name='Add One-Time Meal',exact=True).click()
 p.get_by_role('textbox',name='One-time meal name',exact=True).fill('<Potluck>')
 p.get_by_role('textbox',name='Optional grocery items with quantities',exact=True).fill('2 cups rice\n1 bag salad')
 p.get_by_role('button',name='Save one-time meal',exact=True).click();assert p.locator('.mealname').filter(has_text='<Potluck>').count()==1
 assert not p.locator('potluck').count()
 p.evaluate('weekTest.resume(null,"Tuesday",true)');p.evaluate('weekTest.my()');before=definitions(p);original=p.evaluate('weekTest.keys()')
 handles=p.locator('.week-reorder-handle');assert handles.count()==2
 handles.first.focus();p.keyboard.press('ArrowDown');assert p.evaluate('weekTest.keys()')==list(reversed(original))
 p.reload();p.evaluate('weekTest.my()');assert p.evaluate('weekTest.keys()')==list(reversed(original))
 # Actual long-press pointer drag back to the original order.
 wraps=p.locator('.top-recipe-wrap[data-schedule-day=Tuesday]');first=wraps.first;last=wraps.last;handle=first.locator('.week-reorder-handle').bounding_box();target=last.bounding_box()
 p.mouse.move(handle['x']+handle['width']/2,handle['y']+handle['height']/2);p.mouse.down();p.wait_for_timeout(500)
 p.mouse.move(target['x']+target['width']/2,target['y']+target['height']-2,steps=8);p.mouse.up()
 assert p.evaluate('weekTest.keys()')==original,(p.evaluate('weekTest.keys()'),original)
 assert definitions(p)==before
 # Touch input must not leak into the row's pre-existing swipe-to-edit gesture.
 first=wraps.first;last=wraps.last;handle=first.locator('.week-reorder-handle').bounding_box();target=last.bounding_box();cdp=c.new_cdp_session(p)
 touch={'x':handle['x']+handle['width']/2,'y':handle['y']+handle['height']/2}
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[touch]});p.wait_for_timeout(500)
 cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':target['x']+target['width']-4,'y':target['y']+target['height']-2}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert p.evaluate('weekTest.keys()')==list(reversed(original)) and not p.locator('#name').count()
 p.evaluate('weekTest.order',original);cdp.detach()
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert p.evaluate('weekTest.keys()')==original
 p.evaluate('keys=>{weekTest.my();weekTest.order(keys)}',list(reversed(original)));p.evaluate('weekTest.rotate()');assert not plan(p)['weekSchedule']['order']
 p.evaluate('weekTest.back()');assert p.evaluate('weekTest.keys()')==list(reversed(original)) and definitions(p)==before
 p.evaluate('weekTest.my()');p.locator('.weekday-heading[data-weekday=Tuesday]').click();p.get_by_role('button',name='Leave Entire Day Empty This Week',exact=True).click()
 assert not any(x['planId']=='original' and x['day']=='Tuesday' for x in rows(p))
 assert_clean(errors);c.close();print('PASS',name,width,'real empty/Change Meal/one-time/day controls; escaped text; keyboard and long-press reorder; reload and backup retain display-only order',flush=True)

def failures(browser,name):
 c,p,errors,prefix=setup(browser,name);before=p.evaluate('weekTest.storage()')
 p.evaluate('''window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationPlansV1'))throw Error('injected plan quota');return originalSet.call(this,k,v)};void 0''')
 p.evaluate('weekTest.once()');assert p.locator('#mealSaveWarning').is_visible()
 assert p.evaluate('prefix=>window.localStorage.getItem(prefix+"mealRotationPlansV1")',prefix)==before['mealRotationPlansV1']
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 exported=json.loads(Path(dl.value.path()).read_text());assert 'Potluck' in json.dumps(exported)
 p.evaluate('Storage.prototype.setItem=originalSet;void 0');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.reload()
 assert any(str(x['id']).startswith('once-') for x in rows(p))
 raw=p.evaluate('weekTest.storage()');bad=copy.deepcopy(raw);plans=json.loads(bad['mealRotationPlansV1']);plans['plans'][0]['weekSchedule']['slots']['Tuesday::Rice']['meal']['ingredients']=None;bad['mealRotationPlansV1']=json.dumps(plans)
 try:p.evaluate('weekTest.validate',bad);raise AssertionError('invalid backup accepted')
 except Exception as e:assert 'Invalid temporary meal' in str(e),e
 assert p.evaluate('weekTest.storage()')==raw
 p.evaluate('weekTest.editOnce()');p.get_by_role('textbox',name='One-time meal name',exact=True).fill('Unsaved picnic')
 # Draft collector used by Phase 1 includes the live one-time dialog.
 p.evaluate('''window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('draft test');return originalSet.call(this,k,v)};weekTest.persist()''')
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'Unsaved picnic' in Path(dl.value.path()).read_text()
 p.evaluate('Storage.prototype.setItem=originalSet;void 0');p.get_by_role('dialog',name='Add One-Time Meal').get_by_role('button',name='Cancel',exact=True).click()
 assert_clean(errors);c.close();print('PASS',name,'failed plan save retains durable originals, warning/export/retry/reload, invalid temporary backup rejected unchanged, live draft recovery export',flush=True)

def interactions(browser,name):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.once();weekTest.favorite();weekTest.views()')
 assert not any(str(value).startswith('once-') for item in state(p)['mealPlans'] for value in item.get('weekdayMealOverrides',{}).values()),'temporary IDs must never leak into permanent planner overrides'
 p.evaluate('weekTest.remove(1)');assert all(m['id']!=1 for m in state(p)['meals'])
 p.evaluate("weekTest.rotate(['Tuesday::Rice']);weekTest.back(['original||Tuesday::Rice'])");assert all(m['id']!=1 for m in state(p)['meals'])
 assert any(str(x['id']).startswith('once-') for x in rows(p));assert_clean(errors);c.close()
 c,p,errors,_=setup(browser,name);p.evaluate('weekTest.pair();weekTest.once()');before=definitions(p);p.reload();assert definitions(p)==before
 p.evaluate("weekTest.rotate(['Tuesday::Rice'])");assert definitions(p)==before;assert_clean(errors);c.close()
 c,p,errors,_=setup(browser,name);p.evaluate('weekTest.once(null,"Sunday");weekTest.rotate(["Sunday::@day"]);slotTest.backChooser()')
 d=p.get_by_role('heading',name='Select meals to rotate back').locator('..');assert 'Potluck' in d.inner_text();d.get_by_role('button',name='Move selected',exact=True).click();assert any(x['day']=='Sunday' and str(x['id']).startswith('once-') for x in rows(p));assert_clean(errors);c.close()
 c,p,errors,_=setup(browser,name);p.evaluate('weekTest.once();weekTest.rename()');assert 'Tuesday::Mains' in plan(p)['weekSchedule']['slots'] and 'Tuesday::Rice' not in plan(p)['weekSchedule']['slots'];p.reload();assert any(x['cat']=='Mains' and str(x['id']).startswith('once-') for x in rows(p));assert_clean(errors);c.close()
 c,p,errors,prefix=setup(browser,name);p.evaluate('weekTest.once()');raw=p.evaluate('weekTest.storage()');bad=json.loads(raw['mealRotationPlansV1']);bad['plans'][0]['weekSchedule']['slots']=None;encoded=json.dumps(bad)
 p.evaluate('([key,value])=>window.localStorage.setItem(key,value)',[prefix+'mealRotationPlansV1',encoded]);p.reload();assert p.locator('#mealDataRecovery').is_visible();assert p.evaluate('key=>window.localStorage.getItem(key)',prefix+'mealRotationPlansV1')==encoded
 # The fixture's page-local hooks are deliberately absent while startup is paused.
 assert all('slotTest is not defined' in error for error in errors),errors;c.close()
 print('PASS',name,'temporary slots coexist with bulk edits/deletion, grocery/overview, paired sides, no recipe resurrection, history chooser on unconfigured day, explicit group rename',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   empties(browser,name);temporary(browser,name);manual(browser,name)
   for width in [320,360]:ui_and_reorder(browser,name,width)
   failures(browser,name);interactions(browser,name)
  browser.close()
