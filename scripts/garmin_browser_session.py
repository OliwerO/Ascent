#!/usr/bin/env python3
"""In-page fetch transport for the Garmin Connect API.

Background — what works and why:

Garmin's web SPA hits `connect.garmin.com/gc-api/...` (same-origin) and
attaches a runtime-generated `connect-csrf-token` header to every call.
The gc-api gateway authenticates against the giant Hapi.js Iron-encrypted
`session=Fe26.2*...` cookie that storage_state DOES preserve. There is
NO `JWT_FGP` cookie involved — that was a phantom from Garmin's older
auth scheme.

Three things had to be true to authenticate from headless Firefox:
  1. Use the same-origin host: `connect.garmin.com/gc-api`, NOT
     `connectapi.garmin.com` (which APIRequestContext can't authenticate
     against from inside a different process).
  2. Send the runtime CSRF token in the `connect-csrf-token` header.
  3. Make the request from inside a *rendered page context* via
     `page.evaluate("fetch(...)")` so the browser sets `Origin`,
     `Referer`, `sec-fetch-site: same-origin`, etc. APIRequestContext
     does not include those, and the gateway rejects without them.

This module is monkey-patched into garminconnect.Client._run_request in
garmin_auth.py — see _try_browser_session there.
"""

import atexit
import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

log = logging.getLogger("garmin_browser_session")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORAGE_STATE_PATH = Path.home() / ".garminconnect" / "garmin_storage_state.json"
PROJECT_STORAGE_STATE_PATH = PROJECT_ROOT / ".garminconnect" / "garmin_storage_state.json"

# Same-origin host the SPA uses for all API calls.
GC_API_HOST = "https://connect.garmin.com/gc-api"


class StorageStateMissingError(FileNotFoundError):
    """Raised when no saved Playwright storage state is on disk."""


class BrowserResponse:
    """Duck-typed requests.Response for the bits garminconnect uses."""

    def __init__(self, status: int, headers: dict, text: str):
        self.status_code = status
        self.headers = headers
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._text.encode("utf-8") if isinstance(self._text, str) else self._text

    def json(self) -> Any:
        return json.loads(self._text)


def _resolve_storage_path() -> Path:
    if STORAGE_STATE_PATH.exists():
        return STORAGE_STATE_PATH
    if PROJECT_STORAGE_STATE_PATH.exists():
        return PROJECT_STORAGE_STATE_PATH
    raise StorageStateMissingError(
        f"No saved Garmin storage state at {STORAGE_STATE_PATH} "
        f"or {PROJECT_STORAGE_STATE_PATH}. "
        f"Run: python3 scripts/garmin_browser_bootstrap.py"
    )


class _PlaywrightSingleton:
    """Lazy-launched Playwright + headless Firefox + persistent context + page.

    Captures the CSRF token from the SPA's first authenticated request and
    keeps a live page on connect.garmin.com so in-page fetches can run.
    Torn down via atexit.
    """

    _instance: "_PlaywrightSingleton | None" = None

    def __init__(self) -> None:
        storage_path = _resolve_storage_path()
        from playwright.sync_api import sync_playwright

        log.info("Launching headless Firefox via Playwright (storage=%s)", storage_path)
        self._p = sync_playwright().start()
        self._browser = self._p.firefox.launch(headless=True)
        self._context = self._browser.new_context(
            storage_state=str(storage_path),
            locale="en-US",
        )

        captured = {"csrf": None}

        def _on_request(req):
            if captured["csrf"] is None:
                tok = req.headers.get("connect-csrf-token")
                if tok:
                    captured["csrf"] = tok

        self._page = self._context.new_page()
        self._page.on("request", _on_request)

        log.info("Opening connect.garmin.com/modern/ to capture CSRF token...")
        try:
            self._page.goto(
                "https://connect.garmin.com/modern/",
                wait_until="domcontentloaded",
                timeout=20000,
            )
        except Exception as e:
            log.warning("Initial /modern/ goto error (continuing): %s", e)

        # Wait for SPA to fire its first authenticated request so we capture
        # the runtime CSRF token. Poll up to 10s.
        for _ in range(20):
            if captured["csrf"]:
                break
            self._page.wait_for_timeout(500)

        if not captured["csrf"]:
            self.close()
            raise RuntimeError(
                "BrowserSession: failed to capture connect-csrf-token from SPA. "
                "Storage state may be expired — re-run garmin_browser_bootstrap.py."
            )

        self._csrf_token = captured["csrf"]
        log.info("Captured CSRF token: %s...", self._csrf_token[:12])

        # Verify we landed authenticated (page should be on /app/home or /modern/)
        # rather than redirected back to SSO.
        if "sso.garmin.com" in self._page.url:
            self.close()
            raise RuntimeError(
                f"BrowserSession: page redirected to SSO ({self._page.url}). "
                "Storage state expired — re-run garmin_browser_bootstrap.py."
            )

        atexit.register(self.close)

    @classmethod
    def get(cls) -> "_PlaywrightSingleton":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def page(self):
        return self._page

    @property
    def csrf_token(self) -> str:
        return self._csrf_token

    def close(self) -> None:
        for attr, name in [("_page", "page"), ("_context", "context"), ("_browser", "browser")]:
            try:
                obj = getattr(self, attr, None)
                if obj is not None:
                    obj.close()
            except Exception as e:
                log.debug("Playwright %s close error (ignored): %s", name, e)
        try:
            if getattr(self, "_p", None):
                self._p.stop()
        except Exception as e:
            log.debug("Playwright stop error (ignored): %s", e)
        _PlaywrightSingleton._instance = None


# JavaScript run inside the page to perform the fetch. Defined once.
_FETCH_JS = """
async ({url, method, headers, body}) => {
    try {
        const opts = {
            method: method,
            credentials: 'include',
            headers: headers,
        };
        if (body !== null && body !== undefined) {
            opts.body = body;
        }
        const r = await fetch(url, opts);
        const text = await r.text();
        const respHeaders = {};
        r.headers.forEach((v, k) => { respHeaders[k] = v; });
        return {status: r.status, headers: respHeaders, text: text};
    } catch (e) {
        return {error: String(e)};
    }
}
"""


class BrowserSession:
    """Routes HTTP requests through an in-page fetch in a headless browser.

    Used to monkey-patch garminconnect.Client._run_request — see
    garmin_auth.py _try_browser_session.
    """

    def __init__(self) -> None:
        self._pw = _PlaywrightSingleton.get()

    @property
    def csrf_token(self) -> str:
        return self._pw.csrf_token

    def fetch(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        json_body: Any = None,
        data: Any = None,
        timeout: float = 15.0,
    ) -> BrowserResponse:
        """Make a request via the in-page fetch and return a Response."""
        # Build the final URL with query params
        if params:
            # Drop None values which the library sometimes passes
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}{urlencode(clean_params)}"

        # Merge headers — always include CSRF + browser-shaped Accept.
        merged: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "connect-csrf-token": self._pw.csrf_token,
            "NK": "NT",
            "X-app-ver": "5.23.0.33",
        }
        if headers:
            for k, v in headers.items():
                # Strip cookie headers — the browser handles cookies via the jar.
                if k.lower() == "cookie":
                    continue
                merged[str(k)] = str(v)

        # Body handling
        body: Any = None
        if json_body is not None:
            body = json.dumps(json_body)
            merged.setdefault("Content-Type", "application/json")
        elif data is not None:
            body = data if isinstance(data, str) else json.dumps(data)

        payload = {
            "url": url,
            "method": method.upper(),
            "headers": merged,
            "body": body,
        }

        # Run the fetch inside the page; the browser provides cookies +
        # Origin/Referer/sec-fetch-* automatically.
        result = self._pw.page.evaluate(_FETCH_JS, payload)

        if "error" in result:
            raise RuntimeError(f"In-page fetch failed: {result['error']}")

        return BrowserResponse(
            status=int(result["status"]),
            headers=dict(result.get("headers") or {}),
            text=result.get("text") or "",
        )


def shutdown() -> None:
    """Explicit teardown helper (atexit also handles this)."""
    if _PlaywrightSingleton._instance is not None:
        _PlaywrightSingleton._instance.close()
