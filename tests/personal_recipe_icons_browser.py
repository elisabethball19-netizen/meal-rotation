"""Long mobile rows keep timer, make-ahead, favorite and adjusting actions separate."""
from playwright.sync_api import sync_playwright
import prep_skip_favorites_integration_browser as i
f=i.f
f.EXTRA+='''window.personalIconTest={seed:()=>{integratedTest.seed();const m=meals.find(m=>m.id===1);m.name='Puerto Rican Garlic-Citrus Roast Chicken with Extra Vegetables';m.prep='15';m.total='60';m.marinate='120';m.linkedMealIds=[20];persist();renderList()},stop:cancelCookingTimer};'''
def run(b,name):
 c,p,errors,_=f.setup(b,name,320,'linked-slot');p.evaluate('personalIconTest.seed()');p.evaluate('promotionTest.my()');title='Puerto Rican Garlic-Citrus Roast Chicken with Extra Vegetables'
 p.evaluate('favoriteTest.viewer(1)');p.locator('#recipeViewer .recipe-step-timer').first.tap();p.get_by_role('button',name='Pause timer',exact=True).tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('promotionTest.my()')
 for w,h in [(320,800),(740,360)]:
  p.set_viewport_size({'width':w,'height':h});p.evaluate('promotionTest.my()');assert p.get_by_role('button',name='Make ahead: '+title,exact=True).is_visible();assert p.get_by_role('button',name='Paused timer: '+title,exact=True).is_visible();assert p.get_by_role('button',name='Remove from favorites: '+title,exact=True).is_visible()
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path='/tmp/personal-icons-'+name+'-'+str(w)+'.png')
  p.evaluate('promotionTest.groups()');assert p.get_by_role('button',name='Remove from favorites: '+title,exact=True).is_visible();assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.screenshot(path='/tmp/personal-icons-groups-'+name+'-'+str(w)+'.png')
 p.evaluate('promotionTest.my()');p.get_by_role('button',name='Remove from favorites: '+title,exact=True).tap();assert not p.get_by_role('dialog').count() and not p.locator('#recipeViewer').count()
 p.get_by_role('button',name='Paused timer: '+title,exact=True).tap();p.get_by_role('button',name='Delete timer',exact=True).tap();assert not p.locator('.recipe-list-timer').count();assert p.get_by_role('button',name='Add to favorites: '+title,exact=True).is_visible();assert p.get_by_role('button',name='Make ahead: '+title,exact=True).is_visible()
 p.get_by_role('button',name='Make ahead: '+title,exact=True).tap();assert p.get_by_role('dialog',name='Make ahead: '+title,exact=True).is_visible() and not p.locator('#recipeViewer').count();p.get_by_role('button',name='Close make ahead',exact=True).tap()
 assert not errors,errors
 print('PASS',name,'320px portrait/740px landscape long names, time metadata, linked descriptions; timer/favorite/prep/adjusting coexist without overflow, cancellation retains personal icons and taps stay separate',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
