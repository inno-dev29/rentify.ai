# Admin User Instructions

## Login Credentials

An admin user has been created with the following credentials:

- **Username**: admin
- **Password**: adminpassword123
- **Email**: admin@example.com

⚠️ **Important**: You should change this password after your first login for security reasons.

## Accessing the Admin Interface

1. Start the Django server if it's not already running:
   ```
   cd /Users/inno/Documents/STALS/backend
   source venv/bin/activate
   python manage.py runserver 8005
   ```

2. Access the Django admin interface in your browser:
   ```
   http://localhost:8005/admin/
   ```

3. Log in with the admin credentials above.

## Viewing LLM Statistics

### Through the Admin Interface

1. In the admin interface, you can browse and manage LLM-related models:
   - **Property Summaries**: View all property summaries generated by the LLM
   - **Personas**: View user and property personas created by the LLM
   - **Recommendations**: View property recommendations generated for users

### Through the API

The admin user can also access LLM statistics through dedicated API endpoints:

1. **LLM Cache Statistics**:
   ```
   GET http://localhost:8005/api/llm/cache/stats/
   ```
   This will provide detailed statistics about the LLM cache usage and performance.

2. **LLM Provider Status**:
   ```
   GET http://localhost:8005/api/llm/info/
   ```
   This will provide information about the current LLM provider configuration.

3. **Cache Savings Analysis**:
   ```
   GET http://localhost:8005/api/llm/cache/savings/
   ```
   This will provide an analysis of estimated cost savings from LLM caching.

## Additional Admin Functions

As an admin user, you can also:

1. **Clear the LLM Cache**:
   ```
   DELETE http://localhost:8005/api/llm/cache/stats/
   ```

2. **Regenerate All Property Summaries**:
   ```
   POST http://localhost:8005/api/llm/properties/regenerate-summaries/
   ```

## Using the Frontend Admin Panel

If a frontend admin panel for LLM statistics is implemented, you can access it at:
```
http://localhost:3000/admin/llm-stats
```

Use the same admin credentials to log in.

## Getting Help

If you encounter any issues with the admin interface or API endpoints, please check the server logs:
```
cat /Users/inno/Documents/STALS/backend/logs/debug.log
``` 