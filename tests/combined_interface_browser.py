"""Focused interface batch checks in disposable mobile contexts; both existing apps."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as base
ROOT=Path(__file__).resolve().parents[1]
base.HOOK+='''window.interfaceTest={
 largeText:()=>{mealTextSize='large';applyMealTextSize()},seed:()=>{
  const by=id=>meals.find(m=>m.id===id);
  assignSharedRecipeFields(by(2),{name:'Tacos de Adobada Northern Style',lastCooked:'2026-10-09T12:00:00.000Z'});
  by(3).name='Al Pastor';by(4).name='Epic Baja Fish Tacos with Avocado Crema';by(5).name='Fish Tacos Recipe with Best Fish Taco Sauce!';by(6).name='Chicken';by(5).prep=10;by(5).total=20;
  by(1).needsTweaking=true;by(1).needsTweakingNote='Old adjustment note';by(1).notes='Ordinary recipe notes stay separate.';
  by(1).linkGroup='owner';by(1).linkedMealIds=[12,8];meals.push({...JSON.parse(JSON.stringify(by(1))),id:21,cat:'Reference'});
  meals.push({id:20,name:'Unassigned Salsa',cat:'',rotation:false,upNextStar:false,ingredients:['tomato'],instructions:'Chop tomato.'});
  for(let id=30;id<55;id++)meals.push({id,name:'Reference recipe '+id,cat:'Reference',rotation:false,upNextStar:false,ingredients:[],instructions:[]});
  const tokens=recipeAssociationItems(by(1));by(1).ingredientStepLinks=[{step:tokens.steps[0].token,ingredients:[tokens.ingredients[0].token]}];
  const flags=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');flags[groupIdentity('Reference',true)]=false;localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify(flags));persist();render();
 },
 viewer:id=>openSavedMealRecipe(meals.find(m=>m.id===id)),note:id=>openNeedsTweaking(meals.find(m=>m.id===id)),
 linkedDraft:()=>$('editLinkedMeals').readDraft(),draftLinks:()=>$('recipeIngredientLinks').captureRecoveryDraft(),
 main:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;render()},
 associations:id=>validRecipeIngredientLinks(meals.find(m=>m.id===id))
};'''
def setup(browser,name,width=360):
 c,p,errors,prefix=base.setup(browser,name,width);p.evaluate('interfaceTest.seed()');base.get(p,'groups()');return c,p,errors,prefix

def rows(browser,name,width):
 c,p,errors,prefix=setup(browser,name,width)
 p.evaluate('interfaceTest.largeText()')
 data=p.locator('[data-category="Meals"] .master-category-meal[data-up-next-star]').evaluate_all('''xs=>xs.map(row=>{const box=x=>{const b=x.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom}};const name=row.querySelector('.master-category-meal-name'),range=document.createRange();range.selectNodeContents(name);const line=range.getClientRects()[0];return {id:Number(row.dataset.mealId),row:box(row),star:box(row.querySelector(':scope>.recipe-up-next-star')),svg:box(row.querySelector(':scope>.recipe-up-next-star svg')),info:box(row.querySelector('.master-meal-info')),arrow:box(row.querySelector('.recipe-section-move')),firstLine:{y:line.y,height:line.height},details:[...row.querySelectorAll('.meal-last-cooked,.times')].filter(x=>x.textContent.trim()).map(box)}})''')
 assert len(data)==5
 for item in data:
  assert item['star']['right']<=item['info']['x'] and item['info']['right']<=item['arrow']['x']
  assert item['arrow']['right']<=width and item['row']['right']<=width
  assert abs(item['svg']['y']+item['svg']['height']/2-(item['firstLine']['y']+item['firstLine']['height']/2))<=7,item
  assert item['star']['height']>=44 and item['arrow']['height']>=44
  for detail in item['details']:assert detail['y']>=item['firstLine']['y']+item['firstLine']['height']-1
 assert next(x for x in data if x['id']==3)['row']['height']<=49
 assert max(item['row']['height'] for item in data)<125
 assert p.locator('[data-category="Meals"] [data-recipe-section="up-next"]>.master-category-group-label').inner_text().startswith('Ideas')
 assert not p.get_by_text('Up Next',exact=True).count()
 p.screenshot(path='/workspace/work/interface-ideas-'+name+'-'+str(width)+'.png')
 # Star and direct arrows keep data semantics and fixed placement.
 row=base.row(p,2);row.get_by_role('button',name='Unstar Tacos de Adobada Northern Style',exact=True).tap();assert not base.record(p,2)['upNextStar'] and not base.record(p,12)['upNextStar']
 row=base.row(p,2);row.get_by_role('button',name='Star Tacos de Adobada Northern Style',exact=True).tap();assert base.record(p,12)['upNextStar']
 schedule=base.get(p,'schedule()');row=base.row(p,2);row.get_by_role('button',name='Move Tacos de Adobada Northern Style to In Rotation',exact=True).tap();assert base.record(p,2)['rotation'] and base.get(p,'schedule()')==schedule
 base.row(p,2).get_by_role('button',name='Move Tacos de Adobada Northern Style to Ideas',exact=True).tap();assert not base.record(p,2)['rotation']
 assert not errors,errors;c.close();print('PASS',name,width,'Ideas star/title/action geometry, compact long/short rows and metadata, wording, star taps and direct arrows',flush=True)

def linked(browser,name):
 c,p,errors,prefix=setup(browser,name);before=base.get(p,'records()');base.get(p,'editor(1)')
 def open_dialog():
  p.get_by_role('button',name='Edit linked recipes',exact=True).tap();return p.get_by_role('dialog',name='Select Linked Recipes',exact=True)
 d=open_dialog();headers=d.locator('.meal-editor-group-heading');assert headers.count()==4 and headers.evaluate_all('(xs)=>xs.every(x=>x.getAttribute("aria-expanded")==="false")')
 assert d.get_by_role('button',name='Reference',exact=True).count() and d.get_by_role('button',name='Unassigned',exact=True).count()
 assert not d.get_by_role('checkbox').count();assert 'Active' not in d.locator('.meal-linked-dialog-options').inner_text()
 assert p.evaluate('document.body.style.overflow')=='hidden'
 p.screenshot(path='/workspace/work/interface-linked-collapsed-'+name+'.png')
 meals=d.get_by_role('button',name='Meals',exact=True);meals.tap();check=d.get_by_role('checkbox',name='Tacos de Adobada Northern Style',exact=True);assert check.is_checked();check.uncheck();meals.tap();other=d.get_by_role('button',name='Other',exact=True);other.tap();check=d.get_by_role('checkbox',name='Tacos de Adobada Northern Style',exact=True);assert not check.is_checked();check.check();other.tap()
 search=d.get_by_role('searchbox',name='Search linked recipes',exact=True);search.fill('Tacos de Adobada');assert d.get_by_role('checkbox',name='Tacos de Adobada Northern Style',exact=True).count()==2
 assert meals.get_attribute('aria-expanded')=='true' and other.get_attribute('aria-expanded')=='true';search.fill('zz-no-match');assert d.get_by_text('No matching meals.',exact=True).is_visible();search.fill('');assert meals.get_attribute('aria-expanded')=='false' and other.get_attribute('aria-expanded')=='false'
 d.get_by_role('button',name='Unassigned',exact=True).tap();d.get_by_role('checkbox',name='Unassigned Salsa',exact=True).check();assert base.get(p,'records()')==before and p.evaluate('interfaceTest.linkedDraft()')==[12,8]
 d.get_by_role('button',name='Close without changes',exact=True).tap();assert p.evaluate('interfaceTest.linkedDraft()')==[12,8]
 d=open_dialog();assert d.locator('.meal-editor-group-heading').evaluate_all('(xs)=>xs.every(x=>x.getAttribute("aria-expanded")==="false")')
 d.get_by_role('button',name='Meals',exact=True).tap();d.get_by_role('checkbox',name='Tacos de Adobada Northern Style',exact=True).uncheck();d.get_by_role('button',name='Other',exact=True).tap();d.get_by_role('checkbox',name='Tacos de Adobada Northern Style',exact=True).last.check()
 search=d.get_by_role('searchbox',name='Search linked recipes',exact=True);search.fill('Reference recipe');list=d.locator('.meal-linked-dialog-options');list.evaluate('(x)=>x.scrollTop=x.scrollHeight');assert list.evaluate('(x)=>x.scrollTop')>0
 assert d.get_by_role('button',name='Apply linked recipes',exact=True).bounding_box()['y']<p.viewport_size['height'];search.fill('');d.get_by_role('button',name='Unassigned',exact=True).tap();d.get_by_role('checkbox',name='Unassigned Salsa',exact=True).check()
 p.screenshot(path='/workspace/work/interface-linked-'+name+'.png');d.get_by_role('button',name='Apply linked recipes',exact=True).tap();draft=p.evaluate('interfaceTest.linkedDraft()');assert set(draft)=={12,8,20} and len(draft)==3 and base.get(p,'records()')==before
 p.locator('#cancel').tap();assert base.record(p,1)['linkedMealIds']==[12,8]
 # Final editor Save commits the single logical link only after both confirmation layers.
 base.get(p,'editor(1)');d=open_dialog();d.get_by_role('button',name='Unassigned',exact=True).tap();d.get_by_role('checkbox',name='Unassigned Salsa',exact=True).check();d.get_by_role('button',name='Apply linked recipes',exact=True).tap();p.locator('#save').tap();assert set(base.record(p,1)['linkedMealIds'])=={12,8,20}
 assert len(base.get(p,'records()'))==len(before)
 for old in before:
  now=base.record(p,old['id']);assert now['cat']==old['cat'] and now.get('rotation')==old.get('rotation')
 assert not errors,errors;c.close();print('PASS',name,'linked groups collapsed per opening, shared selection sync/deduplication, reference/Unassigned, search/clear/no-match, pending confirm/cancel and foreground scrolling/lock',flush=True)

def editor(browser,name):
 c,p,errors,prefix=setup(browser,name);p.evaluate('interfaceTest.viewer(1)');p.get_by_role('button',name='Edit Recipe',exact=True).tap();d=p.get_by_role('dialog',name='Edit Recipe',exact=True)
 assert d.locator('.viewer-editor-section').count()==3
 assert d.locator('.viewer-editor-section').evaluate_all('(xs)=>xs.every(x=>x.open&&x.querySelector(".settings-chevron")&&getComputedStyle(x).backgroundColor==="rgba(0, 0, 0, 0)")')
 assert p.evaluate('document.body.style.overflow')=='hidden'
 ing=d.get_by_role('textbox',name='Ingredients',exact=True);steps=d.get_by_role('textbox',name='Steps',exact=True);notes=d.get_by_role('textbox',name='Recipe notes',exact=True)
 original=base.record(p,1);ing.fill('1 cup rice\n2 carrots');steps.fill('Cook rice.\nAdd carrots.');notes.fill('Draft notes retained through collapsing.');values=[ing.input_value(),steps.input_value(),notes.input_value()]
 for title in ['Ingredients','Steps','Recipe notes']:
  section=d.locator('.viewer-editor-section').filter(has=p.locator('summary',has_text=title));summary=section.locator('summary');summary.tap();assert not section.evaluate('(x)=>x.open');summary.tap();assert section.evaluate('(x)=>x.open')
 assert [ing.input_value(),steps.input_value(),notes.input_value()]==values
 p.evaluate('window.history.back()');p.wait_for_timeout(100);assert d.count()==1 and [ing.input_value(),steps.input_value(),notes.input_value()]==values
 p.screenshot(path='/workspace/work/interface-editor-'+name+'.png');p.set_viewport_size({'width':360,'height':420});notes.focus();assert d.get_by_role('button',name='Cancel',exact=True).is_visible();p.set_viewport_size({'width':360,'height':800})
 d.get_by_role('button',name='Cancel',exact=True).tap();assert base.record(p,1)==original and p.locator('#recipeViewer').count()==1
 p.get_by_role('button',name='Edit Recipe',exact=True).tap();d=p.get_by_role('dialog',name='Edit Recipe',exact=True);notes=d.get_by_role('textbox',name='Recipe notes',exact=True);notes.fill('Saved note after collapsing.');d.locator('.viewer-editor-section').filter(has=p.locator('summary',has_text='Recipe notes')).locator('summary').tap();d.get_by_role('button',name='Save recipe',exact=True).tap()
 assert base.record(p,1)['notes']=='Saved note after collapsing.' and base.record(p,1)['ingredientStepLinks']==original['ingredientStepLinks'] and p.locator('#recipeViewer').count()==1
 p.get_by_role('button',name='Close recipe',exact=True).tap()
 # Shared editor collapse preserves live nodes, pending upload input and ingredient-step draft state.
 base.get(p,'editor(1)');p.locator('[data-editor-section="recipe"]>summary').tap();ing=p.locator('#ingredients');p.locator('#editorIngredientsSection>summary').tap();ing.fill('1 cup rice\n3 carrots');draft=p.evaluate('interfaceTest.draftLinks()')
 p.evaluate("""()=>{const data=new DataTransfer();data.items.add(new File(['pending fixture'],'pending.png',{type:'image/png'}));document.getElementById('ingredientGalleryInput').files=data.files;window.interfaceIngredientNode=document.getElementById('ingredients')}""")
 p.locator('#editorIngredientsSection>summary').tap();p.locator('#editorIngredientsSection>summary').tap();assert ing.input_value()=='1 cup rice\n3 carrots';assert p.evaluate('interfaceIngredientNode===document.getElementById("ingredients")&&document.getElementById("ingredientGalleryInput").files[0].name==="pending.png"');assert p.evaluate('interfaceTest.draftLinks()')==draft
 p.locator('#cancel').tap();assert base.record(p,1)['ingredients']==original['ingredients']
 assert not errors,errors;c.close();print('PASS',name,'viewer and shared editor independent collapse, live drafts/files/ingredient links, text Save/Cancel, keyboard-sized viewport and recipe return',flush=True)

def needs_adjusting(browser,name):
 c,p,errors,prefix=setup(browser,name);p.evaluate('establishDatedFixtureSchedule()');base.get(p,'seedProgress()');p.evaluate('interfaceTest.main()');before=base.get(p,'records()');scheduled=base.get(p,'schedule()');associated=base.get(p,'associated()')
 # Open from the My Rotation icon, not an editor-only entry point.
 p.locator('.needs-tweaking-icon').first.tap();d=p.get_by_role('dialog',name='Needs Adjusting',exact=True);field=d.get_by_role('textbox',name='What would you change? (optional)',exact=True)
 assert p.evaluate('document.activeElement.tagName')!='TEXTAREA';assert not d.get_by_text('Edit note',exact=True).count() and not d.locator('.recipe-tweaking-header button').count()
 assert d.locator('.meal-unified-actions button').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("aria-label"))')==['Save Needs Adjusting','Remove Needs Adjusting','Cancel Needs Adjusting']
 assert p.evaluate('document.body.style.overflow')=='hidden';field.tap();assert field.evaluate('(x)=>x===document.activeElement');field.fill('Pending adjustment');d.get_by_role('button',name='Cancel Needs Adjusting',exact=True).tap();assert base.get(p,'records()')==before
 p.evaluate('interfaceTest.note(1)');d=p.get_by_role('dialog',name='Needs Adjusting',exact=True);field=d.get_by_role('textbox');field.fill('Long note '+('stir carefully; '*100));p.set_viewport_size({'width':360,'height':420});field.focus();p.screenshot(path='/workspace/work/interface-needs-keyboard-'+name+'.png');buttons=d.locator('.meal-unified-actions button').evaluate_all('(xs)=>xs.map(x=>{const b=x.getBoundingClientRect();return [b.top,b.bottom]})');assert all(a>=0 and b<=420 for a,b in buttons),buttons
 d.get_by_role('button',name='Save Needs Adjusting',exact=True).tap();assert base.record(p,1)['needsTweakingNote'].startswith('Long note') and base.record(p,1)['notes']==before[0]['notes'];assert base.get(p,'schedule()')==scheduled and base.get(p,'associated()')==associated;p.set_viewport_size({'width':360,'height':800})
 saved=base.record(p,1);p.evaluate('interfaceTest.note(1)');d=p.get_by_role('dialog',name='Needs Adjusting',exact=True);d.get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();p.get_by_role('button',name='Cancel removal',exact=False).tap();assert base.record(p,1)==saved
 d.get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();p.get_by_role('button',name='Confirm removal',exact=False).tap();assert not base.record(p,1).get('needsTweaking') and not base.record(p,1).get('needsTweakingNote');assert base.get(p,'schedule()')==scheduled and base.get(p,'associated()')==associated
 assert base.record(p,1)['rotation']==saved['rotation'] and base.record(p,1)['notes']==saved['notes'] and base.record(p,1).get('lastCooked')==saved.get('lastCooked')
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,'My Rotation Needs Adjusting immediate editing without autofocus, control order, Save/Cancel/confirmed removal, keyboard/long note and unrelated data preservation',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:rows(browser,name,width)
   linked(browser,name);editor(browser,name);needs_adjusting(browser,name)
  browser.close()
