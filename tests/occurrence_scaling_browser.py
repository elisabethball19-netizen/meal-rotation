"""Occurrence-specific scaling, partial checked quantities and legacy/backup compatibility."""
import json
from playwright.sync_api import sync_playwright
import remaining_meal_features_browser as base
f=base.f
f.EXTRA+='''window.scalingTest={
 seed:()=>{remainingTest.seed();cookingSessions={version:1,occurrences:{}};occurrenceScales={version:1,occurrences:{}};writeOccurrenceScales(occurrenceScales);groceryOccurrenceChecks={version:1,checks:{}};meals.find(m=>m.id===537).ingredients=['3 lb pork','Salt to taste'];meals.find(m=>m.id===22).ingredients=['2 cups broth'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));persist()},
 open:(cat='Weekend',day='Saturday',planId=activePlanId)=>{const e=getDisplayedWeekdayMealsForPlan(mealPlans.find(p=>p.id===planId)).find(e=>e.day===day&&e.cat===cat);openTopMealActionMenu(day,e.cat,e.meal);[...document.querySelectorAll('[role="dialog"] button')].find(b=>b.textContent==='Open recipe').click()},
 library:()=>openRecipeViewer(meals.find(m=>m.id===537)),
 multiplier:()=>recipeViewer.context?occurrenceMultiplier(recipeViewer.context):recipeViewer.previewScale,
 context:()=>recipeViewer.context,
 scale:value=>setViewedRecipeScale(value),
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s),amount:groceryCheckedAmount(s)})),
 groceries:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,quantity:item.quantity,checked:groceryItemChecked(key,item)})),
 check:(want,checked=true)=>{for(const [key,item]of getMasterGroceryItems())if(item.line.includes(want))setGroceryItemChecked(key,item,checked);saveGroceryOccurrenceChecks()},
 scales:()=>JSON.parse(JSON.stringify(occurrenceScales)),
 ingredients:()=>meals.find(m=>m.id===537).ingredients,
 legacy:()=>{const c=cookingContext('original','Saturday','Weekend',meals.find(m=>m.id===537));writeOccurrenceScales({version:1,occurrences:{[cookingOccurrenceKey(c)]:{context:c,multiplier:2}}})},
 backup:()=>{persist();return captureBackupStorage()},
 restore:saved=>{validateBackupStorage(saved);restoreBackupStorage(saved)},
 replace:()=>applyManualWeekdayMeal('Saturday','Weekend',meals.find(m=>m.id===22)),
 readd:()=>applyManualWeekdayMeal('Saturday','Weekend',meals.find(m=>m.id===537)),
 linked:assigned=>{scalingTest.seed();meals.find(m=>m.id===537).linkedMealIds=[25];meals.find(m=>m.id===25).ingredients=['2 cups rice'];if(assigned)setDayCategories('Saturday',['Weekend','Breakfast','Lunch','Bread']);localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));persist()},
 side:()=>{const m=meals.find(m=>m.id===25);openLinkedRecipeTab(m)},
 customRaw:value=>setViewedRecipeScale(value),
 once:()=>saveOneTimeMeal('Saturday','Breakfast','One-time snack',['1 cup berries']),
 rename:()=>renameCategoryDirect('Weekend'),
 exclude:()=>masterGroceryExcludedPlanIds.add('second'),
 extra:()=>{meals.find(m=>m.id===22).ingredients=['1 kg pork','1–2 cups stock','Pepper to taste'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));persist()},
 resume:()=>resumeWeekSlot('Saturday','Weekend'),
 hideSide:()=>leaveWeekEmpty('Saturday','Bread'),
 restoreSide:()=>restoreHiddenLinkedSide('Saturday','Weekend',meals.find(m=>m.id===537),25),
 clear:()=>leaveWeekEmpty('Saturday','Weekend')
};'''

def close(p):
 p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_timeout(60)

def preset(p,label,value):
 p.get_by_role('button',name='Scale Recipe',exact=True).click()
 p.get_by_role('menuitemradio',name=label,exact=True).click()
 assert p.evaluate('scalingTest.multiplier()')==value

def custom(p,value):
 p.get_by_role('button',name='Scale Recipe',exact=True).click()
 p.get_by_role('spinbutton',name='Custom multiplier',exact=True).fill(str(value))
 p.get_by_role('button',name='Apply multiplier',exact=True).click()
 assert p.evaluate('scalingTest.multiplier()')==float(value)

def pork(p,checked=None):
 return sum(x['quantity']['lo'] for x in p.evaluate('scalingTest.groceries()') if x['quantity'] and 'pork' in x['line'] and (checked is None or x['checked']==checked))

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('scalingTest.seed();scalingTest.open()')
 assert p.evaluate('scalingTest.multiplier()')==1
 for label,v in [('½×',.5),('1×',1),('1½×',1.5),('3×',3)]:
  preset(p,label,v);assert pork(p)==3*v
  assert p.locator('.recipe-viewer-ingredients .cooking-item').filter(has_text='pork').first.inner_text() in {0.5:'1½ lb pork',1:'3 lb pork',1.5:'4½ lb pork',3:'9 lb pork'}.get(v,'')
 for v in [.75,2.25]:
  custom(p,v);assert pork(p)==3*v
  p.get_by_role('button',name='Scale Recipe',exact=True).click();assert p.get_by_role('spinbutton',name='Custom multiplier').input_value()==str(v)
  assert not p.locator('.recipe-scale-option[aria-checked="true"]').count()
  p.keyboard.press('Escape');close(p);p.evaluate('scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==v
 # Invalid custom values never alter existing multiplier or schedules.
 p.get_by_role('button',name='Scale Recipe',exact=True).click()
 for v in ['0','-1','']:
  p.get_by_role('spinbutton',name='Custom multiplier').fill(v);p.get_by_role('button',name='Apply multiplier').click();assert p.evaluate('scalingTest.multiplier()')==2.25
 p.get_by_role('spinbutton',name='Custom multiplier').evaluate('(e)=>{e.value="not-a-number"}')
 p.get_by_role('button',name='Apply multiplier').click();assert p.evaluate('scalingTest.multiplier()')==2.25
 for raw in ['NaN','Infinity','-Infinity','0','-2','"bad"','null']:assert p.evaluate('scalingTest.customRaw('+raw+')') is False
 p.keyboard.press('Escape');close(p)
 # Numeric keyboard viewport keeps the custom control available.
 p.evaluate('combinedTest.viewport();scalingTest.open()');p.get_by_role('button',name='Scale Recipe',exact=True).click();field=p.get_by_role('spinbutton',name='Custom multiplier');field.focus();p.evaluate('combinedTest.resize(360,0)');assert field.is_visible();field.fill('0.75');p.get_by_role('button',name='Apply multiplier').click();assert p.evaluate('scalingTest.multiplier()')==.75;p.evaluate('combinedTest.resize(800,0)');close(p)
 # Duplicate same-day group slots have independent definite viewer contexts.
 p.evaluate('scalingTest.seed();remainingTest.duplicate();scalingTest.open()');preset(p,'½×',.5);close(p)
 p.evaluate('scalingTest.open("Lunch")');assert p.evaluate('scalingTest.context().cat')=='Lunch' and p.evaluate('scalingTest.multiplier()')==1
 preset(p,'2×',2);assert pork(p)==7.5;close(p);p.evaluate('scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==.5;close(p)
 original=p.evaluate('scalingTest.ingredients()');p.reload();p.evaluate('promotionTest.my();scalingTest.open("Lunch")');assert p.evaluate('scalingTest.multiplier()')==2;close(p)
 saved=p.evaluate('scalingTest.backup()');p.evaluate('scalingTest.restore',saved);p.reload();p.evaluate('promotionTest.my();scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==.5;close(p)
 # Standalone previews neither read nor overwrite scheduled scales.
 before=p.evaluate('scalingTest.scales()');p.evaluate('scalingTest.library()');assert p.evaluate('scalingTest.context()') is None and p.evaluate('scalingTest.multiplier()')==1
 custom(p,.75);close(p);assert p.evaluate('scalingTest.scales()')==before and p.evaluate('scalingTest.ingredients()')==original
 # Increasing checked quantities splits already checked versus newly required amounts.
 p.evaluate('scalingTest.seed();scalingTest.check("pork");scalingTest.open()');preset(p,'2×',2);assert pork(p,True)==3 and pork(p,False)==3
 custom(p,2.25);assert pork(p,True)==3 and pork(p,False)==3.75
 p.evaluate('scalingTest.check("pork")');assert pork(p,True)==6.75 and pork(p,False)==0
 preset(p,'½×',.5);assert pork(p,True)==1.5
 preset(p,'2×',2);assert pork(p,True)==1.5 and pork(p,False)==4.5
 close(p);p.reload();assert pork(p,True)==1.5 and pork(p,False)==4.5
 saved=p.evaluate('scalingTest.backup()');p.evaluate('scalingTest.restore',saved);p.reload();assert pork(p,True)==1.5 and pork(p,False)==4.5
 p.evaluate('scalingTest.clear();scalingTest.resume()');assert pork(p,True)==1.5 and pork(p,False)==4.5
 p.evaluate('scalingTest.check("pork",false)');assert pork(p,True)==0
 # Other ingredient checks and independent occurrences are retained.
 p.evaluate('scalingTest.seed();remainingTest.duplicate();remainingTest.sunday();remainingTest.anotherTab();scalingTest.check("pork");scalingTest.open()');preset(p,'2×',2);assert pork(p,True)==12 and pork(p,False)==3
 close(p);p.evaluate('scalingTest.exclude()');assert pork(p)==12
 p.evaluate('scalingTest.clear()');assert pork(p)==6
 # Replacing/removing a slot cannot leak scale to its next occurrence.
 p.evaluate('scalingTest.seed();remainingTest.duplicate();scalingTest.open("Lunch")');preset(p,'3×',3);close(p);p.evaluate('scalingTest.open()');preset(p,'2×',2);close(p)
 p.evaluate('scalingTest.replace();scalingTest.readd();scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==1;close(p)
 p.evaluate('scalingTest.open("Lunch")');assert p.evaluate('scalingTest.multiplier()')==3;close(p)
 p.evaluate('sameDay.forward();sameDay.back();scalingTest.open("Lunch")');assert p.evaluate('scalingTest.multiplier()')==1;close(p)
 # Linked sides stay at 1x unless changed separately, including assigned groups.
 for assigned in [False,True]:
  p.evaluate('scalingTest.linked',assigned);p.evaluate('scalingTest.open()');preset(p,'2×',2)
  p.evaluate('scalingTest.side()');assert p.evaluate('scalingTest.multiplier()')==1
  p.evaluate('scalingTest.check("rice")');preset(p,'1½×',1.5);rice=[s for s in p.evaluate('scalingTest.sources()') if str(s['mealId'])=='25'];assert len(rice)==1 and rice[0]['quantity']['lo']==3
  close(p);p.evaluate('scalingTest.hideSide();scalingTest.restoreSide()');rice=[r for r in p.evaluate('scalingTest.groceries()') if r['quantity'] and 'rice' in r['line']];assert sum(r['quantity']['lo'] for r in rice if r['checked'])==2 and sum(r['quantity']['lo'] for r in rice if not r['checked'])==1
  p.evaluate('scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==2;close(p)
 # Incompatible units remain separate; ranges use existing conservative parsing.
 p.evaluate('scalingTest.seed();scalingTest.extra();scalingTest.replace();scalingTest.open()');preset(p,'2×',2);g=p.evaluate('scalingTest.groceries()');assert any(x['line']=='2 kg pork' for x in g) and any(x['line']=='2–4 cups stock' for x in g) and any(x['line']=='Pepper to taste' for x in g);close(p)
 # A temporary meal's groceries and check state are unaffected by scaling a recipe.
 p.evaluate('scalingTest.seed();scalingTest.once();scalingTest.check("berries");scalingTest.open()');preset(p,'3×',3);assert any(r['line']=='1 cup berries' and r['checked'] for r in p.evaluate('scalingTest.groceries()'));close(p)
 # Group rename preserves the scale identity and grocery amounts.
 p.evaluate('scalingTest.rename()');p.get_by_role('textbox').fill('Dinner');p.get_by_role('button',name='Save',exact=True).click();p.wait_for_timeout(50);p.evaluate('scalingTest.open("Dinner")');assert p.evaluate('scalingTest.multiplier()')==3;close(p)
 # Legacy preset scale applies only to its recorded group, not a new duplicate.
 p.evaluate('scalingTest.seed();scalingTest.legacy();remainingTest.duplicate()');p.reload();p.evaluate('promotionTest.my();scalingTest.open()');assert p.evaluate('scalingTest.multiplier()')==2
 custom(p,.75);close(p);p.evaluate('scalingTest.open("Lunch")');assert p.evaluate('scalingTest.multiplier()')==1;close(p)
 p.evaluate('promotionTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'presets/custom/invalid, independent duplicates, viewer/reload/backup, grocery totals/checked increments, linked sides, legacy/library isolation, removal/rotation/back, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
