from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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


from models import WordPressCredentials

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
    from database import SessionLocal, engine
    from models import User, Base, ContentJob
    from auth import verify_password, get_password_hash, create_access_token
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
    status: str
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
                "status": job.status,
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
            status="pending",
            wordpress_credentials_id=job.wordpress_credentials_id
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

