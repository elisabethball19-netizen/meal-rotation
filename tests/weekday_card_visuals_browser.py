"""Synthetic mobile weekday card geometry, edge visibility and data preservation."""
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
fixture.HOOK+='''window.cardTest={setup:(tabs,kind)=>{showMealPlanTabs=tabs;startWeekday='Tuesday';meals.find(m=>m.id===1).linkedMealIds=kind==='linked'?[10,20]:[];if(kind==='long')meals.find(m=>m.id===1).name='A long recipe name that wraps naturally on a narrow mobile screen';weekdayCategories={Tuesday:kind==='multiple'?['Rice','Sides']:['Rice']};weekdayMealOverrides={};weekdayRecipeFilters={};render();window.scrollTo(0,0)}};'''
CSS='''/* Keep empty days at the single-meal minimum, without enlarging populated cards. */'''
END='''/* Single-action dialogs: close in the title row; multi-action footers stay unchanged. */'''
def geometry(p):
 return p.evaluate('''()=>{const h=document.querySelector('.weekday-heading'),head=document.querySelector('.rotation-compact-header'),b=h.getBoundingClientRect();let next=h.nextElementSibling,total=0;while(next&&!next.classList.contains('weekday-heading')){total+=next.getBoundingClientRect().height;next=next.nextElementSibling}const empty=document.querySelector('.empty-weekday-meal'),single=document.querySelector('.top-recipe-wrap');return {body:total,heading:b.height,gap:b.top-head.getBoundingClientRect().bottom,top:b.top,empty:empty.getBoundingClientRect().height,emptyPadding:getComputedStyle(empty).paddingTop,radius:getComputedStyle(h).borderRadius,color:getComputedStyle(h).backgroundColor,width:document.documentElement.scrollWidth,edge:[2,4,8].every(y=>document.elementFromPoint(b.x+b.width/2,b.top+y)===h),singleMin:getComputedStyle(single).minHeight}}''')
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for filename in ['index.html','meal-rotation-test.html']:
  for width in [320,360]:
   for tabs in [True,False]:
    for kind in ['single','multiple','linked','long']:
     ctx,p,errors,prefix=fixture.setup(browser,filename,width,multi=True)
     p.evaluate('([tabs,kind])=>cardTest.setup(tabs,kind)',[tabs,kind]);saved=p.evaluate('slotTest.storage()');new=geometry(p)
     assert new['empty']==40 and new['emptyPadding']=='3px',new
     assert new['gap']>=10 and new['edge'] and new['radius']=='8px 8px 0px 0px' and new['width']==width,new
     if kind=='single':assert new['body']==new['empty'],new
     # Compare the exact pre-change CSS: populated cards and colors must not change.
     css=p.locator('style').first.text_content();a=css.index(CSS);b=css.index(END,a)
     p.locator('style').first.evaluate('(e,s)=>e.textContent=s',css[:a]+css[b:]);old=geometry(p)
     assert new['body']==old['body'] and new['heading']==old['heading'] and new['radius']==old['radius'] and new['color']==old['color'],(new,old)
     assert old['empty']>new['empty'] and new['gap']>old['gap'],(new,old)
     p.locator('style').first.evaluate('(e,s)=>e.textContent=s',css)
     if filename.startswith('meal-') and width==360 and tabs and kind in ['single','multiple','linked']:
      p.screenshot(path='/tmp/weekday-cards-'+kind+'.png',full_page=True)
     # Heading and recipe actions remain separate after visual changes.
     p.locator('.weekday-heading').first.tap();p.get_by_role('button',name='Close',exact=True).tap()
     p.locator('.mealname').first.tap();p.get_by_role('button',name='Close meal options',exact=True).tap()
     p.evaluate('window.scrollTo(0,180)');p.wait_for_timeout(150)
     assert p.locator('.rotation-compact-header').evaluate('(e)=>Math.abs(e.getBoundingClientRect().top-(parseFloat(getComputedStyle(e).top)||0))<1')
     assert p.evaluate('slotTest.storage()')==saved
     assert not errors,errors
     print('PASS',filename,width,'tabs' if tabs else 'no tabs',kind,'empty=single minimum; populated geometry/colors/radii unchanged; first edge clear; sticky header/actions/storage; no JS errors',flush=True)
     ctx.close()
 browser.close()
