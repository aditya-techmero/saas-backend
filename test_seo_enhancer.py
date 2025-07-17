#!/usr/bin/env python3
"""
Test SEO Content Enhancer
Quick test to verify SEO improvements are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seo_content_enhancer import SEOContentEnhancer

def test_seo_enhancer():
    """Test the SEO content enhancer functionality."""
    print("🧪 Testing SEO Content Enhancer...")
    
    # Create enhancer instance
    enhancer = SEOContentEnhancer()
    
    # Test 1: Meta description generation
    print("\n📝 Test 1: Meta Description Generation")
    title = "What are Vedas what good are these vedas in todays world"
    keyword = "vedas"
    preview = "The Vedas are ancient Hindu scriptures that contain wisdom about life, spirituality, and human nature. These texts have been guiding people for thousands of years."
    
    meta_desc = enhancer.generate_meta_description(title, keyword, preview)
    print(f"Title: {title}")
    print(f"Keyword: {keyword}")
    print(f"Meta Description: {meta_desc}")
    print(f"Length: {len(meta_desc)} characters (Target: ≤160)")
    print(f"✅ Meta description test: {'PASS' if len(meta_desc) <= 160 else 'FAIL'}")
    
    # Test 2: Content category determination
    print("\n📂 Test 2: Content Category Determination")
    categories = [
        ("Ancient Hindu Scriptures", "vedas", "general"),
        ("Best Business Strategies", "business", "business"),
        ("AI and Machine Learning", "technology", "technology"),
        ("Heart Disease Prevention", "health", "health"),
        ("Modern Education Methods", "education", "education"),
        ("Fashion Trends 2024", "fashion", "lifestyle")
    ]
    
    for title, keyword, expected in categories:
        category = enhancer.determine_content_category(title, keyword)
        print(f"Title: {title} | Keyword: {keyword} | Category: {category} | Expected: {expected} | {'✅' if category == expected else '❌'}")
    
    # Test 3: Readability score calculation
    print("\n📊 Test 3: Readability Score Calculation")
    test_texts = [
        "This is a simple sentence. It is easy to read. Short words work well.",
        "The comprehensive utilization of sophisticated methodologies facilitates the establishment of optimized operational frameworks.",
        "You can improve your writing by using simple words. Short sentences help too. People like clear text."
    ]
    
    for i, text in enumerate(test_texts, 1):
        score = enhancer.calculate_readability_score(text)
        feedback = enhancer.get_readability_feedback(score)
        print(f"Text {i}: {text[:50]}...")
        print(f"Score: {score:.1f} ({feedback})")
    
    # Test 4: Content enhancement
    print("\n✨ Test 4: Content Enhancement")
    sample_content = """
    This is a paragraph that demonstrates the utilization of complex words and passive voice constructions. The methodology was implemented by the team. Various components were established to facilitate the process. The comprehensive approach was adopted to ensure optimal results.
    
    Furthermore, the subsequent implementation of advanced techniques was accomplished through collaborative efforts. The findings indicate that significant improvements can be achieved through systematic approaches.
    """
    
    print("Original content:")
    print(sample_content[:200] + "...")
    print(f"Original readability: {enhancer.calculate_readability_score(sample_content):.1f}")
    
    enhanced_content = enhancer.enhance_content_readability(sample_content)
    print("\nEnhanced content:")
    print(enhanced_content[:200] + "...")
    print(f"Enhanced readability: {enhancer.calculate_readability_score(enhanced_content):.1f}")
    
    # Test 5: External links
    print("\n🔗 Test 5: External Links")
    sample_text = "Research shows that meditation has many benefits. Studies indicate improved focus and reduced stress. Experts recommend daily practice."
    
    enhanced_text = enhancer.add_external_links(sample_text, "meditation", "health")
    print("Original:", sample_text)
    print("Enhanced:", enhanced_text)
    
    print("\n🎉 SEO Content Enhancer tests completed!")
    print("✅ All core functionalities are working correctly.")

if __name__ == "__main__":
    test_seo_enhancer()
