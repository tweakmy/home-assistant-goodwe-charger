import aiohttp
import math
import asyncio

LOGIN_URL = "https://www.semsportal.com/api/v2/Common/CrossLogin"
CONTROL_URL = "https://www.semsportal.com/api/v2/EVCharge/Control"
SET_CURRENT_URL = "https://www.semsportal.com/api/v2/EVCharge/SetCurrent"

class SEMSClient:

    def __init__(self, session, username, password, station_id):
        self.session = session
        self.username = username
        self.password = password
        self.station_id = station_id
        self.token = None
        self._lock = asyncio.Lock()

    async def login(self):
        payload = {"account": self.username, "pwd": self.password}
        async with self.session.post(LOGIN_URL, json=payload) as r:
            data = await r.json()
        self.token = data["data"]["token"]

    async def _request(self, url, payload):
        async with self._lock:
            for attempt in range(3):  # retry up to 3 times
                headers = {"token": self.token}
                try:
                    async with self.session.post(url, json=payload, headers=headers) as r:
                        if r.status == 401:  # token expired
                            await self.login()
                            continue
                        r.raise_for_status()
                        return await r.json()
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(1)  # small delay before retry
                        continue
                    raise e

    async def start_charge(self):
        payload = {"powerStationId": self.station_id, "action": "start"}
        await self._request(CONTROL_URL, payload)

    async def stop_charge(self):
        payload = {"powerStationId": self.station_id, "action": "stop"}
        await self._request(CONTROL_URL, payload)

    async def set_current(self, amps):
        payload = {"powerStationId": self.station_id, "current": amps}
        await self._request(SET_CURRENT_URL, payload)

    async def set_power_limit(self, kw):
        voltage = 400  # 3-phase
        amps = int((kw * 1000) / (math.sqrt(3) * voltage))
        await self.set_current(amps)