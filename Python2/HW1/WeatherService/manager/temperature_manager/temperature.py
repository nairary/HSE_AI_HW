import aiohttp
from multiprocessing import Pool

async def get_current_temperature_async(town: str, api_key: str):
    api_url = f"http://api.openweathermap.org/data/2.5/weather?q={town}&units=metric&appid={api_key}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status != 200:
                    error_message = await response.json()
                    return None, error_message.get("message", "Unknown error")
                data = await response.json()
                current_temperature = data['main']['temp']
                return current_temperature, None
        except aiohttp.ClientError as e:
            return None, str(e)