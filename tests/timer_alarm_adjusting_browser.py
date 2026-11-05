"""Bounded alarm ownership, global volume and temporary Needs Adjusting expansion."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.alarmTest={
 sound:()=>cookingTimerSound?{kind:cookingTimerSound.kind,timerId:cookingTimerSound.timerId,loop:cookingTimerSound.source.loop}:null,
 flag:()=>{const m=meals.find(m=>m.id===1);m.needsTweaking=true;m.needsTweakingNote='Try more seasoning.\\n'+('Keep this full saved note intact. '.repeat(50));persist()},
 rerender:renderRecipeViewer,volume:()=>recipeViewPrefs.timerAlarmVolume,
 prefs:()=>localStorage.getItem(RECIPE_VIEW_PREFS_KEY),
 waveform:()=>{const a=cookingTimerSound.source.buffer.getChannelData(0),n=a.length;return {length:n,peak:Math.max(...a),last:a.slice(n*.6).some(x=>x!==0),pulses:[.05,.37,.69].map(p=>a.slice(n*p/2,n*(p+.03)/2).some(x=>x!==0))}},
 blocked:()=>{cookingTimerAudio.state='suspended';cookingTimerAudio.resume=()=>Promise.reject(Error('blocked'))},
 unblock:()=>{cookingTimerAudio.state='running';cookingTimerAudio.resume=()=>Promise.resolve()},
 setVolume:setCookingTimerAlarmVolume
};'''
def sound(p):return p.evaluate('alarmTest.sound()')
def settings(p):
 panel=p.locator('#recipeViewerSettings')
 if not panel.is_visible():p.get_by_role('button',name='Recipe settings',exact=True).tap()
 return panel
def close_settings(p):p.get_by_role('button',name='Close settings',exact=True).tap()
def volume(p,value):
 slider=settings(p).get_by_role('slider',name='Timer alarm volume',exact=True)
 slider.evaluate('(e,value)=>{e.value=String(value);e.dispatchEvent(new Event("input",{bubbles:true}))}',value)
 assert slider.get_attribute('aria-valuetext')==str(value)+'%'
 assert p.locator('.recipe-timer-volume-output').inner_text()==str(value)+'%'
def stable(p,before,schedule,groceries):
 after=state(p)
 for key in ['meals','sessions','scales']:assert before[key]==after[key],key
 assert compose(p)==schedule and f.sources(p)==groceries
 assert {k:v for k,v in before['prefs'].items() if k!='timerAlarmVolume'}=={k:v for k,v in after['prefs'].items() if k!='timerAlarmVolume'}
def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.clock.install();p.evaluate('timerTest.setup()');p.evaluate('promotionTest.check()');p.evaluate('alarmTest.flag()');p.evaluate('timerTest.viewer()');t.mock_alerts(p)
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 panel=settings(p);slider=panel.get_by_role('slider',name='Timer alarm volume',exact=True)
 assert slider.count()==1 and slider.input_value()=='80' and p.evaluate('alarmTest.volume()')==.8
 assert panel.get_by_role('checkbox',name='Sync Ingredients',exact=True).count()==1
 panel.get_by_role('button',name='Test alarm sound',exact=True).tap();assert sound(p)['kind']=='test' and sound(p)['loop']
 assert p.evaluate('alertCalls.levels.at(-1)')==.8
 shape=p.evaluate('alarmTest.waveform()');assert shape['peak']>.25 and shape['peak']<=.4 and not shape['last'] and all(shape['pulses']),shape
 p.clock.fast_forward(1000);assert sound(p)['kind']=='test'
 volume(p,25);assert p.evaluate('alertCalls.levels.at(-1)')==.25
 panel.get_by_role('button',name='Stop test sound',exact=True).tap();assert sound(p) is None and p.evaluate('alertCalls.stops')==1
 panel.get_by_role('button',name='Test alarm sound',exact=True).tap();p.clock.fast_forward(3100);assert sound(p) is None and p.evaluate('alertCalls.stops')==2
 panel.get_by_role('button',name='Test alarm sound',exact=True).tap();close_settings(p);assert sound(p) is None
 # Timer completion takes over a preview; its expired preview timeout cannot stop the alarm.
 t.icon(p,2).tap();panel=settings(p);panel.get_by_role('button',name='Test alarm sound',exact=True).tap();assert sound(p)['kind']=='test'
 p.clock.fast_forward(2100);assert sound(p)['kind']=='alarm' and p.evaluate('alertCalls.tones-alertCalls.stops')==1
 p.clock.fast_forward(4000);assert sound(p)['kind']=='alarm' and p.evaluate('alertCalls.tones-alertCalls.stops')==1
 p.get_by_role('button',name='Acknowledge completed timer',exact=True).tap();close_settings(p);assert sound(p) is None
 # Volume is shared by other recipes and survives reload.
 p.evaluate('timerTest.close()');p.evaluate('timerTest.viewer(20)');assert settings(p).get_by_role('slider').input_value()=='25'
 volume(p,60);close_settings(p);p.evaluate('timerTest.close()');p.evaluate('timerTest.viewer()');assert settings(p).get_by_role('slider').input_value()=='60';close_settings(p)
 p.reload();p.evaluate('timerTest.viewer()');assert settings(p).get_by_role('slider').input_value()=='60';close_settings(p);t.mock_alerts(p,'granted')
 # One bounded source is never restarted by synchronization or later gestures.
 t.icon(p,2).tap();p.clock.fast_forward(2100);p.wait_for_timeout(30);assert t.timer(p)['status']=='complete' and sound(p)['kind']=='alarm'
 assert p.evaluate('alertCalls.tones')==1 and p.evaluate('alertCalls.levels.at(-1)')==.6
 p.evaluate('alarmTest.setVolume(0)');assert p.evaluate('alertCalls.levels.at(-1)')==0
 p.evaluate('alarmTest.setVolume(100)');assert p.evaluate('alertCalls.levels.at(-1)')==1
 p.clock.fast_forward(20000)
 for _ in range(5):p.evaluate('timerTest.reconcile()')
 assert p.evaluate('alertCalls.tones')==1 and sound(p) is None and len(p.evaluate('alertCalls.notifications'))==1
 p.evaluate('alarmTest.blocked()');p.evaluate("window.dispatchEvent(new Event('focus'))");p.evaluate('alarmTest.unblock()');p.evaluate("window.dispatchEvent(new Event('focus'))");assert sound(p) is None and p.evaluate('alertCalls.tones')==1
 p.get_by_role('button',name='Acknowledge completed timer',exact=True).tap();assert sound(p) is None and t.timer(p) is None
 p.clock.fast_forward(10000);p.evaluate('timerTest.reconcile()');assert p.evaluate('alertCalls.tones')==1
 # Existing warning is never removed by collapsing it; expansion persists across rerenders.
 p.evaluate('timerTest.close()');p.evaluate('timerTest.viewer()');section=p.locator('.recipe-tweaking-status');note=section.locator('.recipe-tweaking-note');saved=next(m for m in state(p)['meals'] if m['id']==1)['needsTweakingNote']
 assert note.is_visible() and note.inner_text()==saved
 expanded=section.bounding_box()['height'];section.get_by_role('button',name='Collapse Needs Adjusting note',exact=True).tap()
 assert section.bounding_box()['height']<expanded and not note.is_visible()
 assert not section.get_by_role('button',name='Edit note',exact=True).count() and not section.get_by_role('button',name='Remove Needs Adjusting',exact=True).count()
 assert section.locator('.recipe-tweaking-heading svg').count()==1 and section.get_by_role('button',name='Expand Needs Adjusting note',exact=True).get_attribute('aria-expanded')=='false'
 p.evaluate('alarmTest.rerender()');assert not section.locator('.recipe-tweaking-note').is_visible()
 p.locator('#recipeViewer').get_by_role('button',name='Current side',exact=True).tap();assert not p.locator('.recipe-tweaking-status').count()
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Pernil',exact=True).tap();assert not section.locator('.recipe-tweaking-note').is_visible()
 section.get_by_role('button',name='Expand Needs Adjusting note',exact=True).tap();assert section.locator('.recipe-tweaking-note').inner_text()==saved and section.get_by_role('button',name='Edit note',exact=True).is_visible()
 section.get_by_role('button',name='Collapse Needs Adjusting note',exact=True).tap();p.evaluate('timerTest.close()');p.evaluate('timerTest.viewer()');assert section.locator('.recipe-tweaking-note').is_visible()
 # Existing backups contain the global preference and original note/status.
 backup=p.evaluate('timerTest.backup()');assert json.loads(backup['mealRotationRecipeViewPrefsV1'])['timerAlarmVolume']==1
 assert next(m for m in state(p)['meals'] if m['id']==1)['needsTweakingNote']==saved
 stable(p,before,schedule,groceries);assert not errors,errors
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'single bounded alarm/acknowledgment, waveform/live volume, bounded stoppable preview, global/reloaded prefs, blocked audio fallback, temporary note collapse, unchanged recipes/progress/schedules/groceries',flush=True);c.close()
def fresh_context(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('timerTest.setup()');p.evaluate('alarmTest.flag()');p.evaluate('timerTest.viewer()');volume(p,37);close_settings(p)
 backup=p.evaluate('timerTest.backup()');volume(p,12);close_settings(p)
 p.evaluate('storage=>timerTest.restore(storage)',backup);p.reload();p.evaluate('timerTest.viewer()');assert settings(p).get_by_role('slider').input_value()=='37';close_settings(p)
 p.locator('.recipe-tweaking-status').get_by_role('button',name='Collapse Needs Adjusting note',exact=True).tap();p.evaluate('timerTest.close()')
 saved=c.storage_state();assert not errors,errors;c.close()
 source=(f.ROOT/name).read_text().replace('function validateBackupCore(d){','window.slotBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+(f.HOOK+f.EXTRA).replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 c=b.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True,storage_state=saved);p=c.new_page();fresh_errors=[];p.on('pageerror',lambda e:fresh_errors.append(str(e)))
 p.route('http://promotion.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(name) else r.fulfill(status=200,body=''));p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 p.goto('http://promotion.test/'+name);p.evaluate('timerTest.viewer()');assert settings(p).get_by_role('slider').input_value()=='37';close_settings(p)
 assert p.locator('.recipe-tweaking-status .recipe-tweaking-note').is_visible()
 assert not fresh_errors,fresh_errors
 print('PASS',name,'global volume/flag/note through backup restore and fresh browser storage context; note opens expanded',flush=True);c.close()

def layout(b,name,width,mode,landscape):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('timerTest.setup()');p.evaluate('alarmTest.flag()');p.evaluate('timerTest.viewer()');p.evaluate('mode=>timerTest.mode(mode)',mode)
 if landscape:p.set_viewport_size({'width':740,'height':360})
 section=p.locator('.recipe-tweaking-status');section.get_by_role('button',name='Collapse Needs Adjusting note',exact=True).tap();panel=settings(p)
 assert panel.get_by_role('slider',name='Timer alarm volume',exact=True).count()==1
 preview=panel.get_by_role('button',name='Test alarm sound',exact=True);preview.scroll_into_view_if_needed();assert preview.is_visible()
 close_settings(p);section.get_by_role('button',name='Expand Needs Adjusting note',exact=True).tap()
 assert section.locator('.recipe-tweaking-note').is_visible()
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if mode=='split':assert all(h>25 for h in p.locator('.recipe-pane').evaluate_all('(panes)=>panes.map(p=>p.clientHeight)'))
 if name.startswith('meal-') and width==360:
  p.screenshot(path='/tmp/alarm-note-'+mode+('-landscape' if landscape else '-portrait')+'.png')
 assert not errors,errors
 print('PASS',name,width,mode,landscape,'compact note states/settings, reachable preview, no overflow or JS errors',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   fresh_context(b,name)
   for width in [320,360]:
    run(b,name,width)
    for mode in ['full','split']:
     for landscape in [False,True]:layout(b,name,width,mode,landscape)
  b.close()
