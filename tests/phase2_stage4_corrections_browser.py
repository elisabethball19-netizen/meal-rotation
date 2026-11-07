"""Stage 4 corrections: real keyboard-only dialog workflows and domain preservation."""
import copy,json
from playwright.sync_api import sync_playwright
import phase2_stage4_browser as t
# Read-only domain capture: tolerate only active-view and empty cache differences.
t.stage.f.HOOK += '''window.stage4Keyboard={
 seed:()=>{meals.find(m=>m.id===1).favorite=true;persist();moveDisplayedMealsToBottom(new Set(['Tuesday::Rice']),false,false)},
 domain:()=>{
  const emptyObjectKeys=['weekdayCategories','weekdayMealOverrides','weekdayRecipeFilters','lastTopMeals'];
  const plans=JSON.parse(JSON.stringify(mealPlans));
  for(const p of plans)for(const key of emptyObjectKeys)if(!p[key]||!Object.keys(p[key]).length)p[key]={};
  return {recipes:meals,cats,plans,sources:getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),checks:groceryOccurrenceChecks,checked:[...checkedIngredients],selected:localStorage.getItem('mealRotationSelectedIngredientsV1'),history:localStorage.getItem(ROTATION_BACK_KEY),sessions:cookingSessions,scales:occurrenceScales,startWeekday,groupIdentities:localStorage.getItem(GROUP_IDENTITIES_KEY)};
 },direct:day=>openDayCategoryPicker(day)
};'''

def domain(p):return p.evaluate('stage4Keyboard.domain()')
def active(p,d):assert d.evaluate('(e)=>e.contains(document.activeElement)'),'Focus escaped the dialog'
def reach(p,target,limit=70):
 for _ in range(limit):
  if target.evaluate('(e)=>e===document.activeElement'):return
  p.keyboard.press('Tab')
 raise AssertionError('Target unreachable with keyboard: '+str(target))
def ring(p,d):
 active(p,d)
 # Traverse every control in both directions, past both boundaries.
 count=d.locator('button:not([disabled]),input:not([disabled]),select:not([disabled])').count()
 for key in ['Tab','Shift+Tab']:
  for _ in range(count+3):p.keyboard.press(key);active(p,d)
 # Even a direct focus request on a background control cannot steal focus.
 p.locator('#settings').evaluate('(e)=>e.focus()') if p.locator('#settings').count() else p.locator('#undo').evaluate('(e)=>e.focus()')
 active(p,d)
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
def restored(p,day=None):
 assert p.evaluate('document.activeElement!==document.body && !document.activeElement.closest("[inert]") && document.activeElement.getClientRects().length>0')
 if day:assert p.locator('button.weekday-heading[data-weekday='+day+']').evaluate('(e)=>e===document.activeElement')
def picker(p,day):return p.get_by_role('dialog',name="Choose "+day+"'s meal groups",exact=True)
def setup_launcher(p):
 opener=p.get_by_role('button',name='Set Up Your Rotation',exact=True);opener.focus();p.keyboard.press('Enter');return p.get_by_role('dialog',name='Set Up Your Rotation',exact=True)
def choose_tab(p,d,tab='lunch'):
 select=d.get_by_role('combobox',name='Meal to plan',exact=True);reach(p,select)
 p.keyboard.press('Home' if tab=='original' else 'End');p.keyboard.press('Tab');assert select.input_value()==tab

def onboarding(b,name,width):
 c,p,errors,prefix=t.setup(b,name,width);p.evaluate('stage4Keyboard.seed();stage4Test.clearPlans();weekTest.once();weekTest.check();weekTest.empty(null,"Sunday",true);stage4Test.groups()');before=domain(p);assert before['history'] and any(plan.get('favoriteRotationScores') for plan in before['plans'])
 d=setup_launcher(p);ring(p,d);choose_tab(p,d);p.keyboard.press('Escape');assert not d.count();restored(p);assert domain(p)==before
 # Navigate to another tab's day, then cancel without editing. Navigation may persist.
 d=setup_launcher(p);choose_tab(p,d);reach(p,d.get_by_role('button',name='Monday',exact=True));p.keyboard.press('Enter');d=picker(p,'Monday');active(p,d);ring(p,d);p.keyboard.press('Escape');assert not d.count();restored(p,'Monday');assert domain(p)==before,('Picker cancellation domain changed',before,domain(p))
 # Exercise completion independently of the populated rotation-history cancellation fixture.
 t.clean(errors);c.close();c,p,errors,prefix=t.setup(b,name,width);p.evaluate('stage4Test.clearPlans();weekTest.once();weekTest.check();weekTest.empty(null,"Sunday",true);stage4Test.groups()');before=domain(p)
 # Initial focus and keyboard-only completion survive the entire handoff.
 d=setup_launcher(p);choose_tab(p,d);reach(p,d.get_by_role('button',name='Monday',exact=True));p.keyboard.press('Enter');d=picker(p,'Monday');cb=d.locator('input[data-group-choice][value=Rice]');reach(p,cb);p.keyboard.press('Space');assert cb.is_checked();active(p,d);ring(p,d);reach(p,d.get_by_role('button',name='Close',exact=True));p.keyboard.press('Enter');assert not d.count();restored(p,'Monday')
 after=domain(p);assert next(plan for plan in after['plans'] if plan['id']=='lunch')['weekdayCategories']['Monday']==['Rice'];assert after['recipes']==before['recipes'],('completion recipe differences',before['recipes'],after['recipes']);assert next(plan for plan in after['plans'] if plan['id']=='original')==next(plan for plan in before['plans'] if plan['id']=='original');assert after['selected']==before['selected'];assert not p.get_by_role('button',name='Set Up Your Rotation',exact=True).count()
 saved=t.storage(p);p.reload();assert t.records(p)==before['recipes'];touched=domain(p);assert next(plan for plan in touched['plans'] if plan['id']=='lunch')['weekdayCategories']['Monday']==['Rice'];p.evaluate('weekTest.restore',saved);p.reload();assert domain(p)==touched
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 t.clean(errors);c.close();print('PASS',name,width,'keyboard setup launcher/cross-tab picker cancellation domain, focus ring, Escape, selection, close restoration, reload/backup',flush=True)

def existing_entries(b,name,width):
 c,p,errors,prefix=t.setup(b,name,width);p.evaluate('stage4Keyboard.seed();weekTest.once();weekTest.check();weekTest.empty("Sides","Tuesday");weekTest.my()');before=domain(p)
 # Existing assigned-weekday heading entry; all actions after initial focus use keys.
 head=p.locator('button.weekday-heading[data-weekday=Tuesday]');head.focus();p.keyboard.press('Enter');d=picker(p,'Tuesday');ring(p,d);side=d.get_by_role('button',name='Side for Sides',exact=True);reach(p,side);p.keyboard.press('Enter');nested=p.get_by_role('dialog',name='Side for Sides',exact=True);ring(p,nested);p.keyboard.press('Escape');active(p,d);ring(p,d);p.keyboard.press('Escape');assert not d.count();assert head.evaluate('(e)=>e===document.activeElement');assert domain(p)==before
 # Existing empty-day planner -> Choose meal groups entry, whose opener is removed.
 head=p.locator('button.weekday-heading[data-weekday=Monday]');head.focus();p.keyboard.press('Enter');plan=p.get_by_role('dialog',name="Plan Monday's meal",exact=True)
 # Legacy planner has no initial focus; Tab from its meaningful initiating heading.
 reach(p,plan.get_by_role('button',name='Choose meal groups',exact=True));p.keyboard.press('Enter');d=picker(p,'Monday');ring(p,d);reach(p,d.get_by_role('button',name='Close',exact=True));p.keyboard.press('Enter');assert not d.count();restored(p);assert domain(p)==before
 # Pointer/touch dismissal is still wired to the same close behavior.
 head=p.locator('button.weekday-heading[data-weekday=Tuesday]');head.tap();d=picker(p,'Tuesday');d.get_by_role('button',name='Close',exact=True).tap();assert not d.count();restored(p);assert domain(p)==before
 t.clean(errors);c.close();print('PASS',name,width,'existing weekday heading/planner entries, keyboard trap/Escape/Close, restored focus, touch and unchanged domain',flush=True)

def temporary_actions(b,name,width):
 c,p,errors,_=t.setup(b,name,width);p.evaluate('weekTest.check();weekTest.my()');before=domain(p)
 head=p.locator('button.weekday-heading[data-weekday=Tuesday]');head.focus();p.keyboard.press('Enter');d=picker(p,'Tuesday');reach(p,d.get_by_role('button',name='Leave Entire Day Empty This Week',exact=True));p.keyboard.press('Enter');assert not d.count();restored(p,'Tuesday');empty=domain(p);assert empty['recipes']==before['recipes'];assert [plan['weekdayCategories'] for plan in empty['plans']]==[plan['weekdayCategories'] for plan in before['plans']]
 p.keyboard.press('Enter');d=picker(p,'Tuesday');reach(p,d.get_by_role('button',name='Resume planned meals',exact=True));p.keyboard.press('Enter');assert not d.count();restored(p,'Tuesday');resumed=domain(p);assert resumed['recipes']==before['recipes'];assert resumed['sources']==before['sources'];assert resumed['selected']==before['selected'];t.clean(errors);c.close();print('PASS',name,width,'keyboard Leave Empty/Resume restores weekday focus after rendering and retains same-cycle groceries/assignments/recipes',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [280,320,360]:onboarding(b,name,width);existing_entries(b,name,width);temporary_actions(b,name,width)
  b.close()
