# pip install fastapi uvicorn[standard] pydantic requests Pillow python-dotenv aiofiles httpx
from __future__ import annotations

import asyncio
import base64
import io
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

import aiofiles
import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, ImageStat
from pydantic import BaseModel, HttpUrl, validator
import colorsys
import math

app = FastAPI(title="Enhanced Featured Image Generator", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Featured Image Generator is running"}


class FeaturedImageRequest(BaseModel):
    image_url: HttpUrl
    article_title: str
    read_time: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    author_image: Optional[HttpUrl] = None
    style: Optional[str] = "vibrant"
    pattern: Optional[str] = "none"

    @validator("style")
    def validate_style(cls, v):
        valid_styles = ["modern", "vibrant", "subtle", "radial"]
        return v if v in valid_styles else "modern"

    @validator("pattern")
    def validate_pattern(cls, v):
        valid_patterns = ["none", "dots", "waves", "geometric"]
        return v if v in valid_patterns else "none"


class StyleOption(BaseModel):
    value: str
    description: str


class OptionsResponse(BaseModel):
    styles: List[StyleOption]
    patterns: List[StyleOption]


class ColorScheme:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def to_rgb_string(self) -> str:
        return f"rgb({self.r},{self.g},{self.b})"

    def to_rgba_string(self, alpha: float = 1.0) -> str:
        return f"rgba({self.r},{self.g},{self.b},{alpha})"


class ColorPalette:
    def __init__(self, dominant: ColorScheme, complementary: ColorScheme, 
                 analogous1: ColorScheme, analogous2: ColorScheme):
        self.dominant = dominant
        self.complementary = complementary
        self.analogous1 = analogous1
        self.analogous2 = analogous2


def escape_xml(text: str) -> str:
    """Escape special characters for XML/SVG"""
    if not text:
        return ""
    return escape(str(text))


def get_color_brightness(r: int, g: int, b: int) -> float:
    """Calculate color brightness using relative luminance formula"""
    return 0.299 * r + 0.587 * g + 0.114 * b


def is_gradient_light(colors: ColorPalette) -> bool:
    """Determine if gradient is light or dark"""
    dominant_brightness = get_color_brightness(colors.dominant.r, colors.dominant.g, colors.dominant.b)
    analogous1_brightness = get_color_brightness(colors.analogous1.r, colors.analogous1.g, colors.analogous1.b)
    analogous2_brightness = get_color_brightness(colors.analogous2.r, colors.analogous2.g, colors.analogous2.b)
    
    average_brightness = (dominant_brightness + analogous1_brightness + analogous2_brightness) / 3
    return average_brightness > 128


def get_font_color(colors: ColorPalette) -> str:
    """Get contrasting font color based on gradient brightness"""
    return "#2d3748" if is_gradient_light(colors) else "#ffffff"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to HSL"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    h, s, l = 0, 0, (max_val + min_val) / 2
    
    if max_val == min_val:
        h = s = 0  # achromatic
    else:
        d = max_val - min_val
        s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        elif max_val == b:
            h = (r - g) / d + 4
        h /= 6
    
    return h * 360, s, l


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL to RGB"""
    h = h / 360.0
    
    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p
    
    if s == 0:
        r = g = b = l  # achromatic
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return round(r * 255), round(g * 255), round(b * 255)


def extract_dominant_colors(image: Image.Image) -> ColorPalette:
    """Extract dominant colors from an image"""
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get dominant color using PIL's ImageStat
        stat = ImageStat.Stat(image)
        r, g, b = [int(x) for x in stat.mean]
        
        # Create complementary colors
        complementary_r = 255 - r
        complementary_g = 255 - g
        complementary_b = 255 - b
        
        # Create analogous colors by shifting hue
        h, s, l = rgb_to_hsl(r, g, b)
        analogous1_rgb = hsl_to_rgb((h + 30) % 360, s, max(0.3, l * 0.8))
        analogous2_rgb = hsl_to_rgb((h - 30 + 360) % 360, s, max(0.3, l * 0.8))
        
        return ColorPalette(
            dominant=ColorScheme(r, g, b),
            complementary=ColorScheme(complementary_r, complementary_g, complementary_b),
            analogous1=ColorScheme(*analogous1_rgb),
            analogous2=ColorScheme(*analogous2_rgb)
        )
    except Exception as e:
        print(f"Error extracting colors: {e}")
        # Return default colors if extraction fails
        return ColorPalette(
            dominant=ColorScheme(74, 111, 165),
            complementary=ColorScheme(165, 144, 90),
            analogous1=ColorScheme(111, 74, 165),
            analogous2=ColorScheme(165, 74, 111)
        )


def generate_dynamic_gradient(colors: ColorPalette, style: str = "modern") -> str:
    """Generate dynamic gradient based on image colors"""
    if style == "vibrant":
        return f"""
        <linearGradient id="dynamicGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:{colors.dominant.to_rgb_string()};stop-opacity:0.9" />
          <stop offset="35%" style="stop-color:{colors.analogous1.to_rgb_string()};stop-opacity:0.8" />
          <stop offset="65%" style="stop-color:{colors.analogous2.to_rgb_string()};stop-opacity:0.8" />
          <stop offset="100%" style="stop-color:{colors.complementary.to_rgb_string()};stop-opacity:0.9" />
        </linearGradient>
        """
    elif style == "subtle":
        light_dominant = ColorScheme(
            min(255, colors.dominant.r + 40),
            min(255, colors.dominant.g + 40),
            min(255, colors.dominant.b + 40)
        )
        return f"""
        <linearGradient id="dynamicGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:{light_dominant.to_rgb_string()};stop-opacity:0.7" />
          <stop offset="100%" style="stop-color:{colors.dominant.to_rgb_string()};stop-opacity:0.8" />
        </linearGradient>
        """
    elif style == "radial":
        return f"""
        <radialGradient id="dynamicGrad" cx="50%" cy="50%" r="70%">
          <stop offset="0%" style="stop-color:{colors.analogous1.to_rgb_string()};stop-opacity:0.6" />
          <stop offset="50%" style="stop-color:{colors.dominant.to_rgb_string()};stop-opacity:0.8" />
          <stop offset="100%" style="stop-color:{colors.analogous2.to_rgb_string()};stop-opacity:0.9" />
        </radialGradient>
        """
    else:  # modern
        return f"""
        <linearGradient id="dynamicGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:{colors.analogous1.to_rgb_string()};stop-opacity:0.85" />
          <stop offset="50%" style="stop-color:{colors.dominant.to_rgb_string()};stop-opacity:0.9" />
          <stop offset="100%" style="stop-color:{colors.analogous2.to_rgb_string()};stop-opacity:0.85" />
        </linearGradient>
        """


def generate_background_pattern(colors: ColorPalette, pattern: str = "none") -> str:
    """Generate artistic background patterns"""
    if pattern == "dots":
        return f"""
        <pattern id="dots" patternUnits="userSpaceOnUse" width="40" height="40">
          <circle cx="20" cy="20" r="3" fill="{colors.analogous1.to_rgba_string(0.3)}"/>
        </pattern>
        """
    elif pattern == "waves":
        return f"""
        <pattern id="waves" patternUnits="userSpaceOnUse" width="100" height="100">
          <path d="M0,50 Q25,25 50,50 Q75,75 100,50" stroke="{colors.analogous2.to_rgba_string(0.4)}" stroke-width="2" fill="none"/>
        </pattern>
        """
    elif pattern == "geometric":
        return f"""
        <pattern id="geometric" patternUnits="userSpaceOnUse" width="60" height="60">
          <polygon points="30,5 55,25 45,50 15,50 5,25" fill="{colors.dominant.to_rgba_string(0.1)}"/>
        </pattern>
        """
    else:
        return ""


async def download_image(url: str) -> bytes:
    """Download image from URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                str(url),
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
            )
            response.raise_for_status()
            return response.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")


async def image_url_to_data_url(url: str) -> Optional[str]:
    """Convert image URL to data URL"""
    if not url:
        return None
    
    if url.startswith('data:'):
        return url
    
    try:
        image_data = await download_image(url)
        # Detect content type
        content_type = "image/jpeg"
        if image_data.startswith(b'\x89PNG'):
            content_type = "image/png"
        elif image_data.startswith(b'GIF'):
            content_type = "image/gif"
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
            content_type = "image/webp"
        
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{content_type};base64,{base64_data}"
    except Exception as e:
        print(f"Error converting image to data URL: {e}")
        return None


def wrap_text(text: str, max_length: int = 20) -> List[str]:
    """Wrap text into multiple lines with shorter length for larger fonts"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) > max_length:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = current_line + " " + word if current_line else word
    
    if current_line:
        lines.append(current_line)
    
    if not lines:
        lines = ["Article Title"]
    
    if len(lines) > 4:  # Allow more lines for larger fonts
        lines = lines[:3]
        lines.append(lines[2] + "...")
    
    return lines


async def create_enhanced_featured_image(
    image_data: bytes,
    article_title: str,
    read_time: Optional[str] = None,
    author: Optional[str] = None,
    publish_date: Optional[str] = None,
    author_image: Optional[str] = None,
    style: str = "vibrant",
    pattern: str = "none"
) -> bytes:
    """Create enhanced featured image"""
    
    # Load and process the main image
    image = Image.open(io.BytesIO(image_data))
    
    # Extract colors
    colors = extract_dominant_colors(image)
    
    # Generate dynamic elements
    dynamic_gradient = generate_dynamic_gradient(colors, style)
    background_pattern = generate_background_pattern(colors, pattern)
    
    # Get font color
    font_color = get_font_color(colors)
    
    # Process text safely
    safe_title = escape_xml(article_title)
    safe_read_time = escape_xml(read_time) if read_time else None
    safe_author = escape_xml(author) if author else None
    safe_publish_date = escape_xml(publish_date) if publish_date else None
    
    # Wrap title text
    title_lines = wrap_text(safe_title)
    
    # Layout calculations with proper boundaries for larger fonts
    left_padding = 40  # Reduced padding
    text_position = left_padding + 20  # Closer to left edge
    max_text_width = 620  # Maximum width for text to stay in left panel
    
    read_time_height = 80 if safe_read_time else 0
    title_height = 140 + (len(title_lines) - 1) * 65  # Slightly reduced spacing
    author_height = 110 if safe_author else 0
    spacing = 25  # Reduced spacing
    
    total_content_height = (
        read_time_height +
        (spacing if safe_read_time else 0) +
        title_height +
        (spacing if safe_author else 0) +
        author_height
    )
    
    content_start_y = 30 + (740 - total_content_height) // 2
    
    read_time_y = content_start_y
    title_y = content_start_y + (read_time_height + spacing if safe_read_time else 0)
    author_y = title_y + title_height + (spacing if safe_author else 0)
    
    image_x = left_padding + 30
    
    # Create line elements for title with Google Fonts
    line_elements = []
    for i, line in enumerate(title_lines):
        line_elements.append(
            f'<text x="{text_position}" y="{title_y + 65 + i * 65}" '
            f'font-family="Poppins, Inter, Arial, sans-serif" font-size="55" font-weight="bold" '
            f'text-anchor="start" fill="{font_color}" stroke="rgba(0,0,0,0.1)" stroke-width="0.5">'
            f'{line}</text>'
        )
    
    # Resize and process the main image
    image = image.convert('RGB')
    image = image.resize((670, 740), Image.Resampling.LANCZOS)
    
    # Convert PIL image to bytes for SVG embedding
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Create SVG
    svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="1400" height="800" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">
  <defs>
    {dynamic_gradient}
    {background_pattern}
    <filter id="blur">
      <feGaussianBlur stdDeviation="8" result="blurred"/>
    </filter>
    <filter id="shadow">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-opacity="0.3"/>
    </filter>
  </defs>
  
  <!-- Enhanced border with blur effect -->
  <rect width="1400" height="800" fill="url(#dynamicGrad)" rx="20" ry="20" filter="url(#blur)" />
  {f'<rect width="1400" height="800" fill="url(#{pattern})" rx="20" ry="20" />' if pattern != "none" else ""}
  
  <!-- Inner content area -->
  <rect width="1340" height="740" x="30" y="30" fill="rgba(255, 255, 255, 0.95)" rx="10" ry="10" filter="url(#shadow)" />
  
  <!-- Left panel with enhanced blurred gradient -->
  <rect width="670" height="740" x="30" y="30" fill="url(#dynamicGrad)" rx="10" ry="10" filter="url(#blur)" />
  
  <!-- Main image -->
  <image x="700" y="30" width="670" height="740" xlink:href="data:image/png;base64,{img_data}" preserveAspectRatio="xMidYMid slice"/>
  
  {f'''
  <!-- Read time section with proper width -->
  <g>
    <rect x="{left_padding}" y="{read_time_y}" width="580" height="70" fill="rgba(255,255,255,0.95)" rx="15" ry="15" filter="url(#shadow)"/>
    <g transform="translate({text_position}, {read_time_y + 35})">
      <!-- Clock icon -->
      <circle cx="15" cy="0" r="12" fill="none" stroke="#4a5568" stroke-width="2.5"/>
      <line x1="15" y1="0" x2="15" y2="-7" stroke="#4a5568" stroke-width="2.5"/>
      <line x1="15" y1="0" x2="20" y2="3" stroke="#4a5568" stroke-width="2.5"/>
      <text x="40" y="6" font-family="Poppins, Inter, Arial, sans-serif" font-size="32" font-weight="600" text-anchor="start" fill="#4a5568">{safe_read_time}</text>
    </g>
  </g>
  ''' if safe_read_time else ""}
  
  <!-- Article title with proper boundaries -->
  <rect x="{left_padding}" y="{title_y}" width="580" height="{title_height}" fill="rgba(255,255,255,0.1)" rx="15" ry="15" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
  {chr(10).join(line_elements)}
  
  {f'''
  <!-- Author info with proper positioning -->
  <g>
    <rect x="{left_padding}" y="{author_y}" width="580" height="100" fill="rgba(255,255,255,0.95)" rx="15" ry="15" filter="url(#shadow)"/>
    <circle cx="{text_position + 30}" cy="{author_y + 50}" r="28" fill="url(#dynamicGrad)"/>
    <text x="{text_position + 30}" y="{author_y + 58}" font-family="Poppins, Inter, Arial, sans-serif" font-size="26" font-weight="bold" text-anchor="middle" fill="white">{safe_author[0] if safe_author else ""}</text>
    <text x="{text_position + 75}" y="{author_y + 42}" font-family="Poppins, Inter, Arial, sans-serif" font-size="32" font-weight="bold" text-anchor="start" fill="#2d3748">{safe_author}</text>
    {f'<text x="{text_position + 75}" y="{author_y + 75}" font-family="Poppins, Inter, Arial, sans-serif" font-size="22" text-anchor="start" fill="#718096">{safe_publish_date}</text>' if safe_publish_date else ""}
  </g>
  ''' if safe_author else ""}
</svg>"""
    
    # Convert SVG to image
    try:
        # For now, we'll create a simple image composition using PIL
        # In a production environment, you might want to use a proper SVG renderer
        final_image = Image.new('RGB', (1400, 800), color='white')
        
        # Create a simple layout without SVG complexity
        draw = ImageDraw.Draw(final_image)
        
        # Draw background gradient (simplified)
        for i in range(800):
            color_ratio = i / 800
            r = int(colors.dominant.r * (1 - color_ratio) + colors.analogous1.r * color_ratio)
            g = int(colors.dominant.g * (1 - color_ratio) + colors.analogous1.g * color_ratio)
            b = int(colors.dominant.b * (1 - color_ratio) + colors.analogous1.b * color_ratio)
            draw.line([(0, i), (1400, i)], fill=(r, g, b))
        
        # Draw content area
        draw.rectangle([30, 30, 1370, 770], fill=(255, 255, 255, 240))
        
        # Draw left panel
        draw.rectangle([30, 30, 700, 770], fill=(colors.dominant.r, colors.dominant.g, colors.dominant.b, 200))
        
        # Paste the main image
        final_image.paste(image, (700, 30))
        
        # Load Google Fonts (Poppins and Inter)
        try:
            # Try to load Google Fonts from the fonts directory
            fonts_dir = Path("fonts")
            
            # Priority order: Poppins first, then Inter, then system fonts
            font_paths = []
            
            # Add Poppins fonts
            if (fonts_dir / "Poppins-Bold.ttf").exists():
                font_paths.append(str(fonts_dir / "Poppins-Bold.ttf"))
            if (fonts_dir / "Poppins-SemiBold.ttf").exists():
                font_paths.append(str(fonts_dir / "Poppins-SemiBold.ttf"))
            if (fonts_dir / "Poppins-Regular.ttf").exists():
                font_paths.append(str(fonts_dir / "Poppins-Regular.ttf"))
            
            # Add Inter fonts
            if (fonts_dir / "Inter-Bold.ttf").exists():
                font_paths.append(str(fonts_dir / "Inter-Bold.ttf"))
            if (fonts_dir / "Inter-Regular.ttf").exists():
                font_paths.append(str(fonts_dir / "Inter-Regular.ttf"))
            
            # Add system fonts as fallback
            font_paths.extend([
                "/System/Library/Fonts/Arial.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Times.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "arial.ttf",
                "Arial.ttf"
            ])
            
            font_title = None
            font_large = None 
            font_medium = None
            font_small = None
            
            for font_path in font_paths:
                try:
                    font_title = ImageFont.truetype(font_path, 55)  # Title font
                    font_large = ImageFont.truetype(font_path, 32)  # Large text
                    font_medium = ImageFont.truetype(font_path, 26) # Medium text
                    font_small = ImageFont.truetype(font_path, 22)  # Small text
                    
                    font_name = Path(font_path).name
                    print(f"✅ Successfully loaded Google Font: {font_name}")
                    break
                except (OSError, IOError):
                    continue
            
            # If no fonts found, use default
            if font_title is None:
                print("⚠️  No Google Fonts found, using default font")
                font_title = ImageFont.load_default()
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
                
        except Exception as e:
            print(f"❌ Font loading error: {e}")
            font_title = font_large = font_medium = font_small = ImageFont.load_default()
        
        # Draw title with proper positioning to stay in left panel
        y_offset = title_y + 65
        for line in title_lines:
            # Check if text would fit in the left panel
            bbox = draw.textbbox((0, 0), line, font=font_title)
            text_width = bbox[2] - bbox[0]
            
            # Adjust font size if text is too wide
            if text_width > max_text_width:
                # Use smaller font if text is too wide
                try:
                    smaller_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 45)
                    draw.text((text_position, y_offset), line, fill=font_color, font=smaller_font)
                except:
                    draw.text((text_position, y_offset), line, fill=font_color, font=font_large)
            else:
                draw.text((text_position, y_offset), line, fill=font_color, font=font_title)
            y_offset += 65
        
        # Draw read time with proper positioning
        if safe_read_time:
            draw.text((text_position, read_time_y + 35), safe_read_time, fill="#4a5568", font=font_large)
        
        # Draw author with proper positioning
        if safe_author:
            draw.text((image_x + 75, author_y + 42), safe_author, fill="#2d3748", font=font_large)
            if safe_publish_date:
                draw.text((image_x + 75, author_y + 75), safe_publish_date, fill="#718096", font=font_medium)
        
        # Convert to WebP
        output_buffer = io.BytesIO()
        final_image.save(output_buffer, format='WEBP', quality=90)
        return output_buffer.getvalue()
        
    except Exception as e:
        print(f"Error creating image: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating image: {str(e)}")

@app.get("/featured-image/options", response_model=OptionsResponse)
async def get_options():
    """Get available styles and patterns"""
    return OptionsResponse(
        styles=[
            StyleOption(value="modern", description="Clean gradient with analogous colors"),
            StyleOption(value="vibrant", description="Bold multi-color gradient"),
            StyleOption(value="subtle", description="Gentle two-tone gradient"),
            StyleOption(value="radial", description="Radial gradient from center")
        ],
        patterns=[
            StyleOption(value="none", description="No pattern overlay"),
            StyleOption(value="dots", description="Subtle dot pattern"),
            StyleOption(value="waves", description="Flowing wave pattern"),
            StyleOption(value="geometric", description="Geometric shapes pattern")
        ]
    )


@app.post("/featured-image/create")
async def create_featured_image(request: FeaturedImageRequest):
    """Create enhanced featured image"""
    try:
        # Download the main image
        image_data = await download_image(str(request.image_url))
        
        # Process author image if provided
        author_image_data = None
        if request.author_image:
            author_image_data = await image_url_to_data_url(str(request.author_image))
        
        # Create the enhanced featured image
        image_bytes = await create_enhanced_featured_image(
            image_data=image_data,
            article_title=request.article_title,
            read_time=request.read_time,
            author=request.author,
            publish_date=request.publish_date,
            author_image=author_image_data,
            style=request.style,
            pattern=request.pattern
        )
        
        return Response(
            content=image_bytes,
            media_type="image/webp",
            headers={
                "Content-Disposition": "attachment; filename=enhanced-featured-image.webp"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating featured image: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)