import streamlit as st
import mysql.connector
import pandas as pd
import io
from datetime import date

st.set_page_config(
    page_title="Sales Intelligence Hub",
    page_icon="📊",
    layout="wide"
)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="sales_int"
    )

def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    query = """
    SELECT user_id, username, password, branch_id, role, email
    FROM users
    WHERE TRIM(username) = %s AND TRIM(password) = %s
    LIMIT 1
    """
    cursor.execute(query, (username.strip(), password.strip()))
    user = cursor.fetchone()
    conn.close()
    return user

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.branch_id = None

# ----------------------------
# 15 SELECTED SQL QUESTIONS
# ----------------------------
SQL_QUESTIONS = [
    {
        "number": "Q1",
        "label":  "Retrieve all records from customer_sales",
        "sql":    "SELECT * FROM customer_sales",
        "desc":   "Shows every row in customer_sales — sale ID, branch, customer, product, amounts and status."
    },
    {
        "number": "Q2",
        "label":  "Retrieve all records from branches",
        "sql":    "SELECT * FROM branches",
        "desc":   "Lists all registered branches with their IDs and admin details."
    },
    {
        "number": "Q3",
        "label":  "Retrieve all records from payment_splits",
        "sql":    "SELECT * FROM payment_splits",
        "desc":   "Displays all payment transactions including date, method and amount paid."
    },
    {
        "number": "Q4",
        "label":  "Display all sales with status = 'Open'",
        "sql":    "SELECT * FROM customer_sales WHERE status = 'Open'",
        "desc":   "Filters sales records where payment is still open/unpaid."
    },
    {
        "number": "Q5",
        "label":  "Total gross sales across all branches",
        "sql":    "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales",
        "desc":   "Uses SUM() to calculate total gross sales across every record."
    },
    {
        "number": "Q6",
        "label":  "Total received & pending amount",
        "sql":    """SELECT
    SUM(received_amount) AS total_received,
    SUM(pending_amount)  AS total_pending
FROM customer_sales""",
        "desc":   "Single query to compare total collected vs total outstanding."
    },
    {
        "number": "Q7",
        "label":  "Count total number of sales per branch",
        "sql":    """SELECT b.branch_name, COUNT(cs.sale_id) AS total_sales
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY total_sales DESC""",
        "desc":   "Groups sales by branch and counts records per branch."
    },
    {
        "number": "Q8",
        "label":  "Average gross sales amount",
        "sql":    "SELECT ROUND(AVG(gross_sales), 2) AS avg_gross_sales FROM customer_sales",
        "desc":   "Uses AVG() to find the mean gross sales value across all records."
    },
    {
        "number": "Q9",
        "label":  "Sales details with branch name",
        "sql":    """SELECT cs.sale_id, b.branch_name, cs.date, cs.name,
       cs.product_name, cs.gross_sales, cs.status
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
ORDER BY cs.sale_id DESC""",
        "desc":   "JOIN between customer_sales and branches to show branch name alongside each sale."
    },
    {
        "number": "Q10",
        "label":  "Branch-wise total gross sales",
        "sql":    """SELECT b.branch_name, SUM(cs.gross_sales) AS total_gross_sales
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY total_gross_sales DESC""",
        "desc":   "Combines JOIN, GROUP BY and SUM to summarise gross sales by branch."
    },
    {
        "number": "Q11",
        "label":  "Sales with payment method used",
        "sql":    """SELECT cs.sale_id, cs.name, cs.product_name,
       p.payment_date, p.amount_paid, p.payment_method
FROM customer_sales cs
JOIN payment_splits p ON cs.sale_id = p.sale_id
ORDER BY cs.sale_id DESC""",
        "desc":   "Joins customer_sales with payment_splits to show payment method per sale."
    },
    {
        "number": "Q12",
        "label":  "Sales where pending amount > 5000",
        "sql":    """SELECT sale_id, name, product_name,
       gross_sales, received_amount, pending_amount, status
FROM customer_sales
WHERE pending_amount > 5000
ORDER BY pending_amount DESC""",
        "desc":   "Filters high-pending records — useful for follow-up collections."
    },
    {
        "number": "Q13",
        "label":  "Top 5 highest gross sales",
        "sql":    """SELECT sale_id, name, product_name, gross_sales, status
FROM customer_sales
ORDER BY gross_sales DESC
LIMIT 5""",
        "desc":   "Sorts by gross_sales descending and returns top 5 using LIMIT."
    },
    {
        "number": "Q14",
        "label":  "Monthly sales summary",
        "sql":    """SELECT YEAR(date) AS sale_year, MONTH(date) AS sale_month,
       COUNT(*) AS total_sales,
       SUM(gross_sales) AS total_gross,
       SUM(received_amount) AS total_received,
       SUM(pending_amount) AS total_pending
FROM customer_sales
GROUP BY YEAR(date), MONTH(date)
ORDER BY sale_year DESC, sale_month DESC""",
        "desc":   "Groups sales by YEAR() and MONTH() to produce a monthly financial summary."
    },
    {
        "number": "Q15",
        "label":  "Payment method-wise total collection",
        "sql":    """SELECT payment_method,
       COUNT(*) AS total_transactions,
       SUM(amount_paid) AS total_collected
FROM payment_splits
GROUP BY payment_method
ORDER BY total_collected DESC""",
        "desc":   "Compares Cash, UPI and Card collections — great for payment trend analysis."
    },
]

# ----------------------------
# LOGIN PAGE
# ----------------------------
if not st.session_state.logged_in:
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("## 📊 Sales Intelligence Hub")
        st.markdown("Manage your branches, track sales, and monitor payments — all in one place.")
        st.markdown("---")
        st.metric("Branches", "9+")
        st.metric("Security", "100% Secure")
        st.metric("Data", "Live")
    with col_right:
        st.markdown("### 👋 Welcome back!")
        st.markdown("Sign in to your account")
        st.markdown("")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("")
        if st.button("Login →", use_container_width=True):
            user = check_login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.session_state.branch_id = user["branch_id"]
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# ----------------------------
# MAIN APP
# ----------------------------
else:
    # Session state init
    if "sidebar_sql_q"  not in st.session_state: st.session_state.sidebar_sql_q  = None
    if "sql_expanded"   not in st.session_state: st.session_state.sql_expanded   = False
    if "dash_expanded"  not in st.session_state: st.session_state.dash_expanded  = False
    if "menu"           not in st.session_state: st.session_state.menu           = "Dashboard"

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.caption(f"Role: {st.session_state.role}")
        st.divider()

        # ── LEVEL 1: Dashboard (parent) ──
        dash_arrow = "🔽" if st.session_state.dash_expanded else "▶"
        if st.button(f"{dash_arrow} 📊 Dashboard", key="nav_dash_parent", use_container_width=True):
            st.session_state.dash_expanded = not st.session_state.dash_expanded
            if not st.session_state.dash_expanded:
                # collapse everything inside
                st.session_state.sql_expanded  = False
                st.session_state.sidebar_sql_q = None
                st.session_state.menu = "Dashboard"
            else:
                st.session_state.menu = "Dashboard"
            st.rerun()

        # ── LEVEL 2: sub-items under Dashboard ──
        if st.session_state.dash_expanded:
            sub_items = [
                ("📊", "Dashboard"),
                ("🏢", "Branches"),
                ("💼", "Sales"),
                ("💳", "Payments"),
            ]
            for icon, label in sub_items:
                is_active = (st.session_state.menu == label and not st.session_state.sql_expanded)
                prefix = "✅" if is_active else "  ▸"
                if st.button(f"{prefix} {icon} {label}", key=f"nav_{label}", use_container_width=True):
                    st.session_state.menu          = label
                    st.session_state.sql_expanded  = False
                    st.session_state.sidebar_sql_q = None
                    st.rerun()

            # ── LEVEL 2: SQL Questions toggle ──
            sql_arrow = "🔽" if st.session_state.sql_expanded else "  ▸"
            sql_active = "✅" if st.session_state.sql_expanded else ""
            if st.button(f"{sql_arrow} 🧪 SQL Questions", key="nav_sql_parent", use_container_width=True):
                st.session_state.sql_expanded = not st.session_state.sql_expanded
                if st.session_state.sql_expanded:
                    st.session_state.menu = "SQL Questions"
                else:
                    st.session_state.sidebar_sql_q = None
                    st.session_state.menu = "Dashboard"
                st.rerun()

            # ── LEVEL 3: 15 SQL questions ──
            if st.session_state.sql_expanded:
                for i, q in enumerate(SQL_QUESTIONS):
                    is_active = (st.session_state.sidebar_sql_q == q["number"])
                    short = q["label"][:30] + "…" if len(q["label"]) > 30 else q["label"]
                    lbl = f"{'    ✅' if is_active else '    ▹'} {i+1}. {short}"
                    if st.button(lbl, key=f"sb_{q['number']}", use_container_width=True):
                        st.session_state.sidebar_sql_q = None if is_active else q["number"]
                        st.session_state.menu = "SQL Questions"
                        st.rerun()

        st.markdown("")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","username","role","branch_id","sidebar_sql_q","menu","sql_expanded","dash_expanded"]:
                st.session_state[k] = (
                    False if k in ["logged_in","sql_expanded","dash_expanded"]
                    else None if k in ["branch_id","sidebar_sql_q"]
                    else "Dashboard" if k == "menu"
                    else ""
                )
            st.rerun()

    menu_clean = st.session_state.menu

    # ----------------------------
    # SIDEBAR SQL RESULT RENDERER
    # ----------------------------
    def render_sidebar_sql_result():
        if st.session_state.sidebar_sql_q:
            selected = next((q for q in SQL_QUESTIONS if q["number"] == st.session_state.sidebar_sql_q), None)
            if selected:
                st.divider()
                st.subheader(f"🧪 {selected['number']}. {selected['label']}")
                st.caption(selected["desc"])
                st.code(selected["sql"], language="sql")
                try:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(selected["sql"])
                    results = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    if results:
                        df_result = pd.DataFrame(results)
                        st.success(f"✅ {len(df_result)} row(s) returned")
                        excel_out = io.BytesIO()
                        with pd.ExcelWriter(excel_out, engine="openpyxl") as writer:
                            df_result.to_excel(writer, index=False, sheet_name="Query Result")
                        excel_out.seek(0)
                        st.download_button(
                            label="⬇️ Export Result",
                            data=excel_out,
                            file_name=f"query_{selected['number']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{selected['number']}"
                        )
                        st.dataframe(df_result, use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ Query returned 0 rows.")
                except Exception as e:
                    st.error(f"❌ Query Error: {e}")

    # ----------------------------
    # DASHBOARD
    # ----------------------------
    if menu_clean == "Dashboard":
        st.title("📊 Dashboard")
        st.caption("Overview of sales performance across branches")
        st.divider()

        is_super_admin = (st.session_state.role == "Super Admin")

        selected_branch_id = None if is_super_admin else st.session_state.branch_id
        selected_product    = "All Products"
        use_date            = False
        end_date            = date.today()

        # Fetch first record date from DB as default start
        conn = get_connection()
        cursor = conn.cursor()
        if is_super_admin:
            cursor.execute("SELECT MIN(date) FROM customer_sales")
        else:
            cursor.execute("SELECT MIN(date) FROM customer_sales WHERE branch_id = %s", (st.session_state.branch_id,))
        first_date_row = cursor.fetchone()[0]
        cursor.close(); conn.close()
        default_start = first_date_row if first_date_row else date.today()
        start_date = default_start

        with st.expander("🔍 Filters (Optional)", expanded=False):
            if is_super_admin:
                f1, f2, f3, f4 = st.columns([2, 2, 1.5, 1.5])
                with f1:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT branch_id, branch_name FROM branches ORDER BY branch_name")
                    all_branches = cursor.fetchall()
                    cursor.close(); conn.close()
                    branch_options = {"All Branches": None}
                    for b in all_branches:
                        branch_options[b["branch_name"]] = b["branch_id"]
                    selected_branch_name = st.selectbox("🏢 Branch", list(branch_options.keys()))
                    selected_branch_id = branch_options[selected_branch_name]
                with f2:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    if selected_branch_id is None:
                        cursor.execute("SELECT DISTINCT product_name FROM customer_sales ORDER BY product_name")
                    else:
                        cursor.execute("SELECT DISTINCT product_name FROM customer_sales WHERE branch_id = %s ORDER BY product_name", (selected_branch_id,))
                    products = [row["product_name"] for row in cursor.fetchall()]
                    cursor.close(); conn.close()
                    selected_product = st.selectbox("📦 Product", ["All Products"] + products)
                with f3:
                    use_date   = st.checkbox("Enable Date Filter")
                    start_date = st.date_input("📅 From Date", value=default_start, disabled=not use_date)
                with f4:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    end_date = st.date_input("📅 To Date", value=date.today(), disabled=not use_date)
            else:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT branch_name FROM branches WHERE branch_id = %s", (st.session_state.branch_id,))
                branch_row = cursor.fetchone()
                cursor.execute("SELECT DISTINCT product_name FROM customer_sales WHERE branch_id = %s ORDER BY product_name", (st.session_state.branch_id,))
                products = [row["product_name"] for row in cursor.fetchall()]
                cursor.close(); conn.close()
                f1, f2, f3, f4 = st.columns([2, 2, 1.5, 1.5])
                with f1:
                    st.text_input("🏢 Branch", value=branch_row["branch_name"] if branch_row else "", disabled=True)
                with f2:
                    selected_product = st.selectbox("📦 Product", ["All Products"] + products)
                with f3:
                    use_date   = st.checkbox("Enable Date Filter")
                    start_date = st.date_input("📅 From Date", value=default_start, disabled=not use_date)
                with f4:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    end_date = st.date_input("📅 To Date", value=date.today(), disabled=not use_date)

        if use_date and start_date > end_date:
            st.warning("⚠️ 'From Date' cannot be after 'To Date'.")
            st.stop()

        def build_where(branch_id, product, use_dt, s_date, e_date, alias="cs"):
            conditions = ["1=1"]
            params = []
            if branch_id is not None:
                conditions.append(f"{alias}.branch_id = %s"); params.append(branch_id)
            if product and product != "All Products":
                conditions.append(f"{alias}.product_name = %s"); params.append(product)
            if use_dt:
                conditions.append(f"{alias}.date BETWEEN %s AND %s"); params.extend([s_date, e_date])
            return "WHERE " + " AND ".join(conditions), params

        where_clause, query_params = build_where(selected_branch_id, selected_product, use_date, start_date, end_date)

        conn = get_connection()
        cursor = conn.cursor()
        if selected_branch_id is None:
            cursor.execute("SELECT COUNT(*) FROM branches")
        else:
            cursor.execute("SELECT COUNT(*) FROM branches WHERE branch_id = %s", (selected_branch_id,))
        total_branches = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM customer_sales cs {where_clause}", query_params)
        total_sales_records = cursor.fetchone()[0]
        cursor.execute(f"SELECT IFNULL(SUM(cs.gross_sales),0) FROM customer_sales cs {where_clause}", query_params)
        total_gross_sales = cursor.fetchone()[0]
        cursor.execute(f"SELECT IFNULL(SUM(cs.received_amount),0) FROM customer_sales cs {where_clause}", query_params)
        total_received = cursor.fetchone()[0]
        cursor.execute(f"SELECT IFNULL(SUM(cs.pending_amount),0) FROM customer_sales cs {where_clause}", query_params)
        total_pending = cursor.fetchone()[0]
        pay_where, pay_params = build_where(selected_branch_id, selected_product, use_date, start_date, end_date, alias="cs")
        cursor.execute(f"SELECT COUNT(*) FROM payment_splits p JOIN customer_sales cs ON p.sale_id = cs.sale_id {pay_where}", pay_params)
        total_payments = cursor.fetchone()[0]
        cursor.close(); conn.close()

        active_filters = []
        if is_super_admin and selected_branch_id is not None:
            active_filters.append("🏢 Branch filtered")
        if selected_product != "All Products":
            active_filters.append(f"📦 {selected_product}")
        if use_date:
            active_filters.append(f"📅 {start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')}")

        if active_filters:
            st.caption("Active Filters: " + "  |  ".join(active_filters))
        else:
            st.caption("✅ Showing all records — use Filters above to narrow down")

        m1, m2, m3 = st.columns(3)
        m1.metric("Branches", total_branches)
        m2.metric("Sales Records", total_sales_records)
        m3.metric("Payments", total_payments)
        st.markdown("")
        m4, m5, m6 = st.columns(3)
        m4.metric("Gross Sales", f"Rs.{total_gross_sales:,.0f}")
        m5.metric("Received",    f"Rs.{total_received:,.0f}")
        m6.metric("Pending",     f"Rs.{total_pending:,.0f}")
        st.divider()

        st.subheader("📋 Sales Records")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        tbl_where, tbl_params = build_where(selected_branch_id, selected_product, use_date, start_date, end_date, alias="cs")
        cursor.execute(f"""
            SELECT cs.sale_id AS "Sale ID", b.branch_name AS "Branch", cs.date AS "Date",
                   cs.name AS "Customer", cs.mobile_number AS "Mobile", cs.product_name AS "Product",
                   cs.gross_sales AS "Gross Sales", cs.received_amount AS "Received",
                   cs.pending_amount AS "Pending", cs.status AS "Status"
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            {tbl_where}
            ORDER BY cs.sale_id DESC
        """, tbl_params)
        sales_rows = cursor.fetchall()
        cursor.close(); conn.close()

        st.caption(f"🔍 {len(sales_rows)} record(s) found")
        if sales_rows:
            df = pd.DataFrame(sales_rows)
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Sales Data")
            excel_buf.seek(0)
            st.download_button("⬇️ Export to Excel", data=excel_buf, file_name="sales_data.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            def color_status(val):
                colors = {"Paid": "background-color: #dcfce7; color: #166534",
                          "Pending": "background-color: #fee2e2; color: #991b1b",
                          "Partial": "background-color: #fef9c3; color: #854d0e"}
                return colors.get(val, "")

            styled_df = df.style.applymap(color_status, subset=["Status"]).format(
                {"Gross Sales": "Rs.{:,.0f}", "Received": "Rs.{:,.0f}", "Pending": "Rs.{:,.0f}"})
            st.dataframe(styled_df, use_container_width=True, hide_index=True,
                         column_config={"Sale ID": st.column_config.NumberColumn("Sale ID"),
                                        "Date": st.column_config.DateColumn("Date"),
                                        "Gross Sales": st.column_config.NumberColumn("Gross Sales", format="Rs.%.0f"),
                                        "Received": st.column_config.NumberColumn("Received", format="Rs.%.0f"),
                                        "Pending": st.column_config.NumberColumn("Pending", format="Rs.%.0f")})
        else:
            st.info("No sales records found.")

        render_sidebar_sql_result()

    # ----------------------------
    # BRANCHES
    # ----------------------------
    elif menu_clean == "Branches":
        st.title("🏢 Branch Management")
        st.divider()
        if st.session_state.role == "Super Admin":
            with st.expander("➕ Add New Branch", expanded=False):
                branch_name = st.text_input("Branch Name")
                branch_admin_name = st.text_input("Branch Admin Name")
                if st.button("Add Branch"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO branches (branch_name, branch_admin_name) VALUES (%s, %s)",
                                   (branch_name, branch_admin_name))
                    conn.commit(); cursor.close(); conn.close()
                    st.success("✅ Branch added successfully")
        else:
            st.info("Admin can view only their own branch.")

        st.subheader("All Branches")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if st.session_state.role == "Super Admin":
            cursor.execute("SELECT * FROM branches")
        else:
            cursor.execute("SELECT * FROM branches WHERE branch_id = %s", (st.session_state.branch_id,))
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        st.dataframe(rows, use_container_width=True, hide_index=True)
        render_sidebar_sql_result()

    # ----------------------------
    # SALES
    # ----------------------------
    elif menu_clean == "Sales":
        st.title("💼 Sales Management")
        st.divider()
        with st.expander("➕ Add New Sale", expanded=False):
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            if st.session_state.role == "Super Admin":
                cursor.execute("SELECT branch_id, branch_name FROM branches")
            else:
                cursor.execute("SELECT branch_id, branch_name FROM branches WHERE branch_id = %s", (st.session_state.branch_id,))
            branches = cursor.fetchall()
            cursor.close(); conn.close()
            if not branches:
                st.warning("No branches found.")
            else:
                branch_dict = {b["branch_name"]: b["branch_id"] for b in branches}
                c1, c2 = st.columns(2)
                with c1:
                    selected_branch = st.selectbox("Select Branch", list(branch_dict.keys()))
                    sale_date = st.date_input("Sale Date")
                    customer_name = st.text_input("Customer Name")
                with c2:
                    mobile = st.text_input("Mobile Number")
                    product = st.text_input("Product Name")
                    gross = st.number_input("Gross Sales Amount", min_value=0.0)
                st.caption("ℹ️ Received amount will auto-update when payments are added.")
                if st.button("Add Sale"):
                    branch_id = branch_dict[selected_branch]
                    conn = get_connection()
                    cursor = conn.cursor()
                    # Insert with received_amount = 0, DB trigger will update on payment
                    cursor.execute("""INSERT INTO customer_sales
                        (branch_id, date, name, mobile_number, product_name, gross_sales, received_amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (branch_id, sale_date, customer_name, mobile, product, gross, 0))
                    conn.commit(); cursor.close(); conn.close()
                    st.success("✅ Sales record added successfully")

        st.subheader("Sales Records")
        search_term = st.text_input("🔍 Search by Customer Name", placeholder="Type customer name...")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if st.session_state.role == "Super Admin":
            cursor.execute("SELECT branch_id, branch_name FROM branches")
            all_branches = cursor.fetchall()
            filter_options = ["All Branches"] + [b["branch_name"] for b in all_branches]
            filter_branch = st.selectbox("Filter by Branch", filter_options)
            if filter_branch == "All Branches":
                cursor.execute("""SELECT sale_id, branch_id, date, name, mobile_number, product_name,
                    gross_sales, received_amount, pending_amount, status
                    FROM customer_sales WHERE name LIKE %s""", (f"%{search_term}%",))
            else:
                sel_bid = next((b["branch_id"] for b in all_branches if b["branch_name"] == filter_branch), None)
                cursor.execute("""SELECT sale_id, branch_id, date, name, mobile_number, product_name,
                    gross_sales, received_amount, pending_amount, status
                    FROM customer_sales WHERE branch_id = %s AND name LIKE %s""", (sel_bid, f"%{search_term}%"))
        else:
            cursor.execute("""SELECT sale_id, branch_id, date, name, mobile_number, product_name,
                gross_sales, received_amount, pending_amount, status
                FROM customer_sales WHERE branch_id = %s AND name LIKE %s""",
                (st.session_state.branch_id, f"%{search_term}%"))
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        st.dataframe(rows, use_container_width=True, hide_index=True)
        render_sidebar_sql_result()

    # ----------------------------
    # PAYMENTS
    # ----------------------------
    elif menu_clean == "Payments":
        st.title("💳 Payments")
        st.divider()
        tab1, tab2, tab3 = st.tabs(["➕ Add Payment", "📋 Payment History", "🧾 Receipt"])

        with tab1:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            if st.session_state.role == "Super Admin":
                cursor.execute("SELECT sale_id, name, product_name FROM customer_sales")
            else:
                cursor.execute("SELECT sale_id, name, product_name FROM customer_sales WHERE branch_id = %s", (st.session_state.branch_id,))
            sales_rows = cursor.fetchall()
            cursor.close(); conn.close()
            if sales_rows:
                sale_options = {f"{row['sale_id']} - {row['name']} - {row['product_name']}": row["sale_id"] for row in sales_rows}
                selected_sale_label = st.selectbox("Select Sale", list(sale_options.keys()))
                sale_id = sale_options[selected_sale_label]
            else:
                sale_id = None
                st.warning("No sales available for payment.")
            c1, c2 = st.columns(2)
            with c1:
                amount = st.number_input("Payment Amount", min_value=0.0)
            with c2:
                payment_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI"])
            if st.button("Add Payment"):
                if sale_id is None:
                    st.error("No valid sale selected.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        # 1. Insert payment
                        cursor.execute("INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method) VALUES (%s, CURDATE(), %s, %s)",
                                       (sale_id, amount, payment_method))
                        # 2. Auto update received_amount = SUM of all payments for this sale
                        cursor.execute("""
                            UPDATE customer_sales
                            SET received_amount = (
                                SELECT IFNULL(SUM(amount_paid), 0)
                                FROM payment_splits
                                WHERE sale_id = %s
                            ),
                            status = CASE
                                WHEN (SELECT IFNULL(SUM(amount_paid), 0) FROM payment_splits WHERE sale_id = %s) >= gross_sales THEN 'Paid'
                                WHEN (SELECT IFNULL(SUM(amount_paid), 0) FROM payment_splits WHERE sale_id = %s) > 0 THEN 'Partial'
                                ELSE 'Open'
                            END
                            WHERE sale_id = %s
                        """, (sale_id, sale_id, sale_id, sale_id))
                        conn.commit()
                        # Show updated summary
                        cursor2 = conn.cursor(dictionary=True)
                        cursor2.execute("SELECT gross_sales, received_amount, pending_amount, status FROM customer_sales WHERE sale_id = %s", (sale_id,))
                        updated = cursor2.fetchone()
                        cursor2.close()
                        st.success("✅ Payment added & amounts auto-updated!")
                        if updated:
                            u1, u2, u3, u4 = st.columns(4)
                            u1.metric("Gross Sales",  f"Rs.{updated['gross_sales']:,.0f}")
                            u2.metric("Received",     f"Rs.{updated['received_amount']:,.0f}")
                            u3.metric("Pending",      f"Rs.{updated['pending_amount']:,.0f}")
                            u4.metric("Status",       updated['status'])
                    except mysql.connector.Error as err:
                        st.error(f"Error: {err}")
                    finally:
                        cursor.close(); conn.close()

        with tab2:
            st.subheader("Payment History")
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                filter_payment_id = st.text_input("🔢 Payment ID", placeholder="e.g. 101", key="f_pid")
            with fc2:
                filter_customer = st.text_input("👤 Customer Name", placeholder="Search name...", key="f_cust")
            with fc3:
                filter_product = st.text_input("📦 Product Name", placeholder="Search product...", key="f_prod")
            with fc4:
                if st.session_state.role == "Super Admin":
                    conn_b = get_connection()
                    cur_b = conn_b.cursor(dictionary=True)
                    cur_b.execute("SELECT branch_name FROM branches ORDER BY branch_name")
                    branch_list = [r["branch_name"] for r in cur_b.fetchall()]
                    cur_b.close(); conn_b.close()
                    filter_branch = st.selectbox("🏢 Branch", ["All"] + branch_list, key="f_branch")
                else:
                    conn_b = get_connection()
                    cur_b = conn_b.cursor(dictionary=True)
                    cur_b.execute("SELECT branch_name FROM branches WHERE branch_id = %s", (st.session_state.branch_id,))
                    row_b = cur_b.fetchone()
                    cur_b.close(); conn_b.close()
                    filter_branch = row_b["branch_name"] if row_b else ""
                    st.text_input("🏢 Branch", value=filter_branch, disabled=True, key="f_branch_fixed")

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            base_query = """SELECT p.payment_id, cs.name AS customer_name, cs.product_name,
                       b.branch_name, p.payment_date, p.amount_paid, p.payment_method
                FROM payment_splits p
                JOIN customer_sales cs ON p.sale_id = cs.sale_id
                JOIN branches b ON cs.branch_id = b.branch_id WHERE 1=1"""
            params = []
            if st.session_state.role != "Super Admin":
                base_query += " AND cs.branch_id = %s"; params.append(st.session_state.branch_id)
            elif filter_branch != "All":
                base_query += " AND b.branch_name = %s"; params.append(filter_branch)
            if filter_payment_id.strip():
                base_query += " AND p.payment_id = %s"; params.append(filter_payment_id.strip())
            if filter_customer.strip():
                base_query += " AND cs.name LIKE %s"; params.append(f"%{filter_customer.strip()}%")
            if filter_product.strip():
                base_query += " AND cs.product_name LIKE %s"; params.append(f"%{filter_product.strip()}%")
            base_query += " ORDER BY p.payment_date DESC"
            cursor.execute(base_query, params)
            pay_rows = cursor.fetchall()
            cursor.close(); conn.close()
            st.caption(f"🔍 {len(pay_rows)} record(s) found")
            if pay_rows:
                df_pay = pd.DataFrame(pay_rows)
                pay_excel = io.BytesIO()
                with pd.ExcelWriter(pay_excel, engine="openpyxl") as writer:
                    df_pay.to_excel(writer, index=False, sheet_name="Payment History")
                pay_excel.seek(0)
                st.download_button("⬇️ Export Payment History", data=pay_excel, file_name="payment_history.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.dataframe(df_pay, use_container_width=True, hide_index=True)
            else:
                st.info("No payment records found.")

        with tab3:
            st.subheader("Generate Receipt for Customer")
            rf1, rf2, rf3 = st.columns(3)
            with rf1:
                receipt_search_id = st.text_input("🔢 Sale ID", placeholder="e.g. 101", key="r_sid")
            with rf2:
                receipt_search_name = st.text_input("👤 Customer Name", placeholder="Search name...", key="r_name")
            with rf3:
                receipt_search_product = st.text_input("📦 Product Name", placeholder="Search product...", key="r_prod")

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            base_r = """SELECT cs.sale_id, cs.name, cs.product_name, b.branch_name
                FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id WHERE 1=1"""
            r_params = []
            if st.session_state.role != "Super Admin":
                base_r += " AND cs.branch_id = %s"; r_params.append(st.session_state.branch_id)
            if receipt_search_id.strip():
                base_r += " AND cs.sale_id = %s"; r_params.append(receipt_search_id.strip())
            if receipt_search_name.strip():
                base_r += " AND cs.name LIKE %s"; r_params.append(f"%{receipt_search_name.strip()}%")
            if receipt_search_product.strip():
                base_r += " AND cs.product_name LIKE %s"; r_params.append(f"%{receipt_search_product.strip()}%")
            base_r += " ORDER BY cs.sale_id DESC"
            cursor.execute(base_r, r_params)
            receipt_sales = cursor.fetchall()
            cursor.close(); conn.close()

            st.caption(f"🔍 {len(receipt_sales)} record(s) found")
            if receipt_sales:
                receipt_options = {f"{r['sale_id']} - {r['name']} - {r['product_name']}": r["sale_id"] for r in receipt_sales}
                selected_receipt = st.selectbox("Select Sale for Receipt", list(receipt_options.keys()))
                receipt_sale_id = receipt_options[selected_receipt]
                if st.button("Generate Receipt"):
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT cs.*, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id WHERE cs.sale_id = %s", (receipt_sale_id,))
                    sale = cursor.fetchone()
                    cursor.execute("SELECT * FROM payment_splits WHERE sale_id = %s ORDER BY payment_date", (receipt_sale_id,))
                    payments = cursor.fetchall()
                    cursor.close(); conn.close()
                    if sale:
                        st.divider()
                        st.subheader(f"📊 Sales Intelligence Hub — {sale['branch_name']}")
                        st.caption("OFFICIAL RECEIPT")
                        st.divider()
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Receipt No:** #{sale['sale_id']:04d}")
                            st.write(f"**Date:** {sale['date']}")
                            st.write(f"**Customer:** {sale['name']}")
                        with col2:
                            st.write(f"**Mobile:** {sale['mobile_number']}")
                            st.write(f"**Product:** {sale['product_name']}")
                            status_icon = "🟢" if sale['status'] == "Paid" else "🔴" if sale['status'] == "Pending" else "🟡"
                            st.write(f"**Status:** {status_icon} {sale['status']}")
                        st.divider()
                        r1, r2, r3 = st.columns(3)
                        r1.metric("Gross Sales", f"Rs.{sale['gross_sales']:,.0f}")
                        r2.metric("Amount Received", f"Rs.{sale['received_amount']:,.0f}")
                        r3.metric("Pending Amount", f"Rs.{sale['pending_amount']:,.0f}")
                        st.divider()
                        st.write("**Payment History**")
                        if payments:
                            st.dataframe(pd.DataFrame(payments), use_container_width=True, hide_index=True)
                        else:
                            st.info("No payments recorded.")
                        receipt_text = f"""
SALES INTELLIGENCE HUB — RECEIPT
Branch: {sale['branch_name']}
{'='*40}
Receipt No : #{sale['sale_id']:04d}
Date       : {sale['date']}
Customer   : {sale['name']}
Mobile     : {sale['mobile_number']}
Product    : {sale['product_name']}
{'='*40}
Gross Sales    : Rs.{sale['gross_sales']:,.0f}
Received       : Rs.{sale['received_amount']:,.0f}
Pending        : Rs.{sale['pending_amount']:,.0f}
Status         : {sale['status']}
{'='*40}
PAYMENT HISTORY:
""" + "\n".join([f"  {p['payment_date']} | {p['payment_method']} | Rs.{p['amount_paid']:,.0f}" for p in payments])
                        st.download_button("⬇️ Download Receipt", data=receipt_text.encode(),
                                           file_name=f"receipt_{receipt_sale_id}.txt", mime="text/plain")
            else:
                st.info("No sales available for receipt.")

        render_sidebar_sql_result()

    # ----------------------------
    # SQL QUESTIONS PAGE
    # ----------------------------
    elif menu_clean == "SQL Questions":
        st.title("🧪 SQL Questions")
        st.caption("Select any question from the sidebar to run it here")
        st.divider()

        if st.session_state.sidebar_sql_q:
            selected = next((q for q in SQL_QUESTIONS if q["number"] == st.session_state.sidebar_sql_q), None)
            if selected:
                idx = next(i for i, q in enumerate(SQL_QUESTIONS) if q["number"] == selected["number"])
                st.subheader(f"📌 Q{idx+1}. {selected['label']}")
                st.caption(selected["desc"])
                st.markdown("**SQL Query:**")
                st.code(selected["sql"], language="sql")
                try:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(selected["sql"])
                    results = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    if results:
                        df_result = pd.DataFrame(results)
                        st.success(f"✅ Query executed successfully — {len(df_result)} row(s) returned")
                        excel_out = io.BytesIO()
                        with pd.ExcelWriter(excel_out, engine="openpyxl") as writer:
                            df_result.to_excel(writer, index=False, sheet_name="Query Result")
                        excel_out.seek(0)
                        st.download_button(
                            label="⬇️ Export Result to Excel",
                            data=excel_out,
                            file_name=f"query_{selected['number']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"page_dl_{selected['number']}"
                        )
                        st.dataframe(df_result, use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ Query ran successfully but returned 0 rows.")
                except Exception as e:
                    st.error(f"❌ Query Error: {e}")
        else:
            # Show all 15 questions as a clean reference table
            st.info("👈 Click any question from the sidebar to run it here.")
            st.markdown("")
            st.markdown("### 📋 All 15 Questions")
            for i, q in enumerate(SQL_QUESTIONS):
                with st.expander(f"**{i+1}. {q['label']}**"):
                    st.caption(q["desc"])
                    st.code(q["sql"], language="sql")
                    if st.button(f"▶ Run this query", key=f"run_{q['number']}"):
                        st.session_state.sidebar_sql_q = q["number"]
                        st.rerun()