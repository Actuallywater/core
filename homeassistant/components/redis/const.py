"""Constants for the redis integration."""

import re

from homeassistant.const import Platform

DOMAIN = "redis"
PLATFORMS = [Platform.SENSOR]

# CONF_REDIS_URL = "redis://192.168.1.26:6379/0"
CONF_REDIS_URL = "redis_url"
CONF_KEY_NAME = "key"
CONF_KEY_DATA_TYPE = "data_type"

DB_URL_RE = re.compile("//.*:.*@")
