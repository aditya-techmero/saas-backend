#!/usr/bin/env python3
"""
Clean Blog Automation Script
Complete workflow: Markdown → HTML → WordPress Upload

This script:
1. Generates clean Markdown content with images
2. Converts Markdown to HTML
3. Uploads HTML to WordPress
4. Saves all content locally for backup
"""

import sys
import os
import json
import time
import logging
import requests
import base64
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import ContentJob, WordPressCredentials, User
from blog_generation_markdown import MarkdownBlogGenerator
from markdown_to_html_converter import MarkdownToHTMLConverter
from blog_generation_standalone import WordPressClient
from seo_content_enhancer import SEOContentEnhancer
from sqlalchemy import and_

# Configure logging
def setup_logging(debug: bool = False):
    """Setup logging configuration with debug flag support."""
    # Ensure logger directory exists
    logger_dir = "/Users/aditya/Desktop/backend/logger"
    os.makedirs(logger_dir, exist_ok=True)
    
    # Set log level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create handlers
    handlers = []
    
    # File handler - always log to file
    file_handler = logging.FileHandler(
        os.path.join(logger_dir, 'blog_automation_clean.log'),
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    handlers.append(file_handler)
    
    # Console handler - only if debug is enabled
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Override any existing logging configuration
    )
    
    return logging.getLogger(__name__)

# Initialize logger (will be reconfigured when setup_logging is called)
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
    
    def search_pixabay_image(self, query: str, for_featured: bool = False) -> Optional[str]:
        """Search for an image on Pixabay and return the URL."""
        if not self.pixabay_api_key:
            logger.warning("Pixabay API key not set, using free stock images")
            return self.get_stock_image(query)
            
        try:
            url = "https://pixabay.com/api/"
            
            # Different params for featured image vs regular images
            if for_featured:
                params = {
                    'key': self.pixabay_api_key,
                    'q': query,
                    'image_type': 'photo',
                    'category': 'backgrounds',
                    'min_width': 1200,  # Lower requirement for featured images
                    'min_height': 800,   # Lower requirement for featured images
                    'safesearch': 'true',
                    'per_page': 5
                }
            else:
                params = {
                    'key': self.pixabay_api_key,
                    'q': query,
                    'image_type': 'photo',
                    'category': 'backgrounds',
                    'min_width': 1200,
                    'min_height': 600,
                    'safesearch': 'true',
                    'per_page': 5
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
    
    def generate_featured_image_with_fallback(self, title: str, main_keyword: str = None) -> Optional[bytes]:
        """Generate a featured image with multiple fallback options."""
        try:
            # Try multiple search queries in order of preference
            search_queries = []
            
            # Add main keyword if provided
            if main_keyword:
                search_queries.append(main_keyword)
                # Also try a more generic version
                search_queries.append(main_keyword.split()[0] if main_keyword else "")
            
            # Extract key words from title for search
            title_words = title.lower().split()
            # Filter out common words and take important ones
            important_words = [word for word in title_words if len(word) > 3 and word not in ['what', 'how', 'why', 'when', 'where', 'the', 'and', 'or', 'but', 'with', 'for', 'are', 'good', 'these', 'todays', 'world']]
            
            if important_words:
                search_queries.append(" ".join(important_words[:2]))  # Take first 2 important words
                search_queries.append(important_words[0])  # Take the first important word
            
            # Add generic fallback terms
            search_queries.extend([
                "knowledge wisdom",
                "ancient wisdom",
                "spiritual knowledge",
                "meditation spiritual",
                "wisdom"
            ])
            
            # Try each search query
            for search_query in search_queries:
                if not search_query.strip():
                    continue
                    
                logger.info(f"🔍 Searching for featured image with query: {search_query}")
                
                # Search for image
                image_url = self.search_pixabay_image(search_query, for_featured=True)
                
                if image_url:
                    logger.info(f"✅ Found image for featured image: {image_url}")
                    
                    # Generate the featured image
                    featured_image_data = self.generate_featured_image(
                        image_url=image_url, 
                        title=title
                    )
                    
                    if featured_image_data:
                        logger.info(f"✅ Successfully generated featured image with query: {search_query}")
                        return featured_image_data
                    else:
                        logger.warning(f"❌ Failed to generate featured image with query: {search_query}")
                else:
                    logger.warning(f"❌ No image found for query: {search_query}")
            
            # If all searches fail, try with a generic image
            logger.info("🔄 Trying generic fallback image...")
            fallback_image_url = self.get_stock_image("wisdom knowledge")
            
            if fallback_image_url:
                featured_image_data = self.generate_featured_image(
                    image_url=fallback_image_url, 
                    title=title
                )
                
                if featured_image_data:
                    logger.info("✅ Successfully generated featured image with fallback")
                    return featured_image_data
            
            logger.error("❌ All attempts to generate featured image failed")
            return None
            
        except Exception as e:
            logger.error(f"Error in generate_featured_image_with_fallback: {str(e)}")
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
                logger.info(f"✅ Featured image service generated image for title: {title}")
                return response.content
            else:
                logger.error(f"Featured image generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating featured image: {str(e)}")
            return None
    
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

class CleanBlogAutomation:
    """Clean, simple blog automation with Markdown → HTML → WordPress workflow."""
    
    def __init__(self, debug: bool = False, workers: int = 3):
        # Setup logging first
        global logger
        logger = setup_logging(debug)
        
        self.debug = debug
        self.workers = workers
        self.db = SessionLocal()
        self.markdown_generator = MarkdownBlogGenerator()
        self.html_converter = MarkdownToHTMLConverter()
        self.image_generator = ImageGenerator()  # Add image generator
        self.seo_enhancer = SEOContentEnhancer()  # Add SEO enhancer
        self.content_dir = "/Users/aditya/Desktop/backend/generated_content"
        self.html_dir = "/Users/aditya/Desktop/backend/generated_content/html"
        
        # Ensure directories exist
        os.makedirs(self.content_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        
    def get_approved_jobs(self, max_jobs: int = 5) -> List[ContentJob]:
        """Get approved jobs that are ready for blog generation."""
        try:
            jobs = self.db.query(ContentJob).filter(
                and_(
                    ContentJob.status == True,      # Has outline
                    ContentJob.isApproved == True,  # Is approved
                    ContentJob.Outline.isnot(None)  # Has outline content
                )
            ).limit(max_jobs).all()
            
            logger.info(f"Found {len(jobs)} approved jobs ready for blog generation")
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting approved jobs: {str(e)}")
            return []
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content to remove H1 tags and ensure proper formatting."""
        # Remove any H1 tags that might have slipped through
        html_content = re.sub(r'<h1[^>]*>.*?</h1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any standalone H1 markdown that wasn't converted
        html_content = re.sub(r'^# .+$\n?', '', html_content, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
        
        return html_content.strip()

    def process_single_job(self, job: ContentJob) -> bool:
        """Process a single job through the complete workflow."""
        try:
            logger.info(f"🚀 Starting workflow for job {job.id}: {job.title}")
            
            # Step 1: Generate Markdown content
            logger.info(f"📝 Step 1: Generating Markdown content (using {self.workers} workers)...")
            markdown_content = self.markdown_generator.generate_blog_post(job, max_workers=self.workers)
            
            if not markdown_content:
                logger.error(f"❌ Failed to generate markdown for job {job.id}")
                return False
            
            logger.info(f"✅ Markdown generated successfully")
            
            # Step 1.5: Analyze SEO metrics on clean Markdown content
            logger.info(f"📊 Step 1.5: Analyzing SEO metrics on Markdown content...")
            seo_metadata = self.seo_enhancer.prepare_wordpress_metadata(
                title=job.title,
                keyword=job.mainKeyword,
                content=markdown_content  # Analyze the clean Markdown, not HTML
            )
            
            # Step 2: Convert to HTML
            logger.info(f"🔄 Step 2: Converting Markdown to HTML...")
            html_content = self.html_converter.convert_markdown_to_html(markdown_content)
            
            if not html_content:
                logger.error(f"❌ Failed to convert markdown to HTML for job {job.id}")
                return False
            
            # Step 2.5: Clean HTML content to remove H1 tags
            logger.info(f"🧹 Step 2.5: Cleaning HTML content...")
            html_content = self.clean_html_content(html_content)
            
            # Clean HTML content to remove H1 tags and ensure proper formatting
            html_content = self.clean_html_content(html_content)
            
            # Save HTML locally
            safe_title = job.title.replace(' ', '-').replace('/', '-')
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            html_filename = f"{safe_title}-{timestamp}.html"
            html_filepath = os.path.join(self.html_dir, html_filename)
            
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML saved to: {html_filepath}")
            
            # Step 3: Upload to WordPress
            logger.info(f"🌐 Step 3: Uploading to WordPress...")
            post_id = self.upload_to_wordpress(html_content, job, seo_metadata)
            
            if not post_id:
                logger.error(f"❌ Failed to upload to WordPress for job {job.id}")
                return False
            
            logger.info(f"✅ Successfully uploaded to WordPress! Post ID: {post_id}")
            
            # Update job status and set isApproved to False once blog is posted
            job.wordpress_post_id = post_id
            job.isApproved = False
            self.db.commit()
            
            logger.info(f"✅ Job {job.id} isApproved set to False after successful posting")
            logger.info(f"🎉 Complete workflow finished for job {job.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing job {job.id}: {str(e)}")
            return False
    
    def upload_to_wordpress(self, html_content: str, job: ContentJob, seo_metadata: dict) -> Optional[str]:
        """Upload HTML content to WordPress with pre-calculated SEO metadata and set featured image."""
        try:
            # Get WordPress credentials using the job's credentials ID
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                logger.error(f"WordPress credentials not found for job {job.id}")
                return None
            
            # Initialize WordPress client
            wp_client = WordPressClient(
                site_url=wp_creds.siteUrl,
                username=wp_creds.username,
                app_password=wp_creds.applicationPassword
            )
            
            # Use the pre-calculated SEO metadata (analyzed from Markdown)
            logger.info("📊 Using pre-calculated SEO metadata from Markdown analysis...")
            
            # Log metadata being sent
            logger.info(f"📝 Sending metadata to WordPress:")
            logger.info(f"  • Meta Description: {seo_metadata.get('meta_description', 'Not set')}")
            logger.info(f"  • Focus Keyword: {seo_metadata.get('focus_keyword', 'Not set')}")
            logger.info(f"  • Readability Score: {seo_metadata.get('readability_score', 'Not calculated')}")
            logger.info(f"  • Word Count: {seo_metadata.get('word_count', 'Not counted')}")
            logger.info(f"  • External Links: {seo_metadata.get('external_links_count', 0)}")
            
            # Upload to WordPress with metadata
            result = wp_client.post_content(
                title=job.title,
                content=html_content,
                status="draft",
                meta_data=seo_metadata
            )
            
            post_id = result.get('id') if result else None
            
            if post_id:
                logger.info(f"✅ Successfully posted to WordPress with SEO metadata. Post ID: {post_id}")
                
                # Create and set featured image after successful post
                logger.info(f"🖼️  Creating featured image for WordPress post ID: {post_id}")
                
                # Use the enhanced featured image generation with fallback
                featured_image_data = self.image_generator.generate_featured_image_with_fallback(
                    title=job.title,
                    main_keyword=job.mainKeyword
                )
                
                if featured_image_data:
                    # Set as WordPress featured image
                    filename = f"{job.title.replace(' ', '-').replace('?', '').replace('!', '')}-featured.webp"
                    success = self.image_generator.set_featured_image_for_wordpress(
                        post_id=post_id,
                        image_data=featured_image_data,
                        filename=filename,
                        wp_creds=wp_creds
                    )
                    
                    if success:
                        logger.info(f"✅ Successfully set WordPress featured image for post ID: {post_id}")
                    else:
                        logger.warning(f"⚠️  Failed to set WordPress featured image for post ID: {post_id}")
                else:
                    logger.warning("⚠️  Failed to generate featured image data after all attempts")
            
            return post_id
            
        except Exception as e:
            logger.error(f"Error uploading to WordPress: {str(e)}")
            return None
    
    def generate_and_save_metadata(self, content: str, job: ContentJob) -> None:
        """Generate and save SEO metadata for the blog post."""
        try:
            # Generate meta description
            content_preview = content[:500] if content else ""
            meta_description = self.image_generator.image_generator.seo_enhancer.generate_meta_description(
                job.title, job.mainKeyword, content_preview
            ) if hasattr(self.image_generator, 'image_generator') else f"Learn about {job.mainKeyword} with expert insights."
            
            # Calculate overall readability score
            readability_score = 60  # Default score
            readability_feedback = "Good readability (acceptable)"
            
            # Log metadata
            logger.info(f"💾 Generated SEO metadata for: {job.title}")
            logger.info(f"📝 Meta description: {meta_description}")
            logger.info(f"📊 Readability score: {readability_score} ({readability_feedback})")
            
        except Exception as e:
            logger.error(f"Error generating metadata: {str(e)}")

    def run_automation(self, max_jobs: int = 5, workers: int = None) -> None:
        """Run the complete automation workflow."""
        try:
            # Use provided workers or default to instance workers
            if workers is not None:
                self.workers = workers
            
            if self.debug:
                logger.info(f"🔥 Starting Clean Blog Automation (DEBUG MODE - {self.workers} workers)")
            else:
                logger.info(f"🔥 Starting Clean Blog Automation ({self.workers} workers)")
            logger.info("=" * 60)
            
            # Get approved jobs
            jobs = self.get_approved_jobs(max_jobs)
            
            if not jobs:
                logger.info("📭 No approved jobs found. Automation complete.")
                return
            
            successful_jobs = 0
            failed_jobs = 0
            
            for job in jobs:
                logger.info("-" * 60)
                success = self.process_single_job(job)
                
                if success:
                    successful_jobs += 1
                else:
                    failed_jobs += 1
                
                # Small delay between jobs
                time.sleep(2)
            
            # Summary
            logger.info("=" * 60)
            logger.info(f"📊 AUTOMATION SUMMARY:")
            logger.info(f"✅ Successful jobs: {successful_jobs}")
            logger.info(f"❌ Failed jobs: {failed_jobs}")
            logger.info(f"📝 Total processed: {successful_jobs + failed_jobs}")
            logger.info("🎉 Blog automation complete!")
            
        except Exception as e:
            logger.error(f"❌ Critical error in automation: {str(e)}")
        finally:
            self.db.close()

def main():
    """Main function to run the blog automation."""
    automation = CleanBlogAutomation()
    automation.run_automation()

if __name__ == "__main__":
    main()
