import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Datos de conexión
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    # Método para obtener conexión
    @staticmethod
    def get_connection():
        return psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
