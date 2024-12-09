import logging
import azure.functions as func
from pymongo import MongoClient
import requests
import json
import time
import os
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

# Configuración de OpenWeather API
API_KEY = os.getenv("API_KEY")
CITY = os.getenv("CITY")
WEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# Configuración de Cosmos DB
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CONNECTION = os.getenv("COSMOSDB_CONNECTION_STRING")

# Función para insertar datos en Cosmos DB
def insert_weather_data(client, data):
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    document_id = collection.insert_one(data).inserted_id
    logging.info(f"Documento insertado con _id: {document_id}")

# Función para obtener datos meteorológicos
def get_weather_data():
    try:
        response = requests.get(WEATHER_URL)
        if response.status_code == 200:
            weather_data = response.json()
            # Formatear los datos
            formatted_data = {
                "city": weather_data["name"],
                "temperature": weather_data["main"]["temp"],
                "weather": weather_data["weather"][0]["description"],
                "humidity": weather_data["main"]["humidity"],
                "pressure": weather_data["main"]["pressure"],
                "wind_speed": weather_data["wind"]["speed"],
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            return formatted_data
        else:
            logging.error(f"Error al obtener los datos: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error al conectar con la API: {e}")
        return None

app = func.FunctionApp()

@app.timer_trigger(schedule="*/1 * * * * *", arg_name="myTimer", run_on_startup=False,
                use_monitor=False) 
def timer_weather_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ejecutando la obtención de datos del clima.')

    client = MongoClient(CONNECTION)
    weather_data = get_weather_data()
    if weather_data:
        logging.info("Datos obtenidos del clima:")
        logging.info(weather_data)
        insert_weather_data(client, weather_data)
        logging.info("Datos insertados exitosamente en Cosmos DB")
    else:
        logging.error("No se pudieron obtener los datos del clima.")
