"""
Content outline generation functionality.
"""
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, create_provider_from_env, GenerationOptions
from ..types.planning import OutlineRequest, OutlineResponse, OutlineSection


def generate_content_outline(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    target_audience: str = "general",
    content_type: str = "blog",
    provider_type: str = "openai"
) -> Dict[str, Any]:
    """
    Generate a content outline for the given topic.
    
    Args:
        title: The title of the content
        keywords: List of keywords to include
        num_sections: Number of sections to generate
        target_audience: Target audience for the content
        content_type: Type of content (blog, article, etc.)
        provider_type: LLM provider to use
        
    Returns:
        Dictionary containing the outline structure
    """
    
    keywords_str = ", ".join(keywords) if keywords else ""
    
    prompt = f"""
    Create a detailed content outline for: "{title}"
    
    Requirements:
    - Target audience: {target_audience}
    - Content type: {content_type}
    - Number of main sections: {num_sections}
    - Keywords to include: {keywords_str}
    
    Please provide a structured outline with:
    1. Main sections (H2 level)
    2. Subsections (H3 level) for each main section
    3. Key points to cover in each section
    4. Estimated word count for each section
    
    Format as a clear, hierarchical outline.
    """
    
    try:
        provider = create_provider_from_env(provider_type)
        outline_text = generate_text(prompt, provider, GenerationOptions())
        
        return {
            "title": title,
            "outline": outline_text,
            "sections": num_sections,
            "keywords": keywords or [],
            "target_audience": target_audience,
            "content_type": content_type
        }
    except Exception as e:
        return {
            "title": title,
            "outline": f"Error generating outline: {str(e)}",
            "sections": num_sections,
            "keywords": keywords or [],
            "target_audience": target_audience,
            "content_type": content_type
        }


def generate_content_outline_with_research(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    target_audience: str = "general",
    content_type: str = "blog",
    provider_type: str = "openai"
) -> Dict[str, Any]:
    """
    Generate a content outline with research data.
    
    This is a simplified version that falls back to the basic outline generation
    since we don't have the full research functionality.
    """
    
    # For now, just call the basic outline generation
    # In a full implementation, this would include web research
    outline_data = generate_content_outline(
        title=title,
        keywords=keywords,
        num_sections=num_sections,
        target_audience=target_audience,
        content_type=content_type,
        provider_type=provider_type
    )
    
    # Add research indicator
    outline_data["research_included"] = False
    outline_data["research_note"] = "Research functionality not available in minimal version"
    
    return outline_data
