"""Stage 3 correction regressions: synthetic data, real edit/copy/source controls.

MEAL_STAGE3_CORRECTION_SOURCE_ROOT selects an unchanged HTML checkout.
MEAL_STAGE3_EXPECT_FAILURES=1 reproduces the specific independent findings.
"""
import copy,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import phase2_stage3_browser as s3
s2=s3.s2
stage=s3.stage
if os.environ.get('MEAL_STAGE3_CORRECTION_SOURCE_ROOT'):stage.f.ROOT=Path(os.environ['MEAL_STAGE3_CORRECTION_SOURCE_ROOT'])
stage.f.HOOK += '''window.s3Correction={
 prepare:()=>{cats.push('Snacks','Desserts');persist();render()},
 full:id=>openEditor(id),
 sources:(mode='mixed')=>{const first=meals.find(m=>m.id===1),peer=meals.find(m=>m.id===3);for(const record of [first,peer]){for(const key of ['originalRecipeUrl','url','sourceUrl','ingredientImportUrl'])delete record[key];record.linkGroup='source-family';record.importSourceId='stable-import-'+record.id;record.recipeSageId='opaque-legacy-source-'+record.id;record.recipeImportReferences=[{name:'Reference metadata',url:'https://recipes.test/reference'}];if(mode==='mixed'){record.originalRecipeUrl='https://recipes.test/original-'+record.id;record.url='https://recipes.test/saved-'+record.id}if(mode==='mixed'||mode==='source')record.sourceUrl='https://recipes.test/fallback-'+record.id;if(mode==='mixed'||mode==='ingredient')record.ingredientImportUrl='https://recipes.test/ingredients-'+record.id;if(mode==='url')record.url='https://recipes.test/saved-'+record.id}peer.cat='Sauces';persist();render()},
 enrich:id=>{const meal=meals.find(m=>m.id===id),next={...meal};fillMissingRecipeContent(next,{originalRecipeUrl:'https://recipes.test/enriched-source'});assignSharedRecipeFields(meal,sharedRecipeChanges(meal,next));persist();renderRecipeViewer()},
 original:id=>recipeOriginalUrl(meals.find(m=>m.id===id)),
 members:id=>sharedRecipeMembers(meals.find(m=>m.id===id)).map(m=>m.id),
 scores:()=>mealPlans.map(p=>({id:p.id,scores:p.favoriteRotationScores||null}))
};'''

def setup(b,name,width=320):return s3.setup(b,name,width)
def records(p):return copy.deepcopy(stage.state(p)['meals'])
def selection(p):return p.evaluate('stage3Test.rawSelections()')
def contributions(p,id):return p.evaluate('stage3Test.defaultSources',id)
def close_view(p):p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_function('!document.querySelector("#recipeViewer")&&!window.history.state?.mealRotationRecipeViewer')
def save_light(d):d.get_by_role('button',name='Save recipe',exact=True).click()
def add_membership(p,id,cat):
 p.evaluate('s3Correction.full',id);p.locator('#editor [data-editor-section=organization]>summary').click();p.get_by_role('button',name='Add group membership',exact=True).click();p.get_by_role('combobox',name='Additional group',exact=True).last.select_option(cat);p.locator('#save').click();p.wait_for_function('!document.querySelector("#editor .editor")')

def membership(b,name,empty=False,first='copy'):
 c,p,errors,_=setup(b,name);p.evaluate('s3Correction.prepare()');d=s2.create_dialog(p,{'planId':'original','day':'Tuesday','category':'Rice','occasional':False});s2.fill_recipe(d,'Correction membership recipe',rotation=True,groceries=True);d.get_by_role('button',name='Save recipe and schedule',exact=True).click();source=next(m for m in records(p) if m['name']=='Correction membership recipe')['id']
 p.evaluate('stage3Test.chooser',source);chooser=p.locator('[data-recipe-edit-draft]').filter(has=p.get_by_text('Add ingredients to grocery list',exact=True));chooser.get_by_role('checkbox',name='2 cups rice',exact=True).uncheck()
 if empty:chooser.get_by_role('checkbox',name='3 apples',exact=True).uncheck()
 chooser.get_by_role('button',name='Save',exact=True).click();expected=[] if empty else ['3 apples'];assert selection(p)[str(source)]==expected
 p.evaluate('stage3Test.copy');d=p.get_by_role('dialog').filter(has_text='Add existing meals to Rice');d.get_by_role('searchbox',name='Search meals',exact=True).fill('Correction membership recipe');d.locator('input[type=checkbox]:visible').check();d.get_by_role('button',name='Add selected meals',exact=True).click();members=p.evaluate('s3Correction.members',source);copied=next(id for id in members if id!=source);assert str(copied) not in selection(p)
 p.evaluate('weekTest.check()');rows=stage.rows(p);progress=s2.prior.progress(p);scores=p.evaluate('s3Correction.scores()');definitions=records(p);old_selections=selection(p)
 for index,cat in enumerate(['Sides','Snacks','Desserts']):
  actor=(copied if first=='copy' else source) if index==0 else source if index==1 else next(m['id'] for m in records(p) if m['cat']=='Sides' and m['name']=='Correction membership recipe')
  add_membership(p,actor,cat)
  assert [s['original'] for s in contributions(p,source)]==expected,'S3-1 new memberships must inherit effective explicit selections, including empty arrays'
  assert all(selection(p).get(key)==value for key,value in old_selections.items())
  assert [m for m in records(p) if m['id'] in {old['id'] for old in definitions}]==definitions
  assert stage.rows(p)==rows and s2.prior.progress(p)==progress and p.evaluate('s3Correction.scores()')==scores
  added=next(m for m in records(p) if m['cat']==cat and m['name']=='Correction membership recipe');assert selection(p)[str(added['id'])]==expected
  p.reload();assert [s['original'] for s in contributions(p,source)]==expected
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert [s['original'] for s in contributions(p,source)]==expected and s2.prior.progress(p)==progress;assert not errors,errors;c.close();print('PASS',name,'membership',first,'empty',empty,'partial/empty exclusions survive three full-editor additions, different members, reload, backups and shopping state',flush=True)

def source_links(b,name,mode='mixed'):
 c,p,errors,_=setup(b,name,360);p.evaluate('s3Correction.sources',mode);p.reload();before=records(p);rows=stage.rows(p);progress=s2.prior.progress(p);p.evaluate('stage3Test.open()');effective=p.evaluate('s3Correction.original',1);assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')==effective
 d=s3.editor(p);field=d.get_by_role('textbox',name='Recipe source link',exact=True);assert field.input_value()==effective,'S3-2 source field must reflect the effective fallback link'
 d.get_by_role('button',name='Cancel',exact=True).click();assert records(p)==before
 d=s3.editor(p);d.get_by_role('textbox',name='Recipe source link',exact=True).fill('https://recipes.test/replacement?x=1&y=2');save_light(d);assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')=='https://recipes.test/replacement?x=1&y=2'
 after_replace=records(p)
 for id in [1,3]:
  old=next(m for m in before if m['id']==id);new=next(m for m in after_replace if m['id']==id)
  assert {k:v for k,v in new.items() if k not in ['url','originalRecipeUrl','recipeSourceHidden']}=={k:v for k,v in old.items() if k not in ['url','originalRecipeUrl','recipeSourceHidden']}
 d=s3.editor(p);d.get_by_role('textbox',name='Recipe source link',exact=True).fill('');save_light(d);assert not p.get_by_role('link',name='View Original Recipe',exact=True).count(),'S3-2 explicitly clearing must hide every fallback source action'
 after_clear=records(p);assert [{k:v for k,v in m.items() if k!='recipeSourceHidden'} for m in after_clear]==[{k:v for k,v in m.items() if k!='recipeSourceHidden'} for m in after_replace],'Clearing the display link must preserve stored provenance and all recipe content'
 close_view(p)
 for id in [1,3]:
  p.evaluate('stage3Test.open',id);assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();d=s3.editor(p);assert d.get_by_role('textbox',name='Recipe source link',exact=True).input_value()=='';d.get_by_role('button',name='Cancel',exact=True).click();close_view(p)
 p.evaluate('stage3Test.open()');assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();close_view(p);p.reload();p.evaluate('stage3Test.open()');assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();close_view(p)
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();p.evaluate('stage3Test.open()');assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();assert records(p)==after_clear,[(m['id'],{k:(old.get(k),m.get(k)) for k in set(old)|set(m) if old.get(k)!=m.get(k)}) for m,old in zip(records(p),after_clear) if m!=old];assert stage.rows(p)==rows,(rows,stage.rows(p));assert s2.prior.progress(p)==progress,(progress,s2.prior.progress(p))
 # A deliberate subsequent replacement restores the display link.
 d=s3.editor(p);d.get_by_role('textbox',name='Recipe source link',exact=True).fill('https://recipes.test/restored');save_light(d);assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')=='https://recipes.test/restored';assert not errors,errors;c.close();print('PASS',name,'source',mode,'effective initial/replacement/clear, shared members, provenance, reopen/reload/backup and re-enable',flush=True)

def clear_fallback_direct(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('s3Correction.sources','ingredient');p.reload();before=records(p);p.evaluate('stage3Test.open()');d=s3.editor(p);field=d.get_by_role('textbox',name='Recipe source link',exact=True);assert field.input_value()==p.evaluate('s3Correction.original',1);field.fill('');save_light(d);assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();assert [{k:v for k,v in m.items() if k!='recipeSourceHidden'} for m in records(p)]==before;p.evaluate('s3Correction.enrich',1);assert not p.get_by_role('link',name='View Original Recipe',exact=True).count();close_view(p);p.evaluate('s3Correction.full',1);p.locator('#editor [data-editor-section=recipe]>summary').click();p.locator('#url').fill('https://recipes.test/full-editor-source');p.locator('#save').click();p.wait_for_function('!document.querySelector("#editor .editor")');p.evaluate('stage3Test.open()');assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')=='https://recipes.test/full-editor-source';assert not errors,errors;c.close();print('PASS',name,'clearing a fallback-only record preserves every underlying source/import field',flush=True)

def source_failure(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('s3Correction.sources','mixed');p.reload();before=records(p);storage=p.evaluate('weekTest.storage()');p.evaluate('stage3Test.open()');d=s3.editor(p);d.get_by_role('textbox',name='Recipe source link',exact=True).fill('')
 p.evaluate('''()=>{window.s3cSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('synthetic source failure');return s3cSet.call(this,k,v)}}''');save_light(d);expect(d.get_by_role('status')).to_contain_text('draft is still open');assert records(p)==before
 with p.expect_download() as download:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'viewer-recipe-editor' in Path(download.value.path()).read_text()
 d.get_by_role('textbox',name='Recipe source link',exact=True).fill('https://recipes.test/latest-retry');p.evaluate('()=>Storage.prototype.setItem=s3cSet');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.querySelector("[data-viewer-recipe-draft]")');assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')=='https://recipes.test/latest-retry'
 saved=records(p);durable=p.evaluate('weekTest.storage()');d=s3.editor(p);d.get_by_role('textbox',name='Recipe source link',exact=True).fill('');p.evaluate('''()=>{Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('synthetic clear failure');return s3cSet.call(this,k,v)}}''');save_light(d);expect(d.get_by_role('status')).to_contain_text('draft is still open');p.evaluate('()=>Storage.prototype.setItem=s3cSet');d.get_by_role('button',name='Cancel',exact=True).click();assert records(p)==saved and p.evaluate('weekTest.storage()')==durable and not p.locator('#mealSaveWarning').count();assert p.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')=='https://recipes.test/latest-retry';assert not errors,errors;c.close();print('PASS',name,'source clear failure rolls back; latest source retry and failed-clear Cancel preserve provenance and data',flush=True)

def run():
 baseline=os.environ.get('MEAL_STAGE3_EXPECT_FAILURES')=='1'
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   cases=[('S3-1 partial',lambda:membership(b,name)),('S3-1 empty',lambda:membership(b,name,True)),('S3-2 mixed',lambda:source_links(b,name)),('S3-2 fallback',lambda:source_links(b,name,'source'))]
   for label,case in cases:
    if baseline:
     try:case()
     except AssertionError as e:
      expected='S3-1 new memberships must inherit' if label.startswith('S3-1') else 'S3-2 explicitly clearing' if label.endswith('mixed') else 'S3-2 source field must reflect'
      assert expected in str(e),'Unexpected reproduction error: '+str(e)
      print('REPRODUCED',name,label,str(e),flush=True)
     else:raise AssertionError('Expected defect did not reproduce: '+label)
    else:case()
   if not baseline:
    for empty in [False,True]:membership(b,name,empty,first='original')
    for mode in ['ingredient','url']:source_links(b,name,mode)
    clear_fallback_direct(b,name);source_failure(b,name)
  b.close()
if __name__=='__main__':run()
