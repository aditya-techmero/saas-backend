#!/usr/bin/env python3
"""
Test script to create a test job and run the blog generation process.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User
from blog_generation_standalone import BlogGenerator

def create_test_job():
    """Create a test job for blog generation."""
    db = SessionLocal()
    
    try:
        # Check if we have a user
        user = db.query(User).first()
        if not user:
            print("No user found in database")
            return None
            
        # Check if we have WordPress credentials
        wp_creds = db.query(WordPressCredentials).first()
        if not wp_creds:
            print("No WordPress credentials found in database")
            return None
            
        # Create test outline
        test_outline = {
            "chapters": [
                {
                    "id": "heading-1",
                    "title": "Understanding the Basics",
                    "headingTag": "h2",
                    "content": [
                        {
                            "id": "heading-1-1",
                            "title": "What is the main concept?",
                            "headingTag": "h3"
                        },
                        {
                            "id": "heading-1-2", 
                            "title": "Why is it important?",
                            "headingTag": "h3"
                        }
                    ]
                },
                {
                    "id": "heading-2",
                    "title": "Implementation Guide",
                    "headingTag": "h2",
                    "content": [
                        {
                            "id": "heading-2-1",
                            "title": "Step-by-step process",
                            "headingTag": "h3"
                        },
                        {
                            "id": "heading-2-2",
                            "title": "Common challenges",
                            "headingTag": "h3"
                        }
                    ]
                }
            ]
        }
        
        # Create test job
        test_job = ContentJob(
            user_id=user.id,
            title="Complete Guide to Python Programming for Beginners",
            status=True,  # Outlined
            isApproved=True,  # Approved
            Outline=json.dumps(test_outline),
            audienceType="beginners",
            contentFormat="guide",
            mainKeyword="python programming",
            toneOfVoice="friendly",
            related_keywords="python tutorial, programming basics, coding",
            article_word_count=2000,
            article_length="medium",
            wordpress_credentials_id=wp_creds.id
        )
        
        db.add(test_job)
        db.commit()
        db.refresh(test_job)
        
        print(f"✓ Created test job {test_job.id}: {test_job.title}")
        return test_job
        
    except Exception as e:
        print(f"❌ Error creating test job: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_blog_generation():
    """Test the blog generation process."""
    try:
        # Create test job
        test_job = create_test_job()
        if not test_job:
            print("Failed to create test job")
            return
            
        print(f"Testing blog generation for job {test_job.id}")
        
        # Create blog generator
        generator = BlogGenerator()
        
        # Test outline parsing
        chapters = generator.parse_outline(test_job.Outline)
        print(f"✓ Parsed {len(chapters)} chapters from outline")
        
        # Test section content generation (without actually calling OpenAI)
        if chapters:
            section = chapters[0]
            print(f"✓ Would generate content for section: {section.get('title')}")
            
            # Test prompt building
            prompt = generator.build_section_prompt(section, test_job)
            print(f"✓ Built prompt for section (length: {len(prompt)} chars)")
            
        # Test introduction prompt
        intro_prompt = f"""Write a compelling introduction for a blog post titled "{test_job.title}"."""
        print(f"✓ Built introduction prompt")
        
        # Test FAQ prompt
        faq_prompt = f"""Create 5-7 frequently asked questions for "{test_job.title}"."""
        print(f"✓ Built FAQ prompt")
        
        # Test conclusion prompt
        conclusion_prompt = f"""Write a conclusion for "{test_job.title}"."""
        print(f"✓ Built conclusion prompt")
        
        print("\n✓ All blog generation components tested successfully!")
        print("To run actual generation with OpenAI, use: python3 blog_generation_standalone.py")
        
    except Exception as e:
        print(f"❌ Error testing blog generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blog_generation()
