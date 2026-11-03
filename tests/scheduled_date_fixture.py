"""Create fixture schedules at an explicit instant instead of guessing their age."""
from datetime import datetime,timezone

DATED_SCHEDULE_HOOK='''window.establishDatedFixtureSchedule=()=>{
 const saved=mealPlans.map(p=>({p,weekdayCategories:JSON.parse(JSON.stringify(p.weekdayCategories)),weekdayMealOverrides:{...p.weekdayMealOverrides},choices:JSON.parse(JSON.stringify(p.cycleSlotChoices||{})),pins:{...p.cycleRetainedSlots}}));
 for(const {p}of saved){p.weekdayCategories={};p.weekdayMealOverrides={};p.cycleSlotChoices={};p.cycleRetainedSlots={}}
 weekdayCategories={};weekdayMealOverrides={};saveActiveMealPlan();persist();
 for(const x of saved)Object.assign(x.p,{weekdayCategories:x.weekdayCategories,weekdayMealOverrides:x.weekdayMealOverrides,cycleSlotChoices:x.choices,cycleRetainedSlots:x.pins});
 const active=mealPlans.find(p=>p.id===activePlanId);weekdayCategories=JSON.parse(JSON.stringify(active.weekdayCategories));weekdayMealOverrides={...active.weekdayMealOverrides};saveActiveMealPlan();persist();renderList();
};'''

def establish_dated_schedule(page):
 page.clock.set_fixed_time(datetime(2026,10,27,8,tzinfo=timezone.utc))
 page.evaluate('establishDatedFixtureSchedule()')
 page.evaluate('window.slotTest?slotTest.seed():cycleTest.seed()')
 page.clock.set_fixed_time(datetime(2026,11,3,8,tzinfo=timezone.utc))
