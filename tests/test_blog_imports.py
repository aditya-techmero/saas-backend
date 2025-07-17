#!/usr/bin/env python3
"""
Test script to verify blog generation imports and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.blog_AI.src.text_generation.core import generate_text, create_provider_from_env, GenerationOptions
    from app.blog_AI.src.types.providers import ProviderType
    print("✓ Successfully imported blog-AI modules")
    
    # Test provider creation
    if os.getenv('OPENAI_API_KEY'):
        provider = create_provider_from_env("openai")
        print("✓ Successfully created OpenAI provider")
    else:
        print("⚠ OPENAI_API_KEY not set - skipping provider test")
    
    # Test database imports
    from app.database import SessionLocal
    from app.models import ContentJob, WordPressCredentials
    print("✓ Successfully imported database modules")
    
    print("\nAll imports successful! Blog generation script should work.")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
