"""Delete dialog + Deleted recipes bin (2026-11-24, v375).

Checks on index.html and meal-rotation-test.html: reason radios (defaults by status), optional note,
deletion moves the recipe to the bin, dislike record, Undo/Redo, Settings restore (same group, place, status),
restore Undo toast, 30-day purge, missing-group fallback to Unassigned, Ask AI request lists dislikes,
backup validation of the two new keys.
Run: python3 tests/deleted_recipes_browser.py   (screenshots in /tmp/deleted)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/deleted')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.bin={
 meal:id=>{const m=meals.find(x=>String(x.id)===String(id));return m&&{id:m.id,name:m.name,cat:m.cat,rotation:!!m.rotation,index:meals.indexOf(m)}},
 regular:()=>{const m=meals.find(x=>x.rotation&&x.cat&&!x.linkGroup&&!x._scheduledEditorDraft);return m&&String(m.id)},
 offmenu:()=>{let m=meals.find(x=>!x.rotation&&x.cat&&!x.linkGroup&&!x._scheduledEditorDraft);if(!m){m=meals.find(x=>x.rotation&&x.cat&&!x.linkGroup&&String(x.id)!==window.__first);setRecipeStatus(m,'up-next');persist()}return String(m.id)},
 ask:ids=>{window.__choice=undefined;confirmDeleteRecipes(ids).then(v=>{window.__choice=v})},
 choice:()=>window.__choice,
 del:()=>deleteRecipesToBin(window.__choice),
 list:()=>deletedRecipes(),dislikes:()=>recipeDislikes(),
 undo:()=>document.getElementById('undo').click(),redo:()=>document.getElementById('redo')?.click(),
 age:days=>{const l=deletedRecipes();l[0].deletedAt=new Date(Date.now()-days*864e5).toISOString();testOrLocal().setItem('mealRotationDeletedRecipesV1',JSON.stringify(l))},
 purge:()=>purgeDeletedRecipes(),restore:id=>restoreDeletedRecipe(id)&&true,
 request:()=>buildAiJobRequest('write',{input:'a soup'}),
 dropGroup:name=>{cats=cats.filter(c=>c!==name);persist()},
 validate:(key,value)=>{try{validateSavedRecords({[key]:value},false);return 'ok'}catch(e){return e.message}}
};
window.testOrLocal=()=>typeof testStorage!=='undefined'?testStorage:localStorage;'''


def shot(p, tag, label):
    p.screenshot(path=str(OUT / f'{tag}-{label}.png'))


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    reg = p.evaluate('bin.regular()')
    p.evaluate(f'window.__first="{reg}"')
    before = p.evaluate(f'bin.meal("{reg}")')

    # Regular: default "Didn't like it", note visible.
    p.evaluate(f'bin.ask(["{reg}"])')
    dlg = p.locator('.recipe-delete-dialog')
    dlg.wait_for()
    assert dlg.locator('strong').first.text_content() == 'Delete this recipe?'
    assert dlg.locator('input[value=disliked]').is_checked()
    assert dlg.locator('.recipe-delete-note').is_visible()
    assert '30 days' in dlg.locator('.recipe-bulk-note').text_content()
    dlg.locator('textarea').fill('too spicy')
    shot(p, tag, 'dialog-regular')
    # Cleaning up hides the note and does not send it.
    dlg.locator('input[value=cleanup]').check()
    assert not dlg.locator('.recipe-delete-note').is_visible()
    dlg.locator('input[value=disliked]').check()
    dlg.get_by_role('button', name='Confirm deletion').click()
    choice = p.evaluate('bin.choice()')
    assert choice['reason'] == 'disliked' and choice['note'] == 'too spicy', choice

    p.evaluate('bin.del()')
    assert p.evaluate(f'bin.meal("{reg}")') is None, 'recipe removed'
    lst = p.evaluate('bin.list()')
    assert len(lst) == 1 and lst[0]['name'] == before['name'] and lst[0]['reason'] == 'disliked' and lst[0]['note'] == 'too spicy'
    dis = p.evaluate('bin.dislikes()')
    assert len(dis) == 1 and dis[0]['name'] == before['name'] and dis[0]['group'] == before['cat']
    req = p.evaluate('bin.request()')
    assert "didn't like" in req and before['name'] + ' (too spicy)' in req, req

    # Undo brings the recipe back and empties bin + dislikes; Redo deletes again.
    p.evaluate('bin.undo()')
    assert p.evaluate(f'bin.meal("{reg}")') is not None and p.evaluate('bin.list()') == [] and p.evaluate('bin.dislikes()') == []
    p.evaluate('bin.redo()')
    assert p.evaluate(f'bin.meal("{reg}")') is None and len(p.evaluate('bin.list()')) == 1

    # Off menu: default "Just cleaning up", no dislike recorded.
    off = p.evaluate('bin.offmenu()')
    p.evaluate(f'bin.ask(["{off}"])')
    dlg.wait_for()
    assert dlg.locator('input[value=cleanup]').is_checked() and not dlg.locator('.recipe-delete-note').is_visible()
    shot(p, tag, 'dialog-offmenu')
    dlg.get_by_role('button', name='Confirm deletion').click()
    p.evaluate('bin.del()')
    assert len(p.evaluate('bin.list()')) == 2 and len(p.evaluate('bin.dislikes()')) == 1

    # X cancels without deleting.
    reg2 = p.evaluate('bin.regular()')
    p.evaluate(f'bin.ask(["{reg2}"])')
    dlg.wait_for()
    dlg.get_by_role('button', name='Cancel deletion').click()
    assert p.evaluate('bin.choice()') is None and p.evaluate(f'bin.meal("{reg2}")') is not None

    # Settings: list and restore the Regular to its group, place and status.
    p.locator('#settings').click()
    group = p.locator('details[data-settings-group=deleted]')
    group.locator('summary').click()
    p.wait_for_timeout(300)
    rows = group.locator('.deleted-recipe-row')
    assert rows.count() == 3, rows.count()  # 2 deleted + 1 dislike
    group.scroll_into_view_if_needed()
    shot(p, tag, 'settings')
    btn = group.get_by_role('button', name='Restore ' + before['name'])
    btn.click()
    p.wait_for_timeout(300)
    after = p.evaluate(f'bin.meal("{reg}")')
    assert after and after['cat'] == before['cat'] and after['rotation'] == before['rotation'] and after['index'] == before['index'], (before, after)
    assert len(p.evaluate('bin.list()')) == 1 and p.evaluate('bin.dislikes()') == []
    assert p.locator('.serving-undo-toast').is_visible()
    assert group.locator('.deleted-recipe-row').count() == 1
    shot(p, tag, 'restored')
    p.locator('.serving-undo-toast button').click()
    assert p.evaluate(f'bin.meal("{reg}")') is None and len(p.evaluate('bin.list()')) == 2

    # Group gone -> restores to Unassigned, not Regulars.
    p.evaluate(f'bin.dropGroup("{before["cat"]}")')
    entry = [e for e in p.evaluate('bin.list()') if e['name'] == before['name']][0]
    p.evaluate(f'bin.restore("{entry["id"]}")')
    m = p.evaluate(f'bin.meal("{reg}")')
    assert m['cat'] == '' and m['rotation'] is False, m

    # 30-day purge keeps dislikes.
    p.evaluate('bin.age(31)')
    p.evaluate('bin.purge()')
    assert p.evaluate('bin.list()') == []

    # Backup validation.
    assert p.evaluate('bin.validate("mealRotationDeletedRecipesV1","[]")') == 'ok'
    assert p.evaluate('bin.validate("mealRotationRecipeDislikesV1","[{\\"id\\":\\"a\\",\\"name\\":\\"x\\"}]")') == 'ok'
    assert 'Invalid' in p.evaluate('bin.validate("mealRotationDeletedRecipesV1","[{\\"id\\":\\"a\\",\\"name\\":\\"x\\"}]")')
    assert not errors, errors
    c.close()
    print(name, 'ok')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ['index.html', 'meal-rotation-test.html']:
        run(b, n)
    b.close()
