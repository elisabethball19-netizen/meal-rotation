"""Shared source-link editor: Save/Cancel and the existing viewer Back guard."""
import phone_corrections120_browser as t
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['index.html','meal-rotation-test.html']:
  c,p,errors,prefix=t.old.setup_followup(b,name);p.evaluate("active120.viewer('full')");before=p.evaluate('batch1.records()')
  def edit():
   p.get_by_role('button',name='Edit Recipe',exact=True).tap();d=p.get_by_role('dialog',name='Edit Recipe',exact=True);d.locator('.recipe-source-action').tap();return d
  d=edit();d.locator('input[type=url]').fill('https://example.org/viewer-cancel');d.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('batch1.records()')==before
  d=edit();d.locator('input[type=url]').fill('https://example.org/viewer-save');d.locator('input[type=url]').dispatch_event('input');assert d.get_by_role('button',name='Edit recipe link',exact=True).is_visible();p.wait_for_timeout(200);t.shot(p,name,'viewer-source-editor');d.get_by_role('button',name='Save recipe',exact=True).tap();assert next(m for m in p.evaluate('batch1.records()') if m['id']==72)['url']=='https://example.org/viewer-save'
  edit();p.go_back();p.wait_for_timeout(150);assert p.get_by_role('dialog',name='Edit Recipe',exact=True).is_visible();p.get_by_role('dialog',name='Edit Recipe',exact=True).get_by_role('button',name='Cancel',exact=True).tap();assert p.locator('#recipeViewer').is_visible();p.get_by_role('button',name='Close recipe',exact=True).tap()
  assert not errors,errors;c.close();print('PASS shared viewer source link Save/Cancel/Back',name,flush=True)
 b.close()
