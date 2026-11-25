"""2026-11-24: an automatic defrost/marinate/sourdough reminder disappears once its meal's Last cooked date is on or after
the day it was scheduled; manual tasks hide the same way; an older Last cooked date does not hide it. Run: python3 tests/prep_cooked_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s

s.fixture.HOOK += '''window.pc={check:()=>{const mk=(auto,scheduled,last)=>({task:{autoPrep:auto,id:'t'},scheduled,due:scheduled,entry:{meal:{lastCooked:last}}});
 const today='2026-11-24';return {sameDay:stalePrepReminder(mk('defrost','2026-11-24','2026-11-24T12:00:00'),today),later:stalePrepReminder(mk('marinating','2026-11-24','2026-11-25T12:00:00'),today),older:stalePrepReminder(mk('defrost','2026-11-24','2026-11-20T12:00:00'),today),none:stalePrepReminder(mk('defrost','2026-11-24',''),today),manual:stalePrepReminder(mk(undefined,'2026-11-24','2026-11-24T12:00:00'),today),sour:stalePrepReminder(mk('sourdough-feed','2026-11-24','2026-11-24T12:00:00'),today)}}};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    r = p.evaluate('pc.check()')
    assert r == {'sameDay': True, 'later': True, 'older': False, 'none': False, 'manual': True, 'sour': True}, r
    assert not errors, errors
    c.close()
    print('PASS', name, 'automatic prep reminders hide once the meal is marked cooked', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
