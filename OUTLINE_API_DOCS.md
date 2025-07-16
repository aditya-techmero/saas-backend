# Outline API Documentation

## Overview
This document describes the new outline management functionality for the content management system. The system now supports creating, updating, and retrieving structured outlines for content jobs with comprehensive validation.

## Features

### 1. **Optional Outline Creation**
- Content jobs can now be created with or without an outline
- If an outline is provided during job creation, it's validated against the full schema
- If no outline is provided, the job status remains "pending" for later outline generation

### 2. **Structured Outline Schema**
- Comprehensive JSON schema with strict validation
- Ensures all required fields are present and not empty
- Validates data types, lengths, and business logic rules

### 3. **Outline Update Endpoint**
- Dedicated PUT endpoint for updating job outlines
- Full schema validation with detailed error messages
- User permission checks and business logic validation

## API Endpoints

### Create Job (Modified)
```
POST /create-job
```

**Changes:**
- `Outline` field is now optional in the request body
- If outline is provided, it's validated against `OutlineSchema`
- Job status is set to "outlined" if valid outline is provided, "pending" otherwise

### Update Job Outline
```
PUT /jobs/{job_id}/outline
```

**Request Body:**
```json
{
  "outline": {
    "title": "Blog Post Title",
    "meta_description": "SEO-optimized meta description (120-160 characters)",
    "main_keyword": "primary keyword",
    "target_audience": "target audience",
    "content_format": "blog post",
    "tone_of_voice": "professional",
    "estimated_word_count": 2000,
    "sections": [
      {
        "section_number": 1,
        "title": "Introduction",
        "estimated_words": 300,
        "description": "Section description",
        "key_points": ["Point 1", "Point 2"],
        "keywords_to_include": ["keyword1", "keyword2"]
      }
    ],
    "seo_keywords": {
      "primary_keywords": ["primary1", "primary2"],
      "secondary_keywords": ["secondary1", "secondary2"],
      "long_tail_keywords": ["long tail phrase 1"]
    },
    "call_to_action": "Compelling call to action",
    "faq_suggestions": [
      {
        "question": "Question?",
        "answer_preview": "Answer preview"
      }
    ],
    "internal_linking_opportunities": ["Link 1", "Link 2"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Outline updated successfully",
  "job_id": 123,
  "updated_at": "2025-07-16T12:00:00.000Z",
  "outline": { /* full outline object */ }
}
```

### Get Job Outline
```
GET /jobs/{job_id}/outline
```

**Response:**
```json
{
  "job_id": 123,
  "title": "Job Title",
  "status": "outlined",
  "has_outline": true,
  "outline": { /* full outline object */ },
  "created_at": "2025-07-16T12:00:00.000Z"
}
```

## Schema Validation

### Required Fields
All outline objects must include these required fields:
- `title` (1-300 characters)
- `meta_description` (120-160 characters)
- `main_keyword` (1-100 characters)
- `target_audience` (1-100 characters)
- `content_format` (1-50 characters)
- `tone_of_voice` (1-50 characters)
- `estimated_word_count` (300-10,000)
- `sections` (2-15 sections)
- `seo_keywords` (with required sub-fields)
- `call_to_action` (1-500 characters)
- `faq_suggestions` (array, can be empty)
- `internal_linking_opportunities` (array, can be empty)

### Section Validation
Each section must have:
- `section_number` (sequential, starting from 1)
- `title` (1-200 characters)
- `estimated_words` (1-5,000)
- `description` (1-1,000 characters)
- `key_points` (1-10 items, each non-empty)
- `keywords_to_include` (0-20 items)

### SEO Keywords Validation
The `seo_keywords` object must contain:
- `primary_keywords` (1-50 items, required)
- `secondary_keywords` (0-100 items)
- `long_tail_keywords` (0-100 items)

### Business Logic Validation
- Section numbers must be unique and sequential
- Total estimated words should be within 20% of the overall target
- All required string fields cannot be empty
- Meta description must be between 120-160 characters for SEO

## Error Handling

### Validation Errors (422)
```json
{
  "detail": "Validation error: [specific error message]"
}
```

### Permission Errors (404)
```json
{
  "detail": "Content job not found or you don't have permission to access it"
}
```

### Business Logic Errors (400)
```json
{
  "detail": "Cannot update outline for completed jobs"
}
```

### Word Count Validation Error (400)
```json
{
  "detail": "Section word counts (2500) don't match estimated total (2000). Difference should be within 20%."
}
```

## Example Usage

### Creating a Job with Outline
```python
import requests

outline_data = {
    "title": "Complete Python Guide",
    "meta_description": "Learn Python programming with this comprehensive guide covering basics, advanced topics, and real-world applications.",
    "main_keyword": "python programming",
    "target_audience": "beginners",
    "content_format": "tutorial",
    "tone_of_voice": "educational",
    "estimated_word_count": 1500,
    "sections": [
        {
            "section_number": 1,
            "title": "Introduction to Python",
            "estimated_words": 300,
            "description": "Getting started with Python basics",
            "key_points": ["Python syntax", "Variables", "Data types"],
            "keywords_to_include": ["python basics", "syntax"]
        },
        {
            "section_number": 2,
            "title": "Advanced Python Concepts",
            "estimated_words": 800,
            "description": "Deep dive into advanced Python features",
            "key_points": ["Object-oriented programming", "Decorators", "Generators"],
            "keywords_to_include": ["python oop", "decorators"]
        },
        {
            "section_number": 3,
            "title": "Conclusion",
            "estimated_words": 400,
            "description": "Summary and next steps",
            "key_points": ["Key takeaways", "Further learning"],
            "keywords_to_include": ["python learning", "next steps"]
        }
    ],
    "seo_keywords": {
        "primary_keywords": ["python programming", "learn python"],
        "secondary_keywords": ["python tutorial", "python guide"],
        "long_tail_keywords": ["how to learn python programming"]
    },
    "call_to_action": "Start your Python journey today!",
    "faq_suggestions": [
        {
            "question": "How long does it take to learn Python?",
            "answer_preview": "With consistent practice, you can learn Python basics in 2-3 months..."
        }
    ],
    "internal_linking_opportunities": ["Python installation guide", "Python projects"]
}

# Create job with outline
response = requests.post(
    "http://localhost:8000/create-job",
    json={
        "title": "Complete Python Guide",
        "main_keyword": "python programming",
        "related_keywords": "python tutorial, learn python",
        "article_word_count": 1500,
        "article_length": "medium",
        "wordpress_credentials_id": 1,
        "outline_prompt": "Create a comprehensive Python guide",
        "Outline": outline_data
    },
    headers={"Authorization": "Bearer your_token"}
)
```

### Updating an Existing Job's Outline
```python
# Update outline for job ID 123
response = requests.put(
    "http://localhost:8000/jobs/123/outline",
    json={"outline": outline_data},
    headers={"Authorization": "Bearer your_token"}
)
```

## Benefits

1. **Type Safety**: Comprehensive validation prevents invalid data
2. **User Experience**: Clear error messages help users fix issues
3. **SEO Optimization**: Enforces SEO best practices (meta description length, keyword usage)
4. **Flexibility**: Optional outline creation allows for different workflows
5. **Maintainability**: Centralized schema validation makes updates easier

## Migration Notes

- Existing jobs without outlines will continue to work
- The `outline_generation.py` script will still work for automatic outline generation
- New validation only applies to manually created/updated outlines
- All existing API endpoints remain backward compatible
