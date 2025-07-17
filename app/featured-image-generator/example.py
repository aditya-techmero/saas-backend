#!/usr/bin/env python3
"""
Simple example of how to use the Featured Image Generator API
"""
import requests
import json

def create_example_image():
    """Create an example featured image"""
    
    # Example payload
    payload = {
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=500&fit=crop",
        "article_title": "Getting Started with Featured Images",
        "read_time": "5 min read",
        "author": "Your Name",
        "publish_date": "July 2025",
        "style": "modern",
        "pattern": "geometric"
    }
    
    try:
        # Make request to the API
        response = requests.post(
            "http://localhost:8000/featured-image/create",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            # Save the image
            with open("example_featured_image.webp", "wb") as f:
                f.write(response.content)
            print("✅ Example image created: example_featured_image.webp")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Creating example featured image...")
    
    if create_example_image():
        print("🎉 Success! Check the generated image file.")
    else:
        print("❌ Failed to create image. Make sure the server is running.")
        print("💡 Start the server with: python run_server.py")
