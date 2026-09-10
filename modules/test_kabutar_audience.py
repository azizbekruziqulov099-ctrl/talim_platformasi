"""Run python -m unittest modules.test_kabutar_audience -v.
No network; mocked FastAPI routing and DB boundaries. Not live integration.
"""
import sys
import types
import unittest
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch
from modules.kabutar_audience import AudienceService, _HeartbeatThrottle, _bearer_token, _daily_series, register_audience


class HTTPError(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


class FakeRouter:
    def __init__(self, startup): self.startup = startup
    def add_event_handler(self, event, fn):
        self.startup.append((event, fn))


class FakeApp:
    def __init__(self):
        self.state = types.SimpleNamespace()
        self.routes, self.startup = {}, []
        self.router = FakeRouter(self.startup)
    def route(self, path, **kwargs):
        def save(fn):
            self.routes[path] = fn
            return fn
        return save
    post = get = route


FAKE_API = types.SimpleNamespace(Header=lambda default=None, **kw: default,
    Query=lambda default=None, **kw: default, Response=type('Response', (), {}), HTTPException=HTTPError)


class AudienceTests(unittest.TestCase):
    def test_uzbek_day_and_no_preinstallation_history(self):
        started = datetime(2026, 9, 8, 20, 10, tzinfo=timezone.utc)
        rows = [{'day': date(2026, 9, 9), 'active_users': 7, 'logins': 12}]
        self.assertEqual(_daily_series(rows, date(2026, 9, 10), 30, started), [
            {'date': '2026-09-09', 'active_users': 7, 'logins': 12},
            {'date': '2026-09-10', 'active_users': 0, 'logins': 0}])

    def test_requested_days_limits_history(self):
        self.assertEqual(len(_daily_series([], date(2026, 9, 9), 7, datetime(2020, 1, 1, tzinfo=timezone.utc))), 7)

    def test_throttle_initial_boundary_and_memory_bound(self):
        cache = _HeartbeatThrottle(size=2)
        self.assertFalse(cache.recent(1, 100))
        cache.mark(1, 100)
        self.assertTrue(cache.recent(1, 159))
        self.assertFalse(cache.recent(1, 160))
        cache.mark(2, 101)
        cache.mark(3, 102)
        self.assertFalse(cache.recent(1, 103))
        self.assertEqual(len(cache.seen), 2)

    def test_bearer_required(self):
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            for token in [None, '', 'Basic secret', 'Bearer ']:
                with self.assertRaises(HTTPError) as exc:
                    _bearer_token(token)
                self.assertEqual(exc.exception.status_code, 401)
            self.assertEqual(_bearer_token('bEaReR valid-token'), 'valid-token')

    def test_presence_identity_comes_from_verified_session(self):
        platform = types.SimpleNamespace(_jwt_tekshir=Mock(return_value=-44), _admin_tekshir=Mock())
        app = FakeApp()
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            service = register_audience(app, platform)
            service.touch = Mock(return_value=True)
            result = app.routes['/api/presence'](authorization='Bearer signed')
        platform._jwt_tekshir.assert_called_once_with('signed')
        service.touch.assert_called_once_with(-44)
        self.assertEqual(result['online_window_seconds'], 180)

    def test_dynamic_verifier_rejects_revoked_session(self):
        platform = types.SimpleNamespace(_jwt_tekshir=Mock(return_value=1), _admin_tekshir=Mock())
        app = FakeApp()
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            service = register_audience(app, platform)
            service.touch = Mock()
            platform._jwt_tekshir = Mock(side_effect=HTTPError(401, 'revoked'))
            with self.assertRaises(HTTPError) as exc:
                app.routes['/api/presence'](authorization='Bearer revoked-session')
        self.assertEqual(exc.exception.status_code, 401)
        service.touch.assert_not_called()

    def test_non_admin_never_reads_metrics(self):
        platform = types.SimpleNamespace(_jwt_tekshir=Mock(), _admin_tekshir=Mock(side_effect=HTTPError(403, 'admin only')))
        app = FakeApp()
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            service = register_audience(app, platform)
            service.snapshot = Mock()
            with self.assertRaises(HTTPError) as exc:
                app.routes['/api/admin/audience'](types.SimpleNamespace(headers={}), 30, 'Bearer user')
        self.assertEqual(exc.exception.status_code, 403)
        service.snapshot.assert_not_called()

    def test_admin_result_is_private(self):
        platform = types.SimpleNamespace(_jwt_tekshir=Mock(), _admin_tekshir=Mock(return_value=1))
        app, response = FakeApp(), types.SimpleNamespace(headers={})
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            service = register_audience(app, platform)
            service.snapshot = Mock(return_value={'summary': {'online_users': 5}})
            result = app.routes['/api/admin/audience'](response, 7, 'Bearer admin')
        self.assertEqual(response.headers['Cache-Control'], 'private, no-store')
        self.assertEqual(result['summary']['online_users'], 5)
        service.snapshot.assert_called_once_with(7)

    def test_failed_database_rolls_back_closes_and_does_not_poison_throttle(self):
        conn = Mock()
        conn.cursor.return_value.execute.side_effect = RuntimeError('db unavailable')
        service = AudienceService(types.SimpleNamespace(_db=Mock(return_value=conn)))
        with self.assertRaises(RuntimeError):
            service.touch(10)
        self.assertFalse(service.throttle.recent(10, 100))
        conn.rollback.assert_called_once()
        conn.cursor.return_value.close.assert_called_once()
        conn.close.assert_called_once()
        conn.commit.assert_not_called()

    def test_repeat_does_not_inflate_daily_active(self):
        conn = Mock()
        conn.cursor.return_value.fetchone.return_value = {'day_changed': False}
        service = AudienceService(types.SimpleNamespace(_db=Mock(return_value=conn)))
        service.touch(20)
        statements = [args[0] for args, _ in conn.cursor.return_value.execute.call_args_list]
        self.assertFalse(any('INSERT INTO kabutar_audience_daily' in sql for sql in statements))
        conn.commit.assert_called_once()

    def test_new_day_counts_one_distinct_account(self):
        conn = Mock()
        conn.cursor.return_value.fetchone.return_value = {'day_changed': True}
        service = AudienceService(types.SimpleNamespace(_db=Mock(return_value=conn)))
        service.touch(20)
        self.assertEqual(conn.cursor.return_value.execute.call_args.args[1], (1, 0))

    def test_login_counts_when_presence_update_is_throttled(self):
        conn = Mock()
        conn.cursor.return_value.fetchone.return_value = None
        service = AudienceService(types.SimpleNamespace(_db=Mock(return_value=conn)))
        service.touch(20, login=True)
        self.assertEqual(conn.cursor.return_value.execute.call_args.args[1], (0, 1))

    def test_refresh_link_migration_are_not_new_logins(self):
        service = AudienceService(types.SimpleNamespace())
        service.touch = Mock()
        for method in ['legacy', 'refresh', 'link', 'unknown']:
            service.record_login(20, method)
        service.touch.assert_not_called()
        for method in ['google', 'telegram', 'password']:
            service.record_login(20, method)
        self.assertEqual(service.touch.call_count, 3)

    def test_register_is_idempotent(self):
        app, platform = FakeApp(), types.SimpleNamespace()
        with patch.dict(sys.modules, {'fastapi': FAKE_API}):
            first, second = register_audience(app, platform), register_audience(app, platform)
        self.assertIs(first, second)
        self.assertEqual(len(app.startup), 1)

    def test_bounds_reject_expensive_unbounded_scan(self):
        service = AudienceService(types.SimpleNamespace())
        for days in [0, -1, 31, 100000]:
            with self.assertRaises(ValueError):
                service.snapshot(days)


if __name__ == '__main__':
    unittest.main()
