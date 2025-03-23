#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Apply migrations
python3 manage.py migrate

# Start development server
python3 manage.py runserver 