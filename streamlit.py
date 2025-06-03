import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import json
import cv2
import tempfile
from datetime import datetime, timedelta
import os

API_URL = "http://localhost:8000"  # FastAPI backend URL

def login_page():
    st.title("UniGuard Security System")
    st.subheader("Login")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Add validation before sending request
        if not email or not password:
            st.error("Please enter both email and password")
            return
            
        try:
            print(f"Sending login request with email: {email}")  # Debug print
            
            response = requests.post(
                f"{API_URL}/auth/login",
                data={"username": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.token = data["access_token"]
                st.session_state.user_id = data["user_id"]
                st.session_state.user_name = data["name"]
                st.session_state.user_role = data["role"]
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Login failed. Please check your credentials.")
                print(f"Login failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            st.error(f"Error connecting to server: {str(e)}")
            
    st.markdown("---")
    if st.button("Register Instead"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    st.title("UniGuard Security System")
    st.subheader("Register New Account")
    
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match!")
            return
        
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json={
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": "admin"  # Default role
                }
            )
            
            if response.status_code == 200:
                st.success("Registration successful! Please login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error connecting to server: {str(e)}")
    
    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def dashboard_page():
    st.title(f"Welcome, {st.session_state.user_name}")
    
    # Updated sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Dashboard",
        "Manage Users and Vehicles",  
        "Process Gate Video",
        "Access Logs",
        "Settings"
    ])
    
    # Logout button
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "login"
        st.rerun()
    
    # Updated page content routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Manage Users and Vehicles":
        manage_users()
    # elif page == "Manage Vehicles":
    #     manage_vehicles()
    # elif page == "Upload Face Recognition":
    #     upload_face_recognition()
    elif page == "Process Gate Video":
        process_gate_video()
    elif page == "Access Logs":
        view_access_logs()
    elif page == "Settings":
        settings_page()



def manage_users():
    st.header("Manage Users")
    
    if st.session_state.user_role != "admin":
        st.error("Access denied. Only administrators can manage users.")
        return
    
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }
    
    # Tabs for different user management functions
    tab1, tab2 = st.tabs(["Register New User", "View/Edit Users"])
    
    with tab1:
        st.subheader("Register New User")
        with st.form("user_registration_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone_number = st.text_input("Phone Number")
            cnic = st.text_input("CNIC Number")
            registration_number = st.text_input("Registration Number")
            plate_number = st.text_input("Plate Number")
            model = st.text_input("Model")
            color = st.text_input("Color")
            face_image = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
            
            submit_button = st.form_submit_button("Register User")
            
            if submit_button:
                if not all([name, email, phone_number, cnic, registration_number,plate_number,model,color, face_image]):
                    st.error("All fields are required, including face image")
                else:
                    try:
                        # Prepare form data (not JSON)
                        data = {
                            "name": name,
                            "email": email,
                            "phone_number": phone_number,
                            "cnic": cnic,
                            "registration_number": registration_number,
                            "plate_number":plate_number,
                            "model":model,
                            "color":color
                        }
                        
                        # Prepare the file
                        files = {
                            'face_image': (face_image.name, face_image.getvalue(), face_image.type)
                        }
                        
                        # Send form-data request
                        response = requests.post(
                            f"{API_URL}/userdata/",
                            data=data,  # Use `data=` instead of `json=`
                            files=files,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            st.success("User registered successfully!")
                            st.rerun()
                        else:
                            error_detail = response.json().get('detail', 'Unknown error')
                            st.error(f"Failed to register user: {error_detail}")
                            # Debugging
                            st.write("Response Status Code:", response.status_code)
                            st.write("Response Content:", response.text)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    
    with tab2:
        st.subheader("Registered Users")
        try:
            # Add search by CNIC
            search_cnic = st.text_input("Search by CNIC")
            if search_cnic:
                response = requests.get(
                    f"{API_URL}/userdata/cnic/{search_cnic}",
                    headers=headers
                )
                if response.status_code == 200:
                    user_data = response.json()
                    display_user_data(user_data, headers)
                else:
                    st.warning("No user found with this CNIC")
            
            # Display all users
            response = requests.get(f"{API_URL}/userdata/", headers=headers)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    display_user_data(user, headers)
            else:
                st.error("Failed to fetch users")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def fetch_users(headers):
    try:
        response = requests.get(f"{API_URL}/userdata/", headers=headers)
        if response.status_code == 200:
            return response.json()  # Assuming the API returns a list of users
        else:
            st.error("Failed to fetch users")
            return []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []

# Call your function to display user data

def display_user_data(user, headers):
    with st.expander(f"{user['name']} - {user['cnic']}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Name:**", user['name'])
            st.write("**Email:**", user['email'])
            st.write("**Phone:**", user['phone_number'])
        with col2:
            st.write("**CNIC:**", user['cnic'])
            st.write("**Registration:**", user['registration_number'])
        with col3:
            st.write("**Plate Number**",user['plate_number'])
            st.write("**Model**",user['model'])
            st.write("**Color**",user['color'])
        
        # Edit and Delete buttons
        col4, col5 = st.columns(2)
        with col4:
            if st.button("Edit", key=f"edit_{user['id']}"):
                st.session_state.editing_user = user['id']
                with st.form(f"edit_user_{user['id']}"):
                    new_name = st.text_input("Name", value=user['name'])
                    new_email = st.text_input("Email", value=user['email'])
                    new_phone = st.text_input("Phone", value=user['phone_number'])
                    new_reg = st.text_input("Registration", value=user['registration_number'])
                    new_plateNumber = st.text_input("Plate Number", value=user['plate_number'])
                    new_face = st.file_uploader("Update Face Image (optional)", type=["jpg", "jpeg", "png"])
                    
                    if st.form_submit_button("Save Changes"):
                        try:
                            updated_data = {
                                "userData": {
                                    "name": new_name,
                                    "email": new_email,
                                    "phone_number": new_phone,
                                    "cnic": user['cnic'],
                                    "registration_number": new_reg,
                                    "plate_number":new_plateNumber
                                }
                            }
                            files = {}
                            if new_face:
                                files['face_image'] = ('image.jpg', new_face.getvalue(), 'image/jpeg')
                            
                            response = requests.put(
                                f"{API_URL}/userdata/{user['id']}",
                                json=updated_data,
                                files=files if files else None,
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                st.success("User updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update user: {response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with col5:
            if st.button("Delete", key=f"delete_{user['id']}"):
                try:
                    response = requests.delete(f"{API_URL}/userdata/{user['id']}", headers=headers)
                    if response.status_code == 200:
                        st.success("User deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def show_dashboard():
    st.header("Dashboard")
    

    st.title("User Management")

    headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

    if st.button("Show All Users"):
        users = fetch_users(headers)
        for user in users:
            display_user_data(user, headers)
    # Get summary data with auth token
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        # Get vehicle count
        vehicles_response = requests.get(f"{API_URL}/userdata", headers=headers)
        vehicles = vehicles_response.json() if vehicles_response.status_code == 200 else []
        
        # Get access logs
        logs_response = requests.get(f"{API_URL}/access", headers=headers)
        logs = logs_response.json() if logs_response.status_code == 200 else []
        
        # Display summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Registered Vehicles", len(vehicles))
        
        with col2:
            access_count = sum(1 for log in logs if log["status"] == "Granted")
            st.metric("Successful Access", access_count)
        
        with col3:
            denied_count = sum(1 for log in logs if log["status"] == "Denied")
            st.metric("Denied Access", denied_count)
        
        # Filter for recent logs (last 7 days)
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        recent_logs = [
            log for log in logs 
            if datetime.fromisoformat(log["entry_time"].replace("Z", "+00:00")) > week_ago
        ]
        
        # Create access trend chart
        if recent_logs:
            st.subheader("Recent Access Trends")
            df_logs = pd.DataFrame(recent_logs)
            df_logs["date"] = pd.to_datetime(df_logs["entry_time"]).dt.date
            
            # Group by date and status
            trend_data = df_logs.groupby(["date", "status"]).size().reset_index(name="count")
            
            # Plot
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.lineplot(data=trend_data, x="date", y="count", hue="status", markers=True, ax=ax)
            plt.title("Access Trends (Last 7 Days)")
            plt.xlabel("Date")
            plt.ylabel("Number of Access Attempts")
            st.pyplot(fig)
            
            # Display recent access table
            st.subheader("Recent Access Logs")
            
            # Get vehicle and user details for each log
            for log in recent_logs[:10]:  # Show only last 10
                vehicle_response = requests.get(f"{API_URL}/vehicles/{log['vehicle_id']}", headers=headers)
                vehicle = vehicle_response.json() if vehicle_response.status_code == 200 else {"plate_number": "Unknown", "model": "Unknown"}
                
                st.write(f"**{log['status']}** - {datetime.fromisoformat(log['entry_time'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"Vehicle: {vehicle['plate_number']} ({vehicle['model']})")
                st.markdown("---")
        else:
            st.info("No recent access logs available.")
            
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")

# def manage_vehicles():
#     st.header("Manage Vehicles")
    
#     headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
#     # Get existing vehicles
#     try:
#         response = requests.get(f"{API_URL}/vehicles", headers=headers)
#         if response.status_code == 200:
#             vehicles = response.json()
#         else:
#             st.error("Failed to fetch vehicles")
#             vehicles = []
#     except Exception as e:
#         st.error(f"Error connecting to server: {str(e)}")
#         vehicles = []
    
#     # Display existing vehicles
#     if vehicles:
#         st.subheader("Your Registered Vehicles")
#         for vehicle in vehicles:
#             col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
#             with col1:
#                 st.write(f"**Plate:** {vehicle['plate_number']}")
#             with col2:
#                 st.write(f"**Model:** {vehicle['model']}")
#             with col3:
#                 st.write(f"**Color:** {vehicle['color']}")
#             with col4:
#                 if st.button("Delete", key=f"del_{vehicle['id']}"):
#                     try:
#                         del_response = requests.delete(
#                             f"{API_URL}/vehicles/{vehicle['id']}",
#                             headers=headers
#                         )
#                         if del_response.status_code == 200:
#                             st.success("Vehicle deleted successfully!")
#                             st.rerun()
#                         else:
#                             st.error("Failed to delete vehicle")
#                     except Exception as e:
#                         st.error(f"Error: {str(e)}")
#             st.markdown("---")
#     else:
#         st.info("You don't have any registered vehicles.")
    
#     # Form to add new vehicle
#     st.subheader("Register New Vehicle")
#     with st.form("vehicle_form"):
#         plate_number = st.text_input("License Plate Number").upper()
#         model = st.text_input("Vehicle Model")
#         color = st.text_input("Vehicle Color")
        
#         submit_button = st.form_submit_button("Register Vehicle")
        
#         if submit_button:
#             if not plate_number or not model or not color:
#                 st.error("All fields are required")
#             else:
#                 try:
#                     response = requests.post(
#                         f"{API_URL}/vehicles",
#                         json={
#                             "plate_number": plate_number,
#                             "model": model,
#                             "color": color
#                         },
#                         headers=headers
#                     )
                    
#                     if response.status_code == 200:
#                         st.success("Vehicle registered successfully!")
#                         st.rerun()
#                     else:
#                         st.error(f"Failed to register vehicle: {response.json().get('detail', 'Unknown error')}")
#                 except Exception as e:
#                     st.error(f"Error connecting to server: {str(e)}")

# def upload_face_recognition():
#     st.header("Face Recognition Setup")
    
#     headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
#     st.write("Upload a clear photo of your face for the security system.")
#     st.write("This will be used to verify your identity when accessing restricted areas.")
    
#     # Check if face is already registered
#     try:
#         response = requests.get(f"{API_URL}/users/me", headers=headers)
#         if response.status_code == 200:
#             user_data = response.json()
#             has_face = user_data.get("face_embedding") is not None
#         else:
#             st.error("Failed to fetch user data")
#             has_face = False
#     except Exception as e:
#         st.error(f"Error connecting to server: {str(e)}")
#         has_face = False
    
#     if has_face:
#         st.success("✓ Face recognition is set up")
#         if st.button("Update Face Recognition"):
#             st.session_state.update_face = True
    
#     if not has_face or st.session_state.get("update_face", False):
#         uploaded_file = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        
#         if uploaded_file is not None:
#             # Display the uploaded image
#             image_bytes = uploaded_file.getvalue()
#             st.image(image_bytes, caption="Uploaded Image", width=300)
            
#             if st.button("Process and Save Face Recognition"):
#                 try:
#                     files = {"face_image": ("image.jpg", image_bytes, "image/jpeg")}
#                     response = requests.post(
#                         f"{API_URL}/users/face-embedding",
#                         files=files,
#                         headers=headers
#                     )
                    
#                     if response.status_code == 200:
#                         st.success("Face recognition setup successful!")
#                         st.session_state.pop("update_face", None)
#                         st.rerun()
#                     else:
#                         st.error(f"Failed to process face: {response.json().get('detail', 'Unknown error')}")
#                 except Exception as e:
#                     st.error(f"Error connecting to server: {str(e)}")


# /////////////////////////////////////////////////////////////////////////


# 
# def process_gate_video():
#     st.header("Process Gate Access Video")
    
#     if "token" not in st.session_state:
#         st.error("Please log in first")
#         return
        
#     headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
#     st.write("Upload a video from the gate camera to process vehicle license plate recognition.")
    
#     # Upload main gate video
#     uploaded_file = st.file_uploader("Upload Gate Video", type=["mp4", "avi", "mov"])
    
#     # Upload face video for recognition - make it required
#     uploaded_face_video = st.file_uploader("Upload Face Video (Required)", type=["mp4", "avi", "mov"])
    
#     if uploaded_file is not None:
#         # Save uploaded video to temp file for display
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
#             video_bytes = uploaded_file.getvalue()
#             if not video_bytes:
#                 st.error("The uploaded file is empty")
#                 return
                
#             tmp_file.write(video_bytes)
#             temp_path = tmp_file.name
        
#         try:
#             # Display the uploaded video
#             st.video(temp_path)
            
#             # Display face video if provided
#             face_temp_path = None
#             if uploaded_face_video is not None:
#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as face_tmp_file:
#                     face_video_bytes = uploaded_face_video.getvalue()
#                     face_tmp_file.write(face_video_bytes)
#                     face_temp_path = face_tmp_file.name
#                 st.write("Face Video:")
#                 st.video(face_temp_path)
            
#             process_button = st.button("Process Videos for Access")
            
#             if process_button:
#                 # Check if face video is missing
#                 if uploaded_face_video is None:
#                     st.error("Face video is required for access verification")
#                     return
                    
#                 with st.spinner("Processing videos... This may take a moment."):
#                     try:
#                         # Prepare files for API request
#                         files = {"gate_video": (uploaded_file.name, video_bytes, uploaded_file.type)}
                        
#                         # Add face video
#                         face_video_bytes = uploaded_face_video.getvalue()
#                         files["face_video"] = (uploaded_face_video.name, face_video_bytes, uploaded_face_video.type)
                        
#                         # Send request to API
#                         response = requests.post(
#                             f"{API_URL}/api/process-gate-video",
#                             files=files,
#                             headers=headers
#                         )
                        
#                         response_json = response.json()
                        
#                         if response.status_code == 200:
#                             # Display all plates found
#                             st.write("### License Plates Detected")
#                             all_plates = response_json.get("all_plates", [])
#                             if all_plates:
#                                 st.write("The following license plates were detected in the video:")
#                                 for plate in all_plates:
#                                     st.write(f"- {plate}")
#                             else:
#                                 st.warning("No license plates were detected in the video.")
                            
#                             # Create columns for showing recognition results
#                             col1, col2 = st.columns(2)
                            
#                             # Display license plate recognition results
#                             with col1:
#                                 st.write("### License Plate Recognition")
#                                 plate_match = response_json.get("plate_match", False)
#                                 confidence = response_json.get("confidence", 0)
                                
#                                 if plate_match:
#                                     st.success(f"✅ License plate matched with confidence: {confidence * 100:.1f}%")
#                                 else:
#                                     st.warning("❌ No matching license plate found in the database.")
                            
#                             # Display face recognition results
#                             with col2:
#                                 st.write("### Face Recognition")
#                                 face_match = response_json.get("face_match", False)
#                                 face_confidence = response_json.get("face_confidence", 0)
                                
#                                 if face_match:
#                                     st.success(f"✅ Face matched with confidence: {face_confidence * 100:.1f}%")
#                                 else:
#                                     st.warning("❌ No matching face found in the database.")
                            
#                             # Display access result (requires both plate and face match)
#                             st.write("### Access Decision")
#                             if response_json.get("access_granted"):
#                                 st.success("✅ ACCESS GRANTED")
#                                 st.write("Both license plate and face were successfully verified.")
                                
#                                 details = response_json.get("details", {})
#                                 if details:
#                                     with st.expander("View Access Details", expanded=True):
#                                         st.write("### Vehicle Information")
#                                         vehicle_info = details.get("vehicle_info", {})
#                                         st.write(f"**Plate Number:** {vehicle_info.get('plate_number', 'N/A')}")
#                                         st.write(f"**Model:** {vehicle_info.get('model', 'N/A')}")
#                                         st.write(f"**Color:** {vehicle_info.get('color', 'N/A')}")
                                        
#                                         st.write("### User Information")
#                                         user_info = details.get("user_info", {})
#                                         st.write(f"**Name:** {user_info.get('name', 'N/A')}")
#                                         st.write(f"**Email:** {user_info.get('email', 'N/A')}")
#                             else:
#                                 st.error("❌ ACCESS DENIED")
                                
#                                 # Explain access denial reason
#                                 if not response_json.get("plate_match") and not response_json.get("face_match"):
#                                     st.write("Neither license plate nor face matched records in the database.")
#                                 elif not response_json.get("plate_match"):
#                                     st.write("License plate not recognized.")
#                                 elif not response_json.get("face_match"):
#                                     st.write("Face not recognized.")
#                                 else:
#                                     st.write("Access denied for unknown reason.")

#                             # Log the access attempt
#                             user_id = response_json.get("user_id")
#                             vehicle_id = response_json.get("vehicle_id")
#                             status = "Granted" if response_json.get("access_granted") else "Denied"
                            
#                             if user_id is None or vehicle_id is None:
#                                 st.warning("Missing user or vehicle ID - access attempt not logged")
#                             else:
#                                 log_response = requests.post(
#                                     f"{API_URL}/access/",
#                                     json={
#                                         "user_id": user_id,
#                                         "vehicle_id": vehicle_id,
#                                         "status": status
#                                     },
#                                     headers=headers
#                                 )
                                
#                                 if log_response.status_code != 200:
#                                     st.warning("Failed to record access attempt in logs")
                                
#                         else:
#                             error_detail = response_json.get("detail", "Unknown error")
#                             st.error(f"Failed to process video: {error_detail}")
                    
#                     except requests.exceptions.RequestException as e:
#                         st.error(f"Network error: {str(e)}")
#                     except ValueError as e:
#                         st.error(f"Invalid response from server: {str(e)}")
#                     except Exception as e:
#                         st.error(f"Unexpected error: {str(e)}")
        
#         finally:
#             # Clean up temp files
#             try:
#                 if temp_path:
#                     os.unlink(temp_path)
#                 if face_temp_path:
#                     os.unlink(face_temp_path)
#             except Exception as e:
#                 st.error(f"Error removing temporary file: {str(e)}")

# /////////////////////////////////////////////////////////////////////////

def process_gate_video():
    st.header("Process Gate Access Video")
    
    if "token" not in st.session_state:
        st.error("Please log in first")
        return
        
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    st.write("Upload a video from the gate camera to process vehicle license plate recognition.")
    
    # Upload main gate video
    uploaded_file = st.file_uploader("Upload Gate Video", type=["mp4", "avi", "mov"])
    
    # Upload face video for recognition - make it required
    uploaded_face_video = st.file_uploader("Upload Face Video (Required)", type=["mp4", "avi", "mov"])
    
    if uploaded_file is not None:
        # Save uploaded video to temp file for display
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            video_bytes = uploaded_file.getvalue()
            if not video_bytes:
                st.error("The uploaded file is empty")
                return
                
            tmp_file.write(video_bytes)
            temp_path = tmp_file.name
        
        face_temp_path = None
        try:
            # Display the uploaded video
            st.video(temp_path)
            
            # Display face video if provided
            if uploaded_face_video is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as face_tmp_file:
                    face_video_bytes = uploaded_face_video.getvalue()
                    face_tmp_file.write(face_video_bytes)
                    face_temp_path = face_tmp_file.name
                st.write("Face Video:")
                st.video(face_temp_path)
            
            process_button = st.button("Process Videos for Access")
            
            if process_button:
                # Check if face video is missing
                if uploaded_face_video is None:
                    st.error("Face video is required for access verification")
                    return
                    
                with st.spinner("Processing videos... This may take a moment."):
                    try:
                        # Prepare files for API request
                        files = {"gate_video": (uploaded_file.name, video_bytes, uploaded_file.type)}
                        
                        # Add face video
                        face_video_bytes = uploaded_face_video.getvalue()
                        files["face_video"] = (uploaded_face_video.name, face_video_bytes, uploaded_face_video.type)
                        
                        # Send request to API
                        response = requests.post(
                            f"{API_URL}/api/process-gate-video",
                            files=files,
                            headers=headers
                        )
                        
                        response_json = response.json()
                        
                        if response.status_code == 200:
                            # Display all plates found
                            st.write("### License Plates Detected")
                            all_plates = response_json.get("all_plates", [])
                            if all_plates:
                                st.write("The following license plates were detected in the video:")
                                for plate in all_plates:
                                    st.write(f"- {plate}")
                            else:
                                st.warning("No license plates were detected in the video.")
                            
                            # Create columns for showing recognition results
                            col1, col2 = st.columns(2)
                            
                            # Display license plate recognition results
                            with col1:
                                st.write("### License Plate Recognition")
                                plate_match = response_json.get("plate_match", False)
                                confidence = response_json.get("confidence", 0)
                                
                                if plate_match:
                                    st.success(f"✅ License plate matched with confidence: {confidence * 100:.1f}%")
                                else:
                                    st.warning("❌ No matching license plate found in the database.")
                            
                            # Display face recognition results
                            with col2:
                                st.write("### Face Recognition")
                                face_match = response_json.get("face_match", False)
                                face_confidence = response_json.get("face_confidence", 0)
                                
                                if face_match:
                                    st.success(f"✅ Face matched with confidence: {face_confidence * 100:.1f}%")
                                else:
                                    st.warning("❌ No matching face found in the database.")
                            
                            # Display access result (requires both plate and face match)
                            st.write("### Access Decision")
                            if response_json.get("access_granted"):
                                st.success("✅ ACCESS GRANTED")
                                st.write("Both license plate and face were successfully verified.")
                                
                                # Get the user and vehicle details
                                details = response_json.get("details", {})
                                if details:
                                    with st.expander("View Access Details", expanded=True):
                                        st.write("### Vehicle Information")
                                        vehicle_info = details.get("vehicle_info", {})
                                        st.write(f"**Plate Number:** {vehicle_info.get('plate_number', 'N/A')}")
                                        st.write(f"**Model:** {vehicle_info.get('model', 'N/A')}")
                                        st.write(f"**Color:** {vehicle_info.get('color', 'N/A')}")
                                        
                                        st.write("### User Information")
                                        user_info = details.get("user_info", {})
                                        st.write(f"**Name:** {user_info.get('name', 'N/A')}")
                                        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
                            else:
                                st.error("❌ ACCESS DENIED")
                                
                                # Explain access denial reason
                                if not response_json.get("plate_match") and not response_json.get("face_match"):
                                    st.write("Neither license plate nor face matched records in the database.")
                                elif not response_json.get("plate_match"):
                                    st.write("License plate not recognized.")
                                elif not response_json.get("face_match"):
                                    st.write("Face not recognized.")
                                elif response_json.get("face_mismatch"):
                                    st.write("Face does not match the vehicle owner.")
                                else:
                                    st.write("Access denied for security reasons.")

                            # Log the access attempt
                            user_id = response_json.get("user_id")
                            vehicle_id = response_json.get("vehicle_id")
                            status = "Granted" if response_json.get("access_granted") else "Denied"
                        
                        # Only attempt to log if we have both IDs
                        # Always try to log the access attempt
                            try:
                                log_payload = {
                                    "status": status,  # "Granted" or "Denied"
                                    "timestamp": datetime.utcnow().isoformat()  # optional: include time if your API uses it
                                }

                                # Include user_id or vehicle_id if available
                                if user_id is not None:
                                    log_payload["user_id"] = user_id
                                if vehicle_id is not None:
                                    log_payload["vehicle_id"] = vehicle_id

                                log_response = requests.post(
                                    f"{API_URL}/access/",
                                    json=log_payload,
                                    headers=headers
                                )

                                if log_response.status_code == 200:
                                    st.info("✓ Access attempt logged successfully")
                                else:
                                    st.warning("⚠️ Failed to record access attempt in logs")

                            except Exception as e:
                                st.warning(f"⚠️ Error logging access: {str(e)}")

                        else:
                            st.info("Access attempt not logged - user and vehicle could not be identified at all")
                                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"Network error: {str(e)}")
                    except ValueError as e:
                        st.error(f"Invalid response from server: {str(e)}")
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")
        
        finally:
            # Clean up temp files
            try:
                if temp_path:
                    os.unlink(temp_path)
                if face_temp_path:
                    os.unlink(face_temp_path)
            except Exception as e:
                st.error(f"Error removing temporary file: {str(e)}")





def view_access_logs():
    st.header("Access Logs")
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    # Date range filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    status_filter = st.multiselect(
        "Status Filter", 
        options=["Granted", "Denied", "Pending"],
        default=["Granted", "Denied", "Pending"]
    )
    
    if st.button("Fetch Logs"):
        try:
            # Get access logs
            response = requests.get(f"{API_URL}/access", headers=headers)
            
            if response.status_code == 200:
                logs = response.json()
                
                # Convert to DataFrame for easier filtering
                df_logs = pd.DataFrame(logs)
                if not df_logs.empty:
                    # Convert date strings to datetime objects
                    df_logs["entry_time"] = pd.to_datetime(df_logs["entry_time"])
                    df_logs["exit_time"] = pd.to_datetime(df_logs["exit_time"])
                    
                    # Apply filters
                    df_logs = df_logs[
                        (df_logs["entry_time"].dt.date >= start_date) &
                        (df_logs["entry_time"].dt.date <= end_date) &
                        (df_logs["status"].isin(status_filter))
                    ]
                    
                    if not df_logs.empty:
                        # Add vehicle and user details
                        vehicle_details = {}
                        user_details = {}
                        
                        # Get unique vehicle and user IDs
                        vehicle_ids = df_logs["vehicle_id"].unique()
                        user_ids = df_logs["user_id"].unique()
                        
                        # Fetch vehicle details
                        for vid in vehicle_ids:
                            v_response = requests.get(f"{API_URL}/vehicles/{vid}", headers=headers)
                            if v_response.status_code == 200:
                                vehicle_details[vid] = v_response.json()
                        
                        # Fetch user details (admin only)
                        if st.session_state.user_role == "admin":
                            for uid in user_ids:
                                u_response = requests.get(f"{API_URL}/users/{uid}", headers=headers)
                                if u_response.status_code == 200:
                                    user_details[uid] = u_response.json()
                        
                        # Display logs
                        st.subheader(f"Access Logs ({len(df_logs)} records)")
                        
                        for _, log in df_logs.iterrows():
                            col1, col2 = st.columns([1, 3])
                            
                            with col1:
                                if log["status"] == "Granted":
                                    st.markdown("### ✅")
                                elif log["status"] == "Denied":
                                    st.markdown("### ❌")
                                else:
                                    st.markdown("### ⏳")
                            
                            with col2:
                                # Vehicle info
                                vehicle = vehicle_details.get(log["vehicle_id"], {"plate_number": "Unknown", "model": "Unknown"})
                                st.write(f"**Vehicle:** {vehicle.get('plate_number')} ({vehicle.get('model')})")
                                
                                # User info (if admin)
                                if st.session_state.user_role == "admin":
                                    user = user_details.get(log["user_id"], {"name": "Unknown", "email": "Unknown"})
                                    st.write(f"**User:** {user.get('name')} ({user.get('email')})")
                                
                                # Time info
                                entry_time = log["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
                                st.write(f"**Entry Time:** {entry_time}")
                                
                                if not pd.isna(log["exit_time"]):
                                    exit_time = log["exit_time"].strftime("%Y-%m-%d %H:%M:%S")
                                    st.write(f"**Exit Time:** {exit_time}")
                            
                            st.markdown("---")
                    else:
                        st.info("No logs found for the selected filters.")
                else:
                    st.info("No access logs available.")
            else:
                st.error("Failed to fetch access logs")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def settings_page():
    st.header("Account Settings")
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    # Get user info using the /me endpoint
    try:
        response = requests.get(f"{API_URL}/users/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
        else:
            st.error(f"Failed to fetch user data: {response.text}")
            return
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return
    
    # Display user information
    st.subheader("User Information")
    st.write(f"**Name:** {user_data['name']}")
    st.write(f"**Email:** {user_data['email']}")
    st.write(f"**Role:** {user_data['role']}")
    
    # Password change option
    st.subheader("Change Password")
    with st.form("password_change_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if new_password != confirm_password:
                st.error("New passwords do not match!")
                return
                
            try:
                response = requests.post(
                    f"{API_URL}/auth/change-password",
                    headers=headers,
                    json={
                        "current_password": current_password,
                        "new_password": new_password
                    }
                )
                if response.status_code == 200:
                    st.success("Password changed successfully!")
                else:
                    st.error(f"Failed to change password: {response.text}")
            except Exception as e:
                st.error(f"Error connecting to server: {str(e)}")
# Main app
def main():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    # Display appropriate page
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()
    else:
        login_page()

if __name__ == "__main__":
    main()