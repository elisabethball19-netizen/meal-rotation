"""Native Chromium Web Audio expiry; this does not verify physical audibility."""
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
f=t.f
f.EXTRA+='''window.nativeAlarmTest={sound:()=>cookingTimerSound?{kind:cookingTimerSound.kind,stopAt:cookingTimerSound.stopAt,state:cookingTimerAudio?.state}:null,watch:()=>{cookingTimerSound.source.addEventListener('ended',()=>{window.nativeAlarmEndedAt=Date.now()})}};'''
def run(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('timerTest.setup()');p.evaluate('timerTest.viewer()');t.icon(p,2).tap();p.wait_for_timeout(2300);assert t.timer(p)['status']=='complete'
 sound=p.evaluate('nativeAlarmTest.sound()')
 if sound:
  assert sound['kind']=='alarm' and sound['state']=='running';p.evaluate('nativeAlarmTest.watch()');p.wait_for_timeout(6100);assert p.evaluate('nativeAlarmTest.sound()') is None;ended=p.evaluate('nativeAlarmEndedAt');assert ended<=sound['stopAt']+500,(ended,sound)
  print('PASS',name,'native Web Audio source ends within six-second window; completed timer remains until acknowledgment (no audibility claim)',flush=True)
 else:print('SKIP',name,'native audio was unavailable/blocked; completion UI still verified',flush=True)
 popup=p.get_by_role('alertdialog',name="Time's Up!",exact=True);assert popup.is_visible();popup.get_by_role('button',name='Acknowledge completed timer',exact=True).tap();assert t.timer(p) is None and not errors,errors;c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
