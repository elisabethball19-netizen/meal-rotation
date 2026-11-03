"""Grouped weekday chooser and one-time cross-group choices, isolated synthetic data."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import rotation_no_duplicates_browser as fixture
from scheduled_linked_slots_browser import rows,state,compose,context_key,definitions
fixture.HOOK+='''window.chooserTest={open:(day='Saturday',cat='Mains')=>{const current=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat);openWeekdayMealChooser(day,cat,current?.meal)},search:()=>openMealSearch(),single:()=>{weekdayCategories.Saturday=['Mains'];saveWeekdayCategories();saveActiveMealPlan();renderList()},filter:()=>{weekdayRecipeFilters['Saturday::Mains']=['Approved'];meals.find(m=>m.id===1).labels=['Approved'];saveWeekdayRecipeFilters();persist()},many:()=>{for(let i=40;i<85;i++)meals.push({id:i,name:'Long recipe '+i+' with additional words to test narrow mobile wrapping',cat:'Mains',rotation:true,ingredients:[i+' cups rice'],instructions:'Cook rice.'});persist()},overview:()=>{allMealsActive=true;groceryTabActive=false;renderList()},my:()=>{allMealsActive=false;groceryTabActive=false;renderList()}};
if(!cats.includes('Other')){cats.push('Other','Empty');for(const [id,name,rotation]of [[30,'Café Garlic Lentil Bowl',false],[31,'Lemon Fish Stew',true],[32,'Another Lentil Soup',true]])meals.push({id,name,cat:'Other',rotation,url:'',ingredients:[id+' cups rice'],instructions:'Cook rice.',notes:'Keep handwritten notes',lastCooked:'2025-01-01T12:00:00.000Z',linkedMealIds:id===30?[12]:[]});
const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const m of meals)if([30,31,32].includes(m.id))selections[m.id]=m.ingredients;localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));writeMasterGroupOrder(['Other','Empty','Sides','Mains'],false);persist();}'''

def open_picker(p):
 p.evaluate('chooserTest.open()');return p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)
def select(d,id):d.locator(f'.weekday-meal-choice[data-meal-id="{id}"]').tap()
def recipe(p,day='Saturday',cat='Mains',plan='original'):return next(r for r in rows(p) if r['day']==day and r['cat']==cat and r['planId']==plan)
def source_order(p,cat):return [m['id'] for m in state(p)['meals'] if m['cat']==cat]
def outside(d):d.get_by_role('button',name='Other (3 recipes)',exact=True).tap()
def search(d,q):
 if not d.get_by_role('searchbox',name='Search recipes').is_visible():d.get_by_role('button',name='Search recipes').tap()
 d.get_by_role('searchbox',name='Search recipes').fill(q)

def run(browser,filename,width):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,'linked');base=state(p);schedule=compose(p);storage=p.evaluate('slotTest.storage()');d=open_picker(p)
 assert d.get_by_role('button',name='Sort meals').count()==0
 groups=d.locator('[data-group]');assert groups.evaluate_all('(es)=>es.map(e=>e.dataset.group)')==['Mains','Sides','Other','Empty']
 for group in ['Mains','Sides']:
  assert d.locator(f'[data-group="{group}"] [aria-expanded=true]').count()==1
 assert d.locator('[data-group=Other] [aria-expanded=false]').count()==1
 assert d.locator('[data-group=Empty] [aria-expanded=false]').count()==1
 assert d.locator('.weekday-meal-choice[aria-pressed=true]').get_attribute('data-meal-id')=='1'
 assert d.locator('.weekday-choice-cooked').count()>0
 assert d.get_by_role('button',name='Mains (2 recipes)').is_visible()
 outside(d);assert d.locator('[data-meal-id="30"]').is_visible()
 select(d,30);assert recipe(p)['id']==1 and p.evaluate('slotTest.storage()')==storage
 # Search includes collapsed groups, any word order, accents and singular forms.
 outside(d);search(d,'lentil garlic cafe');matches=d.locator('.weekday-meal-choice');assert matches.count()==1 and matches.get_attribute('data-meal-id')=='30'
 assert 'Other' in matches.inner_text()
 search(d,'not found anywhere');assert d.get_by_text('No matching meals.').is_visible()
 search(d,'');assert d.locator('[data-group=Other] [aria-expanded=false]').count()==1
 assert groups.evaluate_all('(es)=>es.map(e=>e.dataset.group)')==['Mains','Sides','Other','Empty']
 d.get_by_role('button',name='Cancel',exact=True).tap();assert compose(p)==schedule and p.evaluate('slotTest.storage()')==storage
 # Standard shared search preserves its ordered/unordered matching semantics too.
 p.evaluate('chooserTest.search()');sd=p.get_by_role('dialog',name='Search meals',exact=True);sd.get_by_role('searchbox').fill('garlic cafe')
 assert 'Café Garlic Lentil Bowl' in sd.inner_text();sd.get_by_role('checkbox').check();assert 'No matching meals.' in sd.inner_text();sd.get_by_role('button',name='Close',exact=True).tap()
 # Assigned-group selection retains linked-side priority and definitions.
 d=open_picker(p);select(d,2);d.get_by_role('button',name='Save',exact=True).tap()
 assert recipe(p)['id']==2 and recipe(p,cat='Sides')['id']==12
 assert definitions(state(p))==definitions(base),[(x,y) for x,y in zip(definitions(base),definitions(state(p))) if x!=y]
 assert recipe(p,day='Sunday',cat='Sides')['id']==11
 assert [(x['day'],x['id']) for x in rows(p) if x['planId']=='lunch']==[(x[1],x[3]) for x in schedule if x[0]=='lunch']
 # A saved outside-group idea keeps its source group and Ideas status.
 p.reload();before=state(p);d=open_picker(p);outside(d);select(d,30);d.get_by_role('button',name='Save',exact=True).tap()
 assert recipe(p)['id']==30 and recipe(p)['cat']=='Mains'
 assert next(m for m in state(p)['meals'] if m['id']==30)['rotation'] is False
 assert next(m for m in state(p)['meals'] if m['id']==30)['cat']=='Other'
 assert [x['weekdayCategories'] for x in state(p)['plans']]==[x['weekdayCategories'] for x in base['plans']]
 assert definitions(state(p))==definitions(base),[(x,y) for x,y in zip(definitions(base),definitions(state(p))) if x!=y]
 assert source_order(p,'Other')==[30,31,32]
 assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==storage['mealRotationSelectedIngredientsV1']
 for r in rows(p):
  if r['planId']=='lunch' or (r['day']=='Sunday'):
   key=context_key(r);assert state(p)['sessions']['occurrences'][key]==base['sessions']['occurrences'][key]
   assert state(p)['scales']['occurrences'][key]==base['scales']['occurrences'][key]
 total=p.evaluate('slotTest.groceries()');expected=sum(r['id']*state(p)['scales']['occurrences'].get(context_key(r),{}).get('multiplier',1) for r in rows(p))
 assert len(total)==1 and abs(total[0]['quantity']['lo']-expected)<1e-8,(total,expected,rows(p))
 saved=p.evaluate('slotTest.storage()');p.reload();assert recipe(p)['id']==30
 p.evaluate('chooserTest.overview()');assert 'Café Garlic Lentil Bowl' in p.locator('#list').inner_text();p.evaluate('chooserTest.my()')
 d=open_picker(p);assert d.locator('.weekday-meal-choice[aria-pressed=true]').count()==0 # Other starts collapsed.
 outside(d);assert d.locator('[data-meal-id="30"]').get_attribute('aria-pressed')=='true';d.get_by_role('button',name='Cancel',exact=True).tap()
 # Backup roundtrip accepts the optional per-slot flag without schema changes.
 backup={**json.loads(saved['mealRotationDataV1']),'version':2,'storage':saved};p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert recipe(p)['id']==30
 p.evaluate('slotTest.cycle(["Sunday::Sides"])');assert recipe(p)['id']==30
 p.evaluate('slotTest.back()');assert recipe(p)['id']==30
 p.evaluate('slotTest.cycle(["Saturday::Mains"])');assert recipe(p)['id'] in [1,2] and recipe(p)['id']!=30
 assert source_order(p,'Other')==[30,31,32]
 p.evaluate('slotTest.back()');assert recipe(p)['id']==30
 p.evaluate('slotTest.cycle(["Saturday::Mains"])');p.evaluate('slotTest.partial(["original||Saturday::Mains"])');assert recipe(p)['id']==30
 assert source_order(p,'Other')==[30,31,32]
 # A rotating recipe from another group also remains there, without queue promotion.
 d=open_picker(p);outside(d);select(d,31);d.get_by_role('button',name='Save',exact=True).tap();assert recipe(p)['id']==31
 p.evaluate('slotTest.cycle(["Saturday::Mains"])');assert recipe(p)['id'] in [1,2] and source_order(p,'Other')==[30,31,32]
 # Long contents scroll within the list, leaving heading and footer fixed.
 p.evaluate('chooserTest.many()');d=open_picker(p);lst=d.locator('.weekday-meal-picker-list');assert lst.evaluate('(e)=>e.scrollHeight>e.clientHeight')
 header=d.get_by_role('heading').bounding_box();footer=d.get_by_role('button',name='Save',exact=True).bounding_box()
 assert footer['height']>=44 and d.get_by_role('button',name='Search recipes').bounding_box()['width']>=44
 box=d.bounding_box();assert box['x']>=15 and box['x']+box['width']<=width-15
 assert d.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 r=lst.bounding_box();x=r['x']+r['width']*.7;y=r['y']+r['height']*.8;cdp=ctx.new_cdp_session(p)
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
 for n in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-r['height']*.6*n/8}]});p.wait_for_timeout(20)
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(250);assert lst.evaluate('(e)=>e.scrollTop')>0
 assert abs(d.get_by_role('heading').bounding_box()['y']-header['y'])<1
 assert abs(d.get_by_role('button',name='Save',exact=True).bounding_box()['y']-footer['y'])<1
 if filename=='index.html':p.screenshot(path=f'/tmp/grouped-chooser-{width}.png')
 d.get_by_role('button',name='Cancel',exact=True).tap();assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 print('PASS',filename,width,'groups/search/order/cancel, assigned/outside/Ideas picks, links/groceries/progress/settings, backups/rotation/full+partial back, source queues, native touch layout; no JS errors',flush=True);ctx.close()

def single_and_filtered(browser,filename):
 ctx,p,errors,prefix=fixture.setup(browser,filename,320,'linked');p.evaluate('chooserTest.single()');base=state(p);original=source_order(p,'Sides');d=open_picker(p)
 assert d.get_by_role('heading').inner_text()=="Choose Saturday's meal"
 assert d.locator('[data-group]').evaluate_all('(es)=>es.map(e=>e.dataset.group)')==['Mains','Other','Empty','Sides']
 assert d.locator('[data-group=Sides] [aria-expanded=false]').count()==1
 d.get_by_role('button',name='Sides (4 recipes)',exact=True).tap();select(d,12);d.get_by_role('button',name='Save',exact=True).tap()
 assert recipe(p)['id']==12 and source_order(p,'Sides')==original
 p.evaluate('slotTest.cycle(["Saturday::Mains"])');assert recipe(p)['id'] in [1,2] and source_order(p,'Sides')==original
 p.evaluate('chooserTest.filter()');assignments=copy.deepcopy(state(p)['plans'][0]['weekdayCategories']);d=open_picker(p);assert d.locator('[data-meal-id="2"]').count()==1
 select(d,2);d.get_by_role('button',name='Save',exact=True).tap();assert recipe(p)['id']==2
 p.evaluate('slotTest.cycle(["Saturday::Mains"])');assert recipe(p)['id']==1
 assert state(p)['plans'][0]['weekdayCategories']==assignments
 p.evaluate('chooserTest.many()');d=open_picker(p);search(d,'long recipe');select(d,45)
 # Simulate reduced keyboard space and landscape while preserving the pending choice.
 for w,h in [(320,380),(740,360),(320,800)]:
  p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(100)
  box=d.bounding_box();save=d.get_by_role('button',name='Save',exact=True).bounding_box()
  assert box['y']>=0 and box['y']+box['height']<=h and save['y']+save['height']<=h
  assert d.locator('[data-meal-id="45"]').get_attribute('aria-pressed')=='true'
 d.get_by_role('button',name='Cancel',exact=True).tap();assert recipe(p)['id']==1
 assert not errors,errors
 print('PASS',filename,'single group, source queue preservation, filtered manual pick and automatic return, reduced keyboard viewport and orientation changes',flush=True);ctx.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for f in ['index.html','meal-rotation-test.html']:
   for width in [280,320,360,390]:run(b,f,width)
   single_and_filtered(b,f)
  b.close()
