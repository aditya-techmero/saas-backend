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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User
from ..competitor_analysis.scraper import scrape_competitor_keywords
from ..seo.semantic_keywords import generate_semantic_keywords_for_job, generate_text_with_openai

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

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


class ContentAutomationError(Exception):
    """Custom exception for content automation errors"""
    pass


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
