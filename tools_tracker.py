import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="Advanced Tools & Service Tracking", layout="wide")

st.markdown("""
    <style>
        .stApp { direction: ltr; }
        table { width: 100% !important; font-size: 13px !important; background-color: white; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Advanced Tools & Service Tracking System")

# ==========================================
# DATABASE INITIALIZATION (SQLite V2)
# ==========================================
DB_NAME = 'tools_service_v2.db'

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Tools table (Added Location & Next Maintenance)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            tool_id TEXT PRIMARY KEY,
            tool_name TEXT NOT NULL,
            category TEXT,
            serial_number TEXT,
            location TEXT,
            status TEXT DEFAULT 'Available',
            assigned_to TEXT,
            next_maintenance_date TEXT
        )
    ''')
    
    # Spare Parts table (New)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spare_parts (
            part_code TEXT PRIMARY KEY,
            part_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            unit_cost REAL DEFAULT 0.0
        )
    ''')
    
    # Service Logs table (Added Costs, Parts, and Photos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id TEXT,
            issue_description TEXT,
            technician TEXT,
            service_status TEXT,
            date_logged TEXT,
            date_resolved TEXT,
            repair_cost REAL DEFAULT 0.0,
            parts_used TEXT,
            photo_before BLOB,
            photo_after BLOB,
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
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
tab1, tab2, tab3, tab4 = st.tabs(["📦 Tools Inventory", "⚙️ Spare Parts", "🔧 Service & Maintenance", "📊 Reports & Export"])

# --- TAB 1: TOOLS INVENTORY ---
with tab1:
    st.subheader("Tool Registry & Status")
    
    if is_admin:
        with st.expander("➕ Add New Tool"):
            with st.form("add_tool_form"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    t_id = st.text_input("Tool ID / Barcode Code")
                    t_name = st.text_input("Tool Name")
                    t_cat = st.text_input("Category")
                    t_loc = st.text_input("Precise Location (e.g., Van 3, Shelf A)")
                with col_t2:
                    t_serial = st.text_input("Serial Number")
                    t_status = st.selectbox("Initial Status", ["Available", "In Service", "Assigned"])
                    t_assigned = st.text_input("Assigned To (Optional)")
                    t_maint = st.date_input("Next Preventive Maintenance Date")
                
                submit_tool = st.form_submit_button("Save Tool to Database", use_container_width=True)
                if submit_tool:
                    if t_id and t_name:
                        try:
                            run_query("INSERT INTO tools VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                      (t_id, t_name, t_cat, t_serial, t_loc, t_status, t_assigned, str(t_maint)), fetch=False)
                            st.success(f"Tool {t_name} added successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Tool ID already exists.")
                    else:
                        st.warning("Tool ID and Name are required.")

    # View Tools
    tools_data = run_query("SELECT tool_id, tool_name, category, location, status, assigned_to, next_maintenance_date FROM tools")
    tools_df = pd.DataFrame(tools_data, columns=["Tool ID", "Name", "Category", "Location", "Status", "Assigned To", "Next Maint."])
    
    search_q = st.text_input("🔍 Search Tools (by Name, ID, or Location):")
    if search_q:
        mask = tools_df.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
        st.markdown(tools_df[mask].to_html(index=False), unsafe_allow_html=True)
    else:
        st.markdown(tools_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 2: SPARE PARTS (EXCEL IMPORT) ---
with tab2:
    st.subheader("Spare Parts Inventory")
    
    if is_admin:
        with st.expander("📥 Import Parts via Excel"):
            st.info("Excel must have these exact column headers: **Part Code**, **Part Name**, **Quantity**, **Unit Cost**")
            uploaded_excel = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
            
            if uploaded_excel and st.button("Process & Import to Database"):
                try:
                    parts_df = pd.read_excel(uploaded_excel)
                    # Force required columns
                    req_cols = ['Part Code', 'Part Name', 'Quantity', 'Unit Cost']
                    if all(col in parts_df.columns for col in req_cols):
                        for _, row in parts_df.iterrows():
                            # INSERT OR REPLACE updates quantity/cost if code already exists
                            run_query("INSERT OR REPLACE INTO spare_parts VALUES (?, ?, ?, ?)", 
                                      (str(row['Part Code']), str(row['Part Name']), int(row['Quantity']), float(row['Unit Cost'])), fetch=False)
                        st.success("✅ Spare parts database updated successfully from Excel!")
                    else:
                        st.error(f"Missing required columns. Ensure your file has: {', '.join(req_cols)}")
                except Exception as e:
                    st.error(f"Error reading Excel: {e}")

    parts_data = run_query("SELECT * FROM spare_parts")
    if parts_data:
        parts_display_df = pd.DataFrame(parts_data, columns=["Part Code", "Part Name", "Quantity in Stock", "Unit Cost ($)"])
        st.markdown(parts_display_df.to_html(index=False), unsafe_allow_html=True)
    else:
        st.info("Spare parts inventory is currently empty.")

# --- TAB 3: SERVICE & MAINTENANCE TRACKING ---
with tab3:
    st.subheader("Service & Maintenance Hub")
    
    col_log, col_update = st.columns(2)
    
    # 1. Log a new issue
    with col_log:
        with st.expander("📝 Log New Damage / Issue", expanded=True):
            with st.form("service_form"):
                all_tools = run_query("SELECT tool_id, tool_name FROM tools WHERE status != 'In Service'")
                tool_options = {f"{row[0]} - {row[1]}": row[0] for row in all_tools}
                
                selected_tool = st.selectbox("Select Tool to Send to Service", list(tool_options.keys()) if tool_options else ["No available tools"])
                issue_desc = st.text_area("Issue Description")
                tech_name = st.text_input("Assigned Technician", value=current_user)
                
                st.write("📸 Attach Photo of Damage (Optional)")
                photo_before = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"], key="photo_b")
                camera_before = st.camera_input("Or snap photo", key="cam_b")
                
                submit_service = st.form_submit_button("Log Issue & Update Tool Status", use_container_width=True)
                if submit_service and tool_options and issue_desc:
                    tool_id_val = tool_options[selected_tool]
                    date_logged = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # Process image to binary
                    img_data = None
                    if photo_before: img_data = photo_before.getvalue()
                    elif camera_before: img_data = camera_before.getvalue()
                    
                    run_query('''INSERT INTO service_logs 
                                 (tool_id, issue_description, technician, service_status, date_logged, date_resolved, photo_before) 
                                 VALUES (?, ?, ?, 'In Progress', ?, 'Pending', ?)''',
                              (tool_id_val, issue_desc, tech_name, date_logged, img_data), fetch=False)
                    
                    run_query("UPDATE tools SET status = 'In Service' WHERE tool_id = ?", (tool_id_val,), fetch=False)
                    st.success("✅ Tool moved to service!")
                    st.rerun()

    # 2. Complete a repair
    with col_update:
        with st.expander("✅ Resolve Active Repair", expanded=True):
            active_logs = run_query("SELECT log_id, tool_id, issue_description FROM service_logs WHERE service_status = 'In Progress'")
            if active_logs:
                log_options = {f"Log #{row[0]} - Tool {row[1]}": row[0] for row in active_logs}
                with st.form("resolve_form"):
                    selected_log_label = st.selectbox("Select Active Repair Job", list(log_options.keys()))
                    
                    st.write("💰 Repair Data")
                    used_parts = st.text_input("Parts Used (Names/Codes)")
                    cost = st.number_input("Total Repair Cost ($)", min_value=0.0)
                    
                    st.write("📸 Attach Photo of Fix (Optional)")
                    photo_after = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"], key="photo_a")
                    camera_after = st.camera_input("Or snap photo", key="cam_a")
                    
                    submit_resolve = st.form_submit_button("Complete Repair & Return to Available", use_container_width=True)
                    
                    if submit_resolve:
                        log_id_val = log_options[selected_log_label]
                        date_res = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        img_fix_data = None
                        if photo_after: img_fix_data = photo_after.getvalue()
                        elif camera_after: img_fix_data = camera_after.getvalue()
                        
                        # Update Log
                        run_query('''UPDATE service_logs SET 
                                     service_status = 'Completed', date_resolved = ?, 
                                     parts_used = ?, repair_cost = ?, photo_after = ?
                                     WHERE log_id = ?''',
                                  (date_res, used_parts, cost, img_fix_data, log_id_val), fetch=False)
                        
                        # Find the tool ID to restore status
                        tool_id_query = run_query("SELECT tool_id FROM service_logs WHERE log_id = ?", (log_id_val,))
                        if tool_id_query:
                            run_query("UPDATE tools SET status = 'Available' WHERE tool_id = ?", (tool_id_query[0][0],), fetch=False)
                        
                        st.success("✅ Repair completed! Tool is now Available.")
                        st.rerun()
            else:
                st.info("No active repairs in progress.")

    st.divider()
    st.write("**Service History**")
    logs_data = run_query("SELECT log_id, tool_id, issue_description, technician, service_status, parts_used, repair_cost, date_logged, date_resolved FROM service_logs")
    logs_df = pd.DataFrame(logs_data, columns=["Log ID", "Tool ID", "Issue", "Technician", "Status", "Parts Used", "Cost", "Date Logged", "Date Resolved"])
    st.markdown(logs_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 4: REPORTS & EXPORT ---
with tab4:
    st.subheader("System Data & Export")
    
    st.info("Download permanent database records into Excel.")
    
    if st.button("📥 Generate Master Excel Report", type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Re-fetch latest data for export
            export_tools = pd.DataFrame(run_query("SELECT * FROM tools"), columns=["Tool ID", "Tool Name", "Category", "Serial", "Location", "Status", "Assigned To", "Next Maint."])
            export_parts = pd.DataFrame(run_query("SELECT * FROM spare_parts"), columns=["Part Code", "Name", "Quantity", "Unit Cost"])
            export_logs = pd.DataFrame(run_query("SELECT log_id, tool_id, issue_description, technician, service_status, date_logged, date_resolved, repair_cost, parts_used FROM service_logs"), columns=["Log ID", "Tool ID", "Issue", "Technician", "Status", "Date Logged", "Date Resolved", "Cost", "Parts Used"])
            
            export_tools.to_excel(writer, index=False, sheet_name='Tools_Inventory')
            export_parts.to_excel(writer, index=False, sheet_name='Spare_Parts')
            export_logs.to_excel(writer, index=False, sheet_name='Service_Logs')
            
        excel_data = output.getvalue()
        
        st.download_button(
            label="💾 Download Master Excel Report",
            data=excel_data,
            file_name="Master_Tools_Service_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
