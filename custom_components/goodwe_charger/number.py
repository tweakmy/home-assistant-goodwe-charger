from homeassistant.components.number import NumberEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    client = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GoodweChargerPowerLimit(client)])

class GoodweChargerPowerLimit(NumberEntity):

    def __init__(self, client):
        self.client = client
        self._value = 11

    @property
    def name(self):
        return "GoodWe Charger Power Limit"

    @property
    def native_unit_of_measurement(self):
        return "kW"

    @property
    def min_value(self):
        return 4

    @property
    def max_value(self):
        return 22

    @property
    def step(self):
        return 1

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value):
        await self.client.set_power_limit(value)
        self._value = value