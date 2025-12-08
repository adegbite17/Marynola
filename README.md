# Clone the repository
git clone https://github.com/adegbite17/Marynola.git
cd Marynola/Marynola

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py

# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# API Endpoints
# Authentication
# Method Endpoint      Description               Auth Required
  POST /api/register  Register new boss/admin     No
  POST  /api/login    Boss login                  No
  POST  /api/logout    Boss logout                Yes
  POST  /api/forgot-password  Request password reset  No
  POST  /api/reset-password  Reset password with code  No

# Staff Management
# Method  Endpoint  Description  Auth Required
  POST    /api/staff  Add new staff member  Yes
  GET    /api/staff   Get all staff         Yes
  GET    /api/staff/<id>  Get specific staff  Yes
  PUT    /api/staff/<id>  Update staff (JSON only)  Yes
  PUT    /api/staff/<id>/update-with-file  Update staff with file  Yes
  DELETE  /api/staff/<id>  Delete staff    Yes
  GET    /api/staff/search  Search staff    Yes
  GET    /api/staff/download  Download staff as Excel  Yes

# Prerequisites
Python 3.8+
Node.js 14+
PostgreSQL (or any SQLAlchemy-compatible database)
Cloudinary account
SMTP email service (Gmail, Mailgun, etc.)

# File Management
# Method  Endpoint                Description          Auth Required
  POST    /api/staff/<id>/upload-id  Upload proof of ID    Yes
  GET    /api/staff/<id>/download-id  Download proof of ID  Yes/Token

# Dashboard
#  Method  Endpoint  Description  Auth Required
    GET    /api/dashboard  Get dashboard statistics  Yes

# Contributing
Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request



https://github.com/user-attachments/assets/61a1cc3d-bc9b-4fcc-b3cd-9c937463b42c



