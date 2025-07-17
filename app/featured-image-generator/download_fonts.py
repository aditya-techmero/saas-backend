#!/usr/bin/env python3
"""
Download Google Fonts (Poppins and Inter) for the Featured Image Generator
"""
import os
import urllib.request
from pathlib import Path

def download_font(url: str, filename: str, fonts_dir: Path) -> bool:
    """Download a font file from URL"""
    try:
        filepath = fonts_dir / filename
        print(f"📥 Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

def main():
    """Download Google Fonts"""
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)
    
    print("🎨 Downloading Google Fonts for Featured Image Generator")
    print("=" * 60)
    
    # Google Fonts URLs (using Google Fonts API)
    fonts_to_download = [
        {
            "url": "https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLDz8Z1xlFd2JQEk.woff2",
            "filename": "Poppins-Regular.woff2"
        },
        {
            "url": "https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLDD8Z1xlFd2JQEk.woff2", 
            "filename": "Poppins-Bold.woff2"
        },
        {
            "url": "https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLEj6Z1xlFd2JQEk.woff2",
            "filename": "Poppins-SemiBold.woff2"
        },
        {
            "url": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
            "filename": "Inter-Regular.woff2"
        },
        {
            "url": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuGKYAZ9hiJ-Ek-_EeA.woff2",
            "filename": "Inter-Bold.woff2"
        }
    ]
    
    success_count = 0
    for font_info in fonts_to_download:
        if download_font(font_info["url"], font_info["filename"], fonts_dir):
            success_count += 1
    
    print(f"\n🎉 Downloaded {success_count}/{len(fonts_to_download)} fonts successfully")
    
    if success_count == len(fonts_to_download):
        print("✅ All Google Fonts downloaded successfully!")
        print("🚀 Your Featured Image Generator is ready to use!")
    else:
        print("⚠️  Some fonts failed to download. The generator will use system fonts as fallback.")

if __name__ == "__main__":
    main()
