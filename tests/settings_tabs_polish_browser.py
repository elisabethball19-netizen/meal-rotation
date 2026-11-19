"""Settings rows evenly spaced, Settings footer stays visible above the nav, folder-style meal tabs.

Run: python3 tests/settings_tabs_polish_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.pol={home:()=>{showMealPlanTabs=true;showTop=true;allMealsActive=false;groceryTabActive=false;render()}};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('pol.home()'); p.wait_for_timeout(300)
    sb.shot(p, name, 'polish-tabs')
    tab = p.locator('#list .meal-plan-tab.selected').bounding_box()
    strip = p.locator('#list .meal-plan-tabs').bounding_box()
    assert abs((tab['y'] + tab['height']) - (strip['y'] + strip['height'])) <= 1, (tab, strip)
    p.get_by_role('button', name='Settings and backups', exact=True).click(); p.wait_for_timeout(300)
    for summary in p.locator('#settingsPanel details > summary').all():
        if 'Display' in summary.inner_text():
            summary.click(); p.wait_for_timeout(300)
    heights = p.locator('#settingsPanel .settings-display-option:visible').evaluate_all('xs=>xs.filter(x=>!x.querySelector(".settings-display-option-help")).map(x=>Math.round(x.getBoundingClientRect().height))')
    sb.shot(p, name, 'polish-settings')
    one_line = [h for h in heights if h < 50]  # two-line labels wrap naturally
    assert one_line and max(one_line) - min(one_line) <= 2, heights
    gaps = p.evaluate("""()=>{const rows=[...document.querySelectorAll('#settingsPanel .settings-display-option')].filter(x=>x.offsetParent);const g=[];for(let i=1;i<rows.length;i++)g.push(Math.round(rows[i].getBoundingClientRect().top-rows[i-1].getBoundingClientRect().bottom));return g}""")
    assert len([g for g in gaps if g > 2]) <= 1 and max(gaps) <= 45, gaps  # only the defrost note sits between rows
    p.mouse.wheel(0, 400); p.wait_for_timeout(300)
    foot = p.locator('.settings-footer').bounding_box()
    nav = p.locator('#mealBottomNav').bounding_box()
    vh = p.viewport_size['height']
    assert foot['y'] + foot['height'] <= (nav['y'] if nav else vh) + 1 and foot['y'] > 0, (foot, nav)
    sb.shot(p, name, 'polish-settings-scrolled')
    assert not errors, errors
    c.close()
    print('PASS', name, 'settings spacing, sticky footer, folder tabs', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
