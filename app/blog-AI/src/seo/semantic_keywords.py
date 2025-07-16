"""
Semantic keyword generation functionality for SEO optimization.
"""
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.seo import SemanticKeywords

# OpenAI for backward compatibility
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-3.5-turbo"

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


class SemanticKeywordError(Exception):
    """Exception raised for errors in the semantic keyword generation process."""
    pass


def generate_text_with_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Generate text using OpenAI API - backward compatibility function"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates high-quality SEO content and semantic keywords."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise SemanticKeywordError(f"OpenAI API error: {str(e)}")


def generate_semantic_keywords_for_job(
    job, 
    target_count: int = 200,
    competitor_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate semantic keywords for a content job using existing job data and competitor keywords.
    
    Args:
        job: The content job containing keyword and title information
        target_count: Target number of keywords to generate
        competitor_keywords: List of keywords extracted from competitor URLs
        
    Returns:
        Dictionary containing semantic keywords
    """
    try:
        # Use existing job fields
        main_keyword = job.mainKeyword or ""
        title = job.title or ""
        
        # Parse related keywords
        related_keywords = []
        if job.related_keywords:
            if isinstance(job.related_keywords, str):
                related_keywords = [kw.strip() for kw in job.related_keywords.split(',')]
            elif isinstance(job.related_keywords, list):
                related_keywords = job.related_keywords
        
        related_keywords_str = ", ".join(related_keywords) if related_keywords else "None provided"
        
        # Add competitor keywords to the context
        competitor_context = ""
        if competitor_keywords and len(competitor_keywords) > 0:
            competitor_context = f"""
Competitor Keywords (extracted from competitor analysis):
{", ".join(competitor_keywords[:50])}  # Limit to first 50 to avoid token limits

Please incorporate relevant competitor keywords into your semantic keyword generation, but focus on the main topic and avoid keyword stuffing.
"""
        
        # Create prompt for semantic keyword generation
        prompt = f"""
Generate {target_count} semantic keywords for SEO optimization based on the following information:

Main Keyword: {main_keyword}
Related Keywords: {related_keywords_str}
Title: {title}

{competitor_context}

Please generate a comprehensive list of semantic keywords that includes:
1. Primary keywords (variations of the main keyword)
2. Secondary keywords (closely related terms)
3. Long-tail keywords (specific phrases and questions)
4. Related keywords (contextually relevant terms)

Requirements:
- Focus on semantic relevance and search intent
- Include variations, synonyms, and related terms
- Consider different search intents (informational, transactional, navigational)
- Include question-based keywords
- Ensure keywords are relevant to the topic and title
- Incorporate insights from competitor analysis where relevant

Format the response as a JSON object with the following structure:
{{
    "primary_keywords": ["keyword1", "keyword2", ...],
    "secondary_keywords": ["keyword1", "keyword2", ...],
    "long_tail_keywords": ["long phrase 1", "long phrase 2", ...],
    "related_keywords": ["related term 1", "related term 2", ...],
    "competitor_inspired_keywords": ["keyword1", "keyword2", ...]
}}

Aim for approximately:
- 20-30 primary keywords
- 40-50 secondary keywords
- 60-70 long-tail keywords
- 50-60 related keywords
- 10-20 competitor-inspired keywords (if competitor data is available)

Generate high-quality, semantically relevant keywords that will improve SEO performance.
"""
        
        # Generate keywords using OpenAI
        response = generate_text_with_openai(prompt)
        
        # Parse the response
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                keywords_data = json.loads(json_str)
                
                # Validate required keys
                required_keys = ['primary_keywords', 'secondary_keywords', 'long_tail_keywords', 'related_keywords']
                for key in required_keys:
                    if key not in keywords_data:
                        keywords_data[key] = []
                
                # Handle competitor keywords if not present
                if 'competitor_inspired_keywords' not in keywords_data:
                    keywords_data['competitor_inspired_keywords'] = []
                
                # Calculate total count
                total_count = sum(len(keywords_data[key]) for key in keywords_data if isinstance(keywords_data[key], list))
                keywords_data['total_count'] = total_count
                
                # Add metadata
                keywords_data['generated_at'] = datetime.now().isoformat()
                keywords_data['competitor_keywords_used'] = len(competitor_keywords) if competitor_keywords else 0
                
                print(f"✅ Generated {total_count} semantic keywords for job {job.id}")
                return keywords_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            # Fallback: return basic structure
            print(f"⚠️ Could not parse JSON response for job {job.id}, using fallback")
            return {
                "primary_keywords": [main_keyword] if main_keyword else [],
                "secondary_keywords": related_keywords,
                "long_tail_keywords": [],
                "related_keywords": [],
                "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
                "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
                "generated_at": datetime.now().isoformat(),
                "competitor_keywords_used": len(competitor_keywords) if competitor_keywords else 0
            }
        
    except Exception as e:
        print(f"❌ Error generating semantic keywords for job {job.id}: {str(e)}")
        # Return basic structure with error info
        return {
            "primary_keywords": [main_keyword] if main_keyword else [],
            "secondary_keywords": related_keywords,
            "long_tail_keywords": [],
            "related_keywords": [],
            "competitor_inspired_keywords": competitor_keywords[:20] if competitor_keywords else [],
            "total_count": len([main_keyword] + related_keywords + (competitor_keywords[:20] if competitor_keywords else [])),
            "generated_at": datetime.now().isoformat(),
            "competitor_keywords_used": len(competitor_keywords) if competitor_keywords else 0,
            "error": str(e)
        }


def generate_semantic_keywords(
    main_keyword: str,
    related_keywords: List[str],
    title: str,
    content: Optional[str] = None,
    target_count: int = 200,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> SemanticKeywords:
    """
    Generate semantic keywords for SEO optimization.
    
    Args:
        main_keyword: The primary keyword for the content.
        related_keywords: List of related keywords provided by the user.
        title: The title of the content.
        content: Optional content to analyze for additional context.
        target_count: Target number of keywords to generate (default: 200).
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        SemanticKeywords object containing categorized keywords.
        
    Raises:
        SemanticKeywordError: If an error occurs during keyword generation.
    """
    if not provider:
        raise SemanticKeywordError("LLM provider is required for semantic keyword generation")
    
    options = options or GenerationOptions()
    
    try:
        # Create prompt for semantic keyword generation
        prompt = _create_semantic_keyword_prompt(
            main_keyword=main_keyword,
            related_keywords=related_keywords,
            title=title,
            content=content,
            target_count=target_count
        )
        
        # Generate keywords using LLM
        response = generate_text(prompt, provider, options)
        
        # Parse the response to extract keywords
        keywords = _parse_keyword_response(response)
        
        # Validate and categorize keywords
        semantic_keywords = _categorize_keywords(
            keywords=keywords,
            main_keyword=main_keyword,
            related_keywords=related_keywords,
            target_count=target_count
        )
        
        return semantic_keywords
        
    except Exception as e:
        raise SemanticKeywordError(f"Failed to generate semantic keywords: {str(e)}")


def _create_semantic_keyword_prompt(
    main_keyword: str,
    related_keywords: List[str],
    title: str,
    content: Optional[str] = None,
    target_count: int = 200
) -> str:
    """Create a prompt for semantic keyword generation."""
    
    related_keywords_str = ", ".join(related_keywords) if related_keywords else "None provided"
    content_context = f"\n\nContent Context:\n{content[:500]}..." if content else ""
    
    prompt = f"""
Generate {target_count} semantic keywords for SEO optimization based on the following information:

Main Keyword: {main_keyword}
Related Keywords: {related_keywords_str}
Title: {title}{content_context}

Please generate a comprehensive list of semantic keywords that includes:
1. Primary keywords (variations of the main keyword)
2. Secondary keywords (closely related terms)
3. Long-tail keywords (specific phrases and questions)
4. Related keywords (contextually relevant terms)

Requirements:
- Focus on semantic relevance and search intent
- Include variations, synonyms, and related terms
- Consider different search intents (informational, transactional, navigational)
- Include question-based keywords
- Ensure keywords are relevant to the topic and title

Format the response as a JSON object with the following structure:
{{
    "primary_keywords": ["keyword1", "keyword2", ...],
    "secondary_keywords": ["keyword1", "keyword2", ...],
    "long_tail_keywords": ["long phrase 1", "long phrase 2", ...],
    "related_keywords": ["related term 1", "related term 2", ...]
}}

Aim for approximately:
- 20-30% primary keywords
- 25-35% secondary keywords
- 30-40% long-tail keywords
- 15-20% related keywords

Generate high-quality, semantically relevant keywords that will improve SEO performance.
"""
    
    return prompt


def _parse_keyword_response(response: str) -> List[str]:
    """Parse the LLM response to extract keywords."""
    try:
        # Try to find JSON in the response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Extract all keywords from different categories
            all_keywords = []
            for category in ['primary_keywords', 'secondary_keywords', 'long_tail_keywords', 'related_keywords']:
                if category in data and isinstance(data[category], list):
                    all_keywords.extend(data[category])
            
            return [kw.strip() for kw in all_keywords if kw.strip()]
        else:
            # Fallback: split by lines and clean up
            lines = response.split('\n')
            keywords = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('*'):
                    # Remove numbering and bullet points
                    line = line.lstrip('0123456789.-• ')
                    if line:
                        keywords.append(line)
            return keywords
            
    except Exception as e:
        print(f"Warning: Could not parse keyword response: {e}")
        return []


def _categorize_keywords(
    keywords: List[str],
    main_keyword: str,
    related_keywords: List[str],
    target_count: int
) -> SemanticKeywords:
    """Categorize keywords into semantic groups."""
    try:
        # Simple categorization based on keyword characteristics
        primary_keywords = []
        secondary_keywords = []
        long_tail_keywords = []
        related_kws = []
        
        main_keyword_lower = main_keyword.lower()
        related_lower = [kw.lower() for kw in related_keywords]
        
        for keyword in keywords:
            kw_lower = keyword.lower()
            
            # Primary keywords: contain main keyword or are very similar
            if main_keyword_lower in kw_lower or any(word in kw_lower for word in main_keyword_lower.split()):
                primary_keywords.append(keyword)
            # Long-tail keywords: longer phrases (typically 4+ words)
            elif len(keyword.split()) >= 4:
                long_tail_keywords.append(keyword)
            # Secondary keywords: related to provided keywords
            elif any(related_kw in kw_lower for related_kw in related_lower):
                secondary_keywords.append(keyword)
            # Related keywords: everything else
            else:
                related_kws.append(keyword)
        
        return SemanticKeywords(
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            long_tail_keywords=long_tail_keywords,
            related_keywords=related_kws,
            total_count=len(keywords)
        )
        
    except Exception as e:
        # Fallback categorization
        return SemanticKeywords(
            primary_keywords=[main_keyword] if main_keyword else [],
            secondary_keywords=related_keywords,
            long_tail_keywords=[],
            related_keywords=[],
            total_count=len([main_keyword] + related_keywords),
            error=str(e)
        )


def optimize_keywords_for_content(
    keywords: SemanticKeywords,
    content: str,
    target_density: float = 0.02
) -> Dict[str, Any]:
    """
    Optimize keyword placement and density for given content.
    
    Args:
        keywords: Generated semantic keywords.
        content: The content to optimize.
        target_density: Target keyword density (default: 2%).
        
    Returns:
        Dictionary with optimization suggestions.
    """
    try:
        content_lower = content.lower()
        word_count = len(content.split())
        
        optimization_data = {
            "target_density": target_density,
            "word_count": word_count,
            "keyword_analysis": {},
            "suggestions": []
        }
        
        # Analyze each keyword category
        for category, kw_list in [
            ("primary", keywords.primary_keywords),
            ("secondary", keywords.secondary_keywords),
            ("long_tail", keywords.long_tail_keywords),
            ("related", keywords.related_keywords)
        ]:
            category_data = {
                "keywords": [],
                "total_occurrences": 0,
                "density": 0.0
            }
            
            for keyword in kw_list:
                occurrences = content_lower.count(keyword.lower())
                density = (occurrences / word_count) * 100 if word_count > 0 else 0
                
                category_data["keywords"].append({
                    "keyword": keyword,
                    "occurrences": occurrences,
                    "density": density
                })
                category_data["total_occurrences"] += occurrences
            
            category_data["density"] = (category_data["total_occurrences"] / word_count) * 100 if word_count > 0 else 0
            optimization_data["keyword_analysis"][category] = category_data
            
            # Generate suggestions
            if category == "primary" and category_data["density"] < target_density * 100:
                optimization_data["suggestions"].append(
                    f"Consider increasing primary keyword density. Current: {category_data['density']:.2f}%, Target: {target_density * 100:.2f}%"
                )
        
        return optimization_data
        
    except Exception as e:
        return {
            "error": str(e),
            "target_density": target_density,
            "word_count": 0,
            "keyword_analysis": {},
            "suggestions": []
        }
