#!/usr/bin/env python3
"""
Simple test script for competitor scraping functionality.
This script tests the competitor keyword extraction logic without database dependencies.
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import openai
import requests

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


def mock_scrape_competitor_url(url: str) -> Dict[str, Any]:
    """
    Mock competitor URL scraping for testing purposes.
    Returns sample scraped data without making actual API calls.
    """
    print(f"🔍 [MOCK] Scraping competitor URL: {url}")
    
    # Return mock data based on URL
    if "cricket" in url.lower():
        return {
            "title": "Complete Guide to Cricket Strategies and Techniques",
            "content": """
            Cricket is one of the most popular sports worldwide, with millions of fans following 
            international matches and tournaments. This comprehensive guide covers batting techniques, 
            bowling strategies, fielding positions, and match tactics used by professional players.
            
            Key topics include:
            - Batting fundamentals and advanced techniques
            - Bowling variations and strategies
            - Fielding positions and team coordination
            - Match analysis and statistical insights
            - Training routines for different skill levels
            - Equipment selection and maintenance
            
            Whether you're a beginner learning the basics or an advanced player looking to improve 
            your game, this guide provides valuable insights into cricket strategy and technique.
            """,
            "url": url,
            "status": "success"
        }
    elif "seo" in url.lower():
        return {
            "title": "Advanced SEO Strategies for Modern Websites",
            "content": """
            Search Engine Optimization (SEO) has evolved significantly with changing algorithms 
            and user behavior. This article covers modern SEO techniques, keyword research, 
            content optimization, and technical SEO best practices.
            
            Essential SEO elements include:
            - Keyword research and semantic analysis
            - On-page optimization techniques
            - Technical SEO fundamentals
            - Content strategy and creation
            - Link building and authority development
            - Local SEO optimization
            - Mobile and voice search optimization
            
            Implementing these strategies will help improve your website's visibility and 
            organic search rankings in today's competitive digital landscape.
            """,
            "url": url,
            "status": "success"
        }
    else:
        return {
            "title": "Sample Blog Post Title",
            "content": """
            This is a sample blog post content that demonstrates the competitor scraping 
            functionality. The content includes various keywords and phrases that would 
            typically be found in a competitor's blog post.
            
            Key points covered:
            - Industry insights and trends
            - Best practices and methodologies
            - Tips and recommendations
            - Case studies and examples
            - Future outlook and predictions
            
            This mock content helps test the keyword extraction process without requiring 
            actual competitor URLs or API calls.
            """,
            "url": url,
            "status": "success"
        }


def extract_keywords_from_scraped_content(scraped_data: Dict[str, Any]) -> List[str]:
    """
    Extract keywords from scraped competitor content using AI.
    """
    try:
        # Extract text content from scraped data
        content = scraped_data.get("content", "")
        title = scraped_data.get("title", "")
        
        # Limit content length to avoid token limits
        max_content_length = 3000
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


def generate_enhanced_semantic_keywords(
    main_keyword: str,
    title: str,
    related_keywords: List[str],
    competitor_keywords: List[str],
    target_count: int = 200
) -> Dict[str, Any]:
    """
    Generate enhanced semantic keywords including competitor insights.
    """
    try:
        related_keywords_str = ", ".join(related_keywords) if related_keywords else "None provided"
        
        # Add competitor keywords to the context
        competitor_context = ""
        if competitor_keywords and len(competitor_keywords) > 0:
            competitor_context = f"""
Competitor Keywords (extracted from competitor analysis):
{", ".join(competitor_keywords[:50])}

Please incorporate relevant competitor keywords into your semantic keyword generation, but focus on the main topic and avoid keyword stuffing.
"""
        
        # Create prompt for semantic keyword generation
        prompt = f"""
Generate {target_count} semantic keywords for SEO optimization based on the following information:

Main Keyword: {main_keyword}
Related Keywords: {related_keywords_str}
Title: {title}

{competitor_context}

Please generate a comprehensive list of semantic keywords that includes:
1. Primary keywords (variations of the main keyword)
2. Secondary keywords (closely related terms)
3. Long-tail keywords (specific phrases and questions)
4. Related keywords (contextually relevant terms)

Requirements:
- Focus on semantic relevance and search intent
- Include variations, synonyms, and related terms
- Consider different search intents (informational, transactional, navigational)
- Include question-based keywords
- Ensure keywords are relevant to the topic and title
- Incorporate insights from competitor analysis where relevant

Format the response as a JSON object with the following structure:
{{
    "primary_keywords": ["keyword1", "keyword2", ...],
    "secondary_keywords": ["keyword1", "keyword2", ...],
    "long_tail_keywords": ["long phrase 1", "long phrase 2", ...],
    "related_keywords": ["related term 1", "related term 2", ...],
    "competitor_inspired_keywords": ["keyword1", "keyword2", ...]
}}

Aim for approximately:
- 20-30 primary keywords
- 40-50 secondary keywords
- 60-70 long-tail keywords
- 50-60 related keywords
- 10-20 competitor-inspired keywords (if competitor data is available)

Generate high-quality, semantically relevant keywords that will improve SEO performance.
"""
        
        # Generate keywords using OpenAI
        response = generate_text_with_openai(prompt)
        
        # Parse the response
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                keywords_data = json.loads(json_str)
                
                # Validate required keys
                required_keys = ['primary_keywords', 'secondary_keywords', 'long_tail_keywords', 'related_keywords']
                for key in required_keys:
                    if key not in keywords_data:
                        keywords_data[key] = []
                
                # Handle competitor keywords if not present
                if 'competitor_inspired_keywords' not in keywords_data:
                    keywords_data['competitor_inspired_keywords'] = []
                
                # Calculate total count
                total_count = sum(len(keywords_data[key]) for key in keywords_data if isinstance(keywords_data[key], list))
                keywords_data['total_count'] = total_count
                keywords_data['competitor_keywords_used'] = len(competitor_keywords)
                
                print(f"✅ Generated {total_count} semantic keywords")
                return keywords_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            # Fallback: return basic structure
            print(f"⚠️ Could not parse JSON response, using fallback")
            return {
                "primary_keywords": [main_keyword] if main_keyword else [],
                "secondary_keywords": related_keywords,
                "long_tail_keywords": [],
                "related_keywords": [],
                "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
                "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
                "competitor_keywords_used": len(competitor_keywords)
            }
        
    except Exception as e:
        print(f"❌ Error generating semantic keywords: {str(e)}")
        return {
            "primary_keywords": [main_keyword] if main_keyword else [],
            "secondary_keywords": related_keywords,
            "long_tail_keywords": [],
            "related_keywords": [],
            "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
            "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
            "competitor_keywords_used": len(competitor_keywords),
            "error": str(e)
        }


def test_competitor_scraping_workflow():
    """
    Test the complete competitor scraping workflow.
    """
    print("🧪 Testing Competitor Scraping Workflow\n")
    
    # Test data
    test_jobs = [
        {
            "title": "Advanced Cricket Batting Techniques for Beginners",
            "main_keyword": "cricket batting",
            "related_keywords": ["batting techniques", "cricket training", "cricket skills"],
            "competitor_urls": [
                "https://cricketblog.com/batting-guide",
                "https://sportsinsights.com/cricket-tips"
            ]
        },
        {
            "title": "Complete SEO Guide for Small Businesses",
            "main_keyword": "SEO for small business",
            "related_keywords": ["local SEO", "small business marketing", "search optimization"],
            "competitor_urls": [
                "https://seoexperts.com/small-business-guide",
                "https://marketingblog.com/seo-strategies"
            ]
        }
    ]
    
    for i, job_data in enumerate(test_jobs, 1):
        print(f"{'='*60}")
        print(f"Test Case {i}: {job_data['title']}")
        print(f"{'='*60}")
        
        # Step 1: Scrape competitor URLs
        print(f"\n🔍 Step 1: Scraping competitor URLs")
        all_competitor_keywords = []
        
        for url in job_data['competitor_urls']:
            # Use mock scraping for testing
            scraped_data = mock_scrape_competitor_url(url)
            
            if scraped_data:
                # Extract keywords from scraped content
                keywords = extract_keywords_from_scraped_content(scraped_data)
                all_competitor_keywords.extend(keywords)
            else:
                print(f"⚠️ Failed to scrape: {url}")
        
        # Remove duplicates
        unique_competitor_keywords = list(set(all_competitor_keywords))
        print(f"✅ Total unique competitor keywords: {len(unique_competitor_keywords)}")
        
        # Step 2: Generate enhanced semantic keywords
        print(f"\n🔑 Step 2: Generating enhanced semantic keywords")
        semantic_keywords = generate_enhanced_semantic_keywords(
            main_keyword=job_data['main_keyword'],
            title=job_data['title'],
            related_keywords=job_data['related_keywords'],
            competitor_keywords=unique_competitor_keywords
        )
        
        # Step 3: Display results
        print(f"\n📊 Results Summary:")
        print(f"   Main Keyword: {job_data['main_keyword']}")
        print(f"   Related Keywords: {len(job_data['related_keywords'])}")
        print(f"   Competitor Keywords: {len(unique_competitor_keywords)}")
        print(f"   Total Generated Keywords: {semantic_keywords.get('total_count', 0)}")
        
        # Show breakdown
        print(f"\n📝 Keyword Breakdown:")
        for category, keywords in semantic_keywords.items():
            if isinstance(keywords, list) and keywords:
                print(f"   {category.replace('_', ' ').title()}: {len(keywords)}")
        
        # Show some sample keywords
        print(f"\n🏷️ Sample Keywords:")
        
        # Primary keywords
        primary = semantic_keywords.get('primary_keywords', [])
        if primary:
            print(f"   Primary (first 3): {', '.join(primary[:3])}")
        
        # Competitor-inspired keywords
        competitor_inspired = semantic_keywords.get('competitor_inspired_keywords', [])
        if competitor_inspired:
            print(f"   Competitor-inspired (first 3): {', '.join(competitor_inspired[:3])}")
        
        # Long-tail keywords
        long_tail = semantic_keywords.get('long_tail_keywords', [])
        if long_tail:
            print(f"   Long-tail (first 2): {', '.join(long_tail[:2])}")
        
        print(f"\n✅ Test case {i} completed successfully!")
    
    print(f"\n🎉 All test cases completed!")


def main():
    """Main function"""
    print("🚀 Competitor Scraping Test - Simple Version\n")
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Test the workflow
    test_competitor_scraping_workflow()


if __name__ == "__main__":
    main()
