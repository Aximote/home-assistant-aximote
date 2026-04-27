"""Aximote public REST API client."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class AximoteError(Exception):
    """Base Aximote API error."""


class AximoteAuthError(AximoteError):
    """Invalid or revoked token (401)."""


class AximoteProRequiredError(AximoteError):
    """Subscription / entitlement issue (402)."""


class AximoteRateLimitedError(AximoteError):
    """Rate limited (429)."""


class AximoteApiError(AximoteError):
    """Other API error with structured code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class AximoteApiClient:
    """Thin async client for /api/public/v1."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        token: str,
    ) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                text = await resp.text()
                if resp.status == 401:
                    raise AximoteAuthError("Unauthorized")
                if resp.status == 402:
                    raise AximoteProRequiredError("Payment required")
                if resp.status == 429:
                    raise AximoteRateLimitedError("Rate limited")
                if resp.status >= 400:
                    code = "http_error"
                    message = text[:500] if text else resp.reason
                    if text:
                        try:
                            body: Any = json.loads(text)
                            if isinstance(body, dict):
                                code = str(body.get("code", code))
                                message = str(body.get("message", message))
                        except (json.JSONDecodeError, TypeError):
                            pass
                    raise AximoteApiError(code, message)
                if not text:
                    return None
                return json.loads(text)
        except aiohttp.ClientError as err:
            raise AximoteApiError("network_error", str(err)) from err

    async def async_me(self) -> dict[str, Any]:
        """GET /api/public/v1/me."""
        result = await self._request("GET", "/api/public/v1/me")
        if not isinstance(result, dict):
            msg = "Unexpected /me response"
            raise AximoteApiError("invalid_response", msg)
        return result

    async def async_list_vehicles(self) -> list[dict[str, Any]]:
        """GET /api/public/v1/vehicles."""
        result = await self._request("GET", "/api/public/v1/vehicles")
        if not isinstance(result, list):
            msg = "Unexpected /vehicles response"
            raise AximoteApiError("invalid_response", msg)
        return result

    async def async_get_vehicle_state(self, vehicle_id: str) -> dict[str, Any]:
        """GET /api/public/v1/vehicles/{id}/state."""
        result = await self._request(
            "GET",
            f"/api/public/v1/vehicles/{vehicle_id}/state",
        )
        if not isinstance(result, dict):
            msg = "Unexpected /state response"
            raise AximoteApiError("invalid_response", msg)
        return result

    async def async_latest_trip(self, vehicle_id: str) -> dict[str, Any] | None:
        """First item from GET /api/public/v1/trips?vehicleId=&limit=1."""
        page = await self._request(
            "GET",
            "/api/public/v1/trips",
            params={"vehicleId": vehicle_id, "limit": 1},
        )
        if not isinstance(page, dict):
            return None
        items = page.get("items")
        if not isinstance(items, list) or not items:
            return None
        first = items[0]
        return first if isinstance(first, dict) else None

    async def async_latest_refuel(self, vehicle_id: str) -> dict[str, Any] | None:
        """First item from GET /api/public/v1/refuels?vehicleId=&limit=1."""
        page = await self._request(
            "GET",
            "/api/public/v1/refuels",
            params={"vehicleId": vehicle_id, "limit": 1},
        )
        if not isinstance(page, dict):
            return None
        items = page.get("items")
        if not isinstance(items, list) or not items:
            return None
        first = items[0]
        return first if isinstance(first, dict) else None
