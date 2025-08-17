import streamlit as st
import pandas as pd
from auth_service import AuthService
from student_interface import student_interface
from teacher_dashboard import teacher_dashboard

st.set_page_config(
    page_title="Educational Quiz System",
    page_icon="🎓",
    layout="wide"
)

def login_page():
    """Display login/register page"""
    st.title("🎓 Educational Quiz System")
    st.markdown("*Multi-Subject Learning Platform*")
    
    auth_service = AuthService()
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary"):
                user = auth_service.authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    st.success(f"Welcome back, {user.full_name}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            reg_full_name = st.text_input("Full Name", key="reg_name")
            reg_role = st.selectbox("Role", ["student", "teacher"], key="reg_role")
            
            if st.form_submit_button("Register", type="primary"):
                if reg_username and reg_email and reg_password and reg_full_name:
                    success = auth_service.create_user(
                        reg_username, reg_email, reg_password, reg_role, reg_full_name
                    )
                    if success:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Registration failed. Username or email might already exist.")
                else:
                    st.error("Please fill all fields")

def main():
    """Main application logic"""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Show login page if not authenticated
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Show appropriate interface based on user role
    user = st.session_state.user
    
    # Add logout button to sidebar
    with st.sidebar:
        st.write(f"**Logged in as:** {user.full_name}")
        st.write(f"**Role:** {user.role.title()}")
        
        if st.button("Logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Route to appropriate interface
    if user.role == "teacher":
        teacher_dashboard()
    elif user.role == "student":
        student_interface()
    else:
        st.error("Invalid user role")

if __name__ == "__main__":
    main()