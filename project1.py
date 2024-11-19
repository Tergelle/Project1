import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from fpdf import FPDF


# Function to visualize Altman Z-Score using a Gauge Chart
def visualize_altman_z_score(z_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=z_score,
        title={'text': "Altman Z-Score", 'font': {'size': 24, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 40}},
        gauge={
            'axis': {'range': [0, 5], 'tickfont': {'color': 'white'}},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 1.8], 'color': "#FF6666"},   
                {'range': [1.8, 3], 'color': "#FFDD57"},   
                {'range': [3, 5], 'color': "#66CC66"}      
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': z_score
            }
        }
    ))

    fig.update_layout(
        height=500,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="#1E1E1E",  
        font=dict(color="white")
    )
    st.plotly_chart(fig)
    
# PDF    
def generate_pdf_report(ratio_groups):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(0, 10, "Financial Ratios Report", ln=True, align="C")
    pdf.ln(10)

    # Add each section dynamically
    for section, ratios in ratio_groups.items():
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(0, 10, section, ln=True)
        pdf.set_font("Arial", size=12)

        for ratio_name, ratio_values in ratios.items():
            pdf.cell(0, 10, f"{ratio_name}: Beginning = {ratio_values['beginning']:.2f}, End = {ratio_values['end']:.2f}", ln=True)

        pdf.ln(5)

    # Save the PDF to a file-like object
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return pdf_output

# Display the download button
def show_pdf_download_button(pdf_content):
    st.subheader("Download Financial Ratios Report (PDF)")
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_content,
        file_name="financial_ratios_report.pdf",
        mime="application/pdf",
        help="Click to download the financial analysis report."
    )


# Check if "page" exists in the session state
if "page" not in st.session_state:
    st.session_state.page = "Home"
# Check if "uploaded_file" exists in the session state
#Ensuring that the file isn't lost when navigating between pages.
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    
# Set up navigation using buttons
st.sidebar.title("Navigation")
if st.sidebar.button(" 🏠 Home"):
    st.session_state.page = "Home"
if st.sidebar.button(" 📈 Financial Analysis"):
    st.session_state.page = "Financial Analysis"   


# Define a function to show the Home Page
def show_home_page():
    st.title("📊 Financial Analysis App")
    st.write("""
    Welcome to the Financial Analysis App! This app allows you to upload your financial data and calculates various financial ratios to assess the performance and health of a company.

    ### Purpose of the App
    The purpose of this app is to provide a quick and efficient analysis of a company's financial statements by calculating key financial ratios. These ratios help in understanding the company's profitability, activity, and solvency.

    ### Key Ratios Explained
    1. **Activity Ratios**:
       - **Inventory Turnover**: Indicates how many times inventory is sold and replaced over a period.
       - **Days of Inventory**: Average number of days inventory is held.
       - **Receivables Turnover**: Measures how efficiently receivables are collected.
       - **Days of Sales Outstanding**: Average collection period for receivables.
       - **Fixed Asset Turnover**: Efficiency of using fixed assets to generate revenue.
       - **Total Asset Turnover**: Overall efficiency of using assets to generate revenue.
    
    2. **Liquidity Ratios**:
       - **Current Ratio**: Evaluates the company's ability to cover its current liabilities with its current assets.
       - **Quick Ratio**: Excludes inventory, providing a more conservative view of liquidity.
       - **Cash Ratio**: Focuses on the most liquid asset, cash, to determine the company’s immediate ability to pay off liabilities.

    3. **Solvency Ratios**:
       - **Debt-to-Equity Ratio**: Indicates the proportion of debt used relative to equity.
       - **Debt Ratio**: Percentage of assets financed by liabilities.
       - **Equity Ratio**: Percentage of assets financed by equity.
       - **Interest Coverage Ratio**: Assesses the company's ability to pay interest expenses.
    
    4. **Profitability Ratios**:
       - **Gross Profit Margin**: Measures the percentage of revenue that exceeds the cost of goods sold.
       - **Net Profit Margin**: Indicates how much net income is generated as a percentage of revenue.
       - **Return on Assets (ROA)**: Shows how efficiently a company uses its assets to generate profit.
       - **Return on Equity (ROE)**: Measures the return generated on shareholders' equity.
       
    5. **Altman Z-Score**:
   - The **Altman Z-Score** is a financial metric used to assess a company's likelihood of bankruptcy. It combines several financial ratios to create a single score. The score is interpreted as follows:
     - **Z-Score > 2.99**: The company is in a **safe zone**, indicating a low risk of bankruptcy.
     - **1.81 ≤ Z-Score ≤ 2.99**: The company is in the **gray zone**, indicating a moderate risk of bankruptcy.
     - **Z-Score < 1.81**: The company is in the **distress zone**, indicating a high risk of bankruptcy.
""")
       

# Define a function to show the Financial Analysis Page
def show_analysis_page():
    st.title("Financial Analysis")

    # File upload for Financial Analysis page
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    # File uploader component
    uploaded_file = st.file_uploader("Upload your Excel file (.xls or .xlsx)", type=["xls", "xlsx"])

    # If a new file is uploaded, store it in session state
    if uploaded_file is not None:
        try:
        # Check file extension
            if uploaded_file.name.endswith('.xls'):
            # Save the uploaded BytesIO to a temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
            
            # Load the file using Pandas and xlrd
                excel_file = pd.ExcelFile(tmp_path, engine='xlrd')
            else:
            # Load .xlsx file directly
                excel_file = pd.ExcelFile(uploaded_file, engine='openpyxl')

        # Load sheets for further calculations
            if "СБД" in excel_file.sheet_names and "ОДТ" in excel_file.sheet_names:
                balance_sheet_df = pd.read_excel(excel_file, sheet_name="СБД", skiprows=4)
                income_statement_df = pd.read_excel(excel_file, sheet_name="ОДТ", skiprows=4)
                retained_earning_df = pd.read_excel(excel_file, sheet_name="ӨӨТ", skiprows=4)
                cashflow_statement_df = pd.read_excel(excel_file, sheet_name="МГТ", skiprows=4)

                # Drop empty columns
                balance_sheet_df.dropna(axis=1, how='all', inplace=True)
                income_statement_df.dropna(axis=1, how='all', inplace=True)

                # Show first few rows of the DataFrames
                with st.expander("Show Preview of Balance Sheet"):
                    st.write("Balance Sheet Preview:", balance_sheet_df.head())
                with st.expander("Show Preview of Income Statement"):
                    st.write("Income Statement Preview:", income_statement_df.head())

                # Extracting the necessary data
                try:
                    cash_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    cash_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ar_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ar_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ca_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эргэлтийн хөрөнгийн дүн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ca_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эргэлтийн хөрөнгийн дүн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    cl_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Богино хугацаат өр төлбөрийн дүн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    cl_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Богино хугацаат өр төлбөрийн дүн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    re_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Хуримтлагдсан ашиг', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    re_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Хуримтлагдсан ашиг', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    inv_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Бараа материал', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    inv_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Бараа материал', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    revenue_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Борлуулалтын орлого (цэвэр)', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    revenue_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Борлуулалтын орлого (цэвэр)', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    cogs_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Борлуулалтын өртөг', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    cogs_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Борлуулалтын өртөг', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    total_assets_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Нийт хөрөнгийн дүн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    total_assets_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Нийт хөрөнгийн дүн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    total_equity_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эздийн өмчийн дүн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    total_equity_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эздийн өмчийн дүн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    sts_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Борлуулах зорилгоор эзэмшиж буй эргэлтийн бус хөрөнгө (борлуулах бүлэг хөрөнгө)', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    sts_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Борлуулах зорилгоор эзэмшиж буй эргэлтийн бус хөрөнгө (борлуулах бүлэг хөрөнгө)', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    gross_profit_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Нийт ашиг ( алдагдал)', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    gross_profit_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Нийт ашиг ( алдагдал)', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    net_income_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Тайлант үеийн цэвэр ашиг ( алдагдал)', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    net_income_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Тайлант үеийн цэвэр ашиг ( алдагдал)', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    fa_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эргэлтийн бус хөрөнгийн дүн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    fa_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Эргэлтийн бус хөрөнгийн дүн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ebit_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Татвар төлөхийн өмнөх  ашиг (алдагдал)', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ebit_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Татвар төлөхийн өмнөх  ашиг (алдагдал)', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    stl_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Богино хугацаат зээл', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    stl_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Богино хугацаат зээл', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ltl_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Урт хугацаат зээл', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ltl_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Урт хугацаат зээл', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    total_liabilities_beginning = stl_beginning + ltl_beginning
                    total_liabilities_end = stl_end + ltl_end

                    interest_expense_beginning = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Орлогын татварын зардал', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    interest_expense_end = pd.to_numeric(income_statement_df.loc[income_statement_df['Үзүүлэлт'] == 'Орлогын татварын зардал', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')


# Activity Ratios (Beginning of the Year)
                    inventory_turnover_beginning = cogs_beginning / inv_beginning if inv_beginning != 0 else float('nan')
                    days_of_inventory_beginning = 365 / inventory_turnover_beginning if inventory_turnover_beginning != 0 else float('nan')
                    receivables_turnover_beginning = revenue_beginning / ar_beginning if ar_beginning != 0 else float('nan')
                    days_of_sales_beginning = 365 / receivables_turnover_beginning if receivables_turnover_beginning != 0 else float('nan')
                    fixed_asset_turnover_beginning = revenue_beginning / fa_beginning if fa_beginning != 0 else float('nan')
                    total_asset_turnover_beginning = revenue_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')

# Activity Ratios (End of the Year)
                    inventory_turnover_end = cogs_end / inv_end if inv_end != 0 else float('nan')
                    days_of_inventory_end = 365 / inventory_turnover_end if inventory_turnover_end != 0 else float('nan')
                    receivables_turnover_end = revenue_end / ar_end if ar_end != 0 else float('nan')
                    days_of_sales_end = 365 / receivables_turnover_end if receivables_turnover_end != 0 else float('nan')
                    fixed_asset_turnover_end = revenue_end / fa_end if fa_end != 0 else float('nan')
                    total_asset_turnover_end = revenue_end / total_assets_end if total_assets_end != 0 else float('nan')

# Storing the ratios in a dictionary for easy access/display
                    activity_ratios = {
    "Inventory Turnover": {"Beginning": inventory_turnover_beginning, "End": inventory_turnover_end},
    "Days of Inventory": {"Beginning": days_of_inventory_beginning, "End": days_of_inventory_end},
    "Receivables Turnover": {"Beginning": receivables_turnover_beginning, "End": receivables_turnover_end},
    "Days of Sales Outstanding": {"Beginning": days_of_sales_beginning, "End": days_of_sales_end},
    "Fixed Asset Turnover": {"Beginning": fixed_asset_turnover_beginning, "End": fixed_asset_turnover_end},
    "Total Asset Turnover": {"Beginning": total_asset_turnover_beginning, "End": total_asset_turnover_end},
}

# Convert the activity ratios dictionary to a DataFrame for display
                    activity_ratios_df = pd.DataFrame(activity_ratios).T
                    activity_ratios_df.columns = ["Beginning of Year", "End of Year"]

# Display the activity ratios in a table format
                    st.subheader("📈 Activity Ratios")
                    st.table(activity_ratios_df)

# Prepare data for visualization
                    with st.expander("Show Graph"):
                        st.subheader("Activity Ratios Comparison")  
                        activity_ratios_visual = activity_ratios_df.reset_index().melt(id_vars="index", var_name="Period", value_name="Value")
                        pivot_data = activity_ratios_visual.pivot(index="index", columns="Period", values="Value")

# Check if the data is not empty
                        if not pivot_data.empty:
                            st.bar_chart(data=pivot_data)
                        else:
                            st.write("No data available to display.")
            

# Liquidity Ratios (Beginning of Year and End of Year)
                    current_ratio_beginning = ca_beginning / cl_beginning if cl_beginning != 0 else float('nan')
                    current_ratio_end = ca_end / cl_end if cl_end != 0 else float('nan')

                    quick_ratio_beginning = (cash_beginning + sts_beginning + ar_beginning) / cl_beginning if cl_beginning != 0 else float('nan')
                    quick_ratio_end = (cash_end + sts_end + ar_end) / cl_end if cl_end != 0 else float('nan')

                    cash_ratio_beginning = (cash_beginning + sts_beginning) / cl_beginning if cl_beginning != 0 else float('nan')
                    cash_ratio_end = (cash_end + sts_end) / cl_end if cl_end != 0 else float('nan')

# Prepare data for display
                    ratios_data = {
    "Ratio": ["Current Ratio", "Quick Ratio", "Cash Ratio"],
    "Beginning of Year": [current_ratio_beginning, quick_ratio_beginning, cash_ratio_beginning],
    "End of Year": [current_ratio_end, quick_ratio_end, cash_ratio_end]
}

# Convert to DataFrame
                    ratios_df = pd.DataFrame(ratios_data)
                    ratios_df.set_index("Ratio", inplace=True)

                    st.subheader("💵 Liquidity Ratios")
                    st.table(ratios_df)

# Prepare data for bar chart visualization
                    with st.expander("Show Graph"):
                        st.subheader("Liquidity Ratios Comparison")  
                        ratios_chart_data = ratios_df.reset_index().melt(id_vars="Ratio", var_name="Period", value_name="Value")
                        pivot_data = ratios_chart_data.pivot(index="Ratio", columns="Period", values="Value")

# Check if the data is not empty
                        if not pivot_data.empty:
                            st.bar_chart(data=pivot_data)
                        else:
                            st.write("No data available to display.")

# Solvency Ratios (Beginning of Year and End of Year)
                    debt_to_equity_beginning = total_liabilities_beginning / total_equity_beginning if total_equity_beginning != 0 else float('nan')
                    debt_to_equity_end = total_liabilities_end / total_equity_end if total_equity_end != 0 else float('nan')

                    debt_ratio_beginning = total_liabilities_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')
                    debt_ratio_end = total_liabilities_end / total_assets_end if total_assets_end != 0 else float('nan')

                    equity_ratio_beginning = total_equity_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')
                    equity_ratio_end = total_equity_end / total_assets_end if total_assets_end != 0 else float('nan')

                    interest_coverage_ratio_beginning = net_income_beginning / interest_expense_beginning if interest_expense_beginning != 0 else float('nan')
                    interest_coverage_ratio_end = net_income_end / interest_expense_end if interest_expense_end != 0 else float('nan')

# Prepare data for display
                    solvency_ratios_data = {
    "Ratio": ["Debt-to-Equity Ratio", "Debt Ratio", "Equity Ratio", "Interest Coverage Ratio"],
    "Beginning of Year": [
        debt_to_equity_beginning,
        debt_ratio_beginning,
        equity_ratio_beginning,
        interest_coverage_ratio_beginning,
    ],
    "End of Year": [
        debt_to_equity_end,
        debt_ratio_end,
        equity_ratio_end,
        interest_coverage_ratio_end,
    ],
}

# Convert to DataFrame
                    solvency_ratios_df = pd.DataFrame(solvency_ratios_data)
                    solvency_ratios_df.set_index("Ratio", inplace=True)

                    st.subheader("🔍 Solvency Ratios")
                    st.table(solvency_ratios_df)

                    if debt_to_equity_end > 2:
                        st.warning("The Debt-to-Equity Ratio at the end of the year is above 2.0, indicating high leverage.")
                        
                    # Prepare data for solvency ratios chart
                    solvency_ratios_data = {
    "Ratio": ["Debt-to-Equity Ratio", "Debt Ratio", "Equity Ratio", "Interest Coverage Ratio"],
    "Beginning of Year": [debt_to_equity_beginning, debt_ratio_beginning, equity_ratio_beginning, interest_coverage_ratio_beginning],
    "End of Year": [debt_to_equity_end, debt_ratio_end, equity_ratio_end, interest_coverage_ratio_end]
}
                    solvency_ratios_df =               pd.DataFrame(solvency_ratios_data).set_index("Ratio")

# Add expander for Solvency Ratios Graph
                    with st.expander("Show Graph"):
                        st.subheader("Solvency Ratios Comparison")
                        st.bar_chart(solvency_ratios_df)

    
    
# Profitability Ratios (Beginning of Year and End of Year)
                    gross_profit_margin_beginning = (gross_profit_beginning / revenue_beginning) * 100 if revenue_beginning != 0 else float('nan')
                    gross_profit_margin_end = (gross_profit_end / revenue_end) * 100 if revenue_end != 0 else float('nan')

                    net_profit_margin_beginning = (net_income_beginning / revenue_beginning) * 100 if revenue_beginning != 0 else float('nan')
                    net_profit_margin_end = (net_income_end / revenue_end) * 100 if revenue_end != 0 else float('nan')

                    roa_beginning = (net_income_beginning / total_assets_beginning) * 100 if total_assets_beginning != 0 else float('nan')
                    roa_end = (net_income_end / total_assets_end) * 100 if total_assets_end != 0 else float('nan')

                    roe_beginning = (net_income_beginning / total_equity_beginning) * 100 if total_equity_beginning != 0 else float('nan')
                    roe_end = (net_income_end / total_equity_end) * 100 if total_equity_end != 0 else float('nan')

# Prepare data for display
                    profitability_ratios_data = {
    "Ratio": ["Gross Profit Margin", "Net Profit Margin", "Return on Assets (ROA)", "Return on Equity (ROE)"],
    "Beginning of Year": [
        gross_profit_margin_beginning,
        net_profit_margin_beginning,
        roa_beginning,
        roe_beginning,
    ],
    "End of Year": [
        gross_profit_margin_end,
        net_profit_margin_end,
        roa_end,
        roe_end,
    ],
}

# Convert to DataFrame
                    profitability_ratios_df = pd.DataFrame(profitability_ratios_data)
                    profitability_ratios_df.set_index("Ratio", inplace=True)

                    st.subheader("💰 Profitability Ratios")
                    st.table(profitability_ratios_df)

                        
                    profitability_ratios_data = {
    "Ratio": ["Gross Profit Margin", "Net Profit Margin", "Return on Assets (ROA)", "Return on Equity (ROE)"],
    "Beginning of Year": [gross_profit_margin_beginning, net_profit_margin_beginning, roa_beginning, roe_beginning],
    "End of Year": [gross_profit_margin_end, net_profit_margin_end, roa_end, roe_end]
}
                    profitability_ratios_df = pd.DataFrame(profitability_ratios_data).set_index("Ratio")
                        
                    with st.expander("Show Graph"):                            
                        st.subheader("Profitability Ratios Comparison")
                        st.bar_chart(profitability_ratios_df)


# Calculate Altman Z-score components     
                    working_capital = ca_end - cl_end
                    A = working_capital/total_assets_end
                    B = re_end/total_assets_end
                    C = ebit_end/ total_assets_end
                    D = total_equity_end/total_liabilities_end
                    
                    z_score = (6.56*A)+(3.26*B)+(6.72*C)+(1.05*D)

                    
                    st.subheader("🟢 Altman Z-Score", divider="blue")
                    st.write(f"**Altman Z-Score**: {z_score:.2f}")
                    visualize_altman_z_score(z_score)

    
                    if z_score > 2.99:
                        st.success("🟢 Safe Zone: Low risk of bankruptcy.")
                    elif z_score >= 1.81 and z_score <= 2.99:
                        st.warning("🟡 Gray Zone: Moderate risk of bankruptcy.")
                    else:
                        st.error("🔴 Distress Zone: High risk of bankruptcy.")
                        
                        
                        
# Group your ratios into structured categories
                    ratio_groups = {
    "Profitability Ratios": {
        "Gross Profit Margin": {"beginning": gross_profit_margin_beginning, "end": gross_profit_margin_end},
        "Net Profit Margin": {"beginning": net_profit_margin_beginning, "end": net_profit_margin_end},
        "Return on Assets (ROA)": {"beginning": roa_beginning, "end": roa_end},
        "Return on Equity (ROE)": {"beginning": roe_beginning, "end": roe_end},
    },
    "Activity Ratios": {
        "Inventory Turnover": {"beginning": inventory_turnover_beginning, "end": inventory_turnover_end},
        "Days of Inventory": {"beginning": days_of_inventory_beginning, "end": days_of_inventory_end},
        "Receivables Turnover": {"beginning": receivables_turnover_beginning, "end": receivables_turnover_end},
        "Days of Sales Outstanding": {"beginning": days_of_sales_beginning, "end": days_of_sales_end},
    },
    "Solvency Ratios": {
        "Debt-to-Equity Ratio": {"beginning": debt_to_equity_beginning, "end": debt_to_equity_end},
        "Debt Ratio": {"beginning": debt_ratio_beginning, "end": debt_ratio_end},
        "Equity Ratio": {"beginning": equity_ratio_beginning, "end": equity_ratio_end},
        "Interest Coverage Ratio": {"beginning": interest_coverage_ratio_beginning, "end": interest_coverage_ratio_end},
    },
    "Altman Z-Score": {
        "Altman Z-Score": {"beginning": z_score, "end": z_score}, 
    },
}

                    
                    pdf_content = generate_pdf_report(ratio_groups)
                    show_pdf_download_button(pdf_content)


                    
                except IndexError as ie:
                    st.error(f"Data extraction error: {ie}. Please check if all required labels exist in the uploaded file.")
                except Exception as e:
                    st.error(f"An unexpected error occurred during calculations: {e}")

            else:
                st.error("The required sheets ('СБД', 'ОДТ') are not found in the uploaded file.")

        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

# Navigation logic
if st.session_state.page == "Home":
    show_home_page()
elif st.session_state.page == "Financial Analysis":
    show_analysis_page()
