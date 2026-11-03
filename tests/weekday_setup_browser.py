"""Compact Weekday Setup: real controls, synthetic data, production/test storage isolation."""
import json,copy,tempfile,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='309866412d9b7778128c5dc8ea58f4a54b0e4f59'
CATS=['Rice','Sides','Sauces','Vegetables and roast accompaniments']
ASSIGNED={'Monday':[],'Tuesday':['Rice','Sides'],'Wednesday':['Sauces'],'Thursday':['__meal_rotation_empty_day__'],'Friday':'Rice','Saturday':CATS,'Sunday':[]}
MEALS=[dict(id=i+1,cat=cat,name=cat+' recipe',rotation=True,ingredients=[str(i+1)+' cups rice'],instructions=[{'type':'step','text':'Cook for 15 minutes.'}],notes='Preserve note',labels=[],linkedMealIds=[2] if i==0 else [],custom={'keep':i}) for i,cat in enumerate(CATS)]
HOOK='''window.weekTest={state:()=>({weekdayCategories,startWeekday,weekdayColors,weekdayMealOverrides,weekdayRecipeFilters,mealPlans,activePlanId,meals,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),storage:()=>weekBackup.capture(),seed:()=>{for(const plan of mealPlans)for(const x of getDisplayedWeekdayMealsForPlan(plan)){const c=cookingContext(plan.id,x.day,x.cat,x.meal,x.linkedTo),key=cookingOccurrenceKey(c),t=cookingItemTokens(x.meal);cookingSessions.occurrences[key]={id:'cook-'+key,context:c,ingredients:[],steps:[t.steps[0].token]};occurrenceScales.occurrences[key]={context:c,multiplier:2}}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales)}};'''
def setup(browser,filename,width,size='normal',baseline=False):
 ctx=browser.new_context(viewport={'width':width,'height':850},is_mobile=width<600,has_touch=True,accept_downloads=True);page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
 plans=[dict(id='original',name='Dinner',weekdayCategories=ASSIGNED,weekdayMealOverrides={},weekdayRecipeFilters={},pinnedCats=['Rice','Sides']),dict(id='lunch',name='Lunch',weekdayCategories={'Wednesday':['Rice']},weekdayMealOverrides={},weekdayRecipeFilters={},pinnedCats=[])]
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=CATS,active='Rice',meals=MEALS)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=plans,activeId='original')),prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationTextSizeV1':size,prefix+'mealRotationStartWeekdayV1':'Monday',prefix+'mealRotationSelectedIngredientsV1':json.dumps({'1':['1 cups rice']}),prefix+'mealRotationTutorialStageV1':'done'}
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL';seed['mealRotationCookingSessionsV1']='PROGRESS SENTINEL'
 text=subprocess.check_output(['git','show',BASE+':'+filename],cwd=ROOT,text=True) if baseline else (ROOT/filename).read_text()
 text=text.replace('function validateBackupCore(d){','window.weekBackup={capture:captureBackupStorage,validate:validateBackupStorage};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 page.route('http://weekday.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=text) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''));page.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 page.goto('http://weekday.test/'+filename);page.evaluate('weekTest.seed()');open_settings(page);return ctx,page,errors,prefix

def open_settings(p):
 if p.locator('#settingsPanel').is_hidden():p.get_by_role('button',name='Settings and backups',exact=True).tap()
 group=p.locator('#topSettingsPanel details[data-settings-group=weekdays]')
 if not group.evaluate('(e)=>e.open'):group.locator('summary').tap()
 return group

def day(p,name):return p.locator('.weekday-assignment').filter(has=p.get_by_role('radio',name='Start weekly plan on '+name,exact=True))
def state(p):return p.evaluate('weekTest.state()')
def selections(p,name):return day(p,name).get_by_role('combobox')
def measure(p):return p.locator('.weekday-assignment').evaluate_all('els=>els.map(e=>{const r=e.getBoundingClientRect(),head=e.querySelector("input[type=radio]").parentElement.getBoundingClientRect(),s=e.querySelector("select").getBoundingClientRect();return {day:e.querySelector("input").value,height:r.height,width:r.width,sameRow:Math.abs(head.y-s.y)<4,selectWidth:s.width,overflow:e.scrollWidth>e.clientWidth+1}})')
def assert_layout(p,width,size='normal'):
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,size,'page overflow')
 for row in p.locator('.weekday-assignment').all():
  selectors=row.get_by_role('combobox').all();first=selectors[0].bounding_box();assert first['width']>=78,(width,size,first)
  for sel in selectors:
   box=sel.bounding_box();assert box['height']>=44 and box['width']>=78,(width,size,box)
   assert abs(box['x']-first['x'])<2,(width,size,'selector alignment',first,box)
  for button in row.get_by_role('button').all():
   b=button.bounding_box();assert b['width']>=44 and b['height']>=44,(width,size,'touch target',b)
  assert not row.evaluate('(e)=>e.scrollWidth>e.clientWidth+1'),(width,size,'row overflow',row.inner_text())
 if width>=360 and size=='normal':assert all(r['sameRow'] for r in measure(p)),measure(p)

def run(browser,filename,width):
 ctx,p,errors,prefix=setup(browser,filename,width);initial=copy.deepcopy(state(p));stored=p.evaluate('weekTest.storage()');assert_layout(p,width)
 assert selections(p,'Tuesday').count()==2 and selections(p,'Monday').count()==1
 assert selections(p,'Tuesday').evaluate_all('els=>els.map(x=>x.value)')==['Rice','Sides']
 assert selections(p,'Monday').input_value()=='' and selections(p,'Thursday').input_value()==''
 assert p.get_by_role('radio').count()==7
 # + is a local, nonpersistent request. It cannot select the weekday or clear progress.
 p.get_by_role('button',name='Add group to Tuesday',exact=True).tap();assert selections(p,'Tuesday').count()==3
 assert state(p)==initial and p.evaluate('weekTest.storage()')==stored
 assert p.get_by_role('button',name='Add group to Tuesday',exact=True).is_disabled()
 assert selections(p,'Tuesday').nth(2).locator('option[value=Rice]').is_disabled()
 p.get_by_role('button',name='Cancel adding group to Tuesday',exact=True).tap();assert selections(p,'Tuesday').count()==2 and state(p)==initial
 # Add, change and remove additional groups with existing saved-data handlers.
 p.get_by_role('button',name='Add group to Tuesday',exact=True).tap();selections(p,'Tuesday').nth(2).select_option('Sauces');assert state(p)['weekdayCategories']['Tuesday']==['Rice','Sides','Sauces']
 selections(p,'Tuesday').nth(2).select_option(CATS[3]);assert state(p)['weekdayCategories']['Tuesday']==['Rice','Sides',CATS[3]]
 p.get_by_role('button',name='Remove '+CATS[3]+' from Tuesday',exact=True).tap();assert state(p)['weekdayCategories']['Tuesday']==['Rice','Sides']
 # Primary selector retains its existing clear option; remaining groups promote naturally.
 selections(p,'Tuesday').nth(0).select_option('');assert state(p)['weekdayCategories']['Tuesday']==['Sides']
 selections(p,'Tuesday').nth(0).select_option('');assert selections(p,'Tuesday').count()==1 and selections(p,'Tuesday').input_value()==''
 selections(p,'Tuesday').nth(0).select_option('Rice');p.get_by_role('button',name='Add group to Tuesday',exact=True).tap();selections(p,'Tuesday').nth(1).select_option('Sauces')
 assert p.get_by_role('button',name='Add group to Saturday',exact=True).is_disabled()
 assert state(p)['weekdayCategories']['Friday']=='Rice' and state(p)['weekdayCategories']['Thursday']==ASSIGNED['Thursday']
 # Unfinished empty additions do not enter saved assignments.
 p.get_by_role('button',name='Add group to Tuesday',exact=True).tap();p.get_by_role('button',name='Save settings',exact=True).tap();assert state(p)['weekdayCategories']['Tuesday']==['Rice','Sauces']
 p.reload();open_settings(p);assert selections(p,'Tuesday').count()==2;assert state(p)['weekdayCategories']['Tuesday']==['Rice','Sauces'];assert_layout(p,width)
 # Existing No/Cancel/Yes behavior of first-weekday radios is unchanged.
 p.get_by_role('radio',name='Start weekly plan on Tuesday',exact=True).check();p.get_by_role('dialog').get_by_role('button',name='Cancel',exact=True).tap();assert state(p)['startWeekday']=='Monday';assert p.get_by_role('radio',name='Start weekly plan on Monday',exact=True).is_checked()
 assigned=copy.deepcopy(state(p)['weekdayCategories']);p.get_by_role('radio',name='Start weekly plan on Wednesday',exact=True).check();p.get_by_role('dialog').get_by_role('button',name='No',exact=True).tap();assert state(p)['startWeekday']=='Wednesday' and state(p)['weekdayCategories']==assigned
 p.get_by_role('button',name='Save settings',exact=True).tap();p.reload();open_settings(p);assert p.get_by_role('radio',name='Start weekly plan on Wednesday',exact=True).is_checked()
 p.get_by_role('radio',name='Start weekly plan on Saturday',exact=True).check();p.get_by_role('dialog').get_by_role('button',name='Yes',exact=True).tap();assert state(p)['startWeekday']=='Saturday' and state(p)['weekdayCategories']==assigned
 p.get_by_role('button',name='Save settings',exact=True).tap();p.reload();open_settings(p);assert state(p)['startWeekday']=='Saturday'
 # Unassigned weekday needs no reorder prompt. Cancel settings restores the current saved baseline.
 before_cancel=copy.deepcopy(state(p));p.get_by_role('radio',name='Start weekly plan on Monday',exact=True).check();assert p.get_by_role('dialog').count()==0 and state(p)['startWeekday']=='Monday'
 selections(p,'Monday').select_option('Sides');p.get_by_role('button',name='Cancel settings',exact=True).tap();assert state(p)['weekdayCategories']==before_cancel['weekdayCategories'] and state(p)['startWeekday']=='Saturday'
 final=state(p);assert final['meals']==initial['meals'] and final['prefs']==initial['prefs'] and final['weekdayColors']==initial['weekdayColors']
 assert next(x for x in final['mealPlans'] if x['id']=='lunch')==next(x for x in initial['mealPlans'] if x['id']=='lunch')
 for key,entry in initial['sessions']['occurrences'].items():
  if entry['context']['day']=='Saturday':assert final['sessions']['occurrences'][key]==entry and final['scales']['occurrences'][key]==initial['scales']['occurrences'][key]
 assert p.evaluate('weekTest.storage()')['mealRotationSelectedIngredientsV1']==stored['mealRotationSelectedIngredientsV1']
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,'compact controls, pending add/cancel, add/change/remove/clear-all, duplicate prevention, save/reload/cancel, radio Yes/No/Cancel/empty-day behavior, colors/recipes/other-plan/selection/progress/scaling preservation; no JS errors',flush=True)

def layouts(browser,filename):
 for width,size in [(280,'normal'),(320,'normal'),(360,'normal'),(390,'normal'),(1280,'normal'),(320,'extra'),(360,'extra')]:
  ctx,p,errors,_=setup(browser,filename,width,size);assert_layout(p,width,size)
  if size=='normal' and width in [320,360]:
   ctx_old,old,old_errors,_=setup(browser,filename,width,size,baseline=True);before=sum(x['height'] for x in measure(old));after=sum(x['height'] for x in measure(p));assert after<before*.85,(width,before,after);assert not old_errors;ctx_old.close();print('COMPACT',filename,width,'weekday height',round(before),'→',round(after),flush=True)
  if filename=='index.html' and width in [280,320,360] and size=='normal':p.screenshot(path='/tmp/weekday-setup-'+str(width)+'.png',full_page=True)
  if filename=='index.html' and size=='extra':p.screenshot(path='/tmp/weekday-setup-'+str(width)+'-extra.png',full_page=True)
  assert not errors;ctx.close()
 print('PASS',filename,'280/320/360/390/desktop and large-text responsive layout, 44px controls, aligned selectors, no overflow',flush=True)
if __name__=='__main__':
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   layouts(browser,filename)
   for width in [320,360]:run(browser,filename,width)
  browser.close()
