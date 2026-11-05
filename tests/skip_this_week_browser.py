"""One-slot substitutions preserve queues/cooked dates, retained groceries and Undo."""
import copy
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.skipTest={skip:(day='Saturday',cat='Weekend')=>{const entry=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat);return skipScheduledMeal(day,cat,entry.meal)},undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))},history:()=>localStorage.getItem(ROTATION_BACK_KEY),menu:()=>{const item=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Weekend');openTopMealActionMenu(item.day,item.cat,item.meal)},single:()=>{for(const m of meals)if(m.cat==='Weekend'&&m.id!==1)m.rotation=false;persist();renderList()}};'''
f.EXTRA+='''skipTest.retained=(day='Wednesday',cat='Mains')=>{const x=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat),key=cookingOccurrenceKey(cookingContext(activePlanId,x.day,x.cat,x.meal,x.linkedTo));cookingSessions.occurrences[key].ingredients=[];cookingSessions.occurrences[key].steps=[];writeCookingSessions(cookingSessions);occurrenceScales.occurrences[key].multiplier=4;writeOccurrenceScales(occurrenceScales);return {key,session:JSON.parse(JSON.stringify(cookingSessions.occurrences[key])),scale:JSON.parse(JSON.stringify(occurrenceScales.occurrences[key]))}};'''
def run(b,name,width,mode):
 c,p,errors,prefix=f.setup(b,name,width,mode);before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);old_history=p.evaluate('skipTest.history()')
 p.evaluate('promotionTest.my()');p.evaluate('skipTest.menu()');menu=p.get_by_role('dialog',name='Meal options for Saturday',exact=True);assert menu.get_by_role('button',name='Skip This Week',exact=True).count()==1;menu.get_by_role('button',name='Skip This Week',exact=True).tap();p.wait_for_timeout(100)
 after=state(p);now=compose(p);old=next(x for x in schedule if x[0]=='original' and x[1]=='Saturday' and x[2]=='Weekend');new=next(x for x in now if x[0]=='original' and x[1]=='Saturday' and x[2]=='Weekend');assert new[3]!=old[3]
 assert [m['id'] for m in before['meals']]==[m['id'] for m in after['meals']]
 assert before['meals']==after['meals'],'Skip must not edit recipe, rotation membership/order, or last-cooked date'
 for entry in schedule:
  if entry[0]!='original' or entry[1]!='Saturday':assert entry in now,(entry,now)
 for id,source in f.sources(p).items():assert source['checked']==(groceries[id]['checked'] if id in groceries else False),(id,source)
 assert p.evaluate('skipTest.history()')==old_history
 p.evaluate('skipTest.undo()');assert compose(p)==schedule,(compose(p),schedule);assert state(p)['meals']==before['meals'];assert f.sources(p)==groceries,(f.sources(p),groceries)
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,mode,'one slot replaced, queues/cooked dates/history intact, other days/tabs/groceries retained, new quantities unchecked, Undo restores',flush=True);c.close()
def undo_retained_progress(b,name,mode='multiple',day='Wednesday',cat='Mains'):
 c,p,errors,_=f.setup(b,name,360,mode);before=copy.deepcopy(state(p));schedule=compose(p);p.evaluate('skipTest.skip()')
 retained=p.evaluate('([d,c])=>skipTest.retained(d,c)',[day,cat])
 p.evaluate('skipTest.undo()');after=state(p);assert compose(p)==schedule
 assert after['sessions']['occurrences'][retained['key']]==retained['session'] and after['scales']['occurrences'][retained['key']]==retained['scale'],'Undo must preserve later work on retained meals'
 for key,value in before['sessions']['occurrences'].items():
  if value['context']['day']=='Saturday' and key!=retained['key']:assert after['sessions']['occurrences'][key]==value and after['scales']['occurrences'][key]==before['scales']['occurrences'][key]
 assert not errors,errors;print('PASS',name,'Undo restores skipped progress/scaling while preserving later retained-meal cooking progress/scaling',flush=True);c.close()
def no_alternative(b,name):
 c,p,errors,_=f.setup(b,name,360,'single');p.evaluate('skipTest.single()');before=copy.deepcopy(state(p));schedule=compose(p)
 p.evaluate('void skipTest.skip()');p.wait_for_timeout(80);assert 'No alternative eligible recipe' in p.get_by_role('alertdialog').inner_text()
 assert state(p)['meals']==before['meals'] and compose(p)==schedule and not errors
 print('PASS',name,'single recipe leaves slot unchanged with short explanation',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   undo_retained_progress(b,name);undo_retained_progress(b,name,'linked-protected','Saturday','Sides');no_alternative(b,name)
   for width in [320,360]:
    for mode in ['multiple','first-manual','linked-slot','linked-protected']:run(b,name,width,mode)
  b.close()
