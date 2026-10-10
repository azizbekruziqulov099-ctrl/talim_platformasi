"""Focused no-database tests for the hardened Google OAuth boundary."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src" / "App.jsx"
sys.path.insert(0, str(BACKEND))
os.environ["JWT_MAXFIY_KALIT"] = "oauth-tests-0123456789abcdef0123456789"
os.environ["GOOGLE_CLIENT_ID"] = "oauth-test-client"
os.environ["GOOGLE_CLIENT_SECRET"] = "oauth-test-secret"
os.environ["BAZA_URL"] = "https://api.example"
os.environ["FRONTEND_URL"] = "https://frontend.example"

main = importlib.import_module("main")


class _FakeGoogleResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class _UnverifiedGoogleClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, *args, **kwargs):
        return _FakeGoogleResponse({"access_token": "google-access"})

    async def get(self, *args, **kwargs):
        return _FakeGoogleResponse({
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified",
        })


class OAuthHardeningTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app, base_url="https://api.example")

    def _registration_grant(self, seconds: int = 60, email: str = "person@example.com") -> str:
        return main._oauth_imzolangan_token(
            "google_registration_grant",
            seconds,
            outcome="registration",
            email=email,
        )

    def _assert_grant_rejected(self, grant, email: str = "person@example.com") -> None:
        with self.assertRaises(HTTPException) as caught:
            main._google_registration_tekshir(grant, email)
        self.assertEqual(caught.exception.status_code, 401)

    def test_login_uses_signed_secure_state_cookie_and_pkce_s256(self):
        response = self.client.get("/auth/google/login", follow_redirects=False)
        params = parse_qs(urlparse(response.headers["location"]).query)
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertEqual(len(params["code_challenge"][0]), 43)
        self.assertTrue(params["state"][0])
        cookie = response.headers["set-cookie"]
        self.assertIn("__Host-google-oauth-state=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=lax", cookie)

    def test_callback_rejects_state_mismatch_before_google_call(self):
        with patch.object(main.httpx, "AsyncClient", side_effect=AssertionError("must not call Google")):
            response = self.client.get(
                "/auth/google/callback?code=code&state=wrong",
                follow_redirects=False,
            )
        parsed = urlparse(response.headers["location"])
        self.assertEqual(parse_qs(parsed.fragment), {"oauth_xato": ["state"]})
        self.assertFalse(parsed.query)

    def test_callback_rejects_unverified_google_email_before_database(self):
        login = self.client.get("/auth/google/login", follow_redirects=False)
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        with (
            patch.object(main.httpx, "AsyncClient", _UnverifiedGoogleClient),
            patch.object(main, "_db", side_effect=AssertionError("must not query database")),
        ):
            response = self.client.get(
                f"/auth/google/callback?code=code&state={state}",
                follow_redirects=False,
            )
        parsed = urlparse(response.headers["location"])
        self.assertEqual(
            parse_qs(parsed.fragment),
            {"oauth_xato": ["email_tasdiqlanmagan"]},
        )
        self.assertFalse(parsed.query)

    def test_login_jwt_is_only_returned_by_post_exchange(self):
        ticket = main._oauth_imzolangan_token(
            "google_login_ticket",
            main.OAUTH_TICKET_SECONDS,
            outcome="login",
            user_id=123,
        )
        redirect = main._oauth_frontend_redirect(ticket=ticket)
        parsed = urlparse(redirect.headers["location"])
        self.assertFalse(parsed.query)
        self.assertEqual(parse_qs(parsed.fragment), {"oauth_ticket": [ticket]})
        self.assertNotIn("/kabinet?token=", redirect.headers["location"])

        exchange = self.client.post(
            "/auth/google/exchange",
            headers={"Origin": "https://frontend.example"},
            json={"ticket": ticket},
        )
        self.assertEqual(exchange.status_code, 200, exchange.text)
        self.assertEqual(exchange.json()["holat"], "kirdi")
        self.assertEqual(main._jwt_tekshir(exchange.json()["token"]), 123)

    def test_registration_grant_rejects_missing_invalid_mismatch_and_expired(self):
        self._assert_grant_rejected(None)
        self._assert_grant_rejected("not-a-jwt")
        self._assert_grant_rejected(self._registration_grant(), "other@example.com")
        self._assert_grant_rejected(self._registration_grant(seconds=-1))

    def test_ulash_and_royxat_reject_bad_grants_before_database(self):
        bad_cases = (
            ("missing", None, "person@example.com"),
            ("invalid", "not-a-jwt", "person@example.com"),
            ("mismatch", self._registration_grant(), "other@example.com"),
            ("expired", self._registration_grant(seconds=-1), "person@example.com"),
        )
        for label, grant, email in bad_cases:
            for path, payload in (
                ("/auth/ulash", {"email": email, "kod": "ABC123"}),
                ("/auth/royxat", {"email": email, "ism": "Person", "rol": "oquvchi"}),
            ):
                if grant is not None:
                    payload["oauth_grant"] = grant
                with self.subTest(label=label, path=path), patch.object(
                    main,
                    "_db",
                    side_effect=AssertionError("invalid grant must be rejected before DB"),
                ):
                    response = self.client.post(path, json=payload)
                    self.assertEqual(response.status_code, 401, response.text)

    def test_valid_registration_grant_is_bound_to_normalized_email(self):
        grant = self._registration_grant(email="person@example.com")
        claims = main._google_registration_tekshir(grant, " Person@Example.com ")
        self.assertEqual(claims["email"], "person@example.com")
        self.assertEqual(claims["purpose"], "google_registration_grant")

    def test_ticket_exchange_returns_bound_registration_grant(self):
        ticket = main._oauth_imzolangan_token(
            "google_login_ticket",
            main.OAUTH_TICKET_SECONDS,
            outcome="registration",
            email="person@example.com",
            name="Person",
        )
        response = self.client.post(
            "/auth/google/exchange",
            headers={"Origin": "https://frontend.example"},
            json={"ticket": ticket},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["holat"], "ulash")
        self.assertEqual(payload["email"], "person@example.com")
        main._google_registration_tekshir(payload["oauth_grant"], payload["email"])
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_frontend_sends_grant_in_both_valid_form_payloads(self):
        source = FRONTEND.read_text(encoding="utf-8")
        self.assertIn(
            "JSON.stringify({ email, kod: kod.trim(), oauth_grant: oauthGrant })",
            source,
        )
        self.assertIn(
            "email, ism: ismInput.trim(), rol, oauth_grant: oauthGrant",
            source,
        )
        self.assertIn("body: JSON.stringify({ ticket: yol.oauthTicket })", source)
        self.assertIn('credentials: "include"', source)


if __name__ == "__main__":
    unittest.main()
