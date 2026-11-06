"""Cold replay of the exact Sunday fields/IDs supplied in the backup analysis.

This is a minimal synthetic fixture, not the user's full backup. Unreported
recipe dates, Pernil ID, and Saturday snapshot variants are explicit test data.
It verifies both flag provenance and the forward/back lifetime of retention.
"""
import copy
import json
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
CHOICE={'mealId':'22','parentId':'','retain':True}
HOOK='''window.retainEvidence={
 rows:()=>getDisplayedWeekdayMeals().map(x=>({day:x.day,cat:x.cat,id:String(x.meal.id)})),
 forward:()=>moveDisplayedMealsToBottom(),back:()=>rotateAllBack(),
 plan:()=>JSON.parse(JSON.stringify(mealPlans.find(p=>p.id===activePlanId))),
 manual:()=>manualWeekdayMealChoice(mealPlans.find(p=>p.id===activePlanId),'Sunday','Weekend','22'),
 recipes:()=>JSON.stringify([...meals].sort((a,b)=>Number(a.id)-Number(b.id))),
 data:()=>localStorage.getItem('mealRotationSelectedIngredientsV1'),
 sentinel:()=>localStorage.getItem('mealRotationUnrelatedDiagnosticV1'),
 history:()=>localStorage.getItem(ROTATION_BACK_KEY),
 editSaturday:()=>{delete mealPlans.find(p=>p.id===activePlanId).cycleSlotChoices['Sunday::Weekend'].retain;saveActiveMealPlan();applyManualWeekdayMeal('Saturday','Weekend',meals.find(m=>m.id===1001))}
};'''


def fixture(saturday='deferred',whole=False,manual=False,empty=True,saved_retain=True):
    ids=[1001,537,535,22,51,52,53]
    names=['Pernil','Korean Slow-Cooker Beef Bowls','Mississippi-Style Pot Roast','Spaghetti','Tortilla Soup','Apple Braised Pork','French Dip']
    meals=[{'id':id,'cat':'Weekend','name':name,'rotation':True,'url':'','notes':'','ingredients':['1 cup rice'],'instructions':'Cook.','labels':[],'linkedMealIds':[],'lastCooked':f'2020-01-{index+1:02d}T12:00:00.000Z'} for index,(id,name) in enumerate(zip(ids,names))]
    def plan(sat,prior=False):
        sunday=copy.deepcopy(CHOICE)
        if manual:sunday['substitution']=True
        if prior and not saved_retain:del sunday['retain']
        saturday_choice={'mealId':str(sat),'parentId':''}
        if prior and saturday!='automatic':
            saturday_choice.update(substitution=True,retain=True)
            if saturday=='deferred':saturday_choice['deferredMealIds']=['537']
        p={'id':'original','name':'Dinner','weekdayCategories':{'Saturday':['Weekend'],'Sunday':['Weekend']},'weekdayRecipeFilters':{},'weekdayMealOverrides':{'Saturday::Weekend':str(sat),'Sunday::Weekend':'22'},'cycleRetainedSlots':{'Saturday::Weekend':str(sat),'Sunday::Weekend':'22'},'cycleSlotChoices':{'Saturday::Weekend':saturday_choice,'Sunday::Weekend':sunday},'pinnedCats':[],'autoPinTopCategories':True}
        if prior and empty:p['weekSchedule']={'version':1,'slots':{'Sunday::'+('@day' if whole else 'Weekend'):{'kind':'empty'}},'order':{}}
        return p
    before_sat=537 if saturday=='automatic' else 1001
    current=plan(537);old=plan(before_sat,True)
    occurrences=[{'planId':'original','planName':'Dinner','day':'Saturday','cat':'Weekend','mealId':str(before_sat),'parentId':'','scheduledSlot':True}]
    if empty:occurrences.append({'planId':'original','planName':'Dinner','day':'Sunday','cat':'@day' if whole else 'Weekend','mealId':'empty:original:Sunday::'+('@day' if whole else 'Weekend'),'parentId':'','scheduleOnly':True})
    else:occurrences.append({'planId':'original','planName':'Dinner','day':'Sunday','cat':'Weekend','mealId':'22','parentId':'','scheduledSlot':True})
    previous={'cats':['Weekend'],'active':'Weekend','meals':copy.deepcopy(meals),'mealPlans':[old],'activePlanId':'original','showMealPlanTabs':False,'weekdayCategories':old['weekdayCategories'],'weekdayMealOverrides':old['weekdayMealOverrides'],'weekdayRecipeFilters':{},'pinnedCats':[],'expandedCats':[],'startWeekday':'Monday','checkedIngredients':[],'groceryOccurrenceChecks':{'version':1,'checks':{}},'rotationOccurrences':occurrences,'favoriteRotationTurns':[],'cookedDateUpdates':[]}
    storage={
        'mealRotationDataV1':json.dumps({'cats':['Weekend'],'active':'Weekend','meals':meals}),
        'mealRotationPlansV1':json.dumps({'plans':[current],'activeId':'original'}),
        'mealRotationWeekdayCategoriesV1':json.dumps(current['weekdayCategories']),
        'mealRotationWeekdayMealOverridesV1':json.dumps(current['weekdayMealOverrides']),
        'mealRotationWeekdayRecipeFiltersV1':'{}','mealRotationStartWeekdayV1':'Monday',
        'mealRotationSelectedIngredientsV1':json.dumps({str(m['id']):m['ingredients'] for m in meals}),
        'mealRotationLastRotationBeforeV1':json.dumps(previous),'mealRotationTutorialStageV1':'done',
        'mealRotationShowPlanTabsV1':'false','mealRotationUnrelatedDiagnosticV1':'keep this opaque setting',
    }
    return storage


class RetainedSundayEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()

    def setup_page(self,filename,**options):
        prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
        storage=fixture(**options);seed={prefix+key:value for key,value in storage.items()}
        if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
        src=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
        c=self.browser.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True);self.addCleanup(c.close)
        p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.add_init_script('if(!sessionStorage.evidenceLoaded){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.evidenceLoaded="1"}')
        p.route('http://retained.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
        p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
        p.goto('http://retained.test/'+filename)
        return p,errors,prefix,storage

    def replay(self,filename,**options):
        p,errors,prefix,storage=self.setup_page(filename,**options)
        def picks():return {x['day']:x['id'] for x in p.evaluate('retainEvidence.rows()')}
        def sunday():return p.evaluate('retainEvidence.plan()')['cycleSlotChoices']['Sunday::Weekend']
        manual=options.get('manual',False)
        expected_choice={**CHOICE,**({'substitution':True} if manual else {})}
        self.assertEqual(picks(),{'Saturday':'537','Sunday':'22'})
        self.assertEqual(sunday(),expected_choice)
        self.assertEqual(p.evaluate('retainEvidence.manual()'),manual)
        self.assertEqual(p.evaluate('retainEvidence.history()'),storage['mealRotationLastRotationBeforeV1'])
        recipes=p.evaluate('retainEvidence.recipes()');ingredients=p.evaluate('retainEvidence.data()')
        for _ in range(3):
            p.evaluate('retainEvidence.back()');p.reload()
            self.assertNotIn('Sunday',picks())
            self.assertEqual(sunday(),expected_choice,'Back must faithfully restore the saved choice, not erase all retain flags')
            restored=p.evaluate('retainEvidence.plan()')
            self.assertEqual(restored['weekdayMealOverrides']['Sunday::Weekend'],'22')
            self.assertEqual(restored['cycleRetainedSlots']['Sunday::Weekend'],'22')
            self.assertTrue(p.locator('.empty-weekday-meal[aria-label$="empty this week"]').count())
            p.evaluate('retainEvidence.forward()');p.reload()
            expected_sat='1001' if options.get('saturday')=='automatic' else '537'
            self.assertEqual(picks(),{'Saturday':expected_sat,'Sunday':'22' if manual else '535'})
            current=p.evaluate('retainEvidence.plan()')
            self.assertEqual(current['weekdayMealOverrides']['Sunday::Weekend'],'22' if manual else '535')
            self.assertEqual(current['cycleRetainedSlots']['Sunday::Weekend'],'22' if manual else '535')
            self.assertEqual(current['cycleSlotChoices']['Sunday::Weekend'].get('retain',False),manual)
            archived=json.loads(p.evaluate('retainEvidence.history()'))['mealPlans'][0]
            self.assertEqual(archived['cycleSlotChoices']['Sunday::Weekend'],expected_choice,'Forward must preserve the old snapshot, not repair history destructively')
            self.assertEqual(archived['weekdayMealOverrides']['Sunday::Weekend'],'22')
            self.assertEqual(archived['cycleRetainedSlots']['Sunday::Weekend'],'22')
            self.assertEqual(p.evaluate('retainEvidence.recipes()'),recipes)
            self.assertEqual(p.evaluate('retainEvidence.data()'),ingredients)
            self.assertEqual(p.evaluate('retainEvidence.sentinel()'),'keep this opaque setting')
        if prefix:self.assertEqual(p.evaluate("localStorage.getItem('mealRotationDataV1')"),'WORKING SENTINEL')
        self.assertFalse(errors,errors)

    def provenance(self,filename,operation):
        p,errors,_,_=self.setup_page(filename,empty=False,saved_retain=False)
        self.assertFalse(p.evaluate('retainEvidence.manual()'))
        if operation=='saturday-edit':p.evaluate('retainEvidence.editSaturday()')
        else:p.evaluate('retainEvidence.back()')
        p.reload();plan=p.evaluate('retainEvidence.plan()')
        self.assertEqual(plan['cycleSlotChoices']['Sunday::Weekend'],CHOICE)
        self.assertEqual(plan['weekdayMealOverrides']['Sunday::Weekend'],'22')
        self.assertEqual(plan['cycleRetainedSlots']['Sunday::Weekend'],'22')
        self.assertFalse(p.evaluate('retainEvidence.manual()'),'Automatic retention must not be mistaken for a manual substitution')
        self.assertFalse(errors,errors)


def replay_case(filename,options):
    def test(self):self.replay(filename,**options)
    return test


def provenance_case(filename,operation):
    def test(self):self.provenance(filename,operation)
    return test

for filename,tag in [('index.html','production'),('meal-rotation-test.html','sandbox')]:
    for name,options in [('exact',{}),('whole_day',{'whole':True}),('legacy_saturday',{'saturday':'legacy'}),('automatic_saturday',{'saturday':'automatic'}),('manual_control',{'manual':True})]:
        setattr(RetainedSundayEvidence,'test_'+name+'_'+tag,replay_case(filename,options))
    for operation in ['saturday-edit','visible-back']:
        setattr(RetainedSundayEvidence,'test_retain_provenance_'+operation.replace('-','_')+'_'+tag,provenance_case(filename,operation))

if __name__=='__main__':unittest.main(verbosity=2)
