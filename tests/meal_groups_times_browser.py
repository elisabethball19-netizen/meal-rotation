"""Existing time settings/formatters in Meal Groups, using isolated mobile data."""
import json,subprocess,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from section_visibility_fixture import expand_recipe_sections
from scheduled_linked_slots_browser import state,compose
ROOT=Path(__file__).resolve().parents[1]
f.EXTRA+='''window.groupTimeTest={
 seed:()=>{const base=JSON.parse(JSON.stringify(meals[0]));meals.push({...JSON.parse(JSON.stringify(base)),id:7,name:'Zero prep and total with a recorded marinade',rotation:false,linkedMealIds:[]},{...JSON.parse(JSON.stringify(base)),id:8,name:'A long unhighlighted recipe name with several lines of metadata and ingredients',linkedMealIds:[]});
 const values={1:{prep:15,cook:30,total:45,marinate:'1-2 hours'},2:{prep:'',cook:90,total:'',marinate:'30 min'},3:{prep:10,cook:20,marinate:'24-48 hours'},4:{},5:{prep:'',cook:'',total:'',marinate:'2 hours'},6:{prep:'bad',cook:null,total:null,marinate:'invalid'},7:{prep:0,cook:0,total:0,marinate:'00:30'},8:{prep:20,cook:30,total:75,marinate:''}};
 for(const [id,fields]of Object.entries(values)){const meal=meals.find(m=>String(m.id)===id);for(const key of ['prep','cook','total','marinate'])delete meal[key];Object.assign(meal,fields)}
 meals.find(m=>m.id===1).name='Long highlighted recipe name with fragrant vegetables and garlic jasmine rice';meals.find(m=>m.id===1).lastCooked='2026-10-20T12:00:00.000Z';meals.find(m=>m.id===1).linkedMealIds=[20,21];meals.find(m=>m.id===3).lastCooked='2026-10-19T12:00:00.000Z';meals.find(m=>m.id===3).linkedMealIds=[20,21];
 timeDisplayPrefs={top:{cooking:true,marinate:true},category:{cooking:false,marinate:false},all:{cooking:false,marinate:false}};saveTimeDisplayPrefs();persist();renderList()},
 manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 prefs:()=>timeDisplayPrefs,
 top:()=>{const old=showTop,all=allMealsActive;showTop=true;allMealsActive=false;try{return Object.fromEntries(meals.filter(m=>[1,2,3,4,5,6,7,8].includes(m.id)).map(m=>[m.id,mealTimeDescription(m)]))}finally{showTop=old;allMealsActive=all}},
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
COOK={1:'15m prep · 45m total',2:'1h 30m total',3:'10m prep · 30m total',4:'',5:'',6:'',7:'0m prep · 0m total',8:'20m prep · 1h 15m total'}
MARINATE={1:'1h–2h marinate',2:'30m marinate',3:'24h–48h marinate',4:'',5:'2h marinate',6:'',7:'30m marinate',8:''}
def show(p):p.evaluate('promotionTest.groups()');expand_recipe_sections(p)
def setup(b,name,w):
 c,p,e,pr=f.setup(b,name,w,'already-scheduled');p.evaluate('groupTimeTest.seed()');show(p);return c,p,e,pr
def times(p):return p.locator('#list .master-category-meal').evaluate_all('(rows)=>Object.fromEntries(rows.map(row=>[row.dataset.mealId,row.querySelector(".times")?.textContent||" "]))')
def assert_times(p,cooking,marinate):
 actual=times(p)
 for id in COOK:
  expected=' · '.join(x for x in [COOK[id] if cooking else '',MARINATE[id] if marinate else ''] if x)
  assert actual[str(id)].strip()==expected,(id,cooking,marinate,actual[str(id)],expected)
  row=p.locator('#list .master-category-meal[data-meal-id="'+str(id)+'"]');assert row.locator('.times').count()==bool(expected)
 assert p.locator('#list .times').evaluate_all('(es)=>es.every(e=>!e.textContent.includes("—")&&!e.textContent.includes("undefined")&&!e.textContent.includes("NaN"))')
def settings(p,cooking,marinate,save=True):
 p.get_by_role('button',name='Settings and backups',exact=True).tap();p.locator('details[data-settings-group=display]').evaluate('(e)=>e.open=true')
 for label,value in [('Show cooking times',cooking),('Show marinade time',marinate)]:p.get_by_role('checkbox',name=label,exact=True).set_checked(value)
 # Changes must be visible immediately, before settings Save.
 assert_times(p,cooking,marinate)
 p.get_by_role('button',name='Save settings' if save else 'Cancel settings',exact=True).tap();show(p)
def check(c,p,e,pr):
 assert not e,e;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()
def run(b,name,w,manual):
 c,p,e,pr=setup(b,name,w);p.evaluate('groupTimeTest.manual',manual);show(p);before=state(p);schedule=compose(p);groceries=f.sources(p);top=p.evaluate('groupTimeTest.top()');assert_times(p,False,False)
 prefs=p.evaluate('groupTimeTest.prefs()');assert prefs['top']=={'cooking':True,'marinate':True} and prefs['category']=={'cooking':False,'marinate':False}
 for cook,marinate in [(True,False),(False,True),(True,True),(False,False),(True,True)]:
  settings(p,cook,marinate);assert_times(p,cook,marinate);assert state(p)==before and compose(p)==schedule and f.sources(p)==groceries and p.evaluate('groupTimeTest.top()')==top
 settings(p,False,False,False);assert_times(p,True,True)
 p.locator('#list .master-category-card[data-category=Weekend] [data-recipe-section=ideas]>.master-category-group-label').tap();p.locator('#list .master-category-card[data-category=Weekend] [data-recipe-section=ideas]>.master-category-group-label').tap();assert_times(p,True,True)
 rows=p.locator('#list .master-category-meal:visible').evaluate_all('''rows=>rows.map(row=>{const info=row.querySelector('.master-meal-info'),name=info.querySelector('.shared-meal-name-line'),n=name.getBoundingClientRect(),r=row.getBoundingClientRect();const meta=[...info.querySelectorAll(':scope>.times,:scope>.meal-last-cooked,:scope>.top-inline-linked')];return {id:row.dataset.mealId,aligned:meta.every(e=>Math.abs(e.getBoundingClientRect().left-n.left)<1),overflow:info.scrollWidth>info.clientWidth,order:[...info.children].map(e=>e.className),color:getComputedStyle(row).backgroundColor,arrow:!!row.querySelector('.recipe-section-move'),count:row.querySelectorAll('.times').length,font:row.querySelector('.times')?getComputedStyle(row.querySelector('.times')).fontSize:null,small:row.querySelector('.times')?parseFloat(getComputedStyle(row.querySelector('.times')).fontSize)<parseFloat(getComputedStyle(name.querySelector('button')).fontSize):true}})''')
 assert all(r['aligned'] and not r['overflow'] and r['arrow'] and r['count']<=1 and r['small'] for r in rows),rows
 for row in rows:
  if row['count']:assert row['order'][1]=='times' and (not any('meal-last-cooked'==x for x in row['order']) or row['order'].index('times')<row['order'].index('meal-last-cooked'))
 assert p.locator('#list .times').first.evaluate('(e)=>getComputedStyle(e).color')=='rgb(119, 119, 119)'
 p.reload();show(p);assert_times(p,True,True);assert p.evaluate('groupTimeTest.prefs()')['top']==prefs['top'];assert compose(p)==schedule
 p.evaluate('promotionTest.validate()');backup=p.evaluate('groupTimeTest.backup()');p.evaluate('groupTimeTest.restore',backup);p.reload();show(p);assert_times(p,True,True);assert compose(p)==schedule
 if name.startswith('meal-') and w==320:
  target=p.locator('#list .master-category-card[data-category=Weekend]');y=target.bounding_box()['y']+p.evaluate('scrollY')-140;p.evaluate('(y)=>window.scrollTo(0,y)',y);p.screenshot(path='/tmp/meal-group-times-'+str(manual)+'.png')
 check(c,p,e,pr);print('PASS',name,w,'manual',manual,'all cooking/marinade combinations, actual settings Save/Cancel and persistence, valid/empty/invalid/zero/derived values, both sections/highlights, aligned multiline metadata, unchanged data/schedule/groceries/top output',flush=True)
def top_compatibility(b,name):
 with tempfile.TemporaryDirectory() as tmp:
  Path(tmp,name).write_text(subprocess.check_output(['git','show','bb73c048302f3ecbca6dbb0d526b1f0927b5065f:'+name],cwd=ROOT,text=True));values=[]
  for source in [Path(tmp),ROOT]:
   f.ROOT=source;c,p,e,pr=setup(b,name,320);values.append(p.evaluate('groupTimeTest.top()'));check(c,p,e,pr)
  f.ROOT=ROOT;assert values[0]==values[1]
 print('PASS',name,'My Rotation default formatter matches previous app exactly, including partial/missing legacy fields',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   top_compatibility(b,name)
   for w in [320,360]:
    for manual in [False,True]:run(b,name,w,manual)
  b.close()
