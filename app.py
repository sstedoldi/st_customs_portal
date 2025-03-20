import streamlit as st
import datetime
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format

# Local components and configuration imports
from modules.gral_config import page_config
from modules.data_processes import basic_trafo, load_data, today_filtering
from modules.gral_comp import title, total_metric, metric_dict, colors, line_plot, line_plot_cur_vs_pre
from styles.basics import hide, lg_color, cont_padding

### CONFIGURATION
st.set_page_config(**page_config)

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True)
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True)
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

### HEADER
img = "images/DALLE-customs-portal_cut.jpg"
st.image(img, use_container_width=True)
title()

### SIDEBAR FILTERS
st.sidebar.header("Filters")

# Load and transform raw data
df = load_data("data/import_data.csv")
df = basic_trafo(df)

# Create a proper datetime column if not already present (assuming year,month,day exist)
if 'date' not in df.columns:
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']], errors='coerce')

# Date range filter based on the dataset dates
date_min = df['date'].min().date()
date_max = df['date'].max().date()
selected_dates = st.sidebar.date_input("Select Date Range", [date_min, date_max])

# Filter by Office
office_options = sorted(df['OFFICE'].unique())
selected_offices = st.sidebar.multiselect("Select Office(s)", options=office_options, default=office_options)

# Filter by Importer TIN
importer_options = sorted(df['IMPORTER.TIN'].unique())
selected_importers = st.sidebar.multiselect("Select Importer(s)", options=importer_options, default=importer_options)

# Filter by Tariff Code
tariff_options = sorted(df['TARIFF.CODE'].unique())
selected_tariffs = st.sidebar.multiselect("Select Tariff Code(s)", options=tariff_options, default=tariff_options)

# Filter by Origin Code
origin_options = sorted(df['ORIGIN.CODE'].unique())
selected_origins = st.sidebar.multiselect("Select Origin Code(s)", options=origin_options, default=origin_options)

# Apply sidebar filters to the data
filtered_df = df[
    (df['date'] >= pd.to_datetime(selected_dates[0])) &
    (df['date'] <= pd.to_datetime(selected_dates[1])) &
    (df['OFFICE'].isin(selected_offices)) &
    (df['IMPORTER.TIN'].isin(selected_importers)) &
    (df['TARIFF.CODE'].isin(selected_tariffs)) &
    (df['ORIGIN.CODE'].isin(selected_origins))
]

# Optional: Choose a reference date for time-based comparisons
today = st.sidebar.date_input("Reference Date", datetime.date(2014, 5, 25))
df_today, df_pre_year, df_cur_year = today_filtering(filtered_df, today)

### MAIN DASHBOARD TABS
tabs = st.tabs([
    "Commercial & Operational Info",
    "Revenue Insights",
    "Offices Activity",
    "HS Codes Trends",
    "Importer Activity",
    "Illicit Findings"
])

# Tab 1: Commercial & Operational Information
with tabs[0]:
    st.header("Commercial & Operational Information")
    
    # Metrics (totals)
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]
    count = 0
    for metric in metric_dict:
        with columns[count]:
            total_metric(df_pre_year, df_cur_year,
                         metric_dict[metric]['col'],
                         metric,
                         metric_dict[metric]['scale'],
                         metric_dict[metric]['unit'])
        count += 1
        if count >= 3:
            count = 0

    st.markdown("---")
    
    # Global trends: option to choose different periods
    col1, col2 = st.columns(2)
    with col1:
        st.header("Global Trends")
    with col2:
        period_option = st.radio("Period",
                                 options=['6 months', '12 months', 'vs. previews year'],
                                 horizontal=True)
    
    # Main trends plots for CIF and TOTAL.TAXES.USD
    for idx, var in enumerate(['CIF_USD_EQUIVALENT', 'TOTAL.TAXES.USD']):
        if period_option == 'vs. previews year':
            line_plot_cur_vs_pre(df_cur_year, df_pre_year, var, colors, idx)
        else:
            line_plot(filtered_df, var, colors, idx, today, period=period_option)
    
    st.markdown("---")
    
    # Other trends: illicit findings, raised tax amount, quantity, and gross weight
    trend_vars = ['illicit', 'RAISED_TAX_AMOUNT_USD', 'QUANTITY', 'GROSS.WEIGHT']
    col1, col2 = st.columns(2)
    columns = [col1, col2]
    count = 0
    for idx, var in enumerate(trend_vars, start=2):
        with columns[count]:
            if period_option == 'vs. previews year':
                line_plot_cur_vs_pre(df_cur_year, df_pre_year, var, colors, idx)
            else:
                line_plot(filtered_df, var, colors, idx, today, period=period_option)
        count += 1
        if count >= 2:
            count = 0

# Tab 2: Revenue Insights
with tabs[1]:
    st.header("Revenue Insights")
    st.subheader("Revenue Trends Over Time")
    revenue_vars = ['TOTAL.TAXES.USD', 'RAISED_TAX_AMOUNT_USD']
    for idx, var in enumerate(revenue_vars):
        line_plot(filtered_df, var, colors, idx, today, period='12 months')

# Tab 3: Offices Activity
with tabs[2]:
    st.header("Offices Activity")
    # Aggregate metrics by OFFICE
    offices_grouped = filtered_df.groupby("OFFICE").agg({
        "CIF_USD_EQUIVALENT": "sum",
        "QUANTITY": "sum",
        "GROSS.WEIGHT": "sum",
        "TOTAL.TAXES.USD": "sum",
        "RAISED_TAX_AMOUNT_USD": "sum"
    }).reset_index()
    st.dataframe(offices_grouped)

# Tab 4: HS Codes Trends (using Tariff Codes)
with tabs[3]:
    st.header("HS Codes Trends")
    hs_grouped = filtered_df.groupby("TARIFF.CODE").agg({
        "CIF_USD_EQUIVALENT": "sum",
        "QUANTITY": "sum",
        "GROSS.WEIGHT": "sum",
        "TOTAL.TAXES.USD": "sum",
        "RAISED_TAX_AMOUNT_USD": "sum"
    }).reset_index()
    st.dataframe(hs_grouped)

# Tab 5: Importer Activity
with tabs[4]:
    st.header("Importer Activity")
    importer_grouped = filtered_df.groupby("IMPORTER.TIN").agg({
        "CIF_USD_EQUIVALENT": "sum",
        "QUANTITY": "sum",
        "GROSS.WEIGHT": "sum",
        "TOTAL.TAXES.USD": "sum",
        "RAISED_TAX_AMOUNT_USD": "sum"
    }).reset_index()
    st.dataframe(importer_grouped)

# Tab 6: Illicit Findings
with tabs[5]:
    st.header("Illicit Findings")
    # Assuming the illicit column flags non-compliant operations (e.g., True/False)
    illicit_df = filtered_df[filtered_df['illicit'] == True]
    if not illicit_df.empty:
        st.dataframe(illicit_df)
        st.subheader("Trend of Raised Tax Amount for Illicit Operations")
        line_plot(illicit_df, 'RAISED_TAX_AMOUNT_USD', colors, 0, today, period='12 months')
    else:
        st.info("No illicit findings in the selected period and filters.")
