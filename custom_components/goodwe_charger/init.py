from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_STATION_ID
from .sems import SEMSClient

async def async_setup_entry(hass, entry):

    session = async_get_clientsession(hass)

    client = SEMSClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_STATION_ID],
    )

    await client.login()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    # Forward platforms
    for platform in ["switch", "number"]:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True