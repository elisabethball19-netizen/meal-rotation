"""Issue #12: orientation transitions and both divider axes on isolated Android touch data."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from recipe_tab_reorder_browser import MEALS,HOOK,NAMES
ROOT=Path(__file__).resolve().parents[1]

def run(browser,filename,w,h):
 ctx=browser.new_context(viewport={'width':w,'height':h},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36')
 page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else '';storage='testStorage' if prefix else 'localStorage'
 extra="""window.orientationTest={state:()=>({landscape:recipeViewer.cover.classList.contains('recipe-landscape'),ratio:recipeSplitRatio(),portrait:recipeViewer.activeTab.ratio,width:recipeViewer.activeTab.landscapeRatio,held:recipeViewer.syncGeometryHold,divider:recipeViewer.syncDividerDragging,tokens:recipeViewer.ingredientSyncState?.tokens,order:recipeViewer.tabs.map(t=>t.mealId)}),place:(pane,n,fraction=0)=>{const p=recipeViewer.content.querySelector(pane),el=p.querySelectorAll('[data-cooking-token]')[n];p.scrollTop+=el.getBoundingClientRect().top-p.getBoundingClientRect().top+el.getBoundingClientRect().height*fraction},anchor:pane=>{const p=recipeViewer.content.querySelector(pane),box=p.getBoundingClientRect(),el=[...p.querySelectorAll('[data-cooking-token]')].find(e=>e.getBoundingClientRect().bottom>box.top+1),rect=el?.getBoundingClientRect();return {token:el?.dataset.cookingToken,fraction:rect?Math.max(0,(box.top-rect.top)/rect.height):0,scroll:p.scrollTop}},hold:()=>{recipeViewer.syncGeometryHold=true;recipeViewer.cancelIngredientSync?.()}};"""
 src=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage',storage)+extra+'})();')
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides'],active='Main',meals=MEALS)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main'],'Friday':['Main']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=True,keepScreenAwake=False))}
 if prefix:seed['mealRotationDataV1']='production-sentinel'
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
 page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
 page.route('https://**/*',lambda r:r.fulfill(status=200,body=''));page.goto('http://meal.test/'+filename);cdp=ctx.new_cdp_session(page)
 def state():return page.evaluate('reorderTest.state()')
 def axis():return page.evaluate('orientationTest.state()')
 def saved():return page.evaluate('reorderTest.saved()')
 def button(name):return page.get_by_role('button',name=name,exact=True)
 def touch(kind,x=0,y=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':0}]})
 def anchor(pane):return page.evaluate('(p)=>orientationTest.anchor(p)',pane)
 def position():
  page.evaluate('orientationTest.hold();orientationTest.place(".recipe-ingredients-pane",20,.25);orientationTest.place(".recipe-instructions-pane",10,.3)');page.wait_for_timeout(100)
  return [anchor(p) for p in ['.recipe-ingredients-pane','.recipe-instructions-pane']]
 def check_place(before):
  for old,p in zip(before,['.recipe-ingredients-pane','.recipe-instructions-pane']):
   now=anchor(p);assert now['token']==old['token'],(old,now,axis());assert abs(now['fraction']-old['fraction'])<.06,(old,now)
 def geometry(side):
  rects=page.evaluate("[...document.querySelectorAll('.recipe-ingredients-pane,.recipe-divider,.recipe-instructions-pane')].map(e=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom}})")
  a,d,b=rects
  if side:assert a['right']<=d['x']+1 and d['right']<=b['x']+1 and abs(a['y']-b['y'])<1 and min(a['w'],b['w'])>=150 and min(a['h'],b['h'])>=65,rects
  else:assert a['bottom']<=d['y']+1 and d['bottom']<=b['y']+1 and abs(a['x']-b['x'])<1,rects
  assert page.locator('.recipe-divider').get_attribute('aria-orientation')==('vertical' if side else 'horizontal')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 def rotate(width,height,side):
  before=saved();old=state();order=axis()['order'];page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(300);assert axis()['landscape'] is side
  if state()['mode']=='split':geometry(side)
  else:assert page.locator('.recipe-divider').is_hidden()
  assert state()['active']==old['active'] and state()['context']==old['context'] and axis()['order']==order
  assert saved()==before,'Rotation must not write recipe/progress/scale/preferences data'
 def drag(dx,dy):
  b=page.locator('.recipe-divider').bounding_box();x=b['x']+b['width']/2;y=b['y']+b['height']/2
  touch('touchStart',x,y)
  for n in range(1,9):touch('touchMove',x+dx*n/8,y+dy*n/8);page.wait_for_timeout(25)
  touch('touchEnd');page.wait_for_timeout(120);assert not axis()['divider']
 page.evaluate('reorderTest.open()');page.wait_for_timeout(120);geometry(False);assert axis()['portrait']==.4 and axis()['width']==.5
 page.locator('.recipe-viewer-steps .cooking-item').nth(1).tap();button('Scale Recipe').tap();page.get_by_role('menuitemradio',name='2×',exact=True).tap()
 page.locator('.recipe-viewer-ingredients .cooking-item').first.tap();page.evaluate('reorderTest.link(2);reorderTest.select(1)');page.wait_for_timeout(120)
 drag(0,50);portrait=axis()['portrait'];assert portrait>.4
 # Enable existing sync/automatic behavior, then establish explicit reading positions.
 button('Recipe settings').tap();page.get_by_label('Sync Ingredients',exact=True).check();button('Close settings').tap();page.wait_for_timeout(240)
 before=position();progress=state()['sessions'];scales=state()['scales'];tokens=axis()['tokens']
 rotate(h,w,True);check_place(before);assert axis()['width']==.5 and axis()['portrait']==portrait and axis()['held']
 assert state()['sessions']==progress and state()['scales']==scales and axis()['tokens']==tokens
 before=position();drag(70,0);width_ratio=axis()['width'];assert width_ratio>.5 and axis()['portrait']==portrait;check_place(before)
 # Both panes scroll natively and independently in landscape.
 for pane,other in [('.recipe-ingredients-pane','.recipe-instructions-pane'),('.recipe-instructions-pane','.recipe-ingredients-pane')]:
  # Holding sync here tests geometry/independent scrolling without asking synchronization to move the other pane.
  button('Recipe settings').tap();page.get_by_label('Sync Ingredients',exact=True).uncheck();button('Close settings').tap()
  p=page.locator(pane);o=page.locator(other);p.evaluate('(e)=>e.scrollTop=0');old=o.evaluate('(e)=>e.scrollTop');b=p.bounding_box();x=b['x']+35;y=b['bottom']-20 if 'bottom' in b else b['y']+b['height']-20
  touch('touchStart',x,y)
  for n in range(1,9):touch('touchMove',x,y-45*n/8);page.wait_for_timeout(30)
  page.wait_for_timeout(120);touch('touchEnd');page.wait_for_timeout(100)
  assert p.evaluate('(e)=>e.scrollTop')>3 and abs(o.evaluate('(e)=>e.scrollTop')-old)<1
 # Per-tab landscape widths and reading places survive switches and edit return.
 before=position();page.evaluate('reorderTest.select(2)');page.wait_for_timeout(150);assert axis()['width']==.5;drag(-45,0);child_ratio=axis()['width']
 page.evaluate('reorderTest.select(1)');page.wait_for_timeout(150);assert axis()['width']==width_ratio;check_place(before)
 button('Edit Recipe').tap();page.locator('#cancel').click();page.wait_for_timeout(150);assert axis()['width']==width_ratio and state()['active']=='1';check_place(before)
 # Touch tab reordering in landscape keeps the fixed anchor and active occurrence.
 tab=page.locator('.recipe-tab-strip').get_by_role('tab',name=NAMES[1],exact=True);tab.scroll_into_view_if_needed();b=tab.bounding_box();x=b['x']+30;y=b['y']+20;touch('touchStart',x,y);page.wait_for_timeout(620)
 for n in range(1,9):touch('touchMove',x+(20-x)*n/8,y);page.wait_for_timeout(25)
 touch('touchEnd');page.wait_for_timeout(70);assert axis()['order']==['2','1'] and state()['active']=='1';assert page.locator('.recipe-tab-anchor .recipe-tab-close').count()==0
 # Rotation during an unfinished touch resize cancels the gesture without changing the other orientation's ratio.
 b=page.locator('.recipe-divider').bounding_box();touch('touchStart',b['x']+20,b['y']+25);assert axis()['divider'];before=position();rotate(w,h,False);touch('touchEnd');assert not axis()['divider'];check_place(before)
 assert axis()['portrait']==portrait and axis()['width']==width_ratio
 before=position();rotate(h,w,True);check_place(before);assert axis()['width']==width_ratio
 # Keyboard axes, minimum widths and Full View still behave correctly.
 divider=page.locator('.recipe-divider');divider.focus();old=axis()['ratio'];divider.press('ArrowLeft');assert axis()['ratio']<old;divider.press('Home');geometry(True);divider.press('End');geometry(True)
 button('Full View').tap();assert divider.is_hidden();rotate(w,h,False);assert state()['mode']=='full';button('Split View').tap();geometry(False);assert axis()['portrait']==portrait
 # Ingredient-link editing keeps its draft, highlight and toolbar through rotation.
 rotate(h,w,True);page.evaluate('orientationTest.place(".recipe-instructions-pane",0,0)');page.wait_for_timeout(100)
 b=page.locator('.recipe-instructions-pane').bounding_box();touch('touchStart',b['x']+45,b['y']+18);page.wait_for_timeout(620);touch('touchEnd');page.wait_for_timeout(100)
 assert page.locator('.recipe-link-edit-bar').is_visible() and page.locator('.recipe-link-selected').count()==1
 assert page.locator('.recipe-ingredients-pane input[type=checkbox]').count()>0
 rotate(w,h,False);assert page.locator('.recipe-link-selected').count()==1
 rotate(h,w,True);assert page.locator('.recipe-link-edit-bar').is_visible();button('Cancel ingredient links').tap()
 assert not page.locator('.recipe-link-edit-bar').count()
 # Long content and short landscape height remain scrollable with accessible controls.
 assert button('Close recipe').is_visible() and button('Recipe settings').is_visible()
 if filename=='index.html':page.screenshot(path=f'/workspace/issue-12-work/landscape-{w}.png')
 assert state()['sessions']==progress and state()['scales']==scales
 button('Close recipe').tap();page.wait_for_selector('#recipeViewer',state='detached');page.evaluate('reorderTest.open("Friday")');page.wait_for_timeout(150)
 assert state()['context']['day']=='Friday' and not page.locator('.recipe-viewer-steps .cooking-item.cooking-complete').count()
 # Optional landscape preference is saved in the existing V1 key; portrait value remains separate.
 prefs=json.loads(saved()['mealRotationRecipeViewPrefsV1']);assert prefs['ratio']==portrait and 'landscapeRatio' in prefs
 if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='production-sentinel'
 assert not errors,errors
 print(f'PASS {filename} {w}x{h} ↔ {h}x{w}: automatic axes, semantic places, no rotation writes/completion/sync jump, touch resizing, independent scroll, per-tab/orientation ratios, editor return, cancel on rotation, keyboard/minima, Full View, progress/scale isolation; no JS errors',flush=True)
 ctx.close()


def layout_guards(browser,filename):
 for touch,width,height in [(False,1000,500),(True,1024,768)]:
  ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=touch,is_mobile=False);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else '';storage='testStorage' if prefix else 'localStorage'
  src=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage',storage)+'})();')
  seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides'],active='Main',meals=MEALS)),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,keepScreenAwake=False))}
  page.add_init_script('for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);')
  page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''));page.goto('http://meal.test/'+filename);page.evaluate('reorderTest.open()');page.wait_for_timeout(120)
  assert not page.locator('#recipeViewer').evaluate('(e)=>e.classList.contains("recipe-landscape")')
  assert page.locator('.recipe-divider').get_attribute('aria-orientation')=='horizontal'
  assert not errors,errors;ctx.close()
 print('PASS',filename,'desktop and taller tablet keep their existing stacked layout',flush=True)

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for w,h in [(360,780),(320,640)]:run(b,filename,w,h)
   layout_guards(b,filename)
  b.close()
