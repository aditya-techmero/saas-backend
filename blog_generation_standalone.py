#!/usr/bin/env python3
"""
Blog Generation Script
Processes approved content jobs and generates blog posts by creating content for each section of the outline.
"""

import sys
import os
import json
import time
import logging
import requests
import re
from urllib.parse import urljoin
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from requests.auth import HTTPBasicAuth
import concurrent.futures
import threading

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import ContentJob, WordPressCredentials, User
from seo_content_enhancer import SEOContentEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logger/blog_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BlogGenerationError(Exception):
    """Exception raised for errors in the blog generation process."""
    pass

class OpenAIClient:
    """OpenAI client for text generation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text using OpenAI API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise BlogGenerationError(f"OpenAI API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise BlogGenerationError(f"Error generating text: {str(e)}")

class WordPressClient:
    """WordPress client for posting content."""
    
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        
    def post_content(self, title: str, content: str, status: str = "draft", meta_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Post content to WordPress with optional metadata."""
        try:
            # Prepare the post data
            post_data = {
                'title': title,
                'content': content,
                'status': status,
                'format': 'standard'
            }
            
            # Add meta data if provided
            if meta_data:
                post_data['meta'] = meta_data
            
            # Make the request
            response = requests.post(
                f"{self.api_url}/posts",
                json=post_data,
                auth=HTTPBasicAuth(self.username, self.app_password),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Successfully posted to WordPress. Post ID: {result.get('id')}")
                
                # If we have metadata, update the post with additional meta fields
                if meta_data and result.get('id'):
                    self.update_post_metadata(result['id'], meta_data)
                
                return result
            else:
                logger.error(f"WordPress API error: {response.status_code} - {response.text}")
                raise BlogGenerationError(f"WordPress API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error posting to WordPress: {str(e)}")
            raise BlogGenerationError(f"Error posting to WordPress: {str(e)}")
    
    def update_post_metadata(self, post_id: int, meta_data: Dict[str, Any]) -> bool:
        """Update post metadata using WordPress REST API."""
        try:
            # Prepare metadata for WordPress
            wp_meta = {}
            
            # Add meta description (for SEO plugins like Yoast, RankMath, etc.)
            if 'meta_description' in meta_data:
                wp_meta['_yoast_wpseo_metadesc'] = meta_data['meta_description']
                wp_meta['_genesis_description'] = meta_data['meta_description']
                wp_meta['_aioseop_description'] = meta_data['meta_description']
                wp_meta['rank_math_description'] = meta_data['meta_description']
                wp_meta['seo_meta_description'] = meta_data['meta_description']
                
            # Add readability score
            if 'readability_score' in meta_data:
                wp_meta['seo_readability_score'] = meta_data['readability_score']
                wp_meta['flesch_reading_ease'] = meta_data['readability_score']
                
            # Add keyword information
            if 'focus_keyword' in meta_data:
                wp_meta['_yoast_wpseo_focuskw'] = meta_data['focus_keyword']
                wp_meta['rank_math_focus_keyword'] = meta_data['focus_keyword']
                wp_meta['seo_focus_keyword'] = meta_data['focus_keyword']
                
            # Add content analysis
            if 'content_analysis' in meta_data:
                wp_meta['seo_content_analysis'] = json.dumps(meta_data['content_analysis'])
                
            # Add external links count
            if 'external_links_count' in meta_data:
                wp_meta['seo_external_links_count'] = meta_data['external_links_count']
                
            # Add word count
            if 'word_count' in meta_data:
                wp_meta['seo_word_count'] = meta_data['word_count']
                
            # Update the post with metadata
            if wp_meta:
                update_data = {'meta': wp_meta}
                
                response = requests.post(
                    f"{self.api_url}/posts/{post_id}",
                    json=update_data,
                    auth=HTTPBasicAuth(self.username, self.app_password),
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully updated metadata for post ID: {post_id}")
                    logger.info(f"Updated meta fields: {list(wp_meta.keys())}")
                    return True
                else:
                    logger.warning(f"Failed to update metadata: {response.status_code} - {response.text}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error updating post metadata: {str(e)}")
            return False

class ImageGenerator:
    """Handles image generation and insertion for blog posts."""
    
    def __init__(self, pixabay_api_key: str = None, featured_image_service_url: str = "http://localhost:8001"):
        self.pixabay_api_key = pixabay_api_key or os.getenv('PIXABAY_API_KEY')
        self.featured_image_service_url = featured_image_service_url
        
    def search_pixabay_image(self, query: str) -> Optional[str]:
        """Search for an image on Pixabay and return the URL."""
        if not self.pixabay_api_key:
            logger.warning("Pixabay API key not set, skipping image search")
            return None
            
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
                # Get the first image's large URL
                return data['hits'][0]['largeImageURL']
            
            logger.warning(f"No images found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching Pixabay: {str(e)}")
            return None
    
    def generate_featured_image(self, image_url: str, title: str) -> Optional[str]:
        """Generate a featured image using the featured-image-generator service."""
        try:
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
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # The service returns the image as binary data
                # We need to upload this to WordPress and get the URL
                return self.upload_image_to_wordpress(response.content, f"{title}-featured.webp")
            else:
                logger.error(f"Featured image generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating featured image: {str(e)}")
            return None
    
    def upload_image_to_wordpress(self, image_data: bytes, filename: str, wp_creds=None) -> Optional[str]:
        """Upload image to WordPress and return the URL."""
        if not wp_creds:
            logger.error("WordPress credentials not provided for image upload")
            return None
            
        try:
            # WordPress media upload endpoint
            upload_url = f"{wp_creds.siteUrl.rstrip('/')}/wp-json/wp/v2/media"
            
            # Prepare the file upload
            files = {
                'file': (filename, image_data, 'image/webp')
            }
            
            headers = {
                'Authorization': f'Basic {self._get_basic_auth(wp_creds.username, wp_creds.applicationPassword)}'
            }
            
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('source_url')
            
        except Exception as e:
            logger.error(f"Error uploading image to WordPress: {str(e)}")
            return None
    
    def _get_basic_auth(self, username: str, password: str) -> str:
        """Generate basic auth header."""
        import base64
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode()).decode()
    
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

class BlogGenerator:
    """Main blog generation class."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.openai_client = OpenAIClient(os.getenv('OPENAI_API_KEY'))
        self.image_generator = ImageGenerator()
        self.seo_enhancer = SEOContentEnhancer()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_approved_jobs(self, limit: int = 5) -> List[ContentJob]:
        """Get approved content jobs that need blog generation."""
        try:
            jobs = self.db.query(ContentJob).filter(
                and_(
                    ContentJob.status == True,  # Outlined jobs
                    ContentJob.isApproved == True,  # Approved jobs
                    ContentJob.Outline.isnot(None)  # Has outline
                )
            ).limit(limit).all()
            
            logger.info(f"Found {len(jobs)} approved jobs ready for blog generation")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching approved jobs: {str(e)}")
            raise BlogGenerationError(f"Error fetching approved jobs: {str(e)}")
    
    def parse_outline(self, outline_json: str) -> List[Dict[str, Any]]:
        """Parse the outline JSON to extract sections."""
        try:
            outline = json.loads(outline_json)
            
            # Extract chapters/sections from the outline
            chapters = []
            if 'chapters' in outline:
                chapters = outline['chapters']
            elif 'content' in outline and 'chapters' in outline['content']:
                chapters = outline['content']['chapters']
            
            logger.info(f"Parsed {len(chapters)} chapters from outline")
            return chapters
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing outline JSON: {str(e)}")
            raise BlogGenerationError(f"Error parsing outline JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing outline: {str(e)}")
            raise BlogGenerationError(f"Error processing outline: {str(e)}")
    
    def generate_section_content_threaded(self, section: Dict[str, Any], job: ContentJob, section_index: int) -> tuple[int, str]:
        """Generate content for a specific section with threading support."""
        try:
            # Extract section information
            section_id = section.get('id', '')
            section_title = section.get('title', '')
            section_content = section.get('content', [])
            heading_tag = section.get('headingTag', 'h2')
            
            # Build the content generation prompt
            prompt = self.build_section_prompt(section, job)
            
            # Generate content using OpenAI
            generated_content = self.openai_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Enhance content for readability
            generated_content = self.seo_enhancer.enhance_content_readability(generated_content)
            
            # Add external links
            content_category = self.seo_enhancer.determine_content_category(job.title, job.mainKeyword)
            generated_content = self.seo_enhancer.add_external_links(generated_content, job.mainKeyword, content_category)
            
            # Calculate readability score
            readability_score = self.seo_enhancer.calculate_readability_score(generated_content)
            readability_feedback = self.seo_enhancer.get_readability_feedback(readability_score)
            
            # Format the content as WordPress blocks
            formatted_content = self.format_as_wordpress_blocks(
                generated_content, section_title, heading_tag
            )
            
            logger.info(f"Generated content for section {section_index + 1}: {section_title} - Readability: {readability_score:.1f} ({readability_feedback})")
            return (section_index, formatted_content)
            
        except Exception as e:
            logger.error(f"Error generating section content for section {section_index + 1}: {str(e)}")
            return (section_index, f'<!-- wp:heading {{"level":2}} -->\n<h2>{section.get("title", "Error")}</h2>\n<!-- /wp:heading -->\n\n<!-- wp:paragraph -->\n<p>Content generation failed for this section.</p>\n<!-- /wp:paragraph -->\n\n')

    def generate_section_content(self, section: Dict[str, Any], job: ContentJob) -> str:
        """Generate content for a specific section."""
        try:
            # Extract section information
            section_id = section.get('id', '')
            section_title = section.get('title', '')
            section_content = section.get('content', [])
            heading_tag = section.get('headingTag', 'h2')
            
            # Build the content generation prompt
            prompt = self.build_section_prompt(section, job)
            
            # Generate content using OpenAI
            generated_content = self.openai_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Enhance content for readability
            generated_content = self.seo_enhancer.enhance_content_readability(generated_content)
            
            # Add external links
            content_category = self.seo_enhancer.determine_content_category(job.title, job.mainKeyword)
            generated_content = self.seo_enhancer.add_external_links(generated_content, job.mainKeyword, content_category)
            
            # Calculate readability score
            readability_score = self.seo_enhancer.calculate_readability_score(generated_content)
            readability_feedback = self.seo_enhancer.get_readability_feedback(readability_score)
            
            # Format the content as WordPress blocks
            formatted_content = self.format_as_wordpress_blocks(
                generated_content, section_title, heading_tag
            )
            
            logger.info(f"Generated content for section: {section_title} - Readability: {readability_score:.1f} ({readability_feedback})")
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error generating section content: {str(e)}")
            raise BlogGenerationError(f"Error generating section content: {str(e)}")

    def generate_sections_parallel(self, chapters: List[Dict], job: ContentJob, max_workers: int = 3) -> List[str]:
        """Generate all sections in parallel using ThreadPoolExecutor."""
        try:
            logger.info(f"Starting parallel generation of {len(chapters)} sections with {max_workers} workers")
            
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all section generation tasks
                future_to_section = {
                    executor.submit(self.generate_section_content_threaded, chapter, job, i): i
                    for i, chapter in enumerate(chapters)
                }
                
                # Collect results as they complete
                results = {}
                for future in concurrent.futures.as_completed(future_to_section):
                    section_index, content = future.result()
                    results[section_index] = content
                    logger.info(f"✅ Completed section {section_index + 1}/{len(chapters)}")
            
            # Sort results by original order and return
            sorted_results = [results[i] for i in sorted(results.keys())]
            logger.info(f"✅ All {len(chapters)} sections generated successfully")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error in parallel section generation: {str(e)}")
            # Fallback to sequential processing
            logger.info("Falling back to sequential processing...")
            return self.generate_sections_sequential(chapters, job)
    
    def generate_sections_sequential(self, chapters: List[Dict], job: ContentJob) -> List[str]:
        """Fallback method for sequential section generation."""
        results = []
        for i, chapter in enumerate(chapters):
            _, content = self.generate_section_content_threaded(chapter, job, i)
            results.append(content)
        return results
    
    def build_section_prompt(self, section: Dict[str, Any], job: ContentJob) -> str:
        """Build the prompt for generating section content."""
        section_title = section.get('title', '')
        section_content = section.get('content', [])
        heading_tag = section.get('headingTag', 'h2')
        
        # Get job parameters
        main_keyword = job.mainKeyword or ''
        related_keywords = job.related_keywords or ''
        tone_of_voice = job.toneOfVoice or 'informative'
        audience_type = job.audienceType or 'general'
        article_length = job.article_length or 'medium'
        
        # Word count based on article length
        word_count_map = {
            'short': '400-600',
            'medium': '800-1200', 
            'long': '1500-2000'
        }
        section_word_count = word_count_map.get(article_length, '800-1200')
        
        # Get SEO-enhanced prompt
        seo_prompts = self.seo_enhancer.get_enhanced_prompts(None)  # Will create a generic job-like object
        
        # Create a temporary job-like object for the prompt
        temp_job = type('obj', (object,), {
            'title': f"Section: {section_title}",
            'mainKeyword': main_keyword,
            'related_keywords': related_keywords,
            'toneOfVoice': tone_of_voice,
            'audienceType': audience_type
        })()
        
        enhanced_prompts = self.seo_enhancer.get_enhanced_prompts(temp_job)
        
        # Build the section outline
        section_outline = ""
        if section_content:
            for item in section_content:
                if isinstance(item, dict):
                    item_title = item.get('title', '')
                    item_tag = item.get('headingTag', 'h3')
                    section_outline += f"- {item_title} ({item_tag})\n"
                elif isinstance(item, str):
                    section_outline += f"- {item}\n"
        
        prompt = f"""Write comprehensive content for the following section:

## Section Title: {section_title}

## Content Requirements:
- **Tone of Voice**: {tone_of_voice}
- **Audience Type**: {audience_type}
- **Word Count**: {section_word_count} words
- **Heading Level**: {heading_tag}

## Keywords to Include:
- **Main Keyword**: {main_keyword}
- **Related Keywords**: {related_keywords}

## Section Structure to Follow:
{section_outline}

## SEO & READABILITY REQUIREMENTS:
1. **Readability**: Use simple, clear language. Prefer short sentences (15-20 words max).
2. **Paragraph Length**: Keep paragraphs short (3-4 sentences max, 50-75 words).
3. **Transition Words**: Use transition words for better flow (however, moreover, furthermore, etc.).
4. **Active Voice**: Use active voice (subject + verb + object). Avoid passive constructions.
5. **External Links**: Include 1-2 references to authoritative sources.
6. **Flesch Reading Ease**: Target 60+ score (use shorter sentences, common words).
7. **Keyword Density**: Use main keyword naturally 2-3 times per 200 words.

## Writing Guidelines:
1. Write in a conversational, engaging tone
2. Use short paragraphs (3-4 lines maximum)
3. Include actionable tips and practical advice
4. Use bullet points and numbered lists where appropriate
5. Include relevant examples and case studies
6. End with a "Pro Tip" or actionable takeaway
7. Naturally incorporate the keywords without stuffing

## Format Requirements:
- Use proper HTML tags for structure
- Bold important phrases and keywords
- Include subheadings (h3) for better readability
- Add transitions between paragraphs

Write the content now:"""
        
        return prompt
    
    def format_as_wordpress_blocks(self, content: str, title: str, heading_tag: str) -> str:
        """Format content as WordPress Gutenberg blocks."""
        # Start with the heading block
        heading_level = heading_tag[1:] if heading_tag.startswith('h') else '2'
        formatted_content = f'<!-- wp:heading {{"level":{heading_level}}} -->\n<{heading_tag}>{title}</{heading_tag}>\n<!-- /wp:heading -->\n\n'
        
        # Add the generated content
        # Split content into paragraphs and wrap in paragraph blocks
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Check if it's a list
                if paragraph.startswith('- ') or paragraph.startswith('* ') or paragraph.startswith('1. '):
                    # Format as list block
                    formatted_content += '<!-- wp:list -->\n<ul>\n'
                    items = paragraph.split('\n')
                    for item in items:
                        item = item.strip()
                        if item.startswith('- ') or item.startswith('* '):
                            item = item[2:]  # Remove list marker
                            formatted_content += f'<li>{item}</li>\n'
                        elif item.startswith(('1. ', '2. ', '3. ')):
                            item = item[3:]  # Remove numbered list marker
                            formatted_content += f'<li>{item}</li>\n'
                    formatted_content += '</ul>\n<!-- /wp:list -->\n\n'
                else:
                    # Format as paragraph block
                    formatted_content += f'<!-- wp:paragraph -->\n<p>{paragraph}</p>\n<!-- /wp:paragraph -->\n\n'
        
        # Add separator
        formatted_content += '<!-- wp:separator -->\n<hr class="wp-block-separator"/>\n<!-- /wp:separator -->\n\n'
        
        return formatted_content
    
    def generate_introduction(self, job: ContentJob) -> str:
        """Generate introduction section."""
        # Get SEO-enhanced prompts
        seo_prompts = self.seo_enhancer.get_enhanced_prompts(job)
        
        # Generate introduction content
        generated_content = self.openai_client.generate_text(
            prompt=seo_prompts['introduction'],
            temperature=0.7,
            max_tokens=500
        )
        
        # Enhance for readability
        generated_content = self.seo_enhancer.enhance_content_readability(generated_content)
        
        # Add external links
        content_category = self.seo_enhancer.determine_content_category(job.title, job.mainKeyword)
        generated_content = self.seo_enhancer.add_external_links(generated_content, job.mainKeyword, content_category)
        
        # Convert markdown to HTML and format as WordPress blocks
        html_content = self.convert_markdown_to_html(generated_content)
        
        # Format as WordPress blocks
        formatted_content = '<!-- wp:paragraph -->\n<p>' + html_content.replace('\n\n', '</p>\n<!-- /wp:paragraph -->\n\n<!-- wp:paragraph -->\n<p>') + '</p>\n<!-- /wp:paragraph -->\n\n'
        
        return formatted_content
    
    def convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert basic markdown to HTML."""
        # Convert basic markdown formatting
        content = markdown_content
        
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        
        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        
        # Links
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)
        
        return content
    
    def generate_conclusion(self, job: ContentJob) -> str:
        """Generate conclusion section."""
        # Get SEO-enhanced prompts
        seo_prompts = self.seo_enhancer.get_enhanced_prompts(job)
        
        # Generate conclusion content
        generated_content = self.openai_client.generate_text(
            prompt=seo_prompts['conclusion'],
            temperature=0.7,
            max_tokens=400
        )
        
        # Enhance for readability
        generated_content = self.seo_enhancer.enhance_content_readability(generated_content)
        
        # Add external links
        content_category = self.seo_enhancer.determine_content_category(job.title, job.mainKeyword)
        generated_content = self.seo_enhancer.add_external_links(generated_content, job.mainKeyword, content_category)
        
        # Convert markdown to HTML
        html_content = self.convert_markdown_to_html(generated_content)
        
        # Format as WordPress blocks
        formatted_content = '<!-- wp:heading {"level":2} -->\n<h2>Conclusion</h2>\n<!-- /wp:heading -->\n\n'
        formatted_content += '<!-- wp:paragraph -->\n<p>' + html_content.replace('\n\n', '</p>\n<!-- /wp:paragraph -->\n\n<!-- wp:paragraph -->\n<p>') + '</p>\n<!-- /wp:paragraph -->\n\n'
        
        return formatted_content
    
    def generate_faqs(self, job: ContentJob) -> str:
        """Generate FAQ section."""
        prompt = f"""Create 5-7 frequently asked questions and answers for a blog post about "{job.title}".

## Requirements:
- Address common questions related to: {job.mainKeyword}
- Provide clear, concise answers (2-3 sentences each)
- Use a helpful tone: {job.toneOfVoice or 'informative'}
- Include related keywords naturally: {job.related_keywords}
- Format each FAQ as Question (H3) followed by Answer (paragraph)

## Structure:
For each FAQ:
1. Question as H3 heading
2. Clear, actionable answer
3. Include relevant keywords naturally

Write 5-7 FAQs now:"""
        
        generated_content = self.openai_client.generate_text(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Format as WordPress blocks
        formatted_content = '<!-- wp:heading {"level":2} -->\n<h2>Frequently Asked Questions</h2>\n<!-- /wp:heading -->\n\n'
        
        # Split the content into Q&A pairs and format them
        lines = generated_content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('Q:') or line.startswith('**Q') or line.endswith('?'):
                    # This is a question
                    question = line.replace('Q:', '').replace('**', '').strip()
                    formatted_content += f'<!-- wp:heading {{"level":3}} -->\n<h3>{question}</h3>\n<!-- /wp:heading -->\n\n'
                elif line.startswith('A:') or line.startswith('**A'):
                    # This is an answer
                    answer = line.replace('A:', '').replace('**', '').strip()
                    formatted_content += f'<!-- wp:paragraph -->\n<p>{answer}</p>\n<!-- /wp:paragraph -->\n\n'
                elif line and not line.startswith('#'):
                    # Regular paragraph
                    formatted_content += f'<!-- wp:paragraph -->\n<p>{line}</p>\n<!-- /wp:paragraph -->\n\n'
        
        return formatted_content
    
    def generate_blog_post(self, job: ContentJob, max_workers: int = 3) -> str:
        """Generate complete blog post for a job with parallel processing."""
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
            conclusion = self.generate_conclusion(job, main_content)
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
            raise BlogGenerationError(f"Error generating blog post: {str(e)}")
    
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
                # Generate featured image
                featured_image_url = self.image_generator.generate_featured_image(image_url, job.title)
                
                if featured_image_url:
                    # Upload featured image to WordPress
                    try:
                        # Download the featured image
                        response = requests.get(featured_image_url)
                        if response.status_code == 200:
                            uploaded_url = self.image_generator.upload_image_to_wordpress(
                                response.content, 
                                f"{job.title}-featured.webp", 
                                wp_creds
                            )
                            if uploaded_url:
                                alt_text = f"Featured image for {job.title}"
                                content = self.image_generator.insert_image_after_first_h2(content, uploaded_url, alt_text)
                                logger.info(f"Successfully added featured image to blog post")
                                return content
                    except Exception as e:
                        logger.error(f"Error uploading featured image: {str(e)}")
                
                # If featured image upload fails, try with original image
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        uploaded_url = self.image_generator.upload_image_to_wordpress(
                            response.content, 
                            f"{job.title}-image.jpg", 
                            wp_creds
                        )
                        if uploaded_url:
                            alt_text = f"Image related to {job.mainKeyword or job.title}"
                            content = self.image_generator.insert_image_after_first_h2(content, uploaded_url, alt_text)
                            logger.info(f"Added original image to blog post")
                            return content
                except Exception as e:
                    logger.error(f"Error uploading original image: {str(e)}")
            else:
                logger.warning(f"No suitable image found for: {search_query}")
                
            return content
            
        except Exception as e:
            logger.error(f"Error adding images to content: {str(e)}")
            # Return original content if image processing fails
            return content
    
    def post_to_wordpress(self, job: ContentJob, content: str) -> Dict[str, Any]:
        """Post content to WordPress with SEO metadata."""
        try:
            # Get WordPress credentials
            wp_creds = self.db.query(WordPressCredentials).filter(
                WordPressCredentials.id == job.wordpress_credentials_id
            ).first()
            
            if not wp_creds:
                logger.error(f"WordPress credentials not found for job {job.id}")
                return {}
            
            # Initialize WordPress client
            wp_client = WordPressClient(
                site_url=wp_creds.siteUrl,
                username=wp_creds.username,
                app_password=wp_creds.applicationPassword
            )
            
            # Prepare SEO metadata
            logger.info("📊 Preparing SEO metadata for WordPress...")
            metadata = self.seo_enhancer.prepare_wordpress_metadata(
                title=job.title,
                keyword=job.mainKeyword,
                content=content
            )
            
            # Log metadata being sent
            logger.info(f"📝 Sending metadata to WordPress:")
            logger.info(f"  • Meta Description: {metadata.get('meta_description', 'Not set')}")
            logger.info(f"  • Focus Keyword: {metadata.get('focus_keyword', 'Not set')}")
            logger.info(f"  • Readability Score: {metadata.get('readability_score', 'Not calculated')}")
            logger.info(f"  • Word Count: {metadata.get('word_count', 'Not counted')}")
            logger.info(f"  • External Links: {metadata.get('external_links_count', 0)}")
            
            # Post to WordPress with metadata
            result = wp_client.post_content(
                title=job.title,
                content=content,
                status="draft",
                meta_data=metadata
            )
            
            if result:
                logger.info(f"✅ Successfully posted to WordPress with SEO metadata. Post ID: {result.get('id')}")
                
                # Update job with WordPress post ID
                job.wordpress_post_id = result.get('id')
                self.db.commit()
                
                return result
            else:
                logger.error("❌ Failed to post to WordPress")
                return {}
                
        except Exception as e:
            logger.error(f"Error posting to WordPress: {str(e)}")
            return {}

    def process_job(self, job: ContentJob) -> bool:
        """Process a single content job."""
        try:
            logger.info(f"Processing job {job.id}: {job.title}")
            
            # Generate blog post content
            content = self.generate_blog_post(job)
            
            # Post to WordPress
            wp_result = self.post_to_wordpress(job, content)
            
            # Log success
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
            raise BlogGenerationError(f"Error in blog generation process: {str(e)}")

def main():
    """Main entry point."""
    try:
        # Ensure we have the required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY environment variable not set")
            return
        
        # Create and run the blog generator
        generator = BlogGenerator()
        generator.run(max_jobs=5)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
