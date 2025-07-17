#!/usr/bin/env python3
"""
Markdown to HTML Converter
Converts the generated markdown files to clean HTML blocks for WordPress posting.
"""

import re
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class MarkdownToHTMLConverter:
    """Convert Markdown content to WordPress-ready HTML."""
    
    def __init__(self):
        self.content_dir = "/Users/aditya/Desktop/backend/generated_content"
        self.html_dir = "/Users/aditya/Desktop/backend/generated_content/html"
        
        # Create HTML directory if it doesn't exist
        os.makedirs(self.html_dir, exist_ok=True)
    
    def convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown content to clean HTML."""
        html = markdown_content
        
        # Remove metadata (YAML front matter)
        html = re.sub(r'^---\n.*?\n---\n', '', html, flags=re.DOTALL)
        
        # Convert headers - SKIP H1 as WordPress uses post title as H1
        # html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)  # REMOVED H1 conversion
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
        
        # Remove any standalone H1 lines that might exist
        html = re.sub(r'^# .+$\n?', '', html, flags=re.MULTILINE)
        
        # Convert bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Convert images with better formatting
        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" class="wp-image-responsive" style="max-width: 100%; height: auto; margin: 20px 0;" />', html)
        
        # Convert unordered lists
        html = re.sub(r'^\s*[-\*\+]\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Wrap consecutive list items in <ul> tags
        html = re.sub(r'(<li>.*?</li>)(?:\s*\n\s*<li>.*?</li>)*', self._wrap_in_ul, html, flags=re.DOTALL)
        
        # Convert ordered lists
        html = re.sub(r'^\s*\d+\.\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Convert paragraphs
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Skip if it's already an HTML tag
                if not para.startswith('<'):
                    html_paragraphs.append(f'<p>{para}</p>')
                else:
                    html_paragraphs.append(para)
        
        html = '\n\n'.join(html_paragraphs)
        
        # Clean up extra whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
        
        return html.strip()
    
    def _wrap_in_ul(self, match):
        """Wrap consecutive list items in <ul> tags."""
        list_content = match.group(0)
        return f'<ul>\n{list_content}\n</ul>'
    
    def convert_file(self, markdown_file: str) -> str:
        """Convert a markdown file to HTML and save it."""
        try:
            # Read markdown file
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Convert to HTML
            html_content = self.convert_markdown_to_html(markdown_content)
            
            # Create HTML filename
            base_name = os.path.splitext(os.path.basename(markdown_file))[0]
            html_filename = f"{base_name}.html"
            html_filepath = os.path.join(self.html_dir, html_filename)
            
            # Add some basic HTML structure
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WordPress Content</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        p {{
            margin-bottom: 15px;
        }}
        ul {{
            margin-left: 20px;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
            
            # Save HTML file
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            print(f"✅ Converted to HTML: {html_filepath}")
            return html_filepath
            
        except Exception as e:
            print(f"❌ Error converting {markdown_file}: {str(e)}")
            return None
    
    def convert_all_markdown_files(self):
        """Convert all markdown files in the content directory."""
        try:
            markdown_files = [f for f in os.listdir(self.content_dir) if f.endswith('.md')]
            
            if not markdown_files:
                print("No markdown files found to convert.")
                return
            
            print(f"Found {len(markdown_files)} markdown files to convert:")
            
            for md_file in markdown_files:
                md_path = os.path.join(self.content_dir, md_file)
                print(f"Converting: {md_file}")
                self.convert_file(md_path)
            
            print(f"\n✅ All files converted to HTML in: {self.html_dir}")
            
        except Exception as e:
            print(f"❌ Error converting files: {str(e)}")

def main():
    """Main entry point."""
    converter = MarkdownToHTMLConverter()
    converter.convert_all_markdown_files()

if __name__ == "__main__":
    main()
