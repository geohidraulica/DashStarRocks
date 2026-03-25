import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Cargar variables de entorno
dotenv_path = r"secrets.env"
load_dotenv(dotenv_path)

def get_engine():
    """
    Crea un engine SQLAlchemy para conectarse a StarRocks/MySQL.
    """
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")

    # Conector MySQL + SQLAlchemy
    conn_str = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    
    # SOLO AGREGAR ESTOS PARÁMETROS:
    engine = create_engine(
        conn_str, 
        echo=False,
        connect_args={
            'connect_timeout': 10,      # Timeout de 10 segundos
            'use_pure': True            # Usar implementación pura de Python
        }
    )
    return engine