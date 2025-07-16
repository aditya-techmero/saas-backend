#!/usr/bin/env python3
"""
Blog-AI System Analysis Script
Analyzes which files are important and which can be removed from the blog-AI folder.
"""

import os
import sys
import importlib.util
from pathlib import Path

def analyze_file_importance(blog_ai_path):
    """Analyze which files in blog-AI are important and working"""
    
    analysis = {
        "essential_files": [],
        "working_files": [],
        "optional_files": [],
        "unused_files": [],
        "missing_dependencies": []
    }
    
    # Core essential files (used by content_automation.py)
    essential_core = [
        "src/text_generation/core.py",
        "src/types/providers.py", 
        "src/types/content.py",
        "src/blog/make_blog.py",
        "src/outline/make_outline.py"
    ]
    
    # Test import capabilities
    test_imports = [
        ("src.blog.make_blog", "generate_blog_post"),
        ("src.outline.make_outline", "OutlineGenerator"),
        ("src.text_generation.core", "create_provider_from_env"),
        ("src.types.providers", "OpenAIConfig"),
        ("src.types.content", "BlogPost")
    ]
    
    print("=== Blog-AI System Analysis ===\n")
    
    # Check if files exist and are importable
    for file_path in essential_core:
        full_path = os.path.join(blog_ai_path, file_path)
        if os.path.exists(full_path):
            analysis["essential_files"].append(file_path)
            print(f"✅ Essential: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
    
    # Test imports
    print("\n=== Import Tests ===")
    sys.path.insert(0, blog_ai_path)
    
    for module_name, function_name in test_imports:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, function_name):
                print(f"✅ Import working: {module_name}.{function_name}")
                analysis["working_files"].append(module_name)
            else:
                print(f"❌ Missing function: {module_name}.{function_name}")
        except ImportError as e:
            print(f"❌ Import failed: {module_name} - {e}")
            analysis["missing_dependencies"].append(f"{module_name}: {e}")
    
    # Analyze all files in the directory
    print("\n=== File Analysis ===")
    
    for root, dirs, files in os.walk(blog_ai_path):
        for file in files:
            if file.endswith('.py'):
                relative_path = os.path.relpath(os.path.join(root, file), blog_ai_path)
                
                # Skip __pycache__ and .git
                if '__pycache__' in relative_path or '.git' in relative_path:
                    continue
                
                if relative_path in essential_core:
                    continue  # Already categorized
                
                # Check if it's a working module
                if any(relative_path.replace('/', '.').replace('.py', '') in working for working in analysis["working_files"]):
                    continue  # Already categorized
                
                # Categorize based on functionality
                if any(keyword in relative_path.lower() for keyword in ['test', 'example', 'demo']):
                    analysis["optional_files"].append(relative_path)
                    print(f"🔶 Optional: {relative_path}")
                elif any(keyword in relative_path.lower() for keyword in ['types', 'blog_sections', 'seo', 'research']):
                    analysis["working_files"].append(relative_path)
                    print(f"✅ Working: {relative_path}")
                else:
                    analysis["unused_files"].append(relative_path)
                    print(f"⚠️  Unused: {relative_path}")
    
    # Special files analysis
    special_files = {
        "server.py": "FastAPI server - Optional if using content_automation.py",
        "setup.py": "Setup script - Can be removed after installation",
        "test_system.py": "Test script - Optional for production",
        "generate_outline.py": "CLI wrapper - Optional",
        ".git/": "Git repository - Can be removed",
        "content/": "Generated content - Can be cleaned up"
    }
    
    print("\n=== Special Files ===")
    for file, description in special_files.items():
        full_path = os.path.join(blog_ai_path, file)
        if os.path.exists(full_path):
            print(f"🔶 {file}: {description}")
            analysis["optional_files"].append(file)
    
    return analysis

def generate_cleanup_recommendations(analysis):
    """Generate recommendations for cleaning up the blog-AI folder"""
    
    print("\n" + "="*60)
    print("CLEANUP RECOMMENDATIONS")
    print("="*60)
    
    print("\n✅ KEEP THESE FILES (Essential for content automation):")
    for file in analysis["essential_files"]:
        print(f"   - {file}")
    
    print("\n✅ KEEP THESE FILES (Working functionality):")
    for file in analysis["working_files"]:
        print(f"   - {file}")
    
    print("\n🔶 OPTIONAL FILES (Can be removed to save space):")
    for file in analysis["optional_files"]:
        print(f"   - {file}")
    
    print("\n⚠️  UNUSED FILES (Likely safe to remove):")
    for file in analysis["unused_files"]:
        print(f"   - {file}")
    
    if analysis["missing_dependencies"]:
        print("\n❌ MISSING DEPENDENCIES:")
        for dep in analysis["missing_dependencies"]:
            print(f"   - {dep}")
    
    print("\n📝 ACTIONS TO TAKE:")
    print("1. Keep all essential and working files")
    print("2. Remove optional files if you want to save space")
    print("3. Remove unused files to clean up the directory")
    print("4. Address any missing dependencies")
    print("5. The content_automation.py should work with the essential files")

def main():
    blog_ai_path = "/Users/aditya/Desktop/backend/app/blog-AI"
    
    if not os.path.exists(blog_ai_path):
        print(f"❌ Blog-AI directory not found: {blog_ai_path}")
        return
    
    analysis = analyze_file_importance(blog_ai_path)
    generate_cleanup_recommendations(analysis)
    
    print(f"\n🎯 SUMMARY:")
    print(f"Essential files: {len(analysis['essential_files'])}")
    print(f"Working files: {len(analysis['working_files'])}")
    print(f"Optional files: {len(analysis['optional_files'])}")
    print(f"Unused files: {len(analysis['unused_files'])}")
    print(f"Missing dependencies: {len(analysis['missing_dependencies'])}")

if __name__ == "__main__":
    main()
