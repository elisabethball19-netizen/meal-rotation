"""Isolated mobile refresh, atomic safety backup, matching and preservation checks.
Optional --backup/--export paths are private fixtures and never enter the repository.
"""
import argparse, copy, json, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import instruction_repair_browser as fixture
ROOT=Path(__file__).resolve().parents[1]
HOOK='''window.refreshTest={plan:r=>recipeSageRefreshPlan(recipeImportItems(r)),planLibrary:(r,library)=>recipeSageRefreshPlan(recipeImportItems(r),library),seedSession:s=>{cookingSessions.occurrences.example=s},state:()=>({cats,active,meals}),storage:()=>refreshBackup.capture(),restore:b=>refreshBackup.restore(refreshBackup.normalize(b)),tokens:m=>cookingItemTokens(m),failBackup:()=>{IDBObjectStore.prototype.put=function(){throw Error('Injected backup failure')}},failBackupReadback:()=>{IDBObjectStore.prototype.get=function(){const r={result:'corrupt'};queueMicrotask(()=>r.onsuccess());return r}},failWrite:()=>{const orig=localStorage.setItem.bind(localStorage);localStorage.setItem=(k,v)=>{if(k==='mealRotationDataV1')throw Error('Injected write failure');orig(k,v)}},mutateWhileBacking:()=>{const orig=storeRecipeSageSafetyBackup;storeRecipeSageSafetyBackup=async(...args)=>{const text=await orig(...args);localStorage.setItem('mealRotationCustomSettingV9','changed elsewhere');return text}}};'''
def setup(browser,filename,backup=None,width=360):
    ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,accept_downloads=True)
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    src=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.refreshBackup={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){')
    src=src.replace('render();runTestLegacyCleanupOnce();window.history','render();window.history')
    src=src.replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
    if backup:
        storage=backup.get('storage') or {'mealRotationDataV1':json.dumps({k:backup[k] for k in ['cats','active','meals']})}
    else:
        library=[fixture.meal(1,fixture.SAGE,rotation=True,instructions='Old instruction.'),fixture.meal(2,fixture.SAGE2,name='Side'),fixture.meal(3,'',name='Unique Name',url=''),fixture.meal(4,'',name='Ambiguous',url=''),fixture.meal(5,'',name='Ambiguous',url='')]
        storage={'mealRotationDataV1':json.dumps({'cats':['Fish','Dinner','Sides'],'active':'Fish','meals':library}),'mealRotationTutorialStageV1':'done','mealRotationCustomSettingV9':'preserve'}
    seed={prefix+k:v for k,v in storage.items()}
    if prefix:seed['mealRotationDataV1']='PRODUCTION SENTINEL'
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
    page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
    page.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
    page.goto('http://meal.test/'+filename);page.get_by_role('button',name='Settings and backups',exact=True).click()
    page.locator('details[data-settings-group="backups"]').evaluate('(e)=>e.open=true')
    assert page.get_by_text('Repair RecipeSage Imports',exact=True).count()==0
    return ctx,page,errors,prefix

def upload(page,sources):
    with page.expect_file_chooser() as chooser:page.get_by_role('button',name='Choose RecipeSage export file',exact=True).click()
    chooser.value.set_files({'name':'recipesage.jsonld','mimeType':'application/json','buffer':json.dumps(sources).encode()})
    page.wait_for_function("!document.querySelector('#recipeSageRefresh button:nth-last-of-type(1)').disabled")

def run(browser,filename,backup=None,export=None,width=360):
    ctx,page,errors,prefix=setup(browser,filename,backup,width)
    sources=export or [fixture.source(fixture.SAGE),fixture.source(fixture.SAGE2,name='Side'),fixture.source('33345678-1234-1234-1234-123456789abc',name='Unique Name'),fixture.source('44445678-1234-1234-1234-123456789abc',name='Ambiguous')]
    before=page.evaluate('refreshTest.state()');saved=page.evaluate('refreshTest.storage()')
    upload(page,sources)
    assert page.evaluate('refreshTest.storage()')==saved
    plan=page.evaluate('(x)=>refreshTest.plan(x)',sources);rows=plan['rows']
    assert rows, 'No refreshable records'
    with tempfile.TemporaryDirectory() as tmp:
        with page.expect_download() as download:page.get_by_role('button',name='Refresh Recipes',exact=True).click()
        path=Path(tmp)/'safety.json';download.value.save_as(path);safety=json.loads(path.read_text())
        assert safety['storage']==saved
        page.wait_for_function("document.querySelector('#recipeSageRefresh [role=status]').textContent.includes('recipes refreshed.')")
        after=page.evaluate('refreshTest.state()');stored=page.evaluate('refreshTest.storage()')
        assert set(stored)==set(saved)
        assert {k:v for k,v in stored.items() if k!='mealRotationDataV1'}=={k:v for k,v in saved.items() if k!='mealRotationDataV1'}
        assert len(before['meals'])==len(after['meals'])
        changed=0
        allowed={'ingredients','instructions','notes','recipeSageImportedNotes'}
        for old,new in zip(before['meals'],after['meals']):
            assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed},old['name']
            if old!=new:changed+=1
            if old.get('notes')=='My handwritten notes':assert new['notes']==old['notes']
        # Idempotence, persistence and restore of the complete backup.
        page.get_by_role('button',name='Refresh Recipes',exact=True).click()
        page.wait_for_function("document.querySelector('#recipeSageRefresh [role=status]').textContent.includes('recipes refreshed.')")
        assert page.evaluate('refreshTest.state()')==after
        page.reload();assert page.evaluate('refreshTest.state()')==after
        page.evaluate('(b)=>refreshTest.restore(b)',safety)
        assert page.evaluate('refreshTest.storage()')==saved
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if prefix:assert page.evaluate("localStorage.getItem('mealRotationDataV1')")=='PRODUCTION SENTINEL'
    assert not errors,errors
    print(filename,'actual' if backup else 'fixture',len(rows),'refreshed',len(plan['skipped']),'skipped',changed,'changed; complete backup/restore, preservation, repeat, reload PASS')
    ctx.close()

def matching(browser,filename):
    ctx,page,errors,prefix=setup(browser,filename)
    def plan(sources,library):return page.evaluate('([r,m])=>refreshTest.planLibrary(r,m)',[sources,library])
    base=fixture.meal(90,fixture.SAGE)
    valid=fixture.source(fixture.SAGE)
    assert len(plan([valid],[{**base,'name':'Personally renamed recipe'}])['rows'])==1
    assert not plan([valid,valid],[base])['rows']
    assert not plan([valid],[{**base,'recipeSageId':fixture.SAGE2,'importSourceId':fixture.SAGE2,'url':''}])['rows']
    # Exact-title fallback is unique on both sides; differently punctuated titles differ.
    bare={**base,'recipeSageId':'','importSourceId':'','url':''}
    assert len(plan([valid],[bare])['rows'])==1
    assert not plan([valid],[bare,{**bare,'id':91}])['rows']
    assert not plan([{**valid,'name':valid['name']+'!'}],[bare])['rows']
    # Proven category copies can all refresh without creating records.
    assert len(plan([valid],[base,{**base,'id':91,'cat':'Dinner','linkGroup':'copy'}])['rows'])==2
    assert not plan([{**valid,'recipeInstructions':[]}],[base])['rows']
    assert not plan([{**valid,'recipeIngredient':[]}],[base])['rows']
    # Notes of uncertain authorship stay verbatim; exact imported notes can refresh.
    source={**valid,'notes':'Useful source note\nCreate an account or login to save this recipe\nCreated: 2026-05-01'}
    original={**base,'notes':source['notes']}
    proposed=plan([source],[original])['rows'][0]['replacement']
    assert 'Create an account' not in proposed['notes']
    assert plan([source],[{**base,'notes':'My personal tip'}])['rows'][0]['replacement']['notes']=='My personal tip'
    # Missing notes must not erase earlier source notes.
    without={k:v for k,v in valid.items() if k not in ['notes','description']}
    assert plan([without],[{**base,'notes':'Imported earlier','recipeSageImportedNotes':'Imported earlier'}])['rows'][0]['replacement']['notes']=='Imported earlier'
    # Saved associations and progress whose tokens would disappear must be preserved by skipping.
    linked={**base,'ingredientStepLinks':[{'step':'old-step','ingredients':['old-ingredient']}]}
    assert not plan([valid],[linked])['rows']
    page.evaluate('refreshTest.seedSession({context:{mealId:"90"},ingredients:[],steps:["old-step"]})')
    assert not plan([valid],[base])['rows']
    # Identical refreshed content retains valid links and completed occurrence tokens.
    page.evaluate('refreshTest.seedSession({context:{mealId:"other"},ingredients:[],steps:[]})')
    identical=plan([valid],[base])['rows'][0]['replacement']
    tokens=page.evaluate('(m)=>refreshTest.tokens(m)',identical)
    it=tokens['ingredients'][0]['token'];st=next(t['token'] for t in tokens['steps'] if t.get('token'))
    identical['ingredientStepLinks']=[{'step':st,'ingredients':[it]}]
    page.evaluate('(s)=>refreshTest.seedSession(s)',{'context':{'mealId':'90'},'ingredients':[it],'steps':[st]})
    assert len(plan([valid],[identical])['rows'])==1
    assert not errors,errors
    ctx.close();print(filename,'matching/ambiguity/renames/incomplete/notes/association/progress guards PASS')

def failures(browser,filename):
    for failure in ['failBackup','failBackupReadback','failWrite','mutateWhileBacking']:
        ctx,page,errors,prefix=setup(browser,filename)
        before=page.evaluate('refreshTest.state()');saved=page.evaluate('refreshTest.storage()')
        upload(page,[fixture.source(fixture.SAGE)])
        page.evaluate('refreshTest.'+failure+'()');page.get_by_role('button',name='Refresh Recipes',exact=True).click()
        page.wait_for_function("!document.querySelector('#recipeSageRefresh button:nth-last-of-type(1)').disabled")
        assert page.evaluate('refreshTest.state()')==before
        assert page.evaluate('refreshTest.storage()')['mealRotationDataV1']==saved['mealRotationDataV1']
        assert not errors,errors
        ctx.close()
    print(filename,'backup write/readback failure, primary write failure, concurrent mutation PASS')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--backup');parser.add_argument('--export');args=parser.parse_args()
    backup=json.loads(Path(args.backup).read_text()) if args.backup else None
    export=json.loads(Path(args.export).read_text()) if args.export else None
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            run(browser,filename);run(browser,filename,width=320);matching(browser,filename);failures(browser,filename)
            if backup:run(browser,filename,backup,export)
        browser.close()
