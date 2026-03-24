import requests
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

dotenv_path = r"secrets.env"
load_dotenv(dotenv_path)

AIRFLOW_URL = os.getenv("AIRFLOW_URL")
USER = os.getenv("AIR_USER")
PASS = os.getenv("AIR_PASS")

def ejecutar_dag(dag_id):
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns"

    response = requests.post(
        url,
        auth=(USER, PASS),
        json={}
    )

    if response.status_code not in [200, 201]:
        raise Exception(f"Error ejecutando DAG: {response.text}")

    return response.json()["dag_run_id"]

def estado_dag(dag_id, dag_run_id):
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"

    response = requests.get(
        url,
        auth=(USER, PASS)
    )

    return response.json()["state"]


def ultima_ejecucion_exitosa(dag_id):
    """
    Devuelve la fecha de la última ejecución exitosa de un DAG en formato
    '%Y-%m-%d %H:%M:%S' en hora de Perú, o None si no hay ejecuciones.
    """
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns?state=success&order_by=-end_date&limit=1"
    try:
        response = requests.get(url, auth=(USER, PASS), timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error consultando última ejecución: {e}")
        return None

    if not data.get("dag_runs"):
        return None

    run = data["dag_runs"][0]
    fecha_utc = run.get("end_date")
    if not fecha_utc:
        return None

    # Parsear fecha UTC correctamente (con Z o microsegundos)
    try:
        dt_utc = datetime.fromisoformat(fecha_utc.replace("Z", "+00:00"))
    except ValueError:
        # fallback si hay microsegundos u otro formato raro
        dt_utc = datetime.strptime(fecha_utc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)

    # Convertir a hora Perú
    peru_tz = pytz.timezone("America/Lima")
    dt_peru = dt_utc.astimezone(peru_tz)
    return dt_peru.strftime("%Y-%m-%d %H:%M:%S")