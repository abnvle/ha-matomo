"""DataUpdateCoordinator for Matomo Analytics."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MatomoAPI, MatomoAPIError, MatomoAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MatomoDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from Matomo API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MatomoAPI,
        site_id: int,
        site_name: str,
        include_aggregate: bool,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{site_name}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api
        self.site_id = site_id
        self.site_name = site_name
        self.include_aggregate = include_aggregate

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Matomo."""
        try:
            data: dict[str, Any] = {"site": {}, "live": {}, "aggregate": {}}

            # Fetch visit summary + actions for day, week, month
            for period in ("day", "week", "month"):
                summary = await self.api.get_visit_summary(self.site_id, period)
                actions = await self.api.get_actions(self.site_id, period)
                merged = {}
                if isinstance(summary, dict):
                    merged.update(summary)
                if isinstance(actions, dict):
                    merged.update(actions)
                data["site"][period] = merged

            # Fetch live counters
            try:
                live_result = await self.api.get_live_counters(self.site_id)
                if isinstance(live_result, list) and len(live_result) > 0:
                    data["live"] = live_result[0]
                else:
                    data["live"] = {}
            except MatomoAPIError:
                _LOGGER.warning("Failed to fetch live counters for site %s", self.site_id)
                data["live"] = {}

            # Fetch aggregate stats for all sites
            if self.include_aggregate:
                try:
                    for period in ("day", "week", "month"):
                        agg_result = await self.api.get_all_sites_summary(period)
                        data["aggregate"][period] = agg_result
                except MatomoAPIError:
                    _LOGGER.warning("Failed to fetch aggregate stats")
                    data["aggregate"] = {}

            return data

        except MatomoAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except MatomoAPIError as err:
            raise UpdateFailed(f"Error fetching Matomo data: {err}") from err