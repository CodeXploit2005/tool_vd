"""Import 10 synthetic scenes via real UI; verify DB/no jobs, then remove only this probe draft."""
import base64
from dataclasses import replace
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession

root = Path(__file__).resolve().parents[2]
studio = root / 'moonreel' / 'moonreel-studio'
title = 'codex-import-probe-' + uuid.uuid4().hex
project_id = None
session = LoginSession(replace(CFG,site_url='about:blank'))

def wait(expression,message,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if session.page.js(expression):return
        time.sleep(.15)
    errors=session.page.js("[...document.querySelectorAll('[role=alert]')].map(e=>e.textContent)")
    raise AssertionError(message+': '+json.dumps(errors,ensure_ascii=False))

def db_check(mode):
    result=subprocess.run(['node','--env-file=.env','scripts/verify-script-import.mjs',mode,project_id,title],cwd=studio,text=True,capture_output=True)
    if result.returncode:raise AssertionError(result.stderr)
    print(result.stdout.strip(),flush=True)

try:
    p=session.page
    p.send('Network.setExtraHTTPHeaders',{'headers':{'Accept-Language':'vi'}})
    p.send('Network.setCookie',{'name':'moonreel_niche','value':sys.argv[1],'url':'http://localhost:3000/','path':'/'})
    p.send('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    p.send('Page.navigate',{'url':'http://localhost:3000/projects/new'})
    wait("!!document.querySelector('#creation-tab-import')",'Import tab missing')
    for _ in range(20):
        p.js("document.querySelector('#creation-tab-import').click()")
        if p.js("document.querySelector('#creation-tab-import').getAttribute('aria-selected')==='true'"):break
        time.sleep(.3)
    wait("!document.querySelector('#creation-panel-import').hidden",'Import panel missing')
    assert p.js("document.querySelector('#creation-panel-idea').hidden"),'Idea form must be hidden in import mode'
    raw='Tiêu đề: '+title+'\n\n'+'\n\n'.join(f'Cảnh {i}:\nPrompt: Exact imported scene {i}. Keep this prompt!' for i in range(1,11))
    p.js("document.querySelector('#import-script-source').focus()")
    p.send('Input.insertText',{'text':raw})
    wait("JSON.parse(document.querySelector('input[name=scenePayload]').value).length===10",'Expected ten scenes')
    assert p.js("!document.querySelector('#creation-panel-import input[name=sceneCount]')"),'Scene count must be inferred'
    assert p.js("document.querySelector('#creation-panel-import input[name=castIds]').value")==''
    assert p.js("document.querySelector('#creation-panel-import button[type=submit]').disabled"),'Review confirmation required'
    out=root/'ui-checks'
    out.mkdir(exist_ok=True)
    for width in (375,1280):
        p.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':width<500})
        time.sleep(.2)
        assert p.js('document.documentElement.scrollWidth<=innerWidth+1'),'Import form overflows screen'
        bounds=p.js("""(() => {const a=document.querySelector('#import-script-source').getBoundingClientRect();return {left:a.left,right:a.right,viewport:innerWidth};})()""")
        assert bounds['left']>=12 and bounds['right']<=bounds['viewport']-12,bounds
        image=p.send('Page.captureScreenshot',{'format':'jpeg','quality':80})['result']['data']
        (out/f'script-import-{width}.jpg').write_bytes(base64.b64decode(image))
    p.js("document.querySelector('#creation-panel-import input[name=reviewed]').click()")
    wait("!document.querySelector('#creation-panel-import button[type=submit]').disabled",'Reviewed import should be enabled')
    p.js("document.querySelector('#creation-panel-import button[type=submit]').click()")
    wait("/^\\/projects\\/[a-f0-9-]{36}$/.test(location.pathname)",'Imported project did not open')
    project_id=p.js("location.pathname.split('/').pop()")
    assert re.fullmatch('[a-f0-9-]{36}',project_id)
    wait("!!document.querySelector('.script-toolbar-actions')",'Scene review editor missing')
    assert p.js("document.querySelectorAll('.script-toolbar-actions button').length")==2,'Imported scripts must not offer automatic script regeneration'
    db_check('verify')
    print('PASS: mobile/desktop import UI, explicit review, ten-scene editor and no automatic generation.',flush=True)
finally:
    session.close()
    if project_id: db_check('cleanup')
