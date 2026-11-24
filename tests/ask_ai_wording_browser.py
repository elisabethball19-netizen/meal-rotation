"""Ask AI wording fix (v377): restrictions followed silently, clean ingredient lines, brand notes marked with '*'.

Checks request text for every job that sends restrictions, that a pasted answer keeps 'Worcestershire* [3]'
(the '*' stays in the recipe, the step tag still links), that the Notes line '* Worcestershire: ...' survives,
and that '*' never reaches grocery text.
Run: python3 tests/ask_ai_wording_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.wording={
 setRestrictions:t=>{saveFamilyTastes({...familyTastes,restrictions:t})},
 request:(job,data)=>buildAiJobRequest(job,data),
 parse:t=>askAiItemFromAnswer(t),
 grocery:l=>groceryShoppingText(l)
};'''

ANSWER = """Title: Soy-Free Beef Stew
Prep time: 15 minutes
Cook time: 1 hour
Servings: 4
Ingredients
- 2 lb beef chuck [1]
- 1 tsp Worcestershire* [3]
- 1 cup beef broth [2, 3]
Instructions
1. Brown the beef.
2. Add the broth.
3. Stir in the Worcestershire and simmer.
Notes
* Worcestershire: US Lea & Perrins is soy-free
Serve with rice.
"""


def run(browser, name):
    c, p, errors, _ = sb.open_page(browser, name)
    p.evaluate('wording.setRestrictions("no soy")')
    for job, data in [('write', {'input': 'a soup'}), ('fridge', {'input': 'chicken'}),
                      ('convert', {'source': '1 cup rice', 'extra': ''}), ('like', {'source': '1 cup rice'})]:
        req = p.evaluate('([j,d])=>wording.request(j,d)', [job, data])
        assert 'Follow them silently' in req, (job, req)
        assert "don't label ingredient lines" in req, job
        assert 'no brand names' in req and '"1 tsp Worcestershire* [3]"' in req and 'Only add a * when you wrote a note' in req, job
        assert 'brand notes marked with *' in req, job
    req = p.evaluate('wording.request("write",{input:"a soup"})')
    assert "ask me whether to keep it as asked" in req, 'conflict rule for fridge/write kept'

    item = p.evaluate('wording.parse(arguments[0])' if False else '(a)=>wording.parse(a)', ANSWER)
    assert '1 tsp Worcestershire*' in item['ingredients'], item['ingredients']
    assert not any('[' in line for line in item['ingredients']), 'step tags removed from lines'
    tags = item.get('aiStepTags') or {}
    assert any('worcestershire' in k.lower() and v == [3] for k, v in tags.items()), tags
    notes = item.get('notes') or ''
    assert 'Worcestershire: US Lea & Perrins is soy-free' in notes and 'Serve with rice' in notes, notes

    assert p.evaluate('wording.grocery("1 tsp Worcestershire*")') == '1 tsp Worcestershire'
    assert p.evaluate('wording.grocery("1 tsp Worcestershire* (brand note)")') == '1 tsp Worcestershire'
    assert p.evaluate('wording.grocery("2 carrots, diced")') == '2 carrots'
    assert not errors, errors
    c.close()
    print(name, 'ok')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ['index.html', 'meal-rotation-test.html']:
        run(b, n)
    b.close()
