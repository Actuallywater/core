"""Sensor from a redis get."""

from datetime import timedelta
import logging
from typing import Any

import redis

from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    MATCH_ALL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.template import Template
from homeassistant.helpers.trigger_template_entity import (
    CONF_AVAILABILITY,
    CONF_PICTURE,
    ManualTriggerSensorEntity,
    ValueTemplate,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_KEY_DATA_TYPE, CONF_KEY_NAME, CONF_REDIS_URL, DOMAIN
from .util import redact_credentials

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)

TRIGGER_ENTITY_OPTIONS = (
    CONF_AVAILABILITY,
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_PICTURE,
    CONF_UNIQUE_ID,
    CONF_STATE_CLASS,
    CONF_UNIT_OF_MEASUREMENT,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the redis sensor from yaml."""
    if (conf := discovery_info) is None:
        return

    name: Template = conf[CONF_NAME]
    value_template: ValueTemplate | None = conf.get(CONF_VALUE_TEMPLATE)
    key_name: str = conf[CONF_KEY_NAME]
    data_type: str = conf[CONF_KEY_DATA_TYPE]
    unique_id: str | None = conf.get(CONF_UNIQUE_ID)
    db_url: str = conf[CONF_REDIS_URL]

    trigger_entity_config = {CONF_NAME: name}
    for key in TRIGGER_ENTITY_OPTIONS:
        if key not in conf:
            continue
        trigger_entity_config[key] = conf[key]

    await async_setup_sensor(
        hass,
        trigger_entity_config,
        key_name,
        data_type,
        value_template,
        unique_id,
        db_url,
        True,
        async_add_entities,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the SQL sensor from config entry."""

    # db_url: str = resolve_db_url(hass, entry.options.get(CONF_DB_URL))
    db_url: str = CONF_REDIS_URL
    name: str = entry.options[CONF_NAME]

    template: str | None = entry.options.get(CONF_VALUE_TEMPLATE)
    key_name: str = entry.options[CONF_KEY_NAME]

    value_template: ValueTemplate | None = None
    if template is not None:
        try:
            value_template = ValueTemplate(template, hass)
            value_template.ensure_valid()
        except TemplateError:
            value_template = None

    name_template = Template(name, hass)
    trigger_entity_config = {CONF_NAME: name_template, CONF_UNIQUE_ID: entry.entry_id}
    for key in TRIGGER_ENTITY_OPTIONS:
        if key not in entry.options:
            continue
        trigger_entity_config[key] = entry.options[key]

    await async_setup_sensor(
        hass,
        trigger_entity_config,
        key_name,
        value_template,
        entry.entry_id,
        db_url,
        False,
        async_add_entities,
    )


'''
@callback
def _async_get_or_init_domain_data(hass: HomeAssistant) -> SQLData:
    """Get or initialize domain data."""
    if DOMAIN in hass.data:
        sql_data: SQLData = hass.data[DOMAIN]
        return sql_data

    session_makers_by_db_url: dict[str, scoped_session] = {}

    #
    # Ensure we dispose of all engines at shutdown
    # to avoid unclean disconnects
    #
    # Shutdown all sessions in the executor since they will
    # do blocking I/O
    #
    def _shutdown_db_engines(event: Event) -> None:
        """Shutdown all database engines."""
        for sessmaker in session_makers_by_db_url.values():
            sessmaker.connection().engine.dispose()

    cancel_shutdown = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, _shutdown_db_engines
    )

    sql_data = SQLData(cancel_shutdown, session_makers_by_db_url)
    hass.data[DOMAIN] = sql_data
    return sql_data
'''


async def async_setup_sensor(
    hass: HomeAssistant,
    trigger_entity_config: ConfigType,
    key_name: str,
    data_type: str,
    value_template: ValueTemplate | None,
    unique_id: str | None,
    db_url: str,
    yaml: bool,
    async_add_entities: AddEntitiesCallback | AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the redis sensor."""
    try:
        redis_conn = redis.from_url(db_url)
    except redis.exceptions.ConnectionError as error:
        _LOGGER.error(
            "Error getting key %s: %s",
            key_name,
            redact_credentials(str(error)),
        )
        return

    async_add_entities(
        [
            RedisSensor(
                trigger_entity_config,
                redis_conn,
                key_name,
                data_type,
                value_template,
                yaml,
            )
        ],
    )


'''
def _validate_and_get_session_maker_for_db_url(db_url: str) -> scoped_session | None:
    """Validate the db_url and return a session maker.

    This does I/O and should be run in the executor.
    """
    sess: Session | None = None
    try:
        engine = sqlalchemy.create_engine(db_url, future=True)
        sessmaker = scoped_session(sessionmaker(bind=engine, future=True))
        # Run a dummy query just to test the db_url
        sess = sessmaker()
        sess.execute(sqlalchemy.text("SELECT 1;"))

    except SQLAlchemyError as err:
        _LOGGER.error(
            "Couldn't connect using %s DB_URL: %s",
            redact_credentials(db_url),
            redact_credentials(str(err)),
        )
        return None
    else:
        return sessmaker
    finally:
        if sess:
            sess.close()
'''
'''
def _generate_lambda_stmt(query: str) -> StatementLambdaElement:
    """Generate the lambda statement."""
    text = sqlalchemy.text(query)
    return lambda_stmt(lambda: text, lambda_cache=_SQL_LAMBDA_CACHE)
'''


class RedisSensor(ManualTriggerSensorEntity):
    """Representation of an redis sensor."""

    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(
        self,
        trigger_entity_config: ConfigType,
        redis_conn: Any,
        key: str,
        data_type: str,
        value_template: ValueTemplate | None,
        yaml: bool,
    ) -> None:
        """Initialize the redis sensor."""
        super().__init__(self.hass, trigger_entity_config)
        self._template = value_template
        self._redis_conn = redis_conn
        self._key = key
        self._data_type = data_type
        self._attr_extra_state_attributes = {}
        self._attr_should_poll = True
        if not yaml and (unique_id := trigger_entity_config.get(CONF_UNIQUE_ID)):
            self._attr_name = None
            self._attr_has_entity_name = True
            self._attr_device_info = DeviceInfo(
                entry_type=DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, unique_id)},
                manufacturer="redis",
                name=self._rendered.get(CONF_NAME),
            )

    @property
    def name(self) -> str | None:
        """Name of the entity."""
        if self.has_entity_name:
            return self._attr_name
        return self._rendered.get(CONF_NAME)

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        await super().async_added_to_hass()
        await self.async_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        return dict(self._attr_extra_state_attributes)

    async def async_update(self) -> None:
        """Retrieve sensor data from the query using the right executor."""
        await self.hass.async_add_executor_job(self._update)

    def _update(self) -> None:
        """Retrieve sensor data from the cache."""
        data = None
        self._attr_extra_state_attributes = {}

        try:
            data = self._redis_conn.get(self._key)
        except redis.exceptions.ConnectionError as error:
            _LOGGER.error(
                "Error getting key %s: %s",
                self._key,
                redact_credentials(str(error)),
            )
            return

        if data is not None:
            _LOGGER.debug("key result is %s ", data)

            if self._data_type == "numeric":
                data = float(data)
            elif self._data_type == "string":
                data = str(data)
            elif self._data_type == "date":
                data = data.isoformat()
            elif self._data_type == "hex":
                data = f"0x{data.hex()}"

        if data is not None and isinstance(data, (bytes, bytearray)):
            data = f"0x{data.hex()}"

        if data is not None and self._template is not None:
            variables = self._template_variables_with_value(data)
            if self._render_availability_template(variables):
                self._attr_native_value = self._template.async_render_as_value_template(
                    self.entity_id, variables, None
                )
                self._process_manual_data(variables)
        else:
            self._attr_native_value = data

        if data is None:
            _LOGGER.warning("%s returned no results", data)

        self._redis_conn.close()
