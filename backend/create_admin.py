import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rental_platform.settings")
django.setup()

# Import Django models after setting up the environment
from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin_user():
    # Create admin user with predefined credentials
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    admin_password = 'adminpassword123'  # You should change this to a strong password
    
    # Check if user already exists
    if User.objects.filter(username=admin_username).exists():
        user = User.objects.get(username=admin_username)
        user.email = admin_email
        user.set_password(admin_password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Admin user '{admin_username}' updated successfully.")
    else:
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        print(f"Admin user '{admin_username}' created successfully.")
    
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"Email: {admin_email}")
    print("You can use these credentials to log in to the admin interface at /admin/")

if __name__ == "__main__":
    create_admin_user() 