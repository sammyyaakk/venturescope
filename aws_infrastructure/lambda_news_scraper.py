import json
import boto3
import urllib.request
import os
from datetime import datetime, timezone

# Sector keywords for classification
SECTOR_KEYWORDS = {
    "Technology": ["tech", "software", "ai", "artificial intelligence", 
                   "cloud", "cybersecurity", "semiconductor", "startup",
                   "machine learning", "deep learning", "saas", "api"],
    "Fintech": ["fintech", "payments", "banking", "crypto", "blockchain", 
                "lending", "insurtech", "neobank", "defi", "bitcoin",
                "investment", "fund", "capital", "ipo"],
    "Healthcare": ["health", "biotech", "pharma", "medical", "clinical", 
                   "drug", "hospital", "wellness", "medtech", "genomics"],
    "Consumer & Retail": ["retail", "ecommerce", "consumer", "fashion", 
                          "food", "beverage", "marketplace", "d2c", "brand"],
    "Education": ["edtech", "education", "learning", "university", 
                  "school", "training", "skills", "upskilling", "mooc"],
    "CleanTech": ["cleantech", "climate", "solar", "renewable", "energy", 
                  "sustainability", "ev", "battery", "carbon", "green"],
    "Media & Entertainment": ["media", "entertainment", "gaming", 
                               "streaming", "content", "music", "film",
                               "podcast", "creator", "metaverse"],
}

def classify_sector(text):
    """Classify headline into a sector based on keywords."""
    text_lower = text.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return sector
    return "Other"

def lambda_handler(event, context):
    
    # Get API key from environment variable
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        raise ValueError("NEWS_API_KEY environment variable not set")
    
    # NewsAPI query
    query = "startup+funding+venture+capital+investor+series"
    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={query}"
        f"&language=en"
        f"&pageSize=100"
        f"&sortBy=publishedAt"
        f"&apiKey={api_key}"
    )
    
    # Fetch news from NewsAPI
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        raise
    
    articles = data.get("articles", [])
    print(f"Fetched {len(articles)} articles from NewsAPI")
    
    # Current timestamp for this ingestion run
    ingestion_time = datetime.now(timezone.utc).isoformat()
    
    # Process articles
    headlines = []
    seen_titles = set()  # Track duplicates
    
    for article in articles:
        title = article.get("title", "").strip()
        
        # Skip empty titles, duplicates, and removed articles
        if not title or title in seen_titles or title == "[Removed]":
            continue
            
        seen_titles.add(title)
        description = article.get("description", "") or ""
        full_text = f"{title} {description}"
        
        headlines.append({
            "title": title,
            "description": description,
            "sector": classify_sector(full_text),
            "published_at": article.get("publishedAt", ""),
            "ingested_at": ingestion_time,  # NEW: timestamp of when WE fetched it
            "source": article.get("source", {}).get("name", ""),
            "url": article.get("url", "")
        })
    
    print(f"Processed {len(headlines)} unique headlines")
    
    # Save to S3
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('S3_BUCKET', 'YOUR-RAW-BUCKET')
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_key = f"news-headlines/headlines_{timestamp}.json"
    
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=json.dumps(headlines, indent=2),
            ContentType="application/json"
        )
        print(f"Saved to s3://{bucket_name}/{file_key}")
    except Exception as e:
        print(f"Error saving to S3: {str(e)}")
        raise
    
    # Trigger Glue Sentiment ETL job
    try:
        glue = boto3.client('glue', region_name='us-east-1')
        glue_response = glue.start_job_run(JobName='VentureScope-Sentiment-ETL')
        glue_run_id = glue_response['JobRunId']
        print(f"Glue job triggered. Run ID: {glue_run_id}")
    except Exception as e:
        print(f"Warning: Could not trigger Glue job: {str(e)}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Success",
            "headlines_saved": len(headlines),
            "s3_location": f"s3://{bucket_name}/{file_key}",
            "ingestion_time": ingestion_time
        })
    }