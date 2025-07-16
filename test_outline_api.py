#!/usr/bin/env python3
"""
Test script for outline API endpoints
"""
import requests
import json
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test data - valid outline schema
VALID_OUTLINE = {
    "title": "Complete Guide to Python Web Development",
    "meta_description": "Master Python web development with this comprehensive guide covering frameworks, best practices, and deployment strategies.",
    "main_keyword": "python web development",
    "target_audience": "intermediate developers",
    "content_format": "comprehensive guide",
    "tone_of_voice": "professional",
    "estimated_word_count": 3000,
    "sections": [
        {
            "section_number": 1,
            "title": "Introduction to Python Web Development",
            "estimated_words": 400,
            "description": "Overview of Python web development landscape and why it's popular",
            "key_points": [
                "Python's role in web development",
                "Popular Python web frameworks",
                "Benefits of using Python for web development"
            ],
            "keywords_to_include": ["python web development", "web frameworks", "django", "flask"]
        },
        {
            "section_number": 2,
            "title": "Setting Up Your Development Environment",
            "estimated_words": 500,
            "description": "Step-by-step guide to setting up Python web development environment",
            "key_points": [
                "Installing Python and virtual environments",
                "Setting up IDE and tools",
                "Version control with Git"
            ],
            "keywords_to_include": ["python setup", "virtual environment", "development environment"]
        },
        {
            "section_number": 3,
            "title": "Django Framework Deep Dive",
            "estimated_words": 800,
            "description": "Comprehensive overview of Django framework for web development",
            "key_points": [
                "Django architecture and MVT pattern",
                "Models, views, and templates",
                "Django admin and ORM",
                "Building REST APIs with Django"
            ],
            "keywords_to_include": ["django framework", "django models", "django rest framework", "MVT pattern"]
        },
        {
            "section_number": 4,
            "title": "Flask Framework Essentials",
            "estimated_words": 600,
            "description": "Understanding Flask microframework for lightweight web applications",
            "key_points": [
                "Flask basics and routing",
                "Templates and Jinja2",
                "Flask extensions and blueprints"
            ],
            "keywords_to_include": ["flask framework", "flask routing", "jinja2 templates", "flask blueprints"]
        },
        {
            "section_number": 5,
            "title": "Database Integration and ORM",
            "estimated_words": 500,
            "description": "Working with databases in Python web applications",
            "key_points": [
                "SQLAlchemy ORM fundamentals",
                "Database migrations and models",
                "Query optimization techniques"
            ],
            "keywords_to_include": ["sqlalchemy", "database orm", "python database", "migrations"]
        },
        {
            "section_number": 6,
            "title": "Conclusion and Next Steps",
            "estimated_words": 200,
            "description": "Summary and recommendations for further learning",
            "key_points": [
                "Key takeaways from the guide",
                "Recommended next steps",
                "Additional resources"
            ],
            "keywords_to_include": ["python web development conclusion", "next steps", "resources"]
        }
    ],
    "seo_keywords": {
        "primary_keywords": [
            "python web development",
            "django framework",
            "flask framework",
            "python web frameworks"
        ],
        "secondary_keywords": [
            "web development with python",
            "python django tutorial",
            "flask web development",
            "python web application"
        ],
        "long_tail_keywords": [
            "how to build web applications with python",
            "best python web development frameworks",
            "python web development for beginners",
            "django vs flask comparison"
        ]
    },
    "call_to_action": "Ready to start your Python web development journey? Download our comprehensive starter kit and begin building your first web application today!",
    "faq_suggestions": [
        {
            "question": "Which Python web framework should I choose?",
            "answer_preview": "The choice depends on your project requirements. Django is great for complex applications, while Flask is perfect for lightweight projects..."
        },
        {
            "question": "How long does it take to learn Python web development?",
            "answer_preview": "With consistent practice, you can learn the basics in 2-3 months and become proficient in 6-12 months..."
        },
        {
            "question": "What are the prerequisites for Python web development?",
            "answer_preview": "You should have basic Python knowledge, understanding of HTML/CSS, and familiarity with databases..."
        }
    ],
    "internal_linking_opportunities": [
        "Python fundamentals tutorial",
        "Database design best practices",
        "RESTful API development guide",
        "Web deployment strategies"
    ],
    "generated_at": datetime.now().isoformat()
}

def test_outline_validation():
    """Test outline validation with various scenarios"""
    print("🧪 Testing outline validation...")
    
    # Test 1: Valid outline
    print("\n1. Testing valid outline...")
    try:
        from app.main import OutlineSchema
        valid_outline = OutlineSchema(**VALID_OUTLINE)
        print("✅ Valid outline passed validation")
    except Exception as e:
        print(f"❌ Valid outline failed validation: {e}")
    
    # Test 2: Invalid outline - missing required field
    print("\n2. Testing outline with missing required field...")
    try:
        from app.main import OutlineSchema
        invalid_outline = VALID_OUTLINE.copy()
        del invalid_outline["title"]
        invalid_outline_obj = OutlineSchema(**invalid_outline)
        print("❌ Invalid outline (missing title) passed validation - this shouldn't happen")
    except Exception as e:
        print(f"✅ Invalid outline (missing title) properly failed validation: {e}")
    
    # Test 3: Invalid outline - empty required field
    print("\n3. Testing outline with empty required field...")
    try:
        from app.main import OutlineSchema
        invalid_outline = VALID_OUTLINE.copy()
        invalid_outline["title"] = ""
        invalid_outline_obj = OutlineSchema(**invalid_outline)
        print("❌ Invalid outline (empty title) passed validation - this shouldn't happen")
    except Exception as e:
        print(f"✅ Invalid outline (empty title) properly failed validation: {e}")
    
    # Test 4: Invalid outline - duplicate section numbers
    print("\n4. Testing outline with duplicate section numbers...")
    try:
        from app.main import OutlineSchema
        invalid_outline = VALID_OUTLINE.copy()
        invalid_outline["sections"][1]["section_number"] = 1  # Make it duplicate
        invalid_outline_obj = OutlineSchema(**invalid_outline)
        print("❌ Invalid outline (duplicate section numbers) passed validation - this shouldn't happen")
    except Exception as e:
        print(f"✅ Invalid outline (duplicate section numbers) properly failed validation: {e}")
    
    # Test 5: Invalid outline - meta description too short
    print("\n5. Testing outline with meta description too short...")
    try:
        from app.main import OutlineSchema
        invalid_outline = VALID_OUTLINE.copy()
        invalid_outline["meta_description"] = "Too short"
        invalid_outline_obj = OutlineSchema(**invalid_outline)
        print("❌ Invalid outline (meta description too short) passed validation - this shouldn't happen")
    except Exception as e:
        print(f"✅ Invalid outline (meta description too short) properly failed validation: {e}")

if __name__ == "__main__":
    print("🚀 Starting outline validation tests...")
    test_outline_validation()
    print("\n✨ All validation tests completed!")
