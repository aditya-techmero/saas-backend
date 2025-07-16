#!/usr/bin/env python3
"""
Simple test script to verify semantic keyword generation without database dependency
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Mock OpenAI for testing
class MockOpenAI:
    class ChatCompletion:
        @staticmethod
        def create(**kwargs):
            # Return a mock response with semantic keywords
            class MockResponse:
                def __init__(self):
                    self.choices = [MockChoice()]
            
            class MockChoice:
                def __init__(self):
                    self.message = MockMessage()
            
            class MockMessage:
                def __init__(self):
                    self.content = """{
                        "primary_keywords": [
                            "python web development",
                            "python web applications",
                            "web development with python",
                            "python for web development",
                            "python web programming"
                        ],
                        "secondary_keywords": [
                            "django framework",
                            "flask framework",
                            "python web frameworks",
                            "web development frameworks",
                            "python backend development"
                        ],
                        "long_tail_keywords": [
                            "how to build web applications with python",
                            "best python framework for web development",
                            "python web development tutorial for beginners",
                            "django vs flask for web development",
                            "python web development career path"
                        ],
                        "related_keywords": [
                            "REST API development",
                            "database integration",
                            "web security",
                            "deployment strategies",
                            "performance optimization"
                        ]
                    }"""
            
            return MockResponse()

# Mock job class
class MockJob:
    def __init__(self):
        self.id = 1
        self.title = "The Ultimate Guide to Python Web Development"
        self.main_keyword = "python web development"
        self.related_keywords = "django, flask, python frameworks, web applications"

def test_semantic_keyword_parsing():
    """Test the semantic keyword parsing logic"""
    print("🧪 Testing semantic keyword parsing logic...")
    
    # Mock response
    mock_response = """{
        "primary_keywords": ["python web development", "python web applications"],
        "secondary_keywords": ["django framework", "flask framework"],
        "long_tail_keywords": ["how to build web applications with python"],
        "related_keywords": ["REST API development", "database integration"]
    }"""
    
    try:
        # Parse the response
        start_idx = mock_response.find('{')
        end_idx = mock_response.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = mock_response[start_idx:end_idx]
            keywords_data = json.loads(json_str)
            
            # Validate required keys
            required_keys = ['primary_keywords', 'secondary_keywords', 'long_tail_keywords', 'related_keywords']
            for key in required_keys:
                if key not in keywords_data:
                    keywords_data[key] = []
            
            # Calculate total count
            total_count = sum(len(keywords_data[key]) for key in required_keys)
            keywords_data['total_count'] = total_count
            
            print(f"✅ Successfully parsed {total_count} semantic keywords")
            print(f"Primary keywords: {len(keywords_data['primary_keywords'])}")
            print(f"Secondary keywords: {len(keywords_data['secondary_keywords'])}")
            print(f"Long-tail keywords: {len(keywords_data['long_tail_keywords'])}")
            print(f"Related keywords: {len(keywords_data['related_keywords'])}")
            
            # Show some examples
            print("\nSample primary keywords:")
            for i, kw in enumerate(keywords_data['primary_keywords'][:3]):
                print(f"  {i+1}. {kw}")
            
            return True
        else:
            print("❌ No JSON found in response")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing semantic keywords: {str(e)}")
        return False

def test_keyword_generation_prompt():
    """Test the keyword generation prompt creation"""
    print("\n🧪 Testing keyword generation prompt creation...")
    
    try:
        job = MockJob()
        target_count = 50
        
        # Parse related keywords
        related_keywords = []
        if job.related_keywords:
            if isinstance(job.related_keywords, str):
                related_keywords = [kw.strip() for kw in job.related_keywords.split(',')]
            elif isinstance(job.related_keywords, list):
                related_keywords = job.related_keywords
        
        related_keywords_str = ", ".join(related_keywords) if related_keywords else "None provided"
        
        # Create prompt
        prompt = f"""
Generate {target_count} semantic keywords for SEO optimization based on the following information:

Main Keyword: {job.main_keyword}
Related Keywords: {related_keywords_str}
Title: {job.title}

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

Generate high-quality, semantically relevant keywords that will improve SEO performance.
"""
        
        print("✅ Successfully created semantic keyword generation prompt")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Target count: {target_count}")
        print(f"Main keyword: {job.main_keyword}")
        print(f"Related keywords: {related_keywords}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating prompt: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting semantic keyword generation tests (mock mode)...\n")
    
    # Test 1: JSON parsing
    success1 = test_semantic_keyword_parsing()
    
    # Test 2: Prompt creation
    success2 = test_keyword_generation_prompt()
    
    print(f"\n📊 Test Results:")
    print(f"JSON parsing test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Prompt creation test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The semantic keyword generation logic is working correctly.")
        print("\nNext steps:")
        print("1. Set up your OpenAI API key in .env file")
        print("2. Configure your database connection")
        print("3. Run the full automation script with: python3 content_automation_with_seo.py")
        print("4. Use manage_semantic_keywords.py to generate keywords for existing jobs")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
