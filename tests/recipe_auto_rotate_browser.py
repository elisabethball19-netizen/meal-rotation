"""Optional Screen Orientation leases; mobile viewport changes and API restrictions."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from recipe_tab_reorder_browser import MEALS,HOOK
ROOT=Path(__file__).resolve().parents[1]
MOCK='''window.rotateMock={calls:[],unlocks:0,fullscreen:0,sensors:0,mode:'resolve',pending:[],locked:null,resolve(){const next=this.pending.shift();if(next){this.locked=next.type;next.resolve()}},reject(){this.pending.shift()?.reject(new DOMException('Denied','NotAllowedError'))}};
const api=new EventTarget();api.type='portrait-primary';api.angle=0;api.lock=function(type){rotateMock.calls.push(type);if(rotateMock.mode==='throw')throw Error('Unavailable');if(rotateMock.mode==='reject')return Promise.reject(new DOMException('Restricted','NotAllowedError'));if(rotateMock.mode==='deferred')return new Promise((resolve,reject)=>rotateMock.pending.push({resolve,reject,type}));rotateMock.locked=type;return Promise.resolve()};api.unlock=function(){rotateMock.unlocks++;rotateMock.locked=null;if(rotateMock.mode==='unlock-throw')throw Error('Cannot unlock')};
Object.defineProperty(screen,'orientation',{configurable:true,value:api});
Element.prototype.requestFullscreen=function(){rotateMock.fullscreen++;return Promise.reject(new Error('Unexpected fullscreen'))};
window.addEventListener('unhandledrejection',e=>{window.unhandled=(window.unhandled||[]).concat(String(e.reason))});
'''
EXTRA='''window.autoRotateTest={
 flush:async()=>{await recipeOrientationQueue},enabled:()=>recipeViewPrefs.autoRotateRecipeView===true,
 set:value=>{recipeViewPrefs.autoRotateRecipeView=value;saveRecipeViewPrefs();syncRecipeAutoRotation()},close:()=>finishRecipeViewerClose(),
 status:()=>({open:!!recipeViewer,owned:!!recipeOrientationOwned,pending:!!recipeOrientationPending,axis:recipeViewer?.cover.classList.contains('recipe-landscape')}),
 visibility:value=>{Object.defineProperty(document,'visibilityState',{configurable:true,value});document.dispatchEvent(new Event('visibilitychange'))},
 saved:()=>autoBackup.capture(),restore:storage=>{autoBackup.restore(autoBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def setup(b,name,mode='resolve',enabled=False,full=False,landscape=False,native=False):
 c=b.new_context(viewport={'width':780 if landscape else 360,'height':360 if landscape else 780},is_mobile=True,has_touch=True,accept_downloads=True,user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36')
 p=c.new_page();p.set_default_timeout(8000);errors=[];p.on('pageerror',lambda x:errors.append(str(x)));prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else '';storage='testStorage' if prefix else 'localStorage'
 src=(ROOT/name).read_text().replace('function validateBackupCore(d){','window.autoBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+(HOOK+EXTRA).replace('localStorage',storage)+'})();')
 prefs=dict(mode='full' if full else 'split',ratio=.4,landscapeRatio=.55,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False)
 if enabled:prefs['autoRotateRecipeView']=True
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Sides'],active='Main',meals=MEALS)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main'],'Friday':['Main']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(prefs),prefix+'mealRotationTutorialStageV1':'done'}
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
 p.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 if not native:p.add_init_script(MOCK+'rotateMock.mode='+json.dumps(mode)+';'+("screen.orientation.lock=undefined;screen.orientation.unlock=undefined;" if mode=='missing' else ''))
 else:p.add_init_script("window.nativeFullscreenRequests=0;Element.prototype.requestFullscreen=function(){nativeFullscreenRequests++;return Promise.reject(new Error('No fullscreen'))};window.addEventListener('unhandledrejection',e=>window.unhandled=(window.unhandled||[]).concat(String(e.reason)))")
 p.route('http://rotation.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(name) else r.fulfill(status=200,body=''));p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 p.goto('http://rotation.test/'+name);return c,p,errors,prefix

def flush(p):p.evaluate('autoRotateTest.flush()')
def mock(p):return p.evaluate('({calls:rotateMock.calls,unlocks:rotateMock.unlocks,fullscreen:rotateMock.fullscreen,locked:rotateMock.locked})')
def close(p):p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_selector('#recipeViewer',state='detached');flush(p)
def settings(p,value,save=True):
 p.get_by_role('button',name='Settings and backups',exact=True).tap();p.locator('details[data-settings-group=display]').evaluate('(e)=>e.open=true');cb=p.get_by_role('checkbox',name='Auto-rotate recipe view',exact=True);assert cb.count()==1;cb.set_checked(value);assert cb.locator('..').bounding_box()['height']>=44
 p.get_by_role('button',name='Save settings' if save else 'Cancel settings',exact=True).tap()
def check(c,p,errors,prefix):
 assert not errors,errors;assert not p.evaluate('window.unhandled||[]');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if p.evaluate('typeof rotateMock!=="undefined"'):assert mock(p)['fullscreen']==0 and all(x=='any' for x in mock(p)['calls'])
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()

def defaults_settings(b,name):
 c,p,e,pr=setup(b,name);assert not p.evaluate('autoRotateTest.enabled()');settings(p,True,False);assert not p.evaluate('autoRotateTest.enabled()');assert mock(p)['calls']==[]
 p.evaluate('reorderTest.open()');flush(p);assert mock(p)['calls']==[];close(p);assert mock(p)['unlocks']==0
 settings(p,True);assert p.evaluate('autoRotateTest.enabled()') and mock(p)['calls']==[];p.reload();assert p.evaluate('autoRotateTest.enabled()');saved=p.evaluate('autoRotateTest.saved()');assert json.loads(saved['mealRotationRecipeViewPrefsV1'])['autoRotateRecipeView']
 settings(p,False);p.evaluate('autoRotateTest.restore',saved);p.reload();assert p.evaluate('autoRotateTest.enabled()');p.evaluate('reorderTest.open()');flush(p);assert mock(p)['calls']==['any'];close(p);assert mock(p)['locked'] is None;check(c,p,e,pr)
 print('PASS',name,'legacy default OFF, one existing-style checkbox, Save/Cancel, reload/backups, no requests outside viewer or while OFF',flush=True)

def transitions(b,name,full,landscape):
 c,p,e,pr=setup(b,name,enabled=True,full=full,landscape=landscape);size=dict(p.viewport_size);p.evaluate('reorderTest.open()');flush(p);assert p.viewport_size==size and mock(p)['calls']==['any'] and mock(p)['locked']=='any'
 p.locator('.recipe-viewer-steps .cooking-item').nth(1).tap();p.get_by_role('button',name='Scale Recipe',exact=True).tap();p.get_by_role('menuitemradio',name='2×',exact=True).tap();p.evaluate('reorderTest.link(2)');p.locator('.recipe-viewer-steps .cooking-item').nth(2).tap();p.evaluate('reorderTest.select(1)')
 before=p.evaluate('reorderTest.saved()');state=p.evaluate('reorderTest.state()');calls=len(mock(p)['calls'])
 for w,h in [(360,780),(780,360),(360,780),(780,360)]:
  p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(250);assert p.evaluate('reorderTest.saved()')==before
  current=p.evaluate('reorderTest.state()');assert current['sessions']==state['sessions'] and current['scales']==state['scales'] and current['active']==state['active'] and current['order']==state['order']
  if not full:assert p.locator('.recipe-divider').get_attribute('aria-orientation')==('vertical' if w>h else 'horizontal')
  assert len(mock(p)['calls'])==calls
 # Opening a linked tab is still the same viewer lease; Edit Recipe releases it.
 p.evaluate('reorderTest.select(2)');assert len(mock(p)['calls'])==calls;p.get_by_role('button',name='Edit Recipe',exact=True).tap();flush(p);assert not p.locator('#recipeViewer').count() and mock(p)['locked'] is None
 p.locator('#cancel').tap();p.wait_for_selector('#recipeViewer');flush(p);assert mock(p)['locked']=='any' and len(mock(p)['calls'])==calls+1
 close(p);assert mock(p)['locked'] is None and not p.evaluate('autoRotateTest.status().owned');outside=len(mock(p)['calls']);p.set_viewport_size({'width':360,'height':780});p.wait_for_timeout(100);assert len(mock(p)['calls'])==outside
 # Close in portrait as well, including history navigation.
 p.evaluate('reorderTest.open()');flush(p);p.go_back();p.wait_for_selector('#recipeViewer',state='detached');flush(p);assert mock(p)['locked'] is None
 check(c,p,e,pr);print('PASS',name,'full',full,'starts landscape',landscape,'open retains orientation, portrait↔landscape, linked tabs, progress/scales, edit return, close/back in both orientations, no fullscreen',flush=True)

def restrictions(b,name,mode):
 c,p,e,pr=setup(b,name,mode,True);p.evaluate('reorderTest.open()');flush(p);assert p.locator('#recipeViewer').is_visible() and not p.evaluate('autoRotateTest.status().owned')
 assert p.viewport_size=={'width':360,'height':780}
 if mode!='missing':assert mock(p)['calls']==['any']
 # Simulate physical movement while Android/browser keeps the viewport locked.
 p.evaluate("screen.orientation.type='landscape-primary';screen.orientation.angle=90;screen.orientation.dispatchEvent(new Event('change'))");p.wait_for_timeout(50);assert not p.evaluate('autoRotateTest.status().axis')
 p.locator('.recipe-viewer-steps .cooking-item').first.tap();assert p.locator('.recipe-viewer-steps .cooking-complete').count()>0
 close(p);assert not p.get_by_role('alertdialog').count();check(c,p,e,pr);print('PASS',name,mode,'unsupported/denied API and simulated system rotation lock: viewport unchanged, recipe remains interactive, no alerts/errors/fullscreen',flush=True)

def lifecycle_races(b,name):
 c,p,e,pr=setup(b,name,'deferred',True);p.evaluate('reorderTest.open()');p.wait_for_timeout(30);assert mock(p)['calls']==['any'];p.evaluate('autoRotateTest.close()');assert mock(p)['unlocks']>=1
 p.evaluate('reorderTest.open()');p.wait_for_timeout(20);assert len(mock(p)['calls'])==1
 p.evaluate("rotateMock.mode='resolve';rotateMock.resolve()");flush(p);assert mock(p)['calls']==['any','any'] and mock(p)['locked']=='any' and p.evaluate('autoRotateTest.status().owned')
 p.evaluate('autoRotateTest.visibility("hidden")');flush(p);assert mock(p)['locked'] is None
 p.evaluate('autoRotateTest.visibility("visible")');flush(p);assert mock(p)['locked']=='any'
 p.evaluate("window.dispatchEvent(new Event('pagehide'))");flush(p);assert mock(p)['locked'] is None
 p.evaluate("window.dispatchEvent(new Event('pageshow'))");flush(p);assert mock(p)['locked']=='any'
 p.evaluate('autoRotateTest.set(false)');flush(p);assert mock(p)['locked'] is None;p.evaluate('autoRotateTest.set(true)');flush(p);assert mock(p)['locked']=='any'
 close(p);assert mock(p)['locked'] is None
 # User-initiated fullscreen may permit a retry, but the app never requests it.
 p.evaluate("rotateMock.mode='reject';reorderTest.open()");flush(p);assert not p.evaluate('autoRotateTest.status().owned');p.evaluate("rotateMock.mode='resolve';document.dispatchEvent(new Event('fullscreenchange'))");flush(p);assert mock(p)['locked']=='any';close(p)
 # A throwing unlock must never strand the viewer or block its close.
 p.evaluate("rotateMock.mode='resolve';reorderTest.open()");flush(p);p.evaluate("rotateMock.mode='unlock-throw'");close(p);check(c,p,e,pr)
 print('PASS',name,'pending close/reopen ownership, hidden/visible/page lifecycle cleanup, setting changes, graceful fullscreen retry and throwing unlock',flush=True)

def native_fallback(b,name):
 c,p,e,pr=setup(b,name,enabled=True,native=True);p.evaluate('reorderTest.open()');flush(p);assert p.locator('#recipeViewer').is_visible();assert p.evaluate('nativeFullscreenRequests')==0;close(p);check(c,p,e,pr);print('PASS',name,'actual Chromium orientation API without fullscreen: graceful supported/rejected outcome, no errors',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   defaults_settings(b,name)
   for full in [False,True]:
    for landscape in [False,True]:transitions(b,name,full,landscape)
   for mode in ['missing','reject','throw']:restrictions(b,name,mode)
   lifecycle_races(b,name);native_fallback(b,name)
  b.close()
