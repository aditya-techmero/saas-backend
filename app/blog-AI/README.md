# Blog-AI Content Automation System

This is the main automation system for AI-powered content generation, SEO optimization, and competitor analysis.

## Directory Structure

```
blog-AI/
├── main.py                    # Main entry point
├── src/
│   ├── automation/
│   │   ├── content_automation.py    # Main automation script
│   │   └── manage_keywords.py       # Keyword management script
│   ├── competitor_analysis/
│   │   └── scraper.py              # Competitor URL scraping
│   ├── seo/
│   │   └── semantic_keywords.py    # SEO keyword generation
│   ├── testing/
│   │   ├── test_competitor_scraping.py
│   │   ├── test_competitor_scraping_simple.py
│   │   ├── test_semantic_keywords_simple.py
│   │   └── create_test_jobs_with_competitors.py
│   └── ... (other modules)
├── docs/
│   ├── README_COMPETITOR_SCRAPING.md
│   ├── COMPETITOR_IMPLEMENTATION_SUMMARY.md
│   ├── README_SEMANTIC_KEYWORDS.md
│   └── SEMANTIC_KEYWORDS_IMPLEMENTATION.md
```

## Usage

### Main Entry Point

```bash
# Run from the blog-AI directory
cd app/blog-AI

# Run content automation
python main.py automate

# Manage keywords
python main.py keywords list
python main.py keywords preview --job-id 1 --competitors
python main.py keywords update --job-id 1 --competitors
python main.py keywords batch --status approved --competitors
```

### Direct Script Usage

```bash
# Run automation directly
python src/automation/content_automation.py

# Manage keywords directly
python src/automation/manage_keywords.py list
python src/automation/manage_keywords.py preview --job-id 1 --competitors
python src/automation/manage_keywords.py update --job-id 1 --competitors
python src/automation/manage_keywords.py batch --status approved --competitors
```

### Testing

```bash
# Test competitor scraping
python src/testing/test_competitor_scraping_simple.py

# Test with real API
python src/testing/test_competitor_scraping.py

# Test semantic keywords
python src/testing/test_semantic_keywords_simple.py

# Create test jobs
python src/testing/create_test_jobs_with_competitors.py
```

## Features

### 1. Content Automation
- Automated content generation from approved jobs
- Integration with WordPress for publishing
- Semantic keyword generation with SEO optimization
- Competitor analysis and keyword extraction

### 2. Competitor Analysis
- Scrapes competitor URLs using external API
- Extracts relevant keywords using AI
- Integrates competitor insights into keyword generation
- Supports multiple competitor URLs per job

### 3. SEO Optimization
- Generates comprehensive semantic keywords
- Categorizes keywords (primary, secondary, long-tail, related)
- Incorporates competitor insights
- Stores keywords in existing database fields

### 4. Management Tools
- Preview keywords before saving
- Update individual jobs or batch process
- List jobs with keyword status
- Comprehensive error handling

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here
```

### API Configuration

The system uses:
- **OpenAI API**: For content and keyword generation
- **Scraper API**: `http://157.245.210.116:3000/api/scrape` for competitor scraping
- **WordPress API**: For content publishing

## Database Integration

The system uses existing database fields:
- `semantic_keywords`: Enhanced keyword data with competitor insights
- `semantic_keywords_2`: Raw competitor data and metadata
- `competitor_url_1`, `competitor_url_2`: Source URLs for competitor analysis

## Error Handling

The system includes comprehensive error handling:
- Network timeouts and API failures
- JSON parsing errors with fallback structures
- Database transaction safety
- Graceful degradation when competitors URLs fail

## Performance Considerations

- Sequential processing to avoid API rate limits
- Content truncation for token management
- Efficient database queries
- Robust fallback mechanisms

## Security

- Input validation for URLs
- Secure API key management
- Error logging without sensitive data
- Rate limiting compliance

## Future Enhancements

- Caching for improved performance
- Parallel processing capabilities
- Multiple scraping API support
- Advanced content analysis
- Real-time competitor monitoring

## Documentation

See the `docs/` directory for detailed documentation:
- `README_COMPETITOR_SCRAPING.md`: Competitor scraping guide
- `COMPETITOR_IMPLEMENTATION_SUMMARY.md`: Implementation summary
- `README_SEMANTIC_KEYWORDS.md`: Semantic keywords guide
- `SEMANTIC_KEYWORDS_IMPLEMENTATION.md`: Implementation details

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Run test scripts to verify setup
3. Check logs for error messages
4. Validate API keys and configurations
