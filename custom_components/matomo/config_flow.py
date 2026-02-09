"""Config flow for Matomo Analytics integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MatomoAPI, MatomoAPIError, MatomoAuthError
from .const import (
    CONF_INCLUDE_AGGREGATE,
    CONF_SITE_ID,
    CONF_SITE_NAME,
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MatomoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Matomo Analytics."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._url: str = ""
        self._token: str = ""
        self._sites: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - URL and token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._url = user_input[CONF_URL].rstrip("/")
            self._token = user_input[CONF_TOKEN]

            session = async_get_clientsession(self.hass)
            api = MatomoAPI(session, self._url, self._token)

            try:
                self._sites = await api.get_sites()

                if not self._sites:
                    errors["base"] = "no_sites"
                else:
                    return await self.async_step_site()

            except MatomoAuthError as err:
                _LOGGER.error("Matomo auth error: %s", err)
                errors[CONF_TOKEN] = "invalid_auth"
            except MatomoAPIError as err:
                _LOGGER.error("Matomo API error: %s", err)
                errors[CONF_URL] = "cannot_connect"
            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.error("Matomo connection error: %s", err)
                errors[CONF_URL] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error connecting to Matomo: %s", err)
                errors[CONF_URL] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_site(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle site selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_id = int(user_input[CONF_SITE_ID])

            # Find the site name
            site_name = ""
            for site in self._sites:
                if int(site["idsite"]) == site_id:
                    site_name = site["name"]
                    break

            # Check for duplicate entries
            unique_id = f"{self._url}_{site_id}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Matomo - {site_name}",
                data={
                    CONF_URL: self._url,
                    CONF_TOKEN: self._token,
                    CONF_SITE_ID: site_id,
                    CONF_SITE_NAME: site_name,
                    CONF_INCLUDE_AGGREGATE: user_input.get(CONF_INCLUDE_AGGREGATE, False),
                },
            )

        # Build site selection options
        site_options = {
            str(site["idsite"]): f"{site['name']} (ID: {site['idsite']})"
            for site in self._sites
        }

        return self.async_show_form(
            step_id="site",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SITE_ID): vol.In(site_options),
                    vol.Optional(CONF_INCLUDE_AGGREGATE, default=False): bool,
                }
            ),
            errors=errors,
        )