import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="Tools & Service Tracking System", layout="wide")

st.markdown("""
    <style>
        .stApp { direction: ltr; }
        table { width: 100% !important; font-size: 13px !important; background-color: white; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Tools & Service Tracking System")

# ==========================================
# DATABASE INITIALIZATION (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('tools_service.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Tools table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            tool_id TEXT PRIMARY KEY,
            tool_name TEXT NOT NULL,
            category TEXT,
            serial_number TEXT,
            status TEXT DEFAULT 'Available',
            assigned_to TEXT
        )
    ''')
    
    # Service Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id TEXT,
            issue_description TEXT,
            technician TEXT,
            service_status TEXT,
            date_logged TEXT,
            date_resolved TEXT,
            FOREIGN KEY (tool_id) REFERENCES tools (tool_id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('admin', '123', 'Admin')")
        cursor.execute("INSERT INTO users VALUES ('tech', '123', 'Technician')")
        
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect('tools_service.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = None
    if fetch:
        result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

# ==========================================
# AUTHENTICATION & USER MANAGEMENT
# ==========================================
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

st.sidebar.header("🔐 Access Control")

if st.session_state['logged_in_user'] is None:
    with st.sidebar.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login", use_container_width=True)
        
        if login_btn:
            user_record = run_query("SELECT password, role FROM users WHERE username = ?", (username_input,))
            if user_record and user_record[0][0] == password_input:
                st.session_state['logged_in_user'] = username_input
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password.")
else:
    current_user = st.session_state['logged_in_user']
    user_role_query = run_query("SELECT role FROM users WHERE username = ?", (current_user,))
    current_role = user_role_query[0][0] if user_role_query else "Technician"
    
    st.sidebar.success(f"Welcome: {current_user}")
    st.sidebar.info(f"Role: {current_role}")
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

    if current_role == "Admin":
        st.sidebar.divider()
        st.sidebar.subheader("👥 User Management")
        with st.sidebar.form("new_user_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["Technician", "Admin"])
            add_user_btn = st.form_submit_button("Create User", use_container_width=True)
            
            if add_user_btn:
                if new_user and new_pass:
                    try:
                        run_query("INSERT INTO users VALUES (?, ?, ?)", (new_user, new_pass, new_role), fetch=False)
                        st.sidebar.success(f"User {new_user} created!")
                    except sqlite3.IntegrityError:
                        st.sidebar.error("Username already exists.")
                else:
                    st.sidebar.warning("Fill all fields.")

is_admin = (current_role == "Admin" if st.session_state['logged_in_user'] else False)

st.divider()

if st.session_state['logged_in_user'] is None:
    st.warning("⚠️ Please log in from the sidebar to access the system.")
    st.stop()

# ==========================================
# MAIN APPLICATION TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📦 Tools Inventory", "🔧 Service & Maintenance", "📊 Reports & Export"])

# --- TAB 1: TOOLS INVENTORY ---
with tab1:
    st.subheader("Tool Registry & Status")
    
    if is_admin:
        with st.expander("➕ Add New Tool"):
            with st.form("add_tool_form"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    t_id = st.text_input("Tool ID / Code")
                    t_name = st.text_input("Tool Name")
                    t_cat = st.text_input("Category (e.g., Electrical, Hand Tool)")
                with col_t2:
                    t_serial = st.text_input("Serial Number")
                    t_status = st.selectbox("Initial Status", ["Available", "In Service", "Assigned"])
                    t_assigned = st.text_input("Assigned To (Optional)")
                
                submit_tool = st.form_submit_button("Save Tool to Database", use_container_width=True)
                if submit_tool:
                    if t_id and t_name:
                        try:
                            run_query("INSERT INTO tools VALUES (?, ?, ?, ?, ?, ?)", 
                                      (t_id, t_name, t_cat, t_serial, t_status, t_assigned), fetch=False)
                            st.success(f"Tool {t_name} added successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Tool ID already exists.")
                    else:
                        st.warning("Tool ID and Name are required.")

    # Search and View Tools
    tools_data = run_query("SELECT * FROM tools")
    tools_df = pd.DataFrame(tools_data, columns=["Tool ID", "Tool Name", "Category", "Serial Number", "Status", "Assigned To"])
    
    search_q = st.text_input("🔍 Search Tools (by Name, ID, or Serial):")
    if search_q:
        mask = tools_df['Tool ID'].str.contains(search_q, case=False, na=False) | \
               tools_df['Tool Name'].str.contains(search_q, case=False, na=False) | \
               tools_df['Serial Number'].str.contains(search_q, case=False, na=False)
        tools_df = tools_df[mask]
        
    st.markdown(tools_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 2: SERVICE & MAINTENANCE TRACKING ---
with tab2:
    st.subheader("Service & Maintenance Logs")
    
    with st.expander("📝 Log New Service Request / Issue"):
        with st.form("service_form"):
            all_tools = run_query("SELECT tool_id, tool_name FROM tools")
            tool_options = {f"{row[0]} - {row[1]}": row[0] for row in all_tools}
            
            selected_tool_label = st.selectbox("Select Tool", list(tool_options.keys()) if tool_options else ["No tools available"])
            issue_desc = st.text_area("Issue Description / Service Requirement")
            technician_name = st.text_input("Assigned Technician", value=current_user)
            service_status = st.selectbox("Service Status", ["Pending", "In Progress", "Completed"])
            
            submit_service = st.form_submit_button("Submit Service Log", use_container_width=True)
            if submit_service:
                if tool_options and issue_desc:
                    tool_id_val = tool_options[selected_tool_label]
                    date_logged = datetime.now().strftime("%Y-%m-%d %H:%M")
                    date_res = date_logged if service_status == "Completed" else "Pending"
                    
                    run_query("INSERT INTO service_logs (tool_id, issue_description, technician, service_status, date_logged, date_resolved) VALUES (?, ?, ?, ?, ?, ?)",
                              (tool_id_val, issue_desc, technician_name, service_status, date_logged, date_res), fetch=False)
                    
                    # Update tool status
                    new_tool_status = "Available" if service_status == "Completed" else "In Service"
                    run_query("UPDATE tools SET status = ? WHERE tool_id = ?", (new_tool_status, tool_id_val), fetch=False)
                    
                    st.success("Service log recorded successfully!")
                    st.rerun()
                else:
                    st.warning("Please select a tool and describe the issue.")

    # View Service Logs
    logs_data = run_query("""
        SELECT s.log_id, s.tool_id, t.tool_name, s.issue_description, s.technician, s.service_status, s.date_logged 
        FROM service_logs s JOIN tools t ON s.tool_id = t.tool_id
    """)
    logs_df = pd.DataFrame(logs_data, columns=["Log ID", "Tool ID", "Tool Name", "Issue", "Technician", "Status", "Date Logged"])
    st.markdown(logs_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 3: REPORTS & EXPORT ---
with tab3:
    st.subheader("System Data & Export")
    
    st.info("Export live database tables into Excel reports.")
    
    if st.button("📥 Generate Excel Report", type="primary"):
        output = io_bytes = io.BytesIO() if 'io' in globals() or True else None
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            tools_df.to_excel(writer, index=False, sheet_name='Tools_Inventory')
            logs_df.to_excel(writer, index=False, sheet_name='Service_Logs')
        excel_data = output.getvalue()
        
        st.download_button(
            label="💾 Download Excel Report",
            data=excel_data,
            file_name="Tools_Service_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
