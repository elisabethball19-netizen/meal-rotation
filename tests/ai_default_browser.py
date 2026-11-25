"""Ask AI is off for a brand-new empty install, stays on for an existing collection, and a saved choice is respected.
Run: python3 tests/ai_default_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

KEY = 'mealRotationAiFeaturesV1'


def fresh(browser):
    c = browser.new_context(viewport={'width': 360, 'height': 800}, service_workers='block')
    p = c.new_page(); errors = []
    p.on('pageerror', lambda e: errors.append(str(e)))
    p.goto((ROOT / 'index.html').as_uri()); p.wait_for_timeout(700)
    return c, p, errors


with sync_playwright() as pw:
    b = pw.chromium.launch()
    # 1. empty install -> off, saved, no Ask AI tab
    c, p, errors = fresh(b)
    assert p.evaluate(f"localStorage.getItem('{KEY}')") == 'off', p.evaluate(f"localStorage.getItem('{KEY}')")
    assert p.evaluate('aiFeaturesOn()') is False
    assert not errors, errors
    c.close()
    # 2. existing collection with no saved choice -> on, saved as 'on'
    c, p, errors, prefix = sb.open_page(b, 'index.html')
    p.evaluate(f"localStorage.removeItem('{KEY}')")
    assert p.evaluate('aiFeaturesOn()') is True and p.evaluate(f"localStorage.getItem('{KEY}')") == 'on'
    # 3. saved off is respected; the switch writes explicit values
    p.evaluate(f"localStorage.setItem('{KEY}','off')")
    assert p.evaluate('aiFeaturesOn()') is False
    p.evaluate(f"localStorage.setItem('{KEY}','on')")
    assert p.evaluate('aiFeaturesOn()') is True
    c.close()
    b.close()
print('PASS Ask AI default: empty install off, existing data on, saved choice kept')
