import sys
import json
import boto3
from datetime import datetime
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, current_timestamp, date_format
from pyspark.sql.types import FloatType, StringType, StructType, StructField
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

# List of target sectors derived from Crunchbase baseline data
SECTOR_KEYWORDS = {
    "software": ["software", "app", "saas", "code", "developer", "platform"],
    "biotech": ["biotech", "genomics", "crispr", "therapeutics", "bio"],
    "mobile": ["mobile", "ios", "android", "smartphone", "app"],
    "web": ["web", "internet", "website", "online"],
    "cleantech": ["cleantech", "solar", "wind", "climate", "sustainability", "green tech"],
    "ecommerce": ["ecommerce", "retail", "shop", "marketplace", "d2c"],
    "medical": ["medical", "healthcare", "healthtech", "hospital", "pharma"],
    "enterprise": ["enterprise", "b2b", "corporate", "cloud", "infrastructure"]
}

# UDF for sentiment scoring
def get_sentiment_score(text):
    if text:
        scores = analyzer.polarity_scores(text)
        return float(scores['compound'])
    return 0.0

def get_sentiment_label(score):
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

# UDF for sector extraction
def extract_sector(text):
    if not text:
        return "other"
    text_lower = text.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return sector
    return "other"

sentiment_score_udf = udf(get_sentiment_score, FloatType())
sentiment_label_udf = udf(get_sentiment_label, StringType())
sector_extraction_udf = udf(extract_sector, StringType())

# Read all JSON files from S3
input_path = "s3://YOUR-RAW-BUCKET-NAME/news-headlines/"
output_path = "s3://YOUR-PROCESSED-BUCKET-NAME/news-sentiment/"

df = spark.read.option("multiline", "true").json(input_path)

# Apply transformations
df = df.withColumn("sentiment_score", sentiment_score_udf(df["title"]))
df = df.withColumn("sentiment_label", sentiment_label_udf(df["sentiment_score"]))
df = df.withColumn("sector", sector_extraction_udf(df["title"]))
df = df.withColumn("ingested_at", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))

# Select only the specific structured columns
df = df.select("title", "sentiment_score", "sentiment_label", "sector", "ingested_at")

# Write output as parquet
df.write.mode("overwrite").parquet(output_path)

print(f"ETL complete. Processed {df.count()} headlines with sentiment and sector tags.")