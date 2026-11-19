"""Unassigned recipes are editable (2026-11-19): each flat Unassigned row has an Edit pencil; tapping the name still opens the recipe.

Run: python3 tests/unassigned_edit_browser.py   (screenshots in /tmp/unassigned)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/unassigned')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.ua={
 setup:()=>{const base=Math.max(...meals.map(m=>Number(m.id)||0))+1;meals.push({id:base,name:'Loose Recipe A',cat:'',rotation:false,ingredients:['1 egg'],instructions:[]},{id:base+1,name:'Loose Recipe B',cat:'',rotation:false,ingredients:['2 eggs'],instructions:[]});persist();showTop=false;groceryTabActive=false;allMealsActive=false;setGroupPageSectionOpen('unassigned',true);render()},
 names:()=>meals.filter(m=>!m.cat).map(m=>m.name).sort(),
 reopen:()=>{showTop=false;setGroupPageSectionOpen('unassigned',true);render()},
 editorOpen:()=>editId!==null
};'''


def run(browser, name):
    c, p, errors, _ = sb.open_page(browser, name)
    p.evaluate('ua.setup()')
    p.wait_for_timeout(300)
    rows = p.locator('.unassigned-row')
    assert rows.count() >= 2, rows.count()
    p.screenshot(path=str(OUT / (name.split('.')[0] + '-list.png')))
    p.get_by_role('button', name='Edit Loose Recipe A', exact=True).click()
    p.wait_for_timeout(400)
    assert p.evaluate('ua.editorOpen()')
    p.evaluate('''()=>{const i=[...document.querySelectorAll("input,textarea")].find(x=>x.value==="Loose Recipe A");i.value="Loose Recipe A edited";i.dispatchEvent(new Event("input",{bubbles:true}));i.dispatchEvent(new Event("change",{bubbles:true}))}''')
    p.locator('#save').click()
    p.wait_for_timeout(500)
    assert p.evaluate('ua.names()') == ['Loose Recipe A edited', 'Loose Recipe B'], p.evaluate('ua.names()')
    p.evaluate('ua.reopen()')
    p.locator('.unassigned-row .unassigned-name', has_text='Loose Recipe B').click()
    p.wait_for_timeout(400)
    assert p.locator('.recipe-viewer, [aria-label*="Loose Recipe B"]').count() >= 1, 'name tap should open the recipe'
    assert not errors, errors
    c.close()
    print('PASS', name, 'Unassigned rows: Edit pencil edits in place; name opens recipe', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
