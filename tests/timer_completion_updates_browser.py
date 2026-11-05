"""One timer, bounded visible-only alarms, automatic completion and compact controls."""
import copy
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.completionTest={
 sound:()=>cookingTimerSound?{kind:cookingTimerSound.kind,stopAt:cookingTimerSound.stopAt}:null,
 hidden:value=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>value});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>value?'hidden':'visible'});document.dispatchEvent(new Event('visibilitychange'))},
 suspend:()=>{if(cookingTimerAudio){cookingTimerAudio.state='suspended';cookingTimerAudio.dispatchEvent(new Event('statechange'))}},
 resume:()=>{if(cookingTimerAudio){cookingTimerAudio.state='running';cookingTimerAudio.dispatchEvent(new Event('statechange'))}},
 expireForReload:()=>{cookingTimer.deadline=Date.now()-60000;saveCookingTimer()},
 volume:setCookingTimerAlarmVolume,deck:()=>({active:recipeViewer?.activeTab.key,scroll:recipeViewer?.cover.scrollTop,panes:[...document.querySelectorAll('.recipe-pane')].map(e=>e.scrollTop)}),
 weekly:()=>{showTop=true;allMealsActive=true;groceryTabActive=false;renderList()}
};'''
def mock(p,permission='granted'):
 t.mock_alerts(p,permission)
 p.evaluate('''()=>{const Original=AudioContext;window.AudioContext=class extends Original{constructor(){super();this.events=new EventTarget()}addEventListener(...a){this.events.addEventListener(...a)}removeEventListener(...a){this.events.removeEventListener(...a)}dispatchEvent(e){return this.events.dispatchEvent(e)}createBufferSource(){const source=super.createBufferSource(),start=source.start;source.start=(...args)=>{(alertCalls.durations??=[]).push(args[2]);start.apply(source,args)};return source}}}''')
def popup(p):return p.get_by_role('alertdialog',name="Time's Up!",exact=True)
def ack(p):popup(p).get_by_role('button',name='Acknowledge completed timer',exact=True).tap()
def start(p,n=2):t.icon(p,n).tap()
def sound(p):return p.evaluate('completionTest.sound()')
def setup(b,name,w=320):
 c,p,errors,prefix=f.setup(b,name,w,'multiple');p.clock.install();p.evaluate('timerTest.setup()');p.evaluate('promotionTest.check()');mock(p);p.evaluate('timerTest.viewer()');return c,p,errors,prefix
def compact(p,root):
 row=root.locator('.recipe-timer-strip');buttons=row.locator('button');assert buttons.count()==3
 assert buttons.nth(1).get_attribute('aria-label')=='Hide timer controls' and buttons.nth(2).get_attribute('aria-label')=='Delete timer'
 assert 'remaining' not in row.inner_text().lower() and 'Timer' not in row.inner_text()
 boxes=[row.locator('.recipe-timer-readout').bounding_box()]+[buttons.nth(i).bounding_box() for i in range(3)];assert max(x['y']+x['height']/2 for x in boxes)-min(x['y']+x['height']/2 for x in boxes)<3
 assert all(boxes[i]['x']+boxes[i]['width']<=boxes[i+1]['x']+1 for i in range(3));assert row.bounding_box()['height']<=48
 assert row.locator('.recipe-timer-readout').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=24

def foreground(b,name,w):
 c,p,errors,prefix=setup(b,name,w);before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 start(p,0);old=t.timer(p);compact(p,p.locator('#recipeViewer'));p.get_by_role('button',name='Pause timer',exact=True).tap();p.get_by_role('button',name='Hide timer controls',exact=True).tap();assert t.timer(p)['status']=='paused' and not t.strip(p).count();p.get_by_role('button',name='Show timer',exact=True).tap();p.get_by_role('button',name='Resume timer',exact=True).tap();p.clock.fast_forward(1000);assert t.timer(p)['deadline']>=old['deadline']
 start(p);d=p.get_by_role('dialog',name='Replace current timer?',exact=True);assert d.locator('button').count()==2 and d.inner_text()=='Replace current timer?';assert not d.locator('.smallbtn').count();boxes=d.locator('button').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().y)');assert abs(boxes[0]-boxes[1])<2
 if w==320:p.screenshot(path='/tmp/timer-replace-'+name+'.png')
 d.get_by_role('button',name='Keep current timer',exact=True).tap();assert t.timer(p)['id']==old['id']
 start(p);d=p.get_by_role('dialog',name='Replace current timer?',exact=True);d.get_by_role('button',name='Replace timer',exact=True).tap();assert t.timer(p)['id']!=old['id'];assert p.locator('.recipe-viewer-steps .cooking-item').nth(3).get_attribute('aria-pressed')=='false'
 p.get_by_role('button',name='Current side',exact=True).tap();deck=p.evaluate('completionTest.deck()');p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and 'Pernil' in popup(p).inner_text();assert p.evaluate('completionTest.deck()')==deck
 assert sound(p)['kind']=='alarm' and p.evaluate('alertCalls.tones')==1 and 5<p.evaluate('alertCalls.durations[0]')<=6
 p.clock.fast_forward(5100);assert sound(p) is not None;p.clock.fast_forward(1000);assert sound(p) is None and t.timer(p)['status']=='complete' and popup(p).is_visible();assert p.evaluate('alertCalls.stops')==1
 for _ in range(3):p.evaluate('timerTest.reconcile()');p.evaluate("window.dispatchEvent(new Event('focus'))")
 assert p.evaluate('alertCalls.tones')==1 and len(p.evaluate('alertCalls.notifications'))==1
 ack(p);assert t.timer(p) is None and not p.locator('.recipe-list-timer').count() and not popup(p).count();assert p.evaluate('completionTest.deck()')==deck
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Pernil',exact=True).tap();start(p);p.evaluate('timerTest.close()');p.evaluate('completionTest.weekly()');p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and sound(p)['kind']=='alarm';ack(p);assert sound(p) is None and t.timer(p) is None
 assert state(p)['meals']==before['meals'] and compose(p)==schedule and f.sources(p)==groceries
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'];assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,w,'compact controls/reopen, two-icon replacement, completion across tabs/pages without progress/scroll changes, one bounded alarm, immediate acknowledgment',flush=True);c.close()
def background(b,name):
 c,p,errors,_=setup(b,name,360);start(p);p.evaluate('completionTest.hidden(true)');p.clock.fast_forward(2200);assert t.timer(p)['status']=='complete' and sound(p) is None and not popup(p).count();assert len(p.evaluate('alertCalls.notifications'))==1
 p.evaluate('completionTest.hidden(false)');p.wait_for_timeout(30);assert popup(p).is_visible() and p.evaluate('alertCalls.tones')==0;ack(p)
 start(p);p.clock.fast_forward(2100);p.wait_for_timeout(30);assert sound(p);p.evaluate('completionTest.hidden(true)');assert sound(p) is None;p.clock.fast_forward(6000);p.evaluate('completionTest.hidden(false)');assert sound(p) is None and p.evaluate('alertCalls.tones')==1;ack(p)
 start(p);p.clock.fast_forward(2100);p.wait_for_timeout(30);assert sound(p);p.evaluate('completionTest.suspend()');assert sound(p) is None;p.clock.fast_forward(6000);p.evaluate('completionTest.resume()');p.evaluate('timerTest.reconcile()');assert sound(p) is None and p.evaluate('alertCalls.tones')==2;ack(p)
 start(p);p.clock.fast_forward(20000);p.wait_for_timeout(30);assert popup(p).is_visible() and sound(p) is None and p.evaluate('alertCalls.tones')==2;ack(p)
 start(p);p.evaluate('completionTest.suspend()');p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and sound(p) is None;p.evaluate('completionTest.resume()');p.evaluate('timerTest.reconcile()');assert p.evaluate('alertCalls.tones')==2;ack(p)
 start(p);p.evaluate('completionTest.expireForReload()');p.reload();p.wait_for_timeout(80);assert popup(p).is_visible() and t.timer(p)['status']=='complete';mock(p);p.evaluate('timerTest.reconcile()');assert p.evaluate('alertCalls.tones')==0;ack(p)
 assert not errors,errors;print('PASS',name,'hidden/locked-state simulation, notification once, stop on hide/suspension, no late/reload/replayed alarm, completed state remains accessible',flush=True);c.close()
def volume_preview(b,name):
 c,p,errors,_=setup(b,name,360);p.get_by_role('button',name='Recipe settings',exact=True).tap();slider=p.get_by_role('slider',name='Timer alarm volume',exact=True);slider.evaluate('(e)=>{e.value="37";e.dispatchEvent(new Event("input",{bubbles:true}))}');p.get_by_role('button',name='Test alarm sound',exact=True).tap();assert sound(p)['kind']=='test' and p.evaluate('alertCalls.levels.at(-1)')==.37 and p.evaluate('alertCalls.durations.at(-1)')==3
 p.get_by_role('button',name='Stop test sound',exact=True).tap();assert sound(p) is None;p.get_by_role('button',name='Test alarm sound',exact=True).tap();p.clock.fast_forward(3100);assert sound(p) is None
 p.get_by_role('button',name='Close settings',exact=True).tap();p.evaluate('timerTest.close()');p.evaluate('timerTest.viewer(20)');p.get_by_role('button',name='Recipe settings',exact=True).tap();assert p.get_by_role('slider').input_value()=='37';p.get_by_role('button',name='Close settings',exact=True).tap()
 backup=p.evaluate('timerTest.backup()');p.evaluate('completionTest.volume(10)');p.evaluate('b=>timerTest.restore(b)',backup);p.reload();assert state(p)['prefs']['timerAlarmVolume']==.37
 assert not errors,errors;print('PASS',name,'global volume, stoppable/bounded preview, shared recipes, backup/restore/reload',flush=True);c.close()
def list_surfaces_and_completion_focus(b,name):
 c,p,errors,_=setup(b,name,320);start(p,0);p.get_by_role('button',name='Pause timer',exact=True).tap();timer=t.timer(p);p.evaluate('timerTest.close()')
 for page in ['promotionTest.my()','promotionTest.groups()','completionTest.weekly()']:
  p.evaluate(page);indicator=p.locator('#list .recipe-list-timer').first;assert indicator.is_visible();indicator.tap();d=p.get_by_role('dialog',name='Cooking timer',exact=True);compact(p,d);d.get_by_role('button',name='Resume timer',exact=True).tap();p.clock.fast_forward(1000);assert t.timer(p)['deadline']>timer.get('deadline',0);d.get_by_role('button',name='Pause timer',exact=True).tap();d.get_by_role('button',name='Hide timer controls',exact=True).tap();assert not d.count() and t.timer(p)['status']=='paused'
 indicator=p.locator('#list .recipe-list-timer').first;indicator.tap();p.get_by_role('dialog',name='Cooking timer',exact=True).get_by_role('button',name='Delete timer',exact=True).tap();assert t.timer(p) is None and not p.locator('.recipe-list-timer').count()
 # Completion supersedes an open recipe picker, then restores an interactive viewer.
 p.evaluate('timerTest.viewer()');start(p);p.get_by_role('button',name='Open recipes',exact=True).tap();p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and not p.get_by_role('dialog',name='Open Recipes',exact=True).count();ack(p);assert not p.locator('#recipeViewer').evaluate('(e)=>e.inert')
 # Completion cancels an unfinished replacement choice, preserving the finished timer.
 start(p);old=t.timer(p);start(p,0);assert p.get_by_role('dialog',name='Replace current timer?',exact=True).is_visible();p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and not p.get_by_role('dialog',name='Replace current timer?',exact=True).count() and t.timer(p)['id']==old['id'];ack(p)
 # Closing the viewer through browser history while complete must not leave the app inert.
 start(p);p.clock.fast_forward(2100);p.wait_for_timeout(30);p.evaluate('timerTest.close()');p.wait_for_timeout(30);assert popup(p).is_visible();p.evaluate('timerTest.close()');assert popup(p).is_visible();ack(p);assert not p.locator('#list').evaluate('(e)=>e.inert')
 assert not errors,errors;print('PASS',name,'all three list timer surfaces, live pause/resume/hide/delete, completion interrupts transient dialogs and restores focus/inert state safely',flush=True);c.close()
def completed_backup(b,name):
 c,p,errors,_=setup(b,name,360);before=copy.deepcopy(state(p));start(p);p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible();p.clock.fast_forward(6100);assert sound(p) is None
 backup=p.evaluate('timerTest.backup()');assert t.timer(p)['alertHandled'] is True;ack(p);p.evaluate('b=>timerTest.restore(b)',backup);p.reload();p.wait_for_timeout(80);assert popup(p).is_visible() and t.timer(p)['status']=='complete';mock(p);p.evaluate('timerTest.reconcile()');assert p.evaluate('alertCalls.tones')==0;ack(p);assert state(p)==before and not errors,errors
 print('PASS',name,'completed timer and handled-alert marker survive complete backup/restore without replay or recipe/schedule/progress changes',flush=True);c.close()
def every_page_and_edit_draft(b,name):
 c,p,errors,_=setup(b,name,360)
 for view in ['promotionTest.my()','promotionTest.groups()','completionTest.weekly()']:
  if not p.locator('#recipeViewer').count():p.evaluate('timerTest.viewer()')
  start(p);p.evaluate('timerTest.close()');p.evaluate(view);headings=p.locator('#list h2').all_text_contents();schedule=compose(p);p.clock.fast_forward(2100);p.wait_for_timeout(30);assert popup(p).is_visible() and 'Pernil' in popup(p).inner_text();ack(p);assert p.locator('#list h2').all_text_contents()==headings and compose(p)==schedule
 p.evaluate('timerTest.viewer()');start(p,0);p.get_by_role('button',name='Edit Recipe',exact=True).tap();p.wait_for_timeout(850);notes=p.locator('#recipeNotes');p.get_by_role('button',name='Show recipe notes',exact=True).tap();original=notes.input_value();notes.fill('Preserve this unsaved recipe draft.');p.evaluate('timerTest.expired()');p.evaluate('timerTest.reconcile()');p.wait_for_timeout(30);assert popup(p).is_visible();ack(p);assert notes.input_value()=='Preserve this unsaved recipe draft.';notes.fill(original);p.locator('#cancel').tap();assert p.locator('#recipeViewer').is_visible()
 assert not errors,errors;print('PASS',name,'automatic completion on My Rotation/Meal Groups/Weekly Overview and over Edit Recipe preserves page, schedule and unsaved editor draft',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for w in [320,360]:foreground(b,name,w)
   background(b,name);volume_preview(b,name);list_surfaces_and_completion_focus(b,name);completed_backup(b,name);every_page_and_edit_draft(b,name)
  b.close()
