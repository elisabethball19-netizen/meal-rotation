"""No-build syntax, changed-module mirror parity, JSON chooser and journal-writer audit."""
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
embedded = (ROOT / 'meal-rotation-test.html').read_text()
for name in ['state.js', 'import-export.js', 'ui.js']:
    subprocess.run(['node', '--check', str(ROOT / name)], check=True)

# Compare the behavior changed here, allowing the embedded app's storage adapter and scope.
state = (ROOT / 'state.js').read_text()
imports = (ROOT / 'import-export.js').read_text()
ui = (ROOT / 'ui.js').read_text()
def adapt(s):
    return s.replace('localStorage.', 'testStorage.')
for module, start, end in [
    (state, 'function createMealPersistence(', '\nconst mealPersistence='),
    (state, 'function normalizeImportedBackup(', '\nfunction restoreBackupStorage('),
    (imports, 'function recipeImportItems(', '\nfunction recipeImportMinutes('),
    (ui, "let restoreBtn=document.createElement('button')", "\nlet closeSettings="),
]:
    block = module[module.index(start):module.index(end, module.index(start))]
    assert adapt(block) in embedded, start
assert len(re.findall(r'base\.setItem\(JOURNAL_KEY,', state)) == 2
writer = state[state.index('function saveJournal('):state.index('function matchesRecords(')]
assert writer.count('base.setItem(JOURNAL_KEY,') == 2
for name in ['index.html', 'state.js', 'import-export.js', 'ui.js',
             'meal-rotation-test.html', 'docs/rotation-diagnostics.html']:
    for value in re.findall(r'accept\s*=\s*[\'"]([^\'"]+)', (ROOT / name).read_text()):
        if 'json' in value:
            assert '*/*' in value, (name, value)

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__();self.active=False;self.scripts=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = not dict(attrs).get('src')
            if self.active:self.scripts.append('')
    def handle_data(self, data):
        if self.active:self.scripts[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':self.active=False

for name in ['index.html', 'meal-rotation-test.html', 'docs/rotation-diagnostics.html']:
    parser = Scripts();parser.feed((ROOT / name).read_text())
    for script in parser.scripts:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js') as f:
            f.write(script);f.flush()
            subprocess.run(['node', '--check', f.name], check=True)
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
print('PASS modular/embedded syntax, changed behavior parity, all JSON accepts, centralized journal writers, whitespace')
