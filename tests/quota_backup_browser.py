"""Quota recovery and V2 import regressions. Disposable contexts; synthetic storage only."""
import copy
import json
import re
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = 'mealRotationRecoveryJournalV1'
CORE_KEY = 'mealRotationDataV1'
CORE = {'cats': ['Dinner', 'Soup'], 'active': 'Dinner', 'meals': [
    {'id': 1, 'name': 'Synthetic stew', 'cat': 'Dinner', 'rotation': True,
     'ingredients': ['1 cup rice'], 'instructions': 'Stir.'},
    {'id': 2, 'name': 'Synthetic soup', 'cat': 'Soup', 'rotation': True,
     'ingredients': ['2 cups water'], 'instructions': 'Boil.'}]}
HOOK = """
window.quotaTest={
 normalize:normalizeImportedBackup,validate:validateBackupStorage,items:recipeImportItems,tags:recipeImportTags,
 capture:captureBackupStorage,settings:()=>settings.click(),picker:openRecipeImportFilePicker,
 state:()=>({cats,meals,mealPlans,weekdayCategories,weekdayMealOverrides,cookingSessions,
 checkedIngredients:[...checkedIngredients],timeDisplayPrefs,applyPinsToAllTabs,masterOpenMode}),
 factory:eval('('+createMealPersistence.toString().replace('return {storage,inspect',
 'return {saveJournal,startFresh,replace,storage,inspect')+')')
};
"""


def source(name):
    text = (ROOT / name).read_text()
    if name == 'index.html':
        text = re.sub(r'<script src="\./([^"]+\.js)"></script>',
                      lambda m: '<script>\n' + (ROOT / m[1]).read_text() + '\n</script>', text)
    return text.replace('mealPersistence.showRecovery({normalize:', HOOK + 'mealPersistence.showRecovery({normalize:', 1)


def setup(browser, name, data=None, init=''):
    prefix = 'mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
    seed = {prefix + k: v for k, v in (data or {CORE_KEY: json.dumps(CORE)}).items()}
    seed['unrelated-setting'] = 'KEEP'
    seed[('mealRotationDataV1' if prefix else 'mealRotationTestSandboxV1:mealRotationDataV1')] = 'OTHER APP'
    context = browser.new_context(accept_downloads=True, viewport={'width': 800, 'height': 850})
    page = context.new_page()
    page.set_default_timeout(7000)
    errors = []
    page.on('pageerror', lambda e: errors.append(e.stack))
    page.add_init_script("""if(!sessionStorage.seeded){
      for(const[k,v] of Object.entries(%s))localStorage.setItem(k,v);
      sessionStorage.seeded='yes';
    }""" % json.dumps(seed) + '\n' + init)
    page.route('https://quota.test/**', lambda r: r.fulfill(
        content_type='text/html', body=source(name)) if r.request.url.endswith(name)
        else r.fulfill(body=''))
    page.goto('https://quota.test/' + name)
    return context, page, errors, prefix


def upload(page, data, recovery=False, success=False):
    if recovery:
        button = page.locator('#mealDataRecovery').get_by_role('button', name='Restore Backup', exact=True)
    else:
        page.evaluate('quotaTest.settings()')
        page.get_by_text('Data & Backups', exact=True).click()
        button = page.get_by_role('button', name='Restore backup', exact=True)
    with page.expect_file_chooser() as chooser:
        button.click()
    assert chooser.value.element.get_attribute('accept') == '.json,application/json,*/*'
    payload = {'name': 'synthetic.json', 'mimeType': 'application/json', 'buffer': json.dumps(data).encode()}
    if success:
        with page.expect_navigation(wait_until='load'):
            chooser.value.set_files(payload)
    else:
        chooser.value.set_files(payload)


def fresh(browser, name):
    for raw in ['{malformed' + 'x' * 180000,
                json.dumps({'version': 1, 'originalStorage': {CORE_KEY: 'x' * 100000},
                            'previousAttempts': [{'legacy': 'y' * 5000}] * 30})]:
        data = {CORE_KEY: '{broken', JOURNAL: raw, 'mealRotationTextSizeV1': 'large'}
        # Fault-inject quota after synthetic seeding, and save the operation log across reload.
        init = """const set=Storage.prototype.setItem,remove=Storage.prototype.removeItem;
        if(!sessionStorage.freshTrace){
         Storage.prototype.setItem=function(k,v){
          if(this===window.localStorage){const log=JSON.parse(sessionStorage.freshLog||'[]');log.push(['set',k]);
           set.call(sessionStorage,'freshLog',JSON.stringify(log));throw new DOMException('Full','QuotaExceededError')}
          return set.call(this,k,v)
         };
         Storage.prototype.removeItem=function(k){
          if(this===window.localStorage){const log=JSON.parse(sessionStorage.freshLog||'[]');log.push(['remove',k]);
           set.call(sessionStorage,'freshLog',JSON.stringify(log))}
          return remove.call(this,k)
         };
        }"""
        c, p, errors, prefix = setup(browser, name, data, init)
        expect(p.locator('#mealDataRecovery')).to_be_visible()
        p.get_by_role('button', name='Start Fresh', exact=True).click()
        p.get_by_role('button', name='Cancel Start Fresh', exact=True).click()
        assert p.evaluate('sessionStorage.freshLog') is None
        p.get_by_role('button', name='Start Fresh', exact=True).click()
        # Keep quota blocking through deletion, but permit normal initialization on reload.
        p.evaluate('sessionStorage.freshTrace="confirmed"')
        p.get_by_role('button', name='Confirm Start Fresh', exact=True).click()
        p.wait_for_function('window.quotaTest && !document.querySelector("#mealDataRecovery")')
        log = p.evaluate('JSON.parse(sessionStorage.freshLog)')
        assert log and all(x[0] == 'remove' for x in log), log
        assert {x[1] for x in log} == {prefix + k for k in data}
        assert p.evaluate('k=>window.localStorage.getItem(k)', prefix + JOURNAL) is None
        assert p.evaluate('quotaTest.state().meals') == []
        assert p.evaluate('window.localStorage.getItem("unrelated-setting")') == 'KEEP'
        assert p.evaluate('k=>window.localStorage.getItem(k)', CORE_KEY if prefix else 'mealRotationTestSandboxV1:' + CORE_KEY) == 'OTHER APP'
        assert not errors, errors
        c.close()
    # Both throwing and silently ignored deletions must leave recovery paused and visible.
    for silent in [False, True]:
        c, p, errors, prefix = setup(browser, name, {CORE_KEY: '{broken'})
        p.evaluate("""silent=>{Storage.prototype.removeItem=function(){
            if(!silent)throw Error('Deletion denied')
        }}""", silent)
        p.get_by_role('button', name='Start Fresh', exact=True).click()
        p.get_by_role('button', name='Confirm Start Fresh', exact=True).click()
        expect(p.locator('#mealRecoveryStatus')).to_contain_text('could not finish')
        assert p.evaluate('k=>window.localStorage.getItem(k)', prefix + CORE_KEY) == '{broken'
        assert not errors, errors
        c.close()
    print('PASS', name, 'deletion-only fresh at quota, huge/bad journals, isolation, deletion failures', flush=True)


def journals(browser, name):
    c, p, errors, _ = setup(browser, name)
    result = p.evaluate("""()=>{
     const key='mealRotationRecoveryJournalV1',core='mealRotationDataV1';
     const make=(seed={},mode='ok')=>{
      const map=new Map(Object.entries(seed)),writes=[];
      let count=0;
      const base={get length(){return map.size},key:i=>[...map.keys()][i]??null,
       getItem:k=>map.get(k)??null,removeItem:k=>map.delete(k),
       setItem(k,v){writes.push({key:k,value:v});count++;
        if(mode==='quota'||mode==='once'&&count===1)throw new DOMException('Full','QuotaExceededError');
        map.set(k,String(v))}};
      return {map,writes,p:quotaTest.factory(()=>base)};
     };
     const value=()=>({version:1,originalStorage:{[core]:'ORIGINAL'},replacement:{},
       previousAttempts:Array.from({length:20},(_,i)=>({marker:i,text:'x'.repeat(7000)}))});
     const bounded=make();if(!bounded.p.saveJournal(value()))throw Error('bounded save');
     const saved=JSON.parse(bounded.map.get(key));
     if(saved.previousAttempts.length>6||new Blob([bounded.map.get(key)]).size>51200)throw Error('journal bounds');
     if(saved.previousAttempts.at(-1).marker!==19)throw Error('newest lost');
     const once=make({},'once');if(!once.p.saveJournal(value())||once.writes.length!==2)throw Error('retry missing');
     const first=JSON.parse(once.writes[0].value),last=JSON.parse(once.writes[1].value);
     if(last.previousAttempts.length>=first.previousAttempts.length||last.previousAttempts.at(-1).marker!==19)throw Error('oldest not dropped');
     const full=make({},'quota');if(full.p.saveJournal(value())||full.writes.length!==2)throw Error('quota escaped');
     const huge=make(),essential=value();essential.originalStorage[core]='x'.repeat(100000);
     if(huge.p.saveJournal(essential)||huge.writes.length)throw Error('essential rollback truncated');
     const startupJournal={version:1,originalStorage:{[core]:'old'},replacement:{[core]:'new'}};
     const startup=make({[core]:'new',[key]:JSON.stringify(startupJournal)},'quota');
     startup.p.inspect(()=>{});
     if(startup.p.recovery||startup.writes.length!==2)throw Error('startup quota loop');
     startup.p.finishStartup();
     if(startup.map.has(key)||startup.p.recovery)throw Error('startup cleanup trapped');
     const next=make(Object.fromEntries(startup.map));next.p.inspect(()=>{});next.p.finishStartup();
     if(next.p.recovery)throw Error('reload trapped');
     return {size:new Blob([bounded.map.get(key)]).size,attempts:saved.previousAttempts.length};
    }""")
    assert not errors, errors
    c.close()
    print('PASS', name, 'all journal writes, quota retry/drop-oldest, complete snapshots, startup cleanup', result, flush=True)


def fixture():
    d = {'version': 2, **copy.deepcopy(CORE)}
    categories = {'Monday': ['Dinner'], 'Tuesday': ['Soup']}
    overrides = {'Monday::Dinner': '1', 'Tuesday::Soup': '2'}
    d.update(weekdayCategories=categories, weekdayMealOverrides=overrides,
             mealPlans={'plans': [
                 {'id': 'original', 'name': 'Home', 'weekdayCategories': categories,
                  'weekdayMealOverrides': overrides, 'pinnedCats': ['Dinner']},
                 {'id': 'away', 'name': 'Away', 'weekdayCategories': {'Friday': ['Soup']},
                  'weekdayMealOverrides': {'Friday::Soup': '2'}}], 'activeId': 'original'},
             checkedIngredients=['rice'], applyPinsToAllTabs=True, masterOpenMode='none',
             timeDisplayPrefs={'top': {'cooking': True, 'marinate': False}},
             showMealPlanTabs=True, weekdayColors={'Monday': '#112233'},
             categoryColors={'Dinner': '#445566'})
    context = {'planId': 'original', 'day': 'Monday', 'cat': 'Dinner', 'mealId': '1', 'parentId': ''}
    d['cookSessions'] = {'version': 1, 'occurrences': {
        '["original","Monday","1",""]': {'id': 'synthetic-progress', 'context': context,
                                       'ingredients': ['["ingredient","","1 cup rice"]#0'],
                                       'steps': ['["step","","Stir."]#0']}}}
    stale = copy.deepcopy(CORE);stale['meals'][0]['name'] = 'Stale storage recipe'
    d['storage'] = {CORE_KEY: json.dumps(stale), 'mealRotationCheckedIngredientsV1': '["storage-only"]',
                    'mealRotationCookingSessionsV1': '{"version":1,"occurrences":{}}',
                    'mealRotationTextSizeV1': 'large', 'mealRotationSelectedIngredientsV1': '{"1":["1 cup rice"]}'}
    return d


def imports(browser, name):
    c, p, errors, prefix = setup(browser, name)
    d = fixture()
    recipes = copy.deepcopy(d)
    recipes['meals'][1]['cat'] = ['Soup', 'Quick']
    recipes['meals'][0]['tags'] = ['Direct']
    tags = p.evaluate("""d=>quotaTest.items(d).map(r=>({name:r.name,tags:quotaTest.tags(r)}))""", recipes)
    assert len(tags) == 2 and set(tags[0]['tags']) == {'Direct', 'Dinner'} and set(tags[1]['tags']) == {'Soup', 'Quick'}, tags
    assert p.evaluate('d=>quotaTest.items({meals:d.meals}).length', recipes) == 2
    # Existing recipe formats stay available.
    assert p.evaluate("""()=>[
      quotaTest.items({recipes:[{name:'A',categories:['Old']}]}).length,
      quotaTest.items({'@graph':[{'@type':'Recipe',name:'B'}]}).length,
      quotaTest.items({items:[{title:'C'}]}).length,
      quotaTest.items({cards:[{id:'1',idList:'L',name:'D',desc:''}],lists:[{id:'L',name:'Old'}]}).length
    ]""") == [1, 1, 1, 1]
    # Actual recipe-only picker must accept meals and leave plan/progress/settings records alone.
    plan_before = p.evaluate('quotaTest.state().mealPlans')
    with p.expect_file_chooser() as chooser:
        p.evaluate('quotaTest.picker()')
    assert '*/*' in chooser.value.element.get_attribute('accept')
    chooser.value.set_files({'name': 'recipes.json', 'mimeType': 'application/json',
                            'buffer': json.dumps(recipes).encode()})
    dialog = p.get_by_role('dialog', name='Choose meal groups', exact=True)
    expect(dialog).to_contain_text('2 recipes found')
    dialog.get_by_role('button', name='Select all', exact=True).click()
    dialog.get_by_role('button', name='Import recipes', exact=True).click()
    p.wait_for_function('!document.querySelector("#recipeImportDialog")')
    p.get_by_role('alertdialog').get_by_role('button', name='OK', exact=True).click()
    imported = p.evaluate('quotaTest.state().meals')
    assert any(m['name'] == 'Synthetic soup' and m['cat'] == 'Quick' for m in imported), imported
    assert p.evaluate('quotaTest.state().mealPlans') == plan_before
    # Invalid full backup must be rejected without mutating persisted data.
    before = p.evaluate('quotaTest.capture()')
    invalid = copy.deepcopy(d);invalid['checkedIngredients'] = {}
    p.on('dialog', lambda dialog: dialog.accept())
    with p.expect_event('dialog') as rejection:
        upload(p, invalid)
    assert 'Backup rejected' in rejection.value.message
    assert p.evaluate('quotaTest.capture()') == before
    p.evaluate('quotaTest.settings()')  # close the still-open panel before the next upload
    upload(p, d, success=True)
    p.wait_for_function('window.quotaTest && quotaTest.state().meals[0]?.name==="Synthetic stew" && quotaTest.state().applyPinsToAllTabs')
    state = p.evaluate('quotaTest.state()')
    assert len(state['mealPlans']) == 2 and state['checkedIngredients'] == ['rice'], state
    assert state['cookingSessions'] == d['cookSessions']
    assert state['timeDisplayPrefs']['top']['cooking'] is True and state['masterOpenMode'] == 'none'
    assert state['weekdayCategories']['Monday'] == ['Dinner']
    assert str(state['weekdayMealOverrides']['Monday::Dinner']) == '1'
    stored = p.evaluate('quotaTest.capture()')
    assert json.loads(stored['mealRotationSelectedIngredientsV1']) == {'1': ['1 cup rice']}
    assert stored['mealRotationTextSizeV1'] == 'large'
    # Real export UI, then restore/reload the export and also a storage-only V2 document.
    p.evaluate('quotaTest.settings()')
    p.get_by_text('Data & Backups', exact=True).click()
    with p.expect_download() as download:
        p.get_by_role('button', name='Export backup', exact=True).click()
    exported = json.loads(Path(download.value.path()).read_text())
    p.evaluate('quotaTest.settings()')
    top_only = {k: v for k, v in d.items() if k != 'storage'}
    for backup in [exported, top_only, {'version': 2, 'storage': exported['storage']}]:
        upload(p, backup, success=True)
        p.wait_for_function('window.quotaTest && quotaTest.state().checkedIngredients.includes("rice")')
        assert p.evaluate('quotaTest.state().cookingSessions') == d['cookSessions']
        assert len(p.evaluate('quotaTest.state().mealPlans')) == 2
    assert not errors, errors
    c.close()
    # Recovery restore accepts the same top-level and storage-only V2 formats.
    for backup in [d, {'version': 2, 'storage': p_storage(d)}]:
        c, p, errors, prefix = setup(browser, name, {CORE_KEY: '{broken'})
        upload(p, backup, recovery=True, success=True)
        p.wait_for_function('window.quotaTest && !document.querySelector("#mealDataRecovery")')
        assert p.evaluate('quotaTest.state().cookingSessions') == d['cookSessions']
        assert not errors, errors
        c.close()
    print('PASS', name, 'V2 meals/tags, formats, full restore, precedence, plans/progress/settings, export/reimport', flush=True)


def journal_fallback(browser, name):
    original = '{synthetic corrupt original'
    c, p, errors, prefix = setup(browser, name, {CORE_KEY: original})
    p.evaluate("""()=>{
     const set=Storage.prototype.setItem;
     window.allowCore=false;
     Storage.prototype.setItem=function(k,v){
      if(k.endsWith('mealRotationRecoveryJournalV1')||!window.allowCore&&k.endsWith('mealRotationDataV1'))
       throw new DOMException('Full','QuotaExceededError');
      return set.call(this,k,v)
     };
    }""")
    upload(p, fixture(), recovery=True)
    expect(p.locator('#mealRecoveryStatus')).to_contain_text('in memory')
    with p.expect_download() as download:
        p.get_by_role('button', name='Export Data for Recovery', exact=True).click()
    recovered = json.loads(Path(download.value.path()).read_text())
    assert recovered['originalStorage'][CORE_KEY] == original
    assert json.loads(recovered['recoveryJournal']['replacement'][CORE_KEY])['meals'] == CORE['meals']
    assert p.evaluate('k=>window.localStorage.getItem(k)', prefix + JOURNAL) is None
    # A valid replacement may succeed when the journal alone remains at quota.
    p.evaluate('window.allowCore=true')
    upload(p, fixture(), recovery=True, success=True)
    assert not p.locator('#mealDataRecovery').count() and not errors, errors
    assert p.evaluate('quotaTest.state().cookingSessions') == fixture()['cookSessions']
    c.close()
    print('PASS', name, 'restore at journal quota, failed rollback recovery export, retry without stale journal', flush=True)


def p_storage(d):
    # Same mapping asserted through the app, assembled here for a storage-only recovery fixture.
    storage = dict(d['storage'])
    for field, key in [('mealPlans', 'mealRotationPlansV1'), ('cookSessions', 'mealRotationCookingSessionsV1'),
                       ('checkedIngredients', 'mealRotationCheckedIngredientsV1'),
                       ('weekdayCategories', 'mealRotationWeekdayCategoriesV1'),
                       ('weekdayMealOverrides', 'mealRotationWeekdayMealOverridesV1')]:
        storage[key] = json.dumps(d[field])
    return storage


if __name__ == '__main__':
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            for check in [fresh, journals, imports, journal_fallback]:
                check(browser, name)
        browser.close()
