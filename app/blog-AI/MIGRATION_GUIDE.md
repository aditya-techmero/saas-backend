# Migration Guide: Moving to Blog-AI Structure

This guide explains how to transition from the old file structure to the new organized blog-AI folder structure.

## What Changed

All automation, content generation, and competitor analysis functionality has been moved to the `app/blog-AI/` folder for better organization.

## File Migration

### Old Structure → New Structure

```
# Old files (root directory)
content_automation_with_seo.py          → app/blog-AI/src/automation/content_automation.py
manage_semantic_keywords.py             → app/blog-AI/src/automation/manage_keywords.py
test_competitor_scraping.py             → app/blog-AI/src/testing/test_competitor_scraping.py
test_competitor_scraping_simple.py      → app/blog-AI/src/testing/test_competitor_scraping_simple.py
test_semantic_keywords_simple.py        → app/blog-AI/src/testing/test_semantic_keywords_simple.py
create_test_jobs_with_competitors.py    → app/blog-AI/src/testing/create_test_jobs_with_competitors.py

# Documentation
README_COMPETITOR_SCRAPING.md           → app/blog-AI/docs/README_COMPETITOR_SCRAPING.md
COMPETITOR_IMPLEMENTATION_SUMMARY.md    → app/blog-AI/docs/COMPETITOR_IMPLEMENTATION_SUMMARY.md
README_SEMANTIC_KEYWORDS.md             → app/blog-AI/docs/README_SEMANTIC_KEYWORDS.md
SEMANTIC_KEYWORDS_IMPLEMENTATION.md     → app/blog-AI/docs/SEMANTIC_KEYWORDS_IMPLEMENTATION.md
```

### New Files Created

```
app/blog-AI/
├── main.py                              # New main entry point
├── README.md                            # New comprehensive README
├── src/
│   ├── competitor_analysis/
│   │   ├── __init__.py                  # New module
│   │   └── scraper.py                   # New competitor scraping module
│   ├── automation/
│   │   ├── __init__.py                  # New module
│   │   ├── content_automation.py        # Migrated and updated
│   │   └── manage_keywords.py           # Migrated and updated
│   └── testing/
│       ├── __init__.py                  # New module
│       └── ... (migrated test files)
└── docs/
    └── ... (migrated documentation)
```

## Updated Commands

### Old Commands → New Commands

```bash
# Old way
python content_automation_with_seo.py
python manage_semantic_keywords.py list

# New way (option 1: main entry point)
cd app/blog-AI
python main.py automate
python main.py keywords list

# New way (option 2: direct script)
python app/blog-AI/src/automation/content_automation.py
python app/blog-AI/src/automation/manage_keywords.py list
```

### Complete Command Migration

```bash
# Content Automation
# Old: python content_automation_with_seo.py
# New: python app/blog-AI/main.py automate

# Keyword Management
# Old: python manage_semantic_keywords.py list
# New: python app/blog-AI/main.py keywords list

# Old: python manage_semantic_keywords.py preview --job-id 1 --competitors
# New: python app/blog-AI/main.py keywords preview --job-id 1 --competitors

# Old: python manage_semantic_keywords.py update --job-id 1 --competitors
# New: python app/blog-AI/main.py keywords update --job-id 1 --competitors

# Old: python manage_semantic_keywords.py batch --status approved --competitors
# New: python app/blog-AI/main.py keywords batch --status approved --competitors

# Testing
# Old: python test_competitor_scraping_simple.py
# New: python app/blog-AI/src/testing/test_competitor_scraping_simple.py

# Old: python test_competitor_scraping.py
# New: python app/blog-AI/src/testing/test_competitor_scraping.py

# Old: python create_test_jobs_with_competitors.py
# New: python app/blog-AI/src/testing/create_test_jobs_with_competitors.py
```

## Import Changes

### Updated Import Paths

The new structure uses relative imports within the blog-AI module:

```python
# Old imports (no longer valid)
from app.blog-AI.src.competitor_analysis.scraper import scrape_competitor_keywords

# New imports
from ..competitor_analysis.scraper import scrape_competitor_keywords
from ..seo.semantic_keywords import generate_semantic_keywords_for_job
```

### Backward Compatibility

The system maintains backward compatibility by:
- Keeping the original functions and classes
- Adding new functions to existing modules
- Maintaining the same database structure
- Preserving all existing functionality

## Environment Setup

No changes required to environment variables or configuration files. The system still uses:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here
```

## Testing the Migration

### 1. Test Basic Functionality

```bash
# Test the main entry point
cd app/blog-AI
python main.py keywords list

# Test direct scripts
python src/automation/manage_keywords.py list
```

### 2. Test Competitor Scraping

```bash
# Test with mock data
python src/testing/test_competitor_scraping_simple.py

# Test with real API (optional)
python src/testing/test_competitor_scraping.py
```

### 3. Test Content Automation

```bash
# Create test jobs
python src/testing/create_test_jobs_with_competitors.py

# Run automation
python main.py automate
```

## Benefits of New Structure

### 1. Better Organization
- Clear separation of concerns
- Modular architecture
- Easier to maintain and extend

### 2. Improved Development
- Proper module structure
- Clear import paths
- Better testing organization

### 3. Enhanced Documentation
- Centralized documentation
- Clear usage examples
- Migration guides

### 4. Future-Proofing
- Scalable architecture
- Easy to add new features
- Better integration possibilities

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all `__init__.py` files are present
   - Verify the Python path includes the project root

2. **Path Issues**
   - Use absolute paths when calling from different directories
   - Check current working directory
   - Verify file permissions

3. **API Errors**
   - Ensure environment variables are set
   - Check API key validity
   - Verify network connectivity

### Debug Commands

```bash
# Check file structure
ls -la app/blog-AI/src/

# Test imports
python -c "from app.blog_AI.src.automation.content_automation import main; print('Import successful')"

# Check Python path
python -c "import sys; print(sys.path)"
```

## Cleanup (Optional)

After verifying the new structure works, you can optionally remove the old files:

```bash
# Remove old files (backup first!)
rm content_automation_with_seo.py
rm manage_semantic_keywords.py
rm test_competitor_scraping.py
rm test_competitor_scraping_simple.py
rm test_semantic_keywords_simple.py
rm create_test_jobs_with_competitors.py
rm README_COMPETITOR_SCRAPING.md
rm COMPETITOR_IMPLEMENTATION_SUMMARY.md
rm README_SEMANTIC_KEYWORDS.md
rm SEMANTIC_KEYWORDS_IMPLEMENTATION.md
```

**Note**: Only remove old files after thoroughly testing the new structure!

## Support

If you encounter issues during migration:
1. Check this migration guide
2. Review the main README in `app/blog-AI/README.md`
3. Test individual components separately
4. Verify all dependencies are installed
5. Check the logs for specific error messages
