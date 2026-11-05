"""Explicitly reveal the newly collapsed editor sections when exercising their controls."""
def open_editor_section(page,key):
 section=page.locator('#editor [data-editor-section="'+key+'"]')
 if section.get_attribute('open') is None:section.locator(':scope > summary').tap()
 return section
def expand_editor_sections(page):
 for key in ['timing','organization','recipe','notes']:open_editor_section(page,key)
