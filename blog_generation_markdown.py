#!/usr/bin/env python3
"""
Enhanced Markdown Blog Generation Script
- Uses multiple image APIs (Pexels, Pixabay, Unsplash)
- Outputs pure Markdown format
- Saves local copies in generated_content folder
- Adds image for every 2 headings
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
from urllib.parse import urljoin, quote
from sqlalchemy.orm import Session
from sqlalchemy import and_
import hashlib

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import ContentJob, WordPressCredentials, User
from blog_generation_standalone import BlogGenerator as BaseGenerator, OpenAIClient, WordPressClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blog_generation_markdown.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedImageGenerator:
    """Enhanced image generator with multiple API fallbacks."""
    
    def __init__(self):
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        self.pixabay_api_key = os.getenv('PIXABAY_API_KEY')
        self.unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        self.featured_image_service_url = "http://localhost:8001"
        self.local_images_dir = "/Users/aditya/Desktop/backend/generated_content/images"
        
        # Create images directory if it doesn't exist
        os.makedirs(self.local_images_dir, exist_ok=True)
        
    def search_pexels_image(self, query: str) -> Optional[Dict]:
        """Search for an image on Pexels."""
        if not self.pexels_api_key:
            return None
            
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {
                'Authorization': self.pexels_api_key
            }
            params = {
                'query': query,
                'per_page': 5,
                'orientation': 'landscape'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('photos'):
                photo = data['photos'][0]
                return {
                    'url': photo['src']['large'],
                    'alt': photo.get('alt', query),
                    'source': 'pexels'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Pexels: {str(e)}")
            return None
    
    def search_pixabay_image(self, query: str) -> Optional[Dict]:
        """Search for an image on Pixabay."""
        if not self.pixabay_api_key:
            return None
            
        try:
            url = "https://pixabay.com/api/"
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
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('hits'):
                hit = data['hits'][0]
                return {
                    'url': hit['largeImageURL'],
                    'alt': hit.get('tags', query),
                    'source': 'pixabay'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Pixabay: {str(e)}")
            return None
    
    def search_unsplash_image(self, query: str) -> Optional[Dict]:
        """Search for an image on Unsplash."""
        if not self.unsplash_access_key:
            return None
            
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {
                'Authorization': f'Client-ID {self.unsplash_access_key}'
            }
            params = {
                'query': query,
                'per_page': 5,
                'orientation': 'landscape'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                return {
                    'url': result['urls']['regular'],
                    'alt': result.get('alt_description', query),
                    'source': 'unsplash'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Unsplash: {str(e)}")
            return None
    
    def get_fallback_image(self, query: str) -> Dict:
        """Get a fallback image if all APIs fail."""
        clean_query = quote(query.replace(' ', '+'))
        return {
            'url': f"https://dummyimage.com/1200x600/4A90E2/FFFFFF&text={clean_query}",
            'alt': f"Image for {query}",
            'source': 'fallback'
        }
    
    def find_image(self, query: str) -> Dict:
        """Find an image using multiple APIs with fallback."""
        logger.info(f"Searching for image: {query}")
        
        # Try APIs in order of preference
        apis = [
            ('Pexels', self.search_pexels_image),
            ('Pixabay', self.search_pixabay_image),
            ('Unsplash', self.search_unsplash_image)
        ]
        
        for api_name, search_func in apis:
            try:
                result = search_func(query)
                if result:
                    logger.info(f"Found image from {api_name}: {result['url']}")
                    return result
            except Exception as e:
                logger.warning(f"Failed to search {api_name}: {str(e)}")
                continue
        
        # Use fallback if all APIs fail
        logger.warning(f"All APIs failed for query: {query}, using fallback")
        return self.get_fallback_image(query)
    
    def generate_custom_image(self, image_info: Dict, heading_text: str, filename: str) -> Optional[str]:
        """Generate custom image with heading using featured image service."""
        try:
            logger.info(f"Generating custom image for heading: {heading_text}")
            
            # Check if the featured image service is running
            health_response = requests.get(f"{self.featured_image_service_url}/health", timeout=5)
            if health_response.status_code != 200:
                logger.warning("Featured image service not available, downloading original image")
                return self.download_and_save_image(image_info, filename)
            
            # Prepare the request for the featured image generator
            payload = {
                "image_url": image_info['url'],
                "article_title": heading_text,
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
                # Save the generated image locally
                local_path = os.path.join(self.local_images_dir, filename)
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Generated and saved custom image: {local_path}")
                return local_path
            else:
                logger.error(f"Custom image generation failed: {response.status_code}")
                return self.download_and_save_image(image_info, filename)
                
        except Exception as e:
            logger.error(f"Error generating custom image: {str(e)}")
            return self.download_and_save_image(image_info, filename)
    
    def download_and_save_image(self, image_info: Dict, filename: str) -> Optional[str]:
        """Download image and save locally."""
        try:
            logger.info(f"Downloading image from {image_info['source']}: {image_info['url']}")
            
            response = requests.get(image_info['url'], timeout=30)
            response.raise_for_status()
            
            # Create local filename
            local_path = os.path.join(self.local_images_dir, filename)
            
            # Save image locally
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved image locally: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading/saving image: {str(e)}")
            return None
    
    def create_seo_filename(self, heading_text: str, counter: int) -> str:
        """Create SEO-friendly filename from heading text."""
        # Clean the heading text
        clean_text = re.sub(r'[^\w\s-]', '', heading_text.lower())
        clean_text = re.sub(r'[-\s]+', '-', clean_text)
        clean_text = clean_text.strip('-')
        
        # Limit length for SEO
        if len(clean_text) > 50:
            clean_text = clean_text[:50].rsplit('-', 1)[0]
        
        return f"{clean_text}-{counter}.jpg"
    
    def upload_image_to_wordpress(self, image_path: str, wp_creds) -> Optional[str]:
        """Upload image to WordPress and return the URL."""
        try:
            # WordPress media upload endpoint
            upload_url = f"{wp_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/media"
            
            # Read the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare the file upload
            files = {
                'file': (os.path.basename(image_path), image_data, 'image/jpeg')
            }
            
            # WordPress authentication
            auth = (wp_creds.username, wp_creds.applicationPassword)
            
            # Upload to WordPress
            response = requests.post(upload_url, files=files, auth=auth, timeout=30)
            response.raise_for_status()
            
            upload_result = response.json()
            wp_image_url = upload_result.get('source_url')
            
            if wp_image_url:
                logger.info(f"Successfully uploaded image to WordPress: {wp_image_url}")
                return wp_image_url
            else:
                logger.error("WordPress upload succeeded but no URL returned")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading image to WordPress: {str(e)}")
            return None

class MarkdownBlogGenerator(BaseGenerator):
    """Enhanced blog generator that outputs Markdown and saves locally."""
    
    def __init__(self):
        super().__init__()
        self.image_generator = EnhancedImageGenerator()
        self.content_dir = "/Users/aditya/Desktop/backend/generated_content"
        self.images_per_headings = 2  # Add image every 2 headings
        
        # Create content directory if it doesn't exist
        os.makedirs(self.content_dir, exist_ok=True)
    
    def generate_section_content(self, section: Dict, job: ContentJob) -> str:
        """Generate content for a section in Markdown format."""
        try:
            # Build context from section details
            section_context = f"Title: {section.get('title', 'Untitled')}"
            
            if section.get('description'):
                section_context += f"\nDescription: {section['description']}"
            
            if section.get('key_points'):
                section_context += f"\nKey Points to Cover: {', '.join(section['key_points'])}"
            
            if section.get('keywords_to_include'):
                section_context += f"\nKeywords to Include: {', '.join(section['keywords_to_include'])}"
            
            prompt = f"""
            Generate a comprehensive section for a blog post about "{job.title}".
            
            Section Details:
            {section_context}
            
            Article Context:
            - Main Keyword: {job.mainKeyword}
            - Related Keywords: {job.related_keywords}
            - Tone: {job.toneOfVoice}
            - Audience: {job.audienceType}
            
            Requirements:
            - Output in PURE MARKDOWN format only
            - Use ## for the main section heading
            - Use ### for subsections if needed
            - Include bullet points and numbered lists where appropriate
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Naturally incorporate the keywords provided
            - Make it comprehensive and informative
            - Length: 400-600 words
            
            Do not include any HTML, Gutenberg blocks, or other formatting.
            Only pure Markdown syntax.
            """
            
            response = self.openai_client.generate_text(prompt)
            
            # Clean up the response to ensure pure Markdown
            content = response.strip()
            
            # Remove any HTML tags if present
            content = re.sub(r'<[^>]+>', '', content)
            
            # Ensure proper markdown formatting
            content = self.clean_markdown(content)
            
            logger.info(f"Generated Markdown content for section: {section.get('title')}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating section content: {str(e)}")
            return f"## {section.get('title', 'Error')}\n\nContent generation failed for this section.\n\n"
    
    def clean_markdown(self, content: str) -> str:
        """Clean and standardize Markdown content."""
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Ensure proper spacing after headers
        content = re.sub(r'^(#{1,6})\s*(.+)$', r'\1 \2', content, flags=re.MULTILINE)
        
        # Ensure proper list formatting
        content = re.sub(r'^\s*-\s*', '- ', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\*\s*', '- ', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def extract_headings(self, content: str) -> List[str]:
        """Extract all headings from Markdown content."""
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []
        
        for match in re.finditer(heading_pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2)
            headings.append({
                'level': level,
                'title': title,
                'full': match.group(0)
            })
        
        return headings
    
    def add_images_to_markdown(self, content: str, job: ContentJob) -> str:
        """Add images to Markdown content every 2 headings."""
        try:
            # Get WordPress credentials for image upload
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                logger.error("WordPress credentials not found, cannot upload images")
                return content
            
            headings = self.extract_headings(content)
            
            if not headings:
                logger.warning("No headings found in content")
                return content
            
            # Process headings and add images
            content_lines = content.split('\n')
            modified_content = []
            heading_count = 0
            
            for line in content_lines:
                modified_content.append(line)
                
                # Check if this line is a heading
                if re.match(r'^#{1,6}\s+', line):
                    heading_count += 1
                    
                    # Add image every 2 headings
                    if heading_count % self.images_per_headings == 0:
                        # Generate search query from heading
                        heading_text = re.sub(r'^#{1,6}\s+', '', line)
                        search_query = f"{job.mainKeyword} {heading_text}"
                        
                        # Find image
                        image_info = self.image_generator.find_image(search_query)
                        
                        if image_info:
                            # Create SEO-friendly filename
                            seo_filename = self.image_generator.create_seo_filename(heading_text, heading_count)
                            
                            # Generate custom image with heading
                            local_path = self.image_generator.generate_custom_image(image_info, heading_text, seo_filename)
                            
                            if local_path:
                                # Upload to WordPress
                                wp_image_url = self.image_generator.upload_image_to_wordpress(local_path, wp_creds)
                                
                                if wp_image_url:
                                    # Add Markdown image syntax with WordPress URL
                                    modified_content.append("")  # Empty line for spacing
                                    modified_content.append(f"![{image_info['alt']}]({wp_image_url})")
                                    modified_content.append("")  # Empty line for spacing
                                    
                                    logger.info(f"Added WordPress image after heading {heading_count}: {seo_filename}")
                                else:
                                    # Fallback to local path if WordPress upload fails
                                    modified_content.append("")  # Empty line for spacing
                                    modified_content.append(f"![{image_info['alt']}](images/{seo_filename})")
                                    modified_content.append("")  # Empty line for spacing
                                    
                                    logger.warning(f"WordPress upload failed, using local image: {seo_filename}")
                            else:
                                logger.error(f"Failed to generate/download image for heading: {heading_text}")
            
            return '\n'.join(modified_content)
            
        except Exception as e:
            logger.error(f"Error adding images to Markdown: {str(e)}")
            return content
    
    def save_markdown_locally(self, content: str, job: ContentJob) -> str:
        """Save Markdown content locally."""
        try:
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', job.title)
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{safe_title}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            
            filepath = os.path.join(self.content_dir, filename)
            
            # Add metadata header
            metadata = f"""---
title: {job.title}
keyword: {job.mainKeyword}
related_keywords: {job.related_keywords}
tone: {job.toneOfVoice}
audience: {job.audienceType}
generated_at: {datetime.now().isoformat()}
---

"""
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(metadata + content)
            
            logger.info(f"Saved Markdown content locally: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving Markdown locally: {str(e)}")
            return None
    
    def generate_blog_post(self, job: ContentJob) -> str:
        """Generate complete blog post in Markdown format."""
        try:
            logger.info(f"Generating Markdown blog post for job {job.id}: {job.title}")
            
            # Parse the outline
            chapters = self.parse_outline(job.Outline)
            
            # Start with content - NO H1 title as WordPress uses post title as H1
            content = ""  # Remove H1 title generation
            
            # Generate introduction
            intro_prompt = f"""
            Write an engaging introduction for a blog post titled "{job.title}".
            
            Requirements:
            - Output in PURE MARKDOWN format
            - Start directly with the introduction paragraph (no H1 title)
            - Make it engaging and informative
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Include the main keyword: {job.mainKeyword}
            - 150-200 words
            - Hook the reader and set expectations
            """
            
            introduction = self.openai_client.generate_text(intro_prompt)
            content += self.clean_markdown(introduction) + "\n\n"
            
            # Generate main content sections
            for chapter in chapters:
                section_content = self.generate_section_content(chapter, job)
                content += section_content + "\n\n"
            
            # Generate conclusion
            conclusion_prompt = f"""
            Write a conclusion for a blog post titled "{job.title}".
            
            Requirements:
            - Output in PURE MARKDOWN format
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Summarize key points
            - Include a call-to-action
            - 100-150 words
            """
            
            conclusion = self.openai_client.generate_text(conclusion_prompt)
            content += "## Conclusion\n\n" + self.clean_markdown(conclusion) + "\n\n"
            
            # Add images to content
            content = self.add_images_to_markdown(content, job)
            
            # Save locally
            local_path = self.save_markdown_locally(content, job)
            
            logger.info(f"Successfully generated Markdown blog post for job {job.id}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating Markdown blog post for job {job.id}: {str(e)}")
            raise Exception(f"Error generating blog post: {str(e)}")
    
    def post_to_wordpress(self, job: ContentJob, content: str) -> Dict[str, Any]:
        """Convert Markdown to WordPress and post."""
        try:
            # Get WordPress credentials
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                raise Exception(f"WordPress credentials not found for job {job.id}")
            
            # Convert Markdown to HTML for WordPress
            html_content = self.markdown_to_html(content)
            
            # Create WordPress client
            wp_client = WordPressClient(
                site_url=wp_creds.siteUrl,
                username=wp_creds.username,
                app_password=wp_creds.applicationPassword
            )
            
            # Post content
            result = wp_client.post_content(
                title=job.title,
                content=html_content,
                status="draft"  # Always post as draft for review
            )
            
            logger.info(f"Successfully posted job {job.id} to WordPress. Post ID: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Error posting job {job.id} to WordPress: {str(e)}")
            raise Exception(f"Error posting to WordPress: {str(e)}")
    
    def markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML for WordPress."""
        try:
            # Simple Markdown to HTML conversion
            html = markdown_content
            
            # Convert headers
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
            
            # Convert lists
            html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
            
            # Convert paragraphs
            paragraphs = html.split('\n\n')
            html_paragraphs = []
            
            for para in paragraphs:
                para = para.strip()
                if para and not para.startswith('<'):
                    html_paragraphs.append(f'<p>{para}</p>')
                else:
                    html_paragraphs.append(para)
            
            html = '\n\n'.join(html_paragraphs)
            
            # Convert images
            html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', html)
            
            return html
            
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML: {str(e)}")
            return markdown_content
    
    def parse_outline(self, outline_json: str) -> List[Dict]:
        """Parse the outline JSON and return sections."""
        try:
            if not outline_json:
                return []
            
            outline = json.loads(outline_json)
            
            # Handle new format with 'sections'
            if 'sections' in outline:
                sections = []
                for section in outline['sections']:
                    # Skip introduction and conclusion as we handle them separately
                    if section.get('title', '').lower() in ['introduction', 'conclusion', 'conclusion: embracing the wisdom of sacred cats']:
                        continue
                    
                    sections.append({
                        'title': section.get('title', 'Untitled'),
                        'description': section.get('description', ''),
                        'key_points': section.get('key_points', []),
                        'keywords_to_include': section.get('keywords_to_include', []),
                        'headingTag': 'h2'
                    })
                logger.info(f"Parsed {len(sections)} sections from outline (excluding intro/conclusion)")
                return sections
            
            # Handle old format with 'chapters'
            elif 'chapters' in outline:
                return outline['chapters']
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing outline JSON: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error processing outline: {str(e)}")
            return []

def main():
    """Main entry point."""
    try:
        # Ensure we have the required environment variables
        required_keys = ['OPENAI_API_KEY']
        for key in required_keys:
            if not os.getenv(key):
                logger.error(f"{key} environment variable not set")
                return
        
        # Check for at least one image API key
        image_apis = ['PEXELS_API_KEY', 'PIXABAY_API_KEY', 'UNSPLASH_ACCESS_KEY']
        if not any(os.getenv(key) for key in image_apis):
            logger.warning("No image API keys found. Image generation will use fallback images.")
        
        # Create and run the Markdown blog generator
        generator = MarkdownBlogGenerator()
        generator.run(max_jobs=1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
