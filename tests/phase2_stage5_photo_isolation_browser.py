"""Same-origin production/test image isolation, reset, selection UI and image handling."""
import json,sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import phase2_stage5_photo_safety_browser as f
p5=f.f

def isolation(b):
 c,p,e,_=p5.setup(b,'index.html');p5.open_view(p);p5.upload(p);one=p5.refs(p)[1];native=p5.safety.native(p);before=p5.state(p);prefix='mealRotationTestSandboxV1:';p.evaluate('prefix=>{for(const [k,v]of Object.entries(localStorage))if(k.startsWith("mealRotation")&&!k.startsWith(prefix))localStorage.setItem(prefix+k,v)}',prefix)
 q=c.new_page();source=(p5.ROOT/'meal-rotation-test.html').read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+p5.t.stage.f.HOOK.replace('localStorage','testStorage')+'})();');q.route('http://slots.test/**',lambda r:r.fulfill(content_type='text/html',body=source) if r.request.url.endswith('meal-rotation-test.html') else r.fulfill(body=''));q.goto('http://slots.test/meal-rotation-test.html');assert q.evaluate('photoTest.db()')!=p.evaluate('photoTest.db()');assert p5.refs(q)[1]==one;assert q.evaluate('photoTest.image',one) is None;p5.open_view(q);assert q.locator('.recipe-photo-placeholder').is_visible();p5.upload(q,p5.B);two=p5.refs(q)[1];assert two!=one;assert p.evaluate('photoTest.image',two) is None;assert q.evaluate('photoTest.image',one) is None;assert p5.safety.native(p)==native and p5.state(p)==before
 p5.close_view(q);q.set_default_timeout(8000);q.on('dialog',lambda d:d.accept());q.locator('#test-reset').click();q.wait_for_load_state('load');q.wait_for_function('window.photoTest && !photoTest.refs().some(r=>r.ref)');assert q.evaluate('photoTest.image',two) is None;assert p.evaluate('photoTest.image',one);assert p5.safety.native(p)==native and p5.state(p)==before;assert not e,e;c.close();print('PASS same-origin production/test DB and reference isolation, actual test reset clears test images only',flush=True)
def images(b,name):
 c,p,e,_=p5.setup(b,name,280);p5.open_view(p);before=p5.state(p)
 bad=[{'name':'vector.svg','mimeType':'image/svg+xml','buffer':b'<svg/>'},{'name':'bad.png','mimeType':'image/png','buffer':b'not an image'},{'name':'large.png','mimeType':'image/png','buffer':b'x'*(20*1024*1024+1)}]
 for file in bad:
  d=p5.photo_dialog(p);d.locator('input[type=file]').set_input_files(file);p.wait_for_function('document.querySelector("[data-photo-editor] [role=status]")?.textContent.includes("not changed")');assert p5.state(p)==before;f.cancel_dialog(p)
 for format in ['JPEG','WEBP','GIF']:
  file=Path('/tmp/photo-format.'+format.lower());Image.new('RGB',(1600,900),(90,100,10)).save(file,format=format);p5.upload(p,file);ref=p5.refs(p)[1];assert p.evaluate('photoTest.image',ref)['type']=='image/jpeg';f.assert_clean(p,before)
 # Large noisy input exercises compression rather than merely resizing a solid color.
 file=Path('/tmp/photo-noise.png');Image.effect_noise((1500,1500),100).convert('RGB').save(file);p5.upload(p,file);ref=p5.refs(p)[1];assert p.evaluate('photoTest.image',ref)['size']<=256*1024
 d=p5.photo_dialog(p);p.set_viewport_size({'width':280,'height':360});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');cancel=d.get_by_role('button',name='Cancel photo change',exact=True);cancel.scroll_into_view_if_needed();assert cancel.is_visible();assert d.locator('input').evaluate('(e)=>e.getBoundingClientRect().width<=e.parentElement.clientWidth');cancel.focus();p.keyboard.press('Tab');assert d.locator('input').evaluate('(e)=>e===document.activeElement');p.keyboard.press('Escape');assert not d.count();p.set_viewport_size({'width':280,'height':800});p5.close_view(p);p.evaluate('weekTest.my()');p.wait_for_function('photoSafety.urls()===0');assert not e,e;c.close();print('PASS',name,'JPEG/WebP/GIF/PNG, corrupt/unsupported/oversize inputs, noisy compression, narrow landscape controls, keyboard trap, object URL cleanup',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  isolation(b)
  for name in ['index.html','meal-rotation-test.html']:images(b,name)
  b.close()
