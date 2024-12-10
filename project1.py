import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from fpdf import FPDF
import tempfile
import os
import requests
from bs4 import BeautifulSoup

# Function to visualize Altman Z-Score using a Gauge Chart
def visualize_altman_z_score(z_score, max_range=5):
    """
    Visualizes the Altman Z-Score using a Gauge Chart.
    """
    if z_score is None or not isinstance(z_score, (int, float)):
        st.error("Invalid Z-Score value. Please provide a numeric value.")
        return

    gauge_max = max(z_score + 1, max_range)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=z_score,
        title={'text': "Altman Z-Score", 'font': {'size': 24, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 40}},
        gauge={
            'axis': {'range': [0, gauge_max], 'tickfont': {'color': 'white'}},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 1.8], 'color': "#FF6666"}, 
                {'range': [1.8, 3], 'color': "#FFDD57"},  
                {'range': [3, gauge_max], 'color': "#66CC66"}  
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': z_score
            }
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="#1E1E1E",
        font=dict(color="white")
    )

    st.plotly_chart(fig)
    
def visualize_piotroski_f_score(f_score, max_score=9):
    """
    Visualizes the Piotroski F-Score using a Gauge Chart.

    Parameters:
        f_score (int): The Piotroski F-Score value (0-9).
        max_score (int): The maximum score for the gauge chart (default is 9).
    """
    # Handle invalid or None values
    if f_score is None or not isinstance(f_score, (int, float)):
        st.error("Invalid F-Score value. Please provide a numeric value.")
        return

    # Define gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=f_score,
        title={'text': "Piotroski F-Score", 'font': {'size': 24, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 40}},
        gauge={
            'axis': {'range': [0, max_score], 'tickfont': {'color': 'white'}},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 3], 'color': "#FF6666"},  # Weak
                {'range': [3, 6], 'color': "#FFDD57"},  # Moderate 
                {'range': [6, max_score], 'color': "#66CC66"}  # Strong 
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': f_score
            }
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="#1E1E1E",  
        font=dict(color="white")
    )

    st.plotly_chart(fig)

    
def calculate_piotroski_f_score(data):
    """
    Calculate the Piotroski F-Score.
    """
    f_score = 0

    # Profitability signals
    if data['net_income_end'] > 0:  # Positive Net Income
        f_score += 1
    if data['roa_end'] > data['roa_beginning']:  # Return on Assets (ROA) improvement
        f_score += 1
    if data['cash_flow'] > 0:  # Positive Operating Cash Flow
        f_score += 1
    if data['cash_flow'] > data['net_income_end']:  # Quality of Earnings
        f_score += 1

    # Leverage, liquidity, and source of funds signals
    if data['leverage'] < data['prev_leverage']:  # Decrease in Leverage (Debt to Total Assets)
        f_score += 1
    if data['current_ratio_end'] > data['current_ratio_beginning']:  # Increase in Current Ratio
        f_score += 1
    if data['shares_outstanding'] <= data['prev_shares_outstanding']:  # No new shares issued
        f_score += 1

    # Operating efficiency signals
    if data['gross_profit_margin_end'] > data['gross_profit_margin_beginning']:  
        f_score += 1
    if data['total_asset_turnover_end'] > data['total_asset_turnover_beginning']:  
        f_score += 1

    return f_score

# PDF  
def generate_pdf_report_to_file(ratio_groups):
    """
    Generates a financial ratios PDF report and saves it to a temporary file.

    Args:
        ratio_groups (dict): A dictionary where keys are section names (e.g., "Activity Ratios")
                             and values are dictionaries of ratios with beginning and end values.

    Returns:
        str: Path to the generated PDF file.
    """
    try:
        # Create a temporary file for the PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
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
                # Handle missing or NaN values gracefully
                beginning = f"{ratio_values['beginning']:.2f}" if pd.notna(ratio_values['beginning']) else "N/A"
                end = f"{ratio_values['end']:.2f}" if pd.notna(ratio_values['end']) else "N/A"
                pdf.cell(0, 10, f"{ratio_name}: Beginning = {beginning}, End = {end}", ln=True)

            pdf.ln(5)

        # Save the PDF to a file
        pdf.output(temp_file.name)
        temp_file.close()
        return temp_file.name

    except Exception as e:
        st.error(f"An error occurred while generating the PDF: {e}")
        return None
    
def show_pdf_download_button_with_file(pdf_file_path):
    """
    Displays a download button for the PDF report and removes the file after download.

    Args:
        pdf_file_path (str): Path to the generated PDF file.
    """
    if pdf_file_path:
        try:
            with open(pdf_file_path, "rb") as file:
                pdf_content = file.read()

                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_content,
                    file_name="financial_ratios_report.pdf",
                    mime="application/pdf",
                    help="Click to download the financial analysis report."
                )
        except Exception as e:
            st.error(f"An error occurred while preparing the download: {e}")
        finally:
            # Ensure the temporary file is deleted
            if os.path.exists(pdf_file_path):
                os.unlink(pdf_file_path)


# Initialize session state variables if not already present
if "page" not in st.session_state:
    st.session_state.page = "Home"  # Tracks the current page in the navigation

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None  # Stores the uploaded file

if "ratio_groups" not in st.session_state:
    st.session_state.ratio_groups = {}  # Stores ratio data for analysis

if "pdf_file_path" not in st.session_state:
    st.session_state.pdf_file_path = None  # Stores the path to the generated PDF report


# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📊 Financial Analysis", "📋 Financial Report", "📈 MSE Trade Data"])


# Navigation Logic
if page == "🏠 Home":
    st.session_state.page = "Home"

elif page == "📊 Financial Analysis":
    st.session_state.page = "Financial Analysis"
    
elif page == "📋 Financial Report":
    st.session_state.page = "Financial Report"
elif page == "📈 MSE Trade Data":
    st.session_state.page = "Trade Data"

    
def show_home_page():
    st.title("📊 Financial Analysis App")
    
    st.write("""
    The purpose of this app is to provide a quick and efficient analysis of a company's financial statements by calculating key financial ratios. These ratios help in understanding the company's profitability, activity, and solvency.
    """)
    
    with st.expander("1. **📈 Activity Ratios**"):
        st.write("""
        - **Inventory Turnover**: Indicates how many times inventory is sold and replaced over a period.
        - **Days of Inventory**: Average number of days inventory is held.
        - **Receivables Turnover**: Measures how efficiently receivables are collected.
        - **Days of Sales Outstanding**: Average collection period for receivables.
        - **Fixed Asset Turnover**: Efficiency of using fixed assets to generate revenue.
        - **Total Asset Turnover**: Overall efficiency of using assets to generate revenue.
        """)

    with st.expander("2. **💵 Liquidity Ratios**"):
        st.write("""
        - **Current Ratio**: Evaluates the company's ability to cover its current liabilities with its current assets.
        - **Quick Ratio**: Excludes inventory, providing a more conservative view of liquidity.
        - **Cash Ratio**: Focuses on the most liquid asset, cash, to determine the company’s immediate ability to pay off liabilities.
        """)

    with st.expander("3. **🔍 Solvency Ratios**"):
        st.write("""
        - **Debt-to-Equity Ratio**: Indicates the proportion of debt used relative to equity.
        - **Debt Ratio**: Percentage of assets financed by liabilities.
        - **Equity Ratio**: Percentage of assets financed by equity.
        - **Interest Coverage Ratio**: Assesses the company's ability to pay interest expenses.
        """)

    with st.expander("4. **💰 Profitability Ratios**"):
        st.write("""
        - **Gross Profit Margin**: Measures the percentage of revenue that exceeds the cost of goods sold.
        - **Net Profit Margin**: Indicates how much net income is generated as a percentage of revenue.
        - **Return on Assets (ROA)**: Shows how efficiently a company uses its assets to generate profit.
        - **Return on Equity (ROE)**: Measures the return generated on shareholders' equity.
        """)

    with st.expander("5. **🟢 Altman Z-Score**"):
        st.write("""
        The **Altman Z-Score** is a financial metric used to assess a company's likelihood of bankruptcy. It combines several financial ratios to create a single score. The score is interpreted as follows:
        - **Z-Score > 2.99**: The company is in a **safe zone**, indicating a low risk of bankruptcy.
        - **1.81 ≤ Z-Score ≤ 2.99**: The company is in the **gray zone**, indicating a moderate risk of bankruptcy.
        - **Z-Score < 1.81**: The company is in the **distress zone**, indicating a high risk of bankruptcy.
        """)
    with st.expander("6. **🟢 Piotroski F-Score**"):
        st.write("""
    The **Piotroski F-Score** is a financial metric that evaluates a company's financial health and strength. It ranges from 0 to 9, with higher scores indicating stronger financial performance. The score is interpreted as follows:
    - **7 ≤ F-Score ≤ 9**: The company is in the **strong zone**, indicating strong financial health and performance.
    - **4 ≤ F-Score ≤ 6**: The company is in the **moderate zone**, indicating moderate financial health and performance.
    - **F-Score < 4**: The company is in the **weak zone**, indicating poor financial health and performance.
    """)

        
    st.markdown("### Sample File")
    st.write("If you are unsure about the required format for financial data, you can download a sample file:")
    with open("sample_report.xls", "rb") as sample_file:
        st.download_button(
            label="📂 Download Sample File",
            data=sample_file,
            file_name="sample_report.xls",
            mime="application/vnd.ms-excel"
        )

    st.markdown("### 🚀 Ready to Get Started?")

    # Add a file uploader 
    uploaded_file = st.file_uploader("Upload your financial data now to begin your analysis (.xls or .xlsx)", type=["xls", "xlsx"])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.success("File uploaded successfully!")
        st.write("If the file is uploaded successfully, proceed to the Financial Analysis page.")
                  

# Define a function to show the Financial Analysis Page
def show_analysis_page():
    st.title("📊 Financial Analysis")
    
    # Check if a file has been uploaded and stored in session state
    if st.session_state.get("uploaded_file") is not None:
        st.success("File is available for analysis.")

        try:
            # Determine the engine based on the file extension
            if st.session_state.uploaded_file.name.endswith('.xls'):
                excel_file = pd.ExcelFile(st.session_state.uploaded_file, engine='xlrd')
            else:
                excel_file = pd.ExcelFile(st.session_state.uploaded_file, engine='openpyxl')

            # Load sheets for further calculations
            if "СБД" in excel_file.sheet_names and "ОДТ" in excel_file.sheet_names:
                balance_sheet_df = pd.read_excel(excel_file, sheet_name="СБД", skiprows=4)
                income_statement_df = pd.read_excel(excel_file, sheet_name="ОДТ", skiprows=4)
                retained_earning_df = pd.read_excel(excel_file, sheet_name="ӨӨТ", skiprows=4)
                cashflow_statement_df = pd.read_excel(excel_file, sheet_name="МГТ", skiprows=4)



# Clean up the DataFrames by dropping columns with all NaN values
                balance_sheet_df.dropna(axis=1, how='all', inplace=True)
                income_statement_df.dropna(axis=1, how='all', inplace=True)
                retained_earning_df.dropna(axis=1, how='all', inplace = True)
                cashflow_statement_df.dropna(axis=1, how='all', inplace=True)
        

                # Debug: Show first few rows of the DataFrames
                with st.expander("Show Preview of Balance Sheet"):
                    st.write("Balance Sheet Preview:", balance_sheet_df.head())
                with st.expander("Show Preview of Income Statement"):
                    st.write("Income Statement Preview:", income_statement_df.head())
                with st.expander("Show Preview of Retained Earning Statement"):
                    st.write("Retained Earning Preview:", retained_earning_df.head())
                with st.expander("Show Preview of Cashflow Statement"):
                    st.write("Cashflow Statement Preview:", cashflow_statement_df.head())
                    


                # Extracting the necessary data
                try:
                    cash_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    cash_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ar_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ar_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')
                    
                    ap_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны өглөг', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ap_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны өглөг', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')


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
                    cash_flow = pd.to_numeric(cashflow_statement_df.loc[cashflow_statement_df['Үзүүлэлт'] =='Үндсэн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн','Эцсийн үлдэгдэл'].values[0], errors = 'coerce')
                    leverage = ltl_end / total_assets_end
                    prev_leverage = ltl_beginning / total_assets_beginning
                    shares_outstanding = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == '    -хувийн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')
                    prev_shares_outstanding = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == '    -хувийн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    
                # except KeyError as e:
                #     st.error(f"KeyError: Missing expected column or data - {e}")
                # except Exception as e:
                #     st.error(f"An unexpected error occurred: {e}")
                # finally:
                #     st.info("Completed attempting to extract financial data.")

                    
               
            
# Activity Ratios (Beginning of the Year)
                    inventory_turnover_beginning = cogs_beginning / inv_beginning if inv_beginning != 0 else float('nan')
                    days_of_inventory_beginning = 365 / inventory_turnover_beginning if inventory_turnover_beginning != 0 else float('nan')
                    receivables_turnover_beginning = revenue_beginning / ar_beginning if ar_beginning != 0 else float('nan')
                    days_of_sales_beginning = 365 / receivables_turnover_beginning if receivables_turnover_beginning != 0 else float('nan')
                    payable_turnover_beginning = cogs_beginning / ap_beginning if ap_beginning != 0 else float('nan')
                    days_payables_beginning = 365 / payable_turnover_beginning if payable_turnover_beginning != 0 else float ('nan')
                    wc_turnover_beginning = revenue_beginning /(ca_beginning-cl_beginning)
                    fixed_asset_turnover_beginning = revenue_beginning / fa_beginning if fa_beginning != 0 else float('nan')
                    total_asset_turnover_beginning = revenue_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')

# Activity Ratios (End of the Year)
                    inventory_turnover_end = cogs_end / inv_end if inv_end != 0 else float('nan')
                    days_of_inventory_end = 365 / inventory_turnover_end if inventory_turnover_end != 0 else float('nan')
                    receivables_turnover_end = revenue_end / ar_end if ar_end != 0 else float('nan')
                    days_of_sales_end = 365 / receivables_turnover_end if receivables_turnover_end != 0 else float('nan')
                    payable_turnover_end = cogs_end / ap_end if ap_end != 0 else float('nan')
                    days_payables_end = 365 / payable_turnover_end if payable_turnover_end != 0 else float ('nan')
                    wc_turnover_end = revenue_end /(ca_end-cl_end)
                    fixed_asset_turnover_end = revenue_end / fa_end if fa_end != 0 else float('nan')
                    total_asset_turnover_end = revenue_end / total_assets_end if total_assets_end != 0 else float('nan')
                    
                    
                    activity_ratio_explanations = {
    "Inventory Turnover": "Measures how efficiently inventory is managed. Higher values indicate faster inventory turnover.",
    "Days of Inventory": "The average number of days inventory is held before it's sold. Lower values are generally better.",
    "Receivables Turnover": "Indicates how efficiently a company collects its accounts receivable. Higher values indicate faster collection.",
    "Days of Sales Outstanding": "The average number of days it takes to collect payment after a sale. Lower values are preferred.",
    "Payable Turnover": "Indicates how quickly a company pays off its suppliers. Higher values indicate faster payments.",
    "Number of Days Payables": "The average number of days it takes to pay suppliers. Lower values indicate faster payment cycles.",
    "Working Capital Turnover": "Measures how efficiently working capital is used to generate sales. Higher values are better.",
    "Fixed Asset Turnover": "Measures how efficiently a company uses fixed assets to generate revenue. Higher values are better.",
    "Total Asset Turnover": "Indicates how efficiently total assets are used to generate revenue. Higher values are preferred."
}

# Storing the ratios in a dictionary for easy access/display
                    activity_ratios = {
    "Inventory Turnover": {"Beginning": inventory_turnover_beginning, "End": inventory_turnover_end},
    "Days of Inventory": {"Beginning": days_of_inventory_beginning, "End": days_of_inventory_end},
    "Receivables Turnover": {"Beginning": receivables_turnover_beginning, "End": receivables_turnover_end},
    "Days of Sales Outstanding": {"Beginning": days_of_sales_beginning, "End": days_of_sales_end},
"Payable Turnover": {"Beginning": payable_turnover_beginning, "End": payable_turnover_end},
    "Number of Days Payables": {"Beginning": days_payables_beginning, "End": days_payables_end},
    "Working Capital Turnover": {"Beginning": wc_turnover_beginning, "End": wc_turnover_end},
    "Fixed Asset Turnover": {"Beginning": fixed_asset_turnover_beginning, "End": fixed_asset_turnover_end},
    "Total Asset Turnover": {"Beginning": total_asset_turnover_beginning, "End": total_asset_turnover_end},
}

# Convert the activity ratios dictionary to a DataFrame for display
                    activity_ratios_df = pd.DataFrame(activity_ratios).T
                    activity_ratios_df.columns = ["Beginning of Year", "End of Year"]
                    activity_ratios_df["Beginning of Year"] = [
    f"{value:.2f} days" if "Days" in ratio else f"{value:.2f}"
    for ratio, value in zip(activity_ratios_df.index, activity_ratios_df["Beginning of Year"])
]
                    activity_ratios_df["End of Year"] = [
    f"{value:.2f} days" if "Days" in ratio else f"{value:.2f}"
    for ratio, value in zip(activity_ratios_df.index, activity_ratios_df["End of Year"])
]
                
# Display the activity ratios in a table format
                    st.subheader("📈 Activity Ratios")
    

# Add CSS for tooltips
                    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin-left: 5px;
        color: #0d6efd; /* Custom color for the question mark */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position the tooltip above the text */
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)
    


# Create a DataFrame with tooltips embedded in the index
                    activity_ratios_with_tooltips = activity_ratios_df.copy()
                    activity_ratios_with_tooltips.index = [
    f'<div>{ratio}<span class="tooltip">❓<span class="tooltiptext">{explanation}</span></span></div>'
    
    for ratio, explanation in zip(activity_ratios_df.index, activity_ratio_explanations.values())
]

# Render the DataFrame as HTML with embedded tooltips
                    st.markdown(
    activity_ratios_with_tooltips.to_html(escape=False, index=True),
    unsafe_allow_html=True
)
                    #st.table(activity_ratios_df)

# Prepare data for visualization
                    with st.expander("Show Graph"):
                       st.subheader("Activity Ratios Comparison")
    
    # Create two columns for side-by-side charts
                       col1, col2 = st.columns(2)
                       with col1:
                           st.subheader("Beginning of Year")
        # Bar Chart for Beginning of Year
                           beginning_data = activity_ratios_df["Beginning of Year"]
                           st.bar_chart(beginning_data)

                       with col2:
                           st.subheader("End of Year")
        # Bar Chart for End of Year
                           end_data = activity_ratios_df["End of Year"]
                           st.bar_chart(end_data)


           
                    liquidity_ratio_explanations = {
    "Current Ratio": "Measures a company's ability to cover short-term liabilities with short-term assets. Higher is generally better.",
    "Quick Ratio": "Measures liquidity excluding inventory. Higher values indicate stronger short-term liquidity.",
    "Cash Ratio": "Measures liquidity based on cash and cash equivalents. A ratio above 1 is ideal."

}

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
                    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin-left: 5px;
        color: #0d6efd; /* Custom color for the question mark */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position the tooltip above the text */
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Create a DataFrame with tooltips embedded in the index
                    liquidity_ratios_with_tooltips = ratios_df.copy()
                    liquidity_ratios_with_tooltips.index = [
    f'<div>{ratio}<span class="tooltip">❓<span class="tooltiptext">{explanation}</span></span></div>'
    
    for ratio, explanation in zip(ratios_df.index, liquidity_ratio_explanations.values())
]

                    st.markdown(
    liquidity_ratios_with_tooltips.to_html(escape=False, index=True),
    unsafe_allow_html=True
)  


# Prepare data for bar chart visualization
                    with st.expander("Show Graph"):
                        st.subheader("Liquidity Ratios Comparison") 
            
            
                        col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Beginning of year")  
                        beginning_data = ratios_df["Beginning of Year"]
                        st.bar_chart(beginning_data) 
                    with col2:
                        st.subheader("End of Year")
                        end_data = ratios_df["End of Year"]
                        st.bar_chart(end_data)
#Solvency ratio

                        solvency_ratio_explanations = {
    "Debt to Equity": "Measures financial leverage. Lower values indicate less reliance on debt.",
    "Debt Ratio": "Shows the proportion of total assets financed by debt. Lower is typically better.",
    "Equity Ratio": "Indicates the proportion of assets financed by equity. Higher values are better.",
    "Interest Coverage": "Measures a company's ability to pay interest on debt. Higher is better."
}

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
                    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin-left: 5px;
        color: #0d6efd; /* Custom color for the question mark */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position the tooltip above the text */
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Create a DataFrame with tooltips embedded in the index
                    solvency_ratios_with_tooltips = solvency_ratios_df.copy()
                    solvency_ratios_with_tooltips.index = [
    f'<div>{ratio}<span class="tooltip">❓<span class="tooltiptext">{explanation}</span></span></div>'
    
    for ratio, explanation in zip(solvency_ratios_df.index, solvency_ratio_explanations.values())
]

# Render the DataFrame as HTML with embedded tooltips
                    st.markdown(
    solvency_ratios_with_tooltips.to_html(escape=False, index=True),
    unsafe_allow_html=True
)
                    #st.table(solvency_ratios_df)

                    if debt_to_equity_end > 2:
                        st.warning("The Debt-to-Equity Ratio at the end of the year is above 2.0, indicating high leverage.")
                        
 
                    with st.expander("Show Graph"):
                        st.subheader("Solvency Ratios Comparison")
                        
                        col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Beginning of year")  
                        beginning_data = solvency_ratios_df["Beginning of Year"]
                        st.bar_chart(beginning_data) 
                    with col2:
                        st.subheader("End of Year")
                        end_data = solvency_ratios_df["End of Year"]
                        st.bar_chart(end_data)

    
                        profitability_ratio_explanations = {
    "Gross Profit Margin": "Indicates the proportion of revenue remaining after covering direct costs. Higher values indicate better profitability.",
    "Net Profit Margin": "Shows the proportion of revenue remaining after all expenses. Higher is better.",
    "Return on Assets (ROA)": "Measures how efficiently a company generates profit from its assets. Higher is better.",
    "Return on Equity (ROE)": "Measures how efficiently a company generates profit from shareholder equity. Higher values are preferred."
}
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
                    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin-left: 5px;
        color: #0d6efd; /* Custom color for the question mark */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position the tooltip above the text */
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Create a DataFrame with tooltips embedded in the index
                    profitability_ratios_with_tooltips = profitability_ratios_df.copy()
                    profitability_ratios_with_tooltips.index = [
    f'<div>{ratio}<span class="tooltip">❓<span class="tooltiptext">{explanation}</span></span></div>'
    
    for ratio, explanation in zip(profitability_ratios_df.index, profitability_ratio_explanations.values())
]

# Render the DataFrame as HTML with embedded tooltips
                    st.markdown(
    profitability_ratios_with_tooltips.to_html(escape=False, index=True),
    unsafe_allow_html=True
)
                   
                        
                    with st.expander("Show Graph"):                            
                        st.subheader("Profitability Ratios Comparison")

                        col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Beginning of year")  
                        beginning_data = profitability_ratios_df["Beginning of Year"]
                        st.bar_chart(beginning_data) 
                    with col2:
                        st.subheader("End of Year")
                        end_data = profitability_ratios_df["End of Year"]
                        st.bar_chart(end_data)


                    piotroski_data = {
    "net_income_end": net_income_end,  # Current Net Income
    "roa_end": roa_end,  # Current Return on Assets
    "roa_beginning": roa_beginning,  # Previous Return on Assets
    "cash_flow": cash_flow,  # Current Operating Cash Flow
    "leverage": leverage,  # Current Leverage
    "prev_leverage": prev_leverage,  # Previous Leverage
    "current_ratio_end": current_ratio_end,  # Current Current Ratio
    "current_ratio_beginning": current_ratio_beginning,  # Previous Current Ratio
    "shares_outstanding": shares_outstanding,  # Current Shares Outstanding
    "prev_shares_outstanding": prev_shares_outstanding,  # Previous Shares Outstanding
    "gross_profit_margin_end": gross_profit_margin_end,  # Current Gross Margin
    "gross_profit_margin_beginning": gross_profit_margin_beginning,  # Previous Gross Margin
    "total_asset_turnover_end": total_asset_turnover_end,  # Current Asset Turnover
    "total_asset_turnover_beginning": total_asset_turnover_beginning  # Previous Asset Turnover
}
                    piotroski_f_score = calculate_piotroski_f_score(piotroski_data)

# Display Altman Z-Score and Piotroski F-Score
                    working_capital = ca_end - cl_end
                    A = working_capital / total_assets_end
                    B = re_end / total_assets_end
                    C = ebit_end / total_assets_end
                    D = total_equity_end / total_liabilities_end
                    z_score = (6.56 * A) + (3.26 * B) + (6.72 * C) + (1.05 * D)
                    col1, col2 = st.columns([1,1])
                    with col1:
                        st.subheader("🟢 Altman Z-Score")
                        st.write("The Altman Z-Score is a formula used to predict likelihood of bankruptcy of publicly traded company. Higher scores indicate lower risk.")
                        st.write(f"**Altman Z-Score**: {z_score:.2f}")
                        visualize_altman_z_score(z_score)
                        if z_score > 2.99:
                            st.success("🟢 Safe Zone: Low risk of bankruptcy.")
                        elif 1.81 <= z_score <= 2.99:
                            st.warning("🟡 Gray Zone: Moderate risk of bankruptcy.")
                        else:
                            st.error("🔴 Distress Zone: High risk of bankruptcy.")


                       
                                                
                    with col2:
                        st.subheader("🟢 Piotroski F-Score")
                        st.write("The Piotroski F-Score is a measure of a company's financial strength, ranging from 0 to 9. Higher scores indicate stronger financial performance.")
                        st.write(f"**Piotroski F-Score**: {piotroski_f_score} / 9")
                        visualize_piotroski_f_score(piotroski_f_score)

                        if piotroski_f_score >= 7:
                            st.success("🟢 Strong financial strength.")
                        elif 4 <= piotroski_f_score <= 6:
                            st.warning("🟡 Moderate financial strength.")
                        else:
                            st.error("🔴 Weak financial strength.")
                  
                        
                        
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
    "Piotroski F-Score": {
        "Piotroski F-Score": {"beginning": piotroski_f_score, "end": piotroski_f_score},
    },
        
}
                    
                    
                    pdf_file_path = generate_pdf_report_to_file(ratio_groups)
                    show_pdf_download_button_with_file(pdf_file_path)
                    
                except IndexError as ie:
                    st.error(f"Data extraction error: {ie}. Please check if all required labels exist in the uploaded file.")
                except Exception as e:
                    st.error(f"An unexpected error occurred during calculations: {e}")

            else:
                st.error("The required sheets ('СБД', 'ОДТ') are not found in the uploaded file.")

        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")


#Report Page
def show_report_page():
    st.title("Financial Report")
    
     # Check if a file has been uploaded and stored in session state
    if st.session_state.get("uploaded_file") is not None:
        try:
            # Determine the engine based on the file extension
            if st.session_state.uploaded_file.name.endswith('.xls'):
                excel_file = pd.ExcelFile(st.session_state.uploaded_file, engine='xlrd')
            else:
                excel_file = pd.ExcelFile(st.session_state.uploaded_file, engine='openpyxl')

            # Load sheets for further calculations
            if "СБД" in excel_file.sheet_names and "ОДТ" in excel_file.sheet_names:
                balance_sheet_df = pd.read_excel(excel_file, sheet_name="СБД", skiprows=4)
                income_statement_df = pd.read_excel(excel_file, sheet_name="ОДТ", skiprows=4)
                retained_earning_df = pd.read_excel(excel_file, sheet_name="ӨӨТ", skiprows=4)
                cashflow_statement_df = pd.read_excel(excel_file, sheet_name="МГТ", skiprows=4)



# Clean up the DataFrames by dropping columns with all NaN values
                balance_sheet_df.dropna(axis=1, how='all', inplace=True)
                income_statement_df.dropna(axis=1, how='all', inplace=True)
                retained_earning_df.dropna(axis=1, how='all', inplace = True)
                cashflow_statement_df.dropna(axis=1, how='all', inplace=True)
        
    
            try:
                    cash_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    cash_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Мөнгө,түүнтэй адилтгах хөрөнгө', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')

                    ar_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ar_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны авлага', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')
                    
                    ap_beginning = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны өглөг', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    ap_end = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == 'Дансны өглөг', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')


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
                    cash_flow = pd.to_numeric(cashflow_statement_df.loc[cashflow_statement_df['Үзүүлэлт'] =='Үндсэн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн','Эцсийн үлдэгдэл'].values[0], errors = 'coerce')
                    leverage = ltl_end / total_assets_end
                    prev_leverage = ltl_beginning / total_assets_beginning
                    shares_outstanding = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == '    -хувийн', 'Эцсийн үлдэгдэл'].values[0], errors='coerce')
                    prev_shares_outstanding = pd.to_numeric(balance_sheet_df.loc[balance_sheet_df['Үзүүлэлт'] == '    -хувийн', 'Эхний үлдэгдэл'].values[0], errors='coerce')
                    
            except KeyError as e:
                    st.error(f"Data missing in uploaded file: {e}")
                    return
            except IndexError as e:
                    st.error(f"Data index error: {e}")
                    return
                
                
            inventory_turnover_beginning = cogs_beginning / inv_beginning if inv_beginning != 0 else float('nan')
            days_of_inventory_beginning = 365 / inventory_turnover_beginning if inventory_turnover_beginning != 0 else float('nan')
            receivables_turnover_beginning = revenue_beginning / ar_beginning if ar_beginning != 0 else float('nan')
            days_of_sales_beginning = 365 / receivables_turnover_beginning if receivables_turnover_beginning != 0 else float('nan')
            payable_turnover_beginning = cogs_beginning / ap_beginning if ap_beginning != 0 else float('nan')
            days_payables_beginning = 365 / payable_turnover_beginning if payable_turnover_beginning != 0 else float ('nan')
            wc_turnover_beginning = revenue_beginning /(ca_beginning-cl_beginning)
            fixed_asset_turnover_beginning = revenue_beginning / fa_beginning if fa_beginning != 0 else float('nan')
            total_asset_turnover_beginning = revenue_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')

# Activity Ratios (End of the Year)
            inventory_turnover_end = cogs_end / inv_end if inv_end != 0 else float('nan')
            days_of_inventory_end = 365 / inventory_turnover_end if inventory_turnover_end != 0 else float('nan')
            receivables_turnover_end = revenue_end / ar_end if ar_end != 0 else float('nan')
            days_of_sales_end = 365 / receivables_turnover_end if receivables_turnover_end != 0 else float('nan')
            payable_turnover_end = cogs_end / ap_end if ap_end != 0 else float('nan')
            days_payables_end = 365 / payable_turnover_end if payable_turnover_end != 0 else float ('nan')
            wc_turnover_end = revenue_end /(ca_end-cl_end)
            fixed_asset_turnover_end = revenue_end / fa_end if fa_end != 0 else float('nan')
            total_asset_turnover_end = revenue_end / total_assets_end if total_assets_end != 0 else float('nan')

#Liquidity Ratios
            current_ratio_beginning = ca_beginning / cl_beginning if cl_beginning != 0 else float('nan')
            current_ratio_end = ca_end / cl_end if cl_end != 0 else float('nan')

            quick_ratio_beginning = (cash_beginning + sts_beginning + ar_beginning) / cl_beginning if cl_beginning != 0 else float('nan')
            quick_ratio_end = (cash_end + sts_end + ar_end) / cl_end if cl_end != 0 else float('nan')

            cash_ratio_beginning = (cash_beginning + sts_beginning) / cl_beginning if cl_beginning != 0 else float('nan')
            cash_ratio_end = (cash_end + sts_end) / cl_end if cl_end != 0 else float('nan')
                
# Solvency Ratios (Beginning of Year and End of Year)
            debt_to_equity_beginning = total_liabilities_beginning / total_equity_beginning if total_equity_beginning != 0 else float('nan')
            debt_to_equity_end = total_liabilities_end / total_equity_end if total_equity_end != 0 else float('nan')

            debt_ratio_beginning = total_liabilities_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')
            debt_ratio_end = total_liabilities_end / total_assets_end if total_assets_end != 0 else float('nan')

            equity_ratio_beginning = total_equity_beginning / total_assets_beginning if total_assets_beginning != 0 else float('nan')
            equity_ratio_end = total_equity_end / total_assets_end if total_assets_end != 0 else float('nan')

            interest_coverage_ratio_beginning = net_income_beginning / interest_expense_beginning if interest_expense_beginning != 0 else float('nan')
            interest_coverage_ratio_end = net_income_end / interest_expense_end if interest_expense_end != 0 else float('nan')
                
                
# Profitability Ratios (Beginning of Year and End of Year)
            gross_profit_margin_beginning = (gross_profit_beginning / revenue_beginning) * 100 if revenue_beginning != 0 else float('nan')
            gross_profit_margin_end = (gross_profit_end / revenue_end) * 100 if revenue_end != 0 else float('nan')

            net_profit_margin_beginning = (net_income_beginning / revenue_beginning) * 100 if revenue_beginning != 0 else float('nan')
            net_profit_margin_end = (net_income_end / revenue_end) * 100 if revenue_end != 0 else float('nan')

            roa_beginning = (net_income_beginning / total_assets_beginning) * 100 if total_assets_beginning != 0 else float('nan')
            roa_end = (net_income_end / total_assets_end) * 100 if total_assets_end != 0 else float('nan')

            roe_beginning = (net_income_beginning / total_equity_beginning) * 100 if total_equity_beginning != 0 else float('nan')
            roe_end = (net_income_end / total_equity_end) * 100 if total_equity_end != 0 else float('nan')
                
                
# Altman Z-Score calculation
            working_capital = ca_end - cl_end
            A = working_capital / total_assets_end if total_assets_end != 0 else float('nan')
            B = re_end / total_assets_end if total_assets_end != 0 else float('nan')
            C = ebit_end / total_assets_end if total_assets_end != 0 else float('nan')
            D = total_equity_end / total_liabilities_end if total_liabilities_end != 0 else float('nan')
            z_score = (6.56 * A) + (3.26 * B) + (6.72 * C) + (1.05 * D)

            # Interpret the Altman Z-Score
            if z_score > 2.99:
                z_score_comment = "Safe Zone: The company is at low risk of bankruptcy."
            elif 1.81 <= z_score <= 2.99:
                z_score_comment = "Gray Zone: The company has a moderate risk of bankruptcy."
            else:
                z_score_comment = "Distress Zone: The company has a high risk of bankruptcy."
                    
                    
            f_score_components = {
                "Net Income Positive": net_income_end > 0,
                "ROA Positive": roa_end > 0,
                "Improved ROA": roa_end > roa_beginning,
                "Operating Cash Flow Positive": cash_flow > 0,
                "Cash Flow > Net Income": cash_flow > net_income_end,
                "Lower Leverage": leverage < prev_leverage,
                "Improved Current Ratio": current_ratio_end > current_ratio_beginning,
                "No Dilution of Shares": shares_outstanding <= prev_shares_outstanding,
                "Improved Gross Margin": gross_profit_margin_end > gross_profit_margin_beginning,
                "Improved Asset Turnover": total_asset_turnover_end > total_asset_turnover_beginning,
            }

            piotroski_f_score = sum(f_score_components.values())

            # Interpret the Piotroski F-Score
            if piotroski_f_score >= 7:
                f_score_comment = "Strong: The company demonstrates excellent financial health."
            elif 4 <= piotroski_f_score <= 6:
                f_score_comment = "Moderate: The company shows average financial health."
            else:
                f_score_comment = "Weak: The company has poor financial health."


                   
           
    # Generate comments for inventory turnover
            
            inventory_turnover_comment = (
    "Higher inventory turnover indicates that products are selling faster."
    if inventory_turnover_end > inventory_turnover_beginning
    else "Lower inventory turnover indicates that products are taking longer to sell, potentially leading to higher storage costs or slow-moving inventory."
)

# Generate comments for receivables turnover
            receivables_turnover_comment = (
    "Higher receivables turnover indicates efficient collection of receivables."
    if receivables_turnover_end > receivables_turnover_beginning
    else "Lower receivables turnover indicates slower collection, which could impact cash flow."
)

# Generate comments for payables turnover
            payables_turnover_comment = (
    "Higher payables turnover indicates faster payment to suppliers."
    if payable_turnover_end > payable_turnover_beginning
    else "Lower payables turnover indicates slower payment to suppliers, which might help conserve cash."
)

# Generate comments for working capital turnover
            wc_turnover_comment = (
    "Higher working capital turnover indicates efficient use of working capital to generate revenue."
    if wc_turnover_end > wc_turnover_beginning
    else "Lower working capital turnover indicates less efficient use of working capital."
)

# Generate comments for fixed asset turnover
            fixed_asset_turnover_comment = (
    "Higher fixed asset turnover indicates better utilization of fixed assets to generate revenue."
    if fixed_asset_turnover_end > fixed_asset_turnover_beginning
    else "Lower fixed asset turnover indicates underutilization of fixed assets."
)

# Generate comments for total asset turnover
            total_asset_turnover_comment = (
    "Higher total asset turnover indicates efficient use of total assets to generate revenue."
    if total_asset_turnover_end > total_asset_turnover_beginning
    else "Lower total asset turnover indicates less efficient use of total assets."
)
            current_ratio_comment = (
                "The current ratio has improved, indicating better ability to meet short-term obligations."
    if current_ratio_end > current_ratio_beginning
    else "The current ratio has declined, indicating potential difficulty in meeting short-term obligations."
            )
            quick_ratio_comment = (
                "The quick ratio has improved, indicating better liquidity without relying on inventory."
    if quick_ratio_end > quick_ratio_beginning
    else "The quick ratio has declined, indicating reduced liquidity without considering inventory."
            )
            cash_ratio_comment = (
                "The cash ratio has improved, indicating better liquidity using only cash and cash equivalents."
    if cash_ratio_end > cash_ratio_beginning
    else "The cash ratio has declined, indicating reduced liquidity using only cash and cash equivalents."
            )
            debt_to_equity_comment = (
                "The debt-to-equity ratio has improved, indicating reduced reliance on debt financing."
    if debt_to_equity_end < debt_to_equity_beginning
    else "The debt-to-equity ratio has increased, indicating higher reliance on debt financing."
            )
            debt_ratio_comment = (
                "The debt ratio has decreased, indicating a lower proportion of assets financed by debt."
    if debt_ratio_end < debt_ratio_beginning
    else "The debt ratio has increased, indicating a higher proportion of assets financed by debt."
            )
            equity_ratio_comment = (
                "The equity ratio has improved, indicating a higher proportion of assets financed by equity."
    if equity_ratio_end > equity_ratio_beginning
    else "The equity ratio has declined, indicating a lower proportion of assets financed by equity."
            )
            interest_coverage_comment = (
                "The interest coverage ratio has improved, indicating better ability to meet interest obligations."
    if interest_coverage_ratio_end > interest_coverage_ratio_beginning
    else "The interest coverage ratio has declined, indicating reduced ability to meet interest obligations."
            )
            gross_profit_margin_comment = (
                "The gross profit margin has improved, indicating better profitability from core operations."
    if gross_profit_margin_end > gross_profit_margin_beginning
    else "The gross profit margin has declined, indicating lower profitability from core operations."
            )
            net_profit_margin_comment = (
                "The net profit margin has improved, indicating better overall profitability."
    if net_profit_margin_end > net_profit_margin_beginning
    else "The net profit margin has declined, indicating reduced overall profitability."
            )
            roa_comment = (
                "Return on Assets (ROA) has improved, indicating better efficiency in using assets to generate profit."
    if roa_end > roa_beginning
    else "Return on Assets (ROA) has declined, indicating reduced efficiency in using assets to generate profit."
            )
            roe_comment = (
                "Return on Equity (ROE) has improved, indicating better returns for shareholders."
    if roe_end > roe_beginning
    else "Return on Equity (ROE) has declined, indicating reduced returns for shareholders."
            )
                
        except Exception as e:
                     st.error(f"An error occurred while processing the report: {e}")
                


# Display Activity Ratios Insights on Financial Report Page
        st.subheader("Activity Ratios")
        st.write(f"**Inventory Turnover:** {inventory_turnover_comment}")
        st.write(f"**Receivables Turnover:** {receivables_turnover_comment}")
        st.write(f"**Payables Turnover:** {payables_turnover_comment}")
        st.write(f"**Working Capital Turnover:** {wc_turnover_comment}")
        st.write(f"**Fixed Asset Turnover:** {fixed_asset_turnover_comment}")
        st.write(f"**Total Asset Turnover:** {total_asset_turnover_comment}")
            
        st.subheader("Liquidity Ratios")
        st.write(f"**Current Ratio:** {current_ratio_comment}")
        st.write(f"**Quick Ratio:** {quick_ratio_comment}")
        st.write(f"**Cash Ratio:** {cash_ratio_comment}")
            
        st.subheader("Solvency Ratios")
        st.write(f"**Debt-to-Equity Ratio:** {debt_to_equity_comment}")
        st.write(f"**Debt Ratio:** {debt_ratio_comment}")
        st.write(f"**Equity Ratio:** {equity_ratio_comment}")
        st.write(f"**Interest Coverage Ratio:** {interest_coverage_comment}")
            
        st.subheader("Profitability Ratios")
        st.write(f"**Gross Profit Margin:** {gross_profit_margin_comment}")
        st.write(f"**Net Profit Margin:** {net_profit_margin_comment}")
        st.write(f"**Return on Assets (ROA):** {roa_comment}")
        st.write(f"**Return on Equity (ROE):** {roe_comment}")
            
        st.subheader("Altman Z-Score")
        st.write(f"{z_score_comment}")
            
        st.subheader("Piotroski F-Score")
        st.write(f"{f_score_comment}")
        
def get_companies_and_urls():
    base_url = "https://mse.mn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the dropdown for companies
    dropdown = soup.find("select", class_="selectpicker")
    companies = {}
    if dropdown:
        options = dropdown.find_all("option")
        for option in options:
            company_name = option.text.strip()
            company_id = option.get("value")
            # Skip invalid or empty values
            if company_id and company_id.isdigit() and int(company_id) > 0:
                company_url = f"{base_url}/mn/company/{company_id}"  # Build full URL
                companies[company_name] = company_url
    return companies



# def get_company_info(company_url):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#     }
#     response = requests.get(company_url, headers=headers)
#     response.raise_for_status()
#     soup = BeautifulSoup(response.text, "html.parser")
#     #Parse company-specific details
#     details_container = soup.find("div", class_="col-lg-6 col-md-6")
#     data = {}
#     if details_container:
#         list_items = details_container.find_all("li")
#         for item in list_items:
#             key = item.contents[0].strip()
#             value_tag = item.find("b")
#             value = value_tag.text.strip() if value_tag else "N/A"
#             data[key] = value
#     else:
#         data["Error"] = "No data found in the specified container."
#     return data

# def show_trade_page():
#     st.title("MSE Company Trade Data")

#     # Get companies
#     with st.spinner("Fetching company list..."):
#         companies = get_companies_and_urls()

#     # Dropdown menu
#     selected_company = st.selectbox("Select a company", list(companies.keys()))

#     if selected_company:
#         # Fetch and display company info
#         company_url = companies[selected_company]
#         with st.spinner(f"Loading data for {selected_company}..."):
#             company_info = get_company_info(company_url)

#         st.subheader(f"Details for {selected_company}")
#         if company_info:
#             for key, value in company_info.items():
#                 st.write(f"**{key}:** {value}")
#         else:
#             st.warning("No data found for the selected company.")


        
                     
# Navigation logic
if st.session_state.page == "Home":
    show_home_page()
elif st.session_state.page == "Financial Analysis":
    show_analysis_page()
elif st.session_state.page == "Financial Report":
    show_report_page()
# elif st.session_state.page == "Trade Data":
#     show_trade_page()
        
