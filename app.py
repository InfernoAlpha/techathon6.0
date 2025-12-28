import streamlit as st
import pandas as pd
import sqlite3
import time
import os
from PIL import Image
import numpy as np

st.set_page_config(
    page_title="EY Techathon - Automotive Agent Command Center",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_databases():

    conn = sqlite3.connect("mock_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, model TEXT, problem TEXT, date DATE)""")

    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO users (name, email,model,problem,date) VALUES (?,?,?,?,?)",[
            ("Alice Smith","alice@example.com","Model X","Engine Leak","2025-01-10"),
            ("Alice Smith","alice@example.com","Model X","Engine Crack","2025-03-21"),
            ("Bob Jones","bob@example.com","Model Y","Tyre Puncture","2025-07-15")
        ])
        conn.commit()
    conn.close()

    conn = sqlite3.connect("slots_booked.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS slots (id INTEGER PRIMARY KEY, customer_name TEXT, garage_name TEXT, price INTEGER, location TEXT, slot DATE)""")
    c.execute("SELECT count(*) FROM slots")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO slots (customer_name,garage_name,price,location,slot) VALUES (?,?,?,?,?)",[
            ("Zach","A Motors", 20000, "Hyderabad", "2025-11-10"),
            ("Xavier","B Motors", 19500, "Pune", "2025-11-15"),
            ("Yasmine","C Motors", 18000, "Mumbai", "2025-11-18")
        ])
        conn.commit()
    conn.close()

    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, name TEXT, model TEXT, feedback TEXT, date DATE, garage TEXT)""")
    c.execute("SELECT count(*) FROM feedback")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO feedback (name,model,feedback,date,garage) VALUES (?,?,?,?,?)",[
            ("Alice","Model X","Bad experience with mechanics","2025-01-10","A Motors"),
            ("Bob","Model X","Too expensive","2025-03-21","A Motors"),
            ("Charlie","Model Y","Short staffed but good work","2025-07-15","B Motors")
        ])
        conn.commit()
    conn.close()

init_databases()

def get_maintenance_data():
    conn = sqlite3.connect("mock_data.db")
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df

def get_slots_data():
    conn = sqlite3.connect("slots_booked.db")
    df = pd.read_sql_query("SELECT * FROM slots", conn)
    conn.close()
    return df

def get_feedback_data():
    conn = sqlite3.connect("feedback.db")
    df = pd.read_sql_query("SELECT * FROM feedback", conn)
    conn.close()
    return df

st.sidebar.title("🔧 Service Control")
page = st.sidebar.radio("Navigate", ["Dashboard", "Database Admin","RCA Reports"])

st.sidebar.divider()
st.sidebar.info("Backend Status: **ONLINE** 🟢")
st.sidebar.text(f"Build v1.0 | EY Techathon")

if page == "Dashboard":
    st.title("🚗 Dashboard")
    st.markdown("Real-time overview of vehicle diagnostics, bookings, and customer sentiment.")
    
    df_maint = get_maintenance_data()
    df_slots = get_slots_data()
    df_feed = get_feedback_data()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Diagnostics Run", len(df_maint), delta="2 Today")
    with col2:
        revenue = df_slots['price'].sum()
        st.metric("Projected Revenue", f"₹{revenue:,}", delta="+₹18,000")
    with col3:
        st.metric("Slots Booked", len(df_slots), delta="High Demand")
    with col4:
        neg_feedback = df_feed[df_feed['feedback'].str.contains('bad|expensive', case=False)].shape[0]
        st.metric("Critical Feedback", neg_feedback, delta_color="inverse")

    st.divider()

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Recent Vehicle Issues")
        st.dataframe(df_maint[['model', 'problem', 'date', 'name']].tail(5), use_container_width=True)
    
    with c2:
        st.subheader("Garage Load")
        garage_counts = df_slots['garage_name'].value_counts()
        st.bar_chart(garage_counts)

elif page == "Database Admin":
    st.title("💾 Backend Database Viewer")
    st.markdown("Direct access to the SQLite databases powering the agents.")

    tab1, tab2, tab3 = st.tabs(["Maintenance History (mock_database.py)", "Slots Booked (slots_booked.py)", "Feedback (feedback_database.py)"])
    
    with tab1:
        st.dataframe(get_maintenance_data(), use_container_width=True)
        st.caption("Source: `mock_data.db` | Schema: `users`")
        
    with tab2:
        st.dataframe(get_slots_data(), use_container_width=True)
        st.caption("Source: `slots_booked.db` | Schema: `slots`")
        
    with tab3:
        st.dataframe(get_feedback_data(), use_container_width=True)
        st.caption("Source: `feedback.db` | Schema: `feedback`")

# --- PAGE: RCA REPORTS ---
elif page == "RCA Reports":
    st.title("📄 RCA & CAPA Report Repository")
    st.markdown("Access technical documents generated by the `RCA_CAPA_init` agent node.")

    report_file = "RCA_CAPA_report.docx"
    
    if os.path.exists(report_file):
        # Get file stats
        file_stats = os.stat(report_file)
        file_size = f"{file_stats.st_size / 1024:.2f} KB"
        created_time = time.ctime(file_stats.st_ctime)

        # 1. File Info Card
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader("🛠️ Critical Failure Report: Model X")
                st.caption(f"Filename: `{report_file}` | Size: {file_size}")
                st.info("Trigger: Recurring Brake Pad Failure identified in Database.")
            with c2:
                with open(report_file, "rb") as f:
                    file_data = f.read()
                st.download_button(
                    label="⬇️ Download DOCX",
                    data=file_data,
                    file_name="RCA_Report_Final.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )

        # 2. DOCUMENT PREVIEW LOGIC
        try:
            from docx import Document
            
            st.divider()
            st.subheader("Document Preview")
            
            # Create an expander so it doesn't take up too much space
            with st.expander("👀 Click to read document content", expanded=True):
                doc = Document(report_file)
                
                # Iterate through paragraphs and display them
                st.markdown("---")
                for para in doc.paragraphs:
                    # Only show non-empty paragraphs to keep it clean
                    if para.text.strip():
                        st.write(para.text)
                st.markdown("---")
                
        except ImportError:
            st.error("Library missing. Please run: `pip install python-docx`")
        except Exception as e:
            st.error(f"Could not preview file: {e}")

    else:
        st.warning("⚠️ No RCA Reports found yet.")
        st.markdown("**Run the agent workflow to generate this file.**")