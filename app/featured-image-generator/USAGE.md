# 🚀 Featured Image Generator - Complete Package

## 📦 What's Included

This is a complete, portable **Featured Image Generator** package that you can copy to any project. It includes:

- ✅ **Complete FastAPI Application** (`main.py`)
- ✅ **Google Fonts Integration** (Poppins & Inter)
- ✅ **All Dependencies** (`requirements.txt`, `pyproject.toml`)
- ✅ **Easy Setup Scripts** (`setup.py`, `start.py`)
- ✅ **Usage Examples** (`example.py`)
- ✅ **Font Management** (`download_fonts.py`)
- ✅ **Complete Documentation** (`README.md`)

## 🎯 Quick Start (3 Steps)

### 1. Copy the Package
```bash
# Copy the entire featured-image-generator folder to your project
cp -r featured-image-generator /path/to/your/project/
cd /path/to/your/project/featured-image-generator
```

### 2. One-Command Setup & Start
```bash
python start.py
```

This will:
- ✅ Check Python version
- ✅ Install all dependencies
- ✅ Verify Google Fonts
- ✅ Start the server at `http://localhost:8000`

### 3. Test the API
```bash
# In another terminal
python example.py
```

## 🛠️ Manual Setup (Alternative)

If you prefer step-by-step setup:

```bash
# 1. Setup environment and dependencies
python setup.py

# 2. Start the server
python run_server.py

# 3. Test the API
python example.py
```

## 📋 API Usage

### Create Featured Image
```bash
curl -X POST "http://localhost:8000/featured-image/create" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
    "article_title": "My Amazing Article",
    "read_time": "5 min read",
    "author": "Your Name",
    "publish_date": "July 2025",
    "style": "modern",
    "pattern": "geometric"
  }' \
  --output featured-image.webp
```

### Available Endpoints
- `GET /health` - Health check
- `GET /options` - Available styles and patterns
- `POST /featured-image/create` - Create featured image
- `GET /docs` - Interactive API documentation

## 🎨 Customization

### Styles
- **modern**: Clean, minimal design
- **vibrant**: Bold, dynamic colors
- **subtle**: Muted, soft tones
- **radial**: Radial gradients

### Patterns
- **none**: No pattern overlay
- **dots**: Subtle dot pattern
- **waves**: Flowing wave pattern
- **geometric**: Modern geometric shapes

### Fonts
- **Primary**: Poppins (Google Fonts)
- **Secondary**: Inter (Google Fonts)
- **Fallback**: System fonts

## 📁 Package Structure

```
featured-image-generator/
├── main.py              # 🚀 Main FastAPI application
├── start.py             # 🎯 Quick start script
├── setup.py             # 🛠️ Setup and dependency installer
├── run_server.py        # 🌐 Server startup script
├── example.py           # 📖 Usage example
├── download_fonts.py    # 🔤 Font download utility
├── requirements.txt     # 📦 Python dependencies
├── pyproject.toml       # ⚙️ Project configuration
├── .gitignore          # 🚫 Git ignore rules
├── README.md           # 📚 Detailed documentation
├── USAGE.md            # 📋 This file
└── fonts/              # 🔤 Google Fonts directory
    ├── Poppins-Bold.ttf
    ├── Poppins-Regular.ttf
    ├── Poppins-SemiBold.ttf
    ├── Inter-Bold.ttf
    └── Inter-Regular.ttf
```

## 🔧 Integration with Your Project

### Option 1: Standalone Service
Run as a separate microservice:
```bash
cd featured-image-generator
python start.py
```

### Option 2: Import into Existing FastAPI App
```python
from featured_image_generator.main import app as featured_image_app
from fastapi import FastAPI

app = FastAPI()
app.mount("/featured-image", featured_image_app)
```

### Option 3: Use as Library
```python
from featured_image_generator.main import create_featured_image
from featured_image_generator.main import FeaturedImageRequest

# Create request
request = FeaturedImageRequest(
    image_url="https://example.com/image.jpg",
    article_title="My Article",
    author="Author Name",
    style="modern"
)

# Generate image
image_data = await create_featured_image(request)
```

## 🌟 Features

- ✅ **Google Fonts**: Professional typography with Poppins and Inter
- ✅ **Dynamic Colors**: Automatic color extraction from images
- ✅ **Multiple Styles**: 4 gradient styles and 4 pattern options
- ✅ **Smart Layout**: Automatic text wrapping and positioning
- ✅ **WebP Output**: Optimized for web performance
- ✅ **Error Handling**: Graceful fallbacks for missing fonts/images
- ✅ **Fast API**: Built on FastAPI with automatic docs
- ✅ **Portable**: Self-contained package with all dependencies

## 🎉 Ready to Use!

Your Featured Image Generator package is **complete and ready to use**. Just copy the folder to any project and run `python start.py` to get started!

**Perfect for:**
- 📝 Blog platforms
- 📰 News websites  
- 🎨 Content management systems
- 📱 Social media tools
- 🛒 E-commerce sites

## 💡 Need Help?

1. **Check the logs**: The server provides detailed logging
2. **Visit `/docs`**: Interactive API documentation
3. **Run examples**: Use `python example.py` to test
4. **Check fonts**: Run `python download_fonts.py` if needed

**Happy image generating! 🎨✨**
