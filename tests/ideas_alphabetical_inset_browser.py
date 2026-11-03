"""Text-only insets and display-only alphabetical Ideas ordering."""
import copy,json,tempfile,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
from section_visibility_fixture import expand_recipe_sections,reveal_recipe
ROOT=Path(__file__).resolve().parents[1]
f.EXTRA+='''window.ideasTest={
 layout:()=>{const base=JSON.parse(JSON.stringify(meals[0]));for(const [number,name]of [[7,'Unscheduled recipe'],[8,'A long unhighlighted recipe title with garden vegetables and fragrant rice']])meals.push({...JSON.parse(JSON.stringify(base)),id:number,name,linkedMealIds:[20,21]});meals.find(m=>m.id===1).name='Scheduled recipe';meals.find(m=>m.id===1).linkedMealIds=[20,21];meals.find(m=>m.id===2).name='A long highlighted recipe title with garden vegetables and fragrant rice';persist();renderList()},
 bulk:()=>{const base=JSON.parse(JSON.stringify(meals[0]));let next=1000;for(let i=399;i>=0;i--)meals.push({...JSON.parse(JSON.stringify(base)),id:next++,name:(i%2?'recipe ':'RECIPE ')+String(i).padStart(3,'0'),rotation:false,linkedMealIds:[]});for(const cat of cats)for(const name of ['zucchini stew','Apple salad','banana bread','apricot soup','APPLE salad'])meals.push({...JSON.parse(JSON.stringify(base)),id:next++,name,cat,rotation:false,linkedMealIds:[]});id=Math.max(...meals.map(m=>m.id))+1;persist();renderList()},
 manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 raw:()=>meals.map(m=>({id:m.id,name:m.name,cat:m.cat,rotation:m.rotation})),
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def card(p,cat='Weekend'):return p.locator('#list .master-category-card[data-category="'+cat+'"]')
def section(p,rot=False,cat='Weekend'):return card(p,cat).locator('[data-recipe-section="'+('rotation' if rot else 'ideas')+'"]')
def show(p):p.evaluate('promotionTest.groups()');expand_recipe_sections(p)
def names(p,cat='Weekend'):return section(p,cat=cat).locator('.master-category-meal-name').evaluate_all('(es)=>es.map(e=>e.textContent)')
def alphabetical(p):
 raw=p.evaluate('ideasTest.raw()')
 for cat in ['Weekend','Mains','Sides']:
  expected=sorted([m['name'] for m in raw if m['cat']==cat and not m['rotation']],key=str.casefold)
  assert names(p,cat)==expected,(cat,names(p,cat)[:12],expected[:12])
  assert int(section(p,cat=cat).locator('.master-recipe-section-count').inner_text())==len(expected)
def chooser(p):
 expected=card(p).locator('.master-category-meal').evaluate_all('(es)=>es.map(e=>e.dataset.mealId)');p.evaluate("promotionTest.chooser('Saturday','Weekend')");d=p.locator('.weekday-meal-picker');toggle=d.locator('[data-group=Weekend] .master-category-title')
 if toggle.get_attribute('aria-expanded')=='false':toggle.tap()
 assert d.locator('[data-group=Weekend] .weekday-meal-choice').evaluate_all('(es)=>es.map(e=>e.dataset.mealId)')==expected;d.get_by_role('button',name='Cancel',exact=True).tap()
def setup(b,name,w):
 c,p,e,pr=f.setup(b,name,w,'cross-group');p.evaluate('ideasTest.layout()');show(p);return c,p,e,pr
def check(c,p,e,pr):
 assert not e,e;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()
def layout(b,name,w,manual):
 results=[]
 with tempfile.TemporaryDirectory() as tmp:
  Path(tmp,name).write_text(subprocess.check_output(['git','show','29bc48c56fa07a231ac1f50131afe8584886c2b3:'+name],cwd=ROOT,text=True))
  for root in [Path(tmp),ROOT]:
   f.ROOT=root;c,p,e,pr=setup(b,name,w);p.evaluate('ideasTest.manual',manual);show(p)
   rows=card(p).locator('.master-category-meal').evaluate_all('''rows=>rows.map(row=>{const r=row.getBoundingClientRect(),s=getComputedStyle(row),info=row.querySelector('.master-meal-info'),name=info.querySelector('.master-category-meal-name'),a=row.querySelector('.recipe-section-move').getBoundingClientRect(),n=name.getBoundingClientRect(),ns=getComputedStyle(name);return {id:row.dataset.mealId,highlight:row.classList.contains('featured-top-meal'),width:r.width,h:r.height,left:s.paddingLeft,right:s.paddingRight,top:s.paddingTop,bottom:s.paddingBottom,color:s.backgroundColor,radius:s.borderRadius,border:s.borderBottomWidth,nameX:n.left-r.left,arrowX:a.left-r.left,font:ns.fontSize,line:ns.lineHeight,overflow:info.scrollWidth>info.clientWidth}})''')
   results.append({r['id']:r for r in rows});assert all(not r['overflow'] for r in rows)
   if root==ROOT:
    assert max(r['nameX'] for r in rows)-min(r['nameX'] for r in rows)<1
    if name.startswith('meal-') and w==320 and not manual:p.evaluate('window.scrollTo(0,0)');p.screenshot(path='/tmp/ideas-text-alignment-mobile.png')
   check(c,p,e,pr)
 f.ROOT=ROOT
 for id,row in results[1].items():
  old=results[0][id]
  for key in ['width','left','right','top','bottom','color','radius','border','arrowX','font','line']:assert row[key]==old[key],(key,old,row)
  assert abs(row['nameX']-old['nameX']-(0 if row['highlight'] else 13))<1
  if row['highlight']:assert row['h']==old['h']
 print('PASS',name,w,'manual',manual,'text aligns across highlighted/unhighlighted Rotation and Ideas; only unhighlighted text shifts 13px; arrows/dividers/highlight geometry/typography unchanged; long linked text fits',flush=True)
def sorting(b,name,w):
 c,p,e,pr=setup(b,name,w);p.evaluate('ideasTest.bulk()');show(p);before=state(p);schedule=compose(p);raw=p.evaluate('ideasTest.raw()');groceries=f.sources(p);alphabetical(p);chooser(p)
 assert len(names(p))>400
 for manual in [True,False,True,False]:
  p.evaluate('ideasTest.manual',manual);show(p);alphabetical(p);chooser(p);assert state(p)['meals']==before['meals'] and compose(p)==schedule and f.sources(p)==groceries and p.evaluate('ideasTest.raw()')==raw
  for field in ['sessions','scales','prefs']:assert state(p)[field]==before[field]
 # Exercise real editor rename/add paths, not only direct fixture updates.
 p.evaluate('promotionTest.editor(1000)');p.locator('#name').fill('aardvark renamed idea');p.locator('#save').tap();show(p);alphabetical(p);assert names(p)[0]=='aardvark renamed idea';assert [m['id'] for m in p.evaluate('ideasTest.raw()')]==[m['id'] for m in raw]
 card(p).get_by_role('button',name='Add meal to Weekend',exact=True).tap();p.locator('#name').fill('aa new idea');p.locator('#save').tap();show(p);alphabetical(p);assert names(p)[0]=='aa new idea';assert compose(p)==schedule;f.stable_sources(groceries,f.sources(p))
 # Down sorts the new Idea immediately; Up promotes normally and preserves section state.
 reveal_recipe(p,7).locator('.recipe-section-move').tap();alphabetical(p);assert 'Unscheduled recipe' in names(p)
 assert section(p,True).locator('>.master-category-group-label').get_attribute('aria-expanded')=='true'
 reveal_recipe(p,7).locator('.recipe-section-move').tap();alphabetical(p);assert 'Unscheduled recipe' not in names(p);assert sum(r['id']==7 for r in f.rows(p))==1;assert f.pick(p,'Wednesday','Mains')['id']==3
 chooser(p);after=compose(p);raw=p.evaluate('ideasTest.raw()');p.reload();show(p);alphabetical(p);assert compose(p)==after and p.evaluate('ideasTest.raw()')==raw
 p.evaluate('promotionTest.validate()');backup=p.evaluate('ideasTest.backup()');p.evaluate('ideasTest.restore',backup);p.reload();show(p);alphabetical(p);assert compose(p)==after and p.evaluate('ideasTest.raw()')==raw
 check(c,p,e,pr);print('PASS',name,w,'400+ mixed-case Ideas across groups; displayed alpha in both modes without raw-order/data/schedule changes; actual editor add/rename; immediate down/up; counts/preferences/chooser/reload/backups',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for w in [320,360]:
    for manual in [False,True]:layout(b,name,w,manual)
    sorting(b,name,w)
  b.close()
