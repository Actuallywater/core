"""The redis integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    Platform,
)
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.trigger_template_entity import (
    CONF_AVAILABILITY,
    CONF_PICTURE,
    ValueTemplate,
)
from homeassistant.helpers.typing import ConfigType

from .const import CONF_KEY_DATA_TYPE, CONF_KEY_NAME, CONF_REDIS_URL, DOMAIN, PLATFORMS

# from .util import redact_credentials

_LOGGER = logging.getLogger(__name__)


QUERY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_KEY_NAME): cv.string,
        vol.Required(CONF_KEY_DATA_TYPE): cv.string,
        vol.Required(CONF_NAME): cv.template,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): vol.All(
            cv.template, ValueTemplate.from_template
        ),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_REDIS_URL): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
        vol.Optional(CONF_AVAILABILITY): cv.template,
        vol.Optional(CONF_ICON): cv.template,
        vol.Optional(CONF_PICTURE): cv.template,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): vol.All(cv.ensure_list, [QUERY_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up redis from yaml config."""
    if (conf := config.get(DOMAIN)) is None:
        return True

    for sensor_conf in conf:
        await discovery.async_load_platform(
            hass, Platform.SENSOR, DOMAIN, sensor_conf, config
        )
    """
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SCHEDULE,
        async_get_schedule,
        schema=CONFIG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up redis from a config entry."""
    """
    _LOGGER.debug(
        "redis url %s ",
        redact_credentials(entry.options.get(CONF_REDIS_URL)),
    )
    """
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload redis config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
