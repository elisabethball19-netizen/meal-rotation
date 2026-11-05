"""Relevant existing workflow cases, independently of obsolete historical probes.

The full legacy suites and their baseline failures are reported separately.
This runner does not claim coverage of their inactive-filter fixtures, obsolete
repair hook, or unavailable pre-Favorites Git comparison.
"""
from playwright.sync_api import sync_playwright
import manual_duplicate_meal_browser as duplicate
import prep_skip_favorites_integration_browser as integration
import recipe_import_audit_browser as imports

if __name__ == '__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for mode in ['standard','linked']:
    for choice in ['yes','no','cancel']:
     duplicate.run(browser,name,360,mode,choice)
   duplicate.undo_and_partial(browser,name)
   integration.history(browser,name)
   integration.multi_slot(browser,name)
   for width in [320,360]:
    integration.run(browser,name,width)
    imports.parse_tests(browser,name,width)
  browser.close()
