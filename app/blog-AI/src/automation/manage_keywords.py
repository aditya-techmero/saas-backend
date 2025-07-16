#!/usr/bin/env python3
"""
Semantic Keywords Management Script

This script generates semantic keywords for existing content jobs and updates
the semantic_keywords and semantic_keywords_2 fields in the database.
Uses existing job data (title, mainKeyword, related_keywords) without 
changing the database structure.

Now includes competitor URL scraping functionality.
"""

import sys
import os
import json
import traceback
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User
from ..competitor_analysis.scraper import scrape_competitor_keywords
from ..seo.semantic_keywords import generate_semantic_keywords_for_job

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class SemanticKeywordError(Exception):
    """Custom exception for semantic keyword errors"""
    pass


def preview_job_keywords(job_id: int, include_competitors: bool = False) -> None:
    """Preview semantic keywords for a job without saving to database"""
    db = SessionLocal()
    
    try:
        # Get the job
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        
        if not job:
            print(f"❌ Job {job_id} not found")
            return
        
        print(f"📋 Job Preview: {job.title}")
        print(f"   Main Keyword: {job.mainKeyword}")
        print(f"   Related Keywords: {job.related_keywords}")
        print(f"   Competitor URL 1: {job.competitor_url_1}")
        print(f"   Competitor URL 2: {job.competitor_url_2}")
        print(f"   Status: {job.status}")
        
        # Scrape competitor keywords if requested
        competitor_keywords = []
        if include_competitors:
            print(f"\n🔍 Scraping competitor keywords...")
            competitor_keywords = scrape_competitor_keywords(job)
            
            if competitor_keywords:
                print(f"🎯 Competitor Keywords ({len(competitor_keywords)}):")
                for i, keyword in enumerate(competitor_keywords[:10], 1):  # Show first 10
                    print(f"   {i:2d}. {keyword}")
                if len(competitor_keywords) > 10:
                    print(f"   ... and {len(competitor_keywords) - 10} more")
        
        # Generate semantic keywords
        print(f"\n🔑 Generating semantic keywords...")
        keywords = generate_semantic_keywords_for_job(job, competitor_keywords=competitor_keywords)
        
        # Display results
        print(f"\n📊 Generated Keywords Summary:")
        print(f"   Total Keywords: {keywords.get('total_count', 0)}")
        print(f"   Primary: {len(keywords.get('primary_keywords', []))}")
        print(f"   Secondary: {len(keywords.get('secondary_keywords', []))}")
        print(f"   Long-tail: {len(keywords.get('long_tail_keywords', []))}")
        print(f"   Related: {len(keywords.get('related_keywords', []))}")
        print(f"   Competitor-inspired: {len(keywords.get('competitor_inspired_keywords', []))}")
        
        # Show sample keywords from each category
        for category, kw_list in keywords.items():
            if isinstance(kw_list, list) and kw_list and category != 'competitor_inspired_keywords':
                print(f"\n🏷️ {category.replace('_', ' ').title()} (showing first 5):")
                for i, keyword in enumerate(kw_list[:5], 1):
                    print(f"   {i}. {keyword}")
        
        # Show competitor-inspired keywords separately
        if keywords.get('competitor_inspired_keywords'):
            print(f"\n🎯 Competitor-inspired Keywords:")
            for i, keyword in enumerate(keywords.get('competitor_inspired_keywords', [])[:10], 1):
                print(f"   {i}. {keyword}")
        
    except Exception as e:
        print(f"❌ Error previewing keywords for job {job_id}: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()


def update_job_keywords(job_id: int, include_competitors: bool = False) -> bool:
    """Update semantic keywords for a specific job"""
    db = SessionLocal()
    
    try:
        # Get the job
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        
        if not job:
            print(f"❌ Job {job_id} not found")
            return False
        
        print(f"📝 Updating keywords for job {job_id}: {job.title}")
        
        # Scrape competitor keywords if requested
        competitor_keywords = []
        if include_competitors:
            print(f"🔍 Scraping competitor keywords...")
            competitor_keywords = scrape_competitor_keywords(job)
        
        # Generate semantic keywords
        print(f"🔑 Generating semantic keywords...")
        keywords = generate_semantic_keywords_for_job(job, competitor_keywords=competitor_keywords)
        
        # Update the job with semantic keywords
        job.semantic_keywords = keywords
        
        # Also store competitor keywords separately if available
        if competitor_keywords:
            job.semantic_keywords_2 = {
                "competitor_keywords": competitor_keywords,
                "extracted_at": datetime.now().isoformat(),
                "source_urls": [url for url in [job.competitor_url_1, job.competitor_url_2] if url]
            }
        
        # Save to database
        db.commit()
        
        print(f"✅ Successfully updated keywords for job {job_id}")
        print(f"   Total keywords: {keywords.get('total_count', 0)}")
        print(f"   Competitor keywords: {len(competitor_keywords)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating keywords for job {job_id}: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        db.close()


def batch_update_keywords(status_filter: str = None, include_competitors: bool = False) -> None:
    """Update keywords for multiple jobs"""
    db = SessionLocal()
    
    try:
        # Build query
        query = db.query(ContentJob)
        
        if status_filter:
            query = query.filter(ContentJob.status == status_filter)
        
        jobs = query.all()
        
        if not jobs:
            print(f"❌ No jobs found with status: {status_filter}")
            return
        
        print(f"📋 Found {len(jobs)} jobs to process")
        
        success_count = 0
        
        for job in jobs:
            print(f"\n{'='*50}")
            try:
                # Scrape competitor keywords if requested
                competitor_keywords = []
                if include_competitors:
                    competitor_keywords = scrape_competitor_keywords(job)
                
                # Generate semantic keywords
                keywords = generate_semantic_keywords_for_job(job, competitor_keywords=competitor_keywords)
                
                # Update the job
                job.semantic_keywords = keywords
                
                # Also store competitor keywords separately if available
                if competitor_keywords:
                    job.semantic_keywords_2 = {
                        "competitor_keywords": competitor_keywords,
                        "extracted_at": datetime.now().isoformat(),
                        "source_urls": [url for url in [job.competitor_url_1, job.competitor_url_2] if url]
                    }
                
                # Save changes
                db.commit()
                
                success_count += 1
                print(f"✅ Updated job {job.id} - Total keywords: {keywords.get('total_count', 0)}")
                
            except Exception as e:
                print(f"❌ Error updating job {job.id}: {str(e)}")
                continue
        
        print(f"\n🎉 Batch update completed!")
        print(f"   Successfully updated: {success_count}/{len(jobs)} jobs")
        
    except Exception as e:
        print(f"❌ Error in batch update: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()


def list_jobs() -> None:
    """List all content jobs with their keyword status"""
    db = SessionLocal()
    
    try:
        jobs = db.query(ContentJob).all()
        
        if not jobs:
            print("❌ No jobs found")
            return
        
        print(f"📋 Found {len(jobs)} jobs:")
        print(f"{'ID':>3} {'Status':>10} {'Keywords':>8} {'Competitor':>10} {'Title':>30}")
        print("-" * 65)
        
        for job in jobs:
            # Check if keywords exist
            has_keywords = "Yes" if job.semantic_keywords else "No"
            has_competitor = "Yes" if (job.competitor_url_1 or job.competitor_url_2) else "No"
            
            # Truncate title if too long
            title = job.title[:27] + "..." if job.title and len(job.title) > 30 else (job.title or "No title")
            
            print(f"{job.id:>3} {job.status:>10} {has_keywords:>8} {has_competitor:>10} {title:>30}")
        
    except Exception as e:
        print(f"❌ Error listing jobs: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Manage semantic keywords for content jobs")
    
    parser.add_argument("action", choices=["list", "preview", "update", "batch"], 
                       help="Action to perform")
    parser.add_argument("--job-id", type=int, help="Job ID for preview/update actions")
    parser.add_argument("--status", type=str, help="Filter jobs by status for batch action")
    parser.add_argument("--competitors", action="store_true", 
                       help="Include competitor keyword scraping")
    
    args = parser.parse_args()
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    print(f"🚀 Semantic Keywords Manager")
    print(f"   Action: {args.action}")
    if args.competitors:
        print(f"   Including competitor analysis: Yes")
    print()
    
    if args.action == "list":
        list_jobs()
    
    elif args.action == "preview":
        if not args.job_id:
            print("❌ Job ID required for preview action")
            return
        preview_job_keywords(args.job_id, include_competitors=args.competitors)
    
    elif args.action == "update":
        if not args.job_id:
            print("❌ Job ID required for update action")
            return
        update_job_keywords(args.job_id, include_competitors=args.competitors)
    
    elif args.action == "batch":
        batch_update_keywords(args.status, include_competitors=args.competitors)
    
    print(f"\n🎉 Operation completed!")


if __name__ == "__main__":
    main()
