"""Onboarding regression in a disposable Chromium profile, never user storage."""
import os
from modular_browser_smoke import run


def checks(evaluate, command, wait_for, errors):
    def reload_page():
        origin=evaluate("performance.timeOrigin")
        # Do not let the old document's pagehide autosave overwrite a test fixture.
        evaluate("window.dispatchEvent(new Event('mealRotationBeforeStorageReset'))")
        command("Page.reload")
        wait_for("performance.timeOrigin!=="+str(origin)+"&&document.readyState==='complete'")

    def empty_library():
        # run() owns a newly created, temporary Chromium profile for this test.
        evaluate("window.localStorage.clear()")
        reload_page()
        wait_for("document.readyState==='complete'&&!!document.getElementById('onboardingWelcome')")

    def mobile_check():
        for width in (360, 375, 390, 414):
            command("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": 820, "deviceScaleFactor": 1, "mobile": True
            })
            result = evaluate("""({
                viewport:innerWidth,width:document.documentElement.scrollWidth,
                targets:[...document.querySelectorAll('.onboarding-actions button,.onboarding-dismiss')].map(b=>b.getBoundingClientRect().height)
            })""")
            assert result["width"] <= width and result["viewport"] == width, result
            assert all(height >= 44 for height in result["targets"]), result

    wait_for("!!document.getElementById('onboardingWelcome')")
    assert evaluate("cats.length===0&&meals.length===0&&!document.querySelector('[aria-modal=\"true\"]')"), "First run must be inline, not modal"
    assert evaluate("!document.querySelector('[data-week-row]')"), "Empty weekly grid should not appear"
    mobile_check()
    evaluate("document.getElementById('onboardingQuickStart').click()")
    wait_for("meals.length===9&&!!document.getElementById('onboardingHint')")
    sample = evaluate("""({
        groups:cats.length,meals:meals.length,days:getDisplayedWeekdayMeals().map(item=>item.day),
        welcome:!!document.getElementById('onboardingWelcome'),
        cookable:meals.every(m=>m.ingredients.length&&m.instructions.some(s=>s.text)),
        bytes:window.localStorage.getItem('mealRotationDataV1').length,
        noModal:!document.querySelector('[aria-modal="true"]')
    })""")
    assert sample["groups"] == 7 and sample["meals"] == 9 and len(set(sample["days"])) == 7, sample
    assert sample["cookable"] and not sample["welcome"] and sample["noModal"], sample
    assert sample["bytes"] < 12000, sample
    mobile_check()
    assert evaluate("""(()=>{
        const before=JSON.stringify({...window.localStorage});
        return quickStartSampleWeek()===false&&before===JSON.stringify({...window.localStorage});
    })()"""), "Repeated Quick-Start must be a no-op"
    reload_page()
    wait_for("document.readyState==='complete'&&!!document.getElementById('onboardingHint')")
    evaluate("document.querySelector('.onboarding-dismiss').click()")
    reload_page()
    wait_for("document.readyState==='complete'&&meals.length===9")
    assert evaluate("!document.getElementById('onboardingHint')&&window.localStorage.getItem(ONBOARDING_DISMISSED_KEY)==='true'"), "Dismissal must survive reload"
    empty_library()
    evaluate("document.getElementById('onboardingQuickStart').click()")
    wait_for("!!document.getElementById('onboardingHint')")
    evaluate("applyManualWeekdayMeal('Monday',cats[0],meals[1])")
    assert evaluate("!document.getElementById('onboardingHint')&&window.localStorage.getItem(ONBOARDING_DISMISSED_KEY)==='true'"), "Manual swap must permanently dismiss orientation"
    reload_page()
    wait_for("document.readyState==='complete'&&meals.length===9")
    assert evaluate("!document.getElementById('onboardingHint')"), "Swap dismissal must survive reload"
    print("PASS: inline first run, seven complete days/nine cookable samples, repeated seed no-op, explicit and manual-swap dismissals, 360–414px layouts.")

    empty_library()
    assert evaluate("""(()=>{
        const core=JSON.stringify({cats:['Existing'],active:'Existing',meals:[]});
        window.localStorage.setItem('mealRotationDataV1',core);
        window.localStorage.setItem('mealRotationSyntheticExtensionV1','do-not-change');
        const before=JSON.stringify({...window.localStorage});
        return !quickStartSampleWeek()&&before===JSON.stringify({...window.localStorage});
    })()"""), "A populated other tab must block stale Quick-Start"
    reload_page()
    wait_for("document.readyState==='complete'&&cats.includes('Existing')")
    assert evaluate("!document.getElementById('onboardingWelcome')&&!quickStartSampleWeek()"), "Categories alone must suppress onboarding"
    empty_library()
    evaluate("""window.localStorage.setItem('mealRotationDataV1',JSON.stringify({
        cats:[],active:'',meals:[{id:77,cat:'Unassigned',name:'Existing recipe',rotation:false,ingredients:[]}]
    }))""")
    reload_page()
    # The existing schema rejects orphaned recipes without a category catalog;
    # that must remain a protected recovery state, never permission to seed.
    assert evaluate("!document.getElementById('onboardingWelcome')&&!quickStartSampleWeek()&&JSON.parse(window.localStorage.getItem('mealRotationDataV1')).meals[0].name==='Existing recipe'"), "Orphaned recipes must suppress onboarding and remain protected"
    print("PASS: category-only, orphaned-recipe, and stale-tab fixtures are not seeded or overwritten.")

    empty_library()
    quota = evaluate("""(()=>{
        const before=window.localStorage.getItem('mealRotationDataV1'),native=Storage.prototype.setItem;
        Storage.prototype.setItem=function(k,v){
            if(this===window.localStorage)throw new DOMException('Synthetic full storage','QuotaExceededError');
            return native.call(this,k,v);
        };
        try{
            const seeded=quickStartSampleWeek();
            return {seeded,unchanged:window.localStorage.getItem('mealRotationDataV1')===before,
                empty:!cats.length&&!meals.length,message:document.getElementById('onboardingStatus')?.textContent};
        }finally{Storage.prototype.setItem=native}
    })()""")
    assert not quota["seeded"] and quota["unchanged"] and quota["empty"] and quota["message"], quota
    print("PASS: forced quota failure preserves the original empty library and reports an inline error.")

    empty_library()
    evaluate("""(()=>{
        const backup=sampleWeekBackup();backup.meals[0].name='Synthetic restored recipe';
        const original=HTMLInputElement.prototype.click;
        HTMLInputElement.prototype.click=function(){
            if(this.type!=='file')return original.call(this);
            sessionStorage.setItem('onboarding-test-accept',this.accept);
            Object.defineProperty(this,'files',{value:[new File([JSON.stringify(backup)],'test-backup.json',{type:'application/json'})]});
            this.dispatchEvent(new Event('change'));
        };
        document.getElementById('onboardingRestore').click();
    })()""")
    wait_for("document.readyState==='complete'&&meals.some(m=>m.name==='Synthetic restored recipe')&&!document.getElementById('onboardingWelcome')")
    assert evaluate("sessionStorage.getItem('onboarding-test-accept')==='.json,application/json,*/*'&&getDisplayedWeekdayMeals().length===7"), "Welcome restore must restore the week using the mobile JSON picker"
    assert not errors, errors
    print("PASS: welcome backup input restores a synthetic version-2 library and full schedule; zero browser JavaScript errors.")


if __name__ == "__main__":
    run("https://" + os.environ["REPLIT_DEV_DOMAIN"], checks=checks)
