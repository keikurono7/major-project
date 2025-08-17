from database import EducationDB
from auth_service import AuthService
from content_service import ContentService

def setup_system():
    """Initialize the system with sample data"""
    # Initialize database
    print("Initializing database...")
    db = EducationDB()
    
    # Create services
    auth_service = AuthService()
    content_service = ContentService()
    
    # Create sample users
    print("Creating sample users...")
    
    # Create teacher
    auth_service.create_user(
        username="teacher1",
        email="teacher@example.com", 
        password="password123",
        role="teacher",
        full_name="Dr. John Smith"
    )
    
    # Create students
    auth_service.create_user(
        username="student1",
        email="student1@example.com",
        password="password123", 
        role="student",
        full_name="Alice Johnson"
    )
    
    auth_service.create_user(
        username="student2", 
        email="student2@example.com",
        password="password123",
        role="student", 
        full_name="Bob Wilson"
    )
    
    print("System setup complete!")
    print("\nSample login credentials:")
    print("Teacher - Username: teacher1, Password: password123")
    print("Student - Username: student1, Password: password123")

if __name__ == "__main__":
    setup_system()