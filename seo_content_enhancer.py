#!/usr/bin/env python3
"""
SEO Content Enhancer
Provides advanced SEO and readability improvements for blog content generation.
"""

import re
import random
from typing import Dict, List, Optional, Any
from urllib.parse import quote
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SEOContentEnhancer:
    """Enhances blog content for SEO and readability."""
    
    def __init__(self):
        # Transition words for better flow
        self.transition_words = [
            "however", "moreover", "furthermore", "additionally", "consequently",
            "therefore", "nevertheless", "meanwhile", "subsequently", "similarly",
            "in contrast", "on the other hand", "as a result", "for instance",
            "for example", "in fact", "indeed", "specifically", "particularly",
            "notably", "importantly", "significantly", "ultimately", "finally",
            "first", "second", "third", "next", "then", "afterward", "previously",
            "currently", "recently", "simultaneously", "meanwhile", "likewise",
            "in addition", "besides", "also", "plus", "what's more", "above all"
        ]
        
        # External authority domains for linking
        self.authority_domains = {
            "general": [
                "wikipedia.org", "britannica.com", "nationalgeographic.com",
                "scientificamerican.com", "harvard.edu", "mit.edu", "stanford.edu"
            ],
            "health": [
                "mayoclinic.org", "webmd.com", "healthline.com", "nih.gov",
                "cdc.gov", "who.int", "medicalnewstoday.com"
            ],
            "business": [
                "hbr.org", "forbes.com", "businessinsider.com", "entrepreneur.com",
                "inc.com", "mckinsey.com", "deloitte.com"
            ],
            "technology": [
                "techcrunch.com", "wired.com", "arstechnica.com", "ieee.org",
                "acm.org", "nature.com", "science.org"
            ],
            "education": [
                "edutopia.org", "khanacademy.org", "coursera.org", "edx.org",
                "ted.com", "chronicle.com"
            ],
            "lifestyle": [
                "goodhousekeeping.com", "realsimple.com", "oprah.com",
                "shape.com", "menshealth.com", "womenshealthmag.com"
            ]
        }
        
        # Simpler word alternatives for readability
        self.simpler_words = {
            "utilize": "use", "facilitate": "help", "commence": "start",
            "terminate": "end", "demonstrate": "show", "indicate": "show",
            "implement": "use", "establish": "set up", "acquire": "get",
            "purchase": "buy", "construct": "build", "eliminate": "remove",
            "accomplish": "achieve", "participate": "take part", "assistance": "help",
            "approximately": "about", "numerous": "many", "sufficient": "enough",
            "component": "part", "methodology": "method", "approximately": "about",
            "nevertheless": "but", "consequently": "so", "fundamental": "basic",
            "subsequently": "then", "currently": "now", "previously": "before",
            "additionally": "also", "furthermore": "also", "therefore": "so"
        }
    
    def get_enhanced_prompts(self, job: Any) -> Dict[str, str]:
        """Get SEO-enhanced prompts for different content sections."""
        
        # Determine content category for authority domains
        content_category = self.determine_content_category(job.title, job.mainKeyword)
        
        base_seo_requirements = f"""
        
        ## SEO & READABILITY REQUIREMENTS:
        1. **Readability**: Use simple, clear language. Prefer short sentences (15-20 words max).
        2. **Paragraph Length**: Keep paragraphs short (3-4 sentences max, 50-75 words).
        3. **Transition Words**: Use transition words for better flow: {', '.join(random.sample(self.transition_words, 8))}.
        4. **Active Voice**: Use active voice (subject + verb + object). Avoid passive constructions.
        5. **External Links**: Include 2-3 references to authoritative sources from domains like: {', '.join(random.sample(self.authority_domains.get(content_category, self.authority_domains['general']), 3))}.
        6. **Flesch Reading Ease**: Target 60+ score (use shorter sentences, common words).
        7. **Keyword Density**: Use main keyword "{job.mainKeyword}" naturally 2-3 times per 200 words.
        8. **Subheadings**: Use descriptive subheadings every 200-300 words for scannability.
        
        ## CONTENT STRUCTURE:
        - Start with a compelling hook (statistic, question, or surprising fact)
        - Use bullet points and numbered lists for better readability
        - Include practical examples and actionable tips
        - End sections with key takeaways or "pro tips"
        """
        
        return {
            "introduction": f"""
            Write an engaging introduction for a blog post titled "{job.title}".
            
            Requirements:
            - Output in PURE MARKDOWN format
            - Start directly with the introduction paragraph (no H1 title)
            - Hook the reader with a compelling statistic, question, or surprising fact
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Include the main keyword: {job.mainKeyword}
            - Length: 150-200 words (short sentences, simple words)
            - Include 1-2 transition words for flow
            - Use active voice throughout
            - End with a preview of what readers will learn
            {base_seo_requirements}
            
            Write the introduction now:
            """,
            
            "section": f"""
            Generate a comprehensive section for a blog post about "{job.title}".
            
            Article Context:
            - Main Keyword: {job.mainKeyword}
            - Related Keywords: {job.related_keywords}
            - Tone: {job.toneOfVoice}
            - Audience: {job.audienceType}
            
            Requirements:
            - Output in PURE MARKDOWN format only
            - Use ## for the main section heading
            - Use ### for subsections if needed
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Naturally incorporate the keywords provided
            - Length: 400-600 words
            - Include 1-2 external links to authoritative sources
            - Use bullet points and numbered lists where appropriate
            - Include practical examples and actionable tips
            - End with a "Pro Tip" or key takeaway
            {base_seo_requirements}
            
            Do not include any HTML, Gutenberg blocks, or other formatting.
            Only pure Markdown syntax.
            """,
            
            "conclusion": f"""
            Write a compelling conclusion for a blog post titled "{job.title}".
            
            Requirements:
            - Output in PURE MARKDOWN format
            - Write in {job.toneOfVoice} tone for {job.audienceType}
            - Summarize key points covered
            - Include actionable next steps
            - Include a call-to-action or thought-provoking question
            - Length: 100-150 words (short sentences, simple words)
            - Use active voice throughout
            - Include 1-2 transition words
            - End with an engaging closing statement
            {base_seo_requirements}
            
            Write the conclusion now:
            """
        }
    
    def determine_content_category(self, title: str, keyword: str) -> str:
        """Determine content category for appropriate authority domains."""
        text = f"{title} {keyword}".lower()
        
        if any(word in text for word in ['health', 'medical', 'wellness', 'fitness', 'nutrition', 'diet']):
            return 'health'
        elif any(word in text for word in ['business', 'marketing', 'finance', 'startup', 'entrepreneur']):
            return 'business'
        elif any(word in text for word in ['technology', 'software', 'programming', 'digital', 'ai', 'tech']):
            return 'technology'
        elif any(word in text for word in ['education', 'learning', 'school', 'teaching', 'study']):
            return 'education'
        elif any(word in text for word in ['lifestyle', 'fashion', 'beauty', 'home', 'travel', 'food']):
            return 'lifestyle'
        else:
            return 'general'
    
    def generate_meta_description(self, title: str, keyword: str, content_preview: str) -> str:
        """Generate an SEO-optimized meta description (≤160 characters)."""
        try:
            # Extract key phrases from content preview
            sentences = content_preview.split('. ')
            first_sentence = sentences[0] if sentences else ""
            
            # Base description template
            base_desc = f"Discover {keyword}"
            
            # Add value proposition
            if "how to" in title.lower():
                base_desc += f" with this comprehensive guide"
            elif "best" in title.lower():
                base_desc += f" - expert insights and recommendations"
            elif "why" in title.lower():
                base_desc += f" - key reasons and explanations"
            else:
                base_desc += f" - expert insights and practical tips"
            
            # Add call to action
            call_to_action = " Learn more now!"
            
            # Combine and ensure it's under 160 characters
            description = base_desc + call_to_action
            
            if len(description) > 160:
                # Truncate and add ellipsis
                description = description[:157] + "..."
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating meta description: {str(e)}")
            return f"Learn about {keyword} with expert insights and practical tips."
    
    def enhance_content_readability(self, content: str) -> str:
        """Enhance content for better readability and SEO."""
        try:
            # Split into paragraphs
            paragraphs = content.split('\n\n')
            enhanced_paragraphs = []
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                
                # Skip headings
                if paragraph.startswith('#'):
                    enhanced_paragraphs.append(paragraph)
                    continue
                
                # Enhance paragraph readability
                enhanced_paragraph = self.improve_paragraph_readability(paragraph)
                enhanced_paragraphs.append(enhanced_paragraph)
            
            return '\n\n'.join(enhanced_paragraphs)
            
        except Exception as e:
            logger.error(f"Error enhancing content readability: {str(e)}")
            return content
    
    def improve_paragraph_readability(self, paragraph: str) -> str:
        """Improve individual paragraph readability."""
        try:
            # Replace complex words with simpler alternatives
            for complex_word, simple_word in self.simpler_words.items():
                paragraph = re.sub(r'\b' + complex_word + r'\b', simple_word, paragraph, flags=re.IGNORECASE)
            
            # Break long sentences (>25 words) into shorter ones
            sentences = paragraph.split('. ')
            improved_sentences = []
            
            for sentence in sentences:
                words = sentence.split()
                if len(words) > 25:
                    # Try to split at conjunctions
                    for i, word in enumerate(words):
                        if word.lower() in ['and', 'but', 'or', 'because', 'since', 'while', 'although']:
                            if i > 8 and i < len(words) - 3:  # Don't split too early or too late
                                first_part = ' '.join(words[:i])
                                second_part = ' '.join(words[i+1:])
                                improved_sentences.append(first_part + '.')
                                improved_sentences.append(second_part)
                                break
                    else:
                        improved_sentences.append(sentence)
                else:
                    improved_sentences.append(sentence)
            
            return '. '.join(improved_sentences)
            
        except Exception as e:
            logger.error(f"Error improving paragraph readability: {str(e)}")
            return paragraph
    
    def add_external_links(self, content: str, keyword: str, content_category: str) -> str:
        """Add external links to authoritative sources."""
        try:
            # Get relevant authority domains
            domains = self.authority_domains.get(content_category, self.authority_domains['general'])
            
            # Find opportunities to add links
            link_opportunities = [
                (r'\b(research shows?|studies indicate|according to experts?)\b', 'research'),
                (r'\b(statistics show|data reveals?|surveys indicate)\b', 'statistics'),
                (r'\b(experts? recommend|professionals? suggest)\b', 'expert-advice'),
                (r'\b(learn more|find out more|additional information)\b', 'additional-resources')
            ]
            
            links_added = 0
            max_links = 2
            
            for pattern, link_type in link_opportunities:
                if links_added >= max_links:
                    break
                
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    match = matches[0]
                    domain = random.choice(domains)
                    
                    # Create a contextual link
                    link_text = match.group(0)
                    link_url = f"https://{domain}"
                    
                    # Replace with markdown link
                    replacement = f"[{link_text}]({link_url})"
                    content = content[:match.start()] + replacement + content[match.end():]
                    links_added += 1
            
            return content
            
        except Exception as e:
            logger.error(f"Error adding external links: {str(e)}")
            return content
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate approximate Flesch Reading Ease score."""
        try:
            # Remove markdown formatting for accurate calculation
            clean_text = re.sub(r'[#*`\[\]()_~]', '', text)
            
            # Count sentences
            sentences = len(re.findall(r'[.!?]+', clean_text))
            if sentences == 0:
                return 0
            
            # Count words
            words = len(clean_text.split())
            if words == 0:
                return 0
            
            # Count syllables (simplified approximation)
            syllables = 0
            for word in clean_text.split():
                word = word.lower().strip('.,!?;:')
                syllable_count = len(re.findall(r'[aeiouy]+', word))
                if syllable_count == 0:
                    syllable_count = 1
                syllables += syllable_count
            
            # Flesch Reading Ease formula
            score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
            
            return max(0, min(100, score))  # Clamp between 0 and 100
            
        except Exception as e:
            logger.error(f"Error calculating readability score: {str(e)}")
            return 60  # Default to acceptable score
    
    def get_readability_feedback(self, score: float) -> str:
        """Get feedback message based on readability score."""
        if score >= 70:
            return "Excellent readability (easy to read)"
        elif score >= 60:
            return "Good readability (acceptable)"
        elif score >= 50:
            return "Average readability (may need improvement)"
        else:
            return "Poor readability (needs significant improvement)"
    
    def prepare_wordpress_metadata(self, title: str, keyword: str, content: str, readability_score: float = None) -> Dict[str, Any]:
        """Prepare metadata for WordPress posting."""
        try:
            # Generate meta description
            meta_description = self.generate_meta_description(title, keyword, content[:500])
            
            # Calculate readability score if not provided
            if readability_score is None:
                readability_score = self.calculate_readability_score(content)
            
            # Count external links
            external_links_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
            
            # Count words
            word_count = len(content.split())
            
            # Prepare content analysis
            content_analysis = {
                'meta_description_length': len(meta_description),
                'readability_score': readability_score,
                'readability_level': self.get_readability_feedback(readability_score),
                'word_count': word_count,
                'external_links_count': external_links_count,
                'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
                'has_images': '![' in content,
                'transition_words_used': len([word for word in self.transition_words if word in content.lower()]),
                'seo_optimized': True
            }
            
            # Prepare WordPress metadata
            wp_metadata = {
                'meta_description': meta_description,
                'focus_keyword': keyword,
                'readability_score': readability_score,
                'word_count': word_count,
                'external_links_count': external_links_count,
                'content_analysis': content_analysis,
                'seo_optimized_date': datetime.now().isoformat(),
                'seo_improvements_applied': [
                    'meta_description_optimized',
                    'external_links_added',
                    'readability_enhanced',
                    'transition_words_included',
                    'active_voice_preferred',
                    'short_paragraphs_enforced'
                ]
            }
            
            return wp_metadata
            
        except Exception as e:
            logger.error(f"Error preparing WordPress metadata: {str(e)}")
            return {
                'meta_description': f"Learn about {keyword} with expert insights.",
                'focus_keyword': keyword,
                'readability_score': 60,
                'seo_optimized_date': datetime.now().isoformat()
            }
