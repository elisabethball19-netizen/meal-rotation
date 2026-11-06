"""Cold-load copied persisted state and repeat full forward/backward rotations.

Only synthetic backup fixtures are available here. The retained-pin variation
models the saved shape in PR #82; it is not represented as backups (20)/(21).
"""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/rotation-upgrades/pre80-after-cycle.json'
HOOK='''window.hiddenReplay={
 rows:()=>mealPlans.flatMap(p=>getDisplayedWeekdayMealsForPlan(p.id===activePlanId?{...p,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:p).map(x=>({planId:p.id,day:x.day,cat:x.cat,id:String(x.meal.id),parent:String(x.linkedTo??'')}))),
 forward:()=>moveDisplayedMealsToBottom(),back:()=>rotateAllBack(),
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 state:()=>({meals,plans:mealPlans}),storage:captureBackupStorage,
 valid:()=>{const storage=captureBackupStorage();return !!normalizeImportedBackup({version:2,...JSON.parse(storage.mealRotationDataV1),storage})}
};'''


def saved_state(mode):
    fixture=json.loads(FIXTURE.read_text());storage=copy.deepcopy(fixture['storage'])
    before=json.loads(storage['mealRotationLastRotationBeforeV1'])
    plans=before['mealPlans'];plan=plans[0]
    source='3' if mode=='ordinary' else '4'
    plan['weekdayMealOverrides']['Sunday::Weekend']=source
    plan['cycleRetainedSlots']['Sunday::Weekend']=source
    plan['cycleSlotChoices']['Sunday::Weekend']={'mealId':source,'parentId':'','retain':True}
    if mode in ['manual','self-manual','manual-deferred']:plan['cycleSlotChoices']['Sunday::Weekend']['substitution']=True
    if mode=='manual-deferred':plan['cycleSlotChoices']['Sunday::Weekend']['deferredMealIds']=['3']
    if mode=='self-manual':plan['cycleSlotChoices']['Sunday::Weekend']['deferredMealIds']=['4']
    if mode=='whole-day':plan['weekSchedule']['slots']['Sunday::@day']=plan['weekSchedule']['slots'].pop('Sunday::Weekend')
    if mode=='ordinary':
        plan['weekdayMealOverrides']['Saturday::Weekend']='1';plan['cycleRetainedSlots']['Saturday::Weekend']='1'
        plan['cycleSlotChoices']['Saturday::Weekend']={'mealId':'1','parentId':''}
    meals=before['meals']
    if mode=='legacy-ranking':
        del plan['cycleSlotChoices']['Saturday::Weekend']['deferredMealIds']
        plan['cycleSlotChoices']['Sunday::Weekend'].update(skipReplacement=True,avoidMealId='3')
        next(m for m in meals if m['id']==2)['lastCooked']='2025-01-01T12:00:00.000Z'
    if mode=='favorite':
        for m in meals:
            if m['id'] in [3,7]:m['favorite']=True
    if mode=='linked':
        next(m for m in meals if m['id']==3)['linkedMealIds']=[200]
        meals.append({'id':200,'name':'Synthetic linked side','url':'','cat':'Sides','rotation':True,'ingredients':['1 cup stock'],'instructions':'Mix.','lastCooked':'2020-01-01T12:00:00.000Z'})
        before['cats'].append('Sides')
        selected=json.loads(storage['mealRotationSelectedIngredientsV1']);selected['200']=['1 cup stock'];storage['mealRotationSelectedIngredientsV1']=json.dumps(selected)
    if mode in ['reserved','hidden-reserved']:
        other=plans[1];other['weekdayCategories']={'Tuesday':['Weekend']};other['weekdayMealOverrides']={'Tuesday::Weekend':'3'};other['cycleRetainedSlots']={'Tuesday::Weekend':'3'};other['cycleSlotChoices']={'Tuesday::Weekend':{'mealId':'3','parentId':'','retain':True,'substitution':True}}
    if mode=='hidden-reserved':
        plans[1]['weekSchedule']={'version':1,'slots':{'Tuesday::Weekend':{'kind':'empty'}},'order':{}}
        del plans[1]['cycleSlotChoices']['Tuesday::Weekend']['substitution']
    before['weekdayMealOverrides']=copy.deepcopy(plan['weekdayMealOverrides'])
    storage['mealRotationDataV1']=json.dumps({'cats':before['cats'],'active':'Weekend','meals':meals})
    storage['mealRotationPlansV1']=json.dumps({'plans':plans,'activeId':'original'})
    storage['mealRotationWeekdayCategoriesV1']=json.dumps(plan['weekdayCategories'])
    storage['mealRotationWeekdayMealOverridesV1']=json.dumps(plan['weekdayMealOverrides'])
    storage['mealRotationWeekdayRecipeFiltersV1']=json.dumps(plan['weekdayRecipeFilters'])
    storage['mealRotationLastRotationBeforeV1']=json.dumps(before)
    return storage


def run(browser,name,mode):
    prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
    storage=saved_state(mode);seed={prefix+k:v for k,v in storage.items()}
    if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
    src=(ROOT/name).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
    c=browser.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True);p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.add_init_script('if(!sessionStorage.loaded){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.loaded="1"}')
    p.route('http://hidden.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(name) else r.fulfill(status=200,body=''))
    p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
    try:
        p.goto('http://hidden.test/'+name)
        def rows():return p.evaluate('hiddenReplay.rows()')
        def picks():return {x['day']:x['id'] for x in rows() if x['planId']=='original' and x['cat']=='Weekend'}
        def sources():return {x['id']:x for x in p.evaluate('hiddenReplay.sources()')}
        original=rows();groceries=sources();recipes=sorted(p.evaluate('hiddenReplay.state()')['meals'],key=lambda m:m['id'])
        assert picks()=={'Saturday':'1'},picks()
        assert p.evaluate('hiddenReplay.valid()')
        expected={'Saturday':'2','Sunday':'4' if mode in ['manual','self-manual'] else '3'}
        preserved_storage=p.evaluate('hiddenReplay.storage()')
        if mode=='legacy-ranking':expected={'Saturday':'3','Sunday':'4'}
        outputs=[]
        for _ in range(3):
            p.reload();p.evaluate('hiddenReplay.forward()');outputs.append(picks())
            if mode in ['reserved','hidden-reserved']:
                assert picks()['Saturday']=='2' and picks()['Sunday']!='3';weekend=[x['id'] for x in rows() if x['cat']=='Weekend'];assert len(weekend)==len(set(weekend))
            else:assert picks()==expected,(name,mode,outputs)
            if mode=='linked':assert any(x['id']=='200' and x['parent']=='3' and x['day']=='Sunday' for x in rows()),rows()
            for key,value in sources().items():
                if value['planId']!='original':assert value==groceries[key]
                if value['planId']=='original' and value['day'] in ['Saturday','Sunday']:assert not value['checked']
            if mode=='hidden-reserved':assert p.evaluate('hiddenReplay.state()')['plans'][1]['weekdayMealOverrides']['Tuesday::Weekend']=='3'
            stable=rows();checks=sources();p.reload();assert rows()==stable and sources()==checks
            assert p.evaluate('hiddenReplay.valid()')
            p.evaluate('hiddenReplay.back()');p.reload()
            assert rows()==original and sources()==groceries
            assert sorted(p.evaluate('hiddenReplay.state()')['meals'],key=lambda m:m['id'])==recipes
        # Consecutive forward rotations must not leave Sunday pinned after the
        # temporary slot expires. Back/forward above intentionally repeats a week.
        p.evaluate('hiddenReplay.forward()');last=picks()['Sunday']
        for _ in range(2):
            p.evaluate('hiddenReplay.forward()');current=picks()['Sunday'];assert current!=last,(mode,last,picks());last=current
        final_storage=p.evaluate('hiddenReplay.storage()')
        for key in ['mealRotationSelectedIngredientsV1','mealRotationCustomSettingV9','mealRotationRecipeViewPrefsV1']:
            assert final_storage.get(key)==preserved_storage.get(key),(mode,key)
        if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
        assert not errors,errors
        print('PASS',name,mode,'three cold-state forward/back/forward cycles, groceries, recipes, backups, no JS errors',flush=True)
    finally:c.close()

if __name__=='__main__':
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        try:
            for name in ['index.html','meal-rotation-test.html']:
                for mode in ['stale','ordinary','manual','self-manual','manual-deferred','whole-day','favorite','linked','reserved','hidden-reserved','legacy-ranking']:run(b,name,mode)
        finally:b.close()
