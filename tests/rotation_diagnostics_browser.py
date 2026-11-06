"""Offline report reads files without changing storage or disclosing recipe text."""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
fixture=json.loads((ROOT/'tests/fixtures/rotation-upgrades/pre80-after-cycle.json').read_text())


def run(browser,width):
    ctx=browser.new_context(viewport={'width':width,'height':800},has_touch=True,is_mobile=True,accept_downloads=True)
    p=ctx.new_page();requests=[];errors=[];p.on('request',lambda r:requests.append(r.url));p.on('pageerror',lambda e:errors.append(str(e)))
    p.route('http://diagnostic.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=(ROOT/'docs/rotation-diagnostics.html').read_text()))
    p.goto('http://diagnostic.test/')
    before=p.evaluate('JSON.stringify({...localStorage})')
    data=copy.deepcopy(fixture['storage']);core=json.loads(data['mealRotationDataV1'])
    forbidden=['SECRET ingredient','SECRET instruction','SECRET note','https://private.example/SECRET','PHOTO_SECRET','PRIVATE_FILENAME','PRIVATE_UNKNOWN']
    for m in core['meals']:
        m['ingredients']=[forbidden[0]];m['instructions']=forbidden[1];m['notes']=forbidden[2];m['url']=forbidden[3];m['photo']=forbidden[4];m['custom']={'extra':forbidden[6]}
    data['mealRotationDataV1']=json.dumps(core)
    data['UNRELATED_SECRET']=forbidden[6]
    data['mealRotationStartWeekdayV1']='Saturday'
    data['mealRotationManualRecipeOrderingV1']='true'
    data['mealRotationGroupIdentitiesV1']=json.dumps({'Weekend':'opaque-weekend','Mains':'opaque-main'})
    plans=json.loads(data['mealRotationPlansV1'])
    plans['plans'][0]['sideGroupPairs']={'Sunday':{'opaque-main':'opaque-weekend'}}
    plans['plans'][0]['dependentSideState']={'["Sunday","opaque-main"]':{'mainId':'2','mealId':'100','automatic':True}}
    data['mealRotationPlansV1']=json.dumps(plans)
    payload={'version':2,'storage':data,'photos':{'secret':forbidden[4]}}
    p.locator('#backup').set_input_files({'name':'PRIVATE_FILENAME.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
    p.locator('#group').select_option('Weekend')
    for selector,value in [('saturday','2'),('sunday','3'),('replacement','1')]:p.locator('#'+selector).select_option(value)
    p.get_by_role('button',name='Generate anonymized report',exact=True).click()
    raw=p.locator('#report').input_value();assert raw,p.locator('#status').inner_text();report=json.loads(raw)
    for secret in forbidden+[m['name'] for m in core['meals']]+['Weekend','Mains','2020-01-','2026-11-']:
        assert secret not in raw,secret
    assert report['format']=='meal-rotation-anonymous-diagnostics'
    assert report['target']=={'group':'G1','saturdayOriginal':'R2','sundaySkipped':'R3','manualReplacement':'R1'}
    assert report['current']['manualRecipeOrdering'] is True and report['current']['startWeekday']=='Saturday'
    assert len(report['current']['meals'])==len(core['meals'])
    assert report['current']['meals'][1]['lastCookedRank']==1
    assert report['current']['plans'][0]['sideGroupPairs']['Sunday']=={'I1':'I2'}
    assert '["Sunday","I1"]' in report['current']['plans'][0]['dependentSideState']
    previous=report['previousRotations'][0]['plans'][0]
    assert previous['cycleSlotChoices']['Sunday::G1']['deferredMealIds']==['R3']
    assert previous['weekSchedule']['slots']['Sunday::G1']['kind']=='empty'
    assert previous['weekSchedule']['slots']['Sunday::G1']['groceryCheckCount']==3
    assert report['previousRotations'][0]['hasRotationOccurrences']
    with p.expect_download() as download:p.get_by_role('button',name='Download report',exact=True).click()
    assert json.loads(Path(download.value.path()).read_text())==report
    assert p.evaluate('JSON.stringify({...localStorage})')==before
    assert requests==['http://diagnostic.test/'],requests
    assert not errors,errors
    # Malformed input fails closed and clears the previous report.
    p.locator('#backup').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"storage":{}}'})
    assert p.locator('#report').input_value()=='' and p.locator('#download').is_disabled()
    ctx.close();print('PASS',width,'local backup selection/UI/download, private content omitted, aliases/old history preserved, no storage writes or network, malformed input',flush=True)

if __name__=='__main__':
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for width in [360,760]:run(b,width)
        b.close()
