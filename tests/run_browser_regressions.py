"""Run the existing browser suites against modular or embedded apps, without a build.

Usage: python3 tests/run_browser_regressions.py tests/phase1_data_safety_browser.py
Requires the same Python Playwright test dependency as the existing suites.
Only test responses are inlined; application files and real browser storage are untouched.
"""
import re
import runpy
import shutil
import sys
from pathlib import Path
from playwright.sync_api import BrowserType

read_text = Path.read_text
launch = BrowserType.launch


def app_source(path, *args, **kwargs):
    source = read_text(path, *args, **kwargs)
    if path.name == 'index.html':
        def inline(match):
            asset = path.parent / match[1]
            # Older fixtures insert hooks at this shared script boundary.
            text = read_text(asset)
            return '<script>\n' + text + '\n</script>'
        source = re.sub(r'<script src="\./([^"]+\.js)"></script>', inline, source)
        # Old fixtures expect one shared scope and a final hook insertion point.
        source = source.replace('</script><script>\n', '\n')
        source = source.replace('<script>\n/* Shared inline', '<script>\n(()=>{\n/* Shared inline', 1)
        source = source.replace('</script><script src="./pwa.js"',
                                '\nif(mealPersistence.recovery)return;resumeRecipeViewer();})();\n</script><script src="./pwa.js"', 1)
    source = source.replace('const mealBulkStorageBase=mealPersistence.storage;',
                            'const mealBulkStorageBase=mealPersistence.storage;window.mealPersistence=mealPersistence;window.mealBulkStorageBase=mealBulkStorageBase;')
    return source


def portable_launch(self, *args, **kwargs):
    executable = kwargs.get('executable_path')
    if executable and not Path(executable).exists():
        kwargs['executable_path'] = shutil.which('chromium')
    return launch(self, *args, **kwargs)


if __name__ == '__main__':
    Path.read_text = app_source
    BrowserType.launch = portable_launch
    for suite in sys.argv[1:]:
        if suite == '--backup-compatibility':
            from playwright.sync_api import sync_playwright
            import phase1_data_safety_browser as safety
            import recipe_import_audit_browser as audit
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
                for name in ['index.html', 'meal-rotation-test.html']:
                    for check in [safety.recovery, safety.recovery_actions]:
                        check(browser, name)
                    for width in [320, 360]:
                        audit.parse_tests(browser, name, width)
                browser.close()
        else:
            runpy.run_path(suite, run_name='__main__')
