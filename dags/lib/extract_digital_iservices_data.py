import urllib.parse
import requests, urllib, json, os
from datetime import datetime
from base64 import b64encode
from pathlib import Path

from minio import Minio

HOME = os.path.expanduser('~')
AIRFLOW_ROOT_FOLDER = HOME + "/airflow"

RTE_CLIENT_ID = "c4d455fd-c0df-4dc3-9d1f-60a9588c730c"
RTE_SECRET_ID = "43afbad5-df81-4c40-a704-c150ab4eb60b"

MINIO_ACCESS_KEY = "9XdCihYxLXyakPKwKocC"
MINIO_SECRET_KEY = "T06fdHyWIUa517m8uRwNKGgNmy9HbA6yjjmL2Fca"

def get_current_date() : 
  # Get date in format YYYY-MM-DDThh:mm:sszzzzzz
  time = datetime.now()
  return f'{time.strftime("%Y-%m-%dT%H:%M:%S%z")}+02:00'
    
def get_token():
  url = "https://digital.iservices.rte-france.com/token/oauth/"
  req = requests.get(url, headers={"Authorization": f"Basic {b64encode(f'{RTE_CLIENT_ID}:{RTE_SECRET_ID}'.encode()).decode()}", "Content-Type": "application/x-www-form-urlencoded"})
  return req.json().get("access_token")

def get_actual_generation(token, start_date, end_date):
  url = f"https://digital.iservices.rte-france.com/open_api/actual_generation/v1/actual_generations_per_production_type?start_date={start_date}&end_date={end_date}"
  req = requests.get(url, headers={"Authorization": f"Bearer {token}"})
  return req.json()

def save_json(json_string, folder_name, file_name):
  file_path = f"{AIRFLOW_ROOT_FOLDER}/data/raw/{folder_name}/{file_name}"
  Path(f"{AIRFLOW_ROOT_FOLDER}/data/raw/{folder_name}").mkdir(parents=True, exist_ok=True)
  with open(file_path, "w") as f:
    f.write(json.dumps(json_string))
  print("Json saved")
  return file_path

def extract_consumption_data():
  token = get_token()
  actual = get_actual_generation(token, start_date="2024-06-01T00:00:00+02:00", end_date=get_current_date())
  local_path = save_json(actual, "digital_iservices", "digital_iservices_data.json")

  # Saving json file to distributed filesytem (S3-like)
  client = Minio(
    "127.0.0.1:9000",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
  )

  bucket_name = "mydatalake"
  destination_path = "data/raw/digital_iservices/digital_iservices_data.json"

  client.fput_object(bucket_name, destination_path, local_path)