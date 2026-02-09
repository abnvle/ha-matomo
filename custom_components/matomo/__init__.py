"""Matomo Analytics integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MatomoAPI
from .const import (
    CONF_INCLUDE_AGGREGATE,
    CONF_SITE_ID,
    CONF_SITE_NAME,
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
)
from .coordinator import MatomoDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Matomo Analytics from a config entry."""
    session = async_get_clientsession(hass)

    api = MatomoAPI(
        session=session,
        url=entry.data[CONF_URL],
        token_auth=entry.data[CONF_TOKEN],
    )

    coordinator = MatomoDataCoordinator(
        hass=hass,
        api=api,
        site_id=entry.data[CONF_SITE_ID],
        site_name=entry.data[CONF_SITE_NAME],
        include_aggregate=entry.data.get(CONF_INCLUDE_AGGREGATE, False),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
