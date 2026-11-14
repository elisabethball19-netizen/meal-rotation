"""Focused single-dispatch, navigation feedback and compact-row presentation checks."""
import json
from playwright.sync_api import sync_playwright
import rotation_task_corrections_browser as t
f=t.f
f.HOOK+='''window.followupTest={
 calls:[],probe:(mode='normal')=>{followupTest.calls=[];const under=document.createElement('button');under.id='underProbe';under.style.cssText='position:fixed;inset:0;z-index:1';under.onclick=()=>followupTest.calls.push('under');document.body.append(under);
  const d=compactMealDialog('Action probe','Action probe');compactMealLinks(d,[['First',()=>{followupTest.calls.push('first');if(mode==='nested'){const nested=compactMealDialog('Nested probe','Nested probe');compactMealButton(nested,'Nested action',()=>followupTest.calls.push('nested'))}if(mode==='error')throw Error('injected action failure');if(mode==='async-error')return Promise.reject(Error('injected async action failure'))}],['Second',()=>followupTest.calls.push('second')]]);window.oldProbeButtons=[...d.box.querySelectorAll('.meal-quick-actions button')];
 },
 repeat:()=>{oldProbeButtons[0].onclick();oldProbeButtons[1].onclick()},
 clean:()=>document.getElementById('underProbe')?.remove(),
 menu:()=>{const entry=getDisplayedWeekdayMeals().find(e=>e.day==='Tuesday'&&e.cat==='Meals'&&!e.occasional);openTopMealActionMenu(entry.day,entry.cat,entry.meal)},
 remember:()=>{window.oldMealButtons=[...document.querySelectorAll('.compact-meal-dialog button')]},
 repeatMeal:()=>{for(const button of oldMealButtons)if(button.classList.contains('meal-full-action')||button.closest('.meal-quick-actions'))button.onclick()},
 history:()=>history.length,
 layout:()=>{meals.find(m=>m.id===3).name='Roasted vegetables with chickpeas and lemon tahini dressing';meals.find(m=>m.id===3).prep='10';meals.find(m=>m.id===3).cook='20';meals.find(m=>m.id===3).lastCooked='2020-01-01T12:00:00.000Z';timeDisplayPrefs.category.cooking=true;showLastCooked=true;renderList()},
 taskLayout:()=>{document.getElementById('taskLayoutProbe')?.remove();const panel=document.createElement('section');panel.id='taskLayoutProbe';for(const description of ['Chop onions','Defrost chicken roast and prepare vegetables for the family dinner']){const item={...scheduledMakeAheadTasks()[0],task:{...scheduledMakeAheadTasks()[0].task,description}};panel.append(makeAheadReminderRow(item,true))}document.body.prepend(panel)},
 assertTasks:()=>[...document.querySelectorAll('#taskLayoutProbe .make-ahead-reminder')].map(row=>{const text=row.querySelector('button').firstChild,range=document.createRange();range.setStart(text,0);range.setEnd(text,1);const first=range.getBoundingClientRect(),box=row.querySelector('input').getBoundingClientRect();return {delta:Math.abs((first.top+first.bottom-box.top-box.bottom)/2),height:row.getBoundingClientRect().height}})
};'''
def setup(b,name):return t.setup(b,name)
def settle(p):p.clock.run_for(450)
def point(loc):
 b=loc.bounding_box();return (b['x']+b['width']/2,b['y']+b['height']/2)

def dispatch_cases(b,name):
 c,p,e,prefix=setup(b,name)
 for mode in ['normal','touch','nested','error','async-error']:
  before=p.evaluate('correctionTest.snapshot()');p.evaluate('mode=>followupTest.probe(mode)',mode);d=p.get_by_role('dialog',name='Action probe',exact=True);first=point(d.get_by_role('button',name='First',exact=True));second=point(d.get_by_role('button',name='Second',exact=True))
  tap=p.touchscreen.tap if mode=='touch' else p.mouse.click;tap(*first);tap(*second);p.evaluate('followupTest.repeat()');assert p.evaluate('followupTest.calls')==['first'];assert not d.count();assert p.locator('.meal-action-shield').count()==1
  settle(p)
  if mode=='nested':
   child=p.get_by_role('dialog',name='Nested probe',exact=True);child.get_by_role('button',name='Nested action',exact=True).tap();assert p.evaluate('followupTest.calls')==['first','nested'];settle(p)
  elif 'error' in mode:
   alert=p.get_by_role('alertdialog');assert alert.count()==1 and 'injected' in alert.inner_text();alert.get_by_role('button',name='OK',exact=True).tap()
  p.mouse.click(*first);assert p.evaluate('followupTest.calls')[-1]=='under';p.evaluate('followupTest.clean()');assert p.evaluate('correctionTest.snapshot()')==before
 # Existing scheduled actions, nested picker cancellation and Undo/Redo.
 before=sorted(p.evaluate('correctionTest.rows()'),key=json.dumps);p.evaluate('followupTest.menu()');p.evaluate('followupTest.remember()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Select',exact=True).tap();p.evaluate('followupTest.repeatMeal()');assert p.locator('.weekday-meal-picker').count()==1;settle(p);p.locator('.weekday-meal-picker').get_by_role('button',name='Cancel',exact=True).tap();assert sorted(p.evaluate('correctionTest.rows()'),key=json.dumps)==before
 p.evaluate('followupTest.menu()');p.evaluate('followupTest.remember()');history=p.evaluate('followupTest.history()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Leave Tuesday meals empty',exact=False).tap();p.evaluate('followupTest.repeatMeal()');assert p.evaluate('followupTest.history()')==history+1;assert p.locator('.empty-weekday-meal[data-category=Meals]').count()==1;settle(p);p.locator('#undo').tap();assert sorted(p.evaluate('correctionTest.rows()'),key=json.dumps)==before;p.locator('#redo').tap();assert p.locator('.empty-weekday-meal[data-category=Meals]').count()==1
 t.hold(p,t.blank(p));d=p.get_by_role('dialog',name='Empty meal options',exact=True);assert not d.get_by_role('button',name='Auto-Populate Meal',exact=True).count();d.get_by_role('button',name='Resume planned meal',exact=True).tap();settle(p);assert sorted(p.evaluate('correctionTest.rows()'),key=json.dumps)==before
 # Inline date/favorite actions preserve their return flow with a fresh popup.
 p.evaluate('followupTest.menu()');d=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True);d.locator('.meal-options-last-cooked').tap();settle(p);p.get_by_role('dialog',name='Edit last cooked date',exact=True).get_by_role('button',name='Cancel',exact=True).tap();p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).wait_for();assert sorted(p.evaluate('correctionTest.rows()'),key=json.dumps)==before
 favorite=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).locator('.meal-options-favorite');previous=f.record(p,1).get('favorite',False);x,y=point(favorite);p.mouse.click(x,y);p.mouse.click(x,y);settle(p);assert f.record(p,1).get('favorite',False)!=previous;p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Close meal options',exact=True).tap();settle(p)
 assert not e,e;c.close();print('PASS',name,'rapid/detached single dispatch, tap shield, nested/error recovery, actual Select/empty/Resume/Undo/Redo/date/favorite flows',flush=True)

def visual_cases(b,name):
 c,p,e,prefix=setup(b,name)
 item=p.evaluate('correctionTest.showTask({id:1})');p.locator('#taskProbe .make-ahead-task-link').tap();p.clock.run_for(50);card=p.locator('.preparation-meal-target');assert card.count()==1 and card.evaluate('(e)=>e.matches(".top-recipe-wrap,.all-meals-day")');assert not p.locator('.mealname.preparation-meal-target').count();assert card.evaluate('(e)=>getComputedStyle(e).animationDuration')=='1s';assert card.evaluate('(e)=>getComputedStyle(e).filter')!='none';p.screenshot(path='/tmp/followup-shadow-'+name+'.png');p.clock.run_for(1050);assert not p.locator('.preparation-meal-target').count()
 p.emulate_media(reduced_motion='reduce');p.evaluate('correctionTest.showTask({id:1})');p.locator('#taskProbe .make-ahead-task-link').tap();p.clock.run_for(50);assert p.locator('.preparation-meal-target').evaluate('(e)=>getComputedStyle(e).animationName')=='none';p.clock.run_for(1050);assert not p.locator('.preparation-meal-target').count()
 p.evaluate('correctionTest.showTask({id:1})');p.locator('#taskProbe .make-ahead-task-link').focus();p.keyboard.press('Tab');p.keyboard.press('Shift+Tab');assert p.locator('#taskProbe .make-ahead-task-link').evaluate('(e)=>e.matches(":focus-visible")&&getComputedStyle(e).outlineStyle!=="none"')
 p.locator('#taskProbe').evaluate('(e)=>e.remove()');p.evaluate('followupTest.taskLayout()');assert all(row['delta']<=2 for row in p.evaluate('followupTest.assertTasks()')),p.evaluate('followupTest.assertTasks()');assert p.evaluate('followupTest.assertTasks()')[1]['height']>p.evaluate('followupTest.assertTasks()')[0]['height'];p.screenshot(path='/tmp/followup-tasks-'+name+'.png')
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e;c.close();print('PASS',name,'whole-card one-second shadow, reduced motion, keyboard focus, first-line checkbox alignment and wrapping',flush=True)

def ideas_cases(b,name):
 c,p,e,prefix=f.setup(b,name,320);p.evaluate('followupTest.layout()');rows=p.locator('.master-category-meal[data-up-next-star]');heights=rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)');style=p.add_style_tag(content='.master-category-meal[data-up-next-star]:not(.meal-card-edit-mode)>.master-meal-info{align-self:start!important}');assert rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)')==heights;style.evaluate('(e)=>e.remove()')
 assert rows.locator(':scope>.master-meal-info').evaluate_all('(xs)=>xs.every(e=>{const row=e.parentElement.getBoundingClientRect(),b=e.getBoundingClientRect();return Math.abs((row.top+row.bottom-b.top-b.bottom)/2)<2&&getComputedStyle(e).textAlign!=="center"})')
 pin=f.row(p,2).get_by_role('button',name='Unpin recipe',exact=True);assert pin.locator('svg path').first.get_attribute('d')=='M16 9V4l1-1H7l1 1v5l-3 3v2h14v-2Z';pin.tap();assert not f.record(p,2)['upNextStar'];f.row(p,2).get_by_role('button',name='Pin recipe',exact=True).tap();assert f.record(p,2)['upNextStar'];p.reload();f.get(p,'groups()');p.evaluate('followupTest.layout()');assert f.row(p,2).get_by_role('button',name='Unpin recipe',exact=True).locator('svg').get_attribute('fill')=='currentColor';assert f.row(p,4).get_by_role('button',name='Pin recipe',exact=True).locator('svg').get_attribute('fill')=='none'
 f.touch_drag(p,c,f.row(p,2),f.row(p,3));assert f.get(p,'order()')[:2]==['3','2'];p.reload();f.get(p,'groups()');assert f.get(p,'order()')[:2]==['3','2'];p.evaluate('followupTest.layout()');p.screenshot(path='/tmp/followup-ideas-'+name+'.png');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e;c.close();print('PASS',name,'Ideas centering without row-height increase, wrapping/metadata, pushpin fill/toggle/touch drag/reload',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:dispatch_cases(b,name);visual_cases(b,name);ideas_cases(b,name)
  b.close()
