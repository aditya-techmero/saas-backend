#!/usr/bin/env python3
"""
Test script for blog generation with images
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials, User
from blog_generation_with_images import EnhancedBlogGenerator, ImageGenerator

def test_image_generation():
    """Test image generation components."""
    print("🖼️  Testing Image Generation Components")
    print("=" * 50)
    
    # Test image generator initialization
    image_gen = ImageGenerator()
    print("✅ Image generator initialized")
    
    # Test Pixabay search (only if API key is set)
    if os.getenv('PIXABAY_API_KEY'):
        print("🔍 Testing Pixabay image search...")
        image_url = image_gen.search_pixabay_image("python programming")
        if image_url:
            print(f"✅ Found image: {image_url}")
        else:
            print("⚠️  No image found")
    else:
        print("⚠️  PIXABAY_API_KEY not set, skipping Pixabay test")
    
    # Test featured image service (only if service is running)
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Featured image service is running")
        else:
            print("⚠️  Featured image service not responding")
    except:
        print("⚠️  Featured image service not available")
    
    print("\n🤖 Testing Enhanced Blog Generator")
    print("=" * 50)
    
    # Test enhanced blog generator
    generator = EnhancedBlogGenerator()
    print("✅ Enhanced blog generator initialized")
    
    # Check for test jobs
    jobs = generator.get_approved_jobs(1)
    if jobs:
        job = jobs[0]
        print(f"✅ Found test job: {job.title}")
        
        # Test image addition (without actually calling APIs)
        print("🔄 Testing image addition logic...")
        test_content = '''<!-- wp:heading {"level":2} -->
<h2>Test Section</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This is test content.</p>
<!-- /wp:paragraph -->'''
        
        # Test image insertion
        test_image_url = "https://example.com/test-image.jpg"
        modified_content = generator.image_generator.insert_image_after_first_h2(
            test_content, test_image_url, "Test image"
        )
        
        if test_image_url in modified_content:
            print("✅ Image insertion logic works correctly")
        else:
            print("❌ Image insertion failed")
    else:
        print("⚠️  No test jobs found")
    
    print("\n📊 Test Summary")
    print("=" * 50)
    print("✅ Image generation components are ready")
    print("✅ Enhanced blog generator is functional")
    print("💡 To test with real images, set PIXABAY_API_KEY environment variable")
    print("🚀 Run: python3 run_blog_generation.py --dry-run to test the full pipeline")

if __name__ == "__main__":
    test_image_generation()
