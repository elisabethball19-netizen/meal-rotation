"""Compare compact weekday cards against the actual pre-tap-target revision."""
from pathlib import Path
import subprocess,tempfile
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
fixture.HOOK+='''window.cardTest={setup:(tabs,kind)=>{showMealPlanTabs=tabs;timeDisplayPrefs.top={prep:true,cook:true,total:true,marinate:true};startWeekday='Tuesday';meals.find(m=>m.id===1).linkedMealIds=kind==='linked'?[10,20]:[];meals.find(m=>m.id===1).prep=kind==='times'?'15 minutes':'';meals.find(m=>m.id===1).marinate=kind==='times'?'120':'';if(kind==='long')meals.find(m=>m.id===1).name='A long recipe name that wraps naturally on a narrow mobile screen';weekdayCategories={Tuesday:kind==='multiple'?['Rice','Sides']:['Rice']};weekdayMealOverrides={};weekdayRecipeFilters={};render();window.scrollTo(0,0)}};'''
def geometry(p):
 return p.evaluate('''()=>{const h=document.querySelector('#list > .section'),head=document.querySelector('.rotation-compact-header'),b=h.getBoundingClientRect();let next=h.nextElementSibling,total=0;while(next&&!next.classList.contains('section')){total+=next.getBoundingClientRect().height;next=next.nextElementSibling}return {body:total,heading:b.height,gap:b.top-head.getBoundingClientRect().bottom,radius:getComputedStyle(h).borderRadius,color:getComputedStyle(h).backgroundColor,width:document.documentElement.scrollWidth,edge:[2,4,8].every(y=>document.elementFromPoint(b.x+b.width/2,b.top+y)===h)}}''')
def run():
 root=fixture.ROOT
 with tempfile.TemporaryDirectory() as tmp,sync_playwright() as pw:
  for name in ['index.html','meal-rotation-test.html']:
   Path(tmp,name).write_bytes(subprocess.check_output(['git','show','f8468d1:'+name],cwd=root))
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:
     for kind in ['single','multiple','linked','times','long']:
      fixture.ROOT=Path(tmp);c0,p0,e0,_=fixture.setup(browser,filename,width,multi=True);p0.evaluate('([tabs,kind])=>cardTest.setup(tabs,kind)',[tabs,kind]);old=geometry(p0);c0.close()
      fixture.ROOT=root;ctx,p,errors,_=fixture.setup(browser,filename,width,multi=True);p.evaluate('([tabs,kind])=>cardTest.setup(tabs,kind)',[tabs,kind]);saved=p.evaluate('slotTest.storage()');new=geometry(p)
      assert new['body']==old['body'] and new['heading']==old['heading'],(filename,width,kind,new,old)
      assert new['radius']==old['radius'] and new['color']==old['color'] and new['width']==width and new['gap']>=10 and new['edge'],new
      assert new['heading']<30,new
      if filename.startswith('meal-') and width==360 and tabs:p.screenshot(path='/tmp/compact-cards-'+kind+'.png',full_page=True)
      p.locator('.weekday-heading').first.tap();p.get_by_role('button',name='Close',exact=True).tap();p.locator('.mealname').first.tap();p.get_by_role('button',name='Close meal options',exact=True).tap()
      p.evaluate('''()=>{const spacer=document.createElement('div');spacer.style.height='600px';document.body.append(spacer);window.scrollTo(0,220)}''');p.wait_for_timeout(100)
      assert p.locator('.rotation-compact-header').evaluate('(e)=>Math.abs(e.getBoundingClientRect().top-(parseFloat(getComputedStyle(e).top)||0))<1')
      assert p.evaluate('slotTest.storage()')==saved and not errors,(errors,new)
      print('PASS',filename,width,tabs,kind,'exact original compact populated heights, colors/radii, clear top edge, sticky header, separate actions and storage',flush=True);ctx.close()
  browser.close();fixture.ROOT=root
if __name__=='__main__':run()
