"""Scheduled linked slots are choices; unscheduled attachments follow the parent."""
import json,copy,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def meal(id,name,cat,links=None):return dict(id=id,name=name,cat=cat,rotation=True,ingredients=[str(id)+' cups rice'],instructions=[{'type':'step','text':'Cook rice for 15 minutes.'}],notes='User note '+str(id),url='https://recipes.test/'+str(id),linkedMealIds=links or [],labels=[],custom={'keep':id})
HOOK='''window.slotTest={state:()=>({meals,plans:mealPlans,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),rows:()=>mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan).map(x=>({planId:plan.id,day:x.day,cat:x.cat,id:x.meal.id,parent:String(x.linkedTo??''),slot:rotationGroupScheduled(plan,x.day,x.cat)}))),open:(all=false)=>openMoveMealChooser(all),cycle:(slots,all=false,mark=false)=>moveDisplayedMealsToBottom(new Set(slots),all,mark),back:()=>rotateAllBack(),partial:keys=>rotateSelectedBack(keys),backChooser:()=>openRotateBackChooser(),history:()=>readPreviousRotation(),oldHistory:()=>{const old=readPreviousRotation();delete old.rotationOccurrences;localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify(old))},storage:()=>slotBackup.capture(),restore:b=>{slotBackup.restore(slotBackup.normalize(b));backupRestoreReloadPending=true},groceries:()=>[...getMasterGroceryItems().values()],seed:()=>{for(const plan of mealPlans)for(const x of getDisplayedWeekdayMealsForPlan(plan)){const c=cookingContext(plan.id,x.day,x.cat,x.meal,x.linkedTo),key=cookingOccurrenceKey(c),t=cookingItemTokens(x.meal);cookingSessions.occurrences[key]={id:'session-'+key,context:c,ingredients:[t.ingredients[0].token],steps:[t.steps[0].token],autoIngredients:[],ingredientOverrides:{[t.ingredients[0].token]:true}};occurrenceScales.occurrences[key]={context:c,multiplier:x.day==='Friday'?3:2}}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales)}};'''
def setup(browser,filename,width,linked=False,side=True,duplicate=False,multi=False):
 library=[meal(1,'Thai Garlic Pork','Rice',[10,20]),meal(2,'Replacement Main','Rice',[12] if linked else []),meal(3,'Third Main','Rice'),meal(11,'New Sides Recipe','Sides'),meal(10,'Garlic Jasmine Rice with Cauliflower','Sides'),meal(12,'Replacement Linked Side','Sides'),meal(13,'Another Side','Sides'),meal(20,'Attached Sauce','Sauces'),meal(21,'Next Sauce','Sauces')]
 assign={'Tuesday':['Rice','Sides'] if side else ['Rice']};overrides={'Tuesday::Sides':'11'} if side else {};pins={}
 if duplicate:assign['Friday']=['Rice','Sides'];overrides.update({'Friday::Rice':'1','Friday::Sides':'10'});pins.update({'Friday::Rice':'1','Friday::Sides':'10'})
 plans=[dict(id='original',name='Dinner',weekdayCategories=assign,weekdayMealOverrides=overrides,weekdayRecipeFilters={},pinnedCats=[],cycleRetainedSlots=pins)]
 if multi:plans.append(dict(id='lunch',name='Lunch',weekdayCategories={'Tuesday':['Sides'],'Thursday':['Sides']},weekdayMealOverrides={'Tuesday::Sides':'10','Thursday::Sides':'10'},weekdayRecipeFilters={},pinnedCats=[],cycleRetainedSlots={'Tuesday::Sides':'10','Thursday::Sides':'10'}))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
 data={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Rice','Sides','Sauces'],active='Rice',meals=library)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=plans,activeId='original')),prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationSelectedIngredientsV1':json.dumps({str(m['id']):m['ingredients'] for m in library}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,autoOpenLinkedRecipes=True,keepScreenAwake=False)),prefix+'mealRotationTutorialStageV1':'done'}
 if prefix:data['mealRotationDataV1']='WORKING SENTINEL';data['mealRotationCookingSessionsV1']='PROGRESS SENTINEL'
 ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,accept_downloads=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 source=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.slotBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(data)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 page.route('http://slots.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''));page.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 page.goto('http://slots.test/'+filename);page.evaluate('slotTest.seed()');return ctx,page,errors,prefix

def state(p):return p.evaluate('slotTest.state()')
def rows(p):return p.evaluate('slotTest.rows()')
def context_key(r):return json.dumps([r['planId'],r['day'],str(r['id']),r['parent']],separators=(',',':'))
def slot(rows,cat,day='Tuesday',plan='original'):return next(r for r in rows if r['planId']==plan and r['day']==day and r['cat']==cat)
def definitions(s):return sorted(s['meals'],key=lambda m:m['id'])
def compose(p):return sorted((x['planId'],x['day'],x['cat'],x['id'],x['parent']) for x in rows(p))
def apply(p,which):
 p.get_by_role('button',name='Cycle Meals',exact=True).tap();p.get_by_role('button',name='Select recipes to rotate out',exact=True).tap();dialog=p.get_by_role('heading',name='Select meals to rotate out').locator('..')
 assert dialog.get_by_role('checkbox').count()==2
 dialog.get_by_role('button',name='Deselect all',exact=True).tap()
 for name in which:dialog.get_by_role('checkbox',name=name,exact=True).check()
 dialog.get_by_role('button',name='Move selected',exact=True).tap()

def run(browser,filename,width):
 labels={'main':'Tuesday · Rice — Thai Garlic Pork','side':'Tuesday · Sides — Garlic Jasmine Rice with Cauliflower'}
 for linked in [False,True]:
  for selection in ['main','side','both','none']:
   ctx,p,errors,prefix=setup(browser,filename,width,linked=linked,duplicate=True,multi=True);before=state(p);before_rows=rows(p);saved=p.evaluate('slotTest.storage()');original=compose(p);grocery=p.evaluate('slotTest.groceries()');before=state(p);saved=p.evaluate('slotTest.storage()')
   # Duplicate Friday rows are additional selectable occurrences; select only Tuesday.
   p.evaluate('slotTest.open()');dialog=p.get_by_role('heading',name='Select meals to rotate out').locator('..');assert dialog.get_by_role('checkbox').count()==4
   assert 'Attached Sauce' not in dialog.inner_text();dialog.get_by_role('button',name='Deselect all',exact=True).tap()
   if selection in ['main','both']:dialog.get_by_role('checkbox',name=labels['main'],exact=True).check()
   if selection in ['side','both']:dialog.get_by_role('checkbox',name=labels['side'],exact=True).check()
   if filename=='index.html' and width==360 and linked and selection=='main':p.screenshot(path='/tmp/scheduled-linked-slots-360.png')
   dialog.get_by_role('button',name='Move selected',exact=True).tap();after=state(p);now=rows(p)
   if selection=='none':assert p.evaluate('slotTest.storage()')==saved
   else:
    assert slot(now,'Rice')['id']==(2 if selection in ['main','both'] else 1),(linked,selection,now)
    expected_side=10 if selection=='main' else 12 if linked and selection=='both' else 11
    assert slot(now,'Sides')['id']==expected_side,(linked,selection,now)
    if selection=='main':
     prior=slot(before_rows,'Sides');assert slot(now,'Sides')==prior
     assert after['sessions']['occurrences'][context_key(prior)]==before['sessions']['occurrences'][context_key(prior)]
     assert after['scales']['occurrences'][context_key(prior)]==before['scales']['occurrences'][context_key(prior)]
    if selection=='side':
     prior=slot(before_rows,'Rice');assert slot(now,'Rice')==prior
     assert after['sessions']['occurrences'][context_key(prior)]==before['sessions']['occurrences'][context_key(prior)]
     attached=next(r for r in before_rows if r['id']==20 and r['day']=='Tuesday');assert attached in now and after['sessions']['occurrences'][context_key(attached)]==before['sessions']['occurrences'][context_key(attached)]
    for r in before_rows:
     if r['planId']!='original' or r['day']!='Tuesday':
      assert r in now,(linked,selection,r,now)
      assert after['sessions']['occurrences'][context_key(r)]==before['sessions']['occurrences'][context_key(r)]
      assert after['scales']['occurrences'][context_key(r)]==before['scales']['occurrences'][context_key(r)]
    assert definitions(before)==definitions(after)
    assert before['prefs']==after['prefs']
    assert not any(c.get('retain') for plan in after['plans'] if plan['id']=='lunch' for c in plan.get('cycleSlotChoices',{}).values())
    assert [p['weekdayCategories'] for p in before['plans']]==[p['weekdayCategories'] for p in after['plans']]
    assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==saved['mealRotationSelectedIngredientsV1']
    totals=p.evaluate('slotTest.groceries()');expected_total=sum(r['id']*after['scales']['occurrences'].get(context_key(r),{}).get('multiplier',1) for r in now);assert len(totals)==1 and abs(totals[0]['quantity']['lo']-expected_total)<1e-8,(linked,selection,totals,expected_total)
    if linked and selection=='both':
     with tempfile.TemporaryDirectory() as tmp:
      p.get_by_role('button',name='Settings and backups',exact=True).click();p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')
      with p.expect_download() as dl:p.get_by_role('button',name='Export backup',exact=True).click()
      target=Path(tmp)/'backup.json';dl.value.save_as(target);backup=json.loads(target.read_text());p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload()
    current=compose(p);p.reload();assert compose(p)==current
    p.evaluate('slotTest.back()');assert compose(p)==original,(linked,selection,'Cycle Back',rows(p),original)
   if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
   assert not errors,errors;ctx.close()
 # Implicit retention (no explicit unchecked choice) allows the replacement main's linked side.
 ctx,p,errors,prefix=setup(browser,filename,width,linked=True);p.evaluate("slotTest.cycle(['Tuesday::Rice'])");assert slot(rows(p),'Sides')['id']==12;assert not errors;ctx.close()
 # Unscheduled side/sauce remain attachments, never independently selectable.
 ctx,p,errors,prefix=setup(browser,filename,width,side=False);original=compose(p);p.evaluate('slotTest.open()');d=p.get_by_role('heading',name='Select meals to rotate out').locator('..');assert d.get_by_role('checkbox').count()==1;d.get_by_role('button',name='Move selected',exact=True).tap();assert [r['id'] for r in rows(p)]==[2];p.evaluate('slotTest.back()');assert compose(p)==original;assert not errors;ctx.close()
 # Partial Back preserves an unselected side and restores a selected linked slot exactly.
 ctx,p,errors,prefix=setup(browser,filename,width,linked=True,multi=True);original=compose(p);apply(p,[labels['main'],labels['side']]);side_now=slot(rows(p),'Sides');p.evaluate("slotTest.partial(['original||Tuesday::Rice'])");assert slot(rows(p),'Sides')==side_now
 assert not any(c.get('retain') for plan in state(p)['plans'] if plan['id']=='lunch' for c in plan.get('cycleSlotChoices',{}).values())
 # A fresh history roundtrip tests the historical explicit linked-side descriptor.
 ctx.close();ctx,p,errors,prefix=setup(browser,filename,width,linked=True);original=compose(p);apply(p,[labels['main'],labels['side']]);p.evaluate('slotTest.oldHistory()');p.evaluate("slotTest.partial(['original||Tuesday::Rice','original||Tuesday::Sides'])");assert compose(p)==original,(rows(p),original);assert not errors;ctx.close()
 # The optional cooked-date action follows selected slots, not every recipe link.
 for chosen,marked,unmarked in [(['Tuesday::Rice'],[1,20],[10]),(['Tuesday::Sides'],[10],[1,20])]:
  ctx,p,errors,prefix=setup(browser,filename,width);p.evaluate('(keys)=>slotTest.cycle(keys,false,true)',chosen);s=state(p)
  assert all(next(m for m in s['meals'] if m['id']==id).get('lastCooked') for id in marked)
  assert all(not next(m for m in s['meals'] if m['id']==id).get('lastCooked') for id in unmarked)
  assert not errors;ctx.close()
 print('PASS',filename,width,'scheduled linked slot choices, main/side/both/neither, explicit retain beats incoming link, implicit linked priority, attachments, duplicate days/cross-plan progress/scales, full/partial/legacy Cycle Back, reload/backups, definitions/settings/selection preservation; no JS errors',flush=True)
if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for f in ['index.html','meal-rotation-test.html']:
   for w in [320,360]:run(b,f,w)
  b.close()
