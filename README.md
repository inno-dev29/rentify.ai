# Rental Listing Platform with LLM Integration

A rental listing platform similar to AirBNB where landlords can create listings for properties, and renters can browse and book them. The platform includes Claude API-powered features for generating property summaries and persona creation based on user data.

## Tech Stack

### Backend
- Django REST Framework (Python)
- PostgreSQL
- JWT Authentication
- Claude API for LLM features
- AWS S3 for image storage

### Frontend
- Next.js (React, TypeScript)
- Tailwind CSS
- SWR for API data fetching

## Project Structure

```
.
├── backend/             # Django backend code
│   ├── rental_platform/ # Project settings
│   ├── users/           # User management app
│   ├── properties/      # Property listings app
│   ├── bookings/        # Booking management app
│   ├── reviews/         # Review system app
│   └── llm_services/    # LLM-powered features app
│
├── frontend/            # Next.js frontend code
│   ├── src/             # Source code
│   ├── public/          # Static assets
│   └── ...
│
└── docs/                # Documentation
```

## Features

- **User Management**
  - User registration and authentication
  - User profiles for both leasers (property owners) and renters
  - Role-based permissions

- **Property Listings**
  - Property creation and management for leasers
  - Image uploads and management
  - Amenity listings
  - Property search and filtering

- **Booking System**
  - Booking creation and management
  - Availability checking
  - Booking status updates

- **Review System**
  - Star ratings across multiple categories
  - Text reviews and responses
  - Photo uploads with reviews

- **LLM-Powered Features**
  - Property summary generation based on details and reviews
  - User persona creation for better recommendations
  - Personalized property recommendations

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```
   python manage.py migrate
   ```

4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

### Backend (.env file)

```
# Django settings
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
USE_SQLITE=True  # For development
DB_NAME=rental_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# LLM settings
CLAUDE_API_KEY=your_claude_api_key

# AWS S3 settings
USE_S3=False
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1
```

### Frontend (.env.local file)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
