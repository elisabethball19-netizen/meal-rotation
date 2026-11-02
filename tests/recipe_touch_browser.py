"""Issue #11: touch ownership/cancellation regressions and slim divider, isolated data."""
import json,subprocess,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from recipe_tab_reorder_browser import MEALS,HOOK,NAMES
ROOT=Path(__file__).resolve().parents[1]
BASELINE='--baseline' in sys.argv

def run(browser,filename,width):
 ctx=browser.new_context(viewport={'width':width,'height':851},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36')
 page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else '';storage='testStorage' if prefix else 'localStorage'
 raw=subprocess.check_output(['git','show','5560ae5fe4433bc222fdc2eb270a53bfc76362de:'+filename],cwd=ROOT,text=True) if BASELINE else (ROOT/filename).read_text()
 extra="""window.touchTest={flags:()=>({tab:!!recipeViewer?.tabDragging,divider:!!recipeViewer?.syncDividerDragging})};window.touchAudit={pointer:0,moves:[],clicks:0};document.addEventListener('pointerdown',e=>{if(e.pointerType==='touch')touchAudit.pointer=e.pointerId},{capture:true});document.addEventListener('touchmove',e=>touchAudit.moves.push(e.defaultPrevented),{passive:true});document.addEventListener('click',e=>{if(e.target.closest('.recipe-tab-strip button'))touchAudit.clicks++},{capture:true});"""
 source=raw.replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage',storage)+extra+'})();')
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides'],active='Main',meals=MEALS)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main'],'Friday':['Main']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False))}
 if prefix:seed['mealRotationDataV1']='production-sentinel'
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
 page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
 page.route('https://**/*',lambda r:r.fulfill(status=200,body=''));page.goto('http://meal.test/'+filename)
 cdp=ctx.new_cdp_session(page)
 def touch(kind,x=0,y=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':0}]})
 def state():return page.evaluate('reorderTest.state()')
 def saved():return page.evaluate('reorderTest.saved()')
 def strip():return page.locator('.recipe-tab-strip')
 def button(label):return page.get_by_role('button',name=label,exact=True)
 def tab(i):return strip().get_by_role('tab',name=NAMES[i-1],exact=True)
 def swipe(x,y,dx,dy=0):
  touch('touchStart',x,y)
  for n in range(1,9):touch('touchMove',x+dx*n/8,y+dy*n/8);page.wait_for_timeout(30)
  page.wait_for_timeout(120);touch('touchEnd');page.wait_for_timeout(100)
 page.evaluate('reorderTest.open()');page.locator('.recipe-viewer-steps .cooking-item').first.tap();button('Scale Recipe').tap();page.get_by_role('menuitemradio',name='2×',exact=True).tap()
 for i in range(2,8):page.evaluate('(i)=>reorderTest.link(i)',i)
 page.evaluate('reorderTest.select(2)');page.locator('.recipe-viewer-steps .cooking-item').nth(1).tap();button('Scale Recipe').tap();page.get_by_role('menuitemradio',name='½×',exact=True).tap()
 # Reproduce Android-style implicit-capture loss/cancellation ordering while a touch remains down.
 strip().evaluate('(e)=>e.scrollLeft=0');b=tab(1).bounding_box();x=b['x']+25;y=b['y']+20
 before=state();original_saved=saved();page.evaluate("window.detachedTabs=0;window.tabMutation=new MutationObserver(rows=>{for(const row of rows)detachedTabs+=row.removedNodes.length});tabMutation.observe(document.querySelector('.recipe-tab-strip'),{childList:true})");touch('touchStart',x,y);page.wait_for_timeout(620)
 assert page.locator('.recipe-tab-drag-preview').count()==1
 tab(1).evaluate("e=>e.dispatchEvent(new PointerEvent('lostpointercapture',{bubbles:true,pointerType:'touch',pointerId:touchAudit.pointer}))")
 assert page.locator('.recipe-tab-drag-preview').count()==1,'Bubbling implicit-capture loss must not abort an owned touch drag'
 tab(1).evaluate("e=>e.dispatchEvent(new PointerEvent('pointercancel',{bubbles:true,pointerType:'touch',pointerId:touchAudit.pointer}))")
 assert page.locator('.recipe-tab-drag-preview').count()==1,'Touch stream must survive pointer-stream cancellation'
 s=strip().bounding_box()
 for n in range(1,9):touch('touchMove',x+(s['x']+s['width']-3-x)*n/8,y);page.wait_for_timeout(20)
 page.wait_for_timeout(2200);assert page.evaluate('detachedTabs')==0,'Held touch target must remain attached during sorting';page.evaluate('tabMutation.disconnect()');touch('touchEnd');page.wait_for_timeout(70)
 assert state()['order'][-1]=='1';assert state()['active']==before['active'] and state()['context']==before['context'];assert saved()==original_saved
 assert page.locator('.recipe-tab-anchor .recipe-tab-close').count()==0
 # Short swipes also work from tab borders, gaps, and X buttons without activating/closing.
 for region in ['padding','gap','close']:
  strip().evaluate('(e)=>e.scrollLeft=0');old=state();old_saved=saved();first=strip().locator('.recipe-tab').first.bounding_box();y=first['y']+20
  if region=='padding':x=first['x']+1
  elif region=='gap':x=first['x']+first['width']+2
  else:
   close=strip().locator('.recipe-tab-close').first.bounding_box();x=close['x']+close['width']/2
  # Move right from the left edge first; then swipe left over the strip.
  if x<75:x=max(x,first['x']+1);dx=-(min(90,x-2))
  else:dx=-75
  swipe(x,y,dx)
  assert strip().evaluate('(e)=>e.scrollLeft')>10,(region,state())
  assert state()['order']==old['order'] and state()['active']==old['active'] and saved()==old_saved
 assert page.evaluate('touchAudit.moves.length>0&&touchAudit.moves.every(Boolean)'), 'Owned tab touch moves must be canceled before browser defaults'
 # Exactly one activation/close per touch tap, followed by a working swipe after reordering.
 tab(3).scroll_into_view_if_needed();count=page.evaluate('touchAudit.clicks');tab(3).tap();assert state()['active']=='3' and page.evaluate('touchAudit.clicks')==count+1
 count=page.evaluate('touchAudit.clicks');button('Close Cilantro Sauce tab').tap();assert state()['active']=='1' and '3' not in state()['order'] and page.evaluate('touchAudit.clicks')==count+1
 # Cancellation removes ghosts; a subsequent ordinary tap still activates.
 tab(2).scroll_into_view_if_needed();b=tab(2).bounding_box();touch('touchStart',b['x']+20,b['y']+20);page.wait_for_timeout(620);old=state()['order'];touch('touchMove',40,b['y']+20);page.wait_for_timeout(90);touch('touchCancel');assert state()['order']==old;assert not page.locator('.recipe-tab-drag-preview').count();tab(2).tap();assert state()['active']=='2'
 # The divider paints only 10px, but the transparent hit region is a full 44px without pane overlap.
 divider=page.locator('.recipe-divider');styles=divider.evaluate("e=>({hit:e.getBoundingClientRect().height,visual:parseFloat(getComputedStyle(e,'::before').height),top:parseFloat(getComputedStyle(e,'::before').top),bg:getComputedStyle(e).backgroundColor})")
 assert styles=={'hit':44,'visual':10,'top':17,'bg':'rgba(0, 0, 0, 0)'},styles
 before=state();old_saved=saved();b=divider.bounding_box();x=b['x']+b['width']/2;y=b['y']+3;touch('touchStart',x,y);assert page.evaluate('touchTest.flags().divider')
 for n in range(1,9):touch('touchMove',x,y+60*n/8);page.wait_for_timeout(20)
 touch('touchEnd');assert not page.evaluate('touchTest.flags().divider');down=state()['ratio'];assert down>before['ratio']+.05
 assert state()['sessions']==before['sessions'] and state()['scales']==before['scales'];assert saved()['mealRotationDataV1']==old_saved['mealRotationDataV1']
 # The lower invisible edge works too, including cancellation and future dragging.
 b=divider.bounding_box();y=b['y']+b['height']-3;touch('touchStart',x,y);touch('touchMove',x,y-45);touch('touchCancel');assert not page.evaluate('touchTest.flags().divider');assert state()['ratio']<down
 ratio=state()['ratio'];page.evaluate('reorderTest.select(1);reorderTest.select(2)');assert abs(state()['ratio']-ratio)<.001
 # Native vertical pane scrolling remains independent and cannot complete cooking items.
 progress=state()['sessions'];scales=state()['scales']
 for name,other in [('.recipe-ingredients-pane','.recipe-instructions-pane'),('.recipe-instructions-pane','.recipe-ingredients-pane')]:
  pane=page.locator(name);o=page.locator(other);pane.evaluate('(e)=>e.scrollTop=0');old_other=o.evaluate('(e)=>e.scrollTop');b=pane.bounding_box();swipe(b['x']+40,b['y']+b['height']-20,0,-55)
  assert pane.evaluate('(e)=>e.scrollTop')>5 and abs(o.evaluate('(e)=>e.scrollTop')-old_other)<1
 assert state()['sessions']==progress and state()['scales']==scales
 # Keyboard/mouse fallback still resizes; switching tabs keeps each divider position.
 divider.focus();old=state()['ratio'];divider.press('ArrowDown');assert state()['ratio']>old
 b=divider.bounding_box();page.mouse.move(b['x']+40,b['y']+22);page.mouse.down();page.mouse.move(b['x']+40,b['y']+2,steps=6);page.mouse.up();assert not page.evaluate('touchTest.flags().divider')
 if filename=='index.html':page.screenshot(path=f'/workspace/issue-11-work/divider-{width}.png')
 button('Full View').tap();assert divider.is_hidden();tab(4).tap();assert state()['active']=='4' and state()['mode']=='split';assert divider.is_visible()
 assert state()['anchor']=='1' and page.locator('.recipe-tab-anchor .recipe-tab-close').count()==0
 if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='production-sentinel'
 assert not errors,errors
 print(f'PASS {filename} {width}px: real touch ownership, pointer cancellation/capture-loss variant, strip/border/gap/X swipes, single tap/close, reorder+edge scroll, cancel/retry, 10px divider/44px target touch+mouse+keyboard, independent pane scrolling, Full/Split, occurrence/progress/scale/data preservation; no JS errors',flush=True)
 ctx.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:run(b,filename,width)
  b.close()
