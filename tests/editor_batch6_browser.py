"""Batch 6 card affordances, shared link picker and custom membership selection."""
from playwright.sync_api import sync_playwright
import editor_batch5_browser as base
f=base.f

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();batch5.seed()');p.locator('#list .master-category-meal[data-meal-id="537"]').evaluate('(e,c)=>e.style.backgroundColor=c','rgb(170, 190, 150)' if width==320 else 'rgb(190, 160, 170)');p.evaluate('batch5.open()');p.wait_for_timeout(850)
 card=p.locator('.meal-card-edit-mode');assert card.bounding_box()['height']<172;fields=card.locator('.meal-card-field-button');assert fields.count()==4
 assert fields.evaluate_all('(es)=>es.every(e=>getComputedStyle(e).borderTopStyle==="solid"&&getComputedStyle(e).boxShadow==="none")')
 assert fields.first.evaluate('(e)=>getComputedStyle(e).minHeight')=='32px'
 # Affordance tint responds to the existing card color; no normal-card style is changed.
 assert card.evaluate('(e)=>e.style.getPropertyValue("--meal-edit-field").includes(getComputedStyle(e).backgroundColor)');assert fields.first.evaluate('(e)=>getComputedStyle(e).backgroundColor') not in ['rgb(255, 255, 255)','rgba(0, 0, 0, 0)']
 p.get_by_role('button',name='Edit prep time',exact=True).click();p.locator('#prep').fill('');p.locator('#prep').press('Enter');assert p.get_by_role('button',name='Edit prep time',exact=True).inner_text()=='— prep'
 base.field(p,'total time','totaltime','60 min');base.field(p,'meal name','name','Batch six draft')
 assert card.locator('.meal-card-name-field input:not([hidden]),.meal-card-time-field input:not([hidden])').count()==0
 links=base.linked(p);assert links.locator(':scope>summary svg').count()==0;assert links.locator(':scope>summary').inner_text().endswith('Edit links')
 assert links.locator(':scope>summary').evaluate('(e)=>getComputedStyle(e).listStyleType')=='none'
 search=links.get_by_role('searchbox');search.fill('roast mississippi');assert links.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast').count()==1
 search.fill('');
 while links.locator('label:visible input:checked').count():links.locator('label:visible input:checked').first.click()
 assert links.locator(':scope>summary').inner_text()=='Add links'
 heading=links.locator('.meal-editor-group-heading').first;heading.click();links.locator(':scope>summary').click();p.wait_for_timeout(40);links.locator(':scope>summary').click();p.wait_for_timeout(40);assert not links.locator('.meal-editor-group-heading[aria-expanded=true]').count()
 # The backing select is retained only as the existing draft adapter; native UI never opens.
 picker=p.locator('.meal-group-picker-button').first;assert p.locator('#cat').is_hidden();original=picker.inner_text();picker.click();d=p.get_by_role('dialog',name='Select Meal Group',exact=True);assert d.is_visible();d.get_by_role('button',name='Cancel',exact=True).click();assert picker.inner_text()==original
 picker.click();d=p.get_by_role('dialog',name='Select Meal Group',exact=True);options=d.get_by_role('radio');values=options.evaluate_all('(es)=>es.filter(e=>e.value&&!e.disabled).map(e=>e.value)');target=next(x for x in values if x!=original);d.get_by_role('radio',name=target,exact=True).click();assert p.locator('.meal-group-picker-button').first.inner_text()==target
 p.locator('.meal-group-picker-button').first.click();p.get_by_role('dialog',name='Select Meal Group',exact=True).get_by_role('radio',name='No group',exact=True).click();assert p.locator('.meal-group-picker-button').first.inner_text()=='Choose group…';p.locator('.meal-group-picker-button').first.click();p.get_by_role('dialog',name='Select Meal Group',exact=True).get_by_role('radio',name=target,exact=True).click()
 p.get_by_role('button',name='Add group membership',exact=True).click();p.locator('.meal-group-picker-button').last.click();d=p.get_by_role('dialog',name='Select Meal Group',exact=True);assert d.get_by_role('radio',name=target,exact=True).is_disabled();d.get_by_role('radio',name=original,exact=True).click();assert p.locator('.meal-group-picker-button').all_inner_texts()==[target,original]
 # Repeat assignment changes: sibling choices remain disabled, current choice remains enabled.
 p.locator('.meal-group-picker-button').first.click();d=p.get_by_role('dialog',name='Select Meal Group',exact=True);assert d.get_by_role('radio',name=original,exact=True).is_disabled();assert not d.get_by_role('radio',name=target,exact=True).is_disabled();d.get_by_role('button',name='Cancel',exact=True).click()
 base.expand(p,'[data-editor-section=serve]');assert p.get_by_text('Choose which types of sides to automatically rotate in with this meal.',exact=True).is_visible();assert not p.get_by_text('Serve with suggestions',exact=True).count()
 serve=p.locator('[data-editor-section=serve]');suggestion=serve.locator('.meal-editor-suggestions button').first;text=suggestion.inner_text();suggestion.click();p.get_by_role('button',name='Remove Serve with '+text,exact=True).click();custom=serve.get_by_role('textbox',name='Custom Serve with suggestion');custom.fill('Fresh salad');custom.press('Enter');assert p.get_by_role('button',name='Remove Serve with Fresh salad',exact=True).count()==1;custom.fill('Fresh salad');custom.press('Enter');assert p.get_by_role('button',name='Remove Serve with Fresh salad',exact=True).count()==1
 base.expand(p,'[data-editor-section=notes]');base.expand(p,'#recipeMakeAhead');units=p.locator('.meal-editor-segmented').first;chosen=units.locator('[aria-pressed=true]');other=units.locator('[aria-pressed=false]');assert chosen.evaluate('(e)=>getComputedStyle(e).boxShadow')!='none';assert other.evaluate('(e)=>getComputedStyle(e).boxShadow')=='none';assert other.evaluate('(e)=>getComputedStyle(e).fontWeight')=='400';label=other.inner_text();other.click();assert units.locator('[aria-pressed=true]').inner_text()==label
 base.fit(p);p.locator('#cancel').click();assert p.evaluate('batch5.meal().name')!='Batch six draft';p.evaluate('batch5.open()');p.wait_for_timeout(700);assert p.locator('.meal-group-picker-button').first.inner_text()==original
 # Save multiple memberships and reopen/reload through the existing data path.
 p.get_by_role('button',name='Add group membership',exact=True).click();p.locator('.meal-group-picker-button').last.click();p.get_by_role('dialog',name='Select Meal Group',exact=True).get_by_role('radio',name=target,exact=True).click();p.locator('#save').click();p.reload();p.evaluate('combinedTest.viewport();promotionTest.groups();batch5.open()');p.wait_for_timeout(750);assert p.locator('.meal-group-picker-button').all_inner_texts()==[original,target]
 p.locator('.meal-group-picker-button').last.click();d=p.get_by_role('dialog',name='Select Meal Group',exact=True);assert d.get_by_role('radio',name=original,exact=True).is_disabled();assert d.locator('.meal-group-picker-options').evaluate('(e)=>getComputedStyle(e).overflowY')=='auto';d.press('Escape');p.locator('#cancel').click()
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'compact/tinted fields, empty times, shared links/reset/search, custom groups/duplicates/save/cancel/reload, Serve with wording, unit styling; no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
