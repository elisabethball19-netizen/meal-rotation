"""2026-11-24: Meal Groups 'AI recipes' section (recipe marker, no group) directly above Unassigned.

Covers: one-time migration of the old app-made 'AI recipes' group (solo recipes get the marker, a recipe with a copy in
a real group just loses its AI copy, empty group removed, toast, Undo restores), skip when that group is on a weekday,
new Ask AI saves land in the section, Move to a real group removes the marker, delete uses the normal dialog/bin,
section always shown (empty text), backups validate the marker. Disposable origins for index.html and the test copy.
Run: python3 tests/ai_recipes_section_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s  # registers follow126 + sw130 hooks

s.fixture.HOOK += '''window.aisec={
 store:()=>typeof testStorage!=='undefined'?testStorage:localStorage,
 seedGroup:(onDay=false)=>{cats=[...cats,'AI recipes'];meals.push({id:20,name:'AI Tacos',cat:'AI recipes',rotation:false,recipeStatus:'ideas',ingredients:['1 lb beef'],groceryDefaultAll:true,url:''},{id:21,name:'AI Curry',cat:'AI recipes',rotation:false,recipeStatus:'ideas',ingredients:['1 cup rice'],groceryDefaultAll:true,url:'',linkGroup:'g21'},{id:22,name:'AI Curry',cat:'Rice',rotation:true,recipeStatus:'rotation',ingredients:['1 cup rice'],groceryDefaultAll:true,url:'',linkGroup:'g21'});if(onDay){weekdayCategories.Friday=['AI recipes'];mealPlans[0].weekdayCategories={...weekdayCategories}}aisec.store().removeItem('mealRotationAiSectionMigratedV1');saveActiveMealPlan(false);persist()},
 groups:()=>{showTop=false;groceryTabActive=false;allMealsActive=false;renderList({readOnly:true})},
 state:()=>({cats:[...cats],ai:meals.filter(m=>m.aiRecipe).map(m=>[m.id,m.cat]),ids:meals.map(m=>m.id)}),
 sections:()=>[...document.querySelectorAll('.master-group-section')].map(x=>x.dataset.groupSection),
 saveMany:()=>{snapshot();for(const name of ['AI Soup','AI Salad'])meals.push({...aiImportRecord({name,ingredients:['1 cup broth'],instructions:[{type:'step',text:'Cook.'}]}),id:id++,cat:'',aiRecipe:true,rotation:false});persist();renderList({readOnly:true})},
 single:async()=>{await reviewRecipeImportItems([{name:'AI Stew',ingredients:['1 lb beef'],instructions:[{type:'step',text:'Simmer.'}],aiTargetGroup:'',aiRecipe:true}],'Ask AI');return meals.find(m=>m.name==='AI Stew')?.aiRecipe===true},
 toGroup:name=>{const m=meals.find(x=>x.name===name);m.cat='Rice';persist();return Object.hasOwn(m,'aiRecipe')},
 backup:()=>{const b=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(b);return true},
 badBackup:()=>{const m=meals.find(x=>x.aiRecipe);m.aiRecipe='yes';try{validateBackupCore({...JSON.parse(captureState()),meals:[m]});return 'accepted'}catch(e){return e.message}finally{m.aiRecipe=true}},
 soup:()=>meals.filter(m=>m.name==='AI Soup').map(m=>[m.cat,!!m.aiRecipe,recipeStatus(m),m.upNextStar===true]),
 oldPin:()=>{meals.push({id:41,name:'Old pinned',cat:'Rice',rotation:false,recipeStatus:'up-next',upNextStar:true,ingredients:[],groceryDefaultAll:true,url:''});persist();placeUpNextFirst(meals.find(m=>m.id===41))},
 riceOffMenu:()=>normalizedUpNextOrder().map(id=>meals.find(m=>String(m.id)===id)).filter(m=>m&&m.cat==='Rice').map(m=>m.name),
 editLabel:()=>{const m=meals.find(x=>x.aiRecipe);openEditor(m.id);const t=document.querySelector('.meal-group-assigned-list')?.textContent;return t},
 loose:()=>{aisec.store().setItem('mealRotationAiSectionMigratedV1','none');meals.push({id:30,name:'Loose recipe',cat:'',rotation:false,recipeStatus:'ideas',ingredients:[],groceryDefaultAll:true,url:''});persist()},
 pie:()=>{meals.push({id:40,name:'AI Pie',cat:'',aiRecipe:true,rotation:false,recipeStatus:'ideas',ingredients:[],groceryDefaultAll:true,url:''});persist();aisec.groups()},
 flag:()=>aisec.store().getItem('mealRotationAiSectionMigratedV1')
};'''


def section(p, key):
    return p.locator('[data-group-section=%s]' % key)


def open_section(p, key):
    box = section(p, key)
    if box.locator('.master-group-section-toggle').get_attribute('aria-expanded') != 'true':
        box.locator('.master-group-section-toggle').click(); p.wait_for_timeout(150)


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    p.evaluate('follow126.seed()')

    # Empty: section shown above Unassigned with a short explanation.
    p.evaluate('aisec.loose()')
    p.evaluate('aisec.groups()')
    order = p.evaluate('aisec.sections()')
    assert order.index('ai') == order.index('unassigned') - 1, order
    open_section(p, 'ai')
    assert 'No AI recipes yet' in section(p, 'ai').text_content()

    # Migration of the old group on reload.
    p.evaluate('aisec.seedGroup()')
    p.reload(); p.wait_for_function('window.aisec'); p.wait_for_timeout(300)
    st = p.evaluate('aisec.state()')
    assert 'AI recipes' not in st['cats'] and st['ai'] == [[20, '']] and 21 not in st['ids'] and 22 in st['ids'], st
    assert p.evaluate('aisec.flag()') == 'done'
    assert 'moved to the new AI recipes section' in p.locator('.serving-undo-toast').inner_text()
    p.evaluate('aisec.groups()'); open_section(p, 'ai')
    assert 'AI Tacos' in section(p, 'ai').text_content() and 'AI Tacos' not in section(p, 'unassigned').text_content()
    assert 'Loose recipe' in section(p, 'unassigned').text_content()
    # Undo puts the group back exactly; the migration does not run again.
    p.locator('.serving-undo-toast button', has_text='Undo').click(); p.wait_for_timeout(300)
    st = p.evaluate('aisec.state()')
    assert 'AI recipes' in st['cats'] and st['ai'] == [] and 21 in st['ids'], st
    p.reload(); p.wait_for_function('window.aisec'); p.wait_for_timeout(300)
    assert 'AI recipes' in p.evaluate('aisec.state()')['cats']

    # A group on a weekday is left alone.
    p.evaluate('follow126.seed()'); p.evaluate('aisec.seedGroup(true)')
    p.reload(); p.wait_for_function('window.aisec'); p.wait_for_timeout(300)
    assert p.evaluate('aisec.flag()') == 'skipped-weekday' and 'AI recipes' in p.evaluate('aisec.state()')['cats']

    # New AI saves (several, and a single one through the editor) land in the section.
    p.evaluate('follow126.seed()'); p.evaluate("aisec.store().setItem('mealRotationAiSectionMigratedV1','none')")
    p.evaluate('aisec.saveMany()')
    assert p.evaluate('aisec.single()') is True
    p.reload(); p.wait_for_function('window.aisec'); p.wait_for_timeout(300)  # leave the single-save editor
    p.evaluate('aisec.groups()'); open_section(p, 'ai')
    text = section(p, 'ai').text_content()
    assert 'AI Soup' in text and 'AI Salad' in text, text

    # The editor names the section instead of 'Unassigned'.
    assert p.evaluate('aisec.editLabel()') == 'AI recipes'
    p.reload(); p.wait_for_function('window.aisec'); p.wait_for_timeout(300); p.evaluate('aisec.groups()'); open_section(p, 'ai')
    # Move to a real group through the section's Move button: marker removed, lands PINNED at the top of its Off menu.
    p.evaluate('aisec.oldPin()'); p.evaluate('aisec.groups()'); open_section(p, 'ai')
    row = section(p, 'ai').locator('.unassigned-row', has_text='AI Soup')
    row.locator('input.check').check()
    section(p, 'ai').locator('.unassigned-move').click()
    dialog = p.get_by_role('dialog').last
    dialog.get_by_role('checkbox', name='Rice', exact=True).check()
    dialog.get_by_role('button', name='Confirm meal groups', exact=True).click(); p.wait_for_timeout(400)
    soup = p.evaluate("aisec.soup()")
    assert soup and all(cat == 'Rice' and not flag and status == 'up-next' and star for cat, flag, status, star in soup), soup
    assert p.evaluate('aisec.riceOffMenu()')[:2] == ['AI Soup', 'Old pinned'], p.evaluate('aisec.riceOffMenu()')
    p.evaluate('aisec.groups()'); open_section(p, 'ai')
    assert 'AI Soup' not in section(p, 'ai').text_content()
    # Giving a group from anywhere else (e.g. the editor) also clears the marker.
    assert p.evaluate("aisec.toGroup('AI Salad')") is False

    # Delete uses the normal delete dialog.
    p.evaluate('aisec.pie()')
    open_section(p, 'ai')
    section(p, 'ai').locator('.unassigned-row', has_text='AI Pie').locator('input.check').check()
    section(p, 'ai').locator('.unassigned-delete').click()
    assert p.get_by_role('dialog').last.is_visible()

    # Backups keep and validate the marker.
    assert p.evaluate('aisec.backup()') is True
    assert p.evaluate('aisec.badBackup()') == 'Invalid AI recipe marker', p.evaluate('aisec.badBackup()')

    assert not errors, errors
    c.close()
    print('PASS', name, 'AI recipes section: migration (+copy, toast, Undo, weekday skip), saves, Move/editor clear marker, delete dialog, empty state, backup', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
