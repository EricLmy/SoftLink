# backend/create_initial_users.py
import os
from app import create_app, db
from app.models import User

# Determine the config name. Default to 'development' if FLASK_CONFIG is not set.
# This should align with how your Flask CLI commands pick up configurations.
# For direct script execution, explicitly setting it or relying on a sensible default is key.
config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name=config_name)

# Test user credentials (should match those in tests/test_api.py)
SUPER_ADMIN_USERNAME = "superadmin"
SUPER_ADMIN_PASSWORD = "password123"
SUPER_ADMIN_EMAIL = "superadmin@example.com"

PARENT_USER_USERNAME = "parentuser"
PARENT_USER_PASSWORD = "password123"
PARENT_USER_EMAIL = "parentuser@example.com"

def create_user_if_not_exists(username, email, password, role, status='active'):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=email,
            role=role,
            status=status
        )
        user.set_password(password)
        db.session.add(user)
        print(f"User '{username}' with role '{role}' created.")
        return True
    else:
        print(f"User '{username}' already exists.")
        # Optionally, update password or role if needed for existing user for testing
        # user.set_password(password) 
        # user.role = role
        # print(f"Updated user '{username}'.")
        return False

if __name__ == '__main__':
    with app.app_context():
        print("Attempting to create initial users...")
        
        created_superadmin = create_user_if_not_exists(
            username=SUPER_ADMIN_USERNAME,
            email=SUPER_ADMIN_EMAIL,
            password=SUPER_ADMIN_PASSWORD,
            role='super_admin' # Ensure this role string matches your User.role possible values
        )
        
        created_parentuser = create_user_if_not_exists(
            username=PARENT_USER_USERNAME,
            email=PARENT_USER_EMAIL,
            password=PARENT_USER_PASSWORD,
            role='parent_user' # Ensure this role string matches your User.role possible values
        )
        
        if created_superadmin or created_parentuser or True: # Commit if any user was newly created or if we just want to be sure
            try:
                db.session.commit()
                print("Database changes committed.")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing to database: {e}")
        else:
            print("No new users were created, no commit needed unless updates were made.")
        
        print("Initial user setup process finished.") 