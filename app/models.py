# models.py - Updated ContentJob model
from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    password = Column(String, nullable=False)
    role = Column(String, default='user')
    created_at = Column(TIMESTAMP, server_default=func.now())
    email = Column(String, nullable=True)
    
    # Relationships
    content_jobs = relationship("ContentJob", back_populates="owner")
    wordpress_credentials = relationship("WordPressCredentials", back_populates="user")

class ContentJob(Base):
    __tablename__ = "content_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    outline_prompt = Column(Text, nullable=True)
    
    # WordPress credentials reference - NOW REQUIRED!
    wordpress_credentials_id = Column(Integer, ForeignKey("WordPressCredentials.id"), nullable=False)
    
    # Content job specific fields from your schema
    Outline = Column(Text, nullable=True)
    audienceType = Column(Text, nullable=True)
    contentFormat = Column(Text, nullable=True)
    mainKeyword = Column(Text, nullable=True)
    toneOfVoice = Column(Text, nullable=True)
    related_keywords = Column(String, nullable=True)
    article_word_count = Column(Integer, nullable=True)
    article_length = Column(String, nullable=True)
    competitor_url_1 = Column(String, nullable=True)
    competitor_url_2 = Column(String, nullable=True)
    semantic_keywords = Column(JSON, nullable=True)
    semantic_keywords_2 = Column(JSON, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="content_jobs")
    wordpress_credentials = relationship("WordPressCredentials", back_populates="content_jobs")

class WordPressCredentials(Base):
    __tablename__ = "WordPressCredentials"
    
    id = Column(Integer, primary_key=True, index=True)
    siteUrl = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    applicationPassword = Column(Text, nullable=False)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="wordpress_credentials")
    content_jobs = relationship("ContentJob", back_populates="wordpress_credentials")