import aiohttp
import math
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = "https://www.semsportal.com/api/v2/Common/CrossLogin"
CONTROL_URL = "https://www.semsportal.com/api/v2/EVCharge/Control"
SET_CURRENT_URL = "https://www.semsportal.com/api/v2/EVCharge/SetCurrent"

class SEMSClient:

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str, station_id: str):
        self.session = session
        self.username = username
        self.password = password
        self.station_id = station_id
        self.token = None
        self._lock = asyncio.Lock()

    async def login(self):
        """Log in to SEMS and get token."""
        payload = {"account": self.username, "pwd": self.password}
        try:
            async with self.session.post(LOGIN_URL, json=payload) as r:
                try:
                    data = await r.json()
                except Exception:
                    text = await r.text()
                    _LOGGER.error("SEMS login failed, response not JSON: %s", text)
                    raise Exception("SEMS login failed: response not JSON")

            if "data" not in data or "token" not in data["data"]:
                _LOGGER.error("SEMS login failed, server response: %s", data)
                raise Exception("SEMS login failed, check username/password/station_id")

            self.token = data["data"]["token"]
            _LOGGER.debug("SEMS login successful, token obtained")

        except Exception as e:
            _LOGGER.error("SEMS login exception: %s", e)
            raise

    async def _request(self, url, payload):
        """Internal helper to send API requests with retries and token refresh."""
        async with self._lock:
            for attempt in range(3):
                if not self.token:
                    await self.login()
                headers = {"token": self.token}
                try:
                    async with self.session.post(url, json=payload, headers=headers) as r:
                        if r.status == 401:  # token expired
                            _LOGGER.info("SEMS token expired, re-login")
                            await self.login()
                            continue
                        r.raise_for_status()
                        return await r.json()
                except Exception as e:
                    _LOGGER.warning("SEMS request attempt %d failed: %s", attempt + 1, e)
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    raise

    async def start_charge(self):
        payload = {"powerStationId": self.station_id, "action": "start"}
        await self._request(CONTROL_URL, payload)

    async def stop_charge(self):
        payload = {"powerStationId": self.station_id, "action": "stop"}
        await self._request(CONTROL_URL, payload)

    async def set_current(self, amps: int):
        payload = {"powerStationId": self.station_id, "current": amps}
        await self._request(SET_CURRENT_URL, payload)

    async def set_power_limit(self, kw: float):
        """Convert kW to current for 3-phase 400V and set it."""
        voltage = 400
        amps = int((kw * 1000) / (math.sqrt(3) * voltage))
        _LOGGER.debug("Setting power %.1f kW -> current %d A", kw, amps)
        await self.set_current(amps)
