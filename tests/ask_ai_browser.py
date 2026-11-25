"""Ask AI page (2026-11-19): bottom-bar tab, five jobs, Family tastes + Claude link on the page,
recipe-page Ask AI, waiting-answer card, single/multi paste, Update original vs Save as new, restriction flags,
step tags -> links. Replaces the earlier pop-up test.

Run: python3 tests/ask_ai_browser.py   (screenshots in /tmp/askai)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/askai')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.ai={
 tastes:()=>({...familyTastes}),
 fav:()=>{const m=meals.find(m=>m.id===2);m.favorite=true;m.ingredients=['1 1/2 lb flank steak','2 tbsp fish sauce (or to taste)','1 lime, juiced'];persist();return m.name},
 request:(job,data)=>buildAiJobRequest(job,data),
 stubOpen:()=>{window.__opened=[];window.open=(u)=>{window.__opened.push(u);return null};window.__copied=null;copyAskAiText=async t=>{window.__copied=t;return true}},
 opened:()=>window.__opened,copied:()=>window.__copied,
 editorOpen:()=>editId!==null,
 meal:name=>{const m=meals.find(x=>x.name===name&&!x._scheduledEditorDraft);return m&&{id:m.id,cat:m.cat,ai:m.aiRecipe===true,rotation:m.rotation,ingredients:m.ingredients,links:(m.ingredientStepLinks||[]).length}},
 count:()=>meals.filter(m=>!m._scheduledEditorDraft).length,
 pending:()=>aiPending(),aiWeekly:()=>groupUsesRotation('AI recipes'),noAiGroup:()=>!cats.some(c=>c.toLocaleLowerCase()==='ai recipes'),
 viewer:name=>openSavedMealRecipe(meals.find(m=>m.name===name),null,null),
 closeViewer:()=>closeRecipeViewer(),
 onGroups:()=>!showTop,
 alt:name=>{const m=meals.find(x=>x.name===name&&!x._scheduledEditorDraft);return m&&m.aiAltVersion?m.aiAltVersion.kind:null},
 setPending:(job,name)=>{const m=meals.find(x=>x.name===name&&!x._scheduledEditorDraft);setAiPending({job,recipeId:String(m.id),recipeName:m.name,at:Date.now()})}
};'''

ONE = """Here you go!

**Title:** Garlic Chicken Stir-Fry
Prep time: 15 minutes
Cook time: 1 hour 10 minutes
Servings: 4
Ingredients
- 1 lb chicken thighs [1]
- 2 tbsp soy sauce [1]
- 1 tbsp butter [steps 1, 2]
- 1 cup coconut milk [2]
Instructions
1. Slice the chicken and toss with the sauce.
2. Stir-fry until cooked through, then add the coconut milk.
"""
TWO = """Title: Lemongrass Pork Bowls
Prep time: 20 minutes
Cook time: 15 minutes
Ingredients
1 lb ground pork [1]
2 stalks lemongrass [1]
Instructions
1. Brown the pork with lemongrass.

Title: Thai Basil Chicken
Prep time: 10 minutes
Cook time: 10 minutes
Ingredients
1 lb ground chicken [1]
1 cup basil [2]
2 tbsp butter [1]
Instructions
1. Cook the chicken.
2. Stir in basil.
"""


def shot(p, tag, name):
    p.screenshot(path=str(OUT / ('%s-%s.png' % (tag, name))))


def go_ai(p):
    p.locator('#mealBottomNav button[data-destination=ai]').click()
    p.wait_for_timeout(250)


def close_dialog(p):
    p.locator('.recipe-bulk-dialog button[aria-label^="Close"]').last.click()
    p.wait_for_timeout(200)


def page_paste(p, text):
    if not p.locator('.ai-paste-card textarea').count():
        p.get_by_role('button', name='Paste an answer').click()
    p.locator('.ai-paste-card textarea').fill(text)
    btn = p.locator('.ai-paste-card').get_by_role('button', name='Review recipe')
    btn.evaluate('b=>b.scrollIntoView({block:"center"})')
    btn.click()
    p.wait_for_timeout(600)


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    p.evaluate('ai.stubOpen()')
    fav = p.evaluate('ai.fav()')
    assert not p.locator('.ask-ai-open').count(), 'Meals page keeps only the calendar'
    go_ai(p)
    assert p.locator('.ask-ai-page h2').text_content() == 'Ask AI'
    jobs = p.locator('.ai-job').all_text_contents()
    assert jobs == ['What’s in my fridge', 'Write a recipe', 'Change a recipe', 'Would my family like it?', 'Out of an ingredient'], jobs
    assert p.locator('#mealBottomNav button[data-destination=ai]').get_attribute('aria-current') == 'page'
    shot(p, tag, 'page')

    # Family tastes on the page (collapsed by default); kept on reload.
    p.locator('.ai-tastes-toggle').click()
    p.get_by_label('What we like', exact=True).fill('Asian flavors, very savory, not too sweet')
    p.get_by_label('Restrictions', exact=True).fill('no dairy, no soy')
    shot(p, tag, 'tastes')
    p.reload(); p.wait_for_timeout(500); p.evaluate('ai.stubOpen()')
    assert p.evaluate('ai.tastes()')['restrictions'] == 'no dairy, no soy'
    go_ai(p)

    # Fridge job: validation, prefilled new chat, waiting card.
    p.locator('.ai-job[data-ai-job=fridge]').click()
    dialog = p.locator('.ask-ai-dialog')
    dialog.get_by_role('button', name='Open in Claude').click()
    assert 'List what you have first.' in dialog.locator('.recipe-bulk-error').text_content()
    dialog.locator('textarea').fill('chicken thighs, bok choy')
    shot(p, tag, 'fridge')
    dialog.get_by_role('button', name='Open in Claude').click()
    p.wait_for_timeout(250)
    opened = p.evaluate('ai.opened()')
    assert opened and opened[-1].startswith('https://claude.ai/new?q=') and 'bok%20choy' in opened[-1], opened
    req = p.evaluate('([j,d])=>ai.request(j,d)', ['fridge', {'input': 'x'}])
    for part in ['Our tastes: Asian flavors', 'no dairy, no soy', fav + ' (flank steak, fish sauce, lime)', 'Other meals we already cook', 'Do NOT write any full recipe yet', 'or "all"', '[3, 5]']:
        assert part in req, (part, req)
    assert not p.locator('.ask-ai-dialog').count(), 'pop-up closes once sent'
    assert p.evaluate('ai.pending()')['job'] == 'fridge'
    assert 'What’s in my fridge' in p.locator('.ai-paste-card').text_content()
    shot(p, tag, 'waiting')

    # Claude project link: copy + open that link instead of a new chat.
    p.locator('.ai-tastes-toggle').click()
    p.get_by_label('Claude project link', exact=True).fill('https://claude.ai/project/abc')
    p.locator('.ai-job[data-ai-job=write]').click()
    p.locator('.ask-ai-dialog textarea').fill('crispy pork')
    p.locator('.ask-ai-dialog').get_by_role('button', name='Open in Claude').click(); p.wait_for_timeout(250)
    assert p.evaluate('ai.opened()')[-1] == 'https://claude.ai/project/abc'
    assert 'a recipe for my family: crispy pork' in p.evaluate('ai.copied()')
    assert not p.locator('.ask-ai-dialog').count()

    # Single answer -> review editor with restriction box; saving keeps step links, Off menu.
    page_paste(p, ONE)
    assert p.evaluate('ai.editorOpen()')
    flags = p.locator('.import-restriction-flags li').all_text_contents()
    assert flags == ['2 tbsp soy sauce (soy)', '1 tbsp butter (dairy)'], flags
    p.locator('#save').click(); p.wait_for_timeout(700)
    assert p.evaluate('ai.onGroups()'), 'after saving an AI recipe the app stays on Meal Groups'
    p.wait_for_timeout(300)
    t = p.locator('.serving-undo-toast')
    assert t.count() == 1 and t.locator('span').text_content() == 'Saved Garlic Chicken Stir-Fry', 'saved-new toast'
    assert t.get_by_role('button', name='Open').count() == 1 and t.get_by_role('button', name='Undo').count() == 1
    p.evaluate("document.getElementById('aiToast')?.remove()"); shot(p, tag, 'saved-toast')
    t.get_by_role('button', name='Open').click(); p.wait_for_timeout(500)
    assert p.locator('.serving-undo-toast').count() == 0, 'Open dismisses the toast'
    assert p.evaluate('!!document.querySelector(".recipe-viewer, #recipeViewer, [data-recipe-viewer]")'), 'Open shows the recipe viewer'
    p.evaluate('ai.closeViewer()'); p.wait_for_timeout(300)
    saved = p.evaluate('n=>ai.meal(n)', 'Garlic Chicken Stir-Fry')
    assert saved and saved['cat'] == '' and saved['ai'] is True and saved['rotation'] is False and saved['links'] == 2 and saved['ingredients'][0] == '1 lb chicken thighs', saved
    assert p.evaluate('ai.pending()') is None

    # Several recipes in one paste -> checklist -> Off menu.
    go_ai(p)
    before = p.evaluate('ai.count()')
    page_paste(p, TWO)
    multi = p.locator('.ai-multi-review')
    assert multi.locator('.ai-multi-row').count() == 2
    assert 'butter' in multi.locator('.ai-multi-row').nth(1).text_content()
    shot(p, tag, 'multi')
    multi.get_by_role('button', name='Save 2 recipes').click(); p.wait_for_timeout(400)
    assert p.evaluate('ai.count()') == before + 2
    assert p.evaluate('n=>ai.meal(n)', 'Thai Basil Chicken')['links'] == 2 and p.evaluate('n=>ai.meal(n)', 'Thai Basil Chicken')['cat'] == '' and p.evaluate('n=>ai.meal(n)', 'Thai Basil Chicken')['ai'] is True
    assert p.evaluate('ai.noAiGroup()') is True  # no app-made AI recipes group any more (2026-11-24)

    # Recipe page -> Ask AI -> Convert -> Update original (one Undo restores it).
    target = 'Garlic Chicken Stir-Fry'
    p.evaluate('n=>ai.viewer(n)', target); p.wait_for_timeout(400)
    p.get_by_role('button', name='Ask AI about this recipe').click(); p.wait_for_timeout(200)
    shot(p, tag, 'recipe-menu')
    p.locator('.ai-recipe-menu').get_by_role('button', name='Change this recipe').click(); p.wait_for_timeout(500)
    conv = p.locator('.ask-ai-dialog')
    assert target in conv.text_content()
    shot(p, tag, 'convert')
    conv.get_by_role('button', name='Copy request').click(); p.wait_for_timeout(200)
    assert 'Convert this recipe' in p.evaluate('ai.copied()') and '2 tbsp soy sauce' in p.evaluate('ai.copied()')
    pend = p.evaluate('ai.pending()')
    assert pend['job'] == 'convert' and pend['recipeName'] == target, pend
    p.wait_for_timeout(400)
    assert p.evaluate('()=>!!document.querySelector(".ask-ai-page .ai-paste-card textarea")'), 'recipe-page request lands on Ask AI with the paste card'
    count = p.evaluate('ai.count()')
    page_paste(p, ONE.replace('2 tbsp soy sauce [1]', '2 tbsp coconut aminos [1]').replace('1 tbsp butter [steps 1, 2]', '1 tbsp olive oil [1]'))
    choice = p.locator('.ai-save-mode')
    assert choice.get_by_role('button', name='Update ' + target).count() == 1
    shot(p, tag, 'save-mode')
    choice.get_by_role('button', name='Update ' + target).click(); p.wait_for_timeout(600)
    assert 'Saving updates ' + target in p.locator('.ai-replace-note').text_content()
    shot(p, tag, 'update-review')
    p.locator('#save').click(); p.wait_for_timeout(500)
    upd = p.evaluate('n=>ai.meal(n)', target)
    assert '2 tbsp coconut aminos' in upd['ingredients'] and upd['id'] == saved['id'], upd
    assert p.evaluate('ai.count()') == count, 'update must not add a recipe'
    ut = p.locator('.serving-undo-toast')
    assert ut.count() == 1 and ut.locator('span').text_content() == 'Updated ' + target and ut.get_by_role('button', name='Open').count() == 1, 'updated toast has Open'
    assert p.evaluate('n=>ai.alt(n)', target) == 'original'
    # Recipe page: switch to the original and back, then discard the other version.
    p.evaluate('n=>ai.viewer(n)', target); p.wait_for_timeout(400)
    p.get_by_role('button', name='Show original').click(); p.wait_for_timeout(200)
    shot(p, tag, 'versions')
    p.get_by_role('button', name='Switch to the original recipe').click(); p.wait_for_timeout(300)
    assert '2 tbsp soy sauce' in p.evaluate('n=>ai.meal(n)', target)['ingredients']
    assert p.get_by_role('button', name='Show changed').count() == 1 and p.locator('.recipe-version-note').text_content().startswith('Original')
    p.get_by_role('button', name='Show changed').click(); p.wait_for_timeout(200)
    p.get_by_role('button', name='Switch to the changed recipe').click(); p.wait_for_timeout(300)
    assert '2 tbsp coconut aminos' in p.evaluate('n=>ai.meal(n)', target)['ingredients']
    p.get_by_role('button', name='Show original').click(); p.wait_for_timeout(200)
    p.get_by_role('button', name='Discard the changed recipe').click(); p.wait_for_timeout(300)
    # Discard targets the version being viewed: the saved original becomes the recipe.
    assert p.evaluate('n=>ai.alt(n)', target) is None and p.get_by_role('button', name='Show original').count() == 0
    assert '2 tbsp soy sauce' in p.evaluate('n=>ai.meal(n)', target)['ingredients']
    # The discard toast sits above the recipe view and its Undo brings the changed version back.
    assert p.locator('.serving-undo-toast').count() == 1
    p.locator('.serving-undo-toast button').click(); p.wait_for_timeout(400)
    assert p.evaluate('n=>ai.alt(n)', target) == 'original', 'toast Undo must restore the changed version'
    assert '2 tbsp coconut aminos' in p.evaluate('n=>ai.meal(n)', target)['ingredients']
    assert p.get_by_role('button', name='Show original').count() == 1
    p.get_by_role('button', name='Show original').click(); p.wait_for_timeout(200)
    p.get_by_role('button', name='Discard the changed recipe').click(); p.wait_for_timeout(300)
    assert p.evaluate('n=>ai.alt(n)', target) is None
    p.evaluate('ai.closeViewer()'); p.wait_for_timeout(300)
    # Replace keeps no other version.
    p.evaluate('n=>ai.setPending("like",n)', target)
    go_ai(p)
    page_paste(p, ONE.replace('1 cup coconut milk [2]', '1/2 cup coconut milk [2]'))
    p.locator('.ai-save-mode').get_by_role('button', name='Replace ' + target).click(); p.wait_for_timeout(600)
    assert 'Saving replaces ' + target in p.locator('.ai-replace-note').text_content()
    p.locator('#save').click(); p.wait_for_timeout(500)
    assert '½ cup coconut milk' in p.evaluate('n=>ai.meal(n)', target)['ingredients'] and p.evaluate('n=>ai.alt(n)', target) is None

    # Out of an ingredient: pick a recipe, tap an ingredient chip; nothing to paste back.
    go_ai(p)
    p.locator('.ai-job[data-ai-job=out]').click()
    out = p.locator('.ask-ai-dialog')
    out.get_by_label('Search your recipes').fill('Garlic Chicken')
    out.locator('.ai-recipe-result').first.click()
    out.locator('.ai-ingredient-chip').first.click()
    shot(p, tag, 'out')
    out.get_by_role('button', name='Copy request').click(); p.wait_for_timeout(200)
    assert "I'm out of 1 lb chicken thighs" in p.evaluate('ai.copied()')
    assert p.evaluate('ai.pending()') is None
    assert not errors, errors
    c.close()
    print('PASS', name, 'Ask AI page: tab, jobs, tastes+link, waiting card, single/multi paste, update original, recipe-page menu, out of ingredient', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
