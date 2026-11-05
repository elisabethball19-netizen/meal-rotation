"""Shared one-row countdown, distinct hide/delete semantics and reopen without restart."""
import copy,re
from playwright.sync_api import sync_playwright
import timer_list_indicators_browser as l
from scheduled_linked_slots_browser import state,compose
f=l.f;t=l.t;a=l.a
f.EXTRA+='''window.compactTimerTest={long:()=>{const m=meals.find(m=>m.id===3);m.instructions=['Cook for 720 hours.'];persist()},scrollSeed:()=>{const m=meals.find(m=>m.id===3);m.ingredients=Array.from({length:80},(_,i)=>'Ingredient '+i);m.instructions=Array.from({length:40},(_,i)=>'Step '+i+': simmer for 15 minutes. '+('Stir carefully. '.repeat(6)));persist()},settings:()=>recipeViewPrefs};'''
def row(p,popup=False):return p.locator('#cookingTimerControlsDialog .recipe-timer-strip' if popup else '#recipeViewer .recipe-timer-strip')
def check_row(p,popup=False,complete=False,long=False):
 r=row(p,popup);assert r.count()==1 and r.is_visible()
 assert re.fullmatch(r'\d{2,3}:\d{2}(?::\d{2})?',r.locator('.recipe-timer-readout').inner_text())
 buttons=r.locator('.recipe-timer-controls button');assert buttons.count()==3 and all(not x for x in buttons.all_inner_texts())
 assert buttons.nth(0).get_attribute('aria-label') in ['Pause timer','Resume timer','Timer finished']
 assert buttons.nth(1).get_attribute('aria-label')=='Hide timer controls' and buttons.nth(2).get_attribute('aria-label')=='Delete timer'
 assert not r.locator('.recipe-timer-source,.recipe-timer-info').count()
 if popup:assert not p.locator('#cookingTimerControlsDialog strong,#cookingTimerControlsDialog .recipe-timer-dialog-heading').count()
 boxes=[x.bounding_box() for x in [r.locator('.recipe-timer-readout'),buttons.nth(0),buttons.nth(1),buttons.nth(2)]]
 centers=[b['y']+b['height']/2 for b in boxes];assert max(centers)-min(centers)<3,boxes
 assert all(boxes[i]['x']+boxes[i]['width']<=boxes[i+1]['x']+1 for i in range(3)),boxes
 assert r.bounding_box()['height']<=48
 assert r.evaluate('(e)=>getComputedStyle(e).borderTopWidth')=='0px'
 assert r.locator('.recipe-timer-readout').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=(20 if long else 24)
 if complete:assert r.locator('.recipe-timer-readout').inner_text()=='00:00' and buttons.nth(0).is_disabled()
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')

def run(b,name,width,mode,landscape=False):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.clock.install();p.evaluate('timerListTest.seed()');p.evaluate('promotionTest.check()');p.evaluate('timerListTest.page("top")');p.evaluate('timerTest.viewer(3)');p.evaluate('mode=>timerTest.mode(mode)',mode);t.mock_alerts(p,'denied')
 if landscape:p.set_viewport_size({'width':740,'height':360})
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 t.icon(p).tap();initial=t.timer(p);check_row(p)
 row(p).get_by_role('button',name='Hide timer controls',exact=True).tap();assert not row(p).count() and t.timer(p)['id']==initial['id'] and t.timer(p)['deadline']==initial['deadline']
 assert p.get_by_role('button',name='Show timer',exact=True).is_visible()
 p.clock.fast_forward(5000);t.icon(p).tap();check_row(p);assert t.timer(p)['id']==initial['id'] and t.timer(p)['deadline']==initial['deadline'] and row(p).locator('.recipe-timer-readout').inner_text()=='14:55'
 assert not p.get_by_role('dialog',name='Replace current timer?',exact=True).count()
 row(p).get_by_role('button',name='Hide timer controls',exact=True).tap()
 p.locator('#recipeViewer').get_by_role('button',name='Current side',exact=True).tap();assert not row(p).count() and p.get_by_role('button',name='Show timer',exact=True).is_visible()
 p.get_by_role('button',name='Show timer',exact=True).tap();check_row(p);assert t.timer(p)['id']==initial['id']
 row(p).get_by_role('button',name='Pause timer',exact=True).tap();remaining=t.timer(p)['remaining'];p.clock.fast_forward(10000);assert t.timer(p)['remaining']==remaining
 row(p).get_by_role('button',name='Hide timer controls',exact=True).tap();p.get_by_role('button',name='Show timer',exact=True).tap();assert t.timer(p)['status']=='paused'
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(80)
 l.page(p,'top');l.indicator(p).first.tap();check_row(p,True)
 assert row(p,True).locator('.recipe-timer-readout').inner_text()=='14:55'
 row(p,True).get_by_role('button',name='Resume timer',exact=True).tap();p.clock.fast_forward(3000);check_row(p,True)
 row(p,True).get_by_role('button',name='Hide timer controls',exact=True).tap();assert not l.popup(p).count() and t.timer(p)['id']==initial['id'] and t.timer(p)['status']=='running'
 l.indicator(p).first.tap();row(p,True).get_by_role('button',name='Pause timer',exact=True).tap();row(p,True).get_by_role('button',name='Hide timer controls',exact=True).tap()
 p.evaluate('timerTest.viewer(3)');check_row(p);assert t.timer(p)['status']=='paused'
 row(p).get_by_role('button',name='Resume timer',exact=True).tap();p.clock.fast_forward(t.timer(p)['remaining']+100);check_row(p,complete=True)
 assert a.sound(p)['kind']=='alarm'
 row(p).get_by_role('button',name='Hide timer controls',exact=True).tap();assert a.sound(p)['kind']=='alarm' and t.timer(p)['status']=='complete'
 p.get_by_role('button',name='Show timer',exact=True).tap();check_row(p,complete=True)
 if name.startswith('meal-') and width==360:p.screenshot(path='/tmp/compact-timer-viewer-'+mode+('-landscape' if landscape else '-portrait')+'.png')
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(80);l.page(p,'groups','complete');l.indicator(p).first.tap();check_row(p,True,complete=True)
 if name.startswith('meal-') and width==360:p.screenshot(path='/tmp/compact-timer-popup-'+mode+('-landscape' if landscape else '-portrait')+'.png')
 row(p,True).get_by_role('button',name='Delete timer',exact=True).tap();assert t.timer(p) is None and a.sound(p) is None and not l.popup(p).count() and not p.locator('.recipe-list-timer').count()
 p.evaluate('timerTest.viewer(3)');t.icon(p).tap();row(p).get_by_role('button',name='Delete timer',exact=True).tap();assert t.timer(p) is None and not row(p).count() and not p.get_by_role('button',name='Show timer',exact=True).count()
 t.stable(p,before,schedule,groceries)
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,mode,landscape,'shared single row/3 icons, large clock, hide/reopen unchanged deadline, source-icon restore, synchronized pause/resume, 00:00/alarm retained on hide, delete clears alarm/indicators, no data changes',flush=True);c.close()

def scrolling(b,name,landscape):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('timerListTest.seed()');p.evaluate('compactTimerTest.scrollSeed()');p.evaluate('timerTest.viewer(3)')
 if landscape:p.set_viewport_size({'width':740,'height':360})
 t.icon(p).first.tap();p.wait_for_timeout(100)
 panes=p.locator('.recipe-pane');panes.nth(0).evaluate('(e)=>e.scrollTop=600');panes.nth(1).evaluate('(e)=>e.scrollTop=800');p.wait_for_timeout(100)
 before=panes.evaluate_all('(ps)=>ps.map(p=>p.scrollTop)');prefs=p.evaluate('compactTimerTest.settings()');assert all(x>0 for x in before)
 row(p).get_by_role('button',name='Hide timer controls',exact=True).tap();p.wait_for_timeout(100)
 assert panes.evaluate_all('(ps)=>ps.map(p=>p.scrollTop)')==before
 p.get_by_role('button',name='Show timer',exact=True).tap();p.wait_for_timeout(100)
 assert panes.evaluate_all('(ps)=>ps.map(p=>p.scrollTop)')==before and p.evaluate('compactTimerTest.settings()')==prefs
 assert not errors,errors
 print('PASS',name,landscape,'hiding/restoring timer preserves independent long-panel scroll positions and divider preferences',flush=True);c.close()

def long_timer(b,name):
 c,p,errors,_=f.setup(b,name,320,'multiple');p.clock.install();p.evaluate('timerListTest.seed()');p.evaluate('compactTimerTest.long()');p.evaluate('timerTest.viewer(3)');t.icon(p).tap();check_row(p,long=True)
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(80);l.page(p,'top','running');l.indicator(p).first.tap();check_row(p,True,long=True)
 assert row(p,True).locator('.recipe-timer-readout').inner_text().startswith('720:')
 assert not errors,errors
 print('PASS',name,'long-hour countdown remains readable and single-row at 320px in both surfaces',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   long_timer(b,name)
   for landscape in [False,True]:scrolling(b,name,landscape)
   for width in [320,360]:
    for mode in ['full','split']:
     for landscape in [False,True]:run(b,name,width,mode,landscape)
  b.close()
