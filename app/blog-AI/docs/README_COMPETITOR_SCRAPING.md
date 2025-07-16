# Competitor URL Scraping and Keyword Extraction

This document describes the competitor URL scraping functionality that has been added to the content automation system.

## Overview

The system now includes the ability to scrape competitor blog URLs and extract relevant keywords for SEO optimization. This feature enhances the semantic keyword generation process by incorporating insights from competitor content analysis.

## Features

1. **Competitor URL Scraping**: Automatically scrapes competitor URLs using an external API
2. **Keyword Extraction**: Uses AI to extract relevant keywords from competitor content
3. **Integration**: Seamlessly integrates with existing semantic keyword generation
4. **Storage**: Stores competitor keywords in the existing database fields

## How It Works

### 1. URL Scraping
- Uses the external scraping API: `http://157.245.210.116:3000/api/scrape`
- Scrapes both `competitor_url_1` and `competitor_url_2` fields if available
- Extracts title, content, and other relevant data from competitor blogs

### 2. Keyword Extraction
- Analyzes scraped content using OpenAI API
- Extracts 20-40 high-quality keywords per URL
- Focuses on SEO-relevant terms and phrases
- Removes duplicates and cleans the keyword list

### 3. Integration with Semantic Keywords
- Competitor keywords are incorporated into the main semantic keyword generation
- Stored separately in the `semantic_keywords_2` field for reference
- Used to enhance the overall keyword strategy

## Database Storage

The competitor keywords are stored in existing database fields:

- **`semantic_keywords`**: Enhanced with competitor insights
- **`semantic_keywords_2`**: Stores raw competitor data with metadata

```json
{
  "competitor_keywords": ["keyword1", "keyword2", ...],
  "extracted_at": "2024-01-15T10:30:00",
  "source_urls": ["https://competitor1.com/blog", "https://competitor2.com/blog"]
}
```

## Usage

### 1. Automatic Processing

When running the main automation script:

```bash
python content_automation_with_seo.py
```

The system will automatically:
1. Check for competitor URLs in each approved job
2. Scrape the URLs if available
3. Extract keywords from the scraped content
4. Generate enhanced semantic keywords
5. Store everything in the database

### 2. Manual Keyword Management

Use the management script to manually process competitor keywords:

```bash
# Preview keywords with competitor analysis
python manage_semantic_keywords.py preview --job-id 1 --competitors

# Update keywords for a specific job with competitor analysis
python manage_semantic_keywords.py update --job-id 1 --competitors

# Batch update all approved jobs with competitor analysis
python manage_semantic_keywords.py batch --status approved --competitors
```

### 3. Testing

Test the competitor scraping functionality:

```bash
python test_competitor_scraping.py
```

## API Configuration

The scraping functionality uses an external API:

- **URL**: `http://157.245.210.116:3000/api/scrape`
- **Method**: POST
- **Timeout**: 30 seconds
- **Headers**: `Content-Type: application/json`

### Request Format
```json
{
  "url": "https://competitor-blog.com/article"
}
```

### Response Format
```json
{
  "title": "Article Title",
  "content": "Full article content...",
  "url": "https://competitor-blog.com/article",
  "status": "success"
}
```

## Error Handling

The system includes robust error handling:

1. **Network Errors**: Gracefully handles API timeouts and connection issues
2. **Parsing Errors**: Falls back to basic keyword structure if AI parsing fails
3. **Missing URLs**: Skips competitor analysis if no URLs are provided
4. **API Failures**: Continues processing even if scraping fails

## Example Output

### Competitor Keywords Extracted
```
🔍 Found 2 competitor URLs to scrape for job 1
🔍 Scraping competitor URL: https://competitor1.com/blog-post
✅ Successfully scraped https://competitor1.com/blog-post
✅ Extracted 23 keywords from competitor content
🔍 Scraping competitor URL: https://competitor2.com/blog-post
✅ Successfully scraped https://competitor2.com/blog-post
✅ Extracted 31 keywords from competitor content
✅ Total unique keywords extracted from competitors: 45
```

### Enhanced Semantic Keywords
```json
{
  "primary_keywords": ["main keyword", "primary variation", ...],
  "secondary_keywords": ["related term", "secondary phrase", ...],
  "long_tail_keywords": ["specific long phrase", "question based keyword", ...],
  "related_keywords": ["contextual term", "semantic variation", ...],
  "competitor_inspired_keywords": ["competitor term", "industry phrase", ...],
  "total_count": 187,
  "generated_at": "2024-01-15T10:30:00",
  "competitor_keywords_used": 45
}
```

## Performance Considerations

1. **Rate Limiting**: The system processes URLs sequentially to avoid overwhelming the API
2. **Content Truncation**: Large content is truncated to 3000 characters to manage token limits
3. **Timeout Handling**: 30-second timeout for scraping requests
4. **Duplicate Prevention**: Automatically removes duplicate keywords

## Troubleshooting

### Common Issues

1. **API Not Responding**
   - Check API endpoint availability
   - Verify network connectivity
   - Check for rate limiting

2. **No Keywords Extracted**
   - Verify content is being scraped successfully
   - Check OpenAI API key and limits
   - Ensure competitor URLs are accessible

3. **Parsing Errors**
   - System will fall back to basic structure
   - Check logs for specific error messages
   - Verify JSON response format

### Debug Commands

```bash
# Test API connectivity
python test_competitor_scraping.py

# Check specific job data
python manage_semantic_keywords.py preview --job-id 1

# List jobs with competitor URLs
python manage_semantic_keywords.py list
```

## Future Enhancements

Potential improvements for the competitor scraping system:

1. **Caching**: Cache scraped content to avoid repeated API calls
2. **Multiple APIs**: Support for additional scraping services
3. **Content Analysis**: More sophisticated content analysis beyond keywords
4. **Competitor Tracking**: Track competitor content changes over time
5. **Batch Processing**: Optimize for processing multiple URLs in parallel

## Security Considerations

1. **API Security**: Scraping API should implement rate limiting and authentication
2. **Data Privacy**: Ensure compliance with content scraping policies
3. **Error Logging**: Sensitive information should not be logged
4. **Input Validation**: Validate competitor URLs before processing

## Conclusion

The competitor URL scraping functionality significantly enhances the semantic keyword generation process by incorporating real competitor insights. This helps create more comprehensive and competitive SEO strategies for content automation.
