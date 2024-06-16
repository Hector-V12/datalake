import os
from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.sql.functions import col, to_utc_timestamp, date_format

HOME = os.path.expanduser('~')
AIRFLOW_ROOT_FOLDER = os.path.join(HOME, "airflow")

def index_data_to_elasticsearch():
    # Initialize Spark session with Elasticsearch configurations
    conf = SparkConf() \
        .setAppName("IndexParquetToElasticsearch") \
        .set("spark.jars.packages", "org.elasticsearch:elasticsearch-spark-30_2.12:8.14.1") \
        .set("spark.es.nodes", "127.0.0.1") \
        .set("spark.es.port", "9200") \
        .set("spark.es.net.ssl", "false") \
        .set("spark.es.net.http.auth.user", "elastic") \
        .set("spark.es.net.http.auth.pass", "password") \
        .set("spark.es.nodes.wan.only", "true")

    spark = SparkSession.builder.config(conf=conf).getOrCreate()
    
    # Set log level to ERROR to reduce verbosity
    spark.sparkContext.setLogLevel("ERROR")
    
    file_location = "data/usage/usage_data.parquet"
    local_path = os.path.join(AIRFLOW_ROOT_FOLDER, file_location)

    # Log the path to ensure it's correct
    print(f"Reading Parquet file from: {local_path}")

    # Read the Parquet file into a DataFrame
    df = spark.read.parquet(local_path)

    # Ensure the date column is correctly formatted to strict_date_optional_time
    df = df.withColumn("date", to_utc_timestamp(col("date"), "UTC"))

    # Log the schema of the DataFrame to verify it's correctly read
    df.printSchema()

    # Format the date column to the strict_date_optional_time format
    df = df.withColumn("date", date_format(col("date"), "yyyy-MM-dd'T'HH:mm:ss.SSSZ"))

    # Show a sample of the data
    df.show(5)

    # Write the DataFrame to Elasticsearch
    df.write \
        .format("org.elasticsearch.spark.sql") \
        .option("es.resource", "datalake_index/_doc") \
        .option("es.nodes", "127.0.0.1") \
        .option("es.port", "9200") \
        .mode("overwrite") \
        .save()

# Ensure that the function is called only if this script is run directly
if __name__ == "__main__":
    index_data_to_elasticsearch()
