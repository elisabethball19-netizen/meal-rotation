"""Open a recipe's section explicitly in tests that exercise its row controls."""
def reveal_recipe(page,meal_id):
 row=page.locator('#list .master-category-meal[data-meal-id="'+str(meal_id)+'"]')
 if not row.is_visible():
  toggle=row.locator('..').locator('..').locator(':scope > .master-category-group-label')
  if toggle.count() and toggle.get_attribute('aria-expanded')=='false':toggle.tap()
 return row

def expand_recipe_sections(page):
 toggles=page.locator('#list .master-category-group-label[aria-expanded=false]:visible')
 while toggles.count():toggles.first.tap()
