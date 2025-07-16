#!/usr/bin/env python3
"""
Competitor URL scraping and keyword extraction functionality.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.append(project_root)

from ..seo.semantic_keywords import generate_text_with_openai
from app.models import ContentJob

# Configuration
SCRAPER_API_URL = "http://157.245.210.116:3000/api/scrape"


def scrape_competitor_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape competitor URL using the external API to extract content.
    
    Args:
        url: The competitor URL to scrape
        
    Returns:
        Dictionary containing scraped content or None if failed
    """
    try:
        print(f"🔍 Scraping competitor URL: {url}")
        
        # Make request to the scraper API
        response = requests.post(
            SCRAPER_API_URL,
            json={"url": url},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully scraped {url}")
            return data
        else:
            print(f"❌ Failed to scrape {url}. Status: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error scraping {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
        return None


def extract_keywords_from_scraped_content(scraped_data: Dict[str, Any]) -> List[str]:
    """
    Extract keywords from scraped competitor content using AI.
    
    Args:
        scraped_data: Dictionary containing scraped content
        
    Returns:
        List of extracted keywords
    """
    try:
        # Extract text content from scraped data
        content = ""
        if "content" in scraped_data:
            content = scraped_data["content"]
        elif "text" in scraped_data:
            content = scraped_data["text"]
        elif "body" in scraped_data:
            content = scraped_data["body"]
        
        # Get title if available
        title = scraped_data.get("title", "")
        
        # Limit content length to avoid token limits
        max_content_length = 3000  # Adjust based on your needs
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        if not content.strip():
            print("⚠️ No content found in scraped data")
            return []
        
        # Create prompt for keyword extraction
        prompt = f"""
Analyze the following blog content and extract relevant keywords that could be useful for SEO:

Title: {title}

Content:
{content}

Please extract keywords that are:
1. Relevant to the main topic
2. Commonly searched terms
3. Include both short and long-tail keywords
4. Focus on semantic variations and related terms

Return only a JSON array of keywords, like:
["keyword1", "keyword2", "long tail keyword phrase", ...]

Aim for 20-40 high-quality keywords.
"""
        
        # Generate keywords using OpenAI
        response = generate_text_with_openai(prompt)
        
        # Parse the response
        try:
            # Try to find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                keywords = json.loads(json_str)
                
                # Validate and clean keywords
                if isinstance(keywords, list):
                    # Filter out empty strings and duplicates
                    cleaned_keywords = list(set([kw.strip() for kw in keywords if kw.strip()]))
                    print(f"✅ Extracted {len(cleaned_keywords)} keywords from competitor content")
                    return cleaned_keywords
                else:
                    print("⚠️ Response is not a list")
                    return []
            else:
                print("⚠️ No JSON array found in response")
                return []
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Could not parse JSON response: {str(e)}")
            return []
        
    except Exception as e:
        print(f"❌ Error extracting keywords from scraped content: {str(e)}")
        return []


def scrape_competitor_keywords(job: ContentJob) -> List[str]:
    """
    Scrape competitor URLs and extract keywords for a content job.
    
    Args:
        job: The content job containing competitor URLs
        
    Returns:
        List of extracted keywords from all competitor URLs
    """
    all_keywords = []
    
    # Check both competitor URL fields
    competitor_urls = []
    if job.competitor_url_1:
        competitor_urls.append(job.competitor_url_1)
    if job.competitor_url_2:
        competitor_urls.append(job.competitor_url_2)
    
    if not competitor_urls:
        print(f"ℹ️ No competitor URLs found for job {job.id}")
        return []
    
    print(f"🔍 Found {len(competitor_urls)} competitor URLs to scrape for job {job.id}")
    
    for url in competitor_urls:
        # Scrape the URL
        scraped_data = scrape_competitor_url(url)
        
        if scraped_data:
            # Extract keywords from scraped content
            keywords = extract_keywords_from_scraped_content(scraped_data)
            all_keywords.extend(keywords)
        else:
            print(f"⚠️ Skipping keyword extraction for failed URL: {url}")
    
    # Remove duplicates and return
    unique_keywords = list(set(all_keywords))
    print(f"✅ Total unique keywords extracted from competitors: {len(unique_keywords)}")
    
    return unique_keywords
