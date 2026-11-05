"""Explicit duration-unit regression, including real Crispy Fish Tacos instructions."""
import copy
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
from scheduled_linked_slots_browser import state,compose
# Instruction text from the supplied RecipeSage export; no working-app data is modified.
SAUCE='In a small bowl, whisk together the mayonnaise, lime juice, grated garlic, honey, cumin and salt. Add 1–2 teaspoons of water until the sauce reaches a drizzle-friendly consistency. Taste and adjust the lime or salt as desired.'
FISH='Heat a large skillet over medium-high heat. Cook the fillets for approximately 3–4 minutes per side, depending on thickness, until golden and cooked through to an internal temperature of 145°F. Transfer to a plate and gently break into bite-sized pieces.'
TORTILLAS='Heat the corn tortillas in a dry skillet over medium heat for about 20–30 seconds per side, until warm and pliable. Keep covered with a clean towel while preparing the tacos.'
INVALID=[SAUCE,'4. Add 1–2 teaspoons of water, as desired.','1–2 teaspoons of water','½ cup broth','2 tablespoons oil','350°F','Step 4','3 cloves garlic','Season as needed.','Use as much as desired.','Stir and serve as is.','Add ½ cup broth and 2 tablespoons oil; heat to 350°F.','4. Add 3 cloves garlic and 1/2 cup water.','Add 1-2 tsp water as needed.','a','as','am','onehour','twohrs','fivemin','3–4 cloves garlic']
VALID=[(FISH,[180000]),(TORTILLAS,[20000]),('Cook for 15 minutes',[900000]),('Rest 5 min',[300000]),('Simmer 1 hour',[3600000]),('Bake for 20–25 minutes',[1200000]),('Wait 30 sec',[30000]),('Rest 5 mins',[300000]),('Cook 1 hr',[3600000]),('Simmer 2 hrs',[7200000]),('Cook for an hour',[3600000]),('Wait a second',[1000]),('Rest half an hour',[1800000]),('Cook for 1h30m',[5400000]),('Cook 15min',[900000]),('Add 1–2 teaspoons of water as needed; simmer for 10–15 min.',[600000]),('4. Heat ½ cup broth with 2 tablespoons oil and 3 cloves garlic at 350°F for 20 minutes, then rest 5 mins.',[1200000,300000])]
t.f.EXTRA+='''window.timerUnitsTest={set:instructions=>{const m=meals.find(m=>m.id===1);m.name='Crispy Fish Tacos';m.instructions=instructions;persist();}};'''
def run(b,name,width,mode):
 c,p,errors,prefix=t.f.setup(b,name,width,'multiple');p.clock.install()
 for text in INVALID:assert p.evaluate('text=>timerTest.durations(text)',text)==[],text
 for text,expected in VALID+t.PARSER:
  got=p.evaluate('text=>timerTest.durations(text).map(x=>x.ms)',text);assert got==expected,(text,got,expected)
 instructions=INVALID+[text for text,_ in VALID]
 p.evaluate('steps=>timerUnitsTest.set(steps)',instructions);p.evaluate('timerTest.viewer()');p.evaluate('mode=>timerTest.mode(mode)',mode)
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=t.f.sources(p)
 rows=p.locator('.recipe-viewer-steps>li')
 assert rows.count()==len(instructions)
 for i in range(len(INVALID)):assert rows.nth(i).locator('.recipe-step-timer').count()==0,instructions[i]
 for i in range(len(INVALID),len(instructions)):assert rows.nth(i).locator('.recipe-step-timer').count()==1,instructions[i]
 # Actual fish and tortilla instructions use the shorter range values and never complete a step.
 for i,expected in [(len(INVALID),180000),(len(INVALID)+1,20000)]:
  row=rows.nth(i);row.locator('.recipe-step-timer').tap()
  assert expected-500<=p.evaluate('timerTest.remaining()')<=expected
  assert row.locator('.cooking-item').get_attribute('aria-pressed')=='false'
  p.get_by_role('button',name='Cancel timer',exact=True).tap()
 # Distinct durations in a mixed measurement/time instruction still require the existing picker.
 rows.last.locator('.recipe-step-timer').tap();d=p.get_by_role('dialog',name='Choose cooking duration',exact=True)
 assert d.locator('.smallbtn').count()==2;d.locator('.smallbtn').nth(1).tap();assert 299500<=p.evaluate('timerTest.remaining()')<=300000
 p.clock.fast_forward(5000);assert '4:55 remaining' in t.strip(p).inner_text()
 p.get_by_role('button',name='Cancel timer',exact=True).tap()
 t.stable(p,before,schedule,groceries)
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,mode,'real taco instructions, 21 negative/17 positive cases plus existing parser corpus; icon presence, range starts, duration choice/countdown, unchanged progress/data, no JS errors',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['full','split']:run(b,name,width,mode)
  b.close()
