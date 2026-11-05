"""Obsolete auto-rotate preferences are ignored; responsive layout remains independent."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.orientationRemovalTest={prefs:()=>recipeViewPrefs,legacy:()=>{const storage=slotBackup.capture(),prefs=JSON.parse(storage.mealRotationRecipeViewPrefsV1);prefs.autoRotateRecipeView=true;prefs.timerAlarmVolume=.37;localStorage.setItem('mealRotationRecipeViewPrefsV1',JSON.stringify(prefs));}};'''
SPY='''window.orientationAudit={lock:0,unlock:0,fullscreen:0};const api=new EventTarget();api.lock=()=>{orientationAudit.lock++;return Promise.reject(Error('Unexpected orientation lock'))};api.unlock=()=>{orientationAudit.unlock++};Object.defineProperty(screen,'orientation',{configurable:true,value:api});Element.prototype.requestFullscreen=()=>{orientationAudit.fullscreen++;return Promise.reject(Error('Unexpected fullscreen'))};'''
def run(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('orientationRemovalTest.legacy()');p.add_init_script(SPY);p.reload()
 assert p.evaluate('orientationRemovalTest.prefs().timerAlarmVolume')==.37
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 backup=p.evaluate('timerTest.backup()');assert json.loads(backup['mealRotationRecipeViewPrefsV1'])['autoRotateRecipeView'] is True
 p.evaluate('timerTest.viewer()');assert p.locator('#recipeViewer').is_visible()
 p.get_by_role('button',name='Recipe settings',exact=True).tap();panel=p.locator('#recipeViewerSettings');assert not panel.get_by_text('Auto-rotate recipe view',exact=True).count()
 assert panel.get_by_role('slider',name='Timer alarm volume',exact=True).input_value()=='37'
 p.get_by_role('button',name='Close settings',exact=True).tap()
 for width,height in [(740,360),(360,780),(740,360),(360,780)]:
  p.set_viewport_size({'width':width,'height':height});p.wait_for_timeout(80)
  assert p.locator('.recipe-divider').get_attribute('aria-orientation')==('vertical' if width>height else 'horizontal')
 p.evaluate("document.dispatchEvent(new Event('fullscreenchange'));document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new Event('pagehide'));window.dispatchEvent(new Event('pageshow'))")
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(80)
 p.locator('#settings').tap();assert not p.locator('#autoRotateRecipeView').count() and not p.get_by_text('Auto-rotate recipe view',exact=True).count()
 p.get_by_role('button',name='Save settings',exact=True).tap()
 # The old backup value is safe to restore, but never triggers orientation API requests.
 p.evaluate('storage=>timerTest.restore(storage)',backup);p.reload();p.evaluate('timerTest.viewer()');assert p.evaluate('orientationRemovalTest.prefs().timerAlarmVolume')==.37
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(80)
 assert p.evaluate('orientationAudit')=={'lock':0,'unlock':0,'fullscreen':0}
 after=state(p)
 for key in ['meals','sessions','scales','prefs']:assert after[key]==before[key],key
 assert compose(p)==schedule and f.sources(p)==groceries
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,'obsolete true preference and backup ignored, zero lock/unlock/fullscreen calls; portrait/landscape/close/lifecycle and other prefs/data intact',flush=True);c.close()
if __name__=='__main__':
 for name in ['index.html','meal-rotation-test.html']:
  source=(f.ROOT/name).read_text();assert 'syncRecipeAutoRotation' not in source and 'screen.orientation.lock' not in source and 'autoRotateRecipeView' not in source
 for name in ['manifest.webmanifest','manifest-test.webmanifest']:
  path=f.ROOT/name
  if path.exists():assert json.loads(path.read_text())['display']=='standalone'
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
