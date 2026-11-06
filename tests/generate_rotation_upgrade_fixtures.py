"""Regenerate synthetic persisted fixtures using verified historical app source.

Prepare read-only clean checkouts of fd1f014 and ba6f3b7, then run:
  python tests/generate_rotation_upgrade_fixtures.py \
    --pre79-dir /path/to/fd1f014 --pre80-dir /path/to/ba6f3b7

Only the synthetic test browser's storage and tests/fixtures are written.
"""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import skipped_empty_rotation_browser as t

VERSIONS={
 'pre79':('fd1f014b3265f833bf187bca08dc21d70515ac22','cd4395c13861e1722160b0bb2bdbd41d7a3f4fd9'),
 'pre80':('ba6f3b7d802338541ecc640cbfe001599e38a453','b1589edc34052318c7bdafe51f7619f3bb250eac'),
}

def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pre79-dir',type=Path,required=True)
    parser.add_argument('--pre80-dir',type=Path,required=True)
    args=parser.parse_args();folders={'pre79':args.pre79_dir,'pre80':args.pre80_dir}
    for version,folder in folders.items():
        assert blob(folder/'index.html')==VERSIONS[version][1], 'Historical index.html must match '+VERSIONS[version][0]
    t.f.EXTRA+='''window.upgradeCapture={legacyEmpty:()=>{const p=mealPlans[0];delete p.weekSchedule;p.cycleSlotChoices['Sunday::Weekend'].empty=true;saveActiveMealPlan();persist();renderList()}};'''
    output=Path(__file__).resolve().parent/'fixtures/rotation-upgrades';output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        try:
            for version,mode in [('pre79','after-cycle'),('pre80','after-cycle'),('pre80','legacy-empty')]:
                sha,source_blob=VERSIONS[version];t.f.ROOT=folders[version]
                c,p,errors,_=t.f.setup(b,'index.html',360)
                try:
                    p.evaluate('emptySkipTest.seed',{})
                    p.evaluate("promotionTest.manual('Saturday','Weekend',1)")
                    p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.empty','Sunday')
                    if mode=='legacy-empty':p.evaluate('upgradeCapture.legacyEmpty()')
                    else:p.evaluate('emptySkipTest.cycle()')
                    p.reload();storage=p.evaluate('slotTest.storage()');assert not errors,errors
                    value={'fixtureVersion':1,'synthetic':True,'producerCommit':sha,'producerSourceBlob':source_blob,'scenario':version+'-'+mode,
                           'construction':'Seven synthetic Weekend recipes; original Saturday 2/Sunday 3; manually choose Pernil 1, Skip Sunday, Leave Empty Sunday, then '+('rotate and reload with saved history' if mode=='after-cycle' else 'represent the empty slot using cycleSlotChoices.empty instead of weekSchedule, save and reload (constructed legacy representation)'),
                           'roles':{'beefBowls':'2','potRoast':'3','pernil':'1'},'rotateBackOnLoad':mode=='after-cycle','storage':storage}
                    path=output/(version+'-'+mode+'.json');path.write_text(json.dumps(value,indent=2)+'\n')
                    print('WROTE synthetic fixture',path.name,flush=True)
                finally:c.close()
        finally:b.close()

if __name__=='__main__':main()
