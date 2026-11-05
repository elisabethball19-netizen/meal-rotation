"""Explicit side slots, membership-based compatibility and retained legacy data."""
import copy,json
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose,rows
from editor_sections_fixture import open_editor_section as section
f.EXTRA+='''window.sideTest={seed:()=>{cats.push('Cereals','Roots');const main=meals.find(m=>m.id===1);main.name='Curry Chicken';main.labels=['Keep legacy'];for(const n of [1,2,3]){meals.find(m=>m.id===n).preferredSideGroupIds=[groupIdentity(n===1?'Cereals':'Roots',true)]}for(const n of [20,21,22]){const m=meals.find(m=>m.id===n);m.linkGroup='side-'+n;meals.push({...JSON.parse(JSON.stringify(m)),id:n+100,cat:n===21?'Roots':'Cereals',rotation:false})}meals.push({...JSON.parse(JSON.stringify(meals.find(m=>m.id===21))),id:23,linkGroup:'side-23',name:'Second root side'}, {...JSON.parse(JSON.stringify(meals.find(m=>m.id===121))),id:123,linkGroup:'side-23',name:'Second root side'});id=200;const p=mealPlans.find(p=>p.id===activePlanId);weekdayCategories.Saturday=['Weekend','Sides'];weekdayMealOverrides['Saturday::Sides']='20';p.cycleRetainedSlots['Saturday::Sides']='20';p.cycleSlotChoices['Saturday::Sides']={mealId:'20',parentId:''};saveWeekdayCategories();saveWeekdayMealOverrides();setSideGroupPair(p,'Saturday','Sides','Weekend');persist();renderList();slotTest.seed();promotionTest.check()},
 prefs:(id,names)=>{assignSharedRecipeFields(meals.find(m=>m.id===id),{preferredSideGroupIds:names.map(n=>groupIdentity(n,true))});persist();renderList()},
 weighted:()=>{for(const n of [24,25]){const m={...JSON.parse(JSON.stringify(meals.find(m=>m.id===22))),id:n,linkGroup:'side-'+n,name:'Cereal side '+n};meals.push(m,{...JSON.parse(JSON.stringify(m)),id:n+100,cat:'Cereals',rotation:false})}assignSharedRecipeFields(meals.find(m=>m.id===20),{favorite:true});persist()},demoteRoots:()=>{for(const n of [21,23])meals.find(m=>m.id===n).rotation=false;persist()},unrestricted:()=>{const p=mealPlans.find(p=>p.id===activePlanId);return JSON.stringify(getDisplayedWeekdayMealsForPlan(p))===JSON.stringify(getDisplayedWeekdayMealsForPlan({...p,sideGroupPairs:{}}))},clocks:()=>mealPlans.find(p=>p.id===activePlanId).favoriteRotationScores,link:()=>{meals.find(m=>m.id===3).linkedMealIds=[22];persist()},rawPrefs:(id,value)=>{meals.find(m=>m.id===id).preferredSideGroupIds=value;persist()},
 record:id=>meals.find(m=>m.id===id),pair:(side,parent)=>setSideGroupPair(mealPlans.find(p=>p.id===activePlanId),'Saturday',side,parent),
 clearSide:()=>{const p=mealPlans.find(p=>p.id===activePlanId);delete weekdayMealOverrides['Saturday::Sides'];delete p.cycleRetainedSlots['Saturday::Sides'];delete p.cycleSlotChoices['Saturday::Sides'];saveWeekdayMealOverrides()},
 next:()=>slotTest.cycle(['Saturday::Sides']),both:()=>slotTest.cycle(['Saturday::Weekend','Saturday::Sides']),
 manual:id=>applyManualWeekdayMeal('Saturday','Sides',meals.find(m=>m.id===id)),
 groupPicker:()=>openDayCategoryPicker('Saturday'),edit:id=>openEditor(id),renameGroup:name=>renameCategoryDirect(name),rename:()=>renameCategoryDirect('Cereals'),remove:()=>removeMealCategory('Cereals','delete',null),
 backup:()=>slotBackup.capture(),restore:b=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(b.mealRotationDataV1),storage:b}));backupRestoreReloadPending=true},
 ids:()=>readGroupIdentities(),undo:()=>restoreState(JSON.parse(history.pop())),skip:()=>skipScheduledMeal('Saturday','Sides',meals.find(m=>m.id===getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Sides').meal.id))};'''
def setup(b,name,w=320):
 c,p,e,pr=f.setup(b,name,w,'multiple');p.evaluate('sideTest.seed()');return c,p,e,pr
def pick(p,cat='Sides'):return next((r['id'] for r in rows(p) if r['planId']=='original' and r['day']=='Saturday' and r['cat']==cat),None)
def data(p,id):return p.evaluate('id=>sideTest.record(id)',id)
def cycle_checks(b,name):
 c,p,e,pr=setup(b,name);before=copy.deepcopy(state(p));schedule=compose(p);checks=f.sources(p);p.evaluate('sideTest.next()');assert pick(p)==22 and pick(p,'Weekend')==1,rows(p)
 assert all(m.get('lastCooked')==next(x for x in before['meals'] if x['id']==m['id']).get('lastCooked') for m in state(p)['meals']);assert [m['id'] for m in state(p)['meals'] if m['cat']=='Roots']==[m['id'] for m in before['meals'] if m['cat']=='Roots'];p.evaluate('slotTest.back()');assert compose(p)==schedule
 p.evaluate('sideTest.both()');assert pick(p,'Weekend')==3 and pick(p) in [21,23],rows(p);assert all(s['checked']==(checks[id]['checked'] if id in checks else False) for id,s in f.sources(p).items())
 p.evaluate('slotTest.back()');assert compose(p)==schedule;p.evaluate('sideTest.prefs(1,["Cereals","Roots"])');p.evaluate('sideTest.next()');assert pick(p) in [21,22,23]
 p.evaluate('sideTest.prefs(1,[])');p.evaluate('sideTest.clearSide()');assert pick(p) is not None and p.evaluate('sideTest.unrestricted()')
 assert data(p,1)['labels']==['Keep legacy'];p.evaluate('promotionTest.groups()');assert not p.get_by_role('button',name='Manage recipe labels',exact=True).count();p.evaluate('sideTest.edit(1)');section(p,'organization');assert p.locator('#preferredSideGroups').is_visible() and not p.locator('#recipeLabels,#editorAdditionalGroups').count();p.locator('#cancel').tap();assert not e,e
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,'main-first compatible sides, partial retained mains, independent histories, multiple/empty preferences, Cycle Back, unchanged groceries/history/labels and removed controls',flush=True);c.close()
def editor_ui(b,name,w):
 c,p,e,pr=setup(b,name,w);p.evaluate('promotionTest.groups()');p.evaluate('sideTest.edit(1)');p.wait_for_timeout(850);assert p.locator('#categoryRows select').count()==1 and p.get_by_role('button',name='Add group membership',exact=True).count()==1 and not p.get_by_role('button',name='Remove meal from Weekend',exact=True).count();p.get_by_role('button',name='Add group membership',exact=True).tap();assert p.locator('#categoryRows select').count()==2;p.get_by_role('combobox',name='Additional group',exact=True).select_option('Mains');assert p.locator('#cat option[value="Mains"]').is_disabled();section(p,'organization');p.locator('#preferredSideGroups').tap();d=p.get_by_role('dialog',name='Preferred side groups',exact=True);d.get_by_role('checkbox',name='Roots',exact=True).check();d.get_by_role('button',name='Cancel preferred side groups',exact=True).tap();assert 'Roots' not in p.locator('#preferredSideGroups').inner_text();p.locator('#preferredSideGroups').tap();d=p.get_by_role('dialog',name='Preferred side groups',exact=True);d.get_by_role('checkbox',name='Roots',exact=True).check();d.get_by_role('button',name='Save preferred side groups',exact=True).tap();p.screenshot(path='/tmp/preferred-side-editor-'+name+'-'+str(w)+'.png');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.locator('#save').tap();copies=[m for m in state(p)['meals'] if m.get('linkGroup')==data(p,1)['linkGroup']];assert len(copies)==2 and all(len(m['preferredSideGroupIds'])==2 for m in copies);assert data(p,1)['cat']=='Weekend' and data(p,1)['labels']==['Keep legacy']
 backup=p.evaluate('sideTest.backup()');expected=copy.deepcopy(state(p));p.reload();assert state(p)==expected;p.evaluate('sideTest.prefs(1,[])');p.evaluate('b=>sideTest.restore(b)',backup);p.reload();assert state(p)==expected
 p.evaluate('sideTest.groupPicker()');picker=p.get_by_role('dialog',name="Choose Saturday's meal groups",exact=True);picker.get_by_role('button',name='Side for Sides',exact=True).tap();d=p.get_by_role('dialog',name='Side for Sides',exact=True);assert d.get_by_role('radio',name='Weekend',exact=True).is_checked();d.get_by_role('radio',name='None',exact=True).check();d.get_by_role('button',name='Cancel side for sides',exact=True).tap();assert 'Weekend' in picker.get_by_role('button',name='Side for Sides',exact=True).inner_text();p.screenshot(path='/tmp/preferred-side-picker-'+name+'-'+str(w)+'.png');picker.get_by_role('button',name='Close',exact=True).tap();assert not e,e
 print('PASS',name,w,'compact +/X memberships, no duplicates, preferred group selector draft/Cancel/shared Save, pairing selector, reload/backup and separate storage',flush=True);c.close()
def unavailable_and_rename(b,name):
 c,p,e,pr=setup(b,name);identities=p.evaluate('sideTest.ids()');p.evaluate('sideTest.rename()');d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Grains renamed');d.get_by_role('button',name='Save',exact=True).tap();assert p.evaluate('sideTest.ids()')['Grains renamed']==identities['Cereals'];p.evaluate('sideTest.next()');assert pick(p)==22
 p.evaluate('sideTest.rawPrefs(1,["deleted-group-id"])');p.evaluate('sideTest.next()');assert pick(p) is None and 'no compatible recipe in rotation' in p.locator('#list').inner_text();assert pick(p,'Weekend')==1
 p.evaluate('promotionTest.groups()');p.evaluate('sideTest.edit(1)');section(p,'organization');p.locator('#preferredSideGroups').tap();d=p.get_by_role('dialog',name='Preferred side groups',exact=True);assert d.get_by_role('checkbox',name='Unavailable group (remove)',exact=True).is_checked();d.get_by_role('button',name='Cancel preferred side groups',exact=True).tap();p.locator('#cancel').tap();assert not e,e
 print('PASS',name,'renaming preserves stable identity and eligible sides; missing groups safely leave side empty with visible explanation and removable unavailable preference',flush=True);c.close()

def histories_links_manual_and_skip(b,name):
 c,p,e,_=setup(b,name,360);sequence=[]
 for _ in range(2):p.evaluate('sideTest.next()');sequence.append(pick(p))
 assert sequence==[22,20],sequence;p.evaluate('sideTest.prefs(1,["Roots"])');root=[]
 for _ in range(3):p.evaluate('sideTest.next()');root.append(pick(p))
 assert root==[21,23,21],root;p.evaluate('sideTest.prefs(1,["Cereals"])');p.evaluate('sideTest.next()');assert pick(p)==22
 before=copy.deepcopy(state(p));p.evaluate('sideTest.skip()');assert pick(p)==20 and {m['id']:m.get('lastCooked') for m in state(p)['meals']}=={m['id']:m.get('lastCooked') for m in before['meals']};p.evaluate('sideTest.undo()');assert pick(p)==22
 p.evaluate('sideTest.manual(21)');assert pick(p)==21;p.evaluate('sideTest.next()');assert pick(p) in [20,22] and not e,e
 print('PASS',name,'Rice/Roots pool sequences stay independent when switching back; Skip uses compatible alternatives without cooked dates, Undo and deliberate manual incompatible selection remain supported',flush=True);c.close()
 c,p,e,_=setup(b,name,360);p.evaluate('sideTest.link()');p.evaluate('sideTest.both()');assert pick(p,'Weekend')==3 and pick(p)==22;assert sum(r['day']=='Saturday' and r['cat']=='Sides' and r['planId']=='original' for r in rows(p))==1;p.evaluate('slotTest.back()');p.evaluate('sideTest.manual(20)');p.evaluate("slotTest.cycle(['Saturday::Weekend'])");assert pick(p)==20 and not e,e
 print('PASS',name,'specific linked side overrides compatibility without duplicate side slots; explicitly retained manual side survives main-only rotation',flush=True);c.close()
def delete_group_and_legacy_backup(b,name):
 c,p,e,_=setup(b,name,320);old_ids=p.evaluate('sideTest.ids()');p.evaluate('sideTest.remove()');assert 'Cereals' not in p.evaluate('sideTest.ids()');assert data(p,20) and data(p,22) and data(p,1)['preferredSideGroupIds']==[old_ids['Cereals']];p.evaluate('sideTest.next()');assert pick(p) is None and not e,e
 backup=p.evaluate('sideTest.backup()');old=copy.deepcopy(backup);old.pop('mealRotationGroupIdentitiesV1',None);core=json.loads(old['mealRotationDataV1']);[m.pop('preferredSideGroupIds',None) for m in core['meals']];old['mealRotationDataV1']=json.dumps(core);plans=json.loads(old['mealRotationPlansV1']);[plan.pop('sideGroupPairs',None) for plan in plans['plans']];old['mealRotationPlansV1']=json.dumps(plans);p.evaluate('b=>sideTest.restore(b)',old);p.reload();assert data(p,1)['labels']==['Keep legacy'];p.evaluate('sideTest.clearSide()');assert pick(p) is not None and not e,e
 print('PASS',name,'deleting a preferred group keeps surviving memberships and warns instead of choosing an incompatible side; old backups without side fields/registry restore with saved labels intact',flush=True);c.close()


def no_eligible_and_pair_rename(b,name):
 c,p,e,_=setup(b,name,320);p.evaluate('sideTest.prefs(1,["Roots"])');p.evaluate('sideTest.demoteRoots()');p.evaluate('sideTest.next()');assert pick(p) is None and 'no compatible recipe in rotation' in p.locator('#list').inner_text();p.evaluate('slotTest.back()');assert pick(p)==20;assert all(data(p,id)['rotation'] is False for id in [21,23]);assert not e,e;c.close()
 c,p,e,_=setup(b,name,320);p.evaluate("sideTest.renameGroup('Sides')");d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Accompaniments');d.get_by_role('button',name='Save',exact=True).tap();p.evaluate("slotTest.cycle(['Saturday::Accompaniments'])");assert pick(p,'Accompaniments')==22 and not e,e
 print('PASS',name,'valid preferred group with no in-rotation candidates leaves an explained empty side; Cycle Back restores the outgoing side; renaming the actual side-slot group preserves its pairing and eligibility',flush=True);c.close()
def weighted_pools_and_back(b,name):
 from collections import Counter
 c,p,e,_=setup(b,name,360);p.evaluate('sideTest.weighted()');seq=[]
 for _ in range(100):seq.append(pick(p));p.evaluate('sideTest.next()')
 counts=Counter(seq);assert counts=={20:40,22:20,24:20,25:20},counts;assert all(a!=b for a,b in zip(seq,seq[1:]));scores=p.evaluate('sideTest.clocks()');p.evaluate('sideTest.prefs(1,["Roots"])')
 for _ in range(4):p.evaluate('sideTest.next()')
 cereal_key=next(k for k in scores if 'Cereals' not in k and json.loads(k)[0]=='Sides');assert p.evaluate('sideTest.clocks()')[cereal_key]==scores[cereal_key]
 p.evaluate('sideTest.prefs(1,["Cereals","Roots"])');saved=data(p,1)['preferredSideGroupIds'];p.evaluate('slotTest.back()');assert data(p,1)['preferredSideGroupIds']==saved and p.evaluate('sideTest.ids()') and not e,e
 print('PASS',name,'100 compatible weighted cycles give 40 favorite and 20 per regular recipe without immediate repeats; switching pools preserves other pool credits; Cycle Back retains later preference edits and group identities',flush=True);c.close()

def renamed_history_and_pair_safety(b,name):
 c,p,e,_=setup(b,name,320);p.evaluate('sideTest.next()');p.evaluate('sideTest.rename()');d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Renamed grains');d.get_by_role('button',name='Save',exact=True).tap();p.evaluate('slotTest.back()');assert pick(p)==20;p.evaluate('sideTest.next()');assert pick(p)==22
 before=copy.deepcopy(state(p));storage=p.evaluate('sideTest.backup()')
 try:p.evaluate("sideTest.pair('Weekend','Sides')");raise AssertionError('Expected invalid pair rejection')
 except Exception as error:assert 'cannot also' in str(error),str(error)
 assert state(p)==before and p.evaluate('sideTest.backup()')==storage and not e,e
 print('PASS',name,'Cycle Back across a preferred-group rename keeps identities resolvable; cyclic/side-as-main pairing is rejected without changing recipes, schedules or storage',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   cycle_checks(b,name);unavailable_and_rename(b,name);histories_links_manual_and_skip(b,name);delete_group_and_legacy_backup(b,name);weighted_pools_and_back(b,name);no_eligible_and_pair_rename(b,name);renamed_history_and_pair_safety(b,name)
   for w in [320,360]:editor_ui(b,name,w)
  b.close()
