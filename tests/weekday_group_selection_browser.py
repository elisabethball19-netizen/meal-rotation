"""Focused weekday assignment, missing-group display and inline group creation."""
import json
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
f.EXTRA+='''window.groupPickerTest={
 seed:()=>{cats=['Weekend','Breakfast','Lunch'];meals=cats.flatMap((cat,i)=>[0,1].map(n=>({id:i*2+n+1,cat,name:cat+' meal '+(n+1),rotation:i===0,ingredients:['1 cup rice'],instructions:'Cook.',url:''})));id=7;mealPlans=[{id:'original',name:'Dinner',weekdayCategories:{Saturday:['Weekend']},weekdayMealOverrides:{},cycleRetainedSlots:{},cycleSlotChoices:{},weekdayRecipeFilters:{},pinnedCats:[]}];activePlanId='original';weekdayCategories={Saturday:['Weekend']};weekdayMealOverrides={};weekdayRecipeFilters={};localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));saveActiveMealPlan();persist();promotionTest.my()},
 assigned:()=>getDayCategories('Saturday'),open:()=>openDayCategoryPicker('Saturday'),
 library:()=>JSON.stringify([...meals].sort((a,b)=>a.id-b.id)),cats:()=>cats,
 enable:cat=>{for(const m of meals)if(m.cat===cat)m.rotation=true;persist();renderList()},
 rotate:()=>moveDisplayedMealsToBottom(new Set(['Saturday::Breakfast'])),
 rows:()=>getDisplayedWeekdayMeals().filter(x=>x.day==='Saturday').map(x=>[x.cat,x.meal.id]),
 menu:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday');openTopMealActionMenu(x.day,x.cat,x.meal)},
 empty:()=>leaveWeekEmpty('Saturday','Weekend'),resume:()=>resumeWeekSlot('Saturday','Weekend'),
 selected:()=>localStorage.getItem('mealRotationSelectedIngredientsV1')
};'''


def group_order(p):
    return p.locator('.top-recipe-wrap[data-schedule-day=Saturday],.empty-weekday-meal[data-schedule-day=Saturday]').evaluate_all('(els)=>els.map(el=>el.classList.contains("empty-weekday-meal")?el.dataset.category:JSON.parse(el.dataset.displayKey)[0])')


def run(browser,name,width):
    c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('groupPickerTest.seed()')
    original=p.evaluate('groupPickerTest.library()');selected=p.evaluate('groupPickerTest.selected()')
    p.evaluate('groupPickerTest.open()');d=p.get_by_role('dialog',name="Choose Saturday's meal groups",exact=True)
    assert d.get_by_role('button',name='Create New Group',exact=True).count()==1
    assert not d.get_by_role('button',name='Leave Entire Day Empty This Week',exact=True).count()
    for cat in ['Breakfast','Lunch']:d.locator('input[data-group-choice][value="'+cat+'"]').check()
    assert p.evaluate('groupPickerTest.assigned()')==['Weekend','Breakfast','Lunch']
    d.get_by_role('button',name='Close',exact=True).click()
    assert group_order(p)==['Weekend','Breakfast','Lunch'],group_order(p)
    assert p.locator('.empty-weekday-meal[data-category=Breakfast]').count()==1
    assert p.locator('.empty-weekday-meal[data-category=Lunch]').count()==1
    assert p.evaluate('groupPickerTest.library()')==original
    p.reload();p.evaluate('promotionTest.my()');assert group_order(p)==['Weekend','Breakfast','Lunch']
    p.evaluate("groupPickerTest.enable('Lunch')");assert group_order(p)==['Weekend','Breakfast','Lunch']
    p.evaluate("groupPickerTest.enable('Breakfast')");assert len(p.locator('.top-recipe-wrap[data-schedule-day=Saturday]').all())==3
    before=dict(p.evaluate('groupPickerTest.rows()'));p.evaluate('groupPickerTest.rotate()');after=dict(p.evaluate('groupPickerTest.rows()'))
    assert before['Weekend']==after['Weekend'] and before['Lunch']==after['Lunch'] and before['Breakfast']!=after['Breakfast']
    p.reload();assert dict(p.evaluate('groupPickerTest.rows()'))==after
    p.evaluate('groupPickerTest.open()');d=p.get_by_role('dialog',name="Choose Saturday's meal groups",exact=True)
    assert d.locator('input[data-group-choice]:checked').count()==3
    d.get_by_role('button',name='Create New Group',exact=True).click()
    prompt=p.get_by_role('dialog').filter(has_text='New group name')
    prompt.get_by_role('textbox').fill('Quick meals');prompt.get_by_role('button',name='Save',exact=True).click()
    cb=d.locator('input[data-group-choice][value="Quick meals"]');assert cb.is_checked()
    assert p.evaluate('groupPickerTest.cats()')==['Weekend','Breakfast','Lunch','Quick meals']
    assert d.get_by_role('button',name='Create New Group',exact=True).count()==1
    assert p.evaluate('document.activeElement.textContent')=='Create New Group'
    box=d.bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
    d.get_by_role('button',name='Create New Group',exact=True).click()
    p.get_by_role('dialog').filter(has_text='New group name').get_by_role('button',name='Cancel',exact=True).click()
    assert cb.is_checked() and d.get_by_role('button',name='Create New Group',exact=True).count()==1
    d.get_by_role('button',name='Close',exact=True).click()
    assert group_order(p)==['Weekend','Breakfast','Lunch','Quick meals']
    p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('groupPickerTest.assigned()')==['Weekend','Breakfast','Lunch','Quick meals']
    assert p.locator('.empty-weekday-meal[data-category="Quick meals"]').count()==1
    # Empty one group must not erase the placeholders/entries of sibling groups.
    p.evaluate('groupPickerTest.empty()');assert group_order(p)==['Weekend','Breakfast','Lunch','Quick meals']
    assert p.locator('.empty-weekday-meal[data-category=Weekend] .mealname').inner_text()=='Empty this week'
    p.evaluate('groupPickerTest.resume()')
    p.evaluate('groupPickerTest.menu()');menu=p.get_by_role('dialog',name='Meal options for Saturday',exact=True)
    menu.get_by_role('button',name='Leave Saturday weekend empty',exact=True).click()
    p.locator('.empty-weekday-meal[data-category=Weekend] .mealname').click()
    empty_menu=p.get_by_role('dialog',name='Empty meal options',exact=True)
    empty_menu.get_by_role('button',name='Leave Entire Day Empty This Week',exact=True).click()
    assert p.locator('.empty-weekday-meal[data-schedule-day=Saturday]').count()==4
    assert not p.locator('.top-recipe-wrap[data-schedule-day=Saturday]').count()
    assert p.evaluate('groupPickerTest.selected()')==selected
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
    assert not errors,errors;c.close();print('PASS',name,width,'all groups/empty states, independent rotation, reload, create/cancel, ordering, sibling empties, meal empty-day action, mobile layout, no JS errors',flush=True)

if __name__=='__main__':
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        try:
            for name in ['index.html','meal-rotation-test.html']:
                for width in [320,390]:run(b,name,width)
        finally:b.close()
