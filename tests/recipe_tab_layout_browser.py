"""Issue #3 layout/settings tests. Hooks exist only in routed test responses."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
NAME='Automatically open linked recipes in tabs'
MEALS=[dict(id=i,name=name,cat='Main' if i!=2 else 'Side',rotation=i==1,linkedMealIds=[2] if i!=2 else [],ingredients=[f'{n+1} ingredient {i}-{n}' for n in range(65)],instructions=[f'Cook batch {i}-{n} for 15 minutes. '+('Stir slowly. '*8) for n in range(40)]) for i,name in [(1,'Crying Tiger'),(2,'Puerto Vallarta salsa roja'),(3,'Pneumonoultramicroscopicsilicovolcanoconiosis'*4)]]
HOOK="""window.layoutTest={open:(id=1)=>{window.history.replaceState({},'');const m=meals.find(m=>m.id===id);openRecipeViewer(m,id===1?cookingContext('original','Tuesday',m.cat,m):null,true)},state:()=>({prefs:recipeViewPrefs,meals,sessions:cookingSessions,scales:occurrenceScales,active:recipeViewer?.mealId,ratio:recipeViewer?.activeTab.ratio}),backup:()=>layoutBackup.capture()};"""

def run(browser,filename,width):
    context=browser.new_context(viewport={'width':width,'height':851},is_mobile=True,has_touch=True)
    page=context.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();').replace('function validateBackupCore(d){','window.layoutBackup={capture:captureBackupStorage,validate:validateBackupStorage};function validateBackupCore(d){')
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    plan=dict(id='original',name='Dinner',weekdayCategories={'Tuesday':['Main'],'Friday':['Main']},weekdayMealOverrides={},weekdayRecipeFilters={})
    seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Side'],active='Main',meals=MEALS)),prefix+'mealRotationPlansV1':json.dumps(dict(activeId='original',plans=[dict(id='breakfast',name='Breakfast',weekdayCategories={}),dict(id='lunch',name='Lunch',weekdayCategories={}),plan])),prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False))}
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
    page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
    page.goto('http://meal.test/'+filename)
    def state():return page.evaluate('layoutTest.state()')
    def op(i=1):page.evaluate('(id)=>layoutTest.open(id)',i);page.wait_for_timeout(80)
    def strip():return page.locator('.recipe-tab-strip')
    def tabs():return page.locator('.recipe-tab-strip [role=tab]')
    def select(name):strip().get_by_role('tab',name=name,exact=True).click()
    def button(name):return page.get_by_role('button',name=name,exact=True)
    def close():button('Close recipe').click();page.wait_for_selector('#recipeViewer',state='detached')
    def settings():
        page.locator('#settings').click();group=page.locator('#settingsPanel details[data-settings-group=display]')
        if not group.evaluate('(e)=>e.open'):group.locator('summary').click()
        return page.get_by_label(NAME,exact=True)
    def scrolls():return page.evaluate('({cover:document.querySelector("#recipeViewer").scrollTop,panes:[...document.querySelectorAll(".recipe-pane")].map(e=>e.scrollTop)})')
    # An old preferences record defaults off, without a second/new storage record.
    assert state()['prefs']['autoOpenLinkedRecipes'] is False
    assert page.get_by_label(NAME,exact=True).count()==1
    op();assert strip().is_hidden() and strip().bounding_box() is None
    assert tabs().first.text_content()=='Crying Tiger' and page.locator('.recipe-tab-close').count()==0
    title=page.locator('.recipe-header h1');assert title.inner_text()=='Crying Tiger'
    gap=title.bounding_box()['y']-(page.locator('.recipe-viewer-bar').bounding_box()['y']+page.locator('.recipe-viewer-bar').bounding_box()['height']);assert 0<=gap<=26,('no empty row under toolbar',gap,page.locator('.recipe-header').bounding_box())
    page.locator('.recipe-viewer-steps .cooking-item').first.click();button('Scale Recipe').click();page.get_by_role('menuitemradio',name='2×',exact=True).click()
    progress=state()['sessions'];scales=state()['scales'];original_meals=state()['meals']
    if filename=='index.html':page.screenshot(path=f'/workspace/recipe-tabs-single-{width}.png')
    button('Recipe settings').click();assert page.locator('#recipeViewerSettings').get_by_label(NAME,exact=True).count()==0;button('Close settings').click()
    # A linked recipe reveals the strip, and full accessible names survive abbreviation.
    page.locator('.recipe-linked-link').get_by_text('Puerto Vallarta salsa roja',exact=True).click();assert strip().is_visible() and tabs().count()==2
    assert all(not text.startswith('Main ·') for text in tabs().all_text_contents())
    assert tabs().nth(0).get_attribute('title')=='Crying Tiger';assert tabs().nth(1).get_attribute('aria-label')=='Puerto Vallarta salsa roja'
    assert page.locator('.recipe-header h1').inner_text()=='Puerto Vallarta salsa roja'
    close_tab=button('Close Puerto Vallarta salsa roja tab');assert close_tab.bounding_box()['width']>=44 and close_tab.bounding_box()['height']>=44
    # Shape, border and selected colors follow the existing Breakfast/Lunch/Dinner tabs.
    plan_style=page.locator('#list .meal-plan-tab.selected').first.evaluate('(e)=>({radius:getComputedStyle(e).borderTopLeftRadius,bg:getComputedStyle(e).backgroundColor})')
    recipe_style=page.locator('.recipe-tab.active').evaluate('(e)=>({radius:getComputedStyle(e).borderTopLeftRadius,bg:getComputedStyle(e).backgroundColor})');assert plan_style==recipe_style
    select('Crying Tiger');assert page.locator('.recipe-tab').first.locator('.recipe-tab-close').count()==0
    page.set_viewport_size({'width':320,'height':851});page.wait_for_timeout(80)
    assert strip().evaluate('(e)=>e.classList.contains("recipe-tabs-abbreviated")')
    assert tabs().all_text_contents()==['Crying T…','Puerto V…']
    assert page.locator('.recipe-header h1').inner_text()=='Crying Tiger'
    page.set_viewport_size({'width':360,'height':851});page.wait_for_timeout(80)
    if filename=='index.html':page.screenshot(path=f'/workspace/recipe-tabs-pair-{width}.png')
    # Test the actual measured threshold on both sides and on repeated resizes.
    low,high=300,850
    while high-low>1:
        mid=(low+high)//2;page.set_viewport_size({'width':mid,'height':851});page.wait_for_timeout(50)
        if strip().evaluate('(e)=>e.classList.contains("recipe-tabs-abbreviated")'):low=mid
        else:high=mid
    for w,abbreviated in [(high+2,False),(low-2,True),(high+2,False)]:
        page.set_viewport_size({'width':w,'height':851});page.wait_for_timeout(70)
        assert strip().evaluate('(e)=>e.classList.contains("recipe-tabs-abbreviated")') is abbreviated
        assert tabs().all_text_contents()==(['Crying T…','Puerto V…'] if abbreviated else ['Crying Tiger','Puerto Vallarta salsa roja'])
    page.set_viewport_size({'width':width,'height':851});page.wait_for_timeout(70)
    # Hiding the row on an inactive close preserves bottom scroll positions, ratio, and progress.
    for pane in ['.recipe-ingredients-pane','.recipe-instructions-pane']:page.locator(pane).evaluate('(e)=>e.scrollTop=e.scrollHeight')
    before=scrolls();ratio=state()['ratio'];close_tab.click();assert strip().is_hidden() and scrolls()==before
    assert state()['ratio']==ratio and state()['sessions']==progress and state()['scales']==scales
    # Closing the active last linked tab also hides the row and returns to the anchor.
    page.locator('.recipe-linked-link').get_by_text('Puerto Vallarta salsa roja',exact=True).click();close_tab.click();assert state()['active']=='1' and strip().is_hidden()
    assert state()['sessions']==progress and state()['scales']==scales
    # Full-view position and title remain intact when removing the redundant row.
    button('Full View').click();page.locator('.recipe-linked-link').get_by_text('Puerto Vallarta salsa roja',exact=True).click();select('Crying Tiger')
    page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=e.scrollHeight');before=scrolls();close_tab.click();assert strip().is_hidden() and scrolls()==before
    close()
    # Main Settings Cancel/Save use the current preference key, with one control only.
    check=settings();assert not check.is_checked();check.check();button('Cancel settings').click();assert state()['prefs']['autoOpenLinkedRecipes'] is False
    op();assert strip().is_hidden();close()
    settings().check();button('Save settings').click();assert state()['prefs']['autoOpenLinkedRecipes'] is True
    page.reload();check=settings();assert check.is_checked();button('Save settings').click()
    assert page.get_by_label(NAME,exact=True).count()==1
    op();assert tabs().count()==2 and strip().is_visible();assert state()['sessions']==progress and state()['scales']==scales
    assert state()['meals']==original_meals
    # One-word labels use normal CSS ellipsis instead of inventing a second word.
    close();op(3);assert tabs().first.text_content()==MEALS[2]['name']
    assert tabs().first.evaluate('(e)=>getComputedStyle(e).textOverflow')=='ellipsis';assert tabs().first.evaluate('(e)=>e.scrollWidth>e.clientWidth')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.locator('.recipe-viewer-bar>button').count()==4
    backup=page.evaluate('layoutTest.backup()');page.evaluate('(b)=>layoutBackup.validate(b)',backup)
    prefs=json.loads(backup['mealRotationRecipeViewPrefsV1']);assert prefs['autoOpenLinkedRecipes'] is True
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationRecipeViewPrefsV1")') is None
    assert not errors,errors
    print(f'PASS {filename} {width}px: hidden single row, screenshot pair, measured abbreviation threshold, single-word ellipsis, native tab styling, close targets, main settings Save/Cancel/persistence, scroll/progress/scaling/data preservation; no JS errors',flush=True)
    context.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width in [320,360,390]:run(browser,filename,width)
        browser.close()
