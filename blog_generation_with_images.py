#!/usr/bin/env python3
"""
Blog Generation Script with Image Support
Enhanced version that includes image generation and insertion into blog posts.
"""

import sys
import os
import json
import time
import logging
import requests
import re
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from sqlalchemy.orm import Session
from sqlalchemy import and_
import concurrent.futures
import threading

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import ContentJob, WordPressCredentials, User
from blog_generation_standalone import BlogGenerator as BaseGenerator, OpenAIClient, WordPressClient
from seo_content_enhancer import SEOContentEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blog_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageGenerator:
    """Enhanced image generator with Pixabay and featured image support."""
    
    def __init__(self, pixabay_api_key: str = None, featured_image_service_url: str = "http://localhost:8001"):
        self.pixabay_api_key = pixabay_api_key or os.getenv('PIXABAY_API_KEY')
        self.featured_image_service_url = featured_image_service_url
        
    def get_stock_image(self, query: str) -> Optional[str]:
        """Get a stock image from a free service like Unsplash."""
        try:
            # Use Unsplash's free API (no key required for basic usage)
            # Clean the query for URL
            clean_query = query.replace(' ', '-').lower()
            
            # Try different free stock photo services
            stock_services = [
                f"https://source.unsplash.com/1200x600/?{clean_query}",
                f"https://picsum.photos/1200/600?random={abs(hash(query))}",
                f"https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1200&h=600&fit=crop&crop=entropy&q=80",  # Programming fallback
                f"https://dummyimage.com/1200x600/4A90E2/FFFFFF&text={clean_query.replace('-', '+')}"
            ]
            
            for service_url in stock_services:
                try:
                    response = requests.head(service_url, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Found stock image from free service: {service_url}")
                        return service_url
                except:
                    continue
            
            # Final fallback to dummyimage.com
            placeholder_url = f"https://dummyimage.com/1200x600/4A90E2/FFFFFF&text={clean_query.replace('-', '+')}"
            logger.info(f"Using placeholder image: {placeholder_url}")
            return placeholder_url
            
        except Exception as e:
            logger.error(f"Error getting stock image: {str(e)}")
            return None
    
    def search_pixabay_image(self, query: str) -> Optional[str]:
        """Search for an image on Pixabay and return the URL."""
        if not self.pixabay_api_key:
            logger.warning("Pixabay API key not set, using free stock images")
            return self.get_stock_image(query)
            
        try:
            url = "https://pixabay.com/api/"
            params = {
                'key': self.pixabay_api_key,
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
            
            logger.warning(f"No images found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching Pixabay: {str(e)}")
            return None
    
    def generate_featured_image(self, image_url: str, title: str) -> Optional[bytes]:
        """Generate a featured image using the featured-image-generator service."""
        try:
            # Check if the featured image service is running
            health_response = requests.get(f"{self.featured_image_service_url}/health", timeout=5)
            if health_response.status_code != 200:
                logger.warning("Featured image service not available, using original image")
                return None
            
            # Prepare the request for the featured image generator
            payload = {
                "image_url": image_url,
                "article_title": title,
                "style": "modern",
                "pattern": "none"
            }
            
            response = requests.post(
                f"{self.featured_image_service_url}/featured-image/create",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Featured image generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating featured image: {str(e)}")
            return None
    
    def upload_image_to_wordpress(self, image_data: bytes, filename: str, wp_creds) -> Optional[str]:
        """Upload image to WordPress and return the URL."""
        try:
            # WordPress media upload endpoint
            upload_url = f"{wp_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/media"
            
            # Prepare the file upload
            files = {
                'file': (filename, image_data, 'image/webp' if filename.endswith('.webp') else 'image/jpeg')
            }
            
            # Create basic auth header
            credentials = f"{wp_creds.username}:{wp_creds.applicationPassword}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}'
            }
            
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully uploaded image to WordPress: {result.get('source_url')}")
            return result.get('source_url')
            
        except Exception as e:
            logger.error(f"Error uploading image to WordPress: {str(e)}")
            return None
    
    def insert_image_after_first_h2(self, html_content: str, image_url: str, alt_text: str) -> str:
        """Insert image after the first </h2> tag in the content."""
        if not image_url:
            return html_content
            
        # Create the image block
        image_block = f'''<!-- wp:image {{"align":"center","sizeSlug":"large"}} -->
<figure class="wp-block-image aligncenter size-large">
<img src="{image_url}" alt="{alt_text}" style="max-width:100%;height:auto;" />
</figure>
<!-- /wp:image -->

'''
        
        # Insert after the first </h2> tag
        modified_html = re.sub(r'(</h2>\s*<!-- /wp:heading -->)', r'\1\n' + image_block, html_content, count=1)
        
        return modified_html
    
    def set_featured_image_for_wordpress(self, post_id: int, image_data: bytes, filename: str, wp_creds) -> bool:
        """Upload and set an image as the featured image for a WordPress post."""
        try:
            # First upload the image to WordPress media library
            upload_url = f"{wp_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/media"
            
            # Prepare the file upload
            files = {
                'file': (filename, image_data, 'image/webp' if filename.endswith('.webp') else 'image/jpeg')
            }
            
            # Create basic auth header
            credentials = f"{wp_creds.username}:{wp_creds.applicationPassword}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}'
            }
            
            # Upload the image
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            image_id = result.get('id')
            
            if not image_id:
                logger.error("Failed to get image ID from WordPress response")
                return False
                
            # Now set this image as the featured image for the post
            update_url = f"{wp_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
            
            update_data = {
                'featured_media': image_id
            }
            
            update_response = requests.post(
                update_url,
                json=update_data,
                headers=headers
            )
            
            update_response.raise_for_status()
            
            logger.info(f"Successfully set featured image (ID: {image_id}) for post ID: {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting featured image: {str(e)}")
            return False

class EnhancedBlogGenerator(BaseGenerator):
    """Enhanced blog generator with image support."""
    
    def __init__(self):
        super().__init__()
        self.image_generator = ImageGenerator()
        self.seo_enhancer = SEOContentEnhancer()
    
    def add_images_to_content(self, content: str, job: ContentJob) -> str:
        """Add images to the blog content."""
        try:
            # Get WordPress credentials for image upload
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                logger.error("WordPress credentials not found for image upload")
                return content
            
            # Search for a relevant image using the main keyword
            search_query = job.mainKeyword or job.title
            image_url = self.image_generator.search_pixabay_image(search_query)
            
            if image_url:
                # Try to generate featured image first
                featured_image_data = self.image_generator.generate_featured_image(image_url, job.title)
                
                if featured_image_data:
                    # Upload featured image to WordPress
                    uploaded_url = self.image_generator.upload_image_to_wordpress(
                        featured_image_data, 
                        f"{job.title.replace(' ', '-')}-featured.webp", 
                        wp_creds
                    )
                    if uploaded_url:
                        alt_text = f"Featured image for {job.title}"
                        content = self.image_generator.insert_image_after_first_h2(content, uploaded_url, alt_text)
                        logger.info(f"Successfully added featured image to blog post")
                        return content
                
                # If featured image fails, try with original image
                try:
                    logger.info(f"Downloading image from: {image_url}")
                    response = requests.get(image_url, timeout=30)
                    if response.status_code == 200:
                        logger.info(f"Successfully downloaded image, size: {len(response.content)} bytes")
                        uploaded_url = self.image_generator.upload_image_to_wordpress(
                            response.content, 
                            f"{job.title.replace(' ', '-')}-image.jpg", 
                            wp_creds
                        )
                        if uploaded_url:
                            alt_text = f"Image related to {job.mainKeyword or job.title}"
                            content = self.image_generator.insert_image_after_first_h2(content, uploaded_url, alt_text)
                            logger.info(f"Added original image to blog post")
                            return content
                        else:
                            logger.error("Failed to upload image to WordPress")
                    else:
                        logger.error(f"Failed to download image: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Error downloading/uploading original image: {str(e)}")
                    # Try one more time with a simple fallback
                    try:
                        fallback_url = "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1200&h=600&fit=crop&crop=entropy&q=80"
                        logger.info(f"Trying fallback image: {fallback_url}")
                        response = requests.get(fallback_url, timeout=30)
                        if response.status_code == 200:
                            uploaded_url = self.image_generator.upload_image_to_wordpress(
                                response.content, 
                                f"{job.title.replace(' ', '-')}-fallback.jpg", 
                                wp_creds
                            )
                            if uploaded_url:
                                alt_text = f"Image for {job.title}"
                                content = self.image_generator.insert_image_after_first_h2(content, uploaded_url, alt_text)
                                logger.info(f"Added fallback image to blog post")
                                return content
                    except Exception as e2:
                        logger.error(f"Fallback image also failed: {str(e2)}")
            else:
                logger.warning(f"No suitable image found for: {search_query}")
                
            return content
            
        except Exception as e:
            logger.error(f"Error adding images to content: {str(e)}")
            # Return original content if image processing fails
            return content
    
    def generate_blog_post(self, job: ContentJob, max_workers: int = 3) -> str:
        """Generate complete blog post for a job with images and parallel processing."""
        try:
            logger.info(f"Generating blog post for job {job.id}: {job.title}")
            start_time = time.time()
            
            # Parse the outline
            chapters = self.parse_outline(job.Outline)
            
            # Generate introduction
            logger.info("🚀 Generating introduction...")
            intro_start = time.time()
            introduction = self.generate_introduction(job)
            intro_time = time.time() - intro_start
            logger.info(f"✅ Introduction generated in {intro_time:.2f} seconds")
            
            # Generate main content sections in parallel
            logger.info(f"🚀 Generating {len(chapters)} sections in parallel...")
            sections_start = time.time()
            section_contents = self.generate_sections_parallel(chapters, job, max_workers)
            sections_time = time.time() - sections_start
            logger.info(f"✅ All sections generated in {sections_time:.2f} seconds")
            
            # Combine all sections
            main_content = ""
            for section_content in section_contents:
                main_content += section_content
            
            # Generate FAQ section
            logger.info("🚀 Generating FAQ section...")
            faq_start = time.time()
            faqs = self.generate_faqs(job)
            faq_time = time.time() - faq_start
            logger.info(f"✅ FAQ section generated in {faq_time:.2f} seconds")
            
            # Generate conclusion
            logger.info("🚀 Generating conclusion...")
            conclusion_start = time.time()
            conclusion = self.generate_conclusion(job)
            conclusion_time = time.time() - conclusion_start
            logger.info(f"✅ Conclusion generated in {conclusion_time:.2f} seconds")
            
            # Combine all sections
            full_content = introduction + main_content + faqs + conclusion
            
            # Generate and insert images
            logger.info("🚀 Adding images to content...")
            image_start = time.time()
            full_content = self.add_images_to_content(full_content, job)
            image_time = time.time() - image_start
            logger.info(f"✅ Images added in {image_time:.2f} seconds")
            
            total_time = time.time() - start_time
            logger.info(f"✅ Successfully generated blog post for job {job.id}")
            logger.info(f"⏱️ Total generation time: {total_time:.2f} seconds")
            logger.info(f"📊 Time breakdown - Intro: {intro_time:.1f}s, Sections: {sections_time:.1f}s, FAQ: {faq_time:.1f}s, Conclusion: {conclusion_time:.1f}s, Images: {image_time:.1f}s")
            
            return full_content
            
        except Exception as e:
            logger.error(f"Error generating blog post for job {job.id}: {str(e)}")
            raise Exception(f"Error generating blog post: {str(e)}")
    
    def post_to_wordpress(self, job: ContentJob, content: str) -> Dict[str, Any]:
        """Post the generated content to WordPress."""
        try:
            # Get WordPress credentials
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                raise Exception(f"WordPress credentials not found for job {job.id}")
            
            # Create WordPress client
            wp_client = WordPressClient(
                site_url=wp_creds.siteUrl,
                username=wp_creds.username,
                app_password=wp_creds.applicationPassword
            )
            
            # Post content
            result = wp_client.post_content(
                title=job.title,
                content=content,
                status="draft"  # Always post as draft for review
            )
            
            post_id = result.get('id')
            if post_id:
                # Create dedicated featured image after successful post
                logger.info(f"Creating dedicated featured image for WordPress post ID: {post_id}")
                
                # Search for a high-quality image for the featured image
                search_query = job.mainKeyword or job.title
                image_url = self.image_generator.search_pixabay_image(search_query)
                
                if image_url:
                    # Generate a more polished featured image specifically for the WordPress featured image
                    featured_image_data = self.image_generator.generate_featured_image(
                        image_url=image_url, 
                        title=job.title
                    )
                    
                    if featured_image_data:
                        # Set as WordPress featured image
                        filename = f"{job.title.replace(' ', '-')}-wordpress-featured.webp"
                        success = self.image_generator.set_featured_image_for_wordpress(
                            post_id=post_id,
                            image_data=featured_image_data,
                            filename=filename,
                            wp_creds=wp_creds
                        )
                        
                        if success:
                            logger.info(f"Successfully set WordPress featured image for post ID: {post_id}")
                        else:
                            logger.warning(f"Failed to set WordPress featured image for post ID: {post_id}")
                    else:
                        logger.warning("Failed to generate featured image data")
                else:
                    logger.warning(f"No suitable image found for featured image: {search_query}")
            
            logger.info(f"Successfully posted job {job.id} to WordPress. Post ID: {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error posting job {job.id} to WordPress: {str(e)}")
            raise Exception(f"Error posting to WordPress: {str(e)}")
    
    def process_job(self, job: ContentJob) -> bool:
        """Process a single content job."""
        try:
            logger.info(f"Processing job {job.id}: {job.title}")
            
            # Generate blog post content
            content = self.generate_blog_post(job)
            
            # Post to WordPress
            wp_result = self.post_to_wordpress(job, content)
            
            logger.info(f"Successfully processed job {job.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}")
            return False
    
    def run(self, max_jobs: int = 5) -> None:
        """Run the blog generation process."""
        try:
            logger.info("Starting blog generation process...")
            
            # Get approved jobs
            jobs = self.get_approved_jobs(max_jobs)
            
            if not jobs:
                logger.info("No approved jobs found for blog generation")
                return
            
            # Process each job
            success_count = 0
            for job in jobs:
                try:
                    if self.process_job(job):
                        success_count += 1
                        # Add a small delay between jobs
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Failed to process job {job.id}: {str(e)}")
                    continue
            
            logger.info(f"Blog generation completed. Successfully processed {success_count}/{len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error in blog generation process: {str(e)}")
            raise Exception(f"Error in blog generation process: {str(e)}")

def main():
    """Main entry point."""
    try:
        # Ensure we have the required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY environment variable not set")
            return
        
        # Create and run the enhanced blog generator
        generator = EnhancedBlogGenerator()
        generator.run(max_jobs=5)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
