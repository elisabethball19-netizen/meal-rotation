"""Meal Groups heart visibility and reusable action-popup toggle, isolated mobile data."""
import copy
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from section_visibility_fixture import reveal_recipe
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.favoriteDisplayTest={
 seed:()=>{for(const m of meals)delete m.favorite;meals.find(m=>m.id===1).favorite=true;meals.find(m=>m.id===20).favorite=true;meals.find(m=>m.id===1).linkedMealIds=[20];persist()},
 long:()=>{meals.find(m=>m.id===1).name='Very long family-favorite garlic chicken recipe with roasted vegetables and jasmine rice';persist();renderList()},
 viewer:id=>openRecipeViewer(meals.find(m=>m.id===id)),
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def row(p,id):return p.locator('.master-category-meal[data-meal-id="'+str(id)+'"]')
def menu(p):return p.get_by_role('dialog',name='Meal options',exact=True)
def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'linked-slot');p.evaluate('favoriteDisplayTest.seed()');p.evaluate('promotionTest.groups()');reveal_recipe(p,20);before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 assert not p.locator('#list .recipe-favorite-toggle[aria-pressed="false"]').count();assert row(p,1).locator('.recipe-favorite-toggle').count()==1;assert row(p,1).locator('.recipe-favorite-toggle').get_attribute('aria-pressed')=='true';assert row(p,1).locator('.recipe-favorite-toggle svg').evaluate('(e)=>getComputedStyle(e).fill')!='none'
 assert not row(p,20).locator('.recipe-favorite-toggle').count() and not p.locator('.top-inline-linked .recipe-favorite-toggle').count()
 # Favorites toggle in the existing popup without dismissing it or changing other data.
 row(p,1).locator('.master-category-meal-name').first.tap();d=menu(p);heart=d.locator('.recipe-favorite-toggle');heart.tap();assert d.is_visible() and heart.get_attribute('aria-pressed')=='false' and not row(p,1).locator('.recipe-favorite-toggle').count();heart.tap();assert d.is_visible() and heart.get_attribute('aria-pressed')=='true' and row(p,1).locator('.recipe-favorite-toggle').count()==1;d.get_by_role('button',name='Close meal options',exact=True).tap()
 # The linked name opens its own popup; its favorite remains available only there/viewer.
 row(p,1).get_by_role('button',name='Current side',exact=True).tap();d=menu(p);assert 'Current side' in d.inner_text();heart=d.get_by_role('button',name='Remove from favorites: Current side',exact=True);heart.tap();assert d.is_visible();d.get_by_role('button',name='Add to favorites: Current side',exact=True).tap();assert d.is_visible() and not p.locator('#list .top-inline-linked .recipe-favorite-toggle').count();d.get_by_role('button',name='Close meal options',exact=True).tap()
 # Unflagged regular rows reserve no hidden heart element or icon space.
 assert not row(p,2).locator('.recipe-favorite-toggle').count();assert state(p)==before and compose(p)==schedule and f.sources(p)==groceries
 p.evaluate('favoriteDisplayTest.long()');row(p,1).locator('.master-category-meal-name').first.tap();d=menu(p);header=d.locator(':scope > div').first;rects=header.locator('.meal-options-heading-controls>button').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})');assert rects[0]['right']<=rects[1]['left'] and abs(rects[0]['top']-rects[1]['top'])<1;lines=header.locator(':scope > div').last.evaluate('(e)=>{const r=document.createRange();r.selectNodeContents(e);return [...r.getClientRects()].map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom}))}');assert all(line['right']<=rects[0]['left'] or line['top']>=rects[0]['bottom'] for line in lines);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path='/tmp/favorite-menu-'+name+'-'+str(width)+'.png');p.set_viewport_size({'width':740,'height':360});assert d.bounding_box()['height']<=324;d.get_by_role('button',name='Edit last cooked date',exact=True).scroll_into_view_if_needed();d.evaluate('(e)=>e.scrollTop=0');assert d.get_by_role('button',name='Close meal options',exact=True).is_visible();p.set_viewport_size({'width':width,'height':800});d.get_by_role('button',name='Close meal options',exact=True).tap()
 p.evaluate('favoriteDisplayTest.viewer(20)');heart=p.locator('.recipe-title-actions .recipe-favorite-toggle');assert heart.get_attribute('aria-pressed')=='true';heart.tap();assert heart.get_attribute('aria-pressed')=='false';heart.tap();assert heart.get_attribute('aria-pressed')=='true';p.get_by_role('button',name='Close recipe',exact=True).tap()
 expected=copy.deepcopy(state(p));backup=p.evaluate('favoriteDisplayTest.backup()');p.reload();assert state(p)==expected;p.evaluate('favoriteDisplayTest.viewer(20)');p.locator('.recipe-title-actions .recipe-favorite-toggle').tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('b=>favoriteDisplayTest.restore(b)',backup);p.reload();assert state(p)==expected and not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'no regular/linked hearts, filled main hearts, immediate popup toggle without close, linked recipe own popup/viewer control, long-heading layout, unchanged schedules/groceries/content, reload/backup/isolation',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:run(b,name,width)
  b.close()
