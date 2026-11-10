from dataclasses import replace
from pathlib import Path
import sys,time,json,base64
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
 brief='Hãy đóng vai đạo diễn phim hoạt hình kiêm họa sĩ storyboard chuyên nghiệp. Hãy chia phân cảnh chi tiết (shot-by-shot) cho Naruto và Sasuke.\nThời lượng khoảng [3–5 phút], tổng cộng [20–30] shot.\nTỷ lệ khung hình: 16:9\n1. Đối mặt\n2. Khai chiến\n3. Cao trào\n4. Kiệt sức\n5. Kết thúc\nMỗi shot phải có đủ camera, hành động, âm thanh, thoại, prompt tiếng Anh.'
 p.js("document.querySelector('#import-script-source').focus()")
 p.send('Input.insertText',{'text':brief})
 time.sleep(.4)
 for width in (375,1280):
  p.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':width<500})
  time.sleep(.2)
  checks=p.js("""(() => {const panel=document.querySelector('#creation-panel-import'); const count=panel.querySelector('input[type=number]');const ai=[...panel.querySelectorAll('button')].find(b=>b.textContent==='AI phân tích & chia cảnh');ai.scrollIntoView({block:'center'});return {count:count.value,ratio:panel.querySelector('input[name=aspectRatio]:checked').value,scenes:JSON.parse(panel.querySelector('input[name=scenePayload]').value).length,aiEnabled:!ai.disabled,importDisabled:panel.querySelector('button[type=submit]').disabled,overflow:document.documentElement.scrollWidth>innerWidth+1};})()""")
  assert checks=={'count':'','ratio':'16:9','scenes':0,'aiEnabled':True,'importDisabled':True,'overflow':False},checks
  out=Path(__file__).resolve().parents[2]/'ui-checks'/f'storyboard-brief-{width}.jpg'
  out.write_bytes(base64.b64decode(p.send('Page.captureScreenshot',{'format':'jpeg','quality':85})['result']['data']))
  print(width,checks,flush=True)
 # Replace with finished shots; they should bypass AI entirely.
 p.js("document.querySelector('#import-script-source').focus()")
 p.send('Input.dispatchKeyEvent',{'type':'keyDown','key':'a','code':'KeyA','modifiers':2,'windowsVirtualKeyCode':65})
 p.send('Input.dispatchKeyEvent',{'type':'keyUp','key':'a','code':'KeyA','modifiers':2,'windowsVirtualKeyCode':65})
 p.send('Input.insertText',{'text':'Shot 1: Naruto waits.\nShot 2: Sasuke arrives.'})
 time.sleep(.3)
 assert p.js("JSON.parse(document.querySelector('#creation-panel-import input[name=scenePayload]').value).length") == 2
 print('PASS finished shot list imports without expansion; no model call or project created.',flush=True)
finally:s.close()

