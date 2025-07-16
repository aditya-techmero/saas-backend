"""
SEO module for the blog-AI project.
"""

from .semantic_keywords import generate_semantic_keywords, generate_semantic_keywords_simple, SemanticKeywordError
from .meta_description import generate_meta_description, MetaDescriptionError
from .image_alt_text import generate_image_alt_text
from .structured_data import generate_structured_data

__all__ = [
    'generate_semantic_keywords',
    'generate_semantic_keywords_simple',
    'SemanticKeywordError',
    'generate_meta_description',
    'MetaDescriptionError',
    'generate_image_alt_text',
    'generate_structured_data'
]
