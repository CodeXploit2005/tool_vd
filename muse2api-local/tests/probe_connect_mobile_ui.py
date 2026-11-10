"""App-browser regression: mocked account API, real React inputs at mobile/desktop sizes."""
import base64
from dataclasses import replace
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession

MOCK = r'''
(() => {
 const original = window.fetch;
 const probe = window.__connectProbe = {stage:'idle', inputs:[], deleted:[], failState:false, failDelete:false, gone:false, stateCalls:0};
 const field = {index:0, fingerprint:'fixture-email', type:'text', placeholder:'Mobile number or email', label:'Email', autocomplete:'username'};
 window.fetch = async (url, options={}) => {
  if (!String(url).includes('/api/muse-connect')) return original(url, options);
  if (!options.method || options.method==='GET') {probe.loaded=true; return Response.json({accounts:[
    {id:'fixture1',label:'b44cb5776f95',enabled:true,ok:true},
    {id:'fixture2',label:'2f49193447a7',enabled:true,ok:true},
    {id:'fixture3',label:'Long connection label for a mobile screen',enabled:true,ok:false}
  ]});}
  const b=JSON.parse(options.body);
  if (b.action==='resume') return Response.json({active:probe.stage!=='idle'});
  if (b.action==='delete') {
   if(probe.failDelete) return Response.json({error:'Fixture deletion failed'}, {status:502});
   probe.deleted.push(b.account_id); return Response.json({ok:true,deleted:true});
  }
  if (b.action==='start') {probe.stage='email';probe.gone=false;return Response.json({ok:true});}
  if (b.action==='cancel') return Response.json({ok:true});
  if (b.action==='state') {
   probe.stateCalls++;
   if(probe.gone) return Response.json({error:'Phiên đã hết hạn. Hãy kết nối lại.'},{status:410});
   if (probe.failState) throw new TypeError('Failed to fetch');
   if (probe.stage==='idle') return Response.json({error:'No session'}, {status:410});
   return Response.json({image:'',width:420,height:760,origin:'https://muse.ai',
    fields:probe.stage==='email'?[field]:[],
    otp:probe.stage==='otp'?{index:0,fingerprint:'fixture-otp',length:6}:null,
    can_finish:probe.stage==='ready',expires_in:600});
  }
  if (b.action==='input') {
   probe.inputs.push(b.input);
   if (b.input.kind==='advance') {
    const wasOtp=probe.stage==='otp';
    probe.stage=probe.stage==='email'?'otp':'ready';
    if(wasOtp) return Response.json({error:'Muse chưa cho tiếp tục. Kiểm tra thông tin hoặc mở màn hình Muse để xem yêu cầu.'},{status:409});
   }
   return Response.json({ok:true});
  }
  if (b.action==='complete') {
   if(probe.failComplete) return Response.json({error:'Fixture completion error'},{status:502});
   return Response.json({ok:true,account:{label:'Fixture connection'}});
  }
  return Response.json({ok:true});
 };
})();
'''


def wait(page, expression, message, timeout=15):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if page.js(expression):
            return
        time.sleep(.15)
    raise AssertionError(message)


session = LoginSession(replace(CFG, site_url='about:blank'))
try:
    p = session.page
    p.send('Page.addScriptToEvaluateOnNewDocument', {'source': MOCK})
    p.send('Network.setExtraHTTPHeaders', {'headers': {'Accept-Language': 'vi'}})
    if len(sys.argv) > 1:
        p.send('Network.setCookie', {'name':'moonreel_niche','value':sys.argv[1],'url':'http://localhost:3000/','path':'/'})
    p.send('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    p.send('Page.navigate', {'url':'http://localhost:3000/accounts'})
    wait(p, "!![...document.querySelectorAll('button')].find(b=>b.textContent.includes('Kết nối Muse'))", 'Connect button missing')
    wait(p, "!!window.__connectProbe.loaded", 'Account page did not hydrate')
    for mobile,width in [(False,320),(False,375),(False,390),(True,320),(True,360),(True,375),(True,390),(True,430)]:
        p.send('Emulation.setDeviceMetricsOverride', {'width':width,'height':844,'deviceScaleFactor':1,'mobile':mobile})
        time.sleep(.2)
        dimensions=p.js("""({viewport:innerWidth,root:document.documentElement.scrollWidth,body:document.body.scrollWidth,
          offenders:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&getComputedStyle(e).position!=='absolute';}).slice(0,12).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))})""")
        print(f'PAGE SCROLL mobile={mobile} {width}: {dimensions}')
        page_shots=Path(__file__).resolve().parents[2] / 'ui-checks'
        page_shots.mkdir(exist_ok=True)
        page_shot=p.send('Page.captureScreenshot',{'format':'jpeg','quality':80})['result']['data']
        (page_shots / f'accounts-page-{mobile}-{width}.jpg').write_bytes(base64.b64decode(page_shot))
        assert dimensions['root']<=dimensions['viewport']+1 and dimensions['body']<=dimensions['viewport']+1, dimensions
    p.send('Emulation.setDeviceMetricsOverride', {'width':375,'height':812,'deviceScaleFactor':1,'mobile':True})
    p.send('Emulation.setTouchEmulationEnabled', {'enabled':True,'maxTouchPoints':1})
    p.send('Input.synthesizeScrollGesture', {'x':180,'y':600,'yDistance':-400,'gestureSourceType':'touch','speed':600})
    time.sleep(.3)
    print('TOUCH SCROLL diagnostics:',p.js("""({y:scrollY,viewport:innerHeight,rootHeight:document.documentElement.scrollHeight,bodyHeight:document.body.scrollHeight,rootOverflow:getComputedStyle(document.documentElement).overflow,bodyOverflow:getComputedStyle(document.body).overflow,touchAction:getComputedStyle(document.body).touchAction})"""))
    if not p.js('window.scrollY'):
        p.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':180,'y':600,'id':0}]})
        for y in (560,520,480,440,400,360):
            p.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':180,'y':y,'id':0}]})
            time.sleep(.05)
        p.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
        time.sleep(.2)
        print('Direct touch y:',p.js('window.scrollY'))
    assert p.js('window.scrollY')>0, 'Touch swipe must scroll accounts page'
    nav=p.js("""(() => {const r=document.querySelector('.mobile-bottom-nav').getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:innerHeight};})()""")
    assert nav['top']>0 and nav['bottom']<=nav['height'], nav
    p.js('window.scrollTo(0,0)')
    print('PASS touch swipe scrolls vertically; bottom navigation stays inside viewport.')
    p.js("document.querySelector('button[title=\"Xóa kết nối\"]').click()")
    wait(p,"!!document.querySelector('dialog[open]')",'Delete confirmation missing')
    assert p.js("document.querySelector('dialog').textContent.includes('Các dự án và video đã tạo vẫn được giữ nguyên')"), 'Removal scope must be clear'
    p.js("[...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Hủy').click()")
    wait(p,"!document.querySelector('dialog[open]')",'Cancel did not close delete dialog')
    assert p.js('window.__connectProbe.deleted.length')==0, 'Cancel must never delete'
    p.js("window.__connectProbe.failDelete=true;document.querySelector('button[title=\"Xóa kết nối\"]').click()")
    wait(p,"!!document.querySelector('dialog[open]')",'Delete retry dialog missing')
    p.js("[...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Xóa kết nối').click()")
    wait(p,"!!document.querySelector('dialog [role=alert]')",'Delete error must be visible')
    assert p.js("document.querySelectorAll('button[title=\"Xóa kết nối\"]').length")==3, 'Failed removal must keep account'
    p.js("window.__connectProbe.failDelete=false;[...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Xóa kết nối').click()")
    wait(p,"!document.querySelector('dialog[open]')",'Successful removal did not close dialog')
    assert p.js("document.querySelectorAll('button[title=\"Xóa kết nối\"]').length")==2, 'Removed account should disappear'
    assert p.js('window.__connectProbe.deleted[0]')=='fixture1', 'Wrong account removal requested'
    print('PASS account removal: confirmation, cancel, failed retry, success and list update; mocked API only.')
    for width in (320,1280):
        p.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':844,'deviceScaleFactor':1,'mobile':width<500})
        time.sleep(.2)
        assert p.js("""[...document.querySelectorAll('button[title="Xóa kết nối"]')].every(b=>{
          const r=b.getBoundingClientRect(),c=b.closest('.glass').getBoundingClientRect();
          return r.height>=44&&r.width>=44&&r.right<=c.right-8&&r.left>=c.left+8;
        })"""), 'Delete controls must remain visible and touch-sized on mobile and desktop'
    p.send('Emulation.setDeviceMetricsOverride',{'width':375,'height':812,'deviceScaleFactor':1,'mobile':True})
    p.js("[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Kết nối Muse')).click()")
    wait(p, "!!document.querySelector('dialog[open] form input')", 'Native sign-in form missing')
    p.js('window.__connectProbe.gone=true')
    wait(p,"document.querySelector('dialog')?.textContent.includes('Phiên đã hết hạn')",'Expired sign-in must show reconnect')
    expired_count=p.js('window.__connectProbe.stateCalls')
    time.sleep(4.3)
    assert p.js('window.__connectProbe.stateCalls')==expired_count, 'Expired session must stop polling'
    p.js("[...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Kết nối lại').click()")
    wait(p,"!!document.querySelector('dialog form input')",'Reconnect must open a new sign-in')
    print('PASS: expired session stops polling; reconnect recovers the sign-in form.')
    out = Path(__file__).resolve().parents[2] / 'ui-checks'
    out.mkdir(exist_ok=True)
    for width, height in [(320,740),(360,740),(375,812),(390,844),(430,932)]:
        p.send('Emulation.setDeviceMetricsOverride', {'width':width,'height':height,'deviceScaleFactor':1,'mobile':True})
        time.sleep(.2)
        metrics = p.js("""(() => {const d=document.querySelector('dialog[open]');const r=d.getBoundingClientRect();
          const input=d.querySelector('form input').getBoundingClientRect();const b=d.querySelector('form button[type="submit"]').getBoundingClientRect();
          return {dialogWidth:r.width,inputLeft:input.left-r.left,inputRight:r.right-input.right,buttonRight:r.right-b.right,
          scrollWidth:d.scrollWidth,clientWidth:d.clientWidth};})()""")
        shot=p.send('Page.captureScreenshot',{'format':'jpeg','quality':80})['result']['data']
        (out / f'connect-email-{width}.jpg').write_bytes(base64.b64decode(shot))
        print(f'Email layout {width}: {metrics}')
        assert metrics['inputLeft'] >= 16 and metrics['inputRight'] >= 16 and metrics['buttonRight'] >= 16, metrics
        steps=p.js("""[...document.querySelectorAll('.muse-connect-steps li')].map(li=>{
          const a=li.firstElementChild.getBoundingClientRect(),b=li.lastElementChild.getBoundingClientRect();
          return Math.abs((a.left+a.width/2)-(b.left+b.width/2));})""")
        assert len(steps)==3 and max(steps)<1, 'Step number and label must share a center'
    p.send('Emulation.setPageScaleFactor', {'pageScaleFactor':1.15})
    time.sleep(.3)
    zoom=p.js("""(() => {const r=document.querySelector('dialog[open]').getBoundingClientRect();const v=visualViewport;
      return {right:r.right,visibleRight:v.offsetLeft+v.width,width:r.width,visibleWidth:v.width};})()""")
    assert abs(zoom['width']-zoom['visibleWidth'])<1 and zoom['right']<=zoom['visibleRight']+1, zoom
    print('PASS: step numbers/labels centered; dialog fits visual viewport at 115% zoom.')
    p.send('Emulation.setPageScaleFactor', {'pageScaleFactor':1})
    p.js("document.querySelector('dialog[open] form input').focus()")
    p.send('Input.insertText', {'text':'test@example.invalid'})
    p.js("document.querySelector('dialog[open] form button[type=submit]').click()")
    wait(p, "!!document.querySelector('input[autocomplete=\"one-time-code\"]')", 'OTP step missing')
    out = Path(__file__).resolve().parents[2] / 'ui-checks'
    out.mkdir(exist_ok=True)
    for width, height in [(360,740),(390,844),(1280,900)]:
        p.send('Emulation.setDeviceMetricsOverride', {'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<500})
        time.sleep(.2)
        metrics = p.js("""(() => {const d=document.querySelector('dialog[open]'); const r=d.getBoundingClientRect();
          const input=d.querySelector('input[autocomplete="one-time-code"]').getBoundingClientRect();
          const b=d.querySelector('form button[type="submit"]').getBoundingClientRect();
          const footer=d.querySelector('footer').getBoundingClientRect();
          return {width:r.width, viewport:innerWidth, inputHeight:input.height, inputVisible:input.top>=r.top&&input.bottom<=footer.top,
           submitVisible:b.bottom<=footer.top, horizontalOverflow:d.scrollWidth>d.clientWidth, screenshotVisible:!!d.querySelector('.muse-remote-screen')};})()""")
        assert not metrics['horizontalOverflow'], metrics
        assert metrics['inputHeight'] >= 48 and metrics['inputVisible'] and metrics['submitVisible'], metrics
        assert not metrics['screenshotVisible'], metrics
        shot = p.send('Page.captureScreenshot', {'format':'jpeg','quality':80})['result']['data']
        (out / f'connect-otp-{width}.jpg').write_bytes(base64.b64decode(shot))
        print(f'PASS layout {width}x{height}: input and submit visible; screenshot collapsed.')
    p.js("window.__connectProbe.failState=true")
    wait(p, "document.querySelector('dialog').textContent.includes('Mất kết nối với Studio')", 'Friendly retry state missing')
    assert not p.js("document.querySelector('dialog').textContent.includes('Failed to fetch')")
    p.js("window.__connectProbe.failState=false; [...document.querySelectorAll('dialog button')].find(b=>b.textContent==='Thử lại').click()")
    wait(p, "!document.querySelector('dialog').textContent.includes('Mất kết nối với Studio')", 'Retry did not recover')
    p.js("document.querySelector('input[autocomplete=\"one-time-code\"]').focus()")
    p.send('Input.insertText', {'text':'123456'})
    p.js("document.querySelector('dialog form button[type=submit]').click()")
    wait(p, "document.querySelector('dialog').textContent.includes('Đã đăng nhập Muse')", 'Finish step missing')
    assert not p.js("document.querySelector('dialog').textContent.includes('Muse chưa cho tiếp tục')"), 'Stale step conflict must clear after successful sign-in'
    assert p.js("window.__connectProbe.inputs.some(i=>i.kind==='fill'&&i.value==='123456')"), 'OTP not forwarded'
    assert p.js("window.__connectProbe.inputs.filter(i=>i.kind==='advance').length") == 2
    print('PASS native email -> OTP -> finish; network error and retry. All credentials were synthetic.')
    p.js("window.__connectProbe.failComplete=true;[...document.querySelectorAll('dialog button')].find(b=>b.textContent.includes('Hoàn tất kết nối')).click()")
    wait(p,"document.querySelector('dialog').textContent.includes('Fixture completion error')",'Real completion error must be shown')
    time.sleep(2.3)
    assert p.js("document.querySelector('dialog').textContent.includes('Fixture completion error')"), 'Polling must not clear a real completion error'
    p.js('window.__connectProbe.failComplete=false')
    p.send('Emulation.setDeviceMetricsOverride', {'width':360,'height':640,'deviceScaleFactor':1,'mobile':True})
    p.js("[...document.querySelectorAll('dialog button')].find(b=>b.textContent.includes('Hoàn tất kết nối')).click()")
    wait(p, "!document.querySelector('dialog[open]')", 'Connection dialog did not close')
    assert p.js("getComputedStyle(document.body).overflow") != 'hidden', 'Page scroll remained locked after finish'
    p.send('Input.dispatchMouseEvent',{'type':'mouseWheel','x':180,'y':400,'deltaX':0,'deltaY':450})
    time.sleep(.4)
    assert p.js('window.scrollY') > 0, 'Vertical wheel could not scroll accounts page after dialog close'
    print('PASS vertical scroll restored after finishing connection.')
finally:
    session.close()
