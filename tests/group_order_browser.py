"""Issue #14: isolated Android group order/drag, persistence, lifecycle and backup tests."""
import json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CATS=['Unassigned A','Friday group','Monday group']+[f'Group {i:02d}' for i in range(4,27)]
MEALS=[dict(id=i,name=f'Recipe {i}',cat=cat,rotation=True,ingredients=[f'1 cup ingredient {i}'],instructions=[f'Cook ingredient {i} for 15 minutes.'],notes='Keep notes',labels=['Favorite'],linkedMealIds=[1] if i==3 else [],custom='keep') for i,cat in enumerate(CATS,1)]
HOOK="""window.groupTest={open:()=>openMasterCategories(),state:()=>({cats,meals,weekdayCategories,plans:mealPlans,custom:masterGroupOrder,expanded:[...masterExpandedCategories],sessions:cookingSessions,scales:occurrenceScales,selected:localStorage.getItem('mealRotationSelectedIngredientsV1')}),order:()=>[...document.querySelectorAll('.master-category-card')].map(c=>c.dataset.category),storage:()=>groupBackup.capture(),expand:cats=>{masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));renderList()},seed:()=>{const m=meals.find(m=>m.id===3),items=cookingItemTokens(m);for(const day of ['Monday','Thursday']){const c=cookingContext('original',day,m.cat,m),key=cookingOccurrenceKey(c);cookingSessions.occurrences[key]={id:day,context:c,ingredients:day==='Monday'?[items.ingredients[0].token]:[],steps:day==='Monday'?[items.steps[0].token]:[]};occurrenceScales.occurrences[key]={context:c,multiplier:day==='Monday'?2:.5}}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales)},assign:()=>{weekdayCategories.Monday=['Group 05'];weekdayCategories.Saturday=['Monday group'];saveWeekdayCategories();renderList()},add:()=>{cats.push('Brand New Group');persist();renderList()},remove:name=>removeMealCategory(name,'delete',null),normalOrder:()=>getCategoryButtonOrder(),schedule:()=>getDisplayedWeekdayMealsForPlan(masterDisplayPlan()).map(x=>({id:x.meal.id,day:x.day,cat:x.cat,parent:x.linkedTo})),groceries:()=>[...getMasterGroceryItems().values()],undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))},restore:b=>{groupBackup.restore(groupBackup.normalize(b));backupRestoreReloadPending=true},fail:()=>{const original=localStorage.setItem.bind(localStorage);localStorage.setItem=(key,value)=>{if(key===MASTER_GROUP_ORDER_KEY)throw Error('QuotaExceededError');original(key,value)};window.restoreGroupWrite=()=>{localStorage.setItem=original}},import:r=>showRecipeImportSelection(recipeImportItems([r]),'fixture.json')};"""

def run(browser,filename,width):
 ctx=browser.new_context(viewport={'width':width,'height':851},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36')
 page=ctx.new_page();page.set_default_timeout(9000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else '';storage='testStorage' if prefix else 'localStorage';key='mealRotationGroupDisplayOrderV1'
 src=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage',storage)+'})();').replace('function validateBackupCore(d){','window.groupBackup={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){')
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=CATS,active=CATS[2],meals=MEALS)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Monday':['Monday group'],'Tuesday':['Group 04'],'Thursday':['Monday group'],'Friday':['Friday group']}),prefix+'mealRotationSelectedIngredientsV1':json.dumps({'3':['1 cup ingredient 3']}),prefix+'mealRotationCheckedIngredientsV1':json.dumps(['1 cup ingredient 3']),prefix+'mealRotationTutorialStageV1':'done',prefix+'mealRotationCustomSettingV8':'preserve'}
 if prefix:seed['mealRotationDataV1']='production-sentinel'
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
 page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''));page.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 page.goto('http://meal.test/'+filename);page.evaluate('groupTest.seed();groupTest.open()');cdp=ctx.new_cdp_session(page)
 def order():return page.evaluate('groupTest.order()')
 def state():return page.evaluate('groupTest.state()')
 def saved():return page.evaluate('groupTest.storage()')
 def card(name):return page.locator('.master-category-card').filter(has=page.locator('.master-category-title strong',has_text=__import__('re').compile('^'+__import__('re').escape(name)+'$')))
 def button(name):return page.get_by_role('button',name=name,exact=True)
 def touch(kind,x=0,y=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':0}]})
 def press(name,body=False):
  item=card(name);item.scroll_into_view_if_needed();target=item.locator('.master-category-meals') if body else item.locator('.master-category-title strong');target.scroll_into_view_if_needed();b=target.bounding_box();x=b['x']+(2 if body else min(30,b['width']/2));y=b['y']+(5 if body else min(12,b['height']/2));touch('touchStart',x,y);page.wait_for_timeout(620);return x,y
 def drag(name,down=True,cancel=False,body=False,wait=2400):
  schedule=page.evaluate('groupTest.schedule()');groceries=page.evaluate('groupTest.groceries()');old=state();before=saved();x,y=press(name,body);assert page.locator('.master-group-drag-ghost').count()==1,'long press must start drag'
  assert state()['expanded']==old['expanded'];assert all(h<100 for h in page.locator('.master-category-card').evaluate_all('(els)=>els.map(e=>e.getBoundingClientRect().height)'))
  destination=838 if down else 9
  for n in range(1,10):touch('touchMove',x,y+(destination-y)*n/9);page.wait_for_timeout(20)
  page.wait_for_timeout(wait);touch('touchCancel' if cancel else 'touchEnd');page.wait_for_timeout(120)
  assert not page.locator('.master-group-drag-ghost').count() and not page.locator('.master-group-drag-active').count()
  assert page.evaluate('groupTest.schedule()')==schedule and page.evaluate('groupTest.groceries()')==groceries
  assert state()['expanded']==old['expanded'];assert {k:v for k,v in state().items() if k not in ['custom','expanded']}=={k:v for k,v in old.items() if k not in ['custom','expanded']}
  assert {k:v for k,v in saved().items() if k!=key}=={k:v for k,v in before.items() if k!=key},{k:(before.get(k),saved().get(k)) for k in set(before)|set(saved()) if k!=key and before.get(k)!=saved().get(k)}
  return old,before
 initial=order();assert initial[:4]==['Monday group','Group 04','Friday group','Unassigned A'],initial
 assert state()['custom'] is None and button('Reset to Weekday Order').is_hidden();normal=page.evaluate('groupTest.normalOrder()')
 # A normal swipe retains native page scrolling and never starts drag or expands cards.
 target=card('Monday group').locator('.master-category-title strong');b=target.bounding_box();x=b['x']+20;y=b['y']+10;touch('touchStart',x,y)
 for n in range(1,9):touch('touchMove',x,y-100*n/8);page.wait_for_timeout(25)
 touch('touchEnd');page.wait_for_timeout(250);assert page.evaluate('scrollY')>20 and order()==initial and state()['custom'] is None
 # Existing chevron/title taps, edit pencil and add buttons stay independent.
 card('Monday group').locator('.master-category-title').tap();page.wait_for_timeout(300);assert 'Monday group' in state()['expanded']
 button('Edit Monday group (reorder, rename, delete)').tap();assert page.get_by_role('dialog',name='Edit meal group').is_visible();assert button('Move group later').is_enabled();button('Cancel category editing').tap()
 # The chevron stays an expansion control, and the add icon still opens the real editor.
 svg=card('Monday group').locator('.master-category-title svg');svg.scroll_into_view_if_needed();b=svg.bounding_box();touch('touchStart',b['x']+9,b['y']+9);page.wait_for_timeout(620);assert not page.locator('.master-group-drag-ghost').count();touch('touchCancel')
 button('Add meal to Monday group').tap();assert page.locator('#name').is_visible();page.locator('#name').fill('Added through existing control');page.locator('#save').click();page.wait_for_timeout(100)
 assert any(m['name']=='Added through existing control' for m in state()['meals'])
 # Recipe long presses now enter multi-select; they must not drag the parent or open a viewer.
 section=card('Monday group').get_by_role('button',name='In Rotation',exact=False)
 if section.get_attribute('aria-expanded')=='false':section.tap()
 name=card('Monday group').get_by_role('button',name='Recipe 3',exact=True);name.scroll_into_view_if_needed();b=name.bounding_box();before_recipe=state()['sessions'];touch('touchStart',b['x']+20,b['y']+10);page.wait_for_timeout(620);touch('touchEnd');page.wait_for_timeout(80)
 assert page.locator('#recipeBulkToolbar').is_visible() and not page.locator('#recipeViewer').count() and not page.locator('.master-group-drag-ghost').count()
 assert state()['sessions']==before_recipe
 button('Exit selection mode').tap()
 # Preserve multiple expanded states and collapse visually only while dragging.
 page.evaluate('groupTest.expand(["Monday group","Friday group","Group 05"])');expanded=state()['expanded'];base=saved()
 before_hold=saved();before_expanded=state()['expanded'];press('Monday group');touch('touchEnd');page.wait_for_timeout(80);assert order()==initial and saved()==before_hold and state()['expanded']==before_expanded
 drag('Monday group');assert order()[-1]=='Monday group' and state()['custom']==order();assert page.evaluate('groupTest.normalOrder()')==normal
 assert button('Reset to Weekday Order').is_visible();assert card('Friday group').locator('.master-category-meals').is_visible()
 # Assigned and unassigned groups can both cross every tier; auto-scroll works upward too.
 drag('Monday group',down=False);assert order()[0]=='Monday group'
 drag('Unassigned A',down=False);assert order()[0]=='Unassigned A'
 original=order();drag('Group 05',cancel=True,body=True);assert order()==original
 drag('Group 05',body=True);assert order()[-1]=='Group 05'
 # Normal tap after drag still toggles, not a delayed drag click.
 old_expanded=state()['expanded'];card('Group 06').locator('.master-category-title').tap();page.wait_for_timeout(150);assert state()['expanded']==['Group 06']
 custom=order();page.reload();page.evaluate('groupTest.open()');assert order()==custom and state()['custom']==custom
 # Weekday changes do not move custom groups; underlying category order stays unchanged.
 page.evaluate('groupTest.assign()');assert order()==custom and state()['cats']==CATS
 page.evaluate('groupTest.add()');assert order()==custom+['Brand New Group']
 # Rename through the real editor keeps its saved position.
 target='Friday group';at=order().index(target);button('Edit '+target+' (reorder, rename, delete)').tap();button('Rename category').tap();field=page.get_by_role('textbox');field.fill('Friday Renamed');button('Save').tap();page.wait_for_timeout(100);assert order()[at]=='Friday Renamed' and target not in order()
 page.evaluate('groupTest.remove("Group 20")');assert 'Group 20' not in order() and 'Group 20' not in state()['custom']
 # Existing ordering arrows operate the same display-only custom order, including assigned groups.
 before=order();button('Edit Monday group (reorder, rename, delete)').tap();button('Move group later').tap();button('Cancel category editing').tap();assert order().index('Monday group')==before.index('Monday group')+1
 # Import adds a predictable trailing group without overwriting the saved order.
 before=order();r={'name':'Imported test recipe','identifier':'new-source','recipeIngredient':['1 cup oats'],'recipeInstructions':'Cook oats.','recipeCategory':['Imported group']};page.evaluate('(r)=>groupTest.import(r)',r)
 page.locator('#recipeImportDialog').get_by_role('checkbox',name='Imported group').check();page.locator('#recipeImportDialog').get_by_role('button',name='Import recipes',exact=True).click();button('OK').tap();page.evaluate('groupTest.open()');assert order()==before+['Imported group']
 # Backup includes and validates the order; missing/legacy keys fall back to automatic ordering.
 storage_copy=saved();page.evaluate('(s)=>groupBackup.validate(s)',storage_copy)
 bad=dict(storage_copy);bad[key]='["duplicate","duplicate"]';assert page.evaluate('(s)=>{try{groupBackup.validate(s);return false}catch(e){return true}}',bad)
 backup={'version':2,**json.loads(storage_copy['mealRotationDataV1']),'storage':storage_copy}
 # Save failures roll back the tentative visual order and preserve all saved data.
 before=order();page.evaluate('groupTest.fail()');drag('Monday group',down=False,wait=1200);assert order()==before
 button('OK').tap();page.evaluate('restoreGroupWrite()')
 # Reset has no confirmation and preserves assignments/meals/progress/scales/groceries.
 before=state();button('Reset to Weekday Order').tap();assert state()['custom'] is None and key not in saved();assert state()['weekdayCategories']==before['weekdayCategories'] and state()['meals']==before['meals'] and state()['sessions']==before['sessions'] and state()['scales']==before['scales']
 assert order()!=before['custom'];page.evaluate('groupTest.undo()');assert state()['custom']==before['custom'];button('Reset to Weekday Order').tap();page.reload();page.evaluate('groupTest.open()');assert state()['custom'] is None
 # Restore exact custom order through the existing V2 storage restore path.
 page.evaluate('(b)=>groupTest.restore(b)',backup);page.reload();page.evaluate('groupTest.open()');assert state()['custom']==json.loads(storage_copy[key]);assert order()==[x for x in json.loads(storage_copy[key]) if x in state()['cats']]+[x for x in state()['cats'] if x not in json.loads(storage_copy[key])]
 # Malformed legacy order values are ignored without silently rewriting that key.
 page.evaluate('(a)=>localStorage.setItem(a[0],a[1])',[prefix+key,'{broken']);page.reload();page.evaluate('groupTest.open()');assert state()['custom'] is None and saved()[key]=='{broken'
 # V1 restore has no custom-order field and returns to the existing weekday default.
 legacy={'version':1,**json.loads(storage_copy['mealRotationDataV1']),'weekdayCategories':state()['weekdayCategories']}
 button('Settings and backups').tap();page.locator('[data-settings-group=backups]').evaluate('(e)=>e.open=true')
 with page.expect_file_chooser() as fc:button('Restore backup').tap()
 fc.value.set_files({'name':'legacy-backup.json','mimeType':'application/json','buffer':json.dumps(legacy).encode()});page.wait_for_timeout(160);page.evaluate('groupTest.open()');assert state()['custom'] is None and key not in saved()
 assert state()['cats']==legacy['cats'] and state()['meals']==legacy['meals']
 if filename=='index.html':page.screenshot(path=f'/workspace/issue-14-work/groups-{width}.png')
 if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='production-sentinel'
 assert not errors,errors
 print(f'PASS {filename} {width}px Android touch: native swipe vs hold, all-tier drag+edge scroll both directions, cancellation, expansion/icons, persistence, weekday changes, rename/delete/add/import, arrows, storage failure, reset, V2 backup/restore, data/progress/scale/isolation; no JS errors',flush=True)
 ctx.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:run(b,filename,width)
  b.close()
