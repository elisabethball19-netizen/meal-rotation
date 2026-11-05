"""Offline Serve with matching and existing dependent-slot integration, isolated fixtures."""
import copy,json
from playwright.sync_api import sync_playwright
import dependent_side_groups_browser as d
from scheduled_linked_slots_browser import state,compose,rows
f=d.f
f.EXTRA+='''window.serveTest={
 seed:()=>{depTest.seed(false);for(const m of meals)if(m.id>=100)m.cat='Sides';for(const [id,name]of [[101,'Garlic Mashed Potatoes'],[102,'Creamy Garlic Mash'],[103,'Roasted Baby Potatoes'],[104,'Potato idea'],[201,'Jasmine Rice'],[202,'Rice Pilaf']])meals.find(m=>m.id===id).name=name;for(const [id,words]of [[1,['Potatoes']],[2,['Rice']],[3,['Potatoes','Rice']]])assignSharedRecipeFields(meals.find(m=>m.id===id),{serveWith:words});persist();depTest.pair('Weekend');renderList()},
 prefs:(id,words)=>{assignSharedRecipeFields(meals.find(m=>m.id===id),{serveWith:words});persist();renderList()},
 match:(title,words)=>serveWithMatches(title,words),
 candidates:()=>automaticSlotCandidates(mealPlans.find(p=>p.id===activePlanId),'Saturday','Sides').map(m=>m.id),
 editor:()=>openEditor(1),
 rename:(id,name)=>{meals.find(m=>m.id===id).name=name;persist();renderList()},
 shared:()=>{meals.find(m=>m.id===1).linkGroup='serve-shared';meals.push({...JSON.parse(JSON.stringify(meals.find(m=>m.id===1))),id:500,cat:'Mains',rotation:false});persist();openEditor(1)},
 external:()=>{meals.find(m=>m.id===202).cat='Tubers';meals.find(m=>m.id===202).name='Rice Pilaf'},
 scores:()=>JSON.stringify(mealPlans.map(p=>p.favoriteRotationScores)),
 pool:()=>meals.filter(m=>m.cat==='Sides'&&m.rotation).map(m=>m.id)
};'''
def setup(b,name,w=320):
 c,p,e,pr=f.setup(b,name,w,'multiple');p.evaluate('serveTest.seed()');return c,p,e,pr
def matching(b,name):
 c,p,e,pr=setup(b,name)
 positives=[('Garlic Mashed Potatoes',['Potatoes']),('Creamy Garlic Mash',['Potatoes']),('Spuds',['Potatoes']),('Jasmine Rice',['Rice']),('Pilaf',['Rice']),('Buttered Noodles',['Pasta']),('Pasta Salad',['Noodles']),('Broccoli',['Vegetables']),('Green-bean skillet',['Vegetables']),('Dinner rolls',['Bread']),('Quinoa-lemon salad',['quinoa']),('Couscous bowl',['couscous']),('Roasted tomatoes',['tomato']),('Berries bowl',['berry']),('Black beans',['bean']),('Cauliflower',['rice','Vegetables'])]
 negatives=[('Rice pudding',['Potatoes']),('Breadcrumbs',['Bread']),('Pasta',['past']),('Rice',['ric']),('Carrot cake',['car']),('Penne',['rice']),('Chicken',['salad']),('Butterfly',['butter'])]
 for title,words in positives+negatives:assert p.evaluate('a=>serveTest.match(...a)',[title,words])==((title,words) in positives),(title,words)
 assert p.evaluate('serveTest.candidates()')==[101,102,103];assert d.pick(p)==101
 p.evaluate('depTest.cycle()');assert d.pick(p)==102;p.evaluate('depTest.cycle()');assert d.pick(p)==103
 print('PASS',name,'whole-word offline synonyms, punctuation/plurals, bidirectional/custom/OR matching, excluded Ideas, exact and synonym candidates rotate equally',flush=True);assert not e,e;c.close()
def integration(b,name):
 c,p,e,pr=setup(b,name);before=copy.deepcopy(state(p));checks=f.sources(p);schedule=compose(p);p.evaluate("depTest.manual('Weekend',2)");assert d.pick(p) in [201,202];assert d.pick(p,'Mains')==11;d.unchanged_checks(checks,f.sources(p));assert all(m.get('lastCooked')==next(x for x in before['meals'] if x['id']==m['id']).get('lastCooked') for m in state(p)['meals'])
 p.evaluate("depTest.manual('Sides',101)");assert d.pick(p)==101;p.evaluate("depTest.manual('Mains',12)");assert d.pick(p)==101;p.reload();assert d.pick(p)==101 and p.evaluate('depTest.manualFlag()');p.evaluate('depTest.cycle()');assert d.pick(p) in [201,202] and not p.evaluate('depTest.manualFlag()')
 p.evaluate("serveTest.prefs(1,['quinoa'])");p.evaluate("depTest.manual('Weekend',1)");assert d.pick(p) is None and 'no matching side' in p.locator('#list').inner_text();p.get_by_role('button',name="Choose Saturday's Sides meal",exact=True).tap();p.locator('.weekday-meal-picker').get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('serveTest.prefs(2,[])');p.evaluate("depTest.manual('Weekend',2)");assert d.pick(p) in p.evaluate('serveTest.pool()');p.evaluate("serveTest.prefs(1,['Potatoes'])");p.evaluate('depTest.link(1,[201])');p.evaluate("depTest.manual('Weekend',1)");assert d.pick(p)==201;assert len([r for r in rows(p) if r['day']=='Saturday' and r['planId']=='original' and r['id']==201])==1
 assert p.evaluate('depTest.record(1).preferredSideGroupIds') # obsolete data retained, ignored
 assert not e,e
 print('PASS',name,'manual main coordination, unrelated slots/checks/dates preserved, manual side override/reload/expiration, empty matching pool/manual chooser, unrestricted fallback, incompatible explicit link priority without duplicate',flush=True);c.close()
def rotation_backup(b,name):
 c,p,e,pr=setup(b,name);before=compose(p);backup=p.evaluate('depTest.backup()');records=copy.deepcopy(state(p)['meals']);p.evaluate("depTest.cycle(['Saturday::Weekend'])");assert d.pick(p,'Weekend')==3 and d.pick(p) in [101,102,103,201,202];p.evaluate('slotTest.back()');assert compose(p)==before
 p.evaluate('depTest.sunday()');assert d.pick(p,day='Sunday') in [201,202];p.evaluate('promotionTest.full()');assert d.pick(p) in p.evaluate('serveTest.candidates()') or d.pick(p) is None
 p.evaluate('b=>depTest.restore(b)',backup);p.reload();assert compose(p)==before;assert sorted(state(p)['meals'],key=lambda m:m['id'])==sorted(records,key=lambda m:m['id']);assert not e,e
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,'main cycle and Cycle Back, multi-day/full cycling, complete backup/restore, legacy data retained, namespace isolation',flush=True);c.close()
def ui(b,name,w):
 c,p,e,pr=setup(b,name,w);initial=compose(p);p.evaluate('serveTest.editor()');p.get_by_text('Organization',exact=True).tap();button=p.locator('#serveWith');assert button.inner_text()=='Serve with: Potatoes';assert not p.get_by_role('button',name='Preferred side groups').count();button.tap();dlg=p.get_by_role('dialog',name='Serve with',exact=True);dlg.get_by_role('checkbox',name='Rice',exact=True).check();dlg.get_by_label('Custom Serve with keyword').fill('quinoa');dlg.get_by_role('button',name='Add Serve with keyword',exact=True).tap();p.screenshot(path='/tmp/serve-with-selector-'+name+'-'+str(w)+'.png');dlg.get_by_role('button',name='Cancel Serve with',exact=True).tap();assert button.inner_text()=='Serve with: Potatoes';button.tap();dlg=p.get_by_role('dialog',name='Serve with',exact=True);dlg.get_by_role('checkbox',name='Rice',exact=True).check();dlg.get_by_label('Custom Serve with keyword').fill('quinoa');dlg.get_by_role('button',name='Save Serve with',exact=True).tap();assert 'quinoa' in button.inner_text();assert p.evaluate('depTest.record(1).serveWith')==['Potatoes'];p.screenshot(path='/tmp/serve-with-editor-'+name+'-'+str(w)+'.png');p.locator('#save').tap();assert p.evaluate('depTest.record(1).serveWith')==['Potatoes','Rice','quinoa'];assert compose(p)==initial;p.reload();assert p.evaluate('depTest.record(1).serveWith')==['Potatoes','Rice','quinoa'];p.evaluate('serveTest.editor()');p.get_by_text('Organization',exact=True).tap();p.locator('#serveWith').tap();dlg=p.get_by_role('dialog',name='Serve with',exact=True)
 for label in ['Potatoes','Rice','quinoa']:dlg.get_by_role('checkbox',name=label,exact=True).uncheck()
 dlg.get_by_role('button',name='Save Serve with',exact=True).tap();p.locator('#save').tap();assert p.evaluate('depTest.record(1).serveWith')==[];assert p.evaluate('document.documentElement.scrollWidth<=innerWidth') and not e,e
 print('PASS',name,w,'compact real selector defaults/multiple/custom/removal, selector Cancel, editor Save, no scheduling mutation, reload, old control absent',flush=True);c.close()

def shared_single_and_history(b,name):
 c,p,e,pr=setup(b,name);p.evaluate("serveTest.shared()")
 p.get_by_text('Organization',exact=True).tap();p.locator('#serveWith').tap();dlg=p.get_by_role('dialog',name='Serve with',exact=True);dlg.get_by_role('checkbox',name='Rice',exact=True).check();dlg.get_by_role('button',name='Save Serve with',exact=True).tap();p.locator('#save').tap();assert p.evaluate('depTest.record(500).serveWith')==['Potatoes','Rice'];assert p.evaluate('depTest.record(500).rotation') is False
 p.evaluate('depTest.demote([102,103])');p.evaluate("serveTest.prefs(2,['Potatoes'])");p.evaluate("depTest.manual('Weekend',2)");assert d.pick(p)==101;p.evaluate('depTest.cycle()');assert d.pick(p)==101
 p.evaluate("serveTest.external();depTest.link(1,[202]);serveTest.prefs(1,['Rice']);depTest.manual('Weekend',1)");assert d.pick(p)==202 and len([r for r in rows(p) if r['day']=='Saturday' and r['planId']=='original' and r['id']==202])==1
 order=p.evaluate("depTest.order('Sides')");scores=p.evaluate("serveTest.scores()");p.evaluate("serveTest.prefs(1,['Bread'])");assert p.evaluate("depTest.order('Sides')")==order and p.evaluate("serveTest.scores()")==scores
 p.evaluate("depTest.seed(false);serveTest.prefs(1,[])");assert d.pick(p) is not None;assert not e,e
 print('PASS',name,'shared identity save without membership/status changes, single eligible repeat fallback, external linked side placement once, preference changes preserve queues/credits, independent default',flush=True);c.close()

def run_all():
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   matching(b,name);integration(b,name);rotation_backup(b,name);shared_single_and_history(b,name)
   for w in [320,360]:ui(b,name,w)
  b.close()

if __name__=='__main__':run_all()
