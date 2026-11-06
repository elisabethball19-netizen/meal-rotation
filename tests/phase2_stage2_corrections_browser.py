"""Stage 2 correction regressions with synthetic browser storage only.

MEAL_STAGE2_EXPECT_FAILURES=1 verifies the two review findings before correction.
MEAL_STAGE2_SOURCE_ROOT selects an unchanged application checkout.
"""
import copy
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import phase2_stage2_browser as stage2
stage=stage2.stage
if os.environ.get('MEAL_STAGE2_SOURCE_ROOT'):
 stage.f.ROOT=Path(os.environ['MEAL_STAGE2_SOURCE_ROOT'])
stage.f.HOOK += '''window.stage2Correction={
 weighted:()=>{for(const m of meals)if(m.cat==='Sides'){m.rotation=true;delete m.favorite}meals.find(m=>m.id===13).favorite=true;meals.push({...JSON.parse(JSON.stringify(meals.find(m=>m.id===14)||meals.find(m=>m.id===13))),id:14,name:'Another Side Two',favorite:false});id=Math.max(id,15);const indices=meals.map((m,i)=>m.cat==='Sides'?i:-1).filter(i=>i>=0),ordered=indices.map(i=>meals[i]).sort((a,b)=>a.id-b.id);indices.forEach((slot,i)=>meals[slot]=ordered[i]);stage2Test.paired();delete mealPlans[0].favoriteRotationScores;persist();renderList()},
 pool:()=>automaticSlotCandidates(mealPlans[0],'Tuesday','Sides').map(m=>({id:m.id,favorite:!!m.favorite})),
 queue:()=>meals.filter(m=>m.cat==='Sides'&&m.rotation).map(m=>m.id),
 scores:()=>mealPlans.map(p=>({id:p.id,scores:p.favoriteRotationScores||null})),
 back:selected=>selected?rotateSelectedBack(['original||Tuesday::Rice']):rotateAllBack(),
 edit:()=>{meals.find(m=>m.id===1).notes='Unrelated edit after rotation';persist()},
 multi:()=>{const lunch=mealPlans.find(p=>p.id==='lunch');lunch.weekdayMealOverrides['Tuesday::Sides']='13';lunch.cycleRetainedSlots['Tuesday::Sides']='13';lunch.cycleSlotChoices['Tuesday::Sides']={mealId:'13',parentId:'',substitution:true};weekdayCategories={Tuesday:['Rice','Sides']};mealPlans[0].weekdayCategories=weekdayCategories;saveActiveMealPlan();persist();renderList()}
};'''

def setup(browser,name,**kw):return stage2.setup(browser,name,**kw)
def side_state(p):return p.evaluate('({queue:stage2Correction.queue(),scores:stage2Correction.scores()})')
def definitions(p):return json.loads(stage.definitions(p))
def schedule_dialog(p,id):
 p.evaluate('stage2Test.groups',id);p.get_by_role('dialog',name='Meal options',exact=True).get_by_role('button',name='Schedule Meal',exact=True).click()
 return p.get_by_role('dialog',name='Schedule Meal',exact=True)

def history(browser,name,selected=False,creation=None,backup=False,full_rotate=False):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('stage2Correction.weighted()')
 before=side_state(p)
 if creation is None:
  d=schedule_dialog(p,3);d.get_by_role('combobox',name='Weekday').select_option('Tuesday');d.get_by_role('combobox',name='Meal slot').select_option('Rice');d.get_by_role('button',name='Schedule meal',exact=True).click();main=3
 else:
  p.evaluate('weekTest.my();weekTest.chooser()');p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True).get_by_role('button',name='Create New Recipe',exact=True).click();d=p.get_by_role('dialog',name='Create New Recipe',exact=True);stage2.fill_recipe(d,'Created paired main',rotation=creation);d.get_by_role('button',name='Save recipe and schedule',exact=True).click();main=next(m['id'] for m in stage.state(p)['meals'] if m['name']=='Created paired main')
 choice=copy.deepcopy(stage.plan(p)['cycleSlotChoices']['Tuesday::Rice']);assert choice['preserveSideQueue'] is True
 pool=p.evaluate('stage2Correction.pool()');assert len(pool)>=2 and any(m['favorite'] for m in pool)
 assert next(e for e in stage.rows(p) if e['planId']=='original' and e['day']=='Tuesday' and e['cat']=='Sides')['id']==13
 assert side_state(p)==before
 library=definitions(p);rotate='weekTest.rotate()' if full_rotate else 'weekTest.rotate(["Tuesday::Rice"])';p.evaluate(rotate);assert side_state(p)==before,'First expiration must not consume a side turn'
 if backup:
  saved=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',saved);p.reload()
 p.evaluate('stage2Correction.edit()');p.evaluate('stage2Correction.back',selected)
 restored=copy.deepcopy(stage.plan(p)['cycleSlotChoices']['Tuesday::Rice'])
 if os.environ.get('MEAL_STAGE2_EXPECT_FAILURES')!='1':assert all(restored.get(key)==value for key,value in choice.items()),'Rotation Back must retain complete scheduling choice metadata'
 assert side_state(p)==before
 assert next(e for e in stage.rows(p) if e['planId']=='original' and e['day']=='Tuesday' and e['cat']=='Rice')['id']==main
 assert next(m for m in definitions(p) if m['id']==1)['notes']=='Unrelated edit after rotation'
 assert [{**m,'notes':next(old['notes'] for old in library if old['id']==m['id'])} for m in definitions(p)]==library
 p.reload()
 if backup:
  saved=p.evaluate('weekTest.storage()');p.evaluate('weekTest.once()');p.evaluate('weekTest.restore',saved);p.reload()
 assert stage.plan(p)['cycleSlotChoices']['Tuesday::Rice']==restored
 states=list(stage.plan(p)['dependentSideState'].values())
 if os.environ.get('MEAL_STAGE2_EXPECT_FAILURES')!='1':assert len(states)==1 and states[0]['mainId']==str(main) and states[0]['automatic'] is False
 p.evaluate(rotate);assert side_state(p)==before,'Restored expiration must not move side queue or charge Favorites: '+json.dumps({'before':before,'after':side_state(p)})
 assert next(m for m in definitions(p) if m['id']==1)['notes']=='Unrelated edit after rotation'
 stage2.clean(errors);c.close();print('PASS',name,'full' if not selected else 'selected','history',creation,'backup',backup,'protects weighted side pool through reload and second rotation',flush=True)

def duplicate_ui(browser,name,side=False):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('stage2Correction.multi();weekTest.check()');id=next(e['id'] for e in stage.rows(p) if e['planId']=='original' and e['day']=='Tuesday' and e['cat']==('Sides' if side else 'Rice'));target='Rice' if side else 'Sides';before=p.evaluate('weekTest.storage()');rows=stage.rows(p);checks=stage2.prior.progress(p);queue=stage.queues(p)
 d=schedule_dialog(p,id);d.get_by_role('combobox',name='Weekday').select_option('Tuesday');d.get_by_role('combobox',name='Meal slot').select_option(target);d.get_by_role('button',name='Schedule meal',exact=True).click()
 assert d.is_visible(),'Unsupported same-day duplicate must keep the scheduling dialog open'
 expect(d.get_by_role('status')).to_contain_text('already scheduled');expect(d.get_by_role('status')).to_contain_text('another group');assert p.evaluate('weekTest.storage()')==before and stage.rows(p)==rows and stage2.prior.progress(p)==checks and stage.queues(p)==queue
 # Another day is supported without moving the original occurrence.
 d.get_by_role('combobox',name='Weekday').select_option('Wednesday');d.get_by_role('button',name='Schedule meal',exact=True).click();assert not d.count();assert any(e['day']=='Wednesday' and e['planId']=='original' and e['id']==id for e in stage.rows(p));assert all(e in stage.rows(p) for e in rows)
 # Same weekday in a different meal tab is also supported.
 d=schedule_dialog(p,id);d.get_by_role('combobox',name='Meal tab').select_option('lunch');d.get_by_role('combobox',name='Weekday').select_option('Tuesday');d.get_by_role('button',name='Schedule meal',exact=True).click();assert not d.count();assert any(e['day']=='Tuesday' and e['planId']=='lunch' and e['id']==id for e in stage.rows(p));assert all(e in stage.rows(p) for e in rows if e['planId']!='lunch' or e['day']!='Tuesday')
 p.reload();assert any(e['day']=='Wednesday' and e['id']==id for e in stage.rows(p));stage2.clean(errors);c.close();print('PASS',name,'side' if side else 'main','same-day duplicate UI rejection has no state changes; other day/tab succeeds',flush=True)

def automatic_control(browser,name):
 c,p,errors,_=setup(browser,name);p.evaluate('stage2Correction.weighted()');before=side_state(p);assert not stage.plan(p)['cycleSlotChoices']['Tuesday::Rice'].get('preserveSideQueue')
 p.evaluate('weekTest.rotate(["Tuesday::Rice"])');after=side_state(p);assert after['queue']!=before['queue'] and after['scores']!=before['scores'],'Ordinary automatic side rotations must still consume weighted turns'
 stage2.clean(errors);c.close();print('PASS',name,'normal automatic side queue and Favorites advancement unchanged',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  baseline=os.environ.get('MEAL_STAGE2_EXPECT_FAILURES')=='1'
  for name in ['index.html','meal-rotation-test.html']:
   cases=[('S2-1 full',lambda:history(b,name)),('S2-1 selected',lambda:history(b,name,True)),('S2-2 main',lambda:duplicate_ui(b,name)),('S2-2 side',lambda:duplicate_ui(b,name,True))]
   for label,case in cases:
    if baseline:
     try:case()
     except AssertionError as e:
      expected='Restored expiration must not move side queue or charge Favorites' if label.startswith('S2-1') else 'Unsupported same-day duplicate must keep the scheduling dialog open'
      assert expected in str(e),'Unexpected reproduction failure: '+str(e)
      print('REPRODUCED',name,label,str(e).splitlines()[0],flush=True)
     else:raise AssertionError('Expected defect did not reproduce: '+name+' '+label)
    else:case()
   if not baseline:
    automatic_control(b,name)
    for selected in [False,True]:
     for rotation in [False,True]:history(b,name,selected,rotation,backup=True,full_rotate=not selected)
     history(b,name,selected,backup=True,full_rotate=True)
  b.close()
