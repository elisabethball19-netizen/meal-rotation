"""#121 focused mobile checks, reusing the existing disposable storage fixture."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as base
OUT=Path('/workspace/work/batch121');OUT.mkdir(parents=True,exist_ok=True)
base.HOOK+='''window.group121={
 seed:()=>{cats.push('Soup','Tacos');for(let n=100;n<112;n++)meals.push({id:n,cat:'Soup',name:n===100?'Soup rotation':n===101?'Shared soup':'Soup idea '+n,rotation:n===100,recipeStatus:n===100?'rotation':'up-next',upNextStar:n===101||n===102,linkGroup:n===101?'soup-shared':n===102?'pin-shared':'',linkedMealIds:n===101?[201]:[],ingredients:['1 cup stock'],instructions:['Simmer.']});meals.push({id:200,cat:'Tacos',name:'Shared soup',rotation:false,recipeStatus:'up-next',upNextStar:true,linkGroup:'soup-shared',linkedMealIds:[201],ingredients:['1 cup stock'],instructions:['Simmer.']},{id:202,cat:'Tacos',name:'Soup idea 102',rotation:false,recipeStatus:'up-next',upNextStar:true,linkGroup:'pin-shared',ingredients:['1 cup stock'],instructions:['Simmer.']},{id:201,cat:'Tacos',name:'Independent taco',rotation:false,ingredients:['corn'],instructions:[]},{id:300,cat:'',name:'Unassigned recipe',rotation:false,ingredients:[],instructions:[]});id=301;saveUpNextOrder();persist();group121.open()},
 open:()=>{batch1.groups();for(const cat of cats)for(const status of ['rotation','up-next'])setMasterRecipeSectionOpen(cat,status,true);renderList({readOnly:true})},
 selected:()=>[...recipeBulkIds],source:()=>recipeBulkSourceGroup,
 data:()=>JSON.parse(JSON.stringify({cats,meals,mealPlans,sessions:cookingSessions,scales:occurrenceScales,groceries:groceryOccurrenceChecks})),
 filter:()=>{recipeBulkFilter={query:'Soup idea',groups:['Soup']};updateRecipeBulkUI()},
 order:()=>masterRecipeOrder('Soup').filter(m=>recipeStatus(m)==='up-next').map(m=>m.id),groups:()=>currentMasterGroupOrder(),
 sentinel:()=>localStorage.getItem('unrelated-sentinel'),validate:()=>recipeBulkBackupAPI.validate(recipeBulkBackupAPI.capture()),
 fail:()=>{const original=Storage.prototype.setItem;let thrown=false;window.restore121=()=>{Storage.prototype.setItem=original};Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationDataV1')&&!thrown){thrown=true;throw Error('simulated storage failure')}return original.call(this,key,value)}}
};'''
def setup(b,name):
 c,p,errors,prefix=base.setup(b,name,320);p.evaluate('group121.seed()');return c,p,errors,prefix

def card(p,cat='Soup'):return p.locator('.master-category-card[data-category="'+cat+'"]')
def row(p,id):return p.locator('.master-category-meal[data-meal-id="'+str(id)+'"]').first
def select(p,id):row(p,id).locator('.recipe-bulk-check input').click()
def pencil(p,cat='Soup'):card(p,cat).get_by_role('button',name='Select recipes in '+(cat or 'Unassigned'),exact=True).tap()
def button(p,name):return p.get_by_role('button',name=name,exact=True)
def done(p):button(p,'Done').tap()
def raw(p):return p.evaluate('group121.data()')
def touch(p,kind,x=0,y=0):
 if not hasattr(p,'group121cdp'):p.group121cdp=p.context.new_cdp_session(p)
 p.group121cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':0}]})

def selection(b,name):
 c,p,e,prefix=setup(b,name);title=card(p).locator('.master-category-title');title.tap();assert title.get_attribute('aria-expanded')=='false';title.tap();pencil(p)
 bar=p.locator('#recipeBulkToolbar');assert bar.is_visible();assert p.evaluate('group121.selected()')==[];assert p.locator('#mealBottomNav').is_hidden();assert [x.inner_text() for x in bar.locator('button').all()]==['Groups','Status','Delete','Done'];assert all(button(p,x).is_disabled() for x in ['Groups','Status','Delete']);assert card(p).get_by_role('button',name='Select all',exact=True).count()==1
 button(p,'Group settings for Soup').tap();d=p.get_by_role('dialog',name='Edit meal group',exact=True);assert d.get_by_role('button',name='Rename group',exact=True).count() and d.get_by_role('button',name='Move group earlier',exact=True).count();d.get_by_role('button',name='Cancel group editing',exact=True).tap();done(p)
 # Real touch long press selects exactly the pressed recipe; entry exception is explicit.
 target=row(p,100).locator('.master-category-meal-name').first;target.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})');p.wait_for_timeout(100);box=target.bounding_box();touch(p,'touchStart',box['x']+15,box['y']+12);p.wait_for_timeout(620);touch(p,'touchEnd');assert p.evaluate('group121.selected()')==['100'];assert card(p).get_by_role('button',name='Select all',exact=True).count()
 for id in range(101,111):select(p,id)
 assert len(p.evaluate('group121.selected()'))==11;assert card(p).get_by_role('button',name='Deselect all',exact=True).count();card(p,'Tacos').locator('.master-category-title').tap();assert row(p,201).locator('.recipe-bulk-check input').is_disabled();card(p).get_by_role('button',name='Deselect all',exact=True).tap();assert p.evaluate('group121.selected()')==[]
 # A manually selected single recipe does not regain the entry exception.
 select(p,105);assert card(p).get_by_role('button',name='Deselect all',exact=True).count();card(p).get_by_role('button',name='Deselect all',exact=True).tap();p.evaluate('group121.filter()');card(p).get_by_role('button',name='Select all',exact=True).tap();assert set(p.evaluate('group121.selected()'))==set(map(str,range(102,112)))
 p.screenshot(path=str(OUT/(name+'-selection.png')));done(p);assert p.locator('#mealBottomNav').is_visible();pencil(p,'Tacos');select(p,201);assert p.evaluate('group121.selected()')==['201'];done(p);assert not e,e;c.close();print('PASS',name,'header/pencil, direct bar, source isolation, exact long-press exception, 11/12 clear, manual-one and filtered selection',flush=True)

def memberships(b,name):
 c,p,e,prefix=setup(b,name);pencil(p);select(p,101);before=raw(p);button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);assert not p.get_by_role('dialog',name='Edit recipes',exact=True).count();d.get_by_role('checkbox',name='Add to groups',exact=True).check();d.get_by_role('checkbox',name='Meals',exact=True).check();d.get_by_role('button',name='New group',exact=True).tap();d.get_by_role('textbox',name='New group',exact=True).fill('Pending group');d.get_by_role('button',name='Create group',exact=True).tap();assert raw(p)==before;d.get_by_role('button',name='Cancel meal groups',exact=True).tap();assert raw(p)==before and p.evaluate('group121.selected()')==['101']
 button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);d.get_by_role('checkbox',name='Add to groups',exact=True).check();d.get_by_role('checkbox',name='Meals',exact=True).check();p.evaluate('group121.fail()');d.get_by_role('button',name='Confirm meal groups',exact=True).tap();assert 'simulated storage failure' in d.inner_text();assert raw(p)==before and p.evaluate('group121.selected()')==['101'];p.evaluate('restore121()');d.get_by_role('button',name='Confirm meal groups',exact=True).tap();after=raw(p);assert {m['cat'] for m in after['meals'] if m.get('linkGroup')=='soup-shared'}=={'Soup','Tacos','Meals'};assert after['mealPlans']==before['mealPlans'];p.locator('#undo').tap();assert raw(p)==before;p.locator('#redo').tap();assert raw(p)==after
 # Remove only the source; preserve the other memberships. No named destination becomes Unassigned.
 pencil(p);select(p,101);button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);d.get_by_role('checkbox',name='Remove from Soup',exact=True).check();d.get_by_role('button',name='Confirm meal groups',exact=True).tap();assert {m['cat'] for m in raw(p)['meals'] if m.get('linkGroup')=='soup-shared'}=={'Tacos','Meals'}
 pencil(p);select(p,105);button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);d.get_by_role('checkbox',name='Remove from Soup',exact=True).check();d.get_by_role('button',name='Confirm meal groups',exact=True).tap();assert next(m for m in raw(p)['meals'] if m['id']==105)['cat']==''
 card(p,'').get_by_role('button',name='Select recipes in Unassigned',exact=True).tap();select(p,300);button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);assert not d.get_by_role('checkbox',name='Remove from Unassigned',exact=True).count();d.get_by_role('button',name='Cancel meal groups',exact=True).tap();done(p)
 p.evaluate('group121.validate()');p.reload();p.wait_for_function('window.group121!==undefined');p.evaluate('group121.open()');assert next(m for m in raw(p)['meals'] if m['id']==105)['cat']=='';assert p.evaluate("localStorage.getItem('unrelated-sentinel')")=='keep'
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not e,e;c.close();print('PASS',name,'direct membership drafts/cancel/copy/remove, unrelated memberships, Unassigned, atomic Undo/Redo and reload',flush=True)

def status_delete(b,name):
 c,p,e,prefix=setup(b,name);pencil(p);select(p,100);select(p,105);before=raw(p);button(p,'Status').tap();d=p.get_by_role('dialog',name='Rotation status',exact=True);assert d.get_by_role('radio',name='Keep existing',exact=True).is_checked();d.get_by_role('radio',name='Ideas',exact=True).check();d.get_by_role('button',name='Cancel rotation status',exact=True).tap();assert raw(p)==before
 button(p,'Status').tap();d=p.get_by_role('dialog',name='Rotation status',exact=True);d.get_by_role('button',name='Confirm rotation status',exact=True).tap();assert raw(p)==before;button(p,'Status').tap();d=p.get_by_role('dialog',name='Rotation status',exact=True);d.get_by_role('radio',name='Ideas',exact=True).check();d.get_by_role('button',name='Confirm rotation status',exact=True).tap();assert all(not m['rotation'] for m in raw(p)['meals'] if m['id'] in [100,105]);p.locator('#undo').tap();assert raw(p)==before
 pencil(p);select(p,101);button(p,'Delete').tap();d=p.get_by_role('dialog',name='Delete these recipes?',exact=True);assert 'Shared soup' in d.inner_text() and 'Unselected linked recipes will not be deleted.' in d.inner_text();d.get_by_role('button',name='Cancel deletion',exact=True).tap();assert raw(p)==before;button(p,'Delete').tap();p.get_by_role('dialog',name='Delete these recipes?',exact=True).get_by_role('button',name='Confirm deletion',exact=True).tap();assert any(m['id']==201 for m in raw(p)['meals']) and not any(m['id']==101 for m in raw(p)['meals']);p.locator('#undo').tap();assert raw(p)==before
 assert not e,e;c.close();print('PASS',name,'direct status mixed Keep/cancel/apply, delete names/cancel/linked protection and Undo',flush=True)

def drag_handle(p,handle,dy,cancel=False):
 handle.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})');p.wait_for_timeout(80);box=handle.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2;touch(p,'touchStart',x,y)
 for n in range(1,9):touch(p,'touchMove',x,y+dy*n/8);p.wait_for_timeout(35)
 p.wait_for_timeout(100);touch(p,'touchCancel' if cancel else 'touchEnd');p.wait_for_timeout(100)

def ordering(b,name):
 c,p,e,prefix=setup(b,name);before=raw(p);assert not p.locator('.organize-drag-handle').count();pencil(p);select(p,105)
 assert not row(p,100).locator('.organize-drag-handle').count();assert row(p,103).locator('.organize-drag-handle').count()==1;assert not card(p,'Tacos').locator('.master-category-meal .organize-drag-handle').count()
 # A visible handle immediately claims a drag; normal recipe taps still select.
 initial=p.evaluate('group121.order()');drag_handle(p,row(p,103).locator('.organize-drag-handle'),100,True);assert p.evaluate('group121.order()')==initial and p.evaluate('group121.selected()')==['105']
 drag_handle(p,row(p,103).locator('.organize-drag-handle'),100);moved=p.evaluate('group121.order()');assert moved.index(103)>initial.index(103);assert moved[:2]==initial[:2];assert p.evaluate('group121.selected()')==['105'];assert raw(p)['mealPlans']==before['mealPlans']
 p.locator('#undo').tap();assert p.evaluate('group121.order()')==initial;p.locator('#redo').tap();assert p.evaluate('group121.order()')==moved
 # Keyboard alternative uses the same ordering and keeps pinned portions separate.
 handle=row(p,102).locator('.organize-drag-handle');handle.focus();handle.press('Alt+ArrowUp');assert p.evaluate('group121.order()')[:2]==[102,101]
 shared=p.evaluate('batch1.list("Tacos")');assert shared.index(202)<shared.index(200)
 old=p.evaluate('group121.groups()');button(p,'Reorder group Soup').focus();button(p,'Reorder group Soup').press('Alt+ArrowDown');assert p.evaluate('group121.groups()').index('Soup')==old.index('Soup')+1
 groups=p.evaluate('group121.groups()');drag_handle(p,button(p,'Reorder group Soup'),-120,True);assert p.evaluate('group121.groups()')==groups;assert p.evaluate('group121.selected()')==['105']
 drag_handle(p,button(p,'Reorder group Soup'),-150);changed=p.evaluate('group121.groups()');assert changed!=groups;p.locator('#undo').tap();assert p.evaluate('group121.groups()')==groups;p.locator('#redo').tap();assert p.evaluate('group121.groups()')==changed;groups=changed
 # Narrow/landscape bar and list stay in bounds with large recipe names.
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);card(p).locator('.master-category-header').evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})');p.screenshot(path=str(OUT/(name+'-editing-'+str(size['width'])+'.png')))
  assert p.locator('#recipeBulkToolbar').evaluate('(e)=>{const b=e.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.bottom<=innerHeight}')
  assert all(x['w']>=44 and x['h']>=44 for x in p.locator('#recipeBulkToolbar button').evaluate_all('(xs)=>xs.map(x=>({w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))'))
 expected=p.evaluate('group121.order()');done(p);assert not p.locator('.organize-drag-handle').count();p.evaluate('group121.validate()');p.reload();p.wait_for_function('window.group121!==undefined');p.evaluate('group121.open()');assert p.evaluate('group121.order()')==expected and p.evaluate('group121.groups()')==groups
 assert not e,e;c.close();print('PASS',name,'Ideas touch handles/cancel/Undo/Redo, pin boundaries, group ordering, selected identity, reload and 320px/landscape layout',flush=True)

def settings_and_new_group(b,name):
 c,p,e,prefix=setup(b,name);pencil(p);select(p,105);button(p,'Group settings for Soup').tap();p.get_by_role('dialog',name='Edit meal group',exact=True).get_by_role('button',name='Rename group',exact=True).tap();d=p.get_by_role('dialog').last;d.get_by_role('textbox').fill('Soup renamed');d.get_by_role('button',name='Save',exact=True).tap();p.wait_for_function("group121.source()==='Soup renamed'");assert p.evaluate('group121.selected()')==['105'];assert card(p,'Soup renamed').get_by_role('button',name='Deselect all',exact=True).count();done(p)
 pencil(p,'');select(p,300);before=raw(p);button(p,'Groups').tap();d=p.get_by_role('dialog',name='Meal groups',exact=True);d.get_by_role('checkbox',name='Add to groups',exact=True).check();d.get_by_role('button',name='New group',exact=True).tap();d.get_by_role('textbox',name='New group',exact=True).fill('New home');d.get_by_role('button',name='Create group',exact=True).tap();assert raw(p)==before
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);p.screenshot(path=str(OUT/(name+'-groups-'+str(size['width'])+'.png')));assert d.get_by_role('button',name='Confirm meal groups',exact=True).is_visible();assert p.locator('#recipeBulkToolbar').is_hidden()
 d.get_by_role('button',name='Confirm meal groups',exact=True).tap();after=raw(p);assert 'New home' in after['cats'];assert next(m for m in after['meals'] if m['id']==300)['cat']=='New home';p.locator('#undo').tap();assert raw(p)==before;p.locator('#redo').tap();assert raw(p)==after
 pencil(p,'New home');select(p,300);button(p,'Group settings for New home').tap();p.get_by_role('dialog',name='Edit meal group',exact=True).get_by_role('button',name='Delete group',exact=True).tap();button(p,'Delete group and its recipes').tap();assert not p.locator('#recipeBulkToolbar,.organize-drag-handle,.recipe-bulk-check').count();assert not any(m['id']==300 for m in raw(p)['meals']);p.locator('#undo').tap();assert raw(p)==after
 assert not e,e;c.close();print('PASS',name,'settings rename retains source/selection, new groups pending final check, portrait/landscape picker and Undo/Redo',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   selection(b,name);memberships(b,name);status_delete(b,name);ordering(b,name);settings_and_new_group(b,name)
