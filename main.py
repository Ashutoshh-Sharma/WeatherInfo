import asyncio
import websockets
import requests
import json
from datetime import datetime, timezone

API_KEY = '9d82f5e18842ac3f6d1c4ba6acdf1ecd'
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'

# Store history
weather_history = {}
HISTORY_LIMIT = 20  # max entries

async def get_weather(city):
    try:
        response = requests.get(WEATHER_URL, params={'q': city, 'appid': API_KEY, 'units': 'metric'})
        response.raise_for_status()
        data = response.json()
        weather_data = {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'forecast': data['weather'][0]['description'],
            'city': city,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        # Save to history
        history = weather_history.setdefault(city.lower(), [])
        history.append(weather_data)
        if len(history) > HISTORY_LIMIT:
            history.pop(0)  
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return {'error': 'Failed to fetch data'}

async def weather_handler(websocket, path):
    city = 'jaipur'  # default city
    await websocket.send(json.dumps(await get_weather(city)))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if 'city' in data:
                    city = data['city']
                    weather_data = await get_weather(city)
                    await websocket.send(json.dumps(weather_data))

                elif 'download_past_data' in data and data['download_past_data'] == True:
                    # Send the past data for the current city
                    past_data = weather_history.get(city.lower(), [])
                    await websocket.send(json.dumps({'past_data': past_data}))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({'error': 'Invalid JSON'}))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    server = await websockets.serve(weather_handler, '127.0.0.1', 9000)
    print("WebSocket server running at ws://127.0.0.1:9000")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Server error: {e}")
