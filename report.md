# KnowEll Educational Platform - Implementation Report

## Table of Contents
1. [Project Overview](#project-overview)
2. [Backend Implementation (gcp folder)](#backend-implementation-gcp-folder)
3. [Frontend Implementation (knowell folder)](#frontend-implementation-knowell-folder)
4. [System Integration](#system-integration)
5. [Data Flow and Architecture](#data-flow-and-architecture)
6. [Deployment and Infrastructure](#deployment-and-infrastructure)

## Project Overview

KnowEll is an educational platform designed to facilitate teaching and learning with dedicated interfaces for students and teachers. The application follows a modern client-server architecture with a React-based frontend and a Python backend deployed on Google Cloud Platform (GCP).

The system focuses on automated content generation (question papers, quizzes, assignments), student assessment, and progress tracking, offering a comprehensive educational management system.

## Backend Implementation (gcp folder)

### Core Files and Their Functions

#### `main.py`
- **Framework**: Flask web application framework
- **Purpose**: Entry point for the backend service, orchestrates all components
- **Server Configuration**:
  - CORS configuration for frontend communication
  - Request size limits for file uploads
  - Timeout configurations
  - Debug mode settings
  
- **API Endpoints**:
  - **Authentication APIs**:
    - `POST /api/auth/login` - User login with credentials
    - `POST /api/auth/register` - New user registration
    - `POST /api/auth/logout` - User logout
    - `GET /api/auth/verify` - Token verification
    - `POST /api/auth/reset-password` - Password reset flow
    
  - **Question Paper APIs**:
    - `POST /api/papers/generate` - Generate new question paper
    - `GET /api/papers/list` - List all question papers
    - `GET /api/papers/:id` - Get specific question paper
    - `DELETE /api/papers/:id` - Delete a question paper
    
  - **Quiz APIs**:
    - `POST /api/quizzes/generate` - Create new quiz
    - `GET /api/quizzes/list` - List available quizzes
    - `GET /api/quizzes/:id` - Get specific quiz
    - `POST /api/quizzes/:id/submit` - Submit quiz answers
    
  - **Assignment APIs**:
    - `POST /api/assignments/generate` - Create new assignment
    - `GET /api/assignments/list` - List assignments
    - `GET /api/assignments/:id` - Get specific assignment
    - `POST /api/assignments/:id/submit` - Submit completed assignment
    
  - **Student APIs**:
    - `GET /api/students/:id/progress` - Get progress metrics
    - `GET /api/students/:id/dashboard` - Get dashboard data
    - `GET /api/students/class/:id` - List students in class
    
  - **Teacher APIs**:
    - `GET /api/teachers/:id/dashboard` - Teacher dashboard data
    - `GET /api/analytics/class/:id` - Class analytics
    
  - **Content APIs**:
    - `POST /api/content/upload` - Upload educational content
    - `GET /api/content/list` - List available content
    - `DELETE /api/content/:id` - Delete content
    
  - **Syllabus APIs**:
    - `POST /api/syllabus/upload` - Upload syllabus
    - `POST /api/syllabus/parse` - Parse syllabus content
    
  - **Health Check**:
    - `GET /api/health` - Service health check

- **Functions**:
  - `initialize_app()` - Sets up the Flask application with configurations
  - `register_blueprints()` - Registers API route blueprints for organization
  - `configure_logging()` - Sets up application logging
  - `configure_error_handlers()` - Sets up error handling
  - `init_firebase()` - Initializes Firebase connection
  - `apply_middlewares()` - Configures request processing middleware
  - `serve()` - Runs the development server

- **Route Handlers**:
  - `handle_health_check()` - Returns service status
  - `handle_not_found()` - 404 error handler
  - `handle_server_error()` - 500 error handler
  - Various other route-specific handlers that call into the appropriate module

- **Middleware**:
  - Authentication middleware to verify tokens
  - Request logging middleware
  - Rate limiting for API abuse prevention
  - Request validation middleware

- **Module Integration**:
  - Imports `auth.py` for authentication functions
  - Imports `backend_api.py` for API implementation
  - Imports `question_paper_generator.py` for paper generation
  - Imports `quiz_generator.py` for quiz generation
  - Imports `assignment_generator.py` for assignment creation
  - Imports `syllabus_parser.py` for syllabus processing
  - Imports `firebase_ops.py` for database operations

#### `backend_api.py`
- **Purpose**: Implements core API endpoints and request handling
- **APIs**:
  - `/api/papers` - Question paper generation and retrieval
  - `/api/quizzes` - Quiz generation and retrieval
  - `/api/assignments` - Assignment generation and management
- **Functions**:
  - `generate_paper()` - Creates new question papers
  - `list_papers()` - Lists available question papers
  - `generate_quiz()` - Creates interactive quizzes
  - `generate_assignment()` - Creates assignments based on syllabus
  - `get_resource()` - Generic function for retrieving content
- **Data Types**:
  - JSON request/response payloads
  - Content metadata (dates, titles, categories)

#### `auth.py`
- **Purpose**: Authentication and authorization logic
- **Functions**:
  - `verify_token()` - Validates user authentication tokens
  - `get_user_claims()` - Extracts user role and permissions
  - `generate_token()` - Creates new authentication tokens
  - `check_permission()` - Validates user access to resources
- **Data Types**:
  - JWT tokens
  - User credentials
  - Permission levels (student, teacher, admin)

#### `firebase_ops.py`
- **Purpose**: Database operations using Firebase
- **Functions**:
  - `initialize_firebase()` - Sets up Firebase connection
  - `store_document()` - Saves data to Firestore
  - `retrieve_document()` - Gets data from Firestore
  - `update_document()` - Updates existing documents
  - `delete_document()` - Removes documents
  - `query_collection()` - Searches for specific data
- **Data Types**:
  - Document references
  - Collection paths
  - Query parameters

#### `question_paper_generator.py`
- **Purpose**: Automated generation of question papers
- **Functions**:
  - `generate_questions()` - Creates question sets
  - `format_paper()` - Structures questions into papers
  - `save_paper()` - Stores papers in filesystem
  - `parse_syllabus_for_questions()` - Extracts content for questions
- **Data Types**:
  - Question objects (text, type, difficulty)
  - Paper metadata
  - Subject taxonomies

#### `quiz_generator.py`
- **Purpose**: Creates interactive quizzes
- **Functions**:
  - `generate_quiz_questions()` - Creates quiz content
  - `add_options()` - Creates multiple-choice options
  - `generate_feedback()` - Creates response feedback
  - `difficulty_calculator()` - Adjusts difficulty based on user performance
- **Data Types**:
  - Quiz question objects
  - Answer options arrays
  - Difficulty ratings

#### `assignment_generator.py`
- **Purpose**: Creates student assignments
- **Functions**:
  - `generate_assignment()` - Creates complete assignments
  - `create_tasks()` - Generates individual tasks
  - `difficulty_mapping()` - Maps content to difficulty levels
  - `generate_rubric()` - Creates assessment criteria
- **Data Types**:
  - Assignment objects
  - Task descriptions
  - Rubric criteria

#### `syllabus_parser.py`
- **Purpose**: Processes and analyzes syllabus content
- **Functions**:
  - `parse_syllabus()` - Extracts structured data from syllabus
  - `identify_topics()` - Identifies key topics
  - `generate_topic_hierarchy()` - Creates topic relationships
  - `extract_learning_objectives()` - Identifies learning goals
- **Data Types**:
  - Syllabus text
  - Topic hierarchies
  - Learning objective mappings

#### `config.py`
- **Purpose**: Configuration settings
- **Data**:
  - Environment variables
  - Service connections
  - Feature flags
  - Authentication settings

#### Supporting Files
- `serviceAccountKey.json` - Firebase credentials for authentication
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `api-tester.html` - Frontend tool for testing APIs
- `syllabus-uploader.html` - Tool for uploading syllabus content

### Generated Content Storage
- `/question_papers/` - Contains generated assessment papers
- `/temp_data/` - Temporary processing files

## Frontend Implementation (knowell folder)

### Build System and Configuration
- `vite.config.js` - Vite bundler configuration
- `tailwind.config.js` - Tailwind CSS framework settings
- `postcss.config.js` - CSS processing configuration
- `eslint.config.js` - Code linting rules
- `package.json` - Dependencies and scripts

### Application Structure

#### Entry Points
- `src/main.jsx`
  - **Purpose**: Application initialization
  - **Functions**:
    - React rendering setup
    - Provider wrapping
    - Initial routing
  - **Dependencies**: React, ReactDOM, App component, AuthContext

- `src/App.jsx`
  - **Purpose**: Main component structure
  - **Functions**:
    - Route definitions
    - Layout composition
    - Authentication routing logic
  - **Data Flow**: Receives auth state from AuthContext
  - **Components Used**: Navbar, Sidebar, Login, StudentHome, TeacherHome

#### Core Styling
- `src/App.css` - Component-specific styles
- `src/index.css` - Global styles
- `src/dashboard.css` - Dashboard-specific styles
- `src/assets/styles/global.css` - Shared styling constants

#### Authentication
- `src/contexts/AuthContext.jsx`
  - **Purpose**: Authentication state management
  - **Functions**:
    - `login()` - Handles user login
    - `logout()` - Handles user logout
    - `register()` - New user registration
    - `resetPassword()` - Password recovery
  - **Data Types**:
    - User object (id, name, email, role)
    - Authentication tokens
    - Login status
  - **Context Provided**: currentUser, loading, login, logout, register

#### Common Components
- `src/components/common/Button.jsx`
  - **Props**: variant, size, onClick, children, disabled
  - **Used In**: Login, ContentUpload, PaperGenerator

- `src/components/common/Card.jsx`
  - **Props**: title, children, footer, className
  - **Used In**: StudentHome, TeacherHome, Analytics

- `src/components/common/Navbar.jsx`
  - **Props**: user, onLogout
  - **Functions**: Navigation handling, user menu display
  - **Used In**: App.jsx

- `src/components/common/ParallaxSection.jsx`
  - **Props**: backgroundImage, children, speed
  - **Used In**: Login page

- `src/components/common/Sidebar.jsx`
  - **Props**: items, activeItem, onItemClick
  - **Data Types**: Navigation item objects
  - **Used In**: StudentHome, TeacherHome

#### Student Components
- `src/components/student/AssignmentInterface.jsx`
  - **Purpose**: Assignment completion interface
  - **Functions**:
    - `submitAssignment()` - Sends completed work
    - `saveProgress()` - Stores partial progress
    - `fetchAssignmentDetails()` - Gets assignment data
  - **Props**: assignmentId, studentId
  - **Data Types**: Assignment submission data
  - **API Calls**: POST /api/assignments/submit, GET /api/assignments/:id

- `src/components/student/QuizInterface.jsx`
  - **Purpose**: Interactive quiz taking
  - **Functions**:
    - `submitAnswer()` - Processes student answers
    - `fetchQuizData()` - Retrieves quiz content
    - `calculateScore()` - Determines quiz results
  - **Props**: quizId, studentId
  - **Data Types**: Quiz response data, scores
  - **API Calls**: GET /api/quizzes/:id, POST /api/quizzes/submit

- `src/components/student/ProgressTracker.jsx`
  - **Purpose**: Student performance visualization
  - **Functions**:
    - `fetchProgressData()` - Gets performance metrics
    - `renderCharts()` - Creates visual representations
  - **Props**: studentId, timeRange
  - **Data Types**: Performance metrics, time series data
  - **API Calls**: GET /api/students/:id/progress

#### Teacher Components
- `src/components/teacher/ContentUpload.jsx`
  - **Purpose**: Educational content management
  - **Functions**:
    - `uploadContent()` - Uploads new materials
    - `categorizeContent()` - Organizes materials
    - `deleteContent()` - Removes outdated content
  - **Props**: teacherId, contentType
  - **Data Types**: File uploads, content metadata
  - **API Calls**: POST /api/content/upload, DELETE /api/content/:id

- `src/components/teacher/PaperGenerator.jsx`
  - **Purpose**: Assessment creation
  - **Functions**:
    - `generatePaper()` - Creates question papers
    - `previewPaper()` - Shows generated content
    - `savePaper()` - Stores paper for later use
  - **Props**: teacherId, subjectId
  - **Data Types**: Question paper parameters, difficulty settings
  - **API Calls**: POST /api/papers/generate, GET /api/papers/:id

- `src/components/teacher/Analytics.jsx`
  - **Purpose**: Student performance analysis
  - **Functions**:
    - `fetchClassData()` - Gets class-wide metrics
    - `generateReports()` - Creates performance summaries
    - `identifyTrends()` - Highlights patterns
  - **Props**: classId, timeRange
  - **Data Types**: Performance metrics, trend data
  - **API Calls**: GET /api/analytics/class/:id

- `src/components/teacher/StudentMonitoring.jsx`
  - **Purpose**: Track student activity and progress
  - **Functions**:
    - `fetchStudentList()` - Gets student roster
    - `viewStudentDetails()` - Shows individual performance
    - `flagStudentIssues()` - Highlights concerns
  - **Props**: classId
  - **Data Types**: Student records, performance flags
  - **API Calls**: GET /api/students/class/:id, GET /api/students/:id

#### Pages
- `src/pages/Login.jsx`
  - **Purpose**: Authentication page
  - **Functions**:
    - `handleLogin()` - Processes login attempts
    - `switchMode()` - Toggles between login/register
  - **Components Used**: Button, ParallaxSection
  - **Context Used**: AuthContext
  - **API Calls**: Uses AuthContext functions

- `src/pages/StudentHome.jsx`
  - **Purpose**: Student dashboard
  - **Functions**:
    - `fetchDashboardData()` - Gets student overview
    - `navigateToSection()` - Changes active section
  - **Components Used**: Sidebar, Card, ProgressTracker
  - **Context Used**: AuthContext
  - **API Calls**: GET /api/students/:id/dashboard

- `src/pages/TeacherHome.jsx`
  - **Purpose**: Teacher dashboard
  - **Functions**:
    - `fetchClassOverview()` - Gets class metrics
    - `navigateToSection()` - Changes active view
  - **Components Used**: Sidebar, Card, Analytics
  - **Context Used**: AuthContext
  - **API Calls**: GET /api/teachers/:id/dashboard

#### API Services
- `src/services/api.js`
  - **Purpose**: Communication with backend services
  - **Functions**:
    - `get()` - HTTP GET requests
    - `post()` - HTTP POST requests
    - `put()` - HTTP PUT requests
    - `delete()` - HTTP DELETE requests
    - `upload()` - File upload handling
  - **Data Types**: API responses, request parameters
  - **Error Handling**: Network errors, API errors

## System Integration

### Authentication Flow
1. Users authenticate via `Login.jsx`
2. `AuthContext.jsx` manages authentication state
3. Authentication requests flow through `api.js` to backend `/api/auth`
4. Backend `auth.py` validates credentials using Firebase
5. JWT tokens are returned and stored in frontend for subsequent requests

### Content Generation Flow
1. Teachers use `PaperGenerator.jsx` or similar components to request content
2. Requests are sent via `api.js` to backend endpoints
3. Backend routes in `main.py` and `backend_api.py` direct to appropriate generators:
   - `question_paper_generator.py`
   - `quiz_generator.py`
   - `assignment_generator.py`
4. Generators utilize `syllabus_parser.py` for content relevance
5. Generated content is stored in the filesystem and referenced in Firebase
6. Frontend retrieves and displays the content

### Data Storage
1. User data stored in Firebase (auth info, preferences)
2. Generated content stored in both:
   - Filesystem (`/question_papers/`, `/temp_data/`)
   - Firebase (metadata and references)

## Data Flow and Architecture

### Request Flow
1. User interacts with React component
2. Component calls function in `api.js`
3. API request reaches backend endpoints in `main.py`
4. Request is processed by specific handler functions
5. Database operations performed via `firebase_ops.py`
6. Response returned to frontend
7. Component state updated with new data

### Data Types
1. **User Data**:
   - Authentication credentials
   - Roles (student, teacher, admin)
   - Preferences

2. **Educational Content**:
   - Question papers (structured text)
   - Quizzes (questions, options, answers)
   - Assignments (instructions, rubrics)
   - Syllabus content (structured text)

3. **Performance Data**:
   - Quiz scores
   - Assignment grades
   - Progress metrics
   - Time-series performance data

## Deployment and Infrastructure

### Backend Deployment
- Container-based deployment using Docker
- Deployed on Google Cloud Platform
- Environment configuration via `config.py`
- Dependencies managed in `requirements.txt`

### Frontend Deployment
- Modern build system using Vite
- CSS utility framework with Tailwind
- Optimized with PostCSS processing
- Code quality maintained with ESLint

This comprehensive educational platform combines automated content generation with structured learning management, providing tailored experiences for both teachers and students through integrated frontend and backend systems.