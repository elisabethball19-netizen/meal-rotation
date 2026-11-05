"""One deadline-based cooking timer; isolated storage and mocked browser alert APIs."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.timerTest={
 resetAudio:()=>{stopCookingTimerSound();cookingTimerAudio=null},durations:recipeCookingDurations,state:()=>cookingTimer,remaining:cookingTimerRemaining,
 viewer:(id=1)=>{const m=meals.find(m=>m.id===id);openRecipeViewer(m,cookingContext('original','Saturday',m.cat,m))},
 close:()=>{finishRecipeViewerClose();window.history.replaceState({},'')},
 setup:()=>{const m=meals.find(m=>m.id===1);m.instructions=['Simmer for 10–15 minutes.','Bake for 1 hour and 30 minutes, then rest for 5 minutes.','Heat to 350°F and add 2 cups rice.','Wait 2 seconds.','Rest 5 min.'];m.linkedMealIds=[20];meals.find(m=>m.id===20).instructions=['Cook 30 seconds.'];persist();},
 mode:mode=>{recipeViewer.activeTab.mode=mode;recipeViewPrefs.mode=mode;renderRecipeViewer()},
 backup:()=>slotBackup.capture(),storage:key=>localStorage.getItem(key),
 restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true},
 page:()=>{showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);render()},
 expired:()=>{cookingTimer.deadline=Date.now()-100;saveCookingTimer()},
 
 parseInvalid:raw=>{localStorage.setItem(COOKING_TIMER_KEY,raw);return readCookingTimer()},
 clock:cookingTimerClock,
 reconcile:syncCookingTimer
};'''
PARSER=[
 ('Simmer for 15 minutes',[900000]),('Bake for 30 minutes',[1800000]),('Let rest for 5 minutes',[300000]),('Cook for 1 hour',[3600000]),
 ('Simmer for 10–15 minutes',[600000]),('Bake 15-10 min',[600000]),('Wait 10 to 15 seconds',[10000]),('Cook 1 hr. 30 mins.',[5400000]),
 ('Bake 1 hour and 30 minutes; rest 5 minutes',[5400000,300000]),('Heat to 350°F and add 2 cups rice',[]),('Set oven to 180°C',[]),
 ('Cook 20 min at 200 degrees',[1200000]),('Wait 30 sec. then boil 2 hrs',[30000,7200000]),('Rest for half an hour',[1800000]),
 ('Rest for an hour',[3600000]),('Cook for one and a half hours',[5400000]),('Wait 1½ hours',[5400000]),('Wait 1 1/2 hours',[5400000]),
 ('Wait ½ hour',[1800000]),('Wait 1/2 minute',[30000]),('Cook for 1h30m',[5400000]),('Cook 10 min–15 min',[600000]),('Rest 1 hour to 90 minutes',[3600000]),
 ('Add 2 tablespoons oil and 5 g salt',[]),('Cut into 2 m lengths',[]),('Rest for 5 m',[300000]),('1. Stir well. 2. Fold in flour.',[]),('Created 2026-11-05 12:30',[]),
 ('Simmer 0 minutes',[]),('Set aside 99999 hours',[]),('Wait 20s',[20000]),('Cook TWO HOURS',[7200000]),('Cook for 1.5 hours',[5400000]),('Simmer twenty-five minutes',[1500000]),('Bake forty five minutes',[2700000]),('Cook -5 minutes',[]),('Take a 15-minute rest',[900000]),('Wait 5 minutes then rest 5 minutes',[300000,300000])]
def step(p,n):return p.locator('.recipe-viewer-steps .cooking-item').nth(n)
def icon(p,n=0):return p.locator('.recipe-viewer-steps .recipe-step-timer').nth(n)
def timer(p):return p.evaluate('timerTest.state()')
def strip(p):return p.locator('.recipe-timer-strip')
def choice(p,title,label):p.get_by_role('dialog',name=title,exact=True).get_by_role('button',name=label,exact=True).tap()
def stable(p,before,schedule,groceries):
 after=state(p);assert compose(p)==schedule and f.sources(p)==groceries
 for key in ['meals','sessions','scales','prefs']:assert after[key]==before[key],key

def mock_alerts(p,permission='default'):
 p.evaluate('''permission=>{
 window.alertCalls={permissions:0,notifications:[],tones:0,stops:0,loops:[],levels:[]};timerTest.resetAudio();
 class Alerts{static permission=permission;static requestPermission(){alertCalls.permissions++;Alerts.permission='granted';return Promise.resolve('granted')}constructor(title,options){alertCalls.notifications.push({title,...options})}};window.Notification=Alerts;
 Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:{getRegistration:async()=>({showNotification:async(title,options)=>alertCalls.notifications.push({title,...options})})}});
 class Audio{constructor(){this.state='suspended';this.currentTime=0;this.sampleRate=8000}resume(){this.state='running';return Promise.resolve()}createBuffer(channels,length,rate){const data=new Float32Array(length);return {getChannelData:()=>data}}createBufferSource(){return {loop:false,connect(){},disconnect(){},start(){alertCalls.tones++;alertCalls.loops.push(this.loop)},stop(){alertCalls.stops++;this.onended?.()}}}createGain(){return {gain:{setValueAtTime(v){alertCalls.levels.push(v)}},connect(){},disconnect(){}}}get destination(){return {}}};window.AudioContext=Audio;
 }''',permission)

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.clock.install();p.evaluate('timerTest.setup()');p.evaluate('promotionTest.check()');mock_alerts(p)
 for text,expected in PARSER:
  got=p.evaluate('text=>timerTest.durations(text).map(x=>x.ms)',text);assert got==expected,(text,got,expected)
 assert p.evaluate('timerTest.clock(3600000)')=='1:00:00'
 p.evaluate('timerTest.viewer()');before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 assert p.locator('.recipe-step-timer').count()==4
 assert step(p,2).locator('..').locator('.recipe-step-timer').count()==0
 assert p.evaluate('alertCalls.permissions')==0
 icon(p).tap();p.wait_for_timeout(30)
 first=timer(p);assert first['recipeId']=='1' and first['stepToken']==step(p,0).get_attribute('data-cooking-token')
 assert 599000<=p.evaluate('timerTest.remaining()')<=600000
 assert step(p,0).get_attribute('aria-pressed')=='false' and strip(p).count()==1
 assert '10:00 remaining' in strip(p).inner_text()
 # Completion and long press remain independent of the timer icon.
 step(p,0).tap();assert step(p,0).get_attribute('aria-pressed')=='true'
 assert icon(p).is_visible() and timer(p)['id']==first['id']
 step(p,0).tap();assert step(p,0).get_attribute('aria-pressed')=='false'
 p.clock.fast_forward(32000);assert '9:28 remaining' in strip(p).inner_text()
 p.get_by_role('button',name='Pause timer',exact=True).tap();remaining=p.evaluate('timerTest.remaining()');p.clock.fast_forward(60000)
 assert p.evaluate('timerTest.remaining()')==remaining and timer(p)['status']=='paused'
 p.get_by_role('button',name='Resume timer',exact=True).tap();p.clock.fast_forward(10000);assert 557000<=p.evaluate('timerTest.remaining()')<=558000
 # Multiple distinct durations require a choice; cancellation preserves the active timer.
 icon(p,1).tap();d=p.get_by_role('dialog',name='Choose cooking duration',exact=True)
 assert d.locator('.smallbtn').count()==2;d.get_by_role('button',name='Cancel timer selection',exact=True).tap();assert timer(p)['id']==first['id']
 icon(p,1).tap();d=p.get_by_role('dialog',name='Choose cooking duration',exact=True);d.locator('.smallbtn').nth(0).tap()
 choice(p,'Replace current timer?','Keep current timer');assert timer(p)['id']==first['id']
 icon(p,1).tap();p.get_by_role('dialog',name='Choose cooking duration',exact=True).locator('.smallbtn').nth(1).tap()
 choice(p,'Replace current timer?','Replace timer');assert 299000<=p.evaluate('timerTest.remaining()')<=300000
 second=timer(p);p.get_by_role('button',name='Enable timer notifications',exact=True).tap();assert p.evaluate('alertCalls.permissions')==1
 # Timer remains associated with its original recipe/instruction while switching linked tabs.
 p.get_by_role('button',name='Current side',exact=True).tap();assert timer(p)['id']==second['id'] and timer(p)['recipeName']=='Pernil'
 assert strip(p).locator('.recipe-timer-source').inner_text()=='Pernil · Step 2'
 p.clock.fast_forward(10000);assert '4:50 remaining' in strip(p).inner_text()
 p.evaluate('timerTest.close()');p.evaluate('timerTest.page()');p.clock.fast_forward(15000);p.evaluate('timerTest.viewer(20)')
 assert timer(p)['id']==second['id'] and '4:35 remaining' in strip(p).inner_text()
 p.reload();assert timer(p)['id']==second['id'] and timer(p)['status']=='running'
 p.evaluate('timerTest.viewer()');assert strip(p).count()==1
 p.get_by_role('button',name='Pause timer',exact=True).tap();paused=p.evaluate('timerTest.remaining()');p.reload();p.clock.fast_forward(30000)
 assert timer(p)['status']=='paused' and p.evaluate('timerTest.remaining()')==paused
 p.evaluate('timerTest.viewer()');p.get_by_role('button',name='Resume timer',exact=True).tap()
 # Deadline jumps model suspended callbacks: reconcile on focus and emit completion once.
 mock_alerts(p,'granted');p.evaluate('timerTest.expired()');p.evaluate("window.dispatchEvent(new Event('focus'))");p.wait_for_timeout(20)
 assert timer(p)['status']=='complete' and 'Timer finished' in strip(p).inner_text()
 assert len(p.evaluate('alertCalls.notifications'))==1
 for _ in range(3):p.evaluate('timerTest.reconcile()')
 assert len(p.evaluate('alertCalls.notifications'))==1
 p.reload();p.evaluate('timerTest.viewer()');assert timer(p)['status']=='complete' and 'Timer finished' in strip(p).inner_text()
 p.get_by_role('button',name='Dismiss finished timer',exact=True).tap();assert timer(p) is None and not strip(p).count()
 # Sound on an unlocked audio context, no permission requests until explicitly enabled.
 mock_alerts(p,'denied');icon(p,2).tap();p.evaluate('timerTest.close()');p.evaluate('timerTest.page()');p.clock.fast_forward(2100)
 assert timer(p)['status']=='complete' and p.evaluate('alertCalls.tones')==1 and p.evaluate('alertCalls.permissions')==0 and not p.evaluate('alertCalls.notifications')
 p.evaluate('timerTest.reconcile()');assert p.evaluate('alertCalls.tones')==1
 p.evaluate('timerTest.viewer()')
 p.get_by_role('button',name='Dismiss finished timer',exact=True).tap()
 # Final comparison excludes only progress deliberately toggled off again (stored empty session may exist).
 after=state(p)
 for key in ['meals','scales','prefs']:assert after[key]==before[key],(key,before[key],after[key])
 assert compose(p)==schedule,('schedule',schedule,compose(p))
 assert f.sources(p)==groceries,('groceries',groceries,f.sources(p))
 assert after['sessions']==before['sessions'],('sessions',before['sessions'],after['sessions'])
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'38 parser cases; timer/step isolation, choices/replacement, pause/resume, tabs/pages/reload, deadline recovery, one-shot mocked alerts, no data/schedule/grocery changes',flush=True);c.close()

def recovery(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.clock.install();p.evaluate('timerTest.setup()');p.evaluate('promotionTest.check()');p.evaluate('timerTest.viewer()')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 mock_alerts(p,'denied');icon(p).tap();original=timer(p);backup=p.evaluate('timerTest.backup()')
 assert json.loads(backup['mealRotationCookingTimerV1'])['id']==original['id']
 icon(p,1).tap();assert p.get_by_role('dialog',name='Choose cooking duration',exact=True).is_visible()
 p.go_back();p.wait_for_timeout(50);assert not p.locator('.recipe-timer-dialog').count() and not p.locator('#recipeViewer').count() and timer(p)['id']==original['id']
 p.evaluate('timerTest.viewer()')
 p.get_by_role('button',name='Cancel timer',exact=True).tap();p.evaluate('storage=>timerTest.restore(storage)',backup);p.reload();p.evaluate('timerTest.viewer()')
 assert timer(p)['id']==original['id'] and strip(p).count()==1
 # Expiration while absent is reconciled from persisted deadline during reload.
 p.evaluate('timerTest.expired()');p.reload();assert timer(p)['status']=='complete'
 p.evaluate('timerTest.viewer()');assert 'Timer finished' in strip(p).inner_text()
 # Completed alarm is replaced only by an explicit choice, never silently dismissed.
 icon(p).tap();choice(p,'Replace current timer?','Replace timer');assert timer(p)['status']=='running' and timer(p)['id']!=original['id'] and not p.get_by_role('dialog',name='Replace current timer?',exact=True).count()
 # Notification APIs are optional and storage failures must not interrupt a live timer.
 p.get_by_role('button',name='Cancel timer',exact=True).tap()
 p.evaluate("()=>{Object.defineProperty(window,'Notification',{configurable:true,value:undefined});}")
 # Delete rather than leave an undefined Notification property for feature detection.
 p.evaluate("delete window.Notification")
 p.evaluate("()=>{const set=Storage.prototype.setItem;window.timerNativeSet=set;Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationCookingTimerV1'))throw Error('quota');return set.call(this,key,value)}}")
 icon(p,2).tap();p.clock.fast_forward(2100);assert timer(p)['status']=='complete' and not p.get_by_role('button',name='Enable timer notifications',exact=True).count()
 p.get_by_role('button',name='Dismiss finished timer',exact=True).tap();assert timer(p) is None
 p.evaluate('()=>{Storage.prototype.setItem=window.timerNativeSet}')
 assert p.evaluate('timerTest.parseInvalid("{broken")') is None
 assert p.evaluate('timerTest.parseInvalid(JSON.stringify({version:1,status:"running",deadline:"bad"}))') is None
 stable(p,before,schedule,groceries)
 assert not errors,errors
 print('PASS',name,'timer backup/restore, suspended reload expiry, direct restart after completion, unsupported alerts, storage failure and malformed timer records; saved app data unchanged',flush=True);c.close()

def layout(b,name,width,mode,landscape):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('timerTest.setup()');p.evaluate('timerTest.viewer()');p.evaluate('mode=>timerTest.mode(mode)',mode)
 if landscape:p.set_viewport_size({'width':740,'height':360})
 icon(p).tap();p.wait_for_timeout(100)
 assert strip(p).count()==1 and strip(p).is_visible()
 dimensions=p.evaluate('''()=>{const bar=document.querySelector('.recipe-viewer-bar').getBoundingClientRect(),s=document.querySelector('.recipe-timer-strip').getBoundingClientRect(),panes=[...document.querySelectorAll('.recipe-pane')].map(e=>({top:e.getBoundingClientRect().top,bottom:e.getBoundingClientRect().bottom,height:e.clientHeight}));return {bar:{top:bar.top,bottom:bar.bottom},strip:{top:s.top,bottom:s.bottom},panes,width:document.documentElement.scrollWidth,window:innerWidth}}''')
 assert dimensions['width']<=dimensions['window'] and dimensions['strip']['bottom']<=dimensions['bar']['bottom'],dimensions
 if mode=='split':
  assert all(x['top']>=dimensions['bar']['bottom'] and x['height']>30 for x in dimensions['panes']),dimensions
 else:
  p.locator('.recipe-instructions-pane').evaluate('(e)=>{e.append(Object.assign(document.createElement("div"),{style:"height:1800px"}))}')
  p.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=900');p.wait_for_timeout(80)
  assert strip(p).bounding_box()['y']>=0 and strip(p).bounding_box()['y']<p.evaluate('innerHeight')
 if name.startswith('meal-') and width==360:p.screenshot(path='/tmp/cooking-timer-'+mode+('-landscape' if landscape else '-portrait')+'.png')
 p.get_by_role('button',name='Cancel timer',exact=True).tap();assert timer(p) is None and not strip(p).count()
 assert not errors,errors
 print('PASS',name,width,mode,'landscape' if landscape else 'portrait','sticky countdown, usable independent panels, no overlap/overflow, cancel',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   recovery(b,name)
   for width in [320,360]:
    run(b,name,width)
    for mode in ['full','split']:
     for landscape in [False,True]:layout(b,name,width,mode,landscape)
  b.close()
