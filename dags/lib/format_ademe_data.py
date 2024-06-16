import os, tarfile
from urllib3.response import HTTPResponse

from pyspark.sql.session import SparkSession
from pyspark.context import SparkContext
from pyspark.sql.functions import explode, col

from minio import Minio

HOME = os.path.expanduser('~')
AIRFLOW_ROOT_FOLDER = HOME + "/airflow"

MINIO_ACCESS_KEY = "9XdCihYxLXyakPKwKocC"
MINIO_SECRET_KEY = "T06fdHyWIUa517m8uRwNKGgNmy9HbA6yjjmL2Fca"

def format_carbon_data():
    client = Minio(
    "127.0.0.1:9000",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
    )

    bucket_name = "mydatalake"

    csv: str = None
    response: HTTPResponse = HTTPResponse()

    try:
        response = client.get_object(bucket_name, "data/raw/ademe/ademe_data.csv")
        csv = response.data.decode().replace("\r", "")
    finally:
        response.close()
        response.release_conn()

    sc = SparkContext('local')
    spark = SparkSession(sc).builder.getOrCreate()

    rdd = sc.parallelize([csv])
    rdd_lines = rdd.flatMap(lambda x: x.split("\n"))
    df = spark.read.option("header", True).csv(rdd_lines)

    file_location = "data/formatted/ademe/ademe_data.parquet"
    local_path = f"{AIRFLOW_ROOT_FOLDER}/{file_location}"
    df.write.mode("overwrite").parquet(local_path)

    # Saving parquet archive file to distributed filesytem (S3-like)
    archive_path = f"{local_path}.tgz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(local_path)

    client.fput_object(bucket_name, file_location, archive_path)