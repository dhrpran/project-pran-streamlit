from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection


COLUMNS = [
    "Date",
    "Teacher_Name",
    "School_Name",
    "District",
    "Category",
    "Summary",
    "Recommendations",
    "Uploaded_File",
]
DISTRICTS = ["District A", "District B", "District C"]
ACTIVITY_CATEGORIES = [
    "Physical Activity Everyday",
    "Diet - How to Choose Meal Plate",
    "Diet - Saying No to Junk Foods",
    "Diet - Reading Nutrition Values",
    "Saying No to Tobacco & Alcohol",
    "Home-based Activity with Parents",
]
UPLOAD_DIR = Path("uploads")
API = "http://127.0.0.1:8000/content"
DEFAULT_CONTENT = {
    "home_title": "Project PRAN",
    "home_text": "Preventing Risk Factors Among Adolescents for Noncommunicable Diseases",
    "hero_image": "https://images.unsplash.com/photo-1576091160550-2173dba999ef",
    "schools": 124,
    "students": 18450,
    "districts": 12,
    "activities": 540,
}


st.set_page_config(
    page_title="Project PRAN",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>

    .main {
        background-color: #f4f9f4;
    }

    .stButton>button {
        background-color: #1b5e20;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 16px;
    }

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_connection() -> GSheetsConnection:
    return st.connection("gsheets", type=GSheetsConnection)


def read_sheet(conn: GSheetsConnection) -> pd.DataFrame:
    try:
        data = conn.read(ttl="1m")
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    if data is None or data.empty:
        return pd.DataFrame(columns=COLUMNS)

    for column in COLUMNS:
        if column not in data.columns:
            data[column] = ""

    return data[COLUMNS]


def save_activity(
    conn: GSheetsConnection,
    existing_data: pd.DataFrame,
    new_row: pd.DataFrame,
) -> None:
    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
    conn.update(data=updated_df)


@st.cache_data(ttl=30)
def load_data() -> dict:
    return requests.get(API, timeout=3).json()


def load_home_content() -> dict:
    try:
        return load_data()
    except requests.RequestException:
        return DEFAULT_CONTENT


def render_admin_content_editor() -> None:
    data = load_home_content()

    st.subheader("Admin Content Editor")

    title = st.text_input("Title", value=data["home_title"])
    text = st.text_input("Text", value=data["home_text"])
    img = st.text_input("Image URL", value=data["hero_image"])

    schools = st.number_input("Schools", min_value=0, value=int(data["schools"]))
    students = st.number_input("Students", min_value=0, value=int(data["students"]))
    districts = st.number_input("Districts", min_value=0, value=int(data["districts"]))
    activities = st.number_input("Activities", min_value=0, value=int(data["activities"]))

    if st.button("Update Backend"):
        payload = {
            "home_title": title,
            "home_text": text,
            "hero_image": img,
            "schools": schools,
            "students": students,
            "districts": districts,
            "activities": activities,
        }

        try:
            response = requests.post(API, json=payload, timeout=3)
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error("Could not update backend content.")
            st.exception(exc)
            return

        st.cache_data.clear()
        st.success("Updated successfully!")
        st.rerun()


def save_uploaded_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    UPLOAD_DIR.mkdir(exist_ok=True)
    safe_name = Path(uploaded_file.name).name
    file_name = f"{uuid4().hex}_{safe_name}"
    file_path = UPLOAD_DIR / file_name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_name


def admin_password_is_valid() -> bool:
    configured_password = st.secrets.get("admin", {}).get("password", "")
    if not configured_password:
        st.error("Configuration Error: Admin password not found in Secrets panel.")
        return False

    entered_password = st.text_input("Enter Administrative Access Password:", type="password")
    if not entered_password:
        return False

    if entered_password != configured_password:
        st.error("Access Denied: Invalid Administrative Password Protocol.")
        return False

    st.success("Access Granted. Welcome Administrator.")
    return True


conn = get_connection()
existing_data = read_sheet(conn)

st.sidebar.title("Project PRAN Menu")
menu = st.sidebar.selectbox(
    "Go to page:",
    ["🏠 Project Overview", "Teacher Entry Panel", "Admin Dashboard"],
)

if menu == "🏠 Project Overview":
    data = load_home_content()

    st.title(data.get("home_title", "PRAN"))

    st.image(data.get("hero_image", ""), width="stretch")

    st.write(data.get("home_text", ""))

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Schools", data.get("schools", 0))

    with col2:
        st.metric("Students", data.get("students", 0))

    with col3:
        st.metric("Districts", data.get("districts", 0))

    with col4:
        st.metric("Activities", data.get("activities", 0))

    st.markdown("---")

    st.info(
        "Project PRAN is a school-based public health initiative "
        "focused on reducing adolescent risk factors for "
        "noncommunicable diseases."
    )

    st.markdown("## 🎯 Key Objectives")

    st.write("✅ Promote healthy lifestyle awareness")
    st.write("✅ Reduce adolescent NCD risk factors")
    st.write("✅ Strengthen school health systems")
    st.write("✅ Monitor district-level interventions")

    st.markdown("---")

    st.success(
        "Welcome to the centralized PRAN digital monitoring platform."
    )

elif menu == "Teacher Entry Panel":
    st.header("Submit School Activity Proof")
    st.write("Teachers: Fill out this reporting form after conducting your session.")

    with st.form("activity_submission_form", clear_on_submit=True):
        teacher_name = st.text_input("Teacher Name")
        school_name = st.text_input("School Name")
        district = st.selectbox("District Name", DISTRICTS)
        activity_category = st.selectbox("Activity Category", ACTIVITY_CATEGORIES)
        summary = st.text_area("Brief summary of session outcomes")
        recommendations = st.text_area("Recommendations")
        uploaded_file = st.file_uploader(
            "Upload Activity Evidence",
            type=["jpg", "jpeg", "png", "pdf", "mp4"],
        )

        submitted = st.form_submit_button("Submit Entry")

    if submitted:
        if teacher_name.strip() and school_name.strip() and summary.strip():
            file_name = save_uploaded_file(uploaded_file)
            new_row = pd.DataFrame(
                [
                        {
                            "Date": str(date.today()),
                            "Teacher_Name": teacher_name.strip(),
                            "School_Name": school_name.strip(),
                            "District": district,
                            "Category": activity_category,
                        "Summary": summary.strip(),
                        "Recommendations": recommendations.strip(),
                        "Uploaded_File": file_name,
                    }
                ]
            )

            try:
                save_activity(conn, existing_data, new_row)
            except Exception as exc:
                st.error("Could not save the activity to Google Sheets.")
                st.exception(exc)
            else:
                st.balloons()
                st.success(f"Excellent work, {teacher_name.strip()}! Data synced.")
        else:
            st.error("Please complete all required text fields before submitting.")

elif menu == "Admin Dashboard":
    st.header("Admin Security Verification")

    if not admin_password_is_valid():
        st.stop()

    st.divider()
    render_admin_content_editor()

    st.divider()
    st.subheader("Multi-District Central Activity Stream")

    if not existing_data.empty:
        filter_dist = st.selectbox("Filter Logs by Target District:", ["All Districts", *DISTRICTS])
        if filter_dist != "All Districts":
            display_data = existing_data[existing_data["District"] == filter_dist]
        else:
            display_data = existing_data

        st.dataframe(display_data, width="stretch", hide_index=True)
    else:
        st.info("The central spreadsheet tracker database is currently empty.")
