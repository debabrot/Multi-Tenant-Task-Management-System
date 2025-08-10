"""
Streamlit Task Manager Application

A web-based task management application built with Streamlit and FastAPI backend.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

import requests
import streamlit as st


# Configuration
BASE_URL = "http://localhost:8000"


class APIClient:
    """API client for handling requests to the FastAPI backend."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Make API request to the backend."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method.upper(), 
                url=url, 
                json=json_data, 
                headers=headers,
                timeout=30
            )
            return response
        except requests.RequestException as e:
            st.error(f"Request failed: {str(e)}")
            raise


class SessionManager:
    """Manages Streamlit session state."""
    
    @staticmethod
    def initialize_session_state() -> None:
        """Initialize session state variables if they don't exist."""
        defaults = {
            'access_token': None,
            'refresh_token': None,
            'logged_in': False,
            'email': ""
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def clear_session() -> None:
        """Clear all authentication-related session data."""
        st.session_state.logged_in = False
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.email = ""


class AuthManager:
    """Handles authentication logic."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not st.session_state.refresh_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {st.session_state.refresh_token}"}
            response = self.api_client.make_request("POST", "/auth/refresh", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.access_token = data["access_token"]
                return True
            else:
                # Invalid refresh token - clear session
                SessionManager.clear_session()
                return False
                
        except Exception as e:
            st.error("Failed to refresh token.")
            return False
    
    def authenticated_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Make an authenticated API request with automatic token refresh."""
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = self.api_client.make_request(method, endpoint, json_data, headers)
        
        # If unauthorized, try refreshing the token
        if response.status_code == 401:
            if self.refresh_access_token():
                # Retry with new access token
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                response = self.api_client.make_request(method, endpoint, json_data, headers)
        
        return response
    
    def login(self, email: str, password: str) -> bool:
        """Attempt to log in the user."""
        response = self.api_client.make_request(
            "POST", 
            "/auth/login", 
            json_data={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            st.session_state.logged_in = True
            st.session_state.email = email
            return True
        else:
            error_message = response.json().get('detail', 'Unknown error')
            st.error(f"Login failed: {error_message}")
            return False
    
    def register(self, email: str, username: str, password: str) -> bool:
        """Register a new user."""
        response = self.api_client.make_request(
            "POST", 
            "/auth/register", 
            json_data={"email": email, "full_name": username, "password": password}
        )
        
        if response.status_code == 200:
            st.success("User registered successfully! You can now log in.")
            return True
        else:
            error_message = response.json().get('detail', 'Unknown error')
            st.error(f"Registration failed: {error_message}")
            return False
    
    def logout(self, auth_manager) -> None:
        """Log out the user."""
        if st.session_state.refresh_token:
            try:
                auth_manager.authenticated_request("POST", "/auth/logout")
            except Exception:
                pass  # Ignore logout failure
        
        SessionManager.clear_session()
        st.success("Logged out successfully!")
        st.query_params["page"] = "login"
        st.rerun()


class TaskManager:
    """Handles task-related operations."""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    def get_tasks(self) -> list:
        """Retrieve all tasks for the current user."""
        response = self.auth_manager.authenticated_request("GET", "/tasks/")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            st.error(f"Could not load tasks: {response.status_code} - {response.text}")
            return []
    
    def create_task(self, title: str, description: str, due_at: Optional[str]) -> bool:
        """Create a new task."""
        task_data = {
            "title": title,
            "body": description,
            "due_at": due_at
        }
        
        response = self.auth_manager.authenticated_request("POST", "/tasks/", json_data=task_data)
        
        if response.status_code == 201:
            st.success("Task created successfully!")
            return True
        else:
            error_message = response.json().get('detail', 'Unknown error')
            st.error(f"Failed to create task: {error_message}")
            return False
    
    def update_task_status(self, task_id: int, is_done: bool) -> bool:
        """Update task completion status."""
        endpoint = f"/tasks/{task_id}/{'done' if is_done else 'undone'}"
        response = self.auth_manager.authenticated_request("PATCH", endpoint)
        
        if response.status_code == 200:
            status = "done" if is_done else "undone"
            st.success(f"Task marked as {status}!")
            return True
        else:
            st.error("Failed to update task.")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        response = self.auth_manager.authenticated_request("DELETE", f"/tasks/{task_id}")
        
        if response.status_code == 204:
            st.success("Task deleted!")
            return True
        else:
            st.error("Failed to delete task.")
            return False
    
    def get_statistics(self) -> Optional[Dict[str, int]]:
        """Get task statistics."""
        response = self.auth_manager.authenticated_request("GET", "/tasks/stats")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Could not load statistics.")
            return None


class TaskManagerUI:
    """Handles the Streamlit UI components."""
    
    def __init__(self):
        self.api_client = APIClient()
        self.auth_manager = AuthManager(self.api_client)
        self.task_manager = TaskManager(self.auth_manager)
    
    def render_login_page(self) -> None:
        """Render the login page."""
        st.title("🔐 Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit and email and password:
                if self.auth_manager.login(email, password):
                    st.query_params["page"] = "dashboard"
                    st.rerun()
        
        st.markdown("[→ Register instead](?page=register)")
    
    def render_register_page(self) -> None:
        """Render the registration page."""
        st.title("📝 Register")
        
        with st.form("register_form"):
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not all([email, username, password, confirm_password]):
                    st.error("All fields are required!")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    if self.auth_manager.register(email, username, password):
                        st.query_params["page"] = "login"
        
        st.markdown("[← Back to Login](?page=login)")
    
    def render_task_item(self, task: Dict[str, Any]) -> None:
        """Render a single task item."""
        with st.container():
            st.markdown(f"### {task['title']}")
            
            description = task.get("body", "").strip()
            st.write(description if description else "No description")
            
            status = "✅ Done" if task["is_done"] else "🕒 Pending"
            st.write(f"**Status:** {status}")
            st.write(f"**Created:** {task['created_at']}")
            
            if task.get("due_at"):
                st.write(f"**Due:** {task['due_at']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not task["is_done"]:
                    if st.button("Mark as Done", key=f"done_{task['id']}"):
                        if self.task_manager.update_task_status(task['id'], True):
                            time.sleep(1)
                            st.rerun()
            
            with col2:
                if task["is_done"]:
                    if st.button("Mark as Undone", key=f"undone_{task['id']}"):
                        if self.task_manager.update_task_status(task['id'], False):
                            time.sleep(1)
                            st.rerun()
            
            with col3:
                if st.button("Delete", key=f"del_{task['id']}"):
                    if self.task_manager.delete_task(task['id']):
                        time.sleep(1)
                        st.rerun()
            
            st.markdown("---")
    
    def render_tasks_tab(self) -> None:
        """Render the tasks tab."""
        st.subheader("Your Tasks")
        tasks = self.task_manager.get_tasks()
        
        if not tasks:
            st.info("No tasks found. Create one in the 'Create Task' tab.")
        else:
            for task in tasks:
                self.render_task_item(task)
    
    def render_create_task_tab(self) -> None:
        """Render the create task tab."""
        st.subheader("Create a New Task")
        
        with st.form("create_task_form"):
            title = st.text_input("Title", max_chars=100)
            description = st.text_area("Description (optional)")
            
            st.write("Due Date & Time (optional)")
            col1, col2 = st.columns(2)
            
            with col1:
                due_date = st.date_input("Due Date", value=None)
            with col2:
                due_time = st.time_input("Due Time", value=None)
            
            submit = st.form_submit_button("Create Task")
            
            if submit:
                if not title.strip():
                    st.error("Title is required!")
                else:
                    due_at = None
                    if due_date and due_time:
                        due_at = datetime.combine(due_date, due_time).isoformat()
                    
                    if self.task_manager.create_task(title, description, due_at):
                        time.sleep(1)
                        st.rerun()
    
    def render_statistics_tab(self) -> None:
        """Render the statistics tab."""
        st.subheader("📊 Task Statistics")
        stats = self.task_manager.get_statistics()
        
        if stats:
            total = stats.get("total", 0)
            done = stats.get("completed", 0)
            pending = stats.get("pending", 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tasks", total)
            with col2:
                st.metric("Completed", done)
            with col3:
                st.metric("Pending", pending)
            
            if total > 0:
                completion_rate = done / total
                st.progress(completion_rate)
                st.write(f"{done}/{total} tasks completed ({completion_rate:.1%})")
            else:
                st.write("No tasks yet.")
    
    def render_dashboard(self) -> None:
        """Render the main dashboard."""
        st.title(f"📋 Task Manager - Welcome, {st.session_state.email}!")
        
        if st.button("Logout"):
            self.auth_manager.logout(self.auth_manager)
        
        tab1, tab2, tab3 = st.tabs(["Your Tasks", "Create Task", "Statistics"])
        
        with tab1:
            self.render_tasks_tab()
        
        with tab2:
            self.render_create_task_tab()
        
        with tab3:
            self.render_statistics_tab()
    
    def run(self) -> None:
        """Main application entry point."""
        SessionManager.initialize_session_state()
        
        # Get current page from query parameters
        page = st.query_params.get("page", "login")
        
        if st.session_state.logged_in:
            if page == "logout":
                self.auth_manager.logout(self.auth_manager)
            else:
                st.query_params["page"] = "dashboard"
                self.render_dashboard()
        else:
            if page == "register":
                self.render_register_page()
            else:
                st.query_params["page"] = "login"
                self.render_login_page()


def main() -> None:
    """Application entry point."""
    app = TaskManagerUI()
    app.run()


if __name__ == "__main__":
    main()