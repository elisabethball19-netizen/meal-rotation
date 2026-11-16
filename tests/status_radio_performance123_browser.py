"""457-record status click-work profile; optional checkout root permits baseline comparison."""
import sys,json
from pathlib import Path
import batch1_ideas_browser as f
from playwright.sync_api import sync_playwright
f.ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1];f.HOOK+='''window.profile123={seed:()=>{for(let n=100;n<547;n++)meals.push({id:n,name:'Recipe '+n,cat:'Meals',rotation:false,ingredients:['1 cup rice'],instructions:[{type:'step',text:'Cook rice.'}]});persist();batch1.groups();batch1.editor(1)},measure:()=>{const root=document.querySelector('#editor .editor'),radio=document.querySelector('#recipeStatus input[value="up-next"]');let events=0,refreshScans=0;const listener=()=>events++;root.addEventListener('change',listener);const filter=Array.prototype.filter;Array.prototype.filter=function(...args){if(this===meals)refreshScans++;return filter.apply(this,args)};const timings=[];for(let i=0;i<40;i++){const t=performance.now();document.querySelector('#recipeStatus input[value="'+(i%2?'rotation':'up-next')+'"]').click();timings.push(performance.now()-t)}Array.prototype.filter=filter;root.removeEventListener('change',listener);return {recipes:meals.length,changes:events,libraryScans:refreshScans,median:timings.sort((a,b)=>a-b)[20],max:Math.max(...timings)}}};'''
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c,p,e,pre=f.setup(b,'index.html');p.evaluate('profile123.seed()');print(json.dumps(p.evaluate('profile123.measure()')));b.close()
