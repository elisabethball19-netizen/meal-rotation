"""Ask AI (copy-and-paste) + Family tastes (2026-11-19).

- Settings > Family tastes saves likes/restrictions (kept on reload; Cancel reverts).
- Meals page Ask AI: request includes tastes, restrictions, favorites with main ingredients, Regulars, reply format.
- Open in Claude opens claude.ai/new?q=<request>.
- Pasted answer opens the normal import review (Off menu) with prep/cook times and restriction flags.

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
 save:()=>finishSettings('save'),cancel:()=>finishSettings('cancel'),tastes:()=>({...familyTastes}),
 fav:()=>{const m=meals.find(m=>m.id===2);m.favorite=true;m.ingredients=['1 1/2 lb flank steak','2 tbsp fish sauce (or to taste)','1 lime, juiced'];persist();return m.name},
 request:(mode,text)=>buildAskAiRequest(mode,text),
 stubOpen:()=>{window.__opened=[];window.open=(u)=>{window.__opened.push(u);return null}},opened:()=>window.__opened,
 item:a=>{const i=askAiItemFromAnswer(a);return {ing:i.ingredients,prep:i.prep,cook:i.cook,steps:(i.instructions||[]).filter(s=>s.type==='step').length}},
 links:()=>{const m=meals.find(x=>x.id===editId),items=recipeAssociationItems(m),name=t=>items.ingredients.find(i=>i.token===t)?.text;return validRecipeIngredientLinks(m).map(l=>l.ingredients.map(name))},
 savedLinks:name=>{const m=meals.find(x=>x.name===name),items=recipeAssociationItems(m),n=t=>items.ingredients.find(i=>i.token===t)?.text;return [validRecipeIngredientLinks(m).map(l=>l.ingredients.map(n)),m.rotation===true]},
 editorOpen:()=>editId!==null,
 conflicts:(lines,r)=>restrictionConflicts(lines,familyRestrictionRules(r)).map(f=>f.line)
};'''

ANSWER = """Here you go!

**Title:** Garlic Chicken Stir-Fry
Prep time: 15 minutes
Cook time: 1 hour 10 minutes
Servings: 4
Ingredients
- 1 lb chicken thighs [1]
- 2 tbsp soy sauce [1]
- 1 tbsp butter [steps 1, 2]
- 1 cup coconut milk [2]
- 1 tbsp peanut butter
Instructions
1. Slice the chicken and toss with the sauce.
2. Stir-fry until cooked through, then add the coconut milk.
Notes
Serve with rice."""


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    # Family tastes in Settings, Cancel reverts, Save keeps (and survives reload).
    p.locator('#settings').click()
    p.evaluate('document.querySelector("details[data-settings-group=tastes]").open=true')
    p.get_by_label('What we like', exact=True).fill('Asian flavors, very savory, not too sweet')
    p.get_by_label('Restrictions', exact=True).fill('no dairy, no soy')
    p.screenshot(path=str(OUT / (tag + '-settings.png')))
    p.evaluate('ai.cancel()')
    assert p.evaluate('ai.tastes()') == {'likes': '', 'restrictions': ''}, p.evaluate('ai.tastes()')
    p.locator('#settings').click()
    p.evaluate('document.querySelector("details[data-settings-group=tastes]").open=true')
    p.get_by_label('What we like', exact=True).fill('Asian flavors, very savory, not too sweet')
    p.get_by_label('Restrictions', exact=True).fill('no dairy, no soy')
    p.evaluate('ai.save()')
    p.reload()
    p.wait_for_timeout(500)
    assert p.evaluate('ai.tastes()')['restrictions'] == 'no dairy, no soy'
    fav = p.evaluate('ai.fav()')

    # Request contents.
    req = p.evaluate('([m,t])=>ai.request(m,t)', ['fridge', 'chicken thighs, bok choy'])
    for part in ['What I have: chicken thighs, bok choy', 'Our tastes: Asian flavors', 'Our usual restrictions: no dairy, no soy', 'first ask me whether to keep it', 'no dairy, no soy',
                 fav + ' (flank steak, fish sauce, lime)', 'Other meals we already cook', 'Suggest 3 different meals', 'Title: Recipe name', 'Prep time:']:
        assert part in req, (part, req)
    assert 'Write a recipe for my family: crispy pork' in p.evaluate('([m,t])=>ai.request(m,t)', ['write', 'crispy pork'])

    # Restriction matching rules.
    hits = p.evaluate('([l,r])=>ai.conflicts(l,r)', [['2 tbsp soy sauce', '1 cup coconut milk', '1 tbsp butter', '1 tbsp peanut butter', '1 eggplant', '2 tbsp hoisin sauce'], 'no dairy, no soy'])
    assert hits == ['2 tbsp soy sauce', '1 tbsp butter', '2 tbsp hoisin sauce'], hits

    # Ask AI dialog from the Meals page.
    p.evaluate('ai.stubOpen()')
    p.get_by_role('button', name='Ask AI').click()
    dialog = p.locator('.ask-ai-dialog')
    assert dialog.get_by_role('tab', name='What’s in my fridge').get_attribute('aria-selected') == 'true'
    dialog.get_by_role('button', name='Open in Claude').click()
    assert 'List what you have first.' in dialog.locator('.recipe-bulk-error').text_content()
    dialog.locator('.ask-ai-input').fill('chicken thighs, bok choy, rice')
    dialog.get_by_role('button', name='Open in Claude').click()
    p.wait_for_timeout(200)
    opened = p.evaluate('ai.opened()')
    assert len(opened) == 1 and opened[0].startswith('https://claude.ai/new?q=') and 'bok%20choy' in opened[0], opened
    dialog.get_by_role('tab', name='Write a recipe').click()
    p.screenshot(path=str(OUT / (tag + '-dialog.png')))
    dialog.get_by_label('Paste the answer').fill('just chatting, no recipe')
    dialog.get_by_role('button', name='Review recipe').click()
    assert 'No ingredients were found' in dialog.locator('.recipe-bulk-error').text_content()
    dialog.get_by_label('Paste the answer').fill(ANSWER)
    dialog.get_by_role('button', name='Review recipe').click()
    p.wait_for_timeout(600)
    assert p.evaluate('ai.editorOpen()'), 'import review should open'
    flags = p.locator('.import-restriction-flags li').all_text_contents()
    assert flags == ['2 tbsp soy sauce (soy)', '1 tbsp butter (dairy)'], flags
    item = p.evaluate('a=>ai.item(a)', ANSWER)
    assert item['ing'] == ['1 lb chicken thighs', '2 tbsp soy sauce', '1 tbsp butter', '1 cup coconut milk', '1 tbsp peanut butter'], item
    links = p.evaluate('ai.links()')
    assert links == [['1 lb chicken thighs', '2 tbsp soy sauce', '1 tbsp butter'], ['1 tbsp butter', '1 cup coconut milk']], links
    assert 'Title: Recipe name' in req and '[3, 5]' in req
    assert item['prep'] == 15 and item['cook'] == 70 and item['steps'] >= 1, item
    p.screenshot(path=str(OUT / (tag + '-review.png')))
    p.locator('.import-restriction-flags').scroll_into_view_if_needed()
    p.screenshot(path=str(OUT / (tag + '-flags.png')))
    rec = p.evaluate('()=>{const n=document.querySelector("#editor input[aria-label*=name i], #editor input[type=text]");return n&&n.value}')
    assert rec == 'Garlic Chicken Stir-Fry', rec
    p.locator('#save').click()
    p.wait_for_timeout(500)
    saved = p.evaluate('n=>ai.savedLinks(n)', 'Garlic Chicken Stir-Fry')
    assert saved == [links, False], saved
    # Pasting the same answer again still opens the single-recipe review (not the bulk importer).
    p.evaluate('follow126.home()')
    p.get_by_role('button', name='Ask AI').click()
    p.locator('.ask-ai-dialog').get_by_label('Paste the answer').fill(ANSWER)
    p.locator('.ask-ai-dialog').get_by_role('button', name='Review recipe').click()
    p.wait_for_timeout(600)
    assert p.evaluate('ai.editorOpen()'), 'repeat paste should open the review editor'
    assert not errors, errors
    c.close()
    print('PASS', name, 'Ask AI: family tastes, request, Open in Claude, paste -> review with restriction flags', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
