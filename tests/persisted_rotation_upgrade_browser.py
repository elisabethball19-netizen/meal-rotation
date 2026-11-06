"""Replay committed pre-fix storage, not a newly initialized app.

The constructed legacy empty-flag probe remains an expectedFailure.
Full pre-#79 and pre-#80 saved-history upgrades must pass.
These fixtures are synthetic; none contains the user's saved app data.
"""
import json
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tests/fixtures/rotation-upgrades'
HOOK='''window.upgradeTest={
 picks:()=>Object.fromEntries(getDisplayedWeekdayMeals().filter(x=>x.cat==='Weekend').map(x=>[x.day,String(x.meal.id)])),
 cycle:()=>moveDisplayedMealsToBottom(),back:()=>rotateAllBack(),
 recipes:()=>JSON.stringify([...meals].sort((a,b)=>String(a.id).localeCompare(String(b.id)))),
 history:()=>localStorage.getItem(ROTATION_BACK_KEY)
};'''

class PersistedUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop()

    def replay(self,filename,fixture):
        saved=json.loads((FIXTURES/fixture).read_text());storage=saved['storage']
        prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
        source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
        ctx=self.browser.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True)
        p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        # Storage is present before the app starts. Reloads never re-seed it.
        seed={prefix+key:value for key,value in storage.items()}
        if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
        p.add_init_script('if(!sessionStorage.fixtureLoaded){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.fixtureLoaded="1"}')
        p.route('http://upgrade.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
        p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
        try:
            p.goto('http://upgrade.test/'+filename)
            self.assertEqual(p.evaluate('upgradeTest.history()'),storage.get('mealRotationLastRotationBeforeV1'))
            recipes=p.evaluate('upgradeTest.recipes()')
            if saved['rotateBackOnLoad']:p.evaluate('upgradeTest.back()')
            observed=[]
            for _ in range(3):
                p.reload();p.evaluate('upgradeTest.cycle()');observed.append(p.evaluate('upgradeTest.picks()'))
                p.reload();p.evaluate('upgradeTest.back()');p.reload()
            self.assertEqual(p.evaluate('upgradeTest.recipes()'),recipes,'Replay changed recipe data')
            if prefix:self.assertEqual(p.evaluate("localStorage.getItem('mealRotationDataV1')"),'WORKING SENTINEL')
            self.assertFalse(errors,errors)
            print('OBSERVED',fixture,filename,observed,flush=True)
            self.assertEqual(observed,[{'Saturday':'2','Sunday':'3'}]*3,(fixture,filename,observed))
        finally:ctx.close()


def case(filename,fixture):
    def test(self):self.replay(filename,fixture)
    return test

for filename,tag in [('index.html','production'),('meal-rotation-test.html','sandbox')]:
    setattr(PersistedUpgrade,'test_pre80_saved_history_'+tag,case(filename,'pre80-after-cycle.json'))
    setattr(PersistedUpgrade,'test_pre79_missing_both_deferrals_'+tag,case(filename,'pre79-after-cycle.json'))
    setattr(PersistedUpgrade,'test_legacy_empty_slot_'+tag,unittest.expectedFailure(case(filename,'pre80-legacy-empty.json')))

if __name__=='__main__':unittest.main(verbosity=2)
