"""Approved #123 correction pass: synthetic 457-recipe and explicit source fixtures."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import import_settings_batch123_browser as base
fixture=base.fixture
fixture.HOOK+='''window.correction123={
 large:()=>Array.from({length:457},(_,i)=>({name:'Collection '+i+' — a long descriptive recipe name for realistic phone wrapping',identifier:'review-'+i,recipeCategory:i%3===0?['Side dish','Vegetables '+(i%35)]:['Main dish','Collection group '+(i%70)],recipeIngredient:['1 cup rice'],recipeInstructions:[{type:'step',text:'Cook rice for 20 minutes.'}],prepTime:'PT10M',cookTime:'PT20M',totalTime:'PT30M'})),
 collection:()=>showRecipeImportSelection(correction123.large(),'recipesage-export-hash-abcdefghijklmnopqrstuvwxyz0123456789.jsonld'),
 empty:tabs=>{cats=['Meals','Sides'];meals=[];active='Meals';mealPlans=[{id:'original',name:'Dinner',weekdayCategories:{Monday:['Meals'],Tuesday:['Meals']},weekdayMealOverrides:{},weekdayRecipeFilters:{},pinnedCats:[]}];if(tabs)mealPlans.push({...JSON.parse(JSON.stringify(mealPlans[0])),id:'lunch',name:'Lunch'});activePlanId='original';weekdayCategories=JSON.parse(JSON.stringify(mealPlans[0].weekdayCategories));weekdayMealOverrides={};weekdayRecipeFilters={};showMealPlanTabs=tabs;showTop=true;groceryTabActive=false;allMealsActive=false;firstRecipePromptShown=true;persist();saveActiveMealPlan();render()},
 parse:extractCompleteRecipe,complete:completeRecipeFields
};'''
OUT=Path('/workspace/work/screenshots123-correction');OUT.mkdir(exist_ok=True)
def run(b,name):
 c,p,errors,prefix=fixture.setup(b,name);p.set_default_timeout(10000)
 # Controlled source payloads, not the unavailable user-tested URL.
 structured={'@context':'https://schema.org','@type':'Recipe','name':'Fixture stew','recipeIngredient':['2 cups lentils','1 tbsp oil'],'recipeInstructions':[{'@type':'HowToSection','name':'Cook','itemListElement':[{'@type':'HowToStep','text':'Simmer lentils.'}]}],'prepTime':'PT15M','cookTime':'PT45M','totalTime':'PT1H'}
 variants=[('<script type="application/ld+json">'+json.dumps(structured)+'</script>',15,45,60),('<script type="application/ld+json">'+json.dumps({**structured,'recipeIngredient':[]})+'</script><ul class="ingredient-list"><li>2 cups lentils</li><li>1 tbsp oil</li></ul>',15,45,60),('<article itemscope itemtype="https://schema.org/Recipe"><h1 itemprop="name">Micro stew</h1><span itemprop="recipeIngredient">2 cups lentils</span><span itemprop="recipeIngredient">1 tbsp oil</span><time itemprop="prepTime" datetime="PT15M">15 minutes</time><time itemprop="cookTime" datetime="PT45M">45 minutes</time><time itemprop="totalTime" datetime="PT1H">1 hour</time><p itemprop="recipeInstructions">Simmer lentils.</p></article>',15,45,60)]
 mixed={key:value for key,value in structured.items()if key not in ['recipeIngredient','prepTime','cookTime','totalTime']}
 variants.append(('<script type="application/ld+json">'+json.dumps(mixed)+'</script>'+variants[2][0].replace('Micro stew','Fixture stew'),15,45,60))
 for index,(html,prep,cook,total)in enumerate(variants):
  url='https://source-fixture.test/stew-'+str(index);p.route(url,lambda route,request,html=html:route.fulfill(status=200,body=html))
  before=len(p.evaluate('spec123.records()'));p.evaluate("spec123.import('website')");d=base.popup(p);d.get_by_role('textbox',name='Website link',exact=True).fill(url);base.review(p)
  assert p.locator('#ingredients').input_value().splitlines()==['2 cups lentils','1 tbsp oil'];assert p.locator('#prep').input_value()=='15m';assert p.locator('#totaltime').input_value()=='1h';assert 'Simmer lentils.'in p.locator('#recipeInstructions').input_value()
  p.screenshot(path=str(OUT/(name+'-source-review-'+str(index)+'.png')))
  if index==0:
   p.locator('#editorIngredientsSection').evaluate('(e)=>e.open=true');p.locator('#ingredients').scroll_into_view_if_needed();p.screenshot(path=str(OUT/(name+'-source-ingredients.png')))
   p.locator('#editorInstructionsSection').evaluate('(e)=>e.open=true');p.locator('#recipeInstructions').scroll_into_view_if_needed();p.screenshot(path=str(OUT/(name+'-source-steps.png')))
  if index==1:base.cancel_editor(p);assert len(p.evaluate('spec123.records()'))==before;continue
  p.locator('#save').click();record=next(r for r in p.evaluate('spec123.records()')if r.get('url')==url);assert record['ingredients']==['2 cups lentils','1 tbsp oil'] and float(record['prep'])==prep and float(record['cook'])==cook and float(record['total'])==total
  p.evaluate('id=>batch1.editor(id)',record['id']);assert p.locator('#ingredients').input_value().splitlines()==record['ingredients'];assert p.locator('#prep').input_value()=='15m';base.cancel_editor(p)
 # No precise time invented when retrieved data omits it; warning visible in review.
 url='https://source-fixture.test/partial';p.route(url,lambda route:route.fulfill(status=200,body='<script type="application/ld+json">'+json.dumps({'@type':'Recipe','name':'Partial','recipeInstructions':['Cook until done.']})+'</script>'))
 p.evaluate("spec123.import('website')");base.popup(p).get_by_role('textbox',name='Website link',exact=True).fill(url);base.review(p);assert p.locator('.import-missing-fields').count()==1 and p.locator('#prep').input_value()=='';base.cancel_editor(p)
 assert p.get_by_role('button',name='Refresh from RecipeSage',exact=True).count()==0
 assert p.evaluate('typeof buildRecipeSageRefresh')=='undefined' and p.evaluate('typeof openRecipeSageRefresh')=='undefined'
 # Full 457-recipe mapping/Sides flow. Header/footer remain outside the single scroller.
 before=p.evaluate('spec123.state()');p.evaluate('correction123.collection()');d=p.get_by_role('dialog',name='Choose meal groups',exact=True)
 assert d.get_by_text('457 recipes found. Choose which groups to import.',exact=True).count()==1 and '.jsonld'not in d.inner_text()
 assert d.locator('.import-side-review input').count()==153
 d.get_by_role('button',name='Select all groups',exact=True).click();d.get_by_role('button',name='Deselect all groups',exact=True).click()
 # Both view states are reviewed at each viewport, including actual bottom-side choices.
 for w,h,size in [(360,800,'normal'),(320,640,'extra'),(740,360,'extra'),(360,360,'extra')]:
  p.set_viewport_size({'width':w,'height':h});p.evaluate('size=>document.body.dataset.mealTextSize=size',size);body=d.locator('.bulk-import-body')
  for position in ['top','bottom']:
   body.evaluate('(e,p)=>e.scrollTop=p==="top"?0:e.scrollHeight',position);p.screenshot(path=str(OUT/(name+f'-bulk-{w}-{h}-{position}.png')))
   geometry=d.evaluate('(d)=>{const panel=d.firstElementChild,h=panel.firstElementChild.getBoundingClientRect(),a=panel.lastElementChild.getBoundingClientRect(),body=panel.querySelector(".bulk-import-body").getBoundingClientRect();return {top:h.top,bottom:a.bottom,contentTop:body.top,contentBottom:body.bottom,footerTop:a.top,headerBottom:h.bottom,viewport:innerHeight}}')
   assert geometry['top']>=0 and geometry['bottom']<=h and geometry['contentBottom']<=geometry['footerTop'] and geometry['contentTop']>=geometry['headerBottom'],geometry
  d.locator('.import-side-review input').last.check();assert d.locator('.import-side-review input').last.is_checked()
 p.go_back();p.wait_for_timeout(150);assert not d.count()and p.evaluate('spec123.state()')==before
 p.set_viewport_size({'width':360,'height':800});p.evaluate('correction123.collection()');d=p.get_by_role('dialog',name='Choose meal groups',exact=True);d.locator('.bulk-import-body').evaluate('(e)=>e.scrollTop=e.scrollHeight');p.screenshot(path=str(OUT/(name+'-before-confirm.png')));d.locator('.import-side-review input').last.check();d.get_by_role('button',name='Import recipes',exact=True).click();p.get_by_role('button',name='OK',exact=True).click();records=p.evaluate('spec123.records()');assert len([r for r in records if r.get('importSourceId','').startswith('review-')])==457;assert len([r for r in records if r.get('importSourceId','').startswith('review-')and r['cat']=='Sides'])==1
 p.screenshot(path=str(OUT/(name+'-large-confirmed.png')));p.evaluate('spec123.undo()');assert p.evaluate('spec123.state()')==before;p.evaluate('spec123.redo()');assert len([r for r in p.evaluate('spec123.records()')if r.get('importSourceId','').startswith('review-')])==457
 # Empty-app launcher: tabs shown/hidden, banner retained, first card clear of button.
 for tabs in [False,True]:
  p.evaluate('tabs=>correction123.empty(tabs)',tabs)
  for w,h in [(360,800),(320,640),(740,360)]:
   p.set_viewport_size({'width':w,'height':h});p.screenshot(path=str(OUT/(name+f'-empty-{tabs}-{w}.png')))
   box=p.locator('.first-recipe-launcher').bounding_box();card=p.locator('.plan-day-row').first
   if card.count():assert card.bounding_box()['y']>=box['y']+box['height']+10
   assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'source hydration, 457-recipe full mapping/Sides/confirm/cancel/Undo, no refresh, empty mobile layouts')
if __name__=='__main__':
 with sync_playwright()as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
