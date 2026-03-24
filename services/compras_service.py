import pandas as pd
from database.connection import get_engine  # Engine SQLAlchemy
from repositories.compras_repository import QUERY_FACT_COMPRAS

def get_fact_compras():
    """
    Retorna un DataFrame con los datos de fact_compras
    """
    engine = get_engine()

    # Leer SQL de forma segura
    with engine.connect() as conn:
        df = pd.read_sql(QUERY_FACT_COMPRAS, conn)

    return df  # Solo devuelve el DataFrame, como antes