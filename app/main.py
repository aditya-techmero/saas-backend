from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import logging
import traceback
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi.responses import FileResponse
import os
from fastapi import Header
import ast
import json


from .models import WordPressCredentials

from fastapi.security import OAuth2PasswordBearer
import jwt
import os
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="bearer")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Try to import your backend modules with error handling
try:
    from .database import SessionLocal, engine
    from .models import User, Base, ContentJob
    from .auth import verify_password, get_password_hash, create_access_token
    logger.info("Successfully imported app modules")
except ImportError as e:
    logger.error(f"Failed to import app modules: {e}")
    raise

# Don't create tables - they already exist in your database
# Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    name: Optional[str] = None  # Optional name field

class UserLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    name: str
    email: Optional[str] = None


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_bearer_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    return token


class ContentJobCreate(BaseModel):
    title: str
    main_keyword: str
    related_keywords: str
    article_word_count: int
    article_length: str
    wordpress_credentials_id: int
    competitor_url_1: Optional[str] = None
    competitor_url_2: Optional[str] = None
    outline_prompt : str
    contentFormat: Optional[str] = None
    audienceType: Optional[str] = None
    toneOfVoice: Optional[str] = None
    Outline: Optional[Dict[str, Any]] = None


class ContentJobOut(BaseModel):
    id: int
    title: str
    main_keyword: str
    related_keywords: str
    article_word_count: int
    article_length: str
    wordpress_credentials_id: int
    competitor_url_1: Optional[str] = None
    competitor_url_2: Optional[str] = None
    status: bool  # Changed from str to bool
    isApproved: bool  # New field for approval status
    semantic_keywords: Optional[List[str]] = None
    semantic_keywords_2: Optional[List[str]] = None
    outline: Optional[Dict[str, Any]] = None
    created_at: str
    
    class Config:
        from_attributes = True

class WordPressCredentialsCreate(BaseModel):
    siteUrl: str
    username: str
    applicationPassword: str

class WordPressCredentialsOut(BaseModel):
    id: int
    siteUrl: str
    username: str
    userId: int
    
    class Config:
        from_attributes = True

class WordPressCredentialsUpdate(BaseModel):
    siteUrl: Optional[str] = None
    username: Optional[str] = None
    applicationPassword: Optional[str] = None

# ===== OUTLINE SCHEMA MODELS =====

class OutlineSection(BaseModel):
    section_number: int = Field(ge=1, description="Section number starting from 1")
    title: str = Field(min_length=1, max_length=200, description="Section title")
    estimated_words: int = Field(ge=1, le=5000, description="Estimated word count for this section")
    description: str = Field(min_length=1, max_length=1000, description="Description of what this section covers")
    key_points: List[str] = Field(min_items=1, max_items=10, description="Key points to cover in this section")
    keywords_to_include: List[str] = Field(max_items=20, description="Keywords to include in this section")
    
    @validator('key_points')
    def validate_key_points(cls, v):
        if not v:
            raise ValueError('At least one key point is required')
        for point in v:
            if not point.strip():
                raise ValueError('Key points cannot be empty')
        return [point.strip() for point in v]
    
    @validator('keywords_to_include')
    def validate_keywords(cls, v):
        return [kw.strip() for kw in v if kw.strip()]

class OutlineSEOKeywords(BaseModel):
    primary_keywords: List[str] = Field(min_items=1, max_items=50, description="Primary keywords for SEO")
    secondary_keywords: List[str] = Field(max_items=100, description="Secondary keywords for SEO")
    long_tail_keywords: List[str] = Field(max_items=100, description="Long-tail keywords for SEO")
    
    @validator('primary_keywords')
    def validate_primary_keywords(cls, v):
        if not v:
            raise ValueError('At least one primary keyword is required')
        for kw in v:
            if not kw.strip():
                raise ValueError('Primary keywords cannot be empty')
        return [kw.strip() for kw in v]
    
    @validator('secondary_keywords', 'long_tail_keywords')
    def validate_keyword_lists(cls, v):
        return [kw.strip() for kw in v if kw.strip()]

class OutlineFAQ(BaseModel):
    question: str = Field(min_length=1, max_length=500, description="FAQ question")
    answer_preview: str = Field(min_length=1, max_length=1000, description="Brief preview of the answer")

class OutlineSchema(BaseModel):
    title: str = Field(min_length=1, max_length=300, description="Blog post title")
    meta_description: str = Field(min_length=120, max_length=160, description="SEO meta description")
    main_keyword: str = Field(min_length=1, max_length=100, description="Primary keyword for SEO")
    target_audience: str = Field(min_length=1, max_length=100, description="Target audience")
    content_format: str = Field(min_length=1, max_length=50, description="Content format (e.g., blog post, guide)")
    tone_of_voice: str = Field(min_length=1, max_length=50, description="Tone of voice for the content")
    estimated_word_count: int = Field(ge=300, le=10000, description="Estimated total word count")
    sections: List[OutlineSection] = Field(min_items=2, max_items=15, description="Content sections")
    seo_keywords: OutlineSEOKeywords = Field(description="SEO keywords categorized by type")
    call_to_action: str = Field(min_length=1, max_length=500, description="Call to action for the end of the article")
    faq_suggestions: List[OutlineFAQ] = Field(max_items=20, description="FAQ suggestions")
    internal_linking_opportunities: List[str] = Field(max_items=50, description="Internal linking opportunities")
    generated_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat(), description="Generation timestamp")
    
    @validator('sections')
    def validate_sections(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 sections are required (introduction and conclusion)')
        
        # Check for duplicate section numbers
        section_numbers = [s.section_number for s in v]
        if len(set(section_numbers)) != len(section_numbers):
            raise ValueError('Section numbers must be unique')
        
        # Check if sections are properly numbered (sequential)
        sorted_numbers = sorted(section_numbers)
        if sorted_numbers != list(range(1, len(sorted_numbers) + 1)):
            raise ValueError('Section numbers must be sequential starting from 1')
        
        return v
    
    @validator('faq_suggestions')
    def validate_faq_suggestions(cls, v):
        return v  # FAQ suggestions are optional, so empty list is allowed
    
    @validator('internal_linking_opportunities')
    def validate_internal_linking(cls, v):
        return [link.strip() for link in v if link.strip()]

class OutlineUpdateRequest(BaseModel):
    outline: OutlineSchema = Field(description="Complete outline data following the schema")

class OutlineUpdateResponse(BaseModel):
    success: bool
    message: str
    job_id: int
    updated_at: str
    outline: Optional[Dict[str, Any]] = None

# ===== END OUTLINE SCHEMA MODELS =====

# WordPress API validation function
def validate_wordpress_credentials(site_url: str, username: str, app_password: str) -> bool:
    """
    Validate WordPress credentials by making a test API call
    """
    try:
        # Clean up the site URL
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        
        # Remove trailing slash
        site_url = site_url.rstrip('/')
        
        # Test endpoint - get current user info
        test_url = f"{site_url}/wp-json/wp/v2/users/me"
        
        response = requests.get(
            test_url,
            auth=(username, app_password),
            timeout=10
        )
        
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"WordPress validation error: {e}")
        return False







# Endpoint to register, login  a new user. 

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for username: {user.username}")
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            logger.warning(f"Username {user.username} already exists")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists (if email column exists)
        try:
            existing_email = db.query(User).filter(User.email == user.email).first()
            if existing_email:
                logger.warning(f"Email {user.email} already exists")
                raise HTTPException(status_code=400, detail="Email already registered")
        except Exception as e:
            logger.warning(f"Email check failed (column might not exist): {e}")
        
        # Create new user
        logger.info("Creating new user")
        hashed_pw = get_password_hash(user.password)
        
        # Create user with fields that exist in your database
        new_user = User(
            username=user.username,
            name=user.name or user.username,  # Use username as name if not provided
            password=hashed_pw,
            role='user'
        )
        
        # Only add email if the column exists
        if hasattr(User, 'email') and user.email:
            new_user.email = user.email
            
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User {user.username} registered successfully")
        return {"msg": "User registered successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/login", response_model=LoginResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username: {user.username}")
    
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        
        if not db_user:
            logger.warning(f"User {user.username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not verify_password(user.password, db_user.password):
            logger.warning(f"Incorrect password for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        token = create_access_token({"sub": user.username})
        
        logger.info(f"User {user.username} logged in successfully")

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            username=db_user.username,
            name=db_user.name,
            email=db_user.email if hasattr(db_user, 'email') else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
def root():
    index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return FileResponse(index_path)

@app.get("/health")
def health_check():
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/my-jobs", response_model=List[ContentJobOut])
def get_my_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        jobs = db.query(ContentJob).filter(ContentJob.user_id == current_user.id).order_by(ContentJob.created_at.desc()).all()
        
        # Convert jobs to the response format
        job_list = []
        for job in jobs:
            # Parse outline safely if it's a string
            outline = {}
            if job.Outline:
                if isinstance(job.Outline, dict):
                    outline = job.Outline
                elif isinstance(job.Outline, str):
                    try:
                        outline = json.loads(job.Outline)
                    except json.JSONDecodeError:
                        try:
                            outline = ast.literal_eval(job.Outline)
                        except (ValueError, SyntaxError):
                            outline = {}

            job_dict = {
                "id": job.id,
                "title": job.title,
                "main_keyword": job.mainKeyword,
                "related_keywords": job.related_keywords,
                "article_word_count": job.article_word_count,
                "article_length": job.article_length,
                "competitor_url_1": job.competitor_url_1,
                "competitor_url_2": job.competitor_url_2,
                "status": job.status,  # Now boolean
                "isApproved": job.isApproved,  # New field
                "semantic_keywords": job.semantic_keywords if job.semantic_keywords else [],
                "semantic_keywords_2": job.semantic_keywords_2 if job.semantic_keywords_2 else [],
                "outline": outline,
                "created_at": job.created_at.isoformat() if isinstance(job.created_at, datetime) else str(job.created_at),
                "wordpress_credentials_id": job.wordpress_credentials_id,  # <-- Add this line
            }
            job_list.append(job_dict)
        
        return job_list
    except Exception as e:
        logger.error(f"Error retrieving jobs: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve jobs: {str(e)}")


@app.post("/create-job", response_model=ContentJobOut)
def create_job(
    job: ContentJobCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        # ✅ Check if the given WordPress account belongs to this user
        wp_account = db.query(WordPressCredentials).filter(
            WordPressCredentials.id == job.wordpress_credentials_id,
            WordPressCredentials.userId == current_user.id
        ).first()

        if not wp_account:
            raise HTTPException(status_code=205, detail="Unauthorized WordPress account ID")

        # Handle optional outline with validation
        outline_json = None
        job_status = False  # False = pending, True = outlined
        
        if job.Outline:
            try:
                # Validate outline against schema if provided
                outline_schema = OutlineSchema(**job.Outline)
                outline_json = json.dumps(outline_schema.dict(), indent=2)
                job_status = True  # True = outlined
                logger.info(f"Job created with valid outline for user {current_user.username}")
            except Exception as e:
                logger.warning(f"Invalid outline provided during job creation: {e}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid outline format: {str(e)}"
                )

        new_job = ContentJob(
            user_id=current_user.id,
            title=job.title,
            mainKeyword=job.main_keyword,
            related_keywords=job.related_keywords,
            article_word_count=job.article_word_count,
            article_length=job.article_length,
            competitor_url_1=job.competitor_url_1,
            competitor_url_2=job.competitor_url_2,
            outline_prompt=job.outline_prompt,
            contentFormat=job.contentFormat,
            audienceType=job.audienceType,
            toneOfVoice=job.toneOfVoice,
            status=job_status,
            isApproved=False,  # Default to not approved
            wordpress_credentials_id=job.wordpress_credentials_id,
            Outline=outline_json
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        return ContentJobOut(
            id=new_job.id,
            title=new_job.title,
            main_keyword=new_job.mainKeyword,
            related_keywords=new_job.related_keywords,
            article_word_count=new_job.article_word_count,
            article_length=new_job.article_length,
            competitor_url_1=new_job.competitor_url_1,
            competitor_url_2=new_job.competitor_url_2,
            status=new_job.status,
            isApproved=new_job.isApproved,
            semantic_keywords=new_job.semantic_keywords,
            semantic_keywords_2=new_job.semantic_keywords_2,
            outline=json.loads(new_job.Outline) if new_job.Outline else {},
            created_at=new_job.created_at.isoformat() if isinstance(new_job.created_at, datetime) else str(new_job.created_at),
            wordpress_credentials_id=new_job.wordpress_credentials_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")





# Endpoint to connect a WordPress account and related things.

@app.post("/wordpress/connect", response_model=WordPressCredentialsOut)
def connect_wordpress_account(
    credentials: WordPressCredentialsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect a new WordPress account to the user's profile
    """
    try:
        # Clean up site URL
        site_url = credentials.siteUrl.strip()
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        site_url = site_url.rstrip('/')
        
        # Validate WordPress credentials
        if not validate_wordpress_credentials(site_url, credentials.username, credentials.applicationPassword):
            raise HTTPException(
                status_code=400,
                detail="Invalid WordPress credentials or site URL"
            )
        
        # Check if this WordPress account is already connected to ANY user
        existing_wp = db.query(WordPressCredentials).filter(
            WordPressCredentials.siteUrl == site_url,
            WordPressCredentials.username == credentials.username
        ).first()
        
        if existing_wp:
            # If it's already connected to the current user, return the existing record
            if existing_wp.userId == current_user.id:
                return WordPressCredentialsOut(
                    id=existing_wp.id,
                    siteUrl=existing_wp.siteUrl,
                    username=existing_wp.username,
                    userId=existing_wp.userId
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="This WordPress account is already connected to another user"
                )
        
        # Also check if the current user already has this site connected (different check)
        existing_site = db.query(WordPressCredentials).filter(
            WordPressCredentials.siteUrl == site_url,
            WordPressCredentials.userId == current_user.id
        ).first()
        
        if existing_site:
            # Update the existing record instead of creating a new one
            existing_site.username = credentials.username
            existing_site.applicationPassword = credentials.applicationPassword
            
            try:
                db.commit()
                db.refresh(existing_site)
                
                logger.info(f"WordPress account updated for user {current_user.username}: {site_url}")
                
                return WordPressCredentialsOut(
                    id=existing_site.id,
                    siteUrl=existing_site.siteUrl,
                    username=existing_site.username,
                    userId=existing_site.userId
                )
            except Exception as db_error:
                db.rollback()
                logger.error(f"Error updating WordPress credentials: {db_error}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update WordPress credentials"
                )
        
        # Create new WordPress credentials entry
        new_wp_creds = WordPressCredentials(
            userId=current_user.id,
            siteUrl=site_url,
            username=credentials.username,
            applicationPassword=credentials.applicationPassword
        )
        
        try:
            db.add(new_wp_creds)
            db.commit()
            db.refresh(new_wp_creds)
        except Exception as db_error:
            db.rollback()
            if "duplicate key value violates unique constraint" in str(db_error):
                # Handle the case where there's a sequence issue or duplicate
                logger.warning(f"Database constraint violation when connecting WordPress account: {db_error}")
                raise HTTPException(
                    status_code=400,
                    detail="This WordPress account connection already exists or there's a database conflict"
                )
            else:
                # Re-raise other database errors
                raise
        
        logger.info(f"WordPress account connected for user {current_user.username}: {site_url}")
        
        return WordPressCredentialsOut(
            id=new_wp_creds.id,
            siteUrl=new_wp_creds.siteUrl,
            username=new_wp_creds.username,
            userId=new_wp_creds.userId
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting WordPress account: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to connect WordPress account: {str(e)}")

@app.get("/wordpress/accounts", response_model=List[WordPressCredentialsOut])
def get_wordpress_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all WordPress accounts connected to the current user
    """
    try:
        wp_accounts = db.query(WordPressCredentials).filter(
            WordPressCredentials.userId == current_user.id
        ).all()
        
        return [
            WordPressCredentialsOut(
                id=account.id,
                siteUrl=account.siteUrl,
                username=account.username,
                userId=account.userId
            )
            for account in wp_accounts
        ]
    
    except Exception as e:
        logger.error(f"Error retrieving WordPress accounts: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve WordPress accounts: {str(e)}")


@app.put("/wordpress/accounts/{account_id}", response_model=WordPressCredentialsOut)
def update_wordpress_account(
    account_id: int,
    credentials: WordPressCredentialsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a WordPress account's credentials
    """
    try:
        # Find the WordPress account
        wp_account = db.query(WordPressCredentials).filter(
            WordPressCredentials.id == account_id,
            WordPressCredentials.userId == current_user.id
        ).first()
        
        if not wp_account:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        # Update fields if provided
        if credentials.siteUrl:
            site_url = credentials.siteUrl.strip()
            if not site_url.startswith(('http://', 'https://')):
                site_url = 'https://' + site_url
            site_url = site_url.rstrip('/')
            wp_account.siteUrl = site_url
        
        if credentials.username:
            wp_account.username = credentials.username
        
        if credentials.applicationPassword:
            wp_account.applicationPassword = credentials.applicationPassword
        
        # Validate updated credentials
        if not validate_wordpress_credentials(
            wp_account.siteUrl, 
            wp_account.username, 
            wp_account.applicationPassword
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid WordPress credentials"
            )
        
        db.commit()
        db.refresh(wp_account)
        
        logger.info(f"WordPress account updated for user {current_user.username}: {wp_account.siteUrl}")
        
        return WordPressCredentialsOut(
            id=wp_account.id,
            siteUrl=wp_account.siteUrl,
            username=wp_account.username,
            userId=wp_account.userId
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating WordPress account: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update WordPress account: {str(e)}")

@app.delete("/wordpress/accounts/{account_id}")
def delete_wordpress_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a WordPress account connection
    """
    try:
        # Find the WordPress account
        wp_account = db.query(WordPressCredentials).filter(
            WordPressCredentials.id == account_id,
            WordPressCredentials.userId == current_user.id
        ).first()
        
        if not wp_account:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        db.delete(wp_account)
        db.commit()
        
        logger.info(f"WordPress account deleted for user {current_user.username}: {wp_account.siteUrl}")
        
        return {"message": "WordPress account disconnected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting WordPress account: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete WordPress account: {str(e)}")

@app.post("/wordpress/test/{account_id}")
def test_wordpress_connection(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test a WordPress account connection
    """
    try:
        # Find the WordPress account
        wp_account = db.query(WordPressCredentials).filter(
            WordPressCredentials.id == account_id,
            WordPressCredentials.userId == current_user.id
        ).first()
        
        if not wp_account:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        # Test the connection
        is_valid = validate_wordpress_credentials(
            wp_account.siteUrl,
            wp_account.username,
            wp_account.applicationPassword
        )
        
        if is_valid:
            return {"status": "success", "message": "WordPress connection is working"}
        else:
            return {"status": "error", "message": "WordPress connection failed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to test WordPress connection: {str(e)}")

@app.get("/wordpress/sites")
def get_wordpress_sites_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about all connected WordPress sites
    """
    try:
        wp_accounts = db.query(WordPressCredentials).filter(
            WordPressCredentials.userId == current_user.id
        ).all()
        
        sites_info = []
        
        for account in wp_accounts:
            try:
                # Get site information
                site_info_url = f"{account.siteUrl}/wp-json/wp/v2/settings"
                response = requests.get(
                    site_info_url,
                    auth=(account.username, account.applicationPassword),
                    timeout=10
                )
                
                if response.status_code == 200:
                    site_data = response.json()
                    sites_info.append({
                        "id": account.id,
                        "siteUrl": account.siteUrl,
                        "username": account.username,
                        "title": site_data.get("title", "Unknown"),
                        "description": site_data.get("description", ""),
                        "status": "connected"
                    })
                else:
                    sites_info.append({
                        "id": account.id,
                        "siteUrl": account.siteUrl,
                        "username": account.username,
                        "title": "Connection Error",
                        "description": "Unable to fetch site information",
                        "status": "error"
                    })
            except Exception as e:
                logger.warning(f"Failed to get info for {account.siteUrl}: {e}")
                sites_info.append({
                    "id": account.id,
                    "siteUrl": account.siteUrl,
                    "username": account.username,
                    "title": "Connection Error",
                    "description": str(e),
                    "status": "error"
                })
        
        return {"sites": sites_info}
    
    except Exception as e:
        logger.error(f"Error retrieving WordPress sites info: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve WordPress sites info: {str(e)}")


# ===== JOB OUTLINE UPDATE ENDPOINT =====

@app.put("/jobs/{job_id}/outline", response_model=OutlineUpdateResponse)
def update_job_outline(
    job_id: int,
    request: OutlineUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a job's outline with comprehensive validation.
    
    This endpoint allows users to update the outline for a specific content job.
    The outline must follow the strict JSON schema with all required fields.
    """
    try:
        # Validate job exists and belongs to current user
        job = db.query(ContentJob).filter(
            ContentJob.id == job_id,
            ContentJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404, 
                detail="Content job not found or you don't have permission to access it"
            )
        
        # Additional business logic validation
        if job.isApproved:
            raise HTTPException(
                status_code=400,
                detail="Cannot update outline for approved jobs"
            )
        
        # Validate word count consistency
        total_estimated_words = sum(section.estimated_words for section in request.outline.sections)
        word_count_diff = abs(total_estimated_words - request.outline.estimated_word_count)
        
        if word_count_diff > (request.outline.estimated_word_count * 0.2):  # Allow 20% variance
            raise HTTPException(
                status_code=400,
                detail=f"Section word counts ({total_estimated_words}) don't match estimated total ({request.outline.estimated_word_count}). Difference should be within 20%."
            )
        
        # Validate that main keyword appears in outline
        main_keyword = request.outline.main_keyword.lower()
        title_contains_keyword = main_keyword in request.outline.title.lower()
        meta_contains_keyword = main_keyword in request.outline.meta_description.lower()
        
        if not (title_contains_keyword or meta_contains_keyword):
            logger.warning(f"Main keyword '{main_keyword}' not found in title or meta description for job {job_id}")
        
        # Convert outline to JSON and update job
        outline_json = request.outline.dict()
        outline_json["updated_at"] = datetime.now().isoformat()
        
        # Update the job in database
        job.Outline = json.dumps(outline_json, indent=2)
        job.status = True  # True = outlined
        
        db.commit()
        
        logger.info(f"Successfully updated outline for job {job_id} by user {current_user.username}")
        
        return OutlineUpdateResponse(
            success=True,
            message="Outline updated successfully",
            job_id=job_id,
            updated_at=outline_json["updated_at"],
            outline=outline_json
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating job outline: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update job outline: {str(e)}"
        )

@app.get("/jobs/{job_id}/outline")
def get_job_outline(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current outline for a specific job.
    """
    try:
        # Validate job exists and belongs to current user
        job = db.query(ContentJob).filter(
            ContentJob.id == job_id,
            ContentJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Content job not found or you don't have permission to access it"
            )
        
        # Parse outline if it exists
        outline_data = {}
        if job.Outline:
            try:
                outline_data = json.loads(job.Outline)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in outline for job {job_id}")
                outline_data = {}
        
        return {
            "job_id": job_id,
            "title": job.title,
            "status": job.status,
            "has_outline": bool(job.Outline),
            "outline": outline_data,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job outline: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job outline: {str(e)}"
        )

# ===== JOB APPROVAL ENDPOINTS =====

@app.put("/jobs/{job_id}/approve")
def approve_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a job (set isApproved to True)
    """
    try:
        # Validate job exists and belongs to current user
        job = db.query(ContentJob).filter(
            ContentJob.id == job_id,
            ContentJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Content job not found or you don't have permission to access it"
            )
        
        # Check if job has an outline
        if not job.status:
            raise HTTPException(
                status_code=400,
                detail="Cannot approve job without an outline. Please create an outline first."
            )
        
        # Check if already approved
        if job.isApproved:
            return {
                "success": True,
                "message": "Job is already approved",
                "job_id": job_id,
                "isApproved": True
            }
        
        # Approve the job
        job.isApproved = True
        db.commit()
        
        logger.info(f"Job {job_id} approved by user {current_user.username}")
        
        return {
            "success": True,
            "message": "Job approved successfully",
            "job_id": job_id,
            "isApproved": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving job: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve job: {str(e)}"
        )

@app.put("/jobs/{job_id}/unapprove")
def unapprove_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unapprove a job (set isApproved to False)
    """
    try:
        # Validate job exists and belongs to current user
        job = db.query(ContentJob).filter(
            ContentJob.id == job_id,
            ContentJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Content job not found or you don't have permission to access it"
            )
        
        # Check if already unapproved
        if not job.isApproved:
            return {
                "success": True,
                "message": "Job is already unapproved",
                "job_id": job_id,
                "isApproved": False
            }
        
        # Unapprove the job
        job.isApproved = False
        db.commit()
        
        logger.info(f"Job {job_id} unapproved by user {current_user.username}")
        
        return {
            "success": True,
            "message": "Job unapproved successfully",
            "job_id": job_id,
            "isApproved": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unapproving job: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unapprove job: {str(e)}"
        )

@app.get("/jobs/{job_id}/status")
def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status and approval status of a job
    """
    try:
        # Validate job exists and belongs to current user
        job = db.query(ContentJob).filter(
            ContentJob.id == job_id,
            ContentJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Content job not found or you don't have permission to access it"
            )
        
        # Convert boolean status to readable format
        status_text = "outlined" if job.status else "pending"
        approval_text = "approved" if job.isApproved else "not approved"
        
        return {
            "job_id": job_id,
            "title": job.title,
            "status": job.status,
            "status_text": status_text,
            "isApproved": job.isApproved,
            "approval_text": approval_text,
            "has_outline": bool(job.Outline),
            "created_at": job.created_at.isoformat() if job.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job status: {str(e)}"
        )

