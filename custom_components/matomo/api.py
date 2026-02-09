"""Matomo API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class MatomoAPIError(Exception):
    """Matomo API error."""


class MatomoAuthError(MatomoAPIError):
    """Matomo authentication error."""


class MatomoAPI:
    """Async client for the Matomo Reporting API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        token_auth: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._base_url = self._normalize_url(url)
        self._token_auth = token_auth

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Ensure the URL points to the Matomo API endpoint."""
        url = url.rstrip("/")
        if not url.endswith("index.php"):
            url = f"{url}/index.php"
        return url

    async def _request(self, method: str, **params: Any) -> Any:
        """Make an API request using POST with token in body."""
        import json

        # URL params (without token)
        url_params: dict[str, Any] = {
            "module": "API",
            "method": method,
            "format": "JSON",
        }

        # POST body with token + extra params
        post_data: dict[str, Any] = {
            "token_auth": self._token_auth,
        }
        post_data.update(params)

        _LOGGER.debug("Matomo API call: %s -> %s", method, self._base_url)

        try:
            async with self._session.post(
                self._base_url,
                params=url_params,
                data=post_data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise MatomoAuthError("Invalid authentication token (HTTP 401)")

                text = await resp.text()
                _LOGGER.debug("Matomo response status=%s, body=%s", resp.status, text[:500])

                resp.raise_for_status()

                # Check if response is actually JSON
                if text.strip().startswith("<!") or text.strip().startswith("<html"):
                    raise MatomoAPIError(
                        f"Matomo returned HTML instead of JSON. Check if URL is correct: {self._base_url}"
                    )

                try:
                    data = json.loads(text)
                except json.JSONDecodeError as err:
                    raise MatomoAPIError(
                        f"Invalid JSON response from Matomo: {text[:200]}"
                    ) from err

        except MatomoAPIError:
            raise
        except aiohttp.ClientError as err:
            raise MatomoAPIError(f"Error communicating with Matomo: {err}") from err

        if isinstance(data, dict) and data.get("result") == "error":
            msg = data.get("message", "Unknown Matomo API error")
            _LOGGER.error("Matomo API error response: %s", msg)
            if "token" in msg.lower() or "auth" in msg.lower() or "access" in msg.lower():
                raise MatomoAuthError(msg)
            raise MatomoAPIError(msg)

        return data

    async def validate_connection(self) -> bool:
        """Test the connection and authentication."""
        # First test basic connectivity
        await self._request("API.getMatomoVersion")
        # Then test auth by fetching sites (requires valid token)
        sites = await self._request("SitesManager.getSitesWithAtLeastViewAccess")
        return isinstance(sites, list)

    async def get_sites(self) -> list[dict[str, Any]]:
        """Get all sites the user has access to."""
        return await self._request("SitesManager.getSitesWithAtLeastViewAccess")

    async def get_site_from_id(self, site_id: int) -> list[dict[str, Any]]:
        """Get site info by ID."""
        return await self._request("SitesManager.getSiteFromId", idSite=site_id)

    async def get_visit_summary(
        self, site_id: int | str, period: str, date: str = "today"
    ) -> dict[str, Any]:
        """Get visit summary for a site and period."""
        result = await self._request(
            "VisitsSummary.get", idSite=site_id, period=period, date=date
        )
        if isinstance(result, list) and len(result) == 0:
            return {}
        return result

    async def get_actions(
        self, site_id: int | str, period: str, date: str = "today"
    ) -> dict[str, Any]:
        """Get actions (pageviews, downloads, outlinks) for a site and period."""
        result = await self._request(
            "Actions.get", idSite=site_id, period=period, date=date
        )
        if isinstance(result, list) and len(result) == 0:
            return {}
        return result

    async def get_live_counters(
        self, site_id: int, last_minutes: int = 30
    ) -> list[dict[str, Any]]:
        """Get live visitor counters."""
        return await self._request(
            "Live.getCounters", idSite=site_id, lastMinutes=last_minutes
        )

    async def get_all_sites_summary(
        self, period: str = "day", date: str = "today"
    ) -> dict[str, Any]:
        """Get visit summary + actions aggregated across all sites (idSite=all)."""
        totals: dict[str, int] = {}

        for api_method in ("VisitsSummary.get", "Actions.get"):
            result = await self._request(
                api_method, idSite="all", period=period, date=date
            )
            if isinstance(result, dict):
                for _site_id, site_data in result.items():
                    if isinstance(site_data, dict):
                        for key, value in site_data.items():
                            if isinstance(value, (int, float)):
                                totals[key] = totals.get(key, 0) + int(value)

        return totals