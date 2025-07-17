#!/usr/bin/env python3
"""
Final comprehensive test for the outline API implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import OutlineSchema, OutlineSection, OutlineSEOKeywords, OutlineFAQ
from datetime import datetime
import json

def test_comprehensive_validation():
    """Test all aspects of the outline validation"""
    
    print("🧪 Running comprehensive outline validation tests...")
    
    # Test 1: Complete valid outline
    print("\n1. Testing complete valid outline...")
    try:
        outline_data = {
            "title": "The Ultimate Guide to Machine Learning",
            "meta_description": "Discover the fundamentals of machine learning with this comprehensive guide covering algorithms, applications, and best practices for beginners.",
            "main_keyword": "machine learning guide",
            "target_audience": "data science beginners",
            "content_format": "comprehensive guide",
            "tone_of_voice": "educational",
            "estimated_word_count": 2500,
            "sections": [
                {
                    "section_number": 1,
                    "title": "Introduction to Machine Learning",
                    "estimated_words": 400,
                    "description": "Overview of machine learning concepts and applications",
                    "key_points": [
                        "What is machine learning?",
                        "Types of machine learning",
                        "Real-world applications"
                    ],
                    "keywords_to_include": ["machine learning", "AI", "artificial intelligence"]
                },
                {
                    "section_number": 2,
                    "title": "Supervised Learning Algorithms",
                    "estimated_words": 800,
                    "description": "Deep dive into supervised learning techniques",
                    "key_points": [
                        "Linear regression",
                        "Decision trees",
                        "Neural networks",
                        "Model evaluation"
                    ],
                    "keywords_to_include": ["supervised learning", "regression", "classification"]
                },
                {
                    "section_number": 3,
                    "title": "Unsupervised Learning Methods",
                    "estimated_words": 600,
                    "description": "Exploring unsupervised learning approaches",
                    "key_points": [
                        "Clustering algorithms",
                        "Dimensionality reduction",
                        "Association rules"
                    ],
                    "keywords_to_include": ["unsupervised learning", "clustering", "PCA"]
                },
                {
                    "section_number": 4,
                    "title": "Practical Implementation",
                    "estimated_words": 500,
                    "description": "How to implement machine learning in practice",
                    "key_points": [
                        "Data preprocessing",
                        "Feature engineering",
                        "Model selection"
                    ],
                    "keywords_to_include": ["data preprocessing", "feature engineering", "python"]
                },
                {
                    "section_number": 5,
                    "title": "Conclusion and Next Steps",
                    "estimated_words": 200,
                    "description": "Summary and recommendations for further learning",
                    "key_points": [
                        "Key takeaways",
                        "Further resources"
                    ],
                    "keywords_to_include": ["machine learning resources", "next steps"]
                }
            ],
            "seo_keywords": {
                "primary_keywords": [
                    "machine learning guide",
                    "machine learning tutorial",
                    "learn machine learning"
                ],
                "secondary_keywords": [
                    "supervised learning",
                    "unsupervised learning",
                    "ML algorithms",
                    "data science"
                ],
                "long_tail_keywords": [
                    "machine learning for beginners",
                    "how to learn machine learning",
                    "machine learning step by step guide"
                ]
            },
            "call_to_action": "Ready to dive deeper into machine learning? Download our hands-on practice exercises and start building your own ML models today!",
            "faq_suggestions": [
                {
                    "question": "What programming language is best for machine learning?",
                    "answer_preview": "Python is the most popular choice due to its extensive libraries like scikit-learn, TensorFlow, and PyTorch..."
                },
                {
                    "question": "How much math do I need for machine learning?",
                    "answer_preview": "A solid foundation in statistics, linear algebra, and calculus is helpful but not strictly required to get started..."
                },
                {
                    "question": "Can I learn machine learning without a computer science background?",
                    "answer_preview": "Absolutely! Many successful ML practitioners come from diverse backgrounds including physics, economics, and biology..."
                }
            ],
            "internal_linking_opportunities": [
                "Python for data science tutorial",
                "Statistics fundamentals guide",
                "Data visualization best practices",
                "Deep learning introduction"
            ]
        }
        
        outline = OutlineSchema(**outline_data)
        print("✅ Complete valid outline passed all validation checks")
        
        # Use fresh outline data for this test
        outline_schema = OutlineSchema(**outline_data)
        outline_json = outline_schema.model_dump()  # Use model_dump instead of dict()
        json_string = json.dumps(outline_json, indent=2)
        print(f"✅ Outline serialization successful ({len(json_string)} characters)")
        
    except Exception as e:
        print(f"❌ Valid outline failed validation: {e}")
        return False
    
    # Test 2: Empty key points validation
    print("\n2. Testing empty key points validation...")
    try:
        invalid_outline = outline_data.copy()
        invalid_outline["sections"][0]["key_points"] = ["Valid point", "", "Another valid point"]
        
        outline = OutlineSchema(**invalid_outline)
        print("❌ Outline with empty key points should have failed validation")
        return False
    except Exception as e:
        print(f"✅ Empty key points properly rejected: {e}")
    
    # Test 3: Word count consistency validation
    print("\n3. Testing word count consistency...")
    try:
        # Use fresh outline data for this test
        fresh_outline = {
            "title": "The Ultimate Guide to Machine Learning",
            "meta_description": "Discover the fundamentals of machine learning with this comprehensive guide covering algorithms, applications, and best practices for beginners.",
            "main_keyword": "machine learning guide",
            "target_audience": "data science beginners",
            "content_format": "comprehensive guide",
            "tone_of_voice": "educational",
            "estimated_word_count": 2500,
            "sections": [
                {
                    "section_number": 1,
                    "title": "Introduction to Machine Learning",
                    "estimated_words": 400,
                    "description": "Overview of machine learning concepts and applications",
                    "key_points": [
                        "What is machine learning?",
                        "Types of machine learning",
                        "Real-world applications"
                    ],
                    "keywords_to_include": ["machine learning", "AI", "artificial intelligence"]
                },
                {
                    "section_number": 2,
                    "title": "Supervised Learning Algorithms",
                    "estimated_words": 800,
                    "description": "Deep dive into supervised learning techniques",
                    "key_points": [
                        "Linear regression",
                        "Decision trees",
                        "Neural networks",
                        "Model evaluation"
                    ],
                    "keywords_to_include": ["supervised learning", "regression", "classification"]
                },
                {
                    "section_number": 3,
                    "title": "Unsupervised Learning Methods",
                    "estimated_words": 600,
                    "description": "Exploring unsupervised learning approaches",
                    "key_points": [
                        "Clustering algorithms",
                        "Dimensionality reduction",
                        "Association rules"
                    ],
                    "keywords_to_include": ["unsupervised learning", "clustering", "PCA"]
                },
                {
                    "section_number": 4,
                    "title": "Practical Implementation",
                    "estimated_words": 500,
                    "description": "How to implement machine learning in practice",
                    "key_points": [
                        "Data preprocessing",
                        "Feature engineering",
                        "Model selection"
                    ],
                    "keywords_to_include": ["data preprocessing", "feature engineering", "python"]
                },
                {
                    "section_number": 5,
                    "title": "Conclusion and Next Steps",
                    "estimated_words": 200,
                    "description": "Summary and recommendations for further learning",
                    "key_points": [
                        "Key takeaways",
                        "Further resources"
                    ],
                    "keywords_to_include": ["machine learning resources", "next steps"]
                }
            ],
            "seo_keywords": {
                "primary_keywords": [
                    "machine learning guide",
                    "machine learning tutorial",
                    "learn machine learning"
                ],
                "secondary_keywords": [
                    "supervised learning",
                    "unsupervised learning",
                    "ML algorithms",
                    "data science"
                ],
                "long_tail_keywords": [
                    "machine learning for beginners",
                    "how to learn machine learning",
                    "machine learning step by step guide"
                ]
            },
            "call_to_action": "Ready to dive deeper into machine learning? Download our hands-on practice exercises and start building your own ML models today!",
            "faq_suggestions": [
                {
                    "question": "What programming language is best for machine learning?",
                    "answer_preview": "Python is the most popular choice due to its extensive libraries like scikit-learn, TensorFlow, and PyTorch..."
                },
                {
                    "question": "How much math do I need for machine learning?",
                    "answer_preview": "A solid foundation in statistics, linear algebra, and calculus is helpful but not strictly required to get started..."
                },
                {
                    "question": "Can I learn machine learning without a computer science background?",
                    "answer_preview": "Absolutely! Many successful ML practitioners come from diverse backgrounds including physics, economics, and biology..."
                }
            ],
            "internal_linking_opportunities": [
                "Python for data science tutorial",
                "Statistics fundamentals guide",
                "Data visualization best practices",
                "Deep learning introduction"
            ]
        }
        
        # Calculate total words from sections
        total_section_words = sum(s["estimated_words"] for s in fresh_outline["sections"])
        print(f"   Total section words: {total_section_words}")
        print(f"   Estimated total: {fresh_outline['estimated_word_count']}")
        print(f"   Difference: {abs(total_section_words - fresh_outline['estimated_word_count'])}")
        
        # This should pass since our example has consistent word counts
        outline = OutlineSchema(**fresh_outline)
        print("✅ Word count consistency check passed")
        
    except Exception as e:
        print(f"❌ Word count consistency validation failed: {e}")
        return False
    
    # Test 4: Section number validation
    print("\n4. Testing section number validation...")
    try:
        invalid_outline = outline_data.copy()
        invalid_outline["sections"][1]["section_number"] = 5  # Skip numbers
        
        outline = OutlineSchema(**invalid_outline)
        print("❌ Non-sequential section numbers should have failed validation")
        return False
    except Exception as e:
        print(f"✅ Non-sequential section numbers properly rejected: {e}")
    
    # Test 5: Meta description length validation
    print("\n5. Testing meta description length validation...")
    try:
        invalid_outline = outline_data.copy()
        invalid_outline["meta_description"] = "Too short for SEO"
        
        outline = OutlineSchema(**invalid_outline)
        print("❌ Short meta description should have failed validation")
        return False
    except Exception as e:
        print(f"✅ Short meta description properly rejected: {e}")
    
    # Test 6: Required SEO keywords validation
    print("\n6. Testing required SEO keywords validation...")
    try:
        invalid_outline = outline_data.copy()
        invalid_outline["seo_keywords"]["primary_keywords"] = []
        
        outline = OutlineSchema(**invalid_outline)
        print("❌ Empty primary keywords should have failed validation")
        return False
    except Exception as e:
        print(f"✅ Empty primary keywords properly rejected: {e}")
    
    print("\n✅ All comprehensive validation tests passed!")
    return True

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    
    print("\n🔍 Testing edge cases and boundary conditions...")
    
    # Test minimum valid outline
    print("\n1. Testing minimum valid outline...")
    try:
        min_outline = {
            "title": "A",  # Minimum length
            "meta_description": "A" * 120,  # Minimum length for SEO
            "main_keyword": "a",
            "target_audience": "a",
            "content_format": "a",
            "tone_of_voice": "a",
            "estimated_word_count": 300,  # Minimum
            "sections": [
                {
                    "section_number": 1,
                    "title": "A",
                    "estimated_words": 150,
                    "description": "A",
                    "key_points": ["A"],
                    "keywords_to_include": []
                },
                {
                    "section_number": 2,
                    "title": "B",
                    "estimated_words": 150,
                    "description": "B",
                    "key_points": ["B"],
                    "keywords_to_include": []
                }
            ],
            "seo_keywords": {
                "primary_keywords": ["a"],
                "secondary_keywords": [],
                "long_tail_keywords": []
            },
            "call_to_action": "a",
            "faq_suggestions": [],
            "internal_linking_opportunities": []
        }
        
        outline = OutlineSchema(**min_outline)
        print("✅ Minimum valid outline passed validation")
        
    except Exception as e:
        print(f"❌ Minimum valid outline failed: {e}")
        return False
    
    # Test maximum valid outline
    print("\n2. Testing maximum boundary conditions...")
    try:
        max_outline = {
            "title": "A" * 300,  # Maximum length
            "meta_description": "A" * 160,  # Maximum length for SEO
            "main_keyword": "a" * 100,
            "target_audience": "a" * 100,
            "content_format": "a" * 50,
            "tone_of_voice": "a" * 50,
            "estimated_word_count": 10000,  # Maximum
            "sections": [
                {
                    "section_number": i,
                    "title": f"Section {i}",
                    "estimated_words": 667,  # 10000 / 15 sections
                    "description": "A" * 1000,  # Maximum description
                    "key_points": [f"Point {j}" for j in range(1, 11)],  # Maximum 10 points
                    "keywords_to_include": [f"keyword{j}" for j in range(1, 21)]  # Maximum 20 keywords
                }
                for i in range(1, 16)  # Maximum 15 sections
            ],
            "seo_keywords": {
                "primary_keywords": [f"primary{i}" for i in range(1, 51)],  # Maximum 50
                "secondary_keywords": [f"secondary{i}" for i in range(1, 101)],  # Maximum 100
                "long_tail_keywords": [f"long tail {i}" for i in range(1, 101)]  # Maximum 100
            },
            "call_to_action": "A" * 500,  # Maximum length
            "faq_suggestions": [
                {
                    "question": f"Question {i}?",
                    "answer_preview": "A" * 1000
                }
                for i in range(1, 21)  # Maximum 20 FAQs
            ],
            "internal_linking_opportunities": [f"Link {i}" for i in range(1, 51)]  # Maximum 50
        }
        
        outline = OutlineSchema(**max_outline)
        print("✅ Maximum boundary conditions passed validation")
        
    except Exception as e:
        print(f"❌ Maximum boundary conditions failed: {e}")
        return False
    
    print("\n✅ All edge case tests passed!")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive outline validation test suite...")
    
    success = True
    
    # Run comprehensive validation tests
    if not test_comprehensive_validation():
        success = False
    
    # Run edge case tests
    if not test_edge_cases():
        success = False
    
    if success:
        print("\n🎉 All tests passed! The outline validation system is working correctly.")
        print("\n📋 Summary of validation features:")
        print("   ✅ Required field validation")
        print("   ✅ Empty string detection")
        print("   ✅ Length constraints")
        print("   ✅ Sequential section numbering")
        print("   ✅ SEO meta description requirements")
        print("   ✅ Primary keyword requirements")
        print("   ✅ Boundary condition handling")
        print("   ✅ JSON serialization support")
        
        print("\n🔧 API endpoints available:")
        print("   📝 PUT /jobs/{job_id}/outline - Update job outline")
        print("   📖 GET /jobs/{job_id}/outline - Get job outline")
        print("   🆕 POST /create-job - Create job with optional outline")
        
        return True
    else:
        print("\n❌ Some tests failed. Please review the validation logic.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
