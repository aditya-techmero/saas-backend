# Semantic Keyword Generation for Content Automation

This folder contains the semantic keyword generation functionality that has been integrated into the content automation system.

## 🎯 Overview

The semantic keyword generation system generates 200 relevant semantic keywords for SEO optimization based on:
- Main keyword
- Related keywords
- Content title
- User context

## 📁 Files Structure

### Core Files
- `content_automation_with_seo.py` - Main automation script with semantic keyword generation
- `manage_semantic_keywords.py` - Utility to manage keywords for existing jobs
- `test_semantic_keywords_simple.py` - Simple test without database dependency

### Blog-AI Integration
- `app/blog-AI/src/seo/semantic_keywords.py` - Core semantic keyword generation module
- `app/blog-AI/src/types/seo.py` - Updated with SemanticKeywords type

### Database Integration
- `app/models.py` - Updated ContentJob model with semantic keyword fields
- `app/main.py` - Updated API endpoints with new fields

## 🚀 Features

### 1. Semantic Keyword Generation
- Generates 200 targeted keywords categorized as:
  - **Primary keywords** (20-30): Variations of the main keyword
  - **Secondary keywords** (40-50): Closely related terms
  - **Long-tail keywords** (60-70): Specific phrases and questions
  - **Related keywords** (50-60): Contextually relevant terms

### 2. SEO Optimization
- Focuses on semantic relevance and search intent
- Includes variations, synonyms, and related terms
- Considers different search intents (informational, transactional, navigational)
- Includes question-based keywords for featured snippets

### 3. Database Integration
- Stores keywords in `semantic_keywords` (full categorized structure)
- Stores top keywords in `semantic_keywords_2` (first 100 keywords)
- Automatically updates during content automation process

## 📊 Database Schema

The `ContentJob` model has been updated with these fields:
```sql
semantic_keywords: JSON     -- Full categorized keyword structure
semantic_keywords_2: JSON   -- First 100 keywords for quick access
outline_prompt: TEXT        -- Custom prompt for outline generation
output_prompt: TEXT         -- Custom prompt for content generation
```

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
pip3 install openai python-dotenv sqlalchemy psycopg2-binary requests
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://username:password@localhost/database_name
```

### 3. Test the System
```bash
# Simple test without database
python3 test_semantic_keywords_simple.py

# Full test with database (requires database setup)
python3 test_semantic_keywords.py
```

## 🎮 Usage

### 1. Automatic Generation (Recommended)
The semantic keywords are automatically generated when running the main automation:
```bash
python3 content_automation_with_seo.py
```

### 2. Manual Generation for Existing Jobs
```bash
# Generate keywords for a specific job
python3 manage_semantic_keywords.py --job-id 1 --update

# Generate keywords for all jobs without them
python3 manage_semantic_keywords.py --update-all --limit 5

# View keywords for a job
python3 manage_semantic_keywords.py --job-id 1 --show
```

### 3. API Integration
The semantic keywords are included in the API responses:
```json
{
  "semantic_keywords": {
    "primary_keywords": ["python web development", "python web apps"],
    "secondary_keywords": ["django framework", "flask framework"],
    "long_tail_keywords": ["how to build web applications with python"],
    "related_keywords": ["REST API development", "database integration"],
    "total_count": 200
  },
  "semantic_keywords_2": ["python web development", "python web apps", ...]
}
```

## 🔍 Example Output

For a job with:
- **Main keyword**: "python web development"
- **Related keywords**: "django, flask, python frameworks"
- **Title**: "The Ultimate Guide to Python Web Development"

The system generates:
- **Primary keywords**: python web development, python web applications, web development with python, python for web development, python web programming
- **Secondary keywords**: django framework, flask framework, python web frameworks, web development frameworks, python backend development
- **Long-tail keywords**: how to build web applications with python, best python framework for web development, python web development tutorial for beginners
- **Related keywords**: REST API development, database integration, web security, deployment strategies

## 🔄 Integration with Content Automation

The semantic keyword generation is integrated into the content automation workflow:

1. **Job Processing**: When a content job is processed, keywords are generated first
2. **Content Generation**: The generated keywords can be used to enhance content quality
3. **SEO Optimization**: Keywords are stored for future reference and optimization
4. **WordPress Publishing**: Keywords can be used as tags when publishing to WordPress

## 🎯 Benefits

1. **Improved SEO**: Semantic keywords help search engines understand content context
2. **Better Rankings**: Long-tail keywords target specific user queries
3. **Content Quality**: Keywords guide content creation for better relevance
4. **User Intent**: Different keyword types address various search intents
5. **Scalability**: Automated generation for large content volumes

## 🔧 Customization

### Adjust Keyword Count
```python
# In manage_semantic_keywords.py or automation script
keywords = generate_semantic_keywords_for_job(job, target_count=300)
```

### Modify Categories
Edit the distribution in `semantic_keywords.py`:
```python
# Aim for approximately:
# - 30-40 primary keywords
# - 50-60 secondary keywords
# - 80-90 long-tail keywords
# - 60-70 related keywords
```

### Custom Prompts
The system supports custom prompts for outline and content generation:
```python
job.outline_prompt = "Create an outline for advanced Python developers..."
job.output_prompt = "Write technical content for {outline}..."
```

## 📈 Performance Notes

- **Generation time**: ~10-30 seconds per job (depends on OpenAI API response)
- **Token usage**: ~1000-2000 tokens per job
- **Database storage**: ~5-10KB per job for keyword data
- **Batch processing**: Recommended for large numbers of jobs

## 🐛 Troubleshooting

### Common Issues
1. **OpenAI API errors**: Check API key and rate limits
2. **Database connection**: Verify DATABASE_URL in .env
3. **Import errors**: Ensure all dependencies are installed
4. **JSON parsing**: The system has fallback parsing for malformed responses

### Debug Mode
Enable debug logging in the automation script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 Next Steps

1. **A/B Testing**: Test different keyword strategies
2. **Analytics Integration**: Track keyword performance
3. **Content Quality**: Use keywords to improve content relevance
4. **SEO Monitoring**: Track ranking improvements
5. **Automation Enhancement**: Further optimize the generation process

The semantic keyword generation system is now ready for production use and will significantly enhance the SEO performance of your automated content!
