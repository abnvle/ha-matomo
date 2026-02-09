"""Sensor platform for Matomo Analytics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INCLUDE_AGGREGATE, CONF_SITE_ID, CONF_SITE_NAME, DOMAIN
from .coordinator import MatomoDataCoordinator


@dataclass(frozen=True, kw_only=True)
class MatomoSensorEntityDescription(SensorEntityDescription):
    """Describe a Matomo sensor."""

    value_fn: Callable[[dict[str, Any]], int | float | None]
    is_aggregate: bool = False


def _site_value(period: str, key: str) -> Callable[[dict[str, Any]], int | None]:
    """Create a value function for per-site metrics."""

    def _get(data: dict[str, Any]) -> int | None:
        val = data.get("site", {}).get(period, {}).get(key)
        return int(val) if val is not None else None

    return _get


def _live_value(key: str) -> Callable[[dict[str, Any]], int | None]:
    """Create a value function for live metrics."""

    def _get(data: dict[str, Any]) -> int | None:
        val = data.get("live", {}).get(key)
        return int(val) if val is not None else None

    return _get


def _aggregate_value(period: str, key: str) -> Callable[[dict[str, Any]], int | None]:
    """Create a value function for aggregate metrics."""

    def _get(data: dict[str, Any]) -> int | None:
        val = data.get("aggregate", {}).get(period, {}).get(key)
        return int(val) if val is not None else None

    return _get


# Per-site sensor descriptions
SITE_SENSORS: tuple[MatomoSensorEntityDescription, ...] = (
    # Unique visitors
    MatomoSensorEntityDescription(
        key="unique_visitors_today",
        translation_key="unique_visitors_today",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visitors",
        value_fn=_site_value("day", "nb_uniq_visitors"),
    ),
    MatomoSensorEntityDescription(
        key="unique_visitors_week",
        translation_key="unique_visitors_week",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visitors",
        value_fn=_site_value("week", "nb_uniq_visitors"),
    ),
    MatomoSensorEntityDescription(
        key="unique_visitors_month",
        translation_key="unique_visitors_month",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visitors",
        value_fn=_site_value("month", "nb_uniq_visitors"),
    ),
    # Page views
    MatomoSensorEntityDescription(
        key="pageviews_today",
        translation_key="pageviews_today",
        icon="mdi:file-document-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_site_value("day", "nb_pageviews"),
    ),
    MatomoSensorEntityDescription(
        key="pageviews_week",
        translation_key="pageviews_week",
        icon="mdi:file-document-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_site_value("week", "nb_pageviews"),
    ),
    MatomoSensorEntityDescription(
        key="pageviews_month",
        translation_key="pageviews_month",
        icon="mdi:file-document-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_site_value("month", "nb_pageviews"),
    ),
    # Visits (sessions)
    MatomoSensorEntityDescription(
        key="visits_today",
        translation_key="visits_today",
        icon="mdi:web",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_site_value("day", "nb_visits"),
    ),
    MatomoSensorEntityDescription(
        key="visits_week",
        translation_key="visits_week",
        icon="mdi:web",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_site_value("week", "nb_visits"),
    ),
    MatomoSensorEntityDescription(
        key="visits_month",
        translation_key="visits_month",
        icon="mdi:web",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_site_value("month", "nb_visits"),
    ),
    # Actions (hits)
    MatomoSensorEntityDescription(
        key="actions_today",
        translation_key="actions_today",
        icon="mdi:cursor-default-click",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_site_value("day", "nb_actions"),
    ),
    MatomoSensorEntityDescription(
        key="actions_week",
        translation_key="actions_week",
        icon="mdi:cursor-default-click",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_site_value("week", "nb_actions"),
    ),
    MatomoSensorEntityDescription(
        key="actions_month",
        translation_key="actions_month",
        icon="mdi:cursor-default-click",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_site_value("month", "nb_actions"),
    ),
    # Live visitors
    MatomoSensorEntityDescription(
        key="live_visitors",
        translation_key="live_visitors",
        icon="mdi:account-eye",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visitors",
        value_fn=_live_value("visitors"),
    ),
    MatomoSensorEntityDescription(
        key="live_visits",
        translation_key="live_visits",
        icon="mdi:account-eye",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_live_value("visits"),
    ),
    MatomoSensorEntityDescription(
        key="live_actions",
        translation_key="live_actions",
        icon="mdi:cursor-default-click-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_live_value("actions"),
    ),
)

# Aggregate sensor descriptions (all sites combined)
AGGREGATE_SENSORS: tuple[MatomoSensorEntityDescription, ...] = (
    MatomoSensorEntityDescription(
        key="all_sites_visits_today",
        translation_key="all_sites_visits_today",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_aggregate_value("day", "nb_visits"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_visits_week",
        translation_key="all_sites_visits_week",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_aggregate_value("week", "nb_visits"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_visits_month",
        translation_key="all_sites_visits_month",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="visits",
        value_fn=_aggregate_value("month", "nb_visits"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_pageviews_today",
        translation_key="all_sites_pageviews_today",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_aggregate_value("day", "nb_pageviews"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_pageviews_week",
        translation_key="all_sites_pageviews_week",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_aggregate_value("week", "nb_pageviews"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_pageviews_month",
        translation_key="all_sites_pageviews_month",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="views",
        value_fn=_aggregate_value("month", "nb_pageviews"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_actions_today",
        translation_key="all_sites_actions_today",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_aggregate_value("day", "nb_actions"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_actions_week",
        translation_key="all_sites_actions_week",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_aggregate_value("week", "nb_actions"),
        is_aggregate=True,
    ),
    MatomoSensorEntityDescription(
        key="all_sites_actions_month",
        translation_key="all_sites_actions_month",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="actions",
        value_fn=_aggregate_value("month", "nb_actions"),
        is_aggregate=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Matomo sensors from a config entry."""
    coordinator: MatomoDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    site_id = entry.data[CONF_SITE_ID]
    site_name = entry.data[CONF_SITE_NAME]
    include_aggregate = entry.data.get(CONF_INCLUDE_AGGREGATE, False)

    entities: list[MatomoSensor] = []

    # Per-site sensors
    for description in SITE_SENSORS:
        entities.append(
            MatomoSensor(
                coordinator=coordinator,
                description=description,
                site_id=site_id,
                site_name=site_name,
                entry_id=entry.entry_id,
            )
        )

    # Aggregate sensors
    if include_aggregate:
        for description in AGGREGATE_SENSORS:
            entities.append(
                MatomoSensor(
                    coordinator=coordinator,
                    description=description,
                    site_id=site_id,
                    site_name=site_name,
                    entry_id=entry.entry_id,
                )
            )

    async_add_entities(entities)


class MatomoSensor(CoordinatorEntity[MatomoDataCoordinator], SensorEntity):
    """Representation of a Matomo sensor."""

    entity_description: MatomoSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MatomoDataCoordinator,
        description: MatomoSensorEntityDescription,
        site_id: int,
        site_name: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        if description.is_aggregate:
            self._attr_unique_id = f"matomo_{entry_id}_{description.key}"
        else:
            self._attr_unique_id = f"matomo_{site_id}_{description.key}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry_id}")},
            "name": f"Matomo - {site_name}",
            "manufacturer": "Lukasz Kozik (lkozik@evilit.pl)",
            "model": "Matomo Analytics Integration",
            "entry_type": None,
        }

    @property
    def native_value(self) -> int | float | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)