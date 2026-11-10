"""Regression probe for Muse-style 1x1 OTP inputs. Synthetic code, no account."""
from dataclasses import replace
from pathlib import Path
import sys
import time
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession

html = '''<html><body><h1>Verification fixture</h1>
<input type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6"
 style="width:1px;height:1px;padding:0;border:0"
 oninput="document.getElementById('boxes').textContent=this.value"
 onkeydown="if(event.key==='Enter')document.body.dataset.enter='yes'">
<div id="boxes"></div>
<button onclick="document.body.dataset.advanced='yes'">Next</button>
<a href="#" role="button" onclick="document.body.dataset.resent='yes'">Resend code</a>
</body></html>'''
session = LoginSession(replace(CFG, site_url='data:text/html,' + quote(html)))
try:
    for _ in range(20):
        state = session.state()
        if state.get('otp'):
            break
        time.sleep(.1)
    otp = state.get('otp')
    assert otp and otp['length'] == 6, 'Tiny OTP input must be detected'
    assert state['fields'] == [], 'Tiny backing input must not be drawn over screenshot'
    session.act({'kind': 'fill', 'index': otp['index'], 'fingerprint': otp['fingerprint'], 'value': '123456'})
    assert session.page.js("document.querySelector('#boxes').textContent") == '123456', 'Input event must reach OTP widget'
    session.act({'kind': 'enter'})
    assert session.page.js("document.body.dataset.enter") == 'yes', 'Enter must reach focused OTP input'
    session.act({'kind': 'advance'})
    assert session.page.js("document.body.dataset.advanced") == 'yes', 'Native form must activate Next'
    session.act({'kind': 'resend'})
    assert session.page.js("document.body.dataset.resent") == 'yes', 'Resend control must be reachable'
    # Model an OTP widget that automatically navigates on the sixth digit.
    session.page.js("""document.body.innerHTML = '<input type="text" autocomplete="one-time-code" maxlength="6" style="width:1px;height:1px"><div id="next-step"></div>';
      document.querySelector('input').addEventListener('input', e => {
        if(e.target.value.length===6) document.body.innerHTML='<textarea placeholder="Message"></textarea>';
      });""")
    otp = session.state()['otp']
    assert otp
    session.act({'kind':'fill','index':otp['index'],'fingerprint':otp['fingerprint'],'value':'123456'})
    result = session.act({'kind':'advance','fingerprint':otp['fingerprint']})
    assert result.get('transitioned') is True, 'Auto-submit must not fail when old Next is gone'
    session.page.js("""document.body.innerHTML='<input type="text" autocomplete="one-time-code" maxlength="6" style="width:1px;height:1px"><button disabled>Next</button>';
      document.querySelector('input').addEventListener('input',e=>{if(e.target.value.length===6)setTimeout(()=>{document.body.innerHTML='<textarea></textarea>';},1800);});""")
    otp = session.state()['otp']
    session.act({'kind':'fill','index':otp['index'],'fingerprint':otp['fingerprint'],'value':'123456'})
    result = session.act({'kind':'advance','fingerprint':otp['fingerprint']})
    assert result.get('pending') is True, 'Disabled Next during automatic OTP processing must return pending'
    time.sleep(2)
    assert session.page.js("!!document.querySelector('textarea')"), 'Delayed auto-submit should finish'
    print('PASS: tiny OTP detection, input, Enter, Next and resend; no account used.')
    print('PASS: auto-submitted OTP advances without clicking the next screen or raising 409.')
    print('PASS: delayed OTP processing returns pending instead of 409.')
finally:
    session.close()
