"""v431 website import fixes (v430 phone test item 5, askchefdennis coleslaw).
Run: python3 -m http.server 8765 (repo root), then python3 tests/website_import_v431_browser.py
Optional BASE env var (default http://localhost:8765). Checks index.html and meal-rotation-test.html.
Fixtures are synthetic but follow the real page's shape: an article 'Ingredients' photo section followed by an
'Ingredient Substitutions' list, a WP Recipe Maker card, and ad lines between steps."""
import asyncio, os, json
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'http://localhost:8765')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'
URL = 'https://www.example.com/best-coleslaw/'

MARKDOWN = """Title: Best Coleslaw

URL Source: https://www.example.com/best-coleslaw/

Markdown Content:
# Best Coleslaw

## Ingredients

![Ingredients to make the recipe.](data:image/svg+xml,abc)

Let's start by gathering the ingredients.

## Ingredient Substitutions

* Replace apple cider vinegar with white vinegar for a different tang.
* Swap granulated sugar for honey if you prefer.
* Add Dijon mustard for extra zip.

## More Recipes You'll Love!

1. Warm the tortillas in a dry skillet for 20 seconds per side until pliable and soft.
2. Fry the fish until golden and crisp, then add it to the tortillas.

## Best Coleslaw

Servings [8](https://www.example.com/best-coleslaw/#)

### Ingredients US CustomaryMetric .5x1x2x

* 1 small cabbage shredded
* 1 large carrot shredded
* 1 cup mayonnaise
* 2 tablespoon apple cider vinegar

### WANT TO SAVE THIS RECIPE?

Enter your email below.

### Instructions

* Cut the cabbage in half and remove the core.
![](data:image/svg+xml;base64,AAA)Report Ad
[What is this?](https://www.mediavine.com/?utm_source=mediavine)
* Combine mayonnaise and vinegar, then pour over the cabbage and mix well.

### Notes

Better after a day.

### Nutrition

Calories 246
"""

HTML = """<!doctype html><html><head><link rel="canonical" href="https://www.example.com/best-coleslaw/"></head><body>
<h1>Best Coleslaw</h1><h2>Ingredient Substitutions</h2><ul><li>Replace apple cider vinegar with white vinegar.</li></ul>
<div class="wprm-recipe-container"><h2 class="wprm-recipe-name">Best Coleslaw</h2>
<div class="wprm-recipe-servings-container"><span class="wprm-recipe-servings-label">Servings</span>
<span class="wprm-recipe-servings">8</span><span class="wprm-recipe-servings-unit">servings</span></div>
<ul><li class="wprm-recipe-ingredient">1 small cabbage shredded</li><li class="wprm-recipe-ingredient">1 cup mayonnaise</li></ul>
<div class="wprm-recipe-instructions-container"><ul><li>Cut the cabbage in half and remove the core.</li>
<li>Combine mayonnaise and vinegar, then pour over the cabbage and mix well.</li></ul></div></div></body></html>"""

async def check(page_name, browser):
    pg = await browser.new_page(viewport={'width': 390, 'height': 844})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    closure = page_name == 'meal-rotation-test.html'
    if closure:
        src = open(os.path.join(ROOT, page_name), encoding='utf-8').read()
        assert src.count(END) == 1
        src = src.replace(END, 'showAppMessage(builtinSidesMigrationNotice),0);window.__t=c=>eval(c);})();')
        await pg.route(f'**/{page_name}', lambda r: r.fulfill(status=200, content_type='text/html', body=src))
    async def ev(js, arg=None):
        if closure:
            return await pg.evaluate('([c,a])=>window.__t("("+c+")")(a)', [js, arg])
        return await pg.evaluate(js, arg)
    await pg.goto(f'{BASE}/{page_name}'); await pg.wait_for_timeout(1200)

    # Plain-text (reader) version: real card ingredients, card steps only, servings, marked text-only.
    r = await ev("""t=>{const d=extractCompleteRecipe(t,'%s','');return {ing:d.ingredients,steps:d.instructions.filter(b=>b.type==='step').map(b=>b.text),servings:d.servings,textOnly:d.textOnly}}""" % URL, MARKDOWN)
    assert r['ing'] == ['1 small cabbage shredded', '1 large carrot shredded', '1 cup mayonnaise', '2 tablespoon apple cider vinegar'], r
    assert len(r['steps']) == 2 and r['steps'][0].startswith('Cut the cabbage') and r['steps'][1].startswith('Combine mayonnaise'), r
    assert not any('tortilla' in s.lower() or 'report ad' in s.lower() or 'what is this' in s.lower() for s in r['steps']), r
    assert r['servings'] == 8 and r['textOnly'] is True, r

    # Full page (HTML): WP Recipe Maker servings, not text-only.
    r = await ev("""h=>{const d=extractCompleteRecipe(h,'%s','');return {ing:d.ingredients,servings:d.servings,textOnly:!!d.textOnly}}""" % URL, HTML)
    assert r['ing'] == ['1 small cabbage shredded', '1 cup mayonnaise'] and r['servings'] == 8 and r['textOnly'] is False, r
    r = await ev("""()=>{const doc=new DOMParser().parseFromString('<div class="wprm-recipe-container"><span class="wprm-recipe-servings">12</span><span class="wprm-recipe-servings-unit">cookies</span></div>','text/html');
      const t=document.createElement('div');t.innerHTML='<div class="tasty-recipes-yield">Yield: 6 servings</div>';const m=document.createElement('div');m.innerHTML='<p class="mv-create-yield">Serves 4</p>';
      return [recipeImportServings(recipeCardServingsText(doc.body)),recipeImportServings(recipeCardServingsText(t)),recipeImportServings(recipeCardServingsText(m))]}""")
    assert r == ['', 6, 4], r
    r = await ev("""()=>[recipeTextServings('Servings [8](#)'),recipeTextServings('Serves: 4'),recipeTextServings('Yield: 6 servings'),recipeTextServings('Yield: 12 cookies'),recipeTextServings('no servings here')]""")
    assert r == [8, 4, 6, '', ''], r

    # Regressions: pasted plain text and recipe cards with sub-sections still parse.
    r = await ev("""()=>{const a=recipeTextSections('My soup\\nIngredients\\n- 1 onion\\nInstructions\\n1. Chop the onion finely.\\n2. Simmer for 20 minutes.\\nNotes\\nFreezes well.');
      const b=recipeTextSections('### Instructions\\n#### For the sauce\\n1. Whisk the sauce together.\\n#### For the fish\\n2. Fry the fish until crisp.\\n### Nutrition\\nCalories 100');
      const c=recipeIngredientsFromMarkdown('## Ingredients\\n### For the dressing\\n- 1 cup mayonnaise\\n- 2 tbsp vinegar\\n## Instructions\\n1. Mix.');
      const step=x=>x.instructions.filter(s=>s.type==='step').map(s=>s.text);return {a:step(a),notes:a.notes,b:step(b),c}}""")
    assert r['a'] == ['Chop the onion finely.', 'Simmer for 20 minutes.'] and 'Freezes well' in r['notes'], r
    assert r['b'] == ['Whisk the sauce together.', 'Fry the fish until crisp.'], r
    assert r['c'] == ['1 cup mayonnaise', '2 tbsp vinegar'], r

    # Which reader wins, and the warning. fetch is stubbed: direct site blocked, allorigins = HTML or failing, jina = text.
    for mode in ('html', 'textonly'):
        r = await ev("""async ([md,html,mode])=>{const real=window.fetch;
          window.fetch=async u=>{u=String(u);if(u.includes('r.jina.ai'))return new Response(md);if(u.includes('allorigins')){if(mode==='html')return new Response(html);return new Response('',{status:500})}throw new TypeError('Failed to fetch')};
          try{const lines=await importIngredientsFromWebsite('%s');return {lines:[...lines],textOnly:!!lines.textOnly,warning:websiteImportWarning(lines),servings:lines.recipeDetails?.servings}}finally{window.fetch=real}}""" % URL, [MARKDOWN, HTML, mode])
        if mode == 'html':
            assert r['textOnly'] is False and r['warning'] == '' and r['lines'] == ['1 small cabbage shredded', '1 cup mayonnaise'] and r['servings'] == 8, r
        else:
            assert r['textOnly'] is True and 'plain text' in r['warning'] and r['lines'][0] == '1 small cabbage shredded' and r['servings'] == 8, r
    assert not errors, errors
    await pg.close()
    print('PASS', page_name)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name in ('index.html', 'meal-rotation-test.html'):
            await check(name, b)
        await b.close()
asyncio.run(main())
