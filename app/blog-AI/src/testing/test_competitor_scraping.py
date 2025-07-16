#!/usr/bin/env python3
"""
Test script for competitor URL scraping functionality.
This script tests the competitor keyword extraction without requiring database access.
"""

import sys
import os
import json
import requests
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-3.5-turbo"
SCRAPER_API_URL = "http://157.245.210.116:3000/api/scrape"

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


def generate_text_with_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Generate text using OpenAI API"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates high-quality content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


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
            print(f"📊 Response keys: {list(data.keys())}")
            
            # Show some basic info about the scraped content
            if "title" in data:
                print(f"📝 Title: {data['title'][:100]}...")
            if "content" in data:
                print(f"📄 Content length: {len(data['content'])} characters")
            elif "text" in data:
                print(f"📄 Text length: {len(data['text'])} characters")
            
            return data
        else:
            print(f"❌ Failed to scrape {url}. Status: {response.status_code}")
            print(f"Response: {response.text}")
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
            print(f"📏 Content truncated to {max_content_length} characters")
        
        if not content.strip():
            print("⚠️ No content found in scraped data")
            return []
        
        print(f"🔍 Extracting keywords from content ({len(content)} characters)...")
        
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
                print(f"Response: {response[:200]}...")
                return []
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Could not parse JSON response: {str(e)}")
            print(f"Response: {response[:200]}...")
            return []
        
    except Exception as e:
        print(f"❌ Error extracting keywords from scraped content: {str(e)}")
        return []


def test_competitor_scraping():
    """Test the competitor scraping functionality"""
    print("🧪 Testing competitor URL scraping functionality\n")
    
    # Test URLs - you can replace these with actual competitor URLs
    test_urls = [
        "https://blog.example.com/test-post",  # Replace with actual competitor URL
        # Add more test URLs as needed
    ]
    
    # Ask user for test URL
    print("Please enter a competitor URL to test (or press Enter to use default):")
    user_url = input("URL: ").strip()
    
    if user_url:
        test_urls = [user_url]
    else:
        print("ℹ️ Using default test URLs (may not work)")
    
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing URL: {url}")
        print(f"{'='*50}")
        
        # Test scraping
        scraped_data = scrape_competitor_url(url)
        
        if scraped_data:
            print(f"\n📊 Scraped data structure:")
            for key, value in scraped_data.items():
                if isinstance(value, str):
                    print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
                else:
                    print(f"  {key}: {type(value).__name__}")
            
            # Test keyword extraction
            print(f"\n🔑 Extracting keywords...")
            keywords = extract_keywords_from_scraped_content(scraped_data)
            
            if keywords:
                print(f"\n✅ Extracted Keywords ({len(keywords)}):")
                for i, keyword in enumerate(keywords, 1):
                    print(f"  {i:2d}. {keyword}")
            else:
                print("❌ No keywords extracted")
        else:
            print("❌ Failed to scrape URL")
    
    print(f"\n🎉 Test completed!")


def test_api_connectivity():
    """Test API connectivity"""
    print("🔌 Testing API connectivity...\n")
    
    # Test OpenAI API
    if OPENAI_API_KEY:
        try:
            response = generate_text_with_openai("Say hello")
            print(f"✅ OpenAI API: Connected")
        except Exception as e:
            print(f"❌ OpenAI API: Error - {str(e)}")
    else:
        print("❌ OpenAI API: No API key found")
    
    # Test Scraper API
    try:
        response = requests.get(SCRAPER_API_URL.replace('/api/scrape', '/'), timeout=10)
        if response.status_code == 200:
            print(f"✅ Scraper API: Connected")
        else:
            print(f"⚠️ Scraper API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Scraper API: Error - {str(e)}")


if __name__ == "__main__":
    print("🚀 Competitor URL Scraping Test\n")
    
    # Test API connectivity first
    test_api_connectivity()
    
    print("\n" + "="*50)
    
    # Test competitor scraping
    test_competitor_scraping()
