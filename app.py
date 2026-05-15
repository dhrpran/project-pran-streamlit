from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
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


st.set_page_config(
    page_title="Project PRAN Portal",
    page_icon=":material/health_and_safety:",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #f4f9f4; }
    h1, h2, h3 { color: #1b5e20; font-family: Arial, sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 12px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
        color: white;
        border-color: #1b5e20;
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
mode = st.sidebar.selectbox(
    "Go to page:",
    ["Project Overview", "Teacher Entry Panel", "Admin Dashboard"],
)

if mode == "Project Overview":
    st.markdown(
        "<h1 style='text-align: center;'>Project PRAN Portal</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 18px; color: #555;'>"
        "Preventing Risk Factors Among Adolescents for Noncommunicable Diseases"
        "</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Our Intervention Objective")
        st.write(
            """
            Project PRAN is an active school health roadmap deployed across **3 districts**.
            We empower teachers to build adolescent knowledge, positive attitudes, and
            self-efficacy across critical behavioral risk factors:

            * **Physical Activity:** Incorporating structured movement daily.
            * **Dietary Literacy:** Building healthy meal plates, understanding nutritional values, and refusing junk foods.
            * **Substance Prevention:** Confidently saying no to tobacco and alcohol.
            * **Home Integration:** Completing family health assignments alongside parents.
            """
        )
    with col2:
        st.info(
            "**Scope:** 3 Monitoring Districts\n\n"
            "**Metric:** Knowledge, Attitude & Practice (KAP)\n\n"
            "**Database:** Live Cloud Spreadsheet Syncing"
        )

elif mode == "Teacher Entry Panel":
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

elif mode == "Admin Dashboard":
    st.header("Admin Security Verification")

    if not admin_password_is_valid():
        st.stop()

    st.divider()
    st.subheader("Multi-District Central Activity Stream")

    if not existing_data.empty:
        filter_dist = st.selectbox("Filter Logs by Target District:", ["All Districts", *DISTRICTS])
        if filter_dist != "All Districts":
            display_data = existing_data[existing_data["District"] == filter_dist]
        else:
            display_data = existing_data

        st.dataframe(display_data, use_container_width=True, hide_index=True)
    else:
        st.info("The central spreadsheet tracker database is currently empty.")
