# API Documentation

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [User Management](#user-management)
  - [Register](#register)
  - [Login](#login)
- [WordPress Integration](#wordpress-integration)
  - [Connect WordPress Account](#connect-wordpress-account)
  - [Get WordPress Accounts](#get-wordpress-accounts)
  - [Update WordPress Account](#update-wordpress-account)
  - [Delete WordPress Account](#delete-wordpress-account)
  - [Test WordPress Connection](#test-wordpress-connection)
  - [Get WordPress Sites Info](#get-wordpress-sites-info)
- [Content Job Management](#content-job-management)
  - [Create Job](#create-job)
  - [Get My Jobs](#get-my-jobs)
  - [Update Job Outline](#update-job-outline)
  - [Get Job Outline](#get-job-outline)
  - [Approve Job](#approve-job)
  - [Unapprove Job](#unapprove-job)
  - [Get Job Status](#get-job-status)
- [System](#system)
  - [Health Check](#health-check)

## Overview

This API provides a comprehensive backend for blog content automation. It allows users to:

- Register and authenticate
- Connect to WordPress sites
- Create and manage content jobs
- Generate and update structured outlines for blog posts
- Approve content for publication

The API uses JWT token-based authentication and includes comprehensive validation for all data models.

## Authentication

The API uses Bearer token authentication. After logging in, you'll receive an access token that should be included in the `Authorization` header of all subsequent requests.

Example:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## User Management

### Register

Register a new user account.

**Endpoint:** `POST /register`

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword",
  "name": "John Doe"  // Optional
}
```

**Response:**
```json
{
  "msg": "User registered successfully"
}
```

**Status Codes:**
- `200 OK`: Registration successful
- `400 Bad Request`: Username or email already registered
- `500 Internal Server Error`: Server error during registration

### Login

Authenticate a user and get an access token.

**Endpoint:** `POST /login`

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "johndoe",
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Status Codes:**
- `200 OK`: Login successful
- `401 Unauthorized`: Incorrect username or password
- `500 Internal Server Error`: Server error during login

## WordPress Integration

### Connect WordPress Account

Connect a WordPress account to your user profile.

**Endpoint:** `POST /wordpress/connect`

**Authentication:** Required

**Request Body:**
```json
{
  "siteUrl": "https://example.com",
  "username": "wpuser",
  "applicationPassword": "xxxx xxxx xxxx xxxx xxxx xxxx"
}
```

**Response:**
```json
{
  "id": 1,
  "siteUrl": "https://example.com",
  "username": "wpuser",
  "userId": 123
}
```

**Status Codes:**
- `200 OK`: Connection successful
- `400 Bad Request`: Invalid WordPress credentials or site URL
- `500 Internal Server Error`: Server error

### Get WordPress Accounts

Get all WordPress accounts connected to your user profile.

**Endpoint:** `GET /wordpress/accounts`

**Authentication:** Required

**Response:**
```json
[
  {
    "id": 1,
    "siteUrl": "https://example.com",
    "username": "wpuser",
    "userId": 123
  },
  {
    "id": 2,
    "siteUrl": "https://another-site.com",
    "username": "wpuser2",
    "userId": 123
  }
]
```

**Status Codes:**
- `200 OK`: Request successful
- `500 Internal Server Error`: Server error

### Update WordPress Account

Update an existing WordPress account's credentials.

**Endpoint:** `PUT /wordpress/accounts/{account_id}`

**Authentication:** Required

**Path Parameters:**
- `account_id`: ID of the WordPress account to update

**Request Body:**
```json
{
  "siteUrl": "https://updated-example.com",  // Optional
  "username": "newuser",                    // Optional
  "applicationPassword": "new-password"     // Optional
}
```

**Response:**
```json
{
  "id": 1,
  "siteUrl": "https://updated-example.com",
  "username": "newuser",
  "userId": 123
}
```

**Status Codes:**
- `200 OK`: Update successful
- `400 Bad Request`: Invalid WordPress credentials
- `404 Not Found`: WordPress account not found
- `500 Internal Server Error`: Server error

### Delete WordPress Account

Delete a WordPress account connection.

**Endpoint:** `DELETE /wordpress/accounts/{account_id}`

**Authentication:** Required

**Path Parameters:**
- `account_id`: ID of the WordPress account to delete

**Response:**
```json
{
  "message": "WordPress account disconnected successfully"
}
```

**Status Codes:**
- `200 OK`: Deletion successful
- `404 Not Found`: WordPress account not found
- `500 Internal Server Error`: Server error

### Test WordPress Connection

Test if a WordPress account connection is working.

**Endpoint:** `POST /wordpress/test/{account_id}`

**Authentication:** Required

**Path Parameters:**
- `account_id`: ID of the WordPress account to test

**Response:**
```json
{
  "status": "success",
  "message": "WordPress connection is working"
}
```

or

```json
{
  "status": "error",
  "message": "WordPress connection failed"
}
```

**Status Codes:**
- `200 OK`: Test performed (check status in response)
- `404 Not Found`: WordPress account not found
- `500 Internal Server Error`: Server error

### Get WordPress Sites Info

Get detailed information about all connected WordPress sites.

**Endpoint:** `GET /wordpress/sites`

**Authentication:** Required

**Response:**
```json
{
  "sites": [
    {
      "id": 1,
      "siteUrl": "https://example.com",
      "username": "wpuser",
      "title": "My WordPress Site",
      "description": "A great blog about interesting topics",
      "status": "connected"
    },
    {
      "id": 2,
      "siteUrl": "https://problem-site.com",
      "username": "wpuser2",
      "title": "Connection Error",
      "description": "Unable to fetch site information",
      "status": "error"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Request successful
- `500 Internal Server Error`: Server error

## Content Job Management

### Create Job

Create a new content job with optional outline.

**Endpoint:** `POST /create-job`

**Authentication:** Required

**Request Body:**
```json
{
  "title": "How to Build a Garden",
  "main_keyword": "garden building",
  "related_keywords": "gardening, DIY garden",
  "article_word_count": 2000,
  "article_length": "long",
  "wordpress_credentials_id": 1,
  "competitor_url_1": "https://example.com/garden-article",
  "competitor_url_2": "https://another-site.com/garden-guide",
  "outline_prompt": "Write a comprehensive guide about building a garden",
  "contentFormat": "blog",
  "audienceType": "beginners",
  "toneOfVoice": "friendly",
  "Outline": {
    "title": "How to Build Your First Garden: A Complete Guide",
    "meta_description": "Learn everything you need to know about building your first garden with our step-by-step guide for beginners.",
    "main_keyword": "garden building",
    "target_audience": "beginners",
    "content_format": "blog post",
    "tone_of_voice": "friendly",
    "estimated_word_count": 2000,
    "sections": [
      {
        "section_number": 1,
        "title": "Introduction",
        "estimated_words": 300,
        "description": "Overview of the garden building process and benefits",
        "key_points": ["Why gardening is rewarding", "Overview of the process"],
        "keywords_to_include": ["garden building", "gardening benefits"]
      },
      {
        "section_number": 2,
        "title": "Planning Your Garden",
        "estimated_words": 500,
        "description": "How to plan your garden layout",
        "key_points": ["Choosing location", "Determining size"],
        "keywords_to_include": ["garden planning", "garden layout"]
      }
    ],
    "seo_keywords": {
      "primary_keywords": ["garden building", "DIY garden"],
      "secondary_keywords": ["beginner gardening", "garden layout"],
      "long_tail_keywords": ["how to build your first garden"]
    },
    "call_to_action": "Start building your garden today!",
    "faq_suggestions": [
      {
        "question": "How much does it cost to build a garden?",
        "answer_preview": "The cost varies depending on size and materials..."
      }
    ],
    "internal_linking_opportunities": ["Gardening tools article", "Plant selection guide"]
  }
}
```

**Response:**
```json
{
  "id": 123,
  "title": "How to Build a Garden",
  "main_keyword": "garden building",
  "related_keywords": "gardening, DIY garden",
  "article_word_count": 2000,
  "article_length": "long",
  "wordpress_credentials_id": 1,
  "competitor_url_1": "https://example.com/garden-article",
  "competitor_url_2": "https://another-site.com/garden-guide",
  "status": true,
  "isApproved": false,
  "semantic_keywords": {},
  "semantic_keywords_2": {},
  "outline": {
    "title": "How to Build Your First Garden: A Complete Guide",
    "meta_description": "Learn everything you need to know about building your first garden with our step-by-step guide for beginners.",
    "main_keyword": "garden building",
    "target_audience": "beginners",
    "content_format": "blog post",
    "tone_of_voice": "friendly",
    "estimated_word_count": 2000,
    "sections": [
      {
        "section_number": 1,
        "title": "Introduction",
        "estimated_words": 300,
        "description": "Overview of the garden building process and benefits",
        "key_points": ["Why gardening is rewarding", "Overview of the process"],
        "keywords_to_include": ["garden building", "gardening benefits"]
      },
      {
        "section_number": 2,
        "title": "Planning Your Garden",
        "estimated_words": 500,
        "description": "How to plan your garden layout",
        "key_points": ["Choosing location", "Determining size"],
        "keywords_to_include": ["garden planning", "garden layout"]
      }
    ],
    "seo_keywords": {
      "primary_keywords": ["garden building", "DIY garden"],
      "secondary_keywords": ["beginner gardening", "garden layout"],
      "long_tail_keywords": ["how to build your first garden"]
    },
    "call_to_action": "Start building your garden today!",
    "faq_suggestions": [
      {
        "question": "How much does it cost to build a garden?",
        "answer_preview": "The cost varies depending on size and materials..."
      }
    ],
    "internal_linking_opportunities": ["Gardening tools article", "Plant selection guide"]
  },
  "created_at": "2025-07-18T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Job created successfully
- `205`: Unauthorized WordPress account ID
- `422 Unprocessable Entity`: Invalid outline format
- `500 Internal Server Error`: Server error

### Get My Jobs

Get all content jobs created by the authenticated user.

**Endpoint:** `GET /my-jobs`

**Authentication:** Required

**Response:**
```json
[
  {
    "id": 123,
    "title": "How to Build a Garden",
    "main_keyword": "garden building",
    "related_keywords": "gardening, DIY garden",
    "article_word_count": 2000,
    "article_length": "long",
    "wordpress_credentials_id": 1,
    "competitor_url_1": "https://example.com/garden-article",
    "competitor_url_2": "https://another-site.com/garden-guide",
    "status": true,
    "isApproved": false,
    "semantic_keywords": {
      "primary": ["garden", "build"],
      "secondary": ["plants", "soil"]
    },
    "semantic_keywords_2": {
      "keywords": ["gardening", "DIY garden"]
    },
    "outline": {
      "title": "How to Build Your First Garden: A Complete Guide",
      "meta_description": "Learn everything you need to know about building your first garden with our step-by-step guide for beginners.",
      "main_keyword": "garden building"
      // ... rest of outline
    },
    "created_at": "2025-07-18T12:00:00.000Z"
  },
  // ... more jobs
]
```

**Status Codes:**
- `200 OK`: Request successful
- `500 Internal Server Error`: Server error retrieving jobs

### Update Job Outline

Update the outline for a specific content job.

**Endpoint:** `PUT /jobs/{job_id}/outline`

**Authentication:** Required

**Path Parameters:**
- `job_id`: ID of the job to update

**Request Body:**
```json
{
  "outline": {
    "title": "How to Build Your First Garden: A Complete Guide",
    "meta_description": "Learn everything you need to know about building your first garden with our step-by-step guide for beginners.",
    "main_keyword": "garden building",
    "target_audience": "beginners",
    "content_format": "blog post",
    "tone_of_voice": "friendly",
    "estimated_word_count": 2000,
    "sections": [
      {
        "section_number": 1,
        "title": "Introduction",
        "estimated_words": 300,
        "description": "Overview of the garden building process and benefits",
        "key_points": ["Why gardening is rewarding", "Overview of the process"],
        "keywords_to_include": ["garden building", "gardening benefits"]
      },
      {
        "section_number": 2,
        "title": "Planning Your Garden",
        "estimated_words": 500,
        "description": "How to plan your garden layout",
        "key_points": ["Choosing location", "Determining size"],
        "keywords_to_include": ["garden planning", "garden layout"]
      }
    ],
    "seo_keywords": {
      "primary_keywords": ["garden building", "DIY garden"],
      "secondary_keywords": ["beginner gardening", "garden layout"],
      "long_tail_keywords": ["how to build your first garden"]
    },
    "call_to_action": "Start building your garden today!",
    "faq_suggestions": [
      {
        "question": "How much does it cost to build a garden?",
        "answer_preview": "The cost varies depending on size and materials..."
      }
    ],
    "internal_linking_opportunities": ["Gardening tools article", "Plant selection guide"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Outline updated successfully",
  "job_id": 123,
  "updated_at": "2025-07-18T13:00:00.000Z",
  "outline": {
    // Full outline object
  }
}
```

**Status Codes:**
- `200 OK`: Outline updated successfully
- `400 Bad Request`: Cannot update outline for approved jobs, or section word counts don't match estimated total
- `404 Not Found`: Content job not found or you don't have permission to access it
- `422 Unprocessable Entity`: Validation error in outline
- `500 Internal Server Error`: Server error

### Get Job Outline

Get the current outline for a specific job.

**Endpoint:** `GET /jobs/{job_id}/outline`

**Authentication:** Required

**Path Parameters:**
- `job_id`: ID of the job to get the outline for

**Response:**
```json
{
  "job_id": 123,
  "title": "How to Build a Garden",
  "status": true,
  "has_outline": true,
  "outline": {
    "title": "How to Build Your First Garden: A Complete Guide",
    "meta_description": "Learn everything you need to know about building your first garden with our step-by-step guide for beginners.",
    "main_keyword": "garden building",
    // ... rest of outline
  },
  "created_at": "2025-07-18T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Request successful
- `404 Not Found`: Content job not found or you don't have permission to access it
- `500 Internal Server Error`: Server error

### Approve Job

Approve a job for processing (set isApproved to True).

**Endpoint:** `PUT /jobs/{job_id}/approve`

**Authentication:** Required

**Path Parameters:**
- `job_id`: ID of the job to approve

**Response:**
```json
{
  "success": true,
  "message": "Job approved successfully",
  "job_id": 123,
  "isApproved": true
}
```

**Status Codes:**
- `200 OK`: Job approved successfully (or was already approved)
- `400 Bad Request`: Cannot approve job without an outline
- `404 Not Found`: Content job not found or you don't have permission to access it
- `500 Internal Server Error`: Server error

### Unapprove Job

Unapprove a job (set isApproved to False).

**Endpoint:** `PUT /jobs/{job_id}/unapprove`

**Authentication:** Required

**Path Parameters:**
- `job_id`: ID of the job to unapprove

**Response:**
```json
{
  "success": true,
  "message": "Job unapproved successfully",
  "job_id": 123,
  "isApproved": false
}
```

**Status Codes:**
- `200 OK`: Job unapproved successfully (or was already unapproved)
- `404 Not Found`: Content job not found or you don't have permission to access it
- `500 Internal Server Error`: Server error

### Get Job Status

Get the status and approval status of a job.

**Endpoint:** `GET /jobs/{job_id}/status`

**Authentication:** Required

**Path Parameters:**
- `job_id`: ID of the job to check

**Response:**
```json
{
  "job_id": 123,
  "title": "How to Build a Garden",
  "status": true,
  "status_text": "outlined",
  "isApproved": false,
  "approval_text": "not approved",
  "has_outline": true,
  "created_at": "2025-07-18T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Request successful
- `404 Not Found`: Content job not found or you don't have permission to access it
- `500 Internal Server Error`: Server error

## System

### Health Check

Check if the API and database are working correctly.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

or

```json
{
  "status": "unhealthy",
  "error": "Error message details"
}
```

**Status Codes:**
- `200 OK`: Health check performed (check status in response)
