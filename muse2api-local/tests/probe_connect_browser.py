"""Smoke-test only the public sign-in screen. Never submits or saves an account."""
import base64
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CFG
from login_bridge import LoginSession

session = LoginSession(CFG)
try:
    frame = None
    for _ in range(8):
        time.sleep(2)
        frame = session.state()
        if frame["fields"]:
            break
    target = Path(__file__).resolve().parents[2] / "connect-probe.jpg"
    target.write_bytes(base64.b64decode(frame["image"]))
    if frame["fields"]:
        field = frame["fields"][0]
        session.act({"kind": "fill", "index": field["index"], "fingerprint": field["fingerprint"], "value": "test@example.invalid"})
        assert session.page.js("document.querySelector('input').value") == "test@example.invalid"
        print("Input bridge verified without submitting sign-in.")
    print(json.dumps({"origin": frame["origin"], "fields": frame["fields"],
                      "can_finish": frame["can_finish"], "screenshot": str(target)}, ensure_ascii=False))
finally:
    session.close()
