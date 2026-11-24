"""Settings > Display is split into five sections; the last opened is remembered for 5 minutes.

Run: python3 tests/display_sections_browser.py   (screenshots in /tmp/disp)
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/disp')
OUT.mkdir(parents=True, exist_ok=True)


def open_display(p):
    if p.locator('#topSettingsPanel, #settingsPanel').first.is_hidden():
        p.locator('#settings').click()
    p.locator('.settings-group[data-settings-group=display] > summary').click()


def ensure_display(p):
    grp = p.locator('.settings-group[data-settings-group=display]')
    if not grp.is_visible():
        p.locator('#settings').click()
        p.wait_for_timeout(300)
    if grp.get_attribute('open') is None:
        grp.locator('> summary').click()


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    p.clock.set_fixed_time(datetime(2026, 11, 16, 20, tzinfo=timezone.utc))
    p.locator('#settings').click()
    p.wait_for_timeout(300)
    grp = p.locator('.settings-group[data-settings-group=display]')
    if grp.get_attribute('open') is None:
        grp.locator('> summary').click()
    names = p.locator('.settings-subgroup > summary .settings-subname').all_text_contents()
    assert names == ['General', 'Meal cards', 'Make Ahead reminders', 'Groceries', 'Ask AI'], names
    assert p.locator('.settings-subgroup[open]').count() == 0, 'all collapsed at first'
    # Opening one closes the others and shows its settings.
    p.locator('.settings-subgroup[data-display-section=general] > summary').click()
    assert p.locator('.text-size-options input[type=radio]').count() == 3
    p.locator('.settings-subgroup[data-display-section=ai] > summary').click()
    p.wait_for_timeout(150)
    assert p.locator('.settings-subgroup[open]').count() == 1 and p.locator('.settings-subgroup[data-display-section=ai]').get_attribute('open') is not None
    assert p.locator('input[name=aiTarget]').count() == 6
    p.screenshot(path=str(OUT / f'{tag}-ai.png'))
    # Text size radios still apply.
    p.locator('.settings-subgroup[data-display-section=general] > summary').click()
    p.wait_for_timeout(150)
    p.locator('.text-size-options input[value=large]').check()
    assert p.evaluate('document.body.dataset.mealTextSize') == 'large'
    p.locator('.text-size-options input[value=normal]').check()
    # Status label shows Off when a master switch is off.
    p.locator('.settings-subgroup[data-display-section=ai]').evaluate('e=>e.open=true')
    p.locator('.settings-subgroup[data-display-section=ai] input[type=checkbox]').first.evaluate('e=>e.click()')
    assert p.locator('.settings-subgroup[data-display-section=ai] .settings-substatus').text_content() == 'Off'
    p.locator('.settings-subgroup[data-display-section=ai] input[type=checkbox]').first.evaluate('e=>e.click()')
    assert p.locator('.settings-subgroup[data-display-section=ai] .settings-substatus').text_content() == ''
    p.wait_for_timeout(600)
    # Remembered across a rebuild within 5 minutes, then reset to collapsed.
    ensure_display(p)
    p.locator('.settings-subgroup[data-display-section=make] > summary').click()
    p.wait_for_timeout(150)
    p.screenshot(path=str(OUT / f'{tag}-make.png'))
    p.reload()
    p.wait_for_timeout(500)
    p.clock.set_fixed_time(datetime(2026, 11, 16, 20, 3, tzinfo=timezone.utc))
    p.locator('#settings').click()
    open_grp = p.locator('.settings-group[data-settings-group=display]')
    if open_grp.get_attribute('open') is None:
        open_grp.locator('> summary').click()
    assert p.locator('.settings-subgroup[data-display-section=make]').get_attribute('open') is not None, 'remembered at 3 min'
    p.reload()
    p.wait_for_timeout(500)
    p.clock.set_fixed_time(datetime(2026, 11, 16, 20, 9, tzinfo=timezone.utc))
    p.locator('#settings').click()
    open_grp = p.locator('.settings-group[data-settings-group=display]')
    if open_grp.get_attribute('open') is None:
        open_grp.locator('> summary').click()
    assert p.locator('.settings-subgroup[open]').count() == 0, 'collapsed after 5+ minutes'
    assert not errors, errors
    c.close()
    print(name, 'ok')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ['index.html', 'meal-rotation-test.html']:
        run(b, n)
    b.close()
