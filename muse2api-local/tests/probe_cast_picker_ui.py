import base64
from dataclasses import replace
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession
s=LoginSession(replace(CFG,site_url='about:blank'))
try:
 p=s.page
 p.send('Network.setExtraHTTPHeaders',{'headers':{'Accept-Language':'vi'}})
 p.send('Network.setCookie',{'name':'moonreel_niche','value':'4ebe2b7b-80f9-4573-8d07-0d7a9ea79328','url':'http://localhost:3000/','path':'/'})
 p.send('Page.navigate',{'url':'http://localhost:3000/projects/new'})
 for _ in range(80):
  if p.js("!!document.querySelector('#creation-tab-import')"):
   p.js("document.querySelector('#creation-tab-import').click()")
   if p.js("document.querySelector('#creation-tab-import').getAttribute('aria-selected')==='true'"):break
  time.sleep(.25)
 for width in (375,1280):
  p.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':width<500})
  p.js("document.querySelector('#creation-panel-import input[name=castIds]').closest('details').open=true")
  time.sleep(.3)
  result=p.js("""(() => {const input=document.querySelector('#creation-panel-import input[name=castIds]'); const b=input.parentElement.querySelector('button'); if(!b)throw Error('No character'); if(b.getAttribute('aria-pressed')!=='true')b.click(); b.scrollIntoView({block:'center'});return b.textContent;})()""")
  time.sleep(.2)
  checks=p.js("""(() => {const input=document.querySelector('#creation-panel-import input[name=castIds]');const b=input.parentElement.querySelector('button'); const avatar=b.firstElementChild.getBoundingClientRect(); const text=b.children[1].getBoundingClientRect();return {selected:!!input.value,avatar:avatar.width,separated:text.left>=avatar.right,overflow:document.documentElement.scrollWidth>innerWidth+1};})()""")
  assert checks['selected'] and checks['avatar']==56 and checks['separated'] and not checks['overflow'],checks
  out=Path(__file__).resolve().parents[2]/'ui-checks'/f'cast-picker-{width}.jpg'
  out.write_bytes(base64.b64decode(p.send('Page.captureScreenshot',{'format':'jpeg','quality':85})['result']['data']))
  print(width,checks,flush=True)
finally:s.close()
