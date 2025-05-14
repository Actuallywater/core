import logging

from .const import DB_URL_RE

_LOGGER = logging.getLogger(__name__)


def redact_credentials(data: str | None) -> str:
    """Redact credentials from string data."""
    if not data:
        return "none"
    return DB_URL_RE.sub("//****:****@", data)
