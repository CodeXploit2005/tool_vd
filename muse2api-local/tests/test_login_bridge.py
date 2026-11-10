"""Connection lifecycle tests: no real browser, credentials or account writes."""
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI, HTTPException
from engine import MuseAuthError
from login_bridge import LoginSession, register_login_routes, valid_coordinates


class LoginTests(unittest.TestCase):
    def session(self):
        return SimpleNamespace(id="test-session", replace_id="old-account", lock=threading.RLock(),
            created=time.monotonic(), closed=False, close=Mock(), state=Mock(), act=Mock(),
            engine=SimpleNamespace(read_cookies=Mock(return_value={}),
                renew_session_http=Mock(), page=None), page=Mock())

    def routes(self, session):
        app, store = FastAPI(), Mock()
        store.get_account.return_value = {"id": "old-account"}
        register_login_routes(app, SimpleNamespace(), store, lambda: True)
        endpoints = {(r.path, next(iter(r.methods))): r.endpoint for r in app.routes if r.path.startswith('/admin/connect')}
        with patch('login_bridge.LoginSession', return_value=session), patch('login_bridge.threading.Timer'):
            endpoints['/admin/connect', 'POST']({"replace_id": "old-account"})
        return endpoints, store

    def cookies(self, session):
        session.engine.read_cookies.return_value = {
            'hatch_sess': {'value': 'test-session-value', 'expires': -1},
            'hatch_native_auth_device': {'value': 'test-device-value', 'expires': -1},
        }

    def test_coordinates_reject_nonfinite_and_outside_view(self):
        for point in [(float('nan'), 1), (1, float('inf')), (-1, 3), (500, 3), (1, '2')]:
            self.assertFalse(valid_coordinates(*point))
        self.assertTrue(valid_coordinates(20, 40))

    def test_missing_session_cookie_never_saves_or_replaces(self):
        session = self.session()
        endpoints, store = self.routes(session)
        with self.assertRaises(HTTPException) as exc:
            endpoints['/admin/connect/{sid}/complete', 'POST'](session.id, {})
        self.assertEqual(exc.exception.status_code, 409)
        store.update_account.assert_not_called()
        store.add_account.assert_not_called()
        session.close.assert_not_called()

    def test_rejected_upstream_keeps_old_account(self):
        session = self.session()
        self.cookies(session)
        session.engine.renew_session_http.side_effect = MuseAuthError('test rejection')
        endpoints, store = self.routes(session)
        with self.assertRaises(HTTPException):
            endpoints['/admin/connect/{sid}/complete', 'POST'](session.id, {})
        store.update_account.assert_not_called()
        store.add_account.assert_not_called()

    def test_successful_replace_preserves_id_and_closes_session(self):
        session = self.session()
        self.cookies(session)
        session.engine.renew_session_http.return_value = {'cookies': {'new': 'session'}, 'cookies_exp': {}}
        endpoints, store = self.routes(session)
        store.update_account.return_value = {'id': 'old-account', 'label': 'New connection'}
        result = endpoints['/admin/connect/{sid}/complete', 'POST'](session.id, {'label': 'New connection'})
        self.assertTrue(result['ok'])
        self.assertEqual(store.update_account.call_args.args, ('old-account',))
        store.add_account.assert_not_called()
        session.close.assert_called_once()

    def test_cancel_is_idempotent_and_does_not_touch_accounts(self):
        session = self.session()
        endpoints, store = self.routes(session)
        cancel = endpoints['/admin/connect/{sid}', 'DELETE']
        cancel(session.id)
        cancel(session.id)
        session.close.assert_called_once()
        store.update_account.assert_not_called()
        store.delete_account.assert_not_called()

    def test_stale_input_is_rejected(self):
        session = LoginSession.__new__(LoginSession)
        session.lock, session.closed, session.page = threading.RLock(), False, Mock()
        session.page.js.return_value = False
        with self.assertRaises(HTTPException) as exc:
            session.act({'kind': 'fill', 'index': 0, 'value': 'test', 'fingerprint': 'old-screen'})
        self.assertEqual(exc.exception.status_code, 409)

    def test_auto_submitted_step_does_not_raise_conflict(self):
        session = LoginSession.__new__(LoginSession)
        session.lock, session.closed, session.page = threading.RLock(), False, Mock()
        session.page.js.return_value = 'progressed'
        result = session.act({'kind': 'advance', 'fingerprint': 'previous-otp-step'})
        self.assertTrue(result['ok'])
        self.assertTrue(result['transitioned'])
        session.page.js.assert_called_once()

    def test_disabled_current_step_still_reports_real_conflict(self):
        session = LoginSession.__new__(LoginSession)
        session.lock, session.closed, session.page = threading.RLock(), False, Mock()
        session.page.js.return_value = 'disabled'
        with patch('login_bridge.time.sleep'), self.assertRaises(HTTPException) as exc:
            session.act({'kind': 'advance', 'fingerprint': 'current-step'})
        self.assertEqual(exc.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
