"""Syntax, shared app parity, and unchanged test shell outside approved photo reset."""
from pathlib import Path
from html.parser import HTMLParser
import re,subprocess,hashlib,tempfile
class Scripts(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script':self.active=not dict(attrs).get('src');self.scripts.append('')
 def handle_data(self,text):
  if self.active:self.scripts[-1]+=text
 def handle_endtag(self,tag):
  if tag=='script':self.active=False
for name in ['index.html','meal-rotation-test.html']:
 p=Scripts();p.feed(Path(name).read_text())
 for script in p.scripts:
  if script.strip():
   with tempfile.NamedTemporaryFile('w',suffix='.js') as f:f.write(script);f.flush();subprocess.run(['node','--check',f.name],check=True,capture_output=True)
 print('PASS inline syntax',name)
subprocess.run(['node','--check','service-worker.js'],check=True)
s=Path('index.html').read_text();t=Path('meal-rotation-test.html').read_text();m='/* Shared inline in both apps:'
a=s[s.index(m):s.index('</script><script>',s.index(m))];b=t[t.index(m):t.index('</script><script>',t.index(m))];assert a.replace('()=>window.localStorage','()=>testStorage').replace('const localStorage=bulkRecipeStorageBridge','const testStorage=bulkRecipeStorageBridge').replace('localStorage.','testStorage.')==b
print('PASS shared JavaScript parity')
css=lambda x:re.search(r'<style>([\s\S]*?)</style>',x)[1]
banner=next(line for line in css(t).splitlines() if line.startswith('#test-banner'));assert css(t).replace(banner,'')==css(s)
print('PASS shared CSS parity with test banner')
prefix=re.sub(r'<style>[\s\S]*?</style>','<shared-style/>',t[:t.index(m)],count=1)
prefix=prefix.replace("addEventListener('click',async()=>{\n if(!confirm('Reset the TEST","addEventListener('click',()=>{\n if(!confirm('Reset the TEST",1)
prefix=prefix.replace(" try{await window.mealRotationClearTestPhotos?.()}catch(e){try{sessionStorage.setItem('mealRotationTestPhotoNotice','Test recipes were reset, but test photo storage could not be cleared.')}catch(e){}}\n",'',1)
assert hashlib.sha256(prefix.encode()).hexdigest()=='e9473080a1453a9f4e4212f239b4e0f56074658191f423c58dc54af044edf1a8'
assert hashlib.sha256(t[t.index('</script><script>',t.index(m)):].encode()).hexdigest()=='9d51f42dee4848c8b7c312dcbba8e102f09cb2bec6aca660c45f59ceddf1c204'
print('PASS preserved storage adapter, banner, shell and suffix; only approved asynchronous photo reset differs')
subprocess.run(['git','diff','--check'],check=True)
