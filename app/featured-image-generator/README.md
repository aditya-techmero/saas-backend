# Featured Image Generator

A FastAPI service that creates beautiful featured images with Google Fonts support (Poppins and Inter).

## Features

- ✅ **Google Fonts Integration**: Uses Poppins and Inter fonts for modern typography
- ✅ **Dynamic Color Extraction**: Automatically extracts colors from input images
- ✅ **Multiple Gradient Styles**: Modern, vibrant, subtle, and radial gradients
- ✅ **Pattern Overlays**: Dots, waves, geometric patterns, or none
- ✅ **Smart Text Layout**: Automatic text wrapping and positioning
- ✅ **WebP Output**: Optimized image format for web use
- ✅ **Automatic Fallbacks**: System fonts if Google Fonts unavailable

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python run_server.py
```

The API will be available at `http://localhost:8001`

## API Endpoints

### Health Check
```http
GET /health
```

### Get Available Options
```http
GET /options
```

### Create Featured Image
```http
POST /featured-image/create
```

**Request Body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "article_title": "Your Article Title",
  "read_time": "5 min read",
  "author": "Author Name",
  "publish_date": "July 16, 2025",
  "style": "modern",
  "pattern": "geometric"
}
```

## Styles

- **modern**: Clean, minimal design with subtle gradients
- **vibrant**: Bold colors and dynamic gradients
- **subtle**: Muted tones with soft transitions
- **radial**: Radial gradients from center outward

## Patterns

- **none**: No background pattern
- **dots**: Subtle dot pattern overlay
- **waves**: Flowing wave pattern
- **geometric**: Modern geometric shapes

## Font Configuration

The generator uses Google Fonts in this priority order:
1. **Poppins-Bold.ttf** (Primary)
2. **Poppins-SemiBold.ttf**
3. **Poppins-Regular.ttf**
4. **Inter-Bold.ttf**
5. **Inter-Regular.ttf**
6. **System fonts** (Fallback)

## Project Structure

```
featured-image-generator/
├── main.py                 # Main FastAPI application
├── run_server.py          # Server startup script
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── download_fonts.py     # Font download utility
├── fonts/                # Google Fonts directory
│   ├── Poppins-Bold.ttf
│   ├── Poppins-Regular.ttf
│   ├── Poppins-SemiBold.ttf
│   ├── Inter-Bold.ttf
│   └── Inter-Regular.ttf
└── README.md             # This file
```

## Usage Example

```python
import requests

# Create a featured image
response = requests.post(
    "http://localhost:8000/featured-image/create",
    json={
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
        "article_title": "Modern Web Development",
        "read_time": "8 min read",
        "author": "Developer",
        "publish_date": "July 2025",
        "style": "vibrant",
        "pattern": "dots"
    }
)

# Save the image
with open("featured-image.webp", "wb") as f:
    f.write(response.content)
```

## Customization

### Adding New Fonts
1. Place font files in the `fonts/` directory
2. Update the font loading logic in `main.py`
3. Restart the server

### Modifying Styles
Edit the `create_gradient_background()` function in `main.py` to add new gradient styles.

### Adding Patterns
Extend the `add_pattern_overlay()` function in `main.py` to include new pattern types.

## Requirements

- Python 3.8+
- FastAPI
- Pillow (PIL)
- httpx
- uvicorn

## License

This project is open source and available under the MIT License.
