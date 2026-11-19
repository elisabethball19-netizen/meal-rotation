"""Final phone captures of touched screens, including complete action footers."""
from playwright.sync_api import sync_playwright
import followup126_browser as f126
import followup126_phone_browser as phone
base=phone.base
shot=base.base.shot
base.fixture.HOOK+="window.capture126={nextTasks:()=>{meals.find(m=>m.id===3).makeAheadTasks=[{id:'next',description:'Prepare the sauce and chopped vegetables for the family meal',daysBefore:1}];follow126.home(1)}};"
def run(browser,name):
 c,p,errors,prefix=base.setup(browser,name)
 p.evaluate('follow126.rules();follow126.overview()');shot(p,name,'overview-with-sides')
 p.evaluate('follow126.home()');card=p.locator('.plan-meal-card[data-meal-id="2"]');assert not card.locator('.shared-meal-actions').is_visible();shot(p,name,'current-collapsed');card.locator('.meal-actions-toggle').click();shot(p,name,'current-expanded');f126.open_sides(card);row=card.locator('.inline-side-row').first;row.get_by_role('button',name='Side actions',exact=False).click();card.get_by_role('button',name='Remove side',exact=True).scroll_into_view_if_needed();shot(p,name,'side-actions-footer');card.get_by_role('button',name='Add side',exact=True).click();picker=p.locator('.serving-add-dialog');picker.get_by_role('searchbox').fill('potatoes');shot(p,name,'side-picker');picker.get_by_role('button',name='Cancel',exact=True).click();p.wait_for_timeout(120);p.wait_for_timeout(200)
 p.evaluate('follow126.scale()');p.get_by_role('button',name='Scale Recipe',exact=True).click();menu=p.locator('#recipeScaleMenu');assert menu.locator('.preference-switch-thumb').count()==2;assert menu.evaluate('(m)=>m.scrollHeight<=m.clientHeight+1');shot(p,name,'scale-normal-two-switches');p.get_by_role('button',name='Cancel recipe scale',exact=True).click();p.evaluate('follow126.close()');p.wait_for_timeout(200)
 p.evaluate('phone126.sizes("extra");follow126.home()');card=p.locator('.plan-meal-card[data-meal-id="2"]');card.locator('.serving-sides-box').scroll_into_view_if_needed();shot(p,name,'current-large-actions');p.evaluate('phone126.sizes("normal");follow126.home(1)');card=p.locator('.preview-plan-card').first;card.locator('.meal-actions-toggle').click();shot(p,name,'next-parity')
 f126.open_sides(card);f126.add_simple(p,card,'Fresh herbs and a very long garnish name');card.get_by_role('button',name='Remove side',exact=True).scroll_into_view_if_needed();shot(p,name,'next-side-footer');p.wait_for_timeout(120);p.locator('#undo').click();p.wait_for_timeout(200)
 p.evaluate('capture126.nextTasks()');shot(p,name,'next-todo-spacing');p.evaluate('serving126.groups()');shot(p,name,'groups-last-cooked');p.get_by_role('button',name='Recipe actions for Chili-Garlic Broth Bowls',exact=True).click();shot(p,name,'groups-expanded-last-cooked');assert not errors,errors
 c.close();print('PASS',name,'follow126 final narrow-phone captures and complete side/picker/scale footers',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
