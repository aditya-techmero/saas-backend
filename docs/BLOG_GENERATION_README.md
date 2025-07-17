# Blog Generation System

This directory contains the blog generation system that processes approved content jobs and generates complete blog posts using AI.

## Files Overview

### Core Scripts
- `blog_generation_standalone.py` - Main blog generation script with OpenAI integration
- `run_blog_generation.py` - Command-line runner with options for dry-run and max jobs
- `outline_generation.py` - Generates outlines for pending content jobs

### Test Scripts
- `test_blog_generation.py` - Tests basic imports and functionality
- `test_comprehensive_blog.py` - Creates test jobs and validates all components
- `test_blog_imports.py` - Tests blog-AI module imports (deprecated)

### Database & Models
- `app/models.py` - Database models for ContentJob, WordPressCredentials, User
- `app/database.py` - Database connection and session management
- `migrate_database.py` - Database migration script for boolean fields

## Blog Generation Workflow

The blog generation process follows these steps:

1. **Job Selection**: Finds approved content jobs (`status=True` AND `isApproved=True`)
2. **Outline Parsing**: Extracts chapters/sections from the JSON outline
3. **Content Generation**: For each section:
   - Builds a detailed prompt with job parameters
   - Generates content using OpenAI API
   - Formats content as WordPress Gutenberg blocks
4. **Blog Assembly**: Combines all sections:
   - Introduction (generated)
   - Main content sections (from outline)
   - FAQ section (generated)
   - Conclusion (generated)
5. **WordPress Publishing**: Posts the complete blog as a draft

## Usage

### Run Blog Generation
```bash
# Basic usage (process up to 5 jobs)
python3 run_blog_generation.py

# Process specific number of jobs
python3 run_blog_generation.py --max-jobs 10

# Dry run (test without posting to WordPress)
python3 run_blog_generation.py --dry-run

# Verbose logging
python3 run_blog_generation.py --verbose

# Combined options
python3 run_blog_generation.py --max-jobs 3 --dry-run --verbose
```

### Generate Outlines
```bash
# Generate outlines for pending jobs
python3 outline_generation.py
```

### Test the System
```bash
# Test basic functionality
python3 test_blog_generation.py

# Test comprehensive workflow
python3 test_comprehensive_blog.py
```

## Environment Variables

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- Database connection variables (if not using defaults)

## Database Schema

### ContentJob Table
- `id` - Primary key
- `user_id` - Foreign key to users table
- `title` - Blog post title
- `status` - Boolean (False=pending, True=outlined)
- `isApproved` - Boolean (False=not approved, True=approved)
- `Outline` - JSON string containing the blog outline
- `mainKeyword` - Primary keyword for SEO
- `related_keywords` - Related keywords for content
- `toneOfVoice` - Writing tone (friendly, professional, etc.)
- `audienceType` - Target audience (beginners, experts, etc.)
- `article_length` - Content length (short, medium, long)
- `article_word_count` - Target word count
- `contentFormat` - Content format (guide, tutorial, etc.)
- `wordpress_credentials_id` - Foreign key to WordPress credentials

### WordPressCredentials Table
- `id` - Primary key
- `siteUrl` - WordPress site URL
- `username` - WordPress username
- `applicationPassword` - WordPress application password
- `userId` - Foreign key to users table

## Features

### Content Generation
- **Section-by-section processing**: Each outline section is processed individually
- **Intelligent prompting**: Prompts are built with job-specific parameters
- **WordPress formatting**: Content is formatted as Gutenberg blocks
- **SEO optimization**: Natural keyword integration throughout content
- **Structured output**: Introduction, main content, FAQs, and conclusion

### Error Handling
- Comprehensive logging to `blog_generation.log`
- Graceful error handling for API failures
- Database transaction management
- Validation of required fields and credentials

### WordPress Integration
- Posts content as drafts for review
- Proper Gutenberg block formatting
- Support for headings, paragraphs, lists, and separators
- Authentication via application passwords

## Logs

All activity is logged to `blog_generation.log` with the following information:
- Job processing status
- Content generation progress
- WordPress posting results
- Error messages and stack traces

## Content Structure

Generated blog posts follow this structure:

1. **Introduction** (150-200 words)
   - Hook with interesting fact/question
   - Topic introduction with main keyword
   - Preview of content covered
   - Value proposition

2. **Main Content Sections** (from outline)
   - Each section follows the outline structure
   - Includes H2 headings for main sections
   - H3 subheadings for subsections
   - Actionable tips and practical advice
   - Natural keyword integration

3. **FAQ Section** (5-7 questions)
   - Common questions related to the topic
   - Clear, concise answers
   - Related keyword integration

4. **Conclusion** (100-150 words)
   - Summary of key points
   - Actionable next steps
   - Call-to-action or thought-provoking question

## WordPress Block Format

Content is generated in WordPress Gutenberg block format:

```html
<!-- wp:heading {"level":2} -->
<h2>Section Title</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Paragraph content here...</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator -->
<hr class="wp-block-separator"/>
<!-- /wp:separator -->
```

## Customization

### Modifying Content Generation
- Edit prompts in `blog_generation_standalone.py`
- Adjust word counts in `word_count_map`
- Modify section structure in `build_section_prompt()`

### Adding New Content Types
- Extend the `generate_blog_post()` method
- Add new prompt builders for specific content types
- Update WordPress formatting functions

### Integrating New AI Providers
- Add new client classes similar to `OpenAIClient`
- Update the `BlogGenerator` class to support multiple providers
- Add environment variable configuration

## Troubleshooting

### Common Issues
1. **ImportError**: Ensure Python path is correctly set
2. **Database connection error**: Check database configuration
3. **OpenAI API error**: Verify API key and quota
4. **WordPress posting error**: Check credentials and site URL

### Debug Mode
Run with `--verbose` flag to see detailed logging:
```bash
python3 run_blog_generation.py --verbose
```

### Testing
Use `--dry-run` to test without posting to WordPress:
```bash
python3 run_blog_generation.py --dry-run
```
