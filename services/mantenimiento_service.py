import pandas as pd
from database.connection import get_engine  # Engine SQLAlchemy
from repositories.mantenimiento_repository import QUERY_FACT_MANTENIMIENTO

def get_fact_mantenimiento():
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(QUERY_FACT_MANTENIMIENTO, conn)
    return df 