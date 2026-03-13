from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    client = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GoodweSwitch(client)])

class GoodweSwitch(SwitchEntity):

    def __init__(self, client):
        self.client = client
        self._is_on = False

    @property
    def name(self):
        return "GoodWe Charger"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        await self.client.start_charge()
        self._is_on = True

    async def async_turn_off(self):
        await self.client.stop_charge()
        self._is_on = False