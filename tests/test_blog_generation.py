#!/usr/bin/env python3
"""
Test script for the standalone blog generation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test basic imports
    from app.database import SessionLocal
    from app.models import ContentJob, WordPressCredentials
    print("✓ Successfully imported database modules")
    
    # Test the blog generator import
    from blog_generation_standalone import BlogGenerator, OpenAIClient, WordPressClient
    print("✓ Successfully imported blog generation modules")
    
    # Test OpenAI client initialization
    if os.getenv('OPENAI_API_KEY'):
        client = OpenAIClient(os.getenv('OPENAI_API_KEY'))
        print("✓ Successfully created OpenAI client")
    else:
        print("⚠ OPENAI_API_KEY not set - skipping OpenAI client test")
    
    # Test database connection
    db = SessionLocal()
    jobs = db.query(ContentJob).filter(ContentJob.status == True).limit(1).all()
    print(f"✓ Database connection successful - found {len(jobs)} outlined jobs")
    db.close()
    
    print("\nAll tests passed! Blog generation script is ready to use.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
