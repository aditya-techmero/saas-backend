# Flow Diagrams for Blog Automation System

This document contains flow diagrams illustrating the architecture and processes of the blog automation system. The diagrams are created using Mermaid.js and cover three main categories:

1. API Flow and Authentication
2. Outline Generation Process
3. Blog Generation and WordPress Posting

## 1. API Flow and Authentication

This diagram illustrates the overall API architecture, including user authentication, WordPress integration, and job management.

```mermaid
flowchart TD
    subgraph Authentication
        Register["POST /register"] --> DB[(Database)]
        Login["POST /login"] --> DB
        Login -- "JWT Token" --> AuthUser[Authenticated User]
    end
    
    subgraph WordPressIntegration
        Connect["POST /wordpress/connect"] --> ValidateWP[Validate WordPress Credentials]
        ValidateWP -- "Valid" --> SaveWP[Save WordPress Account]
        ValidateWP -- "Invalid" --> Error[Return Error]
        GetAccounts["GET /wordpress/accounts"] --> FetchAccounts[Fetch User's WordPress Accounts]
        UpdateAccount["PUT /wordpress/accounts/{id}"] --> ValidateWP
        DeleteAccount["DELETE /wordpress/accounts/{id}"] --> RemoveAccount[Remove WordPress Account]
        TestAccount["POST /wordpress/test/{id}"] --> TestWP[Test WordPress Connection]
        GetSites["GET /wordpress/sites"] --> FetchSites[Fetch WordPress Sites Info]
    end
    
    subgraph JobManagement
        CreateJob["POST /create-job"] --> CheckWP{WordPress Account Valid?}
        CheckWP -- "Yes" --> CheckOutline{Outline Provided?}
        CheckWP -- "No" --> CreateJobError[Return Error]
        
        CheckOutline -- "Yes" --> ValidateOutline{Validate Outline}
        CheckOutline -- "No" --> CreatePendingJob[Create Job with Pending Status]
        
        ValidateOutline -- "Valid" --> CreateOutlinedJob[Create Job with Outlined Status]
        ValidateOutline -- "Invalid" --> OutlineError[Return Validation Error]
        
        GetJobs["GET /my-jobs"] --> FetchJobs[Fetch User's Jobs]
        
        UpdateOutline["PUT /jobs/{id}/outline"] --> ValidateJobAccess{User Owns Job?}
        ValidateJobAccess -- "Yes" --> CheckApproval{Job Approved?}
        ValidateJobAccess -- "No" --> AccessError[Return Access Error]
        
        CheckApproval -- "No" --> ValidateNewOutline[Validate New Outline]
        CheckApproval -- "Yes" --> ApprovalError[Return Already Approved Error]
        
        ValidateNewOutline -- "Valid" --> SaveOutline[Save New Outline]
        ValidateNewOutline -- "Invalid" --> NewOutlineError[Return Validation Error]
        
        GetOutline["GET /jobs/{id}/outline"] --> ValidateJobAccess
        
        ApproveJob["PUT /jobs/{id}/approve"] --> ValidateJobAccess
        UnapproveJob["PUT /jobs/{id}/unapprove"] --> ValidateJobAccess
        GetStatus["GET /jobs/{id}/status"] --> ValidateJobAccess
    end
    
    AuthUser --> WordPressIntegration
    AuthUser --> JobManagement
    
    Health["GET /health"] --> CheckDB[Check Database Connection]
```

## 2. Outline Generation Process

This diagram illustrates the process of generating and validating blog post outlines.

```mermaid
flowchart TD
    Start[Start Outline Creation] --> InputKeyword[Input Main Keyword & Related Keywords]
    InputKeyword --> SetParameters[Set Article Parameters]
    SetParameters --> OutlineGeneration{Generate Outline}
    
    OutlineGeneration -- "Manual Creation" --> ManualOutline[User Creates Outline]
    OutlineGeneration -- "AI Assisted" --> AIOutline[AI Generates Outline]
    
    AIOutline --> OutlineValidation{Validate Outline}
    ManualOutline --> OutlineValidation
    
    OutlineValidation -- "Invalid" --> ValidationErrors[Show Validation Errors]
    ValidationErrors --> FixOutline[Fix Outline Issues]
    FixOutline --> OutlineValidation
    
    OutlineValidation -- "Valid" --> SaveOutline[Save Outline to Job]
    SaveOutline --> UpdateJobStatus[Update Job Status to Outlined]
    UpdateJobStatus --> OutlineReview[Review Outline]
    
    OutlineReview -- "Needs Changes" --> EditOutline[Edit Outline]
    EditOutline --> OutlineValidation
    
    OutlineReview -- "Approved" --> ApproveOutline[Approve Outline for Content Generation]
    
    subgraph OutlineSchema
        OutlineStructure[Outline Structure] --> Title[Title]
        OutlineStructure --> MetaDescription[Meta Description]
        OutlineStructure --> MainKeyword[Main Keyword]
        OutlineStructure --> TargetAudience[Target Audience]
        OutlineStructure --> ContentFormat[Content Format]
        OutlineStructure --> ToneOfVoice[Tone of Voice]
        OutlineStructure --> WordCount[Estimated Word Count]
        
        OutlineStructure --> Sections[Content Sections]
        Sections --> Section1[Section 1: Introduction]
        Sections --> Section2[Section 2: Main Content]
        Sections --> Section3[Section N: Conclusion]
        
        Section2 --> SectionDetails[Section Details]
        SectionDetails --> SectionTitle[Section Title]
        SectionDetails --> SectionWords[Estimated Words]
        SectionDetails --> SectionDesc[Description]
        SectionDetails --> KeyPoints[Key Points]
        SectionDetails --> SectionKeywords[Section Keywords]
        
        OutlineStructure --> SEOKeywords[SEO Keywords]
        SEOKeywords --> PrimaryKeywords[Primary Keywords]
        SEOKeywords --> SecondaryKeywords[Secondary Keywords]
        SEOKeywords --> LongTailKeywords[Long-tail Keywords]
        
        OutlineStructure --> CTA[Call to Action]
        OutlineStructure --> FAQs[FAQ Suggestions]
        OutlineStructure --> InternalLinks[Internal Linking Opportunities]
    end
```

## 3. Blog Generation and WordPress Posting

This diagram illustrates the process of generating blog content from approved outlines and posting to WordPress.

```mermaid
flowchart TD
    Start[Start Blog Generation] --> FetchJob[Fetch Approved Job]
    FetchJob --> LoadOutline[Load Job Outline]
    
    LoadOutline --> ContentGeneration[Generate Blog Content]
    ContentGeneration --> StructuredContent[Create Structured Content]
    
    StructuredContent --> IntroSection[Generate Introduction]
    StructuredContent --> MainSections[Generate Main Content Sections]
    StructuredContent --> ConclusionSection[Generate Conclusion]
    StructuredContent --> FAQsSection[Generate FAQs]
    
    IntroSection --> AssembleContent[Assemble Complete Content]
    MainSections --> AssembleContent
    ConclusionSection --> AssembleContent
    FAQsSection --> AssembleContent
    
    AssembleContent --> SEOOptimization[SEO Optimization]
    SEOOptimization --> KeywordIntegration[Integrate Keywords]
    SEOOptimization --> ReadabilityCheck[Check Readability]
    SEOOptimization --> MetaTagsGeneration[Generate Meta Tags]
    
    KeywordIntegration --> FinalContent[Final Content]
    ReadabilityCheck --> FinalContent
    MetaTagsGeneration --> FinalContent
    
    FinalContent --> ImageGeneration[Generate Featured Image]
    ImageGeneration --> PrepareWordPress[Prepare WordPress Post]
    
    PrepareWordPress --> FetchWPCredentials[Fetch WordPress Credentials]
    FetchWPCredentials --> ValidateWPConnection[Validate WordPress Connection]
    
    ValidateWPConnection -- "Valid" --> CreateWPPost[Create WordPress Post]
    ValidateWPConnection -- "Invalid" --> ConnectionError[Connection Error]
    ConnectionError --> RetryConnection[Retry Connection]
    RetryConnection --> ValidateWPConnection
    
    CreateWPPost --> UploadMedia[Upload Featured Image]
    UploadMedia --> PublishPost[Publish or Save Draft]
    
    PublishPost --> UpdateJobStatus[Update Job Status]
    UpdateJobStatus --> Complete[Job Complete]
    
    subgraph ContentOptimization
        OptimizeHeadings[Optimize Headings]
        OptimizeParagraphs[Optimize Paragraphs]
        AddInternalLinks[Add Internal Links]
        FormatContent[Format Content]
    end
    
    MainSections --> ContentOptimization
    ContentOptimization --> MainSections
```

## Combined System Overview

This diagram provides a high-level overview of how the three main components of the system interact.

```mermaid
flowchart TD
    User[User] --> Auth[Authentication]
    Auth --> Dashboard[User Dashboard]
    
    Dashboard --> WPManagement[WordPress Management]
    Dashboard --> JobManagement[Job Management]
    
    JobManagement --> CreateNewJob[Create New Job]
    CreateNewJob --> OutlineProcess[Outline Generation Process]
    OutlineProcess --> ReviewOutline[Review & Approve Outline]
    
    ReviewOutline -- "Approved" --> BlogGeneration[Blog Generation Process]
    ReviewOutline -- "Needs Changes" --> EditOutline[Edit Outline]
    EditOutline --> OutlineProcess
    
    BlogGeneration --> WordPressPublishing[WordPress Publishing]
    WordPressPublishing --> PublishedContent[Published Content]
    
    WPManagement <--> WordPressPublishing
    
    subgraph SystemComponents
        BackendAPI[FastAPI Backend]
        Database[(SQL Database)]
        AIServices[AI Content Services]
        WordPressAPI[WordPress API]
    end
    
    Auth <--> BackendAPI
    JobManagement <--> BackendAPI
    WPManagement <--> BackendAPI
    OutlineProcess <--> AIServices
    BlogGeneration <--> AIServices
    BackendAPI <--> Database
    WordPressPublishing <--> WordPressAPI
```
