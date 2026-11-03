"""Whole-plan duplicate avoidance during rotation, using isolated synthetic data."""
import json, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from scheduled_linked_slots_browser import HOOK, meal, rows, state, compose, context_key, definitions
ROOT=Path(__file__).resolve().parents[1]
BASE='fcf4ab74d16b9ad67b661e1da561ad8d1b95b359'

def setup(browser, filename, width, scenario, baseline=False):
    library=[meal(i,n,'Weekend') for i,n in [(1,'Saturday stew'),(2,'Lentils'),(3,'Curry'),(4,'Pasta'),(5,'Soup')]]
    assignments={'Saturday':['Weekend'],'Sunday':['Weekend']}
    overrides={'Saturday::Weekend':'1','Sunday::Weekend':'2'}
    pins=dict(overrides); filters={}
    if scenario=='legacy-retained':pins={}
    if scenario=='three-days':
        assignments={'Friday':['Weekend'],'Saturday':['Weekend'],'Sunday':['Weekend']}
        overrides={'Friday::Weekend':'1','Saturday::Weekend':'2','Sunday::Weekend':'3'};pins=dict(overrides)
    if scenario=='one-recipe':
        library=library[:1];overrides={'Saturday::Weekend':'1','Sunday::Weekend':'1'};pins=dict(overrides)
    if scenario=='exhausted':
        library=library[:2];assignments={'Friday':['Weekend'],'Saturday':['Weekend'],'Sunday':['Weekend']}
        overrides={'Friday::Weekend':'1','Saturday::Weekend':'2','Sunday::Weekend':'1'};pins=dict(overrides)
    if scenario=='filtered':
        for m in library:m['labels']=['Eligible'] if m['id'] in [1,2,4] else ['Other']
        filters={'Saturday::Weekend':['Eligible']}
    if scenario in ['linked','retain-linked','attachment']:
        library=[meal(1,'Old Main','Mains'),meal(2,'New Main','Mains',[12]),meal(10,'Unused side','Sides'),meal(11,'Outgoing Sunday side','Sides'),meal(12,'New linked side','Sides'),meal(13,'Retained Saturday side','Sides')]
        assignments={'Saturday':['Mains','Sides'],'Sunday':['Sides']}
        overrides={'Saturday::Mains':'1','Saturday::Sides':'13','Sunday::Sides':'11'};pins=dict(overrides)
        if scenario=='attachment':
            assignments={'Saturday':['Mains'],'Sunday':['Sides']};overrides={'Saturday::Mains':'1','Sunday::Sides':'11'};pins=dict(overrides)
    for m in library:
        m['ingredientStepLinks']=[];m['lastCooked']='2025-01-01T12:00:00.000Z'
    cats=list(dict.fromkeys(m['cat'] for m in library))
    plans=[dict(id='original',name='Dinner',weekdayCategories=assignments,weekdayMealOverrides=overrides,cycleRetainedSlots=pins,weekdayRecipeFilters=filters,pinnedCats=[])]
    other=library[-1] if scenario in ['linked','retain-linked','attachment'] else library[1 if len(library)>1 else 0]
    plans.append(dict(id='lunch',name='Lunch',weekdayCategories={'Tuesday':[other['cat']]},weekdayMealOverrides={'Tuesday::'+other['cat']:str(other['id'])},cycleRetainedSlots={'Tuesday::'+other['cat']:str(other['id'])},weekdayRecipeFilters={},pinnedCats=[]))
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=cats,active=cats[0],meals=library)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=plans,activeId='original')),prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationSelectedIngredientsV1':json.dumps({str(m['id']):m['ingredients'] for m in library}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,keepScreenAwake=False)),prefix+'mealRotationTutorialStageV1':'done'}
    seed[prefix+'mealRotationWeekdayRecipeFiltersV1']=json.dumps(filters)
    if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
    ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True)
    p=ctx.new_page();p.set_default_timeout(8000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    source=subprocess.check_output(['git','show',BASE+':'+filename],cwd=ROOT,text=True) if baseline else (ROOT/filename).read_text()
    source=source.replace('function validateBackupCore(d){','window.slotBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'for(const m of meals){const items=recipeAssociationItems(m);m.ingredientStepLinks=[{step:items.steps[0].token,ingredients:[items.ingredients[0].token]}]}persist();})();')
    p.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
    p.route('http://duplicates.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
    p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
    p.goto('http://duplicates.test/'+filename);p.evaluate('slotTest.seed()')
    return ctx,p,errors,prefix

def pick(p, day, cat, plan='original'):
    return next(r for r in rows(p) if r['planId']==plan and r['day']==day and r['cat']==cat)

def run(browser,filename,width,scenario,baseline=False,all_tabs=False,mark=False):
    ctx,p,errors,prefix=setup(browser,filename,width,scenario,baseline)
    before=state(p);schedule=compose(p);storage=p.evaluate('slotTest.storage()')
    if scenario in ['linked','retain-linked']:
        chosen=['Saturday::Mains','Sunday::Sides']
    elif scenario=='attachment':chosen=['Saturday::Mains','Sunday::Sides']
    elif scenario=='three-days':chosen=['Friday::Weekend','Saturday::Weekend']
    elif scenario=='exhausted':chosen=['Friday::Weekend','Saturday::Weekend']
    else:chosen=['Saturday::Weekend']
    # The exact reported scenario uses the real selection dialog and leaves Sunday unchecked.
    if scenario in ['weekend','legacy-retained','filtered'] and not all_tabs:
        p.get_by_role('button',name='Cycle Meals',exact=True).tap();p.get_by_role('button',name='Select recipes to rotate out',exact=True).tap()
        dialog=p.get_by_role('heading',name='Select meals to rotate out').locator('..')
        dialog.get_by_role('button',name='Deselect all',exact=True).tap()
        dialog.get_by_role('checkbox',name='Saturday · Weekend — Saturday stew',exact=True).check()
        dialog.get_by_role('button',name='Move selected',exact=True).tap()
    else:
        if all_tabs:
            chosen=['original||'+x for x in chosen]+['lunch||Tuesday::'+before['plans'][1]['weekdayCategories']['Tuesday'][0]]
        if scenario=='retain-linked':
            # The normal UI supplies the retained set when its side checkbox is unchecked.
            p.get_by_role('button',name='Cycle Meals',exact=True).tap();p.get_by_role('button',name='Select recipes to rotate out',exact=True).tap()
            d=p.get_by_role('heading',name='Select meals to rotate out').locator('..');d.get_by_role('button',name='Deselect all',exact=True).tap()
            d.get_by_role('checkbox',name='Saturday · Mains — Old Main',exact=True).check();d.get_by_role('checkbox',name='Sunday · Sides — Outgoing Sunday side',exact=True).check();d.get_by_role('button',name='Move selected',exact=True).tap()
        else:p.evaluate('(a)=>slotTest.cycle(...a)',[chosen,all_tabs,mark])
    after=state(p)
    if scenario in ['weekend','legacy-retained','filtered']:
        expected=4 if scenario=='filtered' else 3
        assert pick(p,'Saturday','Weekend')['id']==expected,('duplicate Lentils regression',rows(p))
        assert pick(p,'Sunday','Weekend')['id']==2
        assert [m['id'] for m in after['meals'] if m['cat']=='Weekend']==[2,3,4,5,1], 'Only outgoing stew moves; skipped Lentils stays first'
        assert next(m for m in after['meals'] if m['id']==2)==next(m for m in before['meals'] if m['id']==2)
    elif scenario=='three-days':
        assert [pick(p,d,'Weekend')['id'] for d in ['Friday','Saturday','Sunday']]==[4,5,3]
    elif scenario=='one-recipe':assert [pick(p,d,'Weekend')['id'] for d in ['Saturday','Sunday']]==[1,1]
    elif scenario=='exhausted':assert all(pick(p,d,'Weekend')['id'] in [1,2] for d in ['Friday','Saturday','Sunday'])
    elif scenario=='linked':
        assert pick(p,'Saturday','Mains')['id']==2 and pick(p,'Saturday','Sides')['id']==12
        assert pick(p,'Sunday','Sides')['id']==10,rows(p)
    elif scenario=='retain-linked':
        assert pick(p,'Saturday','Mains')['id']==2 and pick(p,'Saturday','Sides')['id']==13
        assert pick(p,'Sunday','Sides')['id']==12,(rows(p),state(p)['plans'],[m['id'] for m in state(p)['meals']])
    elif scenario=='attachment':
        assert pick(p,'Saturday','Sides')['id']==12 and pick(p,'Saturday','Sides')['parent']=='2'
        assert pick(p,'Sunday','Sides')['id']!=12
    if not all_tabs:
        assert [(x['day'],x['cat'],x['id'],x['parent']) for x in rows(p) if x['planId']=='lunch']==[(x[1],x[2],x[3],x[4]) for x in schedule if x[0]=='lunch']
    assert [x['weekdayCategories'] for x in after['plans']]==[x['weekdayCategories'] for x in before['plans']]
    assert after['prefs']==before['prefs']
    if not mark:assert definitions(after)==definitions(before)
    else:
        for m in after['meals']:
            old=next(x for x in before['meals'] if x['id']==m['id'])
            if m['id'] in [1,2]:assert m['lastCooked']!=old['lastCooked']
            else:assert m==old, 'Skipped recipes must not acquire cooked history'
    total=p.evaluate('slotTest.groceries()')
    expected=sum(r['id']*after['scales']['occurrences'].get(context_key(r),{}).get('multiplier',1) for r in rows(p))
    assert len(total)==1 and abs(total[0]['quantity']['lo']-expected)<1e-8,(total,expected)
    assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==storage['mealRotationSelectedIngredientsV1']
    selected_slots={('original',*k.split('::')) for k in chosen if '||' not in k}
    for key,value in before['sessions']['occurrences'].items():
        r=value['context']
        if (r['planId'],r['day'],r['cat']) not in selected_slots and not all_tabs and scenario not in ['linked','attachment']:
            assert after['sessions']['occurrences'].get(key)==value
            assert after['scales']['occurrences'].get(key)==before['scales']['occurrences'][key]
    current=compose(p);saved=p.evaluate('slotTest.storage()');p.reload()
    assert compose(p)==current
    backup={**json.loads(saved['mealRotationDataV1']),'version':2,'storage':saved}
    p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert compose(p)==current
    p.evaluate('slotTest.back()');assert compose(p)==schedule
    if not mark:assert definitions(state(p))==definitions(before)
    if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
    assert not errors,errors
    print('PASS',filename,width,scenario,'all-tabs' if all_tabs else 'active-tab','mark cooked' if mark else '', 'queue/history, reload/backup/Cycle Back, data preservation; no JS errors',flush=True)
    ctx.close()

if __name__=='__main__':
    baseline='--baseline' in sys.argv
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        if baseline:run(b,'index.html',360,'weekend',True)
        else:
            for f in ['index.html','meal-rotation-test.html']:
                for w in [320,360]:
                    for scenario in ['weekend','legacy-retained','three-days','one-recipe','exhausted','filtered','linked','retain-linked','attachment']:run(b,f,w,scenario)
                run(b,f,360,'three-days',all_tabs=True)
                run(b,f,360,'three-days',mark=True)
        b.close()
