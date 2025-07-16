"""
Outline generation core functionality.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
from datetime import datetime

from ..text_generation.core import generate_text, create_provider_from_env, GenerationOptions
from ..research.web_researcher import conduct_web_research
from ..types.planning import OutlineRequest, OutlineResponse, OutlineSection


@dataclass
class OutlineParameters:
    """Parameters for outline generation."""
    topic: str
    target_audience: str = "general"
    content_type: str = "blog"  # blog, article, guide, tutorial
    depth: str = "medium"  # basic, medium, detailed
    tone: str = "professional"  # professional, casual, academic, conversational
    max_sections: int = 8
    include_research: bool = True
    include_keywords: bool = True
    output_format: str = "markdown"  # markdown, json, text


class OutlineGenerator:
    """Generates structured content outlines."""
    
    def __init__(self):
        self.provider = create_provider_from_env("openai")
        self.options = GenerationOptions()
    
    def generate_outline(self, params: OutlineParameters) -> OutlineResponse:
        """Generate a structured content outline."""
        
        # Research phase (if enabled)
        research_data = None
        if params.include_research:
            research_data = self._conduct_research(params.topic)
        
        # Generate outline structure
        outline_sections = self._generate_outline_structure(params, research_data)
        
        # Generate keywords (if enabled)
        keywords = []
        if params.include_keywords:
            keywords = self._generate_keywords(params.topic, params.target_audience)
        
        # Create response
        response = OutlineResponse(
            topic=params.topic,
            target_audience=params.target_audience,
            content_type=params.content_type,
            sections=outline_sections,
            keywords=keywords,
            estimated_word_count=self._estimate_word_count(outline_sections),
            generated_at=datetime.now().isoformat()
        )
        
        return response
    
    def _conduct_research(self, topic: str) -> Dict[str, Any]:
        """Conduct web research on the topic."""
        try:
            research_results = conduct_web_research([topic])
            return {
                "sources": research_results.serp_results if hasattr(research_results, 'serp_results') else [],
                "key_points": [result.title for result in research_results.serp_results[:5]] if hasattr(research_results, 'serp_results') else [],
                "trending_topics": []
            }
        except Exception as e:
            print(f"Research failed: {e}")
            return {"sources": [], "key_points": [], "trending_topics": []}
    
    def _generate_outline_structure(self, params: OutlineParameters, research_data: Optional[Dict]) -> List[OutlineSection]:
        """Generate the main outline structure."""
        
        # Create prompt for outline generation
        research_context = ""
        if research_data and research_data.get("key_points"):
            research_context = f"\n\nResearch insights:\n" + "\n".join(research_data["key_points"][:5])
        
        prompt = f"""
        Create a detailed outline for a {params.content_type} about "{params.topic}".
        
        Requirements:
        - Target audience: {params.target_audience}
        - Tone: {params.tone}
        - Depth level: {params.depth}
        - Maximum sections: {params.max_sections}
        {research_context}
        
        Please provide a structured outline with main sections. Format each section as:
        
        ## Section Title
        - Key point 1
        - Key point 2
        - Key point 3
        
        Make sure to include {params.max_sections} main sections that would be appropriate for a {params.content_type} on this topic.
        """
        
        print(f"Generating outline with prompt: {prompt[:200]}...")
        outline_text = generate_text(prompt, self.provider, self.options)
        print(f"Generated outline text: {outline_text[:500]}...")
        
        # Parse the generated outline into structured sections
        sections = self._parse_outline_text(outline_text)
        
        return sections
    
    def _parse_outline_text(self, outline_text: str) -> List[OutlineSection]:
        """Parse generated outline text into structured sections."""
        sections = []
        lines = outline_text.strip().split('\n')
        
        current_section = None
        current_points = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a main section header (starts with ## or #)
            if line.startswith('##') or (line.startswith('#') and not line.startswith('###')):
                # Save previous section if exists
                if current_section:
                    sections.append(OutlineSection(
                        title=current_section,
                        key_points=current_points.copy(),
                        estimated_words=self._estimate_section_words(current_points),
                        description=f"Content covering {current_section.lower()}"
                    ))
                
                # Start new section
                current_section = line.strip('#').strip()
                current_points = []
            
            # Check if this is a numbered section (1. 2. etc.)
            elif line and len(line) > 2 and line[0].isdigit() and line[1] == '.':
                # Save previous section if exists
                if current_section:
                    sections.append(OutlineSection(
                        title=current_section,
                        key_points=current_points.copy(),
                        estimated_words=self._estimate_section_words(current_points),
                        description=f"Content covering {current_section.lower()}"
                    ))
                
                # Start new section
                current_section = line[2:].strip()
                current_points = []
            
            # Check if this is a key point
            elif line.startswith(('-', '*', '•')):
                point = line.lstrip('-*•').strip()
                if point:
                    current_points.append(point)
        
        # Add the last section
        if current_section:
            sections.append(OutlineSection(
                title=current_section,
                key_points=current_points.copy(),
                estimated_words=self._estimate_section_words(current_points),
                description=f"Content covering {current_section.lower()}"
            ))
        
        # If no sections were found, create some default ones
        if not sections:
            print("No sections found in outline text, creating default sections...")
            default_sections = [
                "Introduction",
                "Getting Started",
                "Core Concepts",
                "Implementation",
                "Best Practices",
                "Conclusion"
            ]
            
            for title in default_sections[:6]:  # Limit to 6 default sections
                sections.append(OutlineSection(
                    title=title,
                    key_points=["Key point 1", "Key point 2", "Key point 3"],
                    estimated_words=300,
                    description=f"Content covering {title.lower()}"
                ))
        
        return sections[:8]  # Limit to max sections
    
    def _estimate_section_words(self, key_points: List[str]) -> int:
        """Estimate word count for a section based on key points."""
        base_words = 200  # Base words per section
        point_words = len(key_points) * 100  # Additional words per key point
        return base_words + point_words
    
    def _estimate_word_count(self, sections: List[OutlineSection]) -> int:
        """Estimate total word count for the outline."""
        return sum(section.estimated_words for section in sections)
    
    def _generate_keywords(self, topic: str, target_audience: str) -> List[str]:
        """Generate relevant keywords for the topic."""
        prompt = f"""
        Generate 10-15 relevant keywords for the topic "{topic}" 
        targeting "{target_audience}" audience.
        
        Include:
        - Primary keywords (main topic)
        - Secondary keywords (related topics)
        - Long-tail keywords (specific phrases)
        
        Return only the keywords, one per line.
        """
        
        keywords_text = generate_text(prompt, self.provider, self.options)
        keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
        
        return keywords[:15]  # Limit to 15 keywords
    
    def save_outline(self, outline_response: OutlineResponse, output_path: Optional[str] = None) -> str:
        """Save the outline to a file."""
        if not output_path:
            # Generate filename from topic
            safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in outline_response.topic)
            safe_topic = safe_topic.replace(' ', '_').lower()
            output_path = f"content/outlines/{safe_topic}_outline.md"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Format outline content
        content = self._format_outline_content(outline_response)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _format_outline_content(self, outline: OutlineResponse) -> str:
        """Format outline response into markdown content."""
        content = f"""# Content Outline: {outline.topic}

**Target Audience:** {outline.target_audience}
**Content Type:** {outline.content_type}
**Estimated Word Count:** {outline.estimated_word_count}
**Generated:** {outline.generated_at}

## Keywords
{', '.join(outline.keywords)}

## Outline Structure

"""
        
        for i, section in enumerate(outline.sections, 1):
            content += f"### {i}. {section.title}\n"
            content += f"**Estimated Words:** {section.estimated_words}\n"
            content += f"**Description:** {section.description}\n\n"
            
            if section.key_points:
                content += "**Key Points:**\n"
                for point in section.key_points:
                    content += f"- {point}\n"
                content += "\n"
        
        return content


def main():
    """CLI entry point for outline generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate content outlines")
    parser.add_argument("topic", help="Topic for the outline")
    parser.add_argument("--audience", default="general", help="Target audience")
    parser.add_argument("--type", default="blog", choices=["blog", "article", "guide", "tutorial"], help="Content type")
    parser.add_argument("--depth", default="medium", choices=["basic", "medium", "detailed"], help="Content depth")
    parser.add_argument("--tone", default="professional", choices=["professional", "casual", "academic", "conversational"], help="Content tone")
    parser.add_argument("--max-sections", type=int, default=8, help="Maximum number of sections")
    parser.add_argument("--no-research", action="store_true", help="Skip web research")
    parser.add_argument("--no-keywords", action="store_true", help="Skip keyword generation")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Create parameters
    params = OutlineParameters(
        topic=args.topic,
        target_audience=args.audience,
        content_type=args.type,
        depth=args.depth,
        tone=args.tone,
        max_sections=args.max_sections,
        include_research=not args.no_research,
        include_keywords=not args.no_keywords
    )
    
    # Generate outline
    generator = OutlineGenerator()
    print(f"Generating outline for: {args.topic}")
    
    try:
        outline = generator.generate_outline(params)
        output_path = generator.save_outline(outline, args.output)
        print(f"Outline saved to: {output_path}")
        
        # Print summary
        print(f"\nOutline Summary:")
        print(f"- Sections: {len(outline.sections)}")
        print(f"- Keywords: {len(outline.keywords)}")
        print(f"- Estimated Words: {outline.estimated_word_count}")
        
    except Exception as e:
        print(f"Error generating outline: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
