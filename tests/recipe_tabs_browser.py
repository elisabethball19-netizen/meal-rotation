"""Issue #1 regressions; test-only hooks are injected into browser responses."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def meal(i,name,cat,rotation=False,links=None):
    return dict(id=i,name=name,cat=cat,rotation=rotation,linkedMealIds=links or [],ingredients=['1 cup rice' if i==1 else f'1 cup vegetable {i}']+[f'{n+1} test ingredient {i}-{n}' for n in range(65)],instructions=[f'Stir ingredient {i}-{n} for {n+1} minutes. '+('Keep stirring slowly. '*5) for n in range(40)])
MEALS=[meal(1,'Main One','Main',True,[2,3,2,999]),meal(2,'Side Dish','Sides',False,[99]),meal(3,'Sauce','Sauces'),meal(4,'Other Main','Other',True,[2]),meal(99,'Nested Recipe','Nested')]
HOOK="""window.tabTest={open:(id=1,day='Tuesday',parent='')=>{window.history.replaceState({},'');const meal=meals.find(m=>m.id===id);openRecipeViewer(meal,day?cookingContext('original',day,meal.cat,meal,parent):null,true)},state:()=>({meals,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs,tabs:recipeViewer?.tabs.map(t=>({key:t.key,id:t.mealId,context:t.context,mode:t.mode,ratio:t.ratio,previewProgress:t.previewProgress,previewScale:t.previewScale})),active:recipeViewer?.mealId,context:recipeViewer?.context,progress:recipeViewer?(recipeViewer.context?cookingSession(recipeViewer.context):recipeViewer.previewProgress):null}),cycle:(day,id=1)=>clearCycledCookingContexts([{planId:'original',day,meal:meals.find(m=>m.id===id)}]),groceries:()=>[...getMasterGroceryItems().values()],links:(id,ids)=>{meals.find(m=>m.id===id).linkedMealIds=ids;persist()},many:()=>{for(let i=10;i<22;i++)meals.push({id:i,name:'A very long linked recipe title number '+i+' with more description',cat:'Sides',rotation:false,ingredients:['1 cup water'],instructions:'Boil water.'});meals.find(m=>m.id===1).linkedMealIds=[2,3,...Array.from({length:12},(_,n)=>n+10),999];},content:()=>{const m=meals.find(m=>m.id===1),items=cookingItemTokens(m);return {ingredients:m.ingredients,instructions:m.instructions,tokens:items}},historyOpen:()=>{const m=meals.find(m=>m.id===1);openRecipeViewer(m,cookingContext('original','Tuesday',m.cat,m))}};"""

def run(browser,filename,width):
    context=browser.new_context(viewport={'width':width,'height':851 if width<600 else 900},is_mobile=width<600,has_touch=width<600)
    page=context.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();')
    source=source.replace('function validateBackupCore(d){','window.tabBackup={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage};function validateBackupCore(d){')
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides','Sauces','Other','Nested'],active='Main',meals=MEALS)),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main','Other'],'Friday':['Main'],'Thursday':['Other']}),prefix+'mealRotationSelectedIngredientsV1':json.dumps({'1':['1 cup rice']})}
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}window.wakeCalls={request:0,release:0};Object.defineProperty(navigator,"wakeLock",{configurable:true,value:{request:async()=>{wakeCalls.request++;const lock=new EventTarget();lock.released=false;lock.release=async()=>{if(!lock.released){wakeCalls.release++;lock.released=true;lock.dispatchEvent(new Event("release"))}};return lock}}});')
    page.route('http://meal.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=source) if route.request.url.endswith(filename) else route.fulfill(status=200,body=''))
    page.route('https://**/*',lambda route:route.fulfill(status=200,body=''))
    page.goto('http://meal.test/'+filename)
    def state():return page.evaluate('tabTest.state()')
    def op(i=1,day='Tuesday',parent=''):page.evaluate('(a)=>tabTest.open(...a)',[i,day,parent])
    def tabs():return page.locator('#recipeViewer .recipe-tab-strip [role=tab]')
    def select(name):page.locator('#recipeViewer .recipe-tab-strip').get_by_role('tab').filter(has_text=name).click()
    def step(n=0):return page.locator('.recipe-viewer-steps .cooking-item').nth(n)
    def ingredient(n=0):return page.locator('.recipe-viewer-ingredients .cooking-item').nth(n)
    def button(name):return page.get_by_role('button',name=name,exact=True)
    def option(name,value):
        if not page.locator('#recipeViewerSettings').is_visible():button('Recipe settings').click()
        page.get_by_label(name,exact=True).set_checked(value);button('Close settings').click()
    def scale(value):button('Scale Recipe').click();page.get_by_role('menuitemradio',name=value,exact=True).click()
    def close():button('Close recipe').click();page.wait_for_selector('#recipeViewer',state='detached')
    def linked(name):page.locator('.recipe-linked-link').filter(has_text=re.compile('^'+re.escape(name)+'$')).click()
    def scrolls():return page.evaluate('({full:document.querySelector("#recipeViewer").scrollTop,panes:[...document.querySelectorAll(".recipe-pane")].map(p=>p.scrollTop)})')
    def pane_scroll(a,b):page.locator('.recipe-ingredients-pane').evaluate('(e,n)=>e.scrollTop=n',a);page.locator('.recipe-instructions-pane').evaluate('(e,n)=>e.scrollTop=n',b)
    def hold(n=0):
        step(n).scroll_into_view_if_needed();box=step(n).bounding_box();page.mouse.move(box['x']+20,box['y']+15);page.mouse.down();page.wait_for_timeout(650);page.mouse.up()
    def occurrence(day,id=1,parent=''):
        return state()['sessions']['occurrences'].get(json.dumps(['original',day,str(id),str(parent)],separators=(',',':')))
    # Off by default on an older preference record; toolbar remains four icons.
    initial_rotation={m['id']:m['rotation'] for m in state()['meals']}
    op();assert tabs().count()==1;assert page.locator('.recipe-viewer-bar>button').count()==4
    assert page.locator('.recipe-tab').first.locator('.recipe-tab-close').count()==0
    history_length=page.evaluate('window.history.length')
    linked('Side Dish');assert tabs().count()==2;linked('Nested Recipe');assert tabs().count()==3
    select('Main One');linked('Side Dish');assert tabs().count()==3;assert page.evaluate('window.history.length')==history_length
    assert state()['context']['parentId']=='1' and state()['context']['day']=='Tuesday'
    assert {m['id']:m['rotation'] for m in state()['meals']}==initial_rotation
    # Closing inactive retains active; closing active returns to main. Reopen uses cache.
    button('Close Nested Recipe tab').click();assert state()['active']=='2'
    button('Close Side Dish tab').click();assert state()['active']=='1' and tabs().count()==1
    option('Automatically open linked recipes in tabs',True);close();op();assert tabs().count()==3
    assert not tabs().filter(has_text='Nested Recipe').count(),'do not recursively auto-open'
    assert state()['prefs']['autoOpenLinkedRecipes'] is True
    # Every tab restores split/full positions and ratio without running sync or completion.
    pane_scroll(140,280);divider=page.get_by_role('separator');divider.focus();divider.press('ArrowDown');ratio=state()['tabs'][0]['ratio'];main_scroll=scrolls()
    select('Side Dish');button('Full View').click();scale('3×');page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=500');side_scroll=scrolls()
    select('Sauce');pane_scroll(85,350);sauce_scroll=scrolls();select('Main One')
    assert state()['tabs'][0]['ratio']==ratio and scrolls()==main_scroll
    select('Side Dish');assert button('Split View').count()==1 and scrolls()==side_scroll
    assert ingredient().inner_text().startswith('3 cup')
    select('Sauce');assert scrolls()==sauce_scroll;select('Main One')
    # Tuesday/Friday persisted completion and manual ingredient choices remain separate.
    for n in range(3):step(n).click()
    ingredient().click();tuesday=occurrence('Tuesday');assert len(tuesday['steps'])==3
    scale('2×');close();op(1,'Friday');assert not state()['progress'];assert ingredient().inner_text().startswith('1 cup')
    step().click();friday=occurrence('Friday');assert len(friday['steps'])==1
    close();op();assert len(state()['progress']['steps'])==3 and ingredient().get_attribute('aria-pressed')=='true'
    assert ingredient().inner_text().startswith('2 cup')
    close();op(1,'Friday');assert len(state()['progress']['steps'])==1 and ingredient().get_attribute('aria-pressed')=='false'
    groceries=page.evaluate('tabTest.groceries()');rice=[g for g in groceries if g.get('quantity',{}).get('name')=='rice'];assert rice and rice[0]['line']=='3 cups rice'
    assert page.evaluate('tabTest.content().ingredients[0]')=='1 cup rice'
    # Scheduled side: own parent/day; same recipe as main uses a distinct occurrence.
    close();op();select('Side Dish');step().click();side_tue=occurrence('Tuesday',2,'1');assert len(side_tue['steps'])==1
    close();op(1,'Friday');select('Side Dish');assert not state()['progress'];step(1).click();side_fri=occurrence('Friday',2,'1')
    close();op(4,'Thursday');select('Side Dish');assert state()['context']['parentId']=='4' and not state()['progress'];step(2).click()
    close();op(4,'Tuesday');select('Side Dish');assert state()['context'] is None;assert not state()['progress']['steps'];assert page.locator('.recipe-occurrence-notice').is_visible()
    # Unscheduled states are deck-local, stable across tab close/reopen, and never persisted.
    step().click();ingredient().click();scale('2×');sessions=state()['sessions'];button('Close Side Dish tab').click();linked('Side Dish')
    assert len(state()['progress']['steps'])==1 and state()['progress']['ingredientOverrides'];assert ingredient().inner_text().startswith('2 cup')
    assert state()['sessions']==sessions
    close();op(4,'Tuesday');select('Side Dish');assert state()['context'] is None and not state()['progress']['steps']
    close();op(1,None);select('Side Dish');assert not state()['context'] and not state()['progress']['steps']
    step().click();close();op(4,None);select('Side Dish');assert not state()['progress']['steps']
    close();page.evaluate('tabTest.links(4,[2,1])');op(4,'Thursday');select('Main One');assert state()['context']['parentId']=='4';assert not state()['progress'];step(3).click()
    close();op(1,'Tuesday','4');assert state()['context']['parentId']=='' and len(state()['progress']['steps'])==3
    close();page.evaluate('tabTest.links(3,[99])');op();select('Side Dish');linked('Nested Recipe');step().click();button('Close Nested Recipe tab').click()
    select('Sauce');linked('Nested Recipe');assert state()['context'] is None and not state()['progress']['steps'];button('Close Nested Recipe tab').click()
    select('Side Dish');linked('Nested Recipe');assert len(state()['progress']['steps'])==1
    close();op(1,'Friday');assert len(state()['progress']['steps'])==1
    # Reset only active occurrence; cycle only Tuesday and its associated links/scales.
    close();op();before_fri=occurrence('Friday');before_side=occurrence('Tuesday',2,'1');button('Reset Progress').click()
    assert state()['progress'] is None and occurrence('Friday')==before_fri and occurrence('Tuesday',2,'1')==before_side
    assert ingredient().inner_text().startswith('2 cup')
    step().click();page.evaluate("tabTest.cycle('Tuesday')");assert occurrence('Tuesday') is None and occurrence('Tuesday',2,'1') is None
    assert occurrence('Friday')==before_fri and occurrence('Friday',2,'1')==side_fri
    # Link editing draft blocks switching. Saving associations doesn't rewrite other progress.
    close();op(1,'Friday');before=state()['sessions'];hold();assert page.locator('.recipe-link-edit-bar').is_visible()
    select('Side Dish');assert state()['active']=='1';assert page.get_by_role('status').filter(has_text='Save or cancel').count()==1
    page.locator('.recipe-link-ingredient input').first.set_checked(True);button('Save ingredient links').click();assert state()['sessions']==before
    # Sync highlights and future auto-completion work; tab switching itself changes neither scroll nor marks.
    if button('Split View').count():button('Split View').click()
    option('Sync Ingredients',True);option('Auto-complete Ingredients',True);step().click();step().click();page.wait_for_timeout(450)
    assert ingredient().get_attribute('aria-pressed')=='true'
    ingredient().click();assert ingredient().get_attribute('aria-pressed')=='false'
    pane_scroll(110,220);saved=scrolls();before=state()['sessions'];select('Sauce');select('Main One');page.wait_for_timeout(450)
    assert scrolls()==saved and state()['sessions']==before and ingredient().get_attribute('aria-pressed')=='false'
    page.locator('.recipe-instructions-pane').evaluate('(e)=>{e.scrollTop=0;e.dispatchEvent(new WheelEvent("wheel",{deltaY:-1,bubbles:true}))}');page.wait_for_timeout(250)
    assert page.locator('.recipe-sync-relevant').count()>0
    # Edit Recipe acts on active tab and restores every open tab on Cancel and Save.
    select('Side Dish');pane_scroll(77,199);saved=scrolls();button('Edit Recipe').click();page.locator('#cancel').click();assert tabs().count()==3 and state()['active']=='2';assert scrolls()==saved
    button('Edit Recipe').click();field=page.locator('#recipeInstructions');field.fill(field.input_value()+'\nNewly added step stays incomplete.');page.locator('#save').click()
    assert tabs().count()==3 and state()['active']=='2';assert step(40).get_attribute('aria-pressed')=='false'
    assert occurrence('Friday') is not None and occurrence('Friday',2,'1')==side_fri
    # Keep awake belongs to the viewer, not individual tabs (mocked browser API).
    option('Keep Screen Awake',True);page.wait_for_timeout(50);requests=page.evaluate('wakeCalls.request');assert requests>=1
    select('Main One');select('Side Dish');assert page.evaluate('wakeCalls.request')==requests
    option('Keep Screen Awake',False);assert page.evaluate('wakeCalls.release')>=1
    # Backup validation/restore uses existing V1 storage, including preference and occurrence keys.
    backup=page.evaluate('tabBackup.capture()');page.evaluate('(b)=>tabBackup.validate(b)',backup)
    page.evaluate('(k)=>localStorage.setItem(k,JSON.stringify({version:1,occurrences:{}}))',prefix+'mealRotationCookingSessionsV1')
    page.evaluate('(b)=>tabBackup.restore(b)',backup)
    assert page.evaluate('tabBackup.capture()')==backup
    # Many long titles, narrow horizontal scrolling, roving keyboard targets, missing link.
    close();page.evaluate('tabTest.many()');rotation={m['id']:m['rotation'] for m in state()['meals']};op();assert tabs().count()==15
    if width<600:
        client=context.new_cdp_session(page);box=page.locator('.recipe-tab-strip').bounding_box();x=box['x']+box['width']-20;y=box['y']+22
        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
        for delta in [40,80,120,180]:
            client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-delta,'y':y}]});page.wait_for_timeout(30)
        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(100)
        assert page.locator('.recipe-tab-strip').evaluate('(e)=>e.scrollLeft')>0 and tabs().count()==15
    last=tabs().last;last.focus();last.press('Enter');assert state()['active']=='21'
    box=page.locator('.recipe-tab-strip').bounding_box();selected=page.locator('.recipe-tab.active').bounding_box();assert selected['x']>=box['x']-1 and selected['x']+selected['width']<=box['x']+box['width']+1
    for b in page.locator('.recipe-tab-close').all():assert b.bounding_box()['width']>=44 and b.bounding_box()['height']>=44
    assert {m['id']:m['rotation'] for m in state()['meals']}==rotation
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if filename=='index.html' and width<600:page.screenshot(path='/workspace/recipe-tabs-mobile.png')
    close();assert page.locator('#recipeViewer').count()==0
    page.evaluate('tabTest.historyOpen()');select('Side Dish');page.go_back();page.wait_for_selector('#recipeViewer',state='detached');page.go_forward();page.wait_for_selector('#recipeViewer');assert state()['active']=='1' and tabs().count()==15;close()
    # Preference persists after reload; neither progress nor original quantities are migrated.
    page.evaluate("window.history.replaceState({},'')");page.reload();assert state()['prefs']['autoOpenLinkedRecipes'] is True;op();assert tabs().count()==15
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationCookingSessionsV1")') is None
    assert not errors,errors
    print(f'PASS {filename} {width}px: tabs, auto-open, close/reopen, scroll/modes/ratio, Tue/Fri progress+scale+groceries, scheduled/unscheduled links, reset/cycle, editing/associations, sync/overrides, wake lock mock, backups, mobile layout; no JS errors',flush=True)
    context.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width in [360,1280]:run(browser,filename,width)
        browser.close()
