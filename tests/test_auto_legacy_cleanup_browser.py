"""User-authorized TEST-only one-shot cleanup; synthetic data, no production access."""
import copy,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import instruction_repair_browser as base
PREFIX='mealRotationTestSandboxV1:'
BACKUP=PREFIX+'mealRotationTESTONLY__LegacyCleanupBackupV1'
RUN=PREFIX+'mealRotationTESTONLY__LegacyCleanupRunV1'
TIP='Add 1 tsp sesame oil just before serving.'
DIRS=[{'type':'step','text':'Cook rice in broth for 15 minutes.'},{'type':'step','text':'Stir in the green onions.'}]
BAD=TIP+'\n\nLinked Recipes\n\n![Image 1](https://recipesage.com/app/assets/imgs/logo_green_padded.png)\n## Thai garlic pork\n\nCreate an account or login to save this recipe to your collection.\nRegister/Login to Save\n_Created 1/2/2025, 3:04 PM\nLast edited 1/3/2025, 4:05 PM_'
ROOT=Path(__file__).resolve().parents[1]
HOOK="""window.autoTest={state:()=>({meals,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),storage:()=>privateAutoBackup.capture(),seed:()=>{const m=meals.find(m=>m.id===1),items=cookingItemTokens(m),step=items.steps[0].token,ing=items.ingredients[0].token;m.ingredientStepLinks=[{step,ingredients:[ing]}];persist();const c=cookingContext('original','Tuesday',m.cat,m);cookingSession(c).steps=[step];writeCookingSessions(cookingSessions)},change:()=>{meals.find(m=>m.id===1).notes='My later edit.\\n'+meals.find(m=>m.id===1).notes;persist()},restore:b=>{privateAutoBackup.restore(privateAutoBackup.normalize(b));backupRestoreReloadPending=true},tokens:()=>cookingItemTokens(meals.find(m=>m.id===1)),matches:()=>[...recipeIngredientMatches(meals.find(m=>m.id===1))]};"""
def instrument(html):
    return html.replace('function validateBackupCore(d){','window.privateAutoBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();')
def make_snapshot(browser):
    library=[base.meal(1,base.SAGE,name='Garlic Jasmine Rice with Cauliflower',rotation=True,instructions=DIRS,notes=BAD),base.meal(3,base.SAGE2,instructions='My manual directions.',notes='My manual notes.'),base.meal(50,'side',cat='Sides',name='Side',instructions='Boil the side.',linkedMealIds=[]),base.meal(51,'pork',cat='Sides',name='Thai garlic pork',instructions='Fry pork.',linkedMealIds=[])]
    ctx,page,errors,prefix=base.setup(browser,'meal-rotation-test.html',360,library=library)
    # base.setup disables only the new startup operation; preserve ordinary rendering/reconciliation.
    page.evaluate("(()=>{const m=repairTest.state().meals.find(m=>m.id===1);m.ingredientStepLinks=[{step:JSON.stringify(['step','','Cook rice in broth for 15 minutes.'])+'#0',ingredients:[JSON.stringify(['ingredient','','2 fish fillets'])+'#0']}];repairTest.persist();const s=repairTest.state().sessions;Object.values(s.occurrences).find(s=>s.context.day==='Tuesday').steps=[m.ingredientStepLinks[0].step];repairTest.saveProgress()})()")
    result=page.evaluate('repairTest.storage()');assert not errors;ctx.close();return result

def launch(browser,snapshot,width=360,failure=None,filename='meal-rotation-test.html'):
    ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,accept_downloads=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    html=instrument((ROOT/filename).read_text())
    seed={PREFIX+k:v for k,v in snapshot.items()};seed.update({'mealRotationDataV1':'WORKING APP UNTOUCHED','mealRotationCookingSessionsV1':'WORKING PROGRESS UNTOUCHED'})
    if filename=='index.html':seed={**snapshot,'production-sentinel':'keep'}
    script='''if(!sessionStorage.seed){for(const[k,v]of Object.entries(SEED))localStorage.setItem(k,v);sessionStorage.seed='1'}window.writeTrace=[];const originalSet=Storage.prototype.setItem,originalGet=Storage.prototype.getItem;Storage.prototype.setItem=function(k,v){window.writeTrace.push({key:k,value:String(v)});if(FAILURE==='backup'&&k===BACKUP)throw Error('Backup quota failure');if(FAILURE==='marker'&&k===RUN)throw Error('Marker quota failure');if(FAILURE==='primary'&&k===PREFIX+'mealRotationDataV1'&&originalGet.call(this,RUN))throw Error('Primary quota failure');if(FAILURE==='status'&&k===RUN&&String(v).includes('"complete"'))throw Error('Status quota failure');originalSet.call(this,k,v);if(FAILURE==='stale'&&k===BACKUP)originalSet.call(this,PREFIX+'mealRotationCustomSettingV9','external change')};Storage.prototype.getItem=function(k){const v=originalGet.call(this,k);if(FAILURE==='readback'&&k===BACKUP&&v)return v+'corrupt';return v};'''
    for a,b in [('SEED',json.dumps(seed)),('FAILURE',json.dumps(failure)),('BACKUP',json.dumps(BACKUP)),('RUN',json.dumps(RUN)),('PREFIX',json.dumps(PREFIX))]:script=script.replace(a,b)
    page.add_init_script(script)
    page.route('http://auto.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=html) if route.request.url.endswith(filename) else route.fulfill(status=200,body=''))
    page.route('https://**/*',lambda route:route.fulfill(status=200,body=''))
    page.goto('http://auto.test/'+filename);return ctx,page,errors

def run(browser,snapshot,width):
    ctx,page,errors=launch(browser,snapshot,width)
    original=json.loads(snapshot['mealRotationDataV1']);after=page.evaluate('autoTest.state()');saved=page.evaluate('autoTest.storage()')
    assert page.locator('#test-legacy-cleanup-status').inner_text().startswith('Test cleanup complete: 1 recipes cleaned.')
    assert page.locator('#recipeInstructionRepair').count()==0
    for a,b in zip(original['meals'],after['meals']):
        expected=copy.deepcopy(a)
        if a['id']==1:expected['notes']=TIP+'\n\n\n\n'
        assert b==expected,(a['id'],b.get('notes'))
    assert {k:v for k,v in saved.items() if k!='mealRotationDataV1'}=={k:v for k,v in snapshot.items() if k!='mealRotationDataV1'}
    assert after['sessions']==json.loads(snapshot['mealRotationCookingSessionsV1']) and after['scales']==json.loads(snapshot['mealRotationOccurrenceScalesV1'])
    raw=page.evaluate('(k)=>localStorage.getItem(k)',BACKUP);backup=json.loads(raw);assert backup['storage']==snapshot
    trace=page.evaluate('writeTrace');bi=next(i for i,x in enumerate(trace) if x['key']==BACKUP);mi=next(i for i,x in enumerate(trace) if x['key']==RUN);pi=next(i for i,x in enumerate(trace) if i>mi and x['key']==PREFIX+'mealRotationDataV1');assert bi<mi<pi
    assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING APP UNTOUCHED'
    assert page.evaluate('localStorage.getItem("mealRotationCookingSessionsV1")')=='WORKING PROGRESS UNTOUCHED'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    with tempfile.TemporaryDirectory() as tmp:
        with page.expect_download() as dl:page.get_by_role('button',name='Download pre-repair test backup',exact=True).click()
        target=Path(tmp)/'backup.json';dl.value.save_as(target);assert target.read_text()==raw
    before=page.evaluate('autoTest.state()');page.reload();assert page.evaluate('autoTest.state()')==before
    assert page.evaluate('(k)=>localStorage.getItem(k)',BACKUP)==raw
    # The one-time flag protects later user changes, and makes restoring the snapshot an undo.
    page.evaluate('autoTest.change()');edited=page.evaluate('autoTest.state()');page.reload();assert page.evaluate('autoTest.state()')==edited
    page.evaluate('(b)=>autoTest.restore(b)',backup);page.reload();assert page.evaluate('autoTest.storage()')==snapshot
    assert next(m for m in page.evaluate('autoTest.state().meals') if m['id']==1)['notes']==BAD
    assert not errors,errors;ctx.close();print('PASS',width,'automatic test-only cleanup, exact backup readback/download/undo, one-time/reload/later edits, field/progress/scaling/settings/grocery preservation, production isolation; no JS errors',flush=True)
def failures(browser,snapshot):
    for failure in ['backup','readback','marker','primary','stale','status']:
        ctx,page,errors=launch(browser,snapshot,failure=failure);after=page.evaluate('autoTest.state()');m=next(m for m in after['meals'] if m['id']==1)
        if failure=='status':assert m['notes'].strip()==TIP
        else:assert m['notes']==BAD,(failure,m['notes'])
        if failure!='stale':assert {k:v for k,v in page.evaluate('autoTest.storage()').items() if k!='mealRotationDataV1'}=={k:v for k,v in snapshot.items() if k!='mealRotationDataV1'}
        assert 'stopped' in page.locator('#test-legacy-cleanup-status').inner_text().lower() or failure=='status'
        assert not errors,(failure,errors);ctx.close();print('PASS failure:',failure,'retains original recipes or successful atomic result with verified backup',flush=True)
    # An existing different recovery snapshot is never overwritten.
    ctx,page,errors=launch(browser,snapshot);raw=page.evaluate('(k)=>localStorage.getItem(k)',BACKUP);page.evaluate('([run])=>localStorage.removeItem(run)',[RUN]);page.evaluate('(text)=>autoTest.state().meals.find(m=>m.id===1).notes=text',BAD);page.evaluate('autoTest.change()');edited=page.evaluate('autoTest.state()');page.reload();assert page.evaluate('autoTest.state()')==edited;assert 'earlier test backup' in page.locator('#test-legacy-cleanup-status').inner_text();assert page.evaluate('(k)=>localStorage.getItem(k)',BACKUP)==raw;ctx.close()
    clean=copy.deepcopy(snapshot);primary=json.loads(clean['mealRotationDataV1']);primary['meals'][0]['notes']=TIP;clean['mealRotationDataV1']=json.dumps(primary,separators=(',',':'),ensure_ascii=False)
    ctx,page,errors=launch(browser,clean);assert page.evaluate('autoTest.storage()')==clean;assert 'no confirmed legacy clutter' in page.locator('#test-legacy-cleanup-status').inner_text();assert page.evaluate('(k)=>localStorage.getItem(k)',BACKUP) is None;assert not errors;ctx.close()
    # Regular app has no startup cleanup and retains the contaminated note.
    assert 'runTestLegacyCleanupOnce' not in (ROOT/'index.html').read_text()
    ctx,page,errors=launch(browser,snapshot,filename='index.html');assert next(m for m in page.evaluate('autoTest.state().meals') if m['id']==1)['notes']==BAD;assert page.locator('#test-legacy-cleanup-status').count()==0;assert not errors;ctx.close();print('PASS existing backup preserved; regular app stays manual',flush=True)
if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);snapshot=make_snapshot(browser)
        for width in [320,360]:run(browser,snapshot,width)
        failures(browser,snapshot);browser.close()
