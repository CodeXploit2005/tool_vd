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
image_keys = []
session = LoginSession(replace(CFG,site_url='about:blank'))

def wait(expression,message,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if session.page.js(expression):return
        time.sleep(.15)
    errors=session.page.js("[...document.querySelectorAll('[role=alert]')].map(e=>e.textContent)")
    raise AssertionError(message+': '+json.dumps(errors,ensure_ascii=False))

def db_check(mode):
    result=subprocess.run(['node','--env-file=.env','scripts/verify-script-import.mjs',mode,project_id,title] + ([json.dumps(image_keys)] if mode=='verify-products' else []),cwd=studio,text=True,capture_output=True)
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
    document=p.send('DOM.getDocument',{})['result']['root']['nodeId']
    picker=p.send('DOM.querySelector',{'nodeId':document,'selector':'#creation-panel-import input[type=file]'})['result']['nodeId']
    fixture=str(root/'ui-checks'/'product-probe.jpg')
    def keys():
        return json.loads(p.js("document.querySelector('#creation-panel-import input[name=productImagePaths]').value"))
    p.send('DOM.setFileInputFiles',{'nodeId':picker,'files':[fixture,fixture]})
    wait("JSON.parse(document.querySelector('#creation-panel-import input[name=productImagePaths]').value).length===2",'Two images did not upload')
    wait("!document.querySelector('#creation-panel-import input[type=file]').disabled",'Upload stayed busy')
    image_keys=keys()
    assert len(set(image_keys))==2
    for tab in ('idea','import'):
        p.js("document.querySelector('#creation-tab-"+tab+"').click()")
        time.sleep(.2)
        assert json.loads(p.js("document.querySelector('#creation-panel-"+tab+" input[name=productImagePaths]').value"))==image_keys,'Images lost when switching modes'
        for width in (375,1280):
            p.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':width<500})
            p.js("document.querySelector('#creation-panel-"+tab+" [data-product-attachments]').scrollIntoView({block:'center'})")
            time.sleep(.2)
            assert p.js('document.documentElement.scrollWidth<=innerWidth+1'),'Attachments overflow'
            layout=p.js("""(() => {const a=document.querySelector('#creation-panel-"""+tab+""" [data-product-attachments]'); const composer=a.parentElement.getBoundingClientRect();const button=a.querySelector('button[title^=\"Đính kèm\"]').getBoundingClientRect();return {inside:button.left>=composer.left&&button.right<=composer.right&&button.bottom<=composer.bottom,thumbs:a.querySelectorAll('img').length,multiple:a.querySelector('input[type=file]').multiple};})()""")
            assert layout=={'inside':True,'thumbs':2,'multiple':True},layout
            image=p.send('Page.captureScreenshot',{'format':'jpeg','quality':85})['result']['data']
            (root/'ui-checks'/f'product-multi-{tab}-{width}.jpg').write_bytes(base64.b64decode(image))
    p.js("document.querySelector('#creation-panel-import button[aria-label=\"Xóa ảnh 1\"]').click()")
    time.sleep(.2)
    assert keys()==image_keys[1:],'Removing one image removed the wrong reference'
    assert json.loads(p.js("document.querySelector('#creation-panel-idea input[name=productImagePaths]').value"))==image_keys[1:]
    p.send('DOM.setFileInputFiles',{'nodeId':picker,'files':[fixture]})
    wait("JSON.parse(document.querySelector('#creation-panel-import input[name=productImagePaths]').value).length===2",'Adding another image replaced existing photo')
    wait("!document.querySelector('#creation-panel-import input[type=file]').disabled",'Upload stayed busy')
    image_keys=keys()
    p.send('DOM.setFileInputFiles',{'nodeId':picker,'files':[fixture]*7})
    time.sleep(.2)
    assert keys()==image_keys,'Limit violation changed the references'
    assert p.js("document.querySelector('#creation-panel-import [data-product-attachments] [role=alert]').textContent.includes('6')")
    # Keep partial successful uploads if a later image is corrupt.
    bad=root/'ui-checks'/'invalid-product.png'
    bad.write_text('invalid fixture',encoding='utf-8')
    p.send('DOM.setFileInputFiles',{'nodeId':picker,'files':[fixture,str(bad)]})
    wait("JSON.parse(document.querySelector('#creation-panel-import input[name=productImagePaths]').value).length===3",'Partial upload did not preserve success')
    wait("!document.querySelector('#creation-panel-import input[type=file]').disabled",'Failed upload stayed busy')
    assert keys()[:2]==image_keys
    p.js("document.querySelector('#creation-panel-import button[aria-label=\"Xóa ảnh 3\"]').click()")
    time.sleep(.2)
    assert keys()==image_keys
    print('PASS: multiple selection, compact icon, thumbnails, shared state, per-image removal, limits and partial upload failure.',flush=True)
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
    db_check('verify-products')
    wait("document.querySelectorAll('img[alt^=\"Ảnh sản phẩm\"]').length===2",'Saved products not visible in editor')
    print('PASS: mobile/desktop import UI, explicit review, ten-scene editor and no automatic generation.',flush=True)
finally:
    session.close()
    if project_id: db_check('cleanup')
