from readline import redisplay
import os, tarfile
from urllib3.response import HTTPResponse

from pyspark.sql.session import SparkSession
from pyspark.context import SparkContext
from pyspark.sql.functions import col

from minio import Minio

HOME = os.path.expanduser('~')
AIRFLOW_ROOT_FOLDER = HOME + "/airflow"

MINIO_ACCESS_KEY = "9XdCihYxLXyakPKwKocC"
MINIO_SECRET_KEY = "T06fdHyWIUa517m8uRwNKGgNmy9HbA6yjjmL2Fca"

client = Minio(
    "127.0.0.1:9000",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
  )

def download_parquet(bucket_name, df_path):
  df_local_path = f"{AIRFLOW_ROOT_FOLDER}/{df_path}"
  inside_tar_path = df_local_path[1:]
  df_local_archive_path = f"{AIRFLOW_ROOT_FOLDER}/{df_path}.tgz"

  # Downloading archive and extracting it
  client.fget_object(bucket_name, df_path, df_local_archive_path)
  with tarfile.open(df_local_archive_path, "r:gz") as tar:
      members = [member for member in tar.getmembers() if member.name.startswith(inside_tar_path)]
      for member in members:
          member.name = os.path.relpath(member.name, inside_tar_path)
          tar.extract(member, path=df_local_path)
  return df_local_path

def combine_data():
  bucket_name = "mydatalake"

  consumption_df_path = "data/formatted/digital_iservices/digital_iservices_data.parquet"
  consumption_df_local_path = download_parquet(bucket_name, consumption_df_path)

  carbon_df_path = "data/formatted/ademe/ademe_data.parquet"
  carbon_df_local_path = download_parquet(bucket_name, carbon_df_path)

  sc = SparkContext('local')
  spark = SparkSession(sc).builder.getOrCreate()

  df_consumption = spark.read.parquet(consumption_df_local_path)
  df_carbon = spark.read.parquet(carbon_df_local_path)
  df_joined = df_consumption.join(df_carbon, on="production_type", how="inner")
  

    # Converting kgCO2e/kWh to kgCO2e/MWh
  df_joined = df_joined.withColumn("carbon_emission", col("carbon_emission") * 1000)

  # Computing global emissions
  df_joined = df_joined.withColumn("emissions_total", col("value") * col("carbon_emission"))

  df_joined.show()
  
  file_location = "data/usage/usage_data.parquet"
  local_path = f"{AIRFLOW_ROOT_FOLDER}/{file_location}"
  df_joined.write.mode("overwrite").parquet(local_path)

  archive_path = f"{local_path}.tgz"
  with tarfile.open(archive_path, "w:gz") as tar:
      tar.add(local_path)

  client.fput_object(bucket_name, file_location, archive_path)
  
if __name__ == "__main__":
    combine_data()