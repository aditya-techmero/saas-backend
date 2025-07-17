#!/usr/bin/env python3
"""
View Generated Blog Content
Shows the content that was generated and posted to WordPress.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ContentJob, WordPressCredentials
from blog_generation_standalone import BlogGenerator

def main():
    """Show the generated blog content."""
    db = SessionLocal()
    
    try:
        # Get the job that was processed
        job = db.query(ContentJob).filter(ContentJob.id == 21).first()
        if not job:
            print("❌ Job not found")
            return
        
        print(f"📄 Blog Post: {job.title}")
        print("=" * 60)
        
        # Get WordPress credentials
        wp_creds = db.query(WordPressCredentials).filter(
            WordPressCredentials.id == job.wordpress_credentials_id
        ).first()
        
        if wp_creds:
            print(f"🌐 WordPress Site: {wp_creds.siteUrl}")
            print(f"🔗 Edit URL: {wp_creds.siteUrl}/wp-admin/post.php?post=3044&action=edit")
            print(f"🔗 Published URL: {wp_creds.siteUrl}/?p=3044")
            print(f"📁 Local Markdown: generated_content/Sacred-Cats-in-Hindu-Mythology-Divine-Felines-and-Ancient-Wisdom-20250716-172609.md")
            print(f"🖼️  Images Folder: generated_content/images/ (13 images)")
            print("=" * 60)
        
        # Show job details
        print(f"📊 Job Details:")
        print(f"  - Main Keyword: {job.mainKeyword}")
        print(f"  - Tone: {job.toneOfVoice}")
        print(f"  - Audience: {job.audienceType}")
        print(f"  - Article Length: {job.article_length}")
        print(f"  - Related Keywords: {job.related_keywords}")
        print("=" * 60)
        
        # Show outline structure
        if job.Outline:
            try:
                outline = json.loads(job.Outline)
                print(f"📝 Content Structure:")
                if 'chapters' in outline:
                    for i, chapter in enumerate(outline['chapters'], 1):
                        print(f"  {i}. {chapter.get('title', 'Untitled')} ({chapter.get('headingTag', 'h2')})")
                        if 'content' in chapter:
                            for j, section in enumerate(chapter['content'], 1):
                                if isinstance(section, dict):
                                    print(f"     {i}.{j} {section.get('title', 'Untitled')} ({section.get('headingTag', 'h3')})")
                print("=" * 60)
            except:
                print("❌ Could not parse outline")
        
        # Regenerate the content to show what was posted
        print("🔄 Regenerating content to show you what was posted...")
        print("⚠️  Note: This is a fresh generation, so content may vary slightly from what was actually posted")
        print("=" * 60)
        
        generator = BlogGenerator()
        
        # Generate a sample section to show the format
        if job.Outline:
            try:
                chapters = generator.parse_outline(job.Outline)
                if chapters:
                    print("📖 Sample Section Content:")
                    print("-" * 40)
                    
                    # Show the first section
                    section = chapters[0]
                    prompt = generator.build_section_prompt(section, job)
                    
                    print(f"Section: {section.get('title')}")
                    print(f"Prompt Length: {len(prompt)} characters")
                    print("\nContent would be generated here using OpenAI API...")
                    print("Format: WordPress Gutenberg blocks")
                    print("Structure: H2 headings, paragraphs, lists, separators")
                    
            except Exception as e:
                print(f"❌ Error showing content: {e}")
        
        print("\n✅ To see the actual generated content, visit the WordPress edit URL above!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
