"""Four-page heading spacing, isolated data, mobile geometry and sticky checks."""
import json,copy
from playwright.sync_api import sync_playwright
import rotation_no_duplicates_browser as fixture
fixture.HOOK+='''window.headingTest={view:name=>{showTop=name!=='groups';groceryTabActive=name==='grocery';allMealsActive=name==='overview';render();window.scrollTo(0,0)},tabs:on=>{showMealPlanTabs=on;localStorage.setItem('mealRotationShowPlanTabsV1',String(on));render();window.scrollTo(0,0)},plan:id=>loadMealPlan(id),size:value=>{mealTextSize=value;applyMealTextSize()},custom:()=>{writeMasterGroupOrder([...cats].reverse(),false);renderList()},order:()=>masterGroupOrder};
if(!cats.includes('Extra group 0')){
 for(let i=0;i<18;i++)cats.push('Extra group '+i);
 const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');
 for(const meal of meals){meal.ingredients=Array.from({length:18},(_,i)=>(i+1)+' cups ingredient '+meal.id+' '+i);selected[meal.id]=meal.ingredients}
 localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));
 mealPlans[1].name='A very long meal plan name for narrow mobile screens';persist();saveActiveMealPlan();
}'''
VIEWS=['rotation','grocery','overview','groups']
SEL={'rotation':'.rotation-compact-header','grocery':'.grocery-compact-header','overview':'.all-meals-overview>h2','groups':'.master-categories-heading'}
METRICS='''view=>{
 const bounds=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,bottom:r.bottom,right:r.right,height:r.height,width:r.width}};
 const header=document.querySelector({rotation:'.rotation-compact-header',grocery:'.grocery-compact-header',overview:'.all-meals-overview>h2',groups:'.master-categories-heading'}[view]);
 const title=header.querySelector('h2')||header,range=document.createRange();range.selectNodeContents(title);
 const text=range.getBoundingClientRect(),anchor=document.querySelector('#list .meal-plan-tabs')||document.querySelector('#tabs .tab-actions');
 const controls=document.querySelector({rotation:'.rotation-heading-actions',grocery:'.master-grocery-plan-filters',overview:'.none',groups:'.master-expansion-controls'}[view]);
 const first=document.querySelector({rotation:'#list>.section',grocery:'.master-grocery-item',overview:'.all-meals-day',groups:'.master-categories .master-category-card'}[view]);
 return {header:bounds(header),title:bounds(title),controls:bounds(controls),first:bounds(first),anchor:bounds(anchor),textTop:text.top,textBottom:text.bottom,textGap:text.top-anchor.getBoundingClientRect().bottom,stuck:header.classList.contains('is-stuck'),position:getComputedStyle(header).position,bg:getComputedStyle(header).backgroundColor};
}'''

def view(p,v,long=False):
 p.evaluate('headingTest.view',v);p.wait_for_timeout(35)
 if long:
  p.locator(SEL[v]).evaluate("e=>{const title=e.querySelector('h2')||e;title.textContent='A longer page heading with additional words for mobile wrapping'}")
  if v=='grocery':p.locator('.grocery-choose-meals').evaluate("e=>e.textContent='Choose weekly meals'")
  if v=='rotation':p.locator('.rotation-button-label').evaluate_all("es=>{es[0].textContent='Cycle selected meals';es[1].textContent='Restore previous meals'}")
  p.wait_for_timeout(35)
 return p.evaluate(METRICS,v)

def check_geometry(p,v,m,width,long=False):
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),(v,width,'page overflow')
 assert m['header']['right']<=width-10 and m['header']['x']>=10,(v,width,m)
 assert abs(m['first']['y']-m['header']['bottom']-8)<1.1,(v,width,'content gap',m)
 if v=='rotation':
  assert abs(m['controls']['y']-m['title']['bottom']-8)<1,(v,width,'title-controls',m)
 elif v=='grocery' and m['controls']['y']>=m['title']['bottom']:
  assert abs(m['controls']['y']-m['title']['bottom']-8)<1,(v,width,'title-controls',m)
 if m['controls']:
  assert m['controls']['right']<=width-10,(v,width,'controls overflow',m)
  if v=='groups':assert m['title']['right']<=m['controls']['x']+1,(v,width,'inline controls overlap',m)
 for button in p.locator(SEL[v]).get_by_role('button').all():
  if button.is_visible():
   r=button.bounding_box();assert r['height']>=34 and r['width']>=32,(v,'control target shrunk',r)


def run(browser,filename,width,size='normal',long=False):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,'linked');p.evaluate('headingTest.size',size)
 original=p.evaluate('slotTest.state()');selection=p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1'];positions={}
 for tabs in [True,False]:
  p.evaluate('headingTest.tabs',tabs)
  for plan in ['original','lunch']:
   p.evaluate('headingTest.plan',plan)
   values={}
   for v in VIEWS:
    m=view(p,v,long);check_geometry(p,v,m,width,long);values[v]=m['textGap'];positions[tabs,plan,v]=m
    if filename=='index.html' and width==360 and size=='normal' and plan=='original':
     p.screenshot(path=f'/tmp/heading-{v}-tabs-{tabs}.png')
    # Native Android-style swipe, then a deterministic position for sticky measurements.
    cdp=ctx.new_cdp_session(p);x=100;y=650
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    for n in range(1,9):
     cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-280*n/8}]});p.wait_for_timeout(15)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(100)
    assert p.evaluate('window.scrollY')>0,(v,'native touch did not scroll')
    cdp.detach()
    # Meal Groups retains its non-sticky page heading.
    p.evaluate('window.scrollTo(0,260)');p.wait_for_timeout(100);scrolled=p.evaluate(METRICS,v)
    if v=='groups':assert scrolled['header']['y']<0 and scrolled['position']=='static'
    else:
     sticky_top=p.locator(SEL[v]).evaluate('(e)=>parseFloat(getComputedStyle(e).top)||0')
     assert abs(scrolled['header']['y']-sticky_top)<1 and scrolled['stuck'],(v,width,scrolled)
     assert scrolled['bg']=='rgb(255, 255, 255)'
     target=p.locator(SEL[v]);assert target.evaluate('(e)=>{let r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+5,r.y+5);return hit===e||e.contains(hit)}'),(v,'header hit/coverage')
    p.evaluate('window.scrollTo(0,0)');p.wait_for_timeout(60)
    assert not p.locator(SEL[v]).evaluate('(e)=>e.classList.contains("is-stuck")')
   assert max(values.values())-min(values.values())<1.1,(filename,width,size,long,tabs,plan,values)
 for plan in ['original','lunch']:
  for v in ['rotation','grocery','overview']:
   assert positions[True,plan,v]['textTop']>positions[False,plan,v]['textTop']+30,(v,'hidden tab space remained')
 # Sticky controls still operate: rotate menu, grocery source toggle, group expansion.
 p.evaluate('headingTest.plan','original');view(p,'rotation');p.get_by_role('button',name='Rotate Meals',exact=True).tap();p.get_by_role('dialog',name='Rotate out recipes').get_by_role('button',name='Close',exact=True).tap()
 view(p,'grocery');button=p.locator('.grocery-ingredient-name').first;button.tap();assert button.get_attribute('aria-expanded')=='true';button.tap();assert button.get_attribute('aria-expanded')=='false'
 view(p,'groups');p.get_by_role('button',name='Expand all groups',exact=True).tap();assert p.locator('.master-category-meals').count()>0;p.get_by_role('button',name='Collapse all groups',exact=True).tap()
 # A custom order shows the existing reset control between header and first card.
 p.evaluate('headingTest.custom()');m=p.evaluate(METRICS,'groups');reset=p.get_by_role('button',name='Reset to Weekday Order',exact=True).bounding_box()
 assert abs(reset['y']-m['header']['bottom']-8)<1.1 and abs(m['first']['y']-reset['y']-reset['height']-8)<1.1,(m,reset)
 p.get_by_role('button',name='Reset to Weekday Order',exact=True).tap();assert p.evaluate('headingTest.order()') is None
 p.evaluate('headingTest.plan','original');final=p.evaluate('slotTest.state()')
 for key in ['meals','sessions','scales','prefs']:assert final[key]==original[key],(filename,key,'data changed')
 assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==selection
 assert [plan['weekdayCategories'] for plan in final['plans']]==[plan['weekdayCategories'] for plan in original['plans']]
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,size,'long headings' if long else 'normal headings','four pages, tabs on/off, both plans, consistent gaps, scroll/sticky/controls/reset, data preservation; no JS errors',flush=True);ctx.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width,size,long in [(280,'normal',False),(320,'normal',False),(360,'normal',False),(390,'normal',False),(740,'normal',False),(320,'extra',False),(360,'extra',True)]:run(b,filename,width,size,long)
  b.close()

