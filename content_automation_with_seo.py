#!/usr/bin/env python3
"""
Content automation script that processes approved content jobs from PostgreSQL,
generates AI content, creates semantic keywords, and publishes to WordPress.
"""

import sys
import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User

# OpenAI for content generation
import openai

# WordPress API
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_RETRIES = 3
SCRAPER_API_URL = "http://157.245.210.116:3000/api/scrape"

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


class ContentAutomationError(Exception):
    """Custom exception for content automation errors"""
    pass


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
        raise ContentAutomationError(f"OpenAI API error: {str(e)}")


def generate_semantic_keywords_for_job(
    job: ContentJob, 
    target_count: int = 200,
    competitor_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate semantic keywords for a content job using existing job data and competitor keywords.
    
    Args:
        job: The content job containing keyword and title information
        target_count: Target number of keywords to generate
        competitor_keywords: List of keywords extracted from competitor URLs
        
    Returns:
        Dictionary containing semantic keywords
    """
    try:
        # Use existing job fields (note: mainKeyword not main_keyword)
        main_keyword = job.mainKeyword or ""
        title = job.title or ""
        
        # Parse related keywords
        related_keywords = []
        if job.related_keywords:
            if isinstance(job.related_keywords, str):
                related_keywords = [kw.strip() for kw in job.related_keywords.split(',')]
            elif isinstance(job.related_keywords, list):
                related_keywords = job.related_keywords
        
        related_keywords_str = ", ".join(related_keywords) if related_keywords else "None provided"
        
        # Add competitor keywords to the context
        competitor_context = ""
        if competitor_keywords and len(competitor_keywords) > 0:
            competitor_context = f"""
Competitor Keywords (extracted from competitor analysis):
{", ".join(competitor_keywords[:50])}  # Limit to first 50 to avoid token limits

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
                
                # Add metadata
                keywords_data['generated_at'] = datetime.now().isoformat()
                keywords_data['competitor_keywords_used'] = len(competitor_keywords) if competitor_keywords else 0
                
                print(f"✅ Generated {total_count} semantic keywords for job {job.id}")
                return keywords_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            # Fallback: return basic structure
            print(f"⚠️ Could not parse JSON response for job {job.id}, using fallback")
            return {
                "primary_keywords": [main_keyword] if main_keyword else [],
                "secondary_keywords": related_keywords,
                "long_tail_keywords": [],
                "related_keywords": [],
                "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
                "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
                "generated_at": datetime.now().isoformat(),
                "competitor_keywords_used": len(competitor_keywords) if competitor_keywords else 0
            }
        
    except Exception as e:
        print(f"❌ Error generating semantic keywords for job {job.id}: {str(e)}")
        # Return basic structure with error info
        return {
            "primary_keywords": [main_keyword] if main_keyword else [],
            "secondary_keywords": related_keywords,
            "long_tail_keywords": [],
            "related_keywords": [],
            "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
            "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
            "generated_at": datetime.now().isoformat(),
            "competitor_keywords_used": len(competitor_keywords) if competitor_keywords else 0,
            "error": str(e)
        }


def generate_content_outline(job: ContentJob) -> str:
    """Generate content outline for a job"""
    try:
        # Use the outline prompt if available, otherwise create a basic prompt
        if job.outline_prompt:
            prompt = job.outline_prompt
        else:
            prompt = f"""
            Create a comprehensive outline for a blog post about "{job.title}".
            
            Main keyword: {job.mainKeyword}
            Related keywords: {job.related_keywords}
            Target audience: {job.audienceType or 'General audience'}
            
            Please create a detailed outline with:
            1. Introduction
            2. Main sections (4-6 sections)
            3. Conclusion
            4. FAQ section
            
            Format the outline clearly with headings and subheadings.
            """
        
        return generate_text_with_openai(prompt)
        
    except Exception as e:
        raise ContentAutomationError(f"Error generating content outline: {str(e)}")


def generate_blog_content(job: ContentJob) -> str:
    """Generate blog content based on job requirements"""
    try:
        # Get the outline first
        outline = generate_content_outline(job)
        
        # Create content generation prompt
        prompt = f"""
        Write a comprehensive blog post based on the following outline and requirements:
        
        Title: {job.title}
        Main Keyword: {job.mainKeyword}
        Related Keywords: {job.related_keywords}
        Target Audience: {job.audienceType or 'General audience'}
        Tone of Voice: {job.toneOfVoice or 'Professional'}
        Word Count: {job.article_word_count or 800} words
        
        Outline:
        {outline}
        
        Requirements:
        - Write in {job.toneOfVoice or 'professional'} tone
        - Target audience: {job.audienceType or 'general audience'}
        - Include the main keyword naturally throughout the content
        - Use related keywords appropriately
        - Make it engaging and informative
        - Include proper headings and structure
        - Write approximately {job.article_word_count or 800} words
        
        Please write the complete blog post in HTML format with proper headings (h1, h2, h3), paragraphs, and formatting.
        """
        
        content = generate_text_with_openai(prompt)
        
        # Clean up the content
        content = content.strip()
        
        return content
        
    except Exception as e:
        raise ContentAutomationError(f"Error generating blog content: {str(e)}")


def post_to_wordpress(content: str, title: str, wordpress_creds: WordPressCredentials) -> bool:
    """Post content to WordPress"""
    try:
        # WordPress API endpoint
        api_url = f"{wordpress_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/posts"
        
        # Post data
        post_data = {
            "title": title,
            "content": content,
            "status": "draft",  # Change to "publish" if you want to publish immediately
            "format": "standard"
        }
        
        # Make the request
        response = requests.post(
            api_url,
            json=post_data,
            auth=HTTPBasicAuth(wordpress_creds.username, wordpress_creds.applicationPassword),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            post_data = response.json()
            print(f"✅ Successfully posted to WordPress: {post_data['link']}")
            return True
        else:
            print(f"❌ Failed to post to WordPress. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting to WordPress: {str(e)}")
        return False


def process_content_job(job_id: int) -> bool:
    """Process a single content job"""
    db = SessionLocal()
    
    try:
        # Get the job
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        
        if not job:
            print(f"❌ Job {job_id} not found")
            return False
        
        print(f"📝 Processing job {job_id}: {job.title}")
        
        # Check if job is approved
        if job.status != 'approved':
            print(f"⚠️ Job {job_id} is not approved (status: {job.status})")
            return False
        
        # Get WordPress credentials
        wordpress_creds = job.wordpress_credentials
        if not wordpress_creds:
            print(f"❌ No WordPress credentials found for job {job_id}")
            return False
        
        # Step 1: Scrape competitor keywords if URLs are provided
        print(f"🔍 Step 1: Scraping competitor keywords for job {job_id}")
        competitor_keywords = scrape_competitor_keywords(job)
        
        # Step 2: Generate semantic keywords (including competitor insights)
        print(f"🔑 Step 2: Generating semantic keywords for job {job_id}")
        semantic_keywords = generate_semantic_keywords_for_job(job, competitor_keywords=competitor_keywords)
        
        # Update the job with semantic keywords
        job.semantic_keywords = semantic_keywords
        
        # Also store competitor keywords separately if available
        if competitor_keywords:
            job.semantic_keywords_2 = {
                "competitor_keywords": competitor_keywords,
                "extracted_at": datetime.now().isoformat(),
                "source_urls": [url for url in [job.competitor_url_1, job.competitor_url_2] if url]
            }
        
        # Step 3: Generate content
        print(f"📝 Step 3: Generating content for job {job_id}")
        content = generate_blog_content(job)
        
        # Step 4: Post to WordPress
        print(f"📤 Step 4: Posting to WordPress for job {job_id}")
        success = post_to_wordpress(content, job.title, wordpress_creds)
        
        if success:
            # Update job status
            job.status = 'completed'
            print(f"✅ Job {job_id} completed successfully!")
        else:
            job.status = 'failed'
            print(f"❌ Job {job_id} failed during WordPress posting")
        
        # Save changes
        db.commit()
        
        return success
        
    except Exception as e:
        print(f"❌ Error processing job {job_id}: {str(e)}")
        traceback.print_exc()
        
        # Update job status to failed
        try:
            job.status = 'failed'
            db.commit()
        except:
            pass
        
        return False
        
    finally:
        db.close()


def main():
    """Main function to process approved content jobs"""
    print("🚀 Starting content automation...")
    
    # Check for API keys
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    db = SessionLocal()
    
    try:
        # Get all approved jobs
        approved_jobs = db.query(ContentJob).filter(ContentJob.status == 'approved').all()
        
        if not approved_jobs:
            print("ℹ️ No approved jobs found")
            return
        
        print(f"📋 Found {len(approved_jobs)} approved jobs")
        
        # Process each job
        for job in approved_jobs:
            try:
                print(f"\n" + "="*50)
                success = process_content_job(job.id)
                
                if success:
                    print(f"✅ Job {job.id} completed successfully")
                else:
                    print(f"❌ Job {job.id} failed")
                    
            except Exception as e:
                print(f"❌ Error processing job {job.id}: {str(e)}")
                continue
        
        print(f"\n🎉 Content automation completed!")
        
    except Exception as e:
        print(f"❌ Error in main process: {str(e)}")
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
