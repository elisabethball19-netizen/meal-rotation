"""Browser regression test; test hooks are injected in-memory, never shipped in the app."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from editor_sections_fixture import open_editor_section

ROOT = Path(__file__).resolve().parents[1]
HOOK = """window.linkTest={open:(day='Monday')=>openRecipeViewer(meals[0],cookingContext('original',day,'Chicken',meals[0])),state:()=>({links:validRecipeIngredientLinks(meals[0]),matches:[...recipeIngredientMatches(meals[0])],sessions:cookingSessions,edit:recipeViewer?.linkEdit?{step:recipeViewer.linkEdit.step,selected:[...recipeViewer.linkEdit.selected]}:null,prefs:recipeViewPrefs}),render:renderRecipeViewer,followFirst:()=>recipeViewer.syncToInstruction?.(cookingItemTokens(meals[0]).steps[0].token)};"""
MEAL = dict(id=1,cat='Chicken',name='Inline links regression recipe',rotation=True,ingredients=['1 onion','2 carrots','3 potatoes']+[f'{i+1} test vegetable {i}' for i in range(60)],instructions=['Cook onion and carrots.','Add potatoes.']+[f'Stir batch {i}. '+('Continue cooking slowly and stir carefully. '*8) for i in range(30)],notes='Long recipe end')

def run(browser, filename, mode):
    ctx=browser.new_context(viewport={'width':393,'height':851},device_scale_factor=2.75,is_mobile=True,has_touch=True)
    page=ctx.new_page(); errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();')
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    data={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Chicken'],active='Chicken',meals=[MEAL])),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode=mode,ratio=.43,syncIngredients=True,autoCompleteIngredients=True,keepScreenAwake=False)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Monday':['Chicken'],'Tuesday':['Chicken']})}
    page.add_init_script('if(!sessionStorage.seeded){for(const [k,v] of Object.entries('+json.dumps(data)+'))localStorage.setItem(k,v);sessionStorage.seeded="1";}')
    page.route('http://meal.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=source) if route.request.url.split('?')[0].endswith(filename) else route.fulfill(status=200,body=''))
    page.goto('http://meal.test/'+filename)
    page.evaluate('linkTest.open()');page.wait_for_timeout(250)
    def state(): return page.evaluate('linkTest.state()')
    def step(n=0): return page.locator('.recipe-viewer-steps .cooking-item').nth(n)
    def ing(n=0): return page.locator('.recipe-viewer-ingredients .cooking-item').nth(n)
    def hold(n=0):
        step(n).scroll_into_view_if_needed();box=step(n).bounding_box();page.mouse.move(box['x']+20,box['y']+15);page.mouse.down();page.wait_for_timeout(650)
        assert state()['edit'], 'Mode must begin before release'
        page.mouse.up();page.wait_for_timeout(70)
    def save(): page.get_by_role('button',name='Save ingredient links',exact=True).click()
    def cancel(): page.get_by_role('button',name='Cancel ingredient links',exact=True).click()
    def checks(): return page.locator('.recipe-link-ingredient input').evaluate_all('(els)=>els.map(e=>e.checked)')
    # Touch input activates before release; movement cancels the hold.
    client=ctx.new_cdp_session(page)
    step().scroll_into_view_if_needed();box=step().bounding_box();x,y=box['x']+20,box['y']+15
    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    page.wait_for_timeout(650);assert state()['edit']
    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    page.wait_for_timeout(100);assert step().get_attribute('aria-pressed')=='false';cancel()
    step().scroll_into_view_if_needed();box=step().bounding_box();x,y=box['x']+20,box['y']+15
    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+35}]})
    page.wait_for_timeout(650)
    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    assert state()['edit'] is None
    # Normal cooking taps and independent initial occurrence progress.
    step().click();assert step().get_attribute('aria-pressed')=='true'
    step().click();assert step().get_attribute('aria-pressed')=='false'
    ing(2).click();first=state()['sessions']
    hold();assert checks()[:3]==[True,True,False];assert state()['sessions']==first
    assert step().evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(237, 243, 251)'
    step().click();assert state()['sessions']==first
    page.locator('.recipe-link-ingredient').nth(0).click()
    page.locator('.recipe-link-ingredient').nth(2).click()
    assert checks()[:3]==[False,True,True];assert state()['sessions']==first
    # A second held instruction must preserve the draft and provide inline feedback.
    old=state()['edit'];hold(1);assert state()['edit']==old
    assert page.get_by_role('status').filter(has_text='Save or cancel').count()==1
    save();assert state()['sessions']==first
    assert len(state()['links'])==1
    if mode=='split':
        page.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop=e.scrollHeight')
        page.locator('.recipe-instructions-pane').evaluate('(e)=>{e.scrollTop=0;e.dispatchEvent(new WheelEvent("wheel",{deltaY:-1,bubbles:true}))}');page.wait_for_timeout(600)
        assert ing(1).evaluate('(e)=>e.classList.contains("recipe-sync-relevant")')
        assert not ing(0).evaluate('(e)=>e.classList.contains("recipe-sync-relevant")')
        page.wait_for_function('(()=>{const p=document.querySelector(".recipe-ingredients-pane"),b=p.querySelector(".recipe-sync-relevant");return b.getBoundingClientRect().top>=p.getBoundingClientRect().top})()',timeout=3000)
    page.get_by_role('button',name='Close recipe',exact=True).click();page.wait_for_timeout(100)
    page.evaluate('linkTest.open()');hold();assert checks()[:3]==[False,True,True]
    page.locator('.recipe-link-ingredient').nth(1).click();cancel();hold();assert checks()[:3]==[False,True,True];cancel()
    # Shared recipe links, independent progress; persistence through reload.
    page.get_by_role('button',name='Close recipe',exact=True).click();page.wait_for_timeout(100)
    page.reload();page.evaluate("linkTest.open('Tuesday')");assert ing(2).get_attribute('aria-pressed')=='false'
    hold();assert checks()[:3]==[False,True,True];cancel();step().click();page.wait_for_timeout(450)
    if mode=='split':
        assert ing(1).get_attribute('aria-pressed')=='true', 'updated automatic completion'
        assert ing(0).get_attribute('aria-pressed')=='false'
        assert ing(1).evaluate('(e)=>e.classList.contains("recipe-sync-relevant")') or ing(2).evaluate('(e)=>e.classList.contains("recipe-sync-relevant")')
    # Edit Recipe consumes exactly the same saved override.
    page.get_by_role('button',name='Edit Recipe',exact=True).click()
    open_editor_section(page,'recipe');page.locator('#recipeIngredientLinks summary').click()
    assert page.get_by_label('Ingredient matching',exact=True).input_value()=='manual'
    assert page.locator('.recipe-link-choices input').evaluate_all('(els)=>els.slice(0,3).map(e=>e.checked)')==[False,True,True]
    page.locator('#cancel').click();page.wait_for_timeout(100)
    # Restore automatic matching, save, and verify original matches and marks unchanged.
    prior=state()['sessions'];hold();page.get_by_role('button',name='Use Automatic Matching',exact=True).click()
    assert checks()[:3]==[True,True,False];save();assert state()['links']==[];assert state()['sessions']==prior
    # Toolbar and long-content reachability, independent scrolling, divider ratio and offsets.
    hold();ratio=state()['prefs']['ratio']
    if mode=='split':
        page.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop=e.scrollHeight')
        before=page.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop')
        page.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=e.scrollHeight')
        assert page.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop')==before
    else: page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=e.scrollHeight')
    bar=page.locator('.recipe-link-edit-bar').bounding_box()
    assert bar['y']+bar['height']<=852 and bar['y']>=0
    end=page.get_by_text('Long recipe end',exact=True).bounding_box();assert end['y']+end['height']<=bar['y']+1
    if mode=='split':
        last=ing(62).bounding_box();pane=page.locator('.recipe-ingredients-pane').bounding_box();assert last['y']+last['height']<=pane['y']+pane['height']+1
    scrolls=page.locator('.recipe-pane').evaluate_all('(els)=>els.map(e=>e.scrollTop)')
    fullscroll=page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop')
    if filename=='index.html' and mode=='split':page.screenshot(path=str(ROOT/'tests/inline-links-mobile.png'))
    cancel();assert state()['prefs']['ratio']==ratio
    assert page.locator('.recipe-pane').evaluate_all('(els)=>els.map(e=>e.scrollTop)')==scrolls
    assert abs(page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop')-fullscroll)<1
    assert not errors, errors
    print(f'PASS {filename} {mode}: persistence, cancel, automatic, gestures, progress, occurrences, editor, long content, toolbar, scroll positions; no JS errors')
    ctx.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for file in ['index.html','meal-rotation-test.html']:
            for mode in ['split','full']:run(browser,file,mode)
        browser.close()
