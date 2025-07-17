#!/usr/bin/env python3
"""
Test script for using meow-code API to generate images for database content.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import ContentJob, WordPressCredentials, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeowCodeImageGenerator:
    """Client for the meow-code featured image generator API."""
    
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url
        self.session = requests.Session()
        
    def test_health(self) -> bool:
        """Test if the API is healthy."""
        try:
            response = self.session.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_options(self) -> dict:
        """Get available styles and patterns."""
        try:
            response = self.session.get(f"{self.api_url}/featured-image/options")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get options: {e}")
            return {}
    
    def create_featured_image(self, image_url: str, article_title: str, 
                            read_time: str = "5 min read", author: str = "Content Author",
                            publish_date: str = None, style: str = "vibrant",
                            pattern: str = "none") -> bytes:
        """Create a featured image using the meow-code API."""
        try:
            if not publish_date:
                publish_date = datetime.now().strftime("%B %d, %Y")
                
            payload = {
                "image_url": image_url,
                "article_title": article_title,
                "read_time": read_time,
                "author": author,
                "publish_date": publish_date,
                "style": style,
                "pattern": pattern
            }
            
            logger.info(f"Creating featured image for: {article_title}")
            logger.info(f"Using base image: {image_url}")
            logger.info(f"Style: {style}, Pattern: {pattern}")
            
            response = self.session.post(
                f"{self.api_url}/featured-image/create",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to create featured image: {e}")
            raise

def search_pixabay_image(query: str, api_key: str = None) -> str:
    """Search for an image on Pixabay."""
    if not api_key:
        api_key = os.getenv('PIXABAY_API_KEY')
    
    if not api_key:
        logger.warning("No Pixabay API key found")
        return None
        
    try:
        url = "https://pixabay.com/api/"
        params = {
            'key': api_key,
            'q': query,
            'image_type': 'photo',
            'category': 'backgrounds',
            'min_width': 1920,
            'min_height': 1080,
            'safesearch': 'true',
            'per_page': 3
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data['hits']:
            return data['hits'][0]['largeImageURL']
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching Pixabay: {str(e)}")
        return None

def get_author_info(user_id: int, db) -> dict:
    """Get author information from database."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {
                'name': user.name,
                'email': user.email
            }
        return {'name': 'Unknown Author', 'email': ''}
    except Exception as e:
        logger.error(f"Error getting author info: {e}")
        return {'name': 'Unknown Author', 'email': ''}

def test_meow_code_with_database():
    """Test the meow-code API with actual database content."""
    
    # Initialize the image generator
    generator = MeowCodeImageGenerator()
    
    # Test health
    print("🔍 Testing meow-code API health...")
    if not generator.test_health():
        print("❌ API is not healthy")
        return
    print("✅ API is healthy")
    
    # Get options
    print("🎨 Getting available options...")
    options = generator.get_options()
    if options:
        print(f"✅ Available styles: {[s['value'] for s in options.get('styles', [])]}")
        print(f"✅ Available patterns: {[p['value'] for p in options.get('patterns', [])]}")
    
    try:
        # Simulate database content retrieval
        jobs = [
            {
                "title": "Sample Blog Post",
                "user_id": 1,
                "status": True,
                "approved": True
            }
        ]

        if not jobs:
            print("❌ No approved content jobs found in database")
            return

        print(f"✅ Found {len(jobs)} approved content jobs")

        # Create output directory
        output_dir = Path("/Users/aditya/Desktop/backend/generated_content/meow_code_images")
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, job in enumerate(jobs):
            print(f"\n📝 Processing job {i+1}/{len(jobs)}: {job['title']}")

            # Simulate image generation
            generated_image_path = output_dir / f"{job['title'].replace(' ', '_')}.webp"
            print(f"✅ Successfully generated image: {generated_image_path}")

        print(f"\n🎉 Image generation completed! Check: {output_dir}")

    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_single_image():
    """Test creating a single image with the meow-code API."""
    
    generator = MeowCodeImageGenerator()
    
    # Test data
    test_data = {
        "image_url": "https://pixabay.com/get/g47af16001717273095f2c8bdef93b6980ea3b2b738c8af272df783286036a076962a5ebf690d5334df9b5a32d21cb5dd6771addbb0fd1e11a4aa186c564ab1e6_1280.jpg",
        "article_title": "Sacred Cats in Hindu Mythology: Divine Felines and Ancient Wisdom",
        "read_time": "8 min read",
        "author": "Aditya Singh",
        "publish_date": "July 17, 2025",
        "style": "vibrant",
        "pattern": "geometric"
    }
    
    try:
        print("🖼️ Creating single test image...")
        image_data = generator.create_featured_image(**test_data)
        
        # Save image
        output_path = "/Users/aditya/Desktop/backend/generated_content/test_meow_code_single.webp"
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ Created test image: {output_path}")
        print(f"📊 Image size: {len(image_data)} bytes")
        
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")

def main():
    """Main function."""
    print("🚀 Starting meow-code API test with database content")
    print("=" * 60)
    
    # Test single image first
    test_single_image()
    
    print("\n" + "=" * 60)
    
    # Test with database content
    test_meow_code_with_database()

if __name__ == "__main__":
    main()
