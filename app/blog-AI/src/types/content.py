"""
Type definitions for content generation.
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class SubTopic:
    """A subtopic within a section."""
    title: str
    content: Optional[str]
    
    def __init__(self, title: str, content: Optional[str] = None):
        self.title = title
        self.content = content


class Section:
    """A section within a blog post."""
    title: str
    subtopics: List[SubTopic]
    
    def __init__(self, title: str, subtopics: List[SubTopic]):
        self.title = title
        self.subtopics = subtopics


class BlogPost:
    """A blog post."""
    title: str
    description: str
    date: str
    image: str
    tags: List[str]
    sections: List[Section]
    
    def __init__(
        self,
        title: str,
        description: str,
        sections: List[Section],
        date: Optional[str] = None,
        image: str = "/images/blog/default.jpg",
        tags: Optional[List[str]] = None
    ):
        self.title = title
        self.description = description
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.image = image
        self.tags = tags or ["AI", "technology"]
        self.sections = sections


class FAQ:
    """A frequently asked question."""
    question: str
    answer: str
    
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer


ContentType = Literal["blog", "faq"]


class ContentRequest:
    """A request for content generation."""
    topic: str
    type: ContentType
    options: Dict[str, Any]
    
    def __init__(self, topic: str, type: ContentType, options: Optional[Dict[str, Any]] = None):
        self.topic = topic
        self.type = type
        self.options = options or {}
