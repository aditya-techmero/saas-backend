#!/usr/bin/env python3
"""
Outline generation script for processing content jobs.

This script:
1. Fetches up to 10 pending jobs from the database
2. Runs semantic keyword generation and competitor keyword extraction in parallel
3. Generates JSON outlines for each job
4. Updates the database with the results
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal, Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship

# Define ContentJob model inline to avoid import issues
class ContentJob(Base):
    __tablename__ = "content_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(Text, nullable=True)
    status = Column(Boolean, nullable=False, default=False)  # False = pending, True = outlined
    isApproved = Column("isapproved", Boolean, nullable=False, default=False)  # PostgreSQL converts to lowercase
    created_at = Column(TIMESTAMP, server_default=func.now())
    outline_prompt = Column(Text, nullable=True)
    
    # WordPress credentials reference (make nullable to avoid foreign key issues)
    wordpress_credentials_id = Column(Integer, nullable=True)
    
    # Content job specific fields
    Outline = Column(Text, nullable=True)
    audienceType = Column(Text, nullable=True)
    contentFormat = Column(Text, nullable=True)
    mainKeyword = Column(Text, nullable=True)
    toneOfVoice = Column(Text, nullable=True)
    related_keywords = Column(String, nullable=True)
    article_word_count = Column(Integer, nullable=True)
    article_length = Column(String, nullable=True)
    competitor_url_1 = Column(String, nullable=True)
    competitor_url_2 = Column(String, nullable=True)
    semantic_keywords = Column(JSON, nullable=True)
    semantic_keywords_2 = Column(JSON, nullable=True)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-3.5-turbo"
SCRAPER_API_URL = "http://157.245.210.116:3000/api/scrape"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outline_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_pending_jobs(limit: int = 10) -> List[ContentJob]:
    """
    Fetch pending jobs from the database.
    
    Args:
        limit: Maximum number of jobs to fetch
        
    Returns:
        List of pending ContentJob objects
    """
    db = SessionLocal()
    try:
        jobs = db.query(ContentJob).filter(
            ContentJob.status == False  # False = pending
        ).limit(limit).all()
        
        logger.info(f"Retrieved {len(jobs)} pending jobs from database")
        return jobs
    except Exception as e:
        logger.error(f"Error fetching pending jobs: {e}")
        return []
    finally:
        db.close()


def generate_text_with_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Generate text using OpenAI API"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates high-quality SEO content and semantic keywords."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


def generate_semantic_keywords_for_job(job: ContentJob, target_count: int = 200, competitor_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
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
        # Use existing job fields
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
                
                # Add metadata
                keywords_data['generated_at'] = datetime.now().isoformat()
                keywords_data['main_keyword'] = main_keyword
                keywords_data['target_count'] = target_count
                
                logger.info(f"Successfully generated semantic keywords for job {job.id}")
                return keywords_data
                
            else:
                logger.error(f"No JSON found in response for job {job.id}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response for job {job.id}: {e}")
            return {}
    
    except Exception as e:
        logger.error(f"Error generating semantic keywords for job {job.id}: {e}")
        return {}


def scrape_competitor_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape competitor URL using the external API to extract content.
    
    Args:
        url: The competitor URL to scrape
        
    Returns:
        Dictionary containing scraped content or None if failed
    """
    try:
        logger.info(f"Scraping competitor URL: {url}")
        
        # Make request to the scraper API
        response = requests.post(
            SCRAPER_API_URL,
            json={"url": url},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully scraped {url}")
            return data
        else:
            logger.error(f"Failed to scrape {url}. Status: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error scraping {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
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
            logger.warning("No content found in scraped data")
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
                    logger.info(f"Extracted {len(cleaned_keywords)} keywords from competitor content")
                    return cleaned_keywords
                else:
                    logger.warning("Response is not a list")
                    return []
            else:
                logger.warning("No JSON array found in response")
                return []
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse JSON response: {str(e)}")
            return []
        
    except Exception as e:
        logger.error(f"Error extracting keywords from scraped content: {str(e)}")
        return []


def scrape_competitor_keywords(job: ContentJob) -> List[str]:
    """
    Scrape competitor URLs and extract keywords from their content.
    
    Args:
        job: ContentJob object containing competitor URLs
        
    Returns:
        List of extracted keywords from competitor content
    """
    all_keywords = []
    
    # Get competitor URLs from job
    competitor_urls = []
    if job.competitor_url_1:
        competitor_urls.append(job.competitor_url_1)
    if job.competitor_url_2:
        competitor_urls.append(job.competitor_url_2)
    
    if not competitor_urls:
        logger.info(f"No competitor URLs found for job {job.id}")
        return []
    
    # Scrape each competitor URL
    for url in competitor_urls:
        try:
            # Scrape the URL
            scraped_data = scrape_competitor_url(url)
            
            if scraped_data:
                # Extract keywords from scraped content
                keywords = extract_keywords_from_scraped_content(scraped_data)
                all_keywords.extend(keywords)
                
        except Exception as e:
            logger.error(f"Error processing competitor URL {url}: {str(e)}")
            continue
    
    # Remove duplicates and return
    unique_keywords = list(set(all_keywords))
    logger.info(f"Total unique keywords extracted from competitors: {len(unique_keywords)}")
    
    return unique_keywords


def generate_semantic_keywords_for_job_wrapper(job: ContentJob) -> Tuple[int, Dict[str, Any]]:
    """
    Wrapper function for semantic keyword generation that returns job ID and results.
    
    Args:
        job: ContentJob object
        
    Returns:
        Tuple of (job_id, semantic_keywords_dict)
    """
    try:
        logger.info(f"Generating semantic keywords for job {job.id}")
        
        # Generate semantic keywords
        semantic_keywords = generate_semantic_keywords_for_job(job)
        
        logger.info(f"Successfully generated semantic keywords for job {job.id}")
        return job.id, semantic_keywords
        
    except Exception as e:
        logger.error(f"Error generating semantic keywords for job {job.id}: {e}")
        return job.id, {}


def scrape_competitor_keywords_wrapper(job: ContentJob) -> Tuple[int, List[str]]:
    """
    Wrapper function for competitor keyword scraping that returns job ID and results.
    
    Args:
        job: ContentJob object
        
    Returns:
        Tuple of (job_id, competitor_keywords_list)
    """
    try:
        logger.info(f"Scraping competitor keywords for job {job.id}")
        
        # Scrape competitor keywords
        competitor_keywords = scrape_competitor_keywords(job)
        
        logger.info(f"Successfully scraped {len(competitor_keywords)} competitor keywords for job {job.id}")
        return job.id, competitor_keywords
        
    except Exception as e:
        logger.error(f"Error scraping competitor keywords for job {job.id}: {e}")
        return job.id, []


def generate_outline_json(job: ContentJob, semantic_keywords: Dict[str, Any], competitor_keywords: List[str]) -> Dict[str, Any]:
    """
    Generate a JSON outline for a content job using semantic and competitor keywords.
    
    Args:
        job: ContentJob object
        semantic_keywords: Dictionary containing semantic keywords
        competitor_keywords: List of competitor keywords
        
    Returns:
        Dictionary containing the JSON outline
    """
    try:
        # Prepare job information
        title = job.title or "Untitled"
        main_keyword = job.mainKeyword or ""
        audience = job.audienceType or "general audience"
        content_format = job.contentFormat or "blog post"
        tone = job.toneOfVoice or "professional"
        word_count = job.article_word_count or 1500
        
        # Parse related keywords
        related_keywords = []
        if job.related_keywords:
            if isinstance(job.related_keywords, str):
                related_keywords = [kw.strip() for kw in job.related_keywords.split(',')]
            elif isinstance(job.related_keywords, list):
                related_keywords = job.related_keywords
        
        # Prepare semantic keywords context
        semantic_context = ""
        if semantic_keywords:
            primary_kw = semantic_keywords.get('primary_keywords', [])[:10]
            secondary_kw = semantic_keywords.get('secondary_keywords', [])[:10]
            longtail_kw = semantic_keywords.get('long_tail_keywords', [])[:10]
            
            semantic_context = f"""
Semantic Keywords to incorporate:
Primary: {', '.join(primary_kw)}
Secondary: {', '.join(secondary_kw)}
Long-tail: {', '.join(longtail_kw)}
"""
        
        # Prepare competitor keywords context
        competitor_context = ""
        if competitor_keywords:
            competitor_context = f"""
Competitor Keywords (top 20): {', '.join(competitor_keywords[:20])}
"""
        
        # Create outline generation prompt
        prompt = f"""
Generate a comprehensive JSON outline for the following content:

Title: {title}
Main Keyword: {main_keyword}
Target Audience: {audience}
Content Format: {content_format}
Tone of Voice: {tone}
Target Word Count: {word_count}
Related Keywords: {', '.join(related_keywords)}

{semantic_context}

{competitor_context}

Please create a detailed JSON outline with the following structure:
{{
    "title": "{title}",
    "meta_description": "SEO-optimized meta description (155-160 characters)",
    "main_keyword": "{main_keyword}",
    "target_audience": "{audience}",
    "content_format": "{content_format}",
    "tone_of_voice": "{tone}",
    "estimated_word_count": {word_count},
    "sections": [
        {{
            "section_number": 1,
            "title": "Introduction",
            "estimated_words": 200,
            "description": "Brief description of what this section covers",
            "key_points": [
                "Key point 1",
                "Key point 2",
                "Key point 3"
            ],
            "keywords_to_include": ["keyword1", "keyword2"]
        }},
        {{
            "section_number": 2,
            "title": "Main Section Title",
            "estimated_words": 300,
            "description": "Description of main content",
            "key_points": [
                "Main point 1",
                "Main point 2"
            ],
            "keywords_to_include": ["keyword3", "keyword4"]
        }}
    ],
    "seo_keywords": {{
        "primary_keywords": ["primary1", "primary2"],
        "secondary_keywords": ["secondary1", "secondary2"],
        "long_tail_keywords": ["long tail phrase 1", "long tail phrase 2"]
    }},
    "call_to_action": "Compelling call to action for the end of the article",
    "faq_suggestions": [
        {{
            "question": "Frequently asked question 1?",
            "answer_preview": "Brief preview of the answer"
        }},
        {{
            "question": "Frequently asked question 2?",
            "answer_preview": "Brief preview of the answer"
        }}
    ],
    "internal_linking_opportunities": [
        "Related topic 1",
        "Related topic 2"
    ],
    "generated_at": "{datetime.now().isoformat()}"
}}

Requirements:
- Create 5-8 main sections (including introduction and conclusion)
- Each section should have 2-5 key points
- Include relevant keywords from the semantic and competitor analysis
- Ensure the outline is comprehensive and well-structured
- Make sure the estimated word counts add up to approximately {word_count}
- Use the specified tone of voice throughout
- Include SEO-optimized elements (meta description, keyword distribution)

Generate only the JSON object, no additional text.
"""
        
        # Generate outline using OpenAI
        response = generate_text_with_openai(prompt, model="gpt-3.5-turbo")
        
        # Parse the JSON response
        try:
            # Find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                outline_data = json.loads(json_str)
                
                logger.info(f"Successfully generated JSON outline for job {job.id}")
                return outline_data
            else:
                logger.error(f"No JSON found in response for job {job.id}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON outline for job {job.id}: {e}")
            return {}
    
    except Exception as e:
        logger.error(f"Error generating outline for job {job.id}: {e}")
        return {}


def update_job_with_results(job_id: int, semantic_keywords: Dict[str, Any], competitor_keywords: List[str], outline: Dict[str, Any]) -> bool:
    """
    Update the database with the generated results.
    
    Args:
        job_id: ID of the job to update
        semantic_keywords: Generated semantic keywords
        competitor_keywords: Scraped competitor keywords
        outline: Generated JSON outline
        
    Returns:
        True if update was successful, False otherwise
    """
    db = SessionLocal()
    try:
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return False
        
        # Update job with results
        job.semantic_keywords = semantic_keywords
        job.Outline = json.dumps(outline, indent=2)
        job.status = True  # True = outlined
        
        # Store competitor keywords in semantic_keywords_2 field (as a workaround)
        if competitor_keywords:
            job.semantic_keywords_2 = {"competitor_keywords": competitor_keywords}
        
        db.commit()
        logger.info(f"Successfully updated job {job_id} with outline and keywords")
        return True
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def process_job(job: ContentJob) -> bool:
    """
    Process a single job: generate keywords, scrape competitors, create outline, and update database.
    
    Args:
        job: ContentJob object to process
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        logger.info(f"Processing job {job.id}: {job.title}")
        
        # Run semantic keyword generation and competitor scraping in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            semantic_future = executor.submit(generate_semantic_keywords_for_job_wrapper, job)
            competitor_future = executor.submit(scrape_competitor_keywords_wrapper, job)
            
            # Wait for both to complete
            semantic_job_id, semantic_keywords = semantic_future.result()
            competitor_job_id, competitor_keywords = competitor_future.result()
        
        # Generate outline using both sets of keywords
        outline = generate_outline_json(job, semantic_keywords, competitor_keywords)
        
        if not outline:
            logger.error(f"Failed to generate outline for job {job.id}")
            return False
        
        # Update database with results
        success = update_job_with_results(job.id, semantic_keywords, competitor_keywords, outline)
        
        if success:
            logger.info(f"Successfully processed job {job.id}")
        else:
            logger.error(f"Failed to update database for job {job.id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing job {job.id}: {e}")
        return False


def main():
    """Main function to process pending jobs."""
    logger.info("Starting outline generation process")
    
    try:
        # Get pending jobs
        jobs = get_pending_jobs(limit=10)
        
        if not jobs:
            logger.info("No pending jobs found")
            return
        
        # Process jobs
        successful_jobs = 0
        failed_jobs = 0
        
        for job in jobs:
            success = process_job(job)
            if success:
                successful_jobs += 1
            else:
                failed_jobs += 1
        
        logger.info(f"Processing complete. Successful: {successful_jobs}, Failed: {failed_jobs}")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
    
    logger.info("Outline generation process finished")


if __name__ == "__main__":
    main()
