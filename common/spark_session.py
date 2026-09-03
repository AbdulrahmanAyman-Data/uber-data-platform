from pyspark.sql import SparkSession


def get_spark_session(app_name: str) -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("spark://uber-spark-master:7077")
        .config("spark.hadoop.fs.defaultFS", "hdfs://uber-hadoop-master:9000")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.executor.memory", "2g")
        .config("spark.driver.memory", "1500m")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark