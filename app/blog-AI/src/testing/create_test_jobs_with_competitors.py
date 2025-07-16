#!/usr/bin/env python3
"""
Create a test job with competitor URLs to test the enhanced automation pipeline.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User


def create_test_job_with_competitors():
    """Create a test job with competitor URLs for testing the enhanced automation"""
    db = SessionLocal()
    
    try:
        # First, check if we have users and WordPress credentials
        user = db.query(User).first()
        if not user:
            print("❌ No users found. Please create a user first.")
            return None
        
        wordpress_creds = db.query(WordPressCredentials).first()
        if not wordpress_creds:
            print("❌ No WordPress credentials found. Please create WordPress credentials first.")
            return None
        
        # Create test job with competitor URLs
        test_job = ContentJob(
            user_id=user.id,
            title="Advanced Cricket Batting Techniques for Beginners",
            status="approved",  # Set to approved for automation processing
            outline_prompt="Create a comprehensive guide about cricket batting techniques suitable for beginners",
            wordpress_credentials_id=wordpress_creds.id,
            
            # Content job specific fields
            audienceType="Cricket beginners and enthusiasts",
            contentFormat="Blog post",
            mainKeyword="cricket batting techniques",
            toneOfVoice="Informative and encouraging",
            related_keywords="batting stance, cricket training, batting practice, cricket skills, batting tips",
            article_word_count=1200,
            article_length="Medium",
            
            # Competitor URLs - these will be scraped for additional keywords
            competitor_url_1="https://www.cricketcountry.com/articles/batting-techniques-for-beginners",
            competitor_url_2="https://www.espncricinfo.com/story/cricket-batting-fundamentals",
            
            # These will be populated by the automation
            semantic_keywords=None,
            semantic_keywords_2=None
        )
        
        # Add to database
        db.add(test_job)
        db.commit()
        db.refresh(test_job)
        
        print(f"✅ Created test job with ID: {test_job.id}")
        print(f"   Title: {test_job.title}")
        print(f"   Main Keyword: {test_job.mainKeyword}")
        print(f"   Related Keywords: {test_job.related_keywords}")
        print(f"   Competitor URL 1: {test_job.competitor_url_1}")
        print(f"   Competitor URL 2: {test_job.competitor_url_2}")
        print(f"   Status: {test_job.status}")
        
        return test_job.id
        
    except Exception as e:
        print(f"❌ Error creating test job: {str(e)}")
        return None
    finally:
        db.close()


def create_seo_test_job():
    """Create an SEO-focused test job"""
    db = SessionLocal()
    
    try:
        # Get user and WordPress credentials
        user = db.query(User).first()
        wordpress_creds = db.query(WordPressCredentials).first()
        
        if not user or not wordpress_creds:
            print("❌ Missing user or WordPress credentials")
            return None
        
        # Create SEO test job
        seo_job = ContentJob(
            user_id=user.id,
            title="Complete SEO Guide for Small Businesses in 2024",
            status="approved",
            outline_prompt="Create a comprehensive SEO guide for small businesses",
            wordpress_credentials_id=wordpress_creds.id,
            
            # Content job specific fields
            audienceType="Small business owners and marketers",
            contentFormat="Comprehensive guide",
            mainKeyword="SEO for small business",
            toneOfVoice="Professional and actionable",
            related_keywords="local SEO, small business marketing, search optimization, keyword research, content marketing",
            article_word_count=1500,
            article_length="Long",
            
            # Competitor URLs for SEO topic
            competitor_url_1="https://moz.com/blog/small-business-seo-guide",
            competitor_url_2="https://searchengineland.com/small-business-seo-strategies",
            
            semantic_keywords=None,
            semantic_keywords_2=None
        )
        
        # Add to database
        db.add(seo_job)
        db.commit()
        db.refresh(seo_job)
        
        print(f"✅ Created SEO test job with ID: {seo_job.id}")
        print(f"   Title: {seo_job.title}")
        print(f"   Main Keyword: {seo_job.mainKeyword}")
        print(f"   Related Keywords: {seo_job.related_keywords}")
        print(f"   Competitor URL 1: {seo_job.competitor_url_1}")
        print(f"   Competitor URL 2: {seo_job.competitor_url_2}")
        print(f"   Status: {seo_job.status}")
        
        return seo_job.id
        
    except Exception as e:
        print(f"❌ Error creating SEO test job: {str(e)}")
        return None
    finally:
        db.close()


def create_basic_test_job():
    """Create a basic test job without competitor URLs"""
    db = SessionLocal()
    
    try:
        # Get user and WordPress credentials
        user = db.query(User).first()
        wordpress_creds = db.query(WordPressCredentials).first()
        
        if not user or not wordpress_creds:
            print("❌ Missing user or WordPress credentials")
            return None
        
        # Create basic test job
        basic_job = ContentJob(
            user_id=user.id,
            title="Introduction to Python Programming for Beginners",
            status="approved",
            outline_prompt="Create an introductory guide to Python programming",
            wordpress_credentials_id=wordpress_creds.id,
            
            # Content job specific fields
            audienceType="Programming beginners",
            contentFormat="Tutorial",
            mainKeyword="Python programming",
            toneOfVoice="Beginner-friendly and encouraging",
            related_keywords="Python tutorial, programming basics, Python syntax, coding fundamentals",
            article_word_count=1000,
            article_length="Medium",
            
            # No competitor URLs for this test
            competitor_url_1=None,
            competitor_url_2=None,
            
            semantic_keywords=None,
            semantic_keywords_2=None
        )
        
        # Add to database
        db.add(basic_job)
        db.commit()
        db.refresh(basic_job)
        
        print(f"✅ Created basic test job with ID: {basic_job.id}")
        print(f"   Title: {basic_job.title}")
        print(f"   Main Keyword: {basic_job.mainKeyword}")
        print(f"   Related Keywords: {basic_job.related_keywords}")
        print(f"   Competitor URLs: None")
        print(f"   Status: {basic_job.status}")
        
        return basic_job.id
        
    except Exception as e:
        print(f"❌ Error creating basic test job: {str(e)}")
        return None
    finally:
        db.close()


def list_approved_jobs():
    """List all approved jobs"""
    db = SessionLocal()
    
    try:
        approved_jobs = db.query(ContentJob).filter(ContentJob.status == 'approved').all()
        
        if not approved_jobs:
            print("ℹ️ No approved jobs found")
            return
        
        print(f"📋 Found {len(approved_jobs)} approved jobs:")
        print(f"{'ID':>3} {'Title':>40} {'Competitors':>11} {'Keywords':>8}")
        print("-" * 65)
        
        for job in approved_jobs:
            title = job.title[:37] + "..." if job.title and len(job.title) > 40 else (job.title or "No title")
            has_competitors = "Yes" if (job.competitor_url_1 or job.competitor_url_2) else "No"
            has_keywords = "Yes" if job.semantic_keywords else "No"
            
            print(f"{job.id:>3} {title:>40} {has_competitors:>11} {has_keywords:>8}")
        
    except Exception as e:
        print(f"❌ Error listing jobs: {str(e)}")
    finally:
        db.close()


def main():
    """Main function"""
    print("🚀 Create Test Jobs with Competitor URLs\n")
    
    # List existing approved jobs
    print("📋 Current approved jobs:")
    list_approved_jobs()
    
    print("\n" + "="*50)
    print("Creating new test jobs...")
    print("="*50)
    
    # Create test jobs
    print("\n1. Creating cricket test job with competitor URLs...")
    cricket_job_id = create_test_job_with_competitors()
    
    print("\n2. Creating SEO test job with competitor URLs...")
    seo_job_id = create_seo_test_job()
    
    print("\n3. Creating basic test job without competitor URLs...")
    basic_job_id = create_basic_test_job()
    
    print("\n" + "="*50)
    print("Test jobs created successfully!")
    print("="*50)
    
    # List all approved jobs again
    print("\n📋 Updated approved jobs:")
    list_approved_jobs()
    
    print("\n🎯 Next Steps:")
    print("1. Run the automation script to process these jobs:")
    print("   python content_automation_with_seo.py")
    print()
    print("2. Or test specific jobs manually:")
    if cricket_job_id:
        print(f"   python manage_semantic_keywords.py preview --job-id {cricket_job_id} --competitors")
    if seo_job_id:
        print(f"   python manage_semantic_keywords.py preview --job-id {seo_job_id} --competitors")
    if basic_job_id:
        print(f"   python manage_semantic_keywords.py preview --job-id {basic_job_id}")
    print()
    print("3. Test competitor scraping functionality:")
    print("   python test_competitor_scraping.py")
    print("   python test_competitor_scraping_simple.py")


if __name__ == "__main__":
    main()
