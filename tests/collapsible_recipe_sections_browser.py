"""UI-only independent section preferences and fixed weekday badge columns."""
import json,tempfile,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from section_visibility_fixture import expand_recipe_sections,reveal_recipe
from scheduled_linked_slots_browser import state,compose
ROOT=Path(__file__).resolve().parents[1]
f.EXTRA+='''window.sectionUITest={
 rename:()=>renameCategoryDirect('Weekend'),
 group:cat=>openMasterCategories(cat),
 manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 prepare:multi=>{const template=JSON.parse(JSON.stringify(meals[0]));for(const id of [30,31,32])meals.push({...JSON.parse(JSON.stringify(template)),id,name:'Recipe '+id,linkedMealIds:[]});
 meals.find(m=>m.id===1).name='Quick recipe';meals.find(m=>m.id===2).name='Very long slow-cooked garlic chicken with roasted garden vegetables and jasmine rice';meals.find(m=>m.id===3).name='Linked recipe with several lines of supporting details';meals.find(m=>m.id===3).linkedMealIds=[20,21,22];meals.find(m=>m.id===3).lastCooked='2026-10-20T12:00:00.000Z';
 const plan=mealPlans.find(p=>p.id===activePlanId);startWeekday='Tuesday';weekdayCategories={};weekdayMealOverrides={};plan.cycleSlotChoices={};plan.cycleRetainedSlots={};
 for(const [i,day]of orderedDays().entries()){const id=multi&&day==='Friday'?1:[1,2,3,4,30,31,32][i],key=weekdaySlotKey(day,'Weekend');weekdayCategories[day]=['Weekend'];weekdayMealOverrides[key]=String(id);plan.cycleSlotChoices[key]={mealId:String(id),substitution:true,parentId:''};plan.cycleRetainedSlots[key]=String(id)}saveWeekdayCategories();saveWeekdayMealOverrides();persist();renderList()},
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def card(p,cat='Weekend'):return p.locator('#list .master-category-card[data-category="'+cat+'"]')
def toggle(p,kind,cat='Weekend'):return card(p,cat).locator('[data-recipe-section="'+kind+'"]>.master-category-group-label')
def opened(p,kind,cat='Weekend'):return toggle(p,kind,cat).get_attribute('aria-expanded')=='true'
def count(p,kind,cat='Weekend'):return int(toggle(p,kind,cat).locator('.master-recipe-section-count').inner_text())
def setup(b,name,width,mode='multiple'):
 c,p,e,pr=f.setup(b,name,width,mode);p.evaluate('promotionTest.groups()')
 if pr:p.evaluate("localStorage.setItem('mealRotationGroupSectionExpansionV1','WORKING SECTIONS')")
 return c,p,e,pr
def check(c,p,e,pr):
 assert not e,e;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL' and p.evaluate("localStorage.getItem('mealRotationGroupSectionExpansionV1')")=='WORKING SECTIONS'
 c.close()
def preference_test(b,name,width):
 c,p,e,pr=setup(b,name,width);before=state(p);schedule=compose(p);groceries=f.sources(p)
 assert opened(p,'rotation') and not opened(p,'ideas');assert (count(p,'rotation'),count(p,'ideas'))==(4,2)
 assert card(p).locator('.master-category-meal[data-meal-id="5"]').is_hidden()
 assert toggle(p,'rotation').bounding_box()['height']==toggle(p,'ideas').bounding_box()['height']>=44
 for kind in ['rotation','ideas']:
  t=toggle(p,kind);assert t.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(242, 243, 241)';assert t.evaluate('(e)=>getComputedStyle(e).fontWeight')=='600';assert t.locator('svg').count()==1
 assert float(toggle(p,'ideas').evaluate('(e)=>getComputedStyle(e).marginTop').replace('px',''))>float(toggle(p,'rotation').evaluate('(e)=>getComputedStyle(e).marginTop').replace('px',''))
 toggle(p,'rotation').tap();toggle(p,'ideas').tap();assert not opened(p,'rotation') and opened(p,'ideas')
 # Parent groups preserve their existing independent open/close behavior.
 card(p).locator('.master-category-title').tap();assert not card(p).locator('.master-category-meals').count();card(p).locator('.master-category-title').tap();assert not opened(p,'rotation') and opened(p,'ideas')
 card(p,'Mains').locator('.master-category-title').tap();assert opened(p,'rotation','Mains') and not opened(p,'ideas','Mains');toggle(p,'ideas','Mains').tap()
 card(p).locator('.master-category-title').tap();assert not opened(p,'rotation') and opened(p,'ideas')
 p.evaluate('promotionTest.my()');p.evaluate('promotionTest.groups()');assert not opened(p,'rotation') and opened(p,'ideas') and opened(p,'ideas','Mains')
 # Keyboard activation uses the same entire-header button.
 toggle(p,'rotation').focus();p.keyboard.press('Enter');assert opened(p,'rotation');assert toggle(p,'rotation').evaluate('(e)=>e===document.activeElement')
 assert state(p)==before and compose(p)==schedule and f.sources(p)==groceries
 p.reload();p.evaluate('promotionTest.groups()');assert opened(p,'rotation') and opened(p,'ideas') and opened(p,'ideas','Mains')
 prefs=json.loads(p.evaluate('sectionUITest.backup()')['mealRotationGroupSectionExpansionV1']);assert prefs['groups']['Weekend']['ideas'] and prefs['groups']['Mains']['ideas']
 p.evaluate('promotionTest.validate()');backup=p.evaluate('sectionUITest.backup()');toggle(p,'ideas').tap();p.evaluate('sectionUITest.restore',backup);p.reload();p.evaluate('promotionTest.groups()');assert opened(p,'ideas')
 if name.startswith('meal-') and width==320:p.screenshot(path='/tmp/recipe-sections-mobile.png')
 check(c,p,e,pr);print('PASS',name,width,'heading styles/counts/44px targets; default states; independent sections/parents/groups; keyboard/navigation/reload/backups; exact schedule/data/grocery preservation',flush=True)
def moves_test(b,name,width):
 c,p,e,pr=setup(b,name,width);toggle(p,'rotation','Mains').tap();other=toggle(p,'rotation','Mains').get_attribute('aria-expanded');before=state(p)
 # Down reveals the destination, leaving its source and other groups unchanged.
 card(p).locator('[data-meal-id="1"] .recipe-section-move').tap();assert opened(p,'rotation') and opened(p,'ideas') and (count(p,'rotation'),count(p,'ideas'))==(3,3)
 assert toggle(p,'rotation','Mains').get_attribute('aria-expanded')==other
 toggle(p,'rotation').tap();card(p).locator('[data-meal-id="1"] .recipe-section-move').tap();assert opened(p,'rotation') and opened(p,'ideas') and (count(p,'rotation'),count(p,'ideas'))==(4,2)
 assert not p.get_by_role('dialog').count() and not p.get_by_role('alertdialog').count();assert toggle(p,'rotation','Mains').get_attribute('aria-expanded')==other
 prefs=p.evaluate('sectionUITest.backup()')['mealRotationGroupSectionExpansionV1'];raw=p.evaluate("promotionTest.order('Weekend')")
 for manual in [True,False,True]:
  p.evaluate('sectionUITest.manual',manual);assert p.evaluate('sectionUITest.backup()')['mealRotationGroupSectionExpansionV1']==prefs and p.evaluate("promotionTest.order('Weekend')")==raw
  assert card(p).locator('.move:visible').count()==(8 if manual else 0)
 row=card(p).locator('[data-meal-id="4"]');row.locator('.move').first.tap();assert p.evaluate("promotionTest.order('Weekend')")[0]==4
 assert all(next(x for x in state(p)['meals'] if x['id']==m['id']).get('lastCooked')==m.get('lastCooked') for m in before['meals'])
 check(c,p,e,pr);print('PASS',name,width,'arrow moves update counts, reveal only destination, keep source/other preferences; both ordering modes and reorder controls; no confirmations or date changes',flush=True)
def geometry(b,name,width,multi):
 snapshots=[]
 with tempfile.TemporaryDirectory() as tmp:
  Path(tmp,name).write_text(subprocess.check_output(['git','show','4069580db52c6641ca594fe13e949d8568acde65:'+name],cwd=ROOT,text=True))
  for base in [Path(tmp),ROOT]:
   f.ROOT=base;c,p,e,pr=setup(b,name,width);p.evaluate('sectionUITest.prepare',multi);p.evaluate('promotionTest.groups()');expand_recipe_sections(p)
   rows=card(p).locator('.master-category-meal').evaluate_all('''rows=>rows.map(row=>{const r=row.getBoundingClientRect(),s=getComputedStyle(row),info=row.querySelector('.master-meal-info'),badge=row.querySelector('.master-meal-weekdays'),arrow=row.querySelector('.recipe-section-move svg'),b=badge?.getBoundingClientRect(),a=arrow.getBoundingClientRect();let text=null;if(badge){const range=document.createRange();range.selectNodeContents(badge.querySelector('.master-weekday-token')||badge);text=range.getBoundingClientRect()}return {id:row.dataset.mealId,width:r.width,height:r.height,left:s.paddingLeft,right:s.paddingRight,top:s.paddingTop,bottom:s.paddingBottom,radius:s.borderRadius,color:s.backgroundColor,border:s.borderBottomWidth,nameX:info.getBoundingClientRect().left-r.left,days:badge?.textContent||'',badgeRight:b?r.right-b.right:null,textRight:text?r.right-text.right:null,arrowX:a.left-r.left,arrowGap:text?text.left-a.right:null,bodyScroll:info.scrollWidth<=info.clientWidth}})''')
   assert all(r['bodyScroll'] for r in rows);snapshots.append(rows)
   if base==ROOT:
    colored=[r for r in rows if r['days']];assert max(r['arrowX'] for r in colored)-min(r['arrowX'] for r in colored)<1
    assert max(r['badgeRight'] for r in colored)-min(r['badgeRight'] for r in colored)<1
    for r in colored:assert r['textRight']>=7
    if name.startswith('meal-') and width==320 and not multi:p.screenshot(path='/tmp/recipe-weekday-column-mobile.png')
   check(c,p,e,pr)
 f.ROOT=ROOT
 old={r['id']:r for r in snapshots[0]}
 for current in snapshots[1]:
  prior=old[current['id']]
  for key in ['width','left','right','top','bottom','radius','color','border','nameX','days','badgeRight']:assert prior[key]==current[key],(key,prior,current)
  assert abs(prior['height']-current['height'])<1,(prior,current)
  if not current['days']:assert prior['arrowX']==current['arrowX']
  elif not multi:assert current['arrowGap']>=prior['arrowGap']-1,(prior,current)
 print('PASS',name,width,'multi-day',multi,'fixed right-aligned badge/arrow columns; exact baseline row heights/padding/indentation/colors/radii/widths/dividers/name positions; unchanged unhighlighted arrows; long/linked/multiline names',flush=True)
def rename_preference(b,name):
 c,p,e,pr=setup(b,name,320);toggle(p,'rotation').tap();toggle(p,'ideas').tap();p.evaluate('sectionUITest.rename()');dialog=p.get_by_role('dialog');dialog.get_by_role('textbox').fill('Weekend renamed');dialog.get_by_role('button',name='Save',exact=True).tap();p.evaluate('promotionTest.groups()');assert not opened(p,'rotation','Weekend renamed') and opened(p,'ideas','Weekend renamed')
 p.get_by_role('button',name='Undo',exact=True).tap();p.evaluate('promotionTest.groups()');assert not opened(p,'rotation') and opened(p,'ideas');check(c,p,e,pr);print('PASS',name,'group rename/Undo retain independent section preferences',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   rename_preference(b,name)
   for w in [320,360]:
    preference_test(b,name,w);moves_test(b,name,w)
    for multi in [False,True]:geometry(b,name,w,multi)
  b.close()
