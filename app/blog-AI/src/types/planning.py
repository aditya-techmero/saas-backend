"""
Type definitions for content planning functionality.
"""
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta


class ContentTopic:
    """A content topic for a content calendar."""
    title: str
    keywords: List[str]
    description: Optional[str]
    
    def __init__(self, title: str, keywords: List[str], description: Optional[str] = None):
        self.title = title
        self.keywords = keywords
        self.description = description


class ContentItem:
    """A content item for a content calendar."""
    topic: ContentTopic
    date: datetime
    content_type: str
    status: str
    assigned_to: Optional[str]
    
    def __init__(
        self,
        topic: ContentTopic,
        date: datetime,
        content_type: str = "blog",
        status: str = "planned",
        assigned_to: Optional[str] = None
    ):
        self.topic = topic
        self.date = date
        self.content_type = content_type
        self.status = status
        self.assigned_to = assigned_to


class ContentCalendar:
    """A content calendar for planning content creation."""
    items: List[ContentItem]
    start_date: datetime
    end_date: datetime
    
    def __init__(self, items: List[ContentItem], start_date: datetime, end_date: datetime):
        self.items = items
        self.start_date = start_date
        self.end_date = end_date


class CompetitorContent:
    """Content from a competitor."""
    title: str
    url: str
    published_date: Optional[datetime]
    content_type: str
    keywords: List[str]
    
    def __init__(
        self,
        title: str,
        url: str,
        content_type: str,
        keywords: List[str],
        published_date: Optional[datetime] = None
    ):
        self.title = title
        self.url = url
        self.content_type = content_type
        self.keywords = keywords
        self.published_date = published_date


class Competitor:
    """A competitor for competitor analysis."""
    name: str
    website: str
    content: List[CompetitorContent]
    
    def __init__(self, name: str, website: str, content: Optional[List[CompetitorContent]] = None):
        self.name = name
        self.website = website
        self.content = content or []


class CompetitorAnalysisResult:
    """Results from a competitor analysis."""
    competitors: List[Competitor]
    common_keywords: List[str]
    content_gaps: List[str]
    recommendations: List[str]
    
    def __init__(
        self,
        competitors: List[Competitor],
        common_keywords: List[str],
        content_gaps: List[str],
        recommendations: List[str]
    ):
        self.competitors = competitors
        self.common_keywords = common_keywords
        self.content_gaps = content_gaps
        self.recommendations = recommendations


class ContentOutline:
    """An outline for a piece of content."""
    title: str
    sections: List[str]
    keywords: List[str]
    
    def __init__(self, title: str, sections: List[str], keywords: List[str]):
        self.title = title
        self.sections = sections
        self.keywords = keywords


class TopicCluster:
    """A cluster of related topics."""
    main_topic: str
    subtopics: List[str]
    keywords: List[str]
    
    def __init__(self, main_topic: str, subtopics: List[str], keywords: List[str]):
        self.main_topic = main_topic
        self.subtopics = subtopics
        self.keywords = keywords


TimeframeType = Literal["week", "month", "quarter", "year"]


class PlanningOptions:
    """Options for content planning."""
    timeframe: TimeframeType
    content_types: List[str]
    frequency: int
    search_options: Dict[str, Any]
    
    def __init__(
        self,
        timeframe: TimeframeType = "month",
        content_types: Optional[List[str]] = None,
        frequency: int = 1,
        search_options: Optional[Dict[str, Any]] = None
    ):
        self.timeframe = timeframe
        self.content_types = content_types or ["blog"]
        self.frequency = frequency
        self.search_options = search_options or {}


class OutlineSection:
    """A section within a content outline."""
    title: str
    key_points: List[str]
    estimated_words: int
    description: str
    
    def __init__(self, title: str, key_points: List[str], estimated_words: int, description: str):
        self.title = title
        self.key_points = key_points
        self.estimated_words = estimated_words
        self.description = description


class OutlineRequest:
    """Request for generating a content outline."""
    topic: str
    target_audience: str
    content_type: str
    depth: str
    tone: str
    max_sections: int
    include_research: bool
    include_keywords: bool
    
    def __init__(
        self,
        topic: str,
        target_audience: str = "general",
        content_type: str = "blog",
        depth: str = "medium",
        tone: str = "professional",
        max_sections: int = 8,
        include_research: bool = True,
        include_keywords: bool = True
    ):
        self.topic = topic
        self.target_audience = target_audience
        self.content_type = content_type
        self.depth = depth
        self.tone = tone
        self.max_sections = max_sections
        self.include_research = include_research
        self.include_keywords = include_keywords


class OutlineResponse:
    """Response containing a generated content outline."""
    topic: str
    target_audience: str
    content_type: str
    sections: List[OutlineSection]
    keywords: List[str]
    estimated_word_count: int
    generated_at: str
    
    def __init__(
        self,
        topic: str,
        target_audience: str,
        content_type: str,
        sections: List[OutlineSection],
        keywords: List[str],
        estimated_word_count: int,
        generated_at: str
    ):
        self.topic = topic
        self.target_audience = target_audience
        self.content_type = content_type
        self.sections = sections
        self.keywords = keywords
        self.estimated_word_count = estimated_word_count
        self.generated_at = generated_at
