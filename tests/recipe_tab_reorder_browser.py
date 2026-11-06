"""Issue #3 touch reorder regressions; hooks are injected into isolated browser responses."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
NAMES=['Crying Tiger','Puerto Vallarta salsa roja','Cilantro Sauce','Sesame','A long additional recipe','Another side dish','Final garnish']
MEALS=[dict(id=i,name=name,cat='Main' if i==1 else 'Sides',rotation=i==1,linkedMealIds=list(range(2,8)) if i==1 else [1],ingredients=[f'{n+1} ingredient {i}-{n}' for n in range(70)],instructions=[f'Cook ingredient {i}-{n} for {n+1} minutes. '+('Stir carefully. '*8) for n in range(45)]) for i,name in enumerate(NAMES,1)]
HOOK="""window.reorderTest={open:(day='Tuesday')=>{window.history.replaceState({},'');const m=meals.find(m=>m.id===1);openRecipeViewer(m,cookingContext('original',day,m.cat,m))},link:(id)=>openLinkedRecipeTab(meals.find(m=>m.id===id)),select:(id)=>switchRecipeTab(recipeViewer.tabs.find(t=>t.mealId===String(id))),close:(id)=>closeLinkedRecipeTab(recipeViewer.tabs.find(t=>t.mealId===String(id))),state:()=>({order:recipeViewer.tabs.map(t=>t.mealId),anchor:recipeViewer.anchorTab.mealId,active:recipeViewer.mealId,context:recipeViewer.context,sessions:cookingSessions,scales:occurrenceScales,mode:recipeViewingMode(),ratio:recipeViewer.activeTab.ratio,scroll:{cover:recipeViewer.cover.scrollTop,panes:[...recipeViewer.content.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop)},tabState:recipeViewer.tabs.map(t=>({id:t.mealId,mode:t.mode,ratio:t.ratio,panes:t.paneScroll,full:t.coverScroll,preview:t.previewProgress}))}),saved:()=>Object.fromEntries(['mealRotationDataV1','mealRotationCookingSessionsV1','mealRotationOccurrenceScalesV1','mealRotationRecipeViewPrefsV1'].map(k=>[k,localStorage.getItem(k)]))};"""

def run(browser,filename,width):
 ctx=browser.new_context(viewport={'width':width,'height':851},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36')
 page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
 source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides'],active='Main',meals=MEALS)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main'],'Friday':['Main']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False))}
 if prefix:seed['mealRotationDataV1']='working-data-sentinel'
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
 page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
 page.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 page.goto('http://meal.test/'+filename);cdp=ctx.new_cdp_session(page)
 def state():return page.evaluate('reorderTest.state()')
 def saved():return page.evaluate('reorderTest.saved()')
 def strip():return page.locator('.recipe-tab-strip')
 def button(name):return page.get_by_role('button',name=name,exact=True)
 def tab(i):return strip().get_by_role('tab',name=NAMES[i-1],exact=True)
 def touch(kind,x=0,y=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':0}]})
 def start(i,hold=True):
  tab(i).scroll_into_view_if_needed();b=tab(i).bounding_box();s=strip().bounding_box();x=max(s['x']+12,min(s['x']+s['width']-12,b['x']+min(25,b['width']/2)));y=b['y']+b['height']/2
  touch('touchStart',x,y)
  if hold:page.wait_for_timeout(620)
  return x,y
 def drag(i,right=True,wait=800,cancel=False):
  before=state();before_saved=saved();x,y=start(i);s=strip().bounding_box();target=s['x']+s['width']-3 if right else s['x']+3
  for n in range(1,9):touch('touchMove',x+(target-x)*n/8,y);page.wait_for_timeout(18)
  page.wait_for_timeout(wait);touch('touchCancel' if cancel else 'touchEnd');page.wait_for_timeout(80)
  after=state();assert after['active']==before['active'] and after['anchor']=='1';assert after['context']==before['context'];assert after['sessions']==before['sessions'] and after['scales']==before['scales'];assert saved()==before_saved
  assert after['scroll']==before['scroll'],(before['scroll'],after['scroll'])
  assert page.locator('.recipe-tab-drag-preview').count()==0 and page.locator('.recipe-tab-dragging').count()==0
  return before,after
 page.evaluate('reorderTest.open()');assert strip().is_hidden()
 # Main scheduled marks/scaling differ from linked occurrence marks/scaling.
 page.locator('.recipe-viewer-steps .cooking-item').first.click();button('Scale Recipe').click();page.get_by_role('menuitemradio',name='2×',exact=True).click()
 page.evaluate('reorderTest.link(2)');page.locator('.recipe-viewer-steps .cooking-item').nth(2).click();button('Scale Recipe').click();page.get_by_role('menuitemradio',name='½×',exact=True).click()
 page.evaluate('reorderTest.link(3);reorderTest.select(2)')
 page.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop=160');page.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=220')
 # Move the nonactive anchor from first to last; active occurrence and pane positions stay intact.
 before,after=drag(1);assert after['order']==['2','3','1'],after
 assert page.locator('.recipe-tab-anchor .recipe-tab-close').count()==0
 assert strip().get_by_role('button',name='Close Puerto Vallarta salsa roja tab').count()==1
 assert 'Main' not in ''.join(strip().get_by_role('tab').all_text_contents())
 assert [t['id'] for t in after['tabState']]==after['order']
 # Moving a linked tab around the anchor also keeps active selection unchanged.
 before,after=drag(3,right=False);assert after['order'][0]=='3',after
 # Active tabs can also move without selecting another occurrence.
 before,after=drag(2);assert after['order'][-1]=='2' and after['active']=='2'
 # Cancellation rolls back order. A held press alone cannot select an inactive tab.
 before,after=drag(1,right=False,cancel=True);assert after['order']==before['order']
 old=state();x,y=start(1);touch('touchEnd');page.wait_for_timeout(70);assert state()['active']==old['active'] and state()['order']==old['order']
 # Link back to anchor selects that recipe, regardless of its position, without duplicating it.
 page.evaluate('reorderTest.link(1)');assert state()['active']=='1' and state()['order']==old['order']
 page.evaluate('reorderTest.select(2)');assert state()['scroll']['panes']==[160,220]
 # Edit Recipe returns to the same reordered deck, anchor and active occurrence.
 order=state()['order'];prior=state();button('Edit Recipe').click();page.get_by_role('dialog',name='Edit Recipe',exact=True).get_by_role('button',name='Cancel',exact=True).click();assert state()['order']==order and state()['active']=='2' and state()['anchor']=='1';assert state()['scroll']==prior['scroll']
 button('Edit Recipe').click();page.get_by_role('dialog',name='Edit Recipe',exact=True).get_by_role('button',name='Save recipe',exact=True).click();assert state()['order']==order and state()['active']=='2' and state()['anchor']=='1'
 # Keyboard navigation follows the new order rather than stale creation indices.
 tab(2).focus();tab(2).press('ArrowRight');assert state()['active']==order[(order.index('2')+1)%len(order)]
 page.evaluate('reorderTest.select(2)');order=state()['order'];button('Close Cilantro Sauce tab').tap();assert state()['order']==[x for x in order if x!='3'] and state()['active']=='2'
 button('Close Puerto Vallarta salsa roja tab').tap();assert state()['active']=='1' and strip().is_hidden()
 # Opening/reopening appends only that tab; closing active linked returns to the fixed anchor.
 page.evaluate('reorderTest.link(2);reorderTest.link(3)');assert state()['order']==['1','2','3']
 # Many tabs: short touch swipe scrolls without reordering or selecting.
 for i in range(4,8):page.evaluate('(id)=>reorderTest.link(id)',i)
 page.evaluate('reorderTest.select(2)');strip().evaluate('(e)=>e.scrollLeft=0');old=state()['order'];active=state()['active'];x,y=start(1,False)
 for n in range(1,9):touch('touchMove',x-80*n/8,y);page.wait_for_timeout(15)
 touch('touchEnd');page.wait_for_timeout(50);assert state()['order']==old and state()['active']==active;assert strip().evaluate('(e)=>e.scrollLeft')>0
 # Real touch edge autoscroll moves anchor through offscreen tabs in both directions.
 strip().evaluate('(e)=>e.scrollLeft=0');before,after=drag(1,wait=2300);assert after['order'][-1]=='1',after
 assert strip().evaluate('(e)=>e.scrollLeft')>0
 before,after=drag(1,right=False,wait=2300);assert after['order'][0]=='1',after
 # An action during a held drag cancels the tentative move before closing its target.
 old=state()['order'];strip().evaluate('(e)=>e.scrollLeft=0');x,y=start(1);touch('touchMove',width-25,y);page.wait_for_timeout(180)
 page.evaluate('reorderTest.close(3)');touch('touchEnd');assert state()['order']==[x for x in old if x!='3'] and state()['active']=='2'
 # Full View uses the same drag; recipe scroll stays fixed while strip moves.
 button('Full View').click();page.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=280');strip().evaluate('(e)=>e.scrollLeft=0')
 before,after=drag(1,wait=2300);assert after['order'][-1]=='1' and after['mode']=='full'
 if filename=='index.html':page.screenshot(path=f'/workspace/recipe-tabs-reordered-{width}.png')
 # Close controls remain tappable after reorder and only remove their own linked tab.
 order=state()['order'];page.evaluate('reorderTest.close(4)');assert state()['order']==[x for x in order if x!='4']
 # Main cannot be closed even by the shared action, despite its new last position.
 old=state()['order'];page.evaluate('reorderTest.close(1)');assert state()['order']==old
 button('Close recipe').click();page.wait_for_selector('#recipeViewer',state='detached');page.evaluate('reorderTest.open("Friday")');assert strip().is_hidden() and state()['order']==['1'];assert state()['context']['day']=='Friday'
 assert not page.locator('.recipe-viewer-steps .cooking-item.cooking-complete').count()
 if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='working-data-sentinel'
 assert not errors,errors
 print(f'PASS {filename} {width}px Android touch: anchor/linked drag, cancellation, short swipe/edge scrolling, Full/Split positions, unchanged active occurrence/progress/scales/relationships, keyboard order, editor return, close/reopen order, session reset; no JS errors',flush=True)
 ctx.close()

if __name__=='__main__':
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360,390]:run(browser,filename,width)
  browser.close()

