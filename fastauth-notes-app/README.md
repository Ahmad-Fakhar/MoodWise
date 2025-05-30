# FastAuth Notes App

A full-stack web application for note-taking with emotional intelligence features. Built with FastAPI (backend), MongoDB (database), and vanilla HTML/CSS/JavaScript (frontend).

## Features

- **User Authentication**
  - Register with email and password
  - Login with JWT token authentication
  - Password reset functionality

- **Note Management**
  - Create, read, update, and delete notes
  - Notes are associated with user accounts
  - Responsive note card interface

- **Emotional Chatbot**
  - AI-powered chatbot using Groq API
  - Emotion detection and appropriate responses
  - Conversation history tracking

## Project Structure

```
├── backend/
│   ├── main.py           # FastAPI application entry point
│   ├── auth.py           # Authentication utilities
│   ├── database.py       # MongoDB connection and utilities
│   ├── models.py         # Pydantic models for data validation
│   ├── utils.py          # Helper functions
│   └── routes/
│       ├── auth_routes.py    # Authentication endpoints
│       ├── note_routes.py    # Note CRUD operations
│       └── chat_routes.py    # Emotional chatbot endpoints
│
├── frontend/
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Notes dashboard
│   ├── chat.html         # Emotional chatbot interface
│   ├── forgot-password.html  # Password reset request
│   ├── reset-password.html   # Password reset form
│   ├── style.css         # Global styles
│   └── app.js            # Frontend JavaScript
│
├── .env                  # Environment variables
└── requirements.txt      # Python dependencies
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- MongoDB (local installation or MongoDB Atlas)
- Groq API key (for emotional chatbot)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastauth-notes-app.git
   cd fastauth-notes-app
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   MONGO_URI=mongodb://localhost:27017
   DATABASE_NAME=fastauth_notes
   SECRET_KEY=your_jwt_secret
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GROQ_API_KEY=your_groq_key
   ```

5. Start the backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The API will be available at http://localhost:8000

### Frontend Setup

The frontend is built with vanilla HTML, CSS, and JavaScript. You can serve it using any static file server:

1. Using Python's built-in HTTP server:
   ```bash
   cd frontend
   python -m http.server 8080
   ```

2. Or simply open the HTML files directly in your browser.

## API Documentation

Once the backend is running, you can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage

1. Register a new account at `/register.html`
2. Log in with your credentials at `/login.html`
3. Create and manage notes at `/dashboard.html`
4. Chat with the emotional AI at `/chat.html`

## Security Features

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- MongoDB indexes for performance and security
- CORS middleware to control API access

## License

This project is licensed under the MIT License - see the LICENSE file for details.