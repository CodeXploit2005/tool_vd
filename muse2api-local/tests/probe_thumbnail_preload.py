"""Check local app preload warnings and on-demand preview fonts; no account writes."""
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession

session = LoginSession(replace(CFG, site_url='about:blank'))
events = []
try:
    p = session.page
    original_recv = p.ws.recv
    def capture(*args, **kwargs):
        message = original_recv(*args, **kwargs)
        parsed = json.loads(message)
        if parsed.get('method') == 'Log.entryAdded':
            events.append(parsed['params']['entry'])
        return message
    p.ws.recv = capture
    p.send('Log.enable')
    p.send('Network.setExtraHTTPHeaders', {'headers':{'Accept-Language':'vi'}})
    if len(sys.argv)>1:
        p.send('Network.setCookie',{'name':'moonreel_niche','value':sys.argv[1],'url':'http://localhost:3000/','path':'/'})
    p.send('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    p.send('Page.navigate',{'url':'http://localhost:3000/'})
    for _ in range(100):
        if p.js("document.readyState === 'complete' && !!document.querySelector('main h1')"):
            break
        time.sleep(.15)
    time.sleep(6)
    p.js('true')
    warnings=[e.get('text','') for e in events if 'preloaded' in e.get('text','').lower()]
    assert not warnings,warnings
    assert not p.js("performance.getEntriesByType('resource').some(e=>/Anton|Oswald|Montserrat/.test(e.name))"), 'Home must not download unopened preview fonts'
    print('PASS: home page has no unused CSS preload warnings or preview-font downloads.')
    p.send('Page.navigate',{'url':'http://localhost:3000/accounts'})
    for _ in range(100):
        if p.js("document.readyState === 'complete' && !![...document.querySelectorAll('button')].find(b=>b.textContent.includes('Kết nối Muse'))"):
            break
        time.sleep(.15)
    time.sleep(6)
    p.js('true')
    warnings=[e.get('text','') for e in events if 'preloaded' in e.get('text','').lower()]
    assert not warnings, warnings
    print('PASS: accounts page has no unused CSS/font preload warnings.')
    p.send('Page.navigate',{'url':'http://localhost:3000/niches'})
    for _ in range(100):
        if p.js("document.readyState === 'complete' && !!document.querySelector('.niche-mobile-create')"):
            break
        time.sleep(.15)
    time.sleep(6)
    preloads=p.js("[...document.querySelectorAll('link[rel=preload]')].map(e=>({as:e.as,href:e.href}))")
    assert not any(re.search('Anton|Oswald|Montserrat', entry['href']) for entry in preloads), preloads
    requests=p.js("performance.getEntriesByType('resource').map(e=>e.name).filter(n=>/Anton|Oswald|Montserrat/.test(n))")
    assert not requests, 'Preview fonts should not be downloaded on unopened niche list'
    warnings=[e.get('text','') for e in events if 'preloaded' in e.get('text','').lower()]
    assert not warnings, warnings
    print('PASS: niche list has no thumbnail font downloads or unused-preload warnings.')
    p.js("document.querySelector('.niche-mobile-create').click()")
    for _ in range(100):
        if p.js("!!document.querySelector('dialog[open] .aspect-video')"):
            break
        time.sleep(.15)
    assert p.js("!!document.querySelector('dialog[open] .aspect-video')"), 'Preview failed to open'
    validation=p.js("""(() => {
      const input=document.querySelector('dialog[open] input[name="slug"]');
      if(!input) return false;
      new RegExp(input.pattern, 'v');
      input.value='meo-cong-nghe-2026';
      const valid=!input.validity.patternMismatch;
      input.value='Has Space';
      const invalid=input.validity.patternMismatch;
      input.value='';
      return valid&&invalid;
    })()""")
    assert validation, 'Slug pattern must accept lowercase/hyphens and reject uppercase/spaces'
    print('PASS: rendered HTML slug pattern is valid under the browser v flag.')
    p.js('document.fonts.ready.then(()=>true)', await_promise=True)
    time.sleep(5)
    fonts=p.js("[...document.fonts].filter(f=>/anton|oswald|montserrat/i.test(f.family)).map(f=>({family:f.family,status:f.status}))")
    assert any(f['status']=='loaded' for f in fonts), fonts
    p.js('true')  # Drain pending browser log events.
    warnings=[e.get('text','') for e in events if 'preloaded' in e.get('text','').lower()]
    assert not warnings, warnings
    print('PASS: mobile editor opens and loads preview fonts on demand; no preload warnings.')
    if len(sys.argv)>2:
        p.send('Page.navigate',{'url':'http://localhost:3000/projects/'+sys.argv[2]})
        for _ in range(100):
            if p.js("document.readyState==='complete'&&!!document.querySelector('main h1')"):
                break
            time.sleep(.15)
        draft=p.js("""(() => {const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Lưu nháp');return b?{icon:!!b.querySelector('svg')}:null;})()""")
        if draft:
            assert not draft['icon'], 'Save draft must remain a text-only button'
        time.sleep(6)
        p.js('true')
        warnings=[e.get('text','') for e in events if 'preloaded' in e.get('text','').lower()]
        assert not warnings,warnings
        assert p.js("document.querySelectorAll('link[rel=preload][as=font]').length") == 0
        print('PASS: real project page has no unused font preloads; nothing saved.')
        if draft: print('PASS: Save draft button is text-only.')
        else: print('NOTE: Save draft is not shown for this completed project; button verified by source/build checks.')
finally:
    session.close()
