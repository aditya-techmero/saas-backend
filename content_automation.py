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
# Import blog-AI modules with proper path handling
blog_ai_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'blog-AI', 'src')
if blog_ai_path not in sys.path:
    sys.path.insert(0, blog_ai_path)

# Import after adding to path
try:
    from seo.semantic_keywords import generate_semantic_keywords_simple, SemanticKeywordError
    from text_generation.core import generate_text, LLMProvider, GenerationOptions
    from types.providers import ProviderType, OpenAIConfig
except ImportError as e:
    print(f"Warning: Could not import blog-AI modules: {e}")
    print("Will use simplified content generation")

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


class ContentAutomationError(Exception):
    """Custom exception for content automation errors"""
    pass


def setup_llm_provider(api_key: str = None, model: str = DEFAULT_MODEL) -> LLMProvider:
    """Set up the LLM provider for content generation"""
    if not api_key:
        api_key = OPENAI_API_KEY
    
    if not api_key:
        raise ContentAutomationError("OpenAI API key is required")
    
    config = OpenAIConfig(api_key=api_key, model=model)
    return LLMProvider(type=ProviderType.OPENAI, config=config)


def generate_semantic_keywords_for_job(
    job: ContentJob, 
    provider: LLMProvider,
    target_count: int = 200
) -> Dict[str, Any]:
    """
    Generate semantic keywords for a content job.
    
    Args:
        job: The content job containing keyword and title information
        provider: The LLM provider to use
        target_count: Target number of keywords to generate
        
    Returns:
        Dictionary containing semantic keywords
    """
    try:
        # Parse related keywords
        related_keywords = []
        if job.related_keywords:
            if isinstance(job.related_keywords, str):
                related_keywords = [kw.strip() for kw in job.related_keywords.split(',')]
            elif isinstance(job.related_keywords, list):
                related_keywords = job.related_keywords
        
        # Generate semantic keywords
        semantic_keywords = generate_semantic_keywords_simple(
            main_keyword=job.main_keyword,
            related_keywords=related_keywords,
            title=job.title,
            provider=provider,
            target_count=target_count
        )
        
        print(f"✅ Generated {semantic_keywords.get('total_count', 0)} semantic keywords for job {job.id}")
        return semantic_keywords
        
    except Exception as e:
        print(f"❌ Error generating semantic keywords for job {job.id}: {str(e)}")
        # Return basic structure with error info
        return {
            "primary_keywords": [job.main_keyword] if job.main_keyword else [],
            "secondary_keywords": related_keywords,
            "long_tail_keywords": [],
            "related_keywords": [],
            "total_count": len([job.main_keyword] + related_keywords),
            "error": str(e)
        }


def generate_content_outline(job: ContentJob, provider: LLMProvider) -> str:
    """Generate content outline for a job"""
    try:
        # Use the outline prompt if available, otherwise create a basic prompt
        if job.outline_prompt:
            prompt = job.outline_prompt
        else:
            prompt = f"""
            Create a comprehensive outline for a blog post about "{job.title}".
            
            Main keyword: {job.main_keyword}
            Related keywords: {job.related_keywords}
            Target audience: {job.target_audience or 'General audience'}
            
            Please create a detailed outline with:
            1. Introduction
            2. Main sections (4-6 sections)
            3. Conclusion
            4. FAQ section
            
            Make it engaging and SEO-friendly.
            """
        
        outline = generate_text(prompt, provider)
        print(f"✅ Generated outline for job {job.id}")
        return outline
        
    except Exception as e:
        print(f"❌ Error generating outline for job {job.id}: {str(e)}")
        raise ContentAutomationError(f"Failed to generate outline: {str(e)}")


def generate_blog_content_from_outline(job: ContentJob, outline: str, provider: LLMProvider) -> str:
    """Generate blog content from outline"""
    try:
        # Use the output prompt if available, otherwise create a basic prompt
        if job.output_prompt:
            prompt = job.output_prompt.replace("{outline}", outline)
        else:
            prompt = f"""
            Write a comprehensive blog post based on the following outline:
            
            {outline}
            
            Requirements:
            - Target keyword: {job.main_keyword}
            - Related keywords: {job.related_keywords}
            - Target audience: {job.target_audience or 'General audience'}
            - Tone: {job.tone or 'Professional and engaging'}
            - Word count: {job.word_count or 1500} words
            
            Make it engaging, informative, and SEO-optimized.
            """
        
        content = generate_text(prompt, provider)
        print(f"✅ Generated blog content for job {job.id}")
        return content
        
    except Exception as e:
        print(f"❌ Error generating blog content for job {job.id}: {str(e)}")
        raise ContentAutomationError(f"Failed to generate blog content: {str(e)}")


def publish_to_wordpress(job: ContentJob, content: str, wp_credentials: WordPressCredentials) -> Dict[str, Any]:
    """Publish content to WordPress"""
    try:
        # Prepare the post data
        post_data = {
            "title": job.title,
            "content": content,
            "status": "draft",  # Start as draft for review
            "categories": [job.category] if job.category else [],
            "tags": [job.main_keyword] + (job.related_keywords or [])
        }
        
        # WordPress REST API endpoint
        wp_url = f"{wp_credentials.site_url.rstrip('/')}/wp-json/wp/v2/posts"
        
        # Make the API request
        response = requests.post(
            wp_url,
            json=post_data,
            auth=HTTPBasicAuth(wp_credentials.username, wp_credentials.password),
            headers={
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 201:
            wp_post = response.json()
            print(f"✅ Published to WordPress: {wp_post.get('link', 'N/A')}")
            return {
                "success": True,
                "post_id": wp_post.get("id"),
                "post_url": wp_post.get("link"),
                "status": wp_post.get("status")
            }
        else:
            print(f"❌ WordPress publish failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        print(f"❌ Error publishing to WordPress: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def update_job_status(job: ContentJob, status: str, ai_content: str = None, 
                     semantic_keywords: Dict[str, Any] = None,
                     wordpress_result: Dict[str, Any] = None, db_session=None):
    """Update job status and content in database"""
    try:
        if not db_session:
            db_session = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        # Update job fields
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if ai_content:
            job.ai_content = ai_content
        
        if semantic_keywords:
            job.semantic_keywords = semantic_keywords
            # Store first 100 keywords in semantic_keywords_2 for alternative use
            all_keywords = (
                semantic_keywords.get('primary_keywords', []) + 
                semantic_keywords.get('secondary_keywords', [])
            )
            job.semantic_keywords_2 = all_keywords[:100]
        
        if wordpress_result:
            if wordpress_result.get('success'):
                job.wordpress_post_id = wordpress_result.get('post_id')
                job.wordpress_post_url = wordpress_result.get('post_url')
            else:
                job.wordpress_error = wordpress_result.get('error', 'Unknown error')
        
        db_session.commit()
        print(f"✅ Updated job {job.id} status to: {status}")
        
        if should_close:
            db_session.close()
            
    except Exception as e:
        print(f"❌ Error updating job status: {str(e)}")
        if db_session:
            db_session.rollback()
        raise


def process_content_job(job: ContentJob, provider: LLMProvider, db_session) -> bool:
    """Process a single content job"""
    try:
        print(f"\n🔄 Processing job {job.id}: {job.title}")
        
        # Update status to "Processing"
        update_job_status(job, "Processing", db_session=db_session)
        
        # Step 1: Generate semantic keywords
        print("📝 Generating semantic keywords...")
        semantic_keywords = generate_semantic_keywords_for_job(job, provider)
        
        # Step 2: Generate content outline
        print("📋 Generating content outline...")
        outline = generate_content_outline(job, provider)
        
        # Step 3: Generate blog content
        print("✍️ Generating blog content...")
        content = generate_blog_content_from_outline(job, outline, provider)
        
        # Step 4: Get WordPress credentials
        wp_credentials = db_session.query(WordPressCredentials).filter(
            WordPressCredentials.id == job.wordpress_credentials_id
        ).first()
        
        if not wp_credentials:
            raise ContentAutomationError(f"WordPress credentials not found for job {job.id}")
        
        # Step 5: Publish to WordPress
        print("🚀 Publishing to WordPress...")
        wp_result = publish_to_wordpress(job, content, wp_credentials)
        
        # Step 6: Update job status
        final_status = "Completed" if wp_result.get("success") else "Failed"
        update_job_status(
            job, 
            final_status, 
            ai_content=content,
            semantic_keywords=semantic_keywords,
            wordpress_result=wp_result,
            db_session=db_session
        )
        
        print(f"✅ Job {job.id} completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing job {job.id}: {str(e)}")
        print(traceback.format_exc())
        
        # Update job status to "Failed"
        try:
            update_job_status(job, "Failed", db_session=db_session)
        except:
            pass
        
        return False


def get_approved_jobs(db_session, limit: int = 10) -> List[ContentJob]:
    """Get approved content jobs that need processing"""
    try:
        jobs = db_session.query(ContentJob).filter(
            ContentJob.status == "Approved",
            ContentJob.wordpress_credentials_id.isnot(None)
        ).limit(limit).all()
        
        print(f"📊 Found {len(jobs)} approved jobs ready for processing")
        return jobs
        
    except Exception as e:
        print(f"❌ Error fetching approved jobs: {str(e)}")
        return []


def main():
    """Main automation function"""
    print("🚀 Starting content automation process...")
    
    try:
        # Setup LLM provider
        provider = setup_llm_provider()
        print("✅ LLM provider configured")
        
        # Setup database session
        db_session = SessionLocal()
        
        # Get approved jobs
        jobs = get_approved_jobs(db_session)
        
        if not jobs:
            print("ℹ️ No approved jobs found. Exiting.")
            return
        
        # Process each job
        success_count = 0
        for job in jobs:
            if process_content_job(job, provider, db_session):
                success_count += 1
        
        print(f"\n📊 Automation completed: {success_count}/{len(jobs)} jobs processed successfully")
        
    except Exception as e:
        print(f"❌ Automation failed: {str(e)}")
        print(traceback.format_exc())
    finally:
        if 'db_session' in locals():
            db_session.close()


if __name__ == "__main__":
    main()
