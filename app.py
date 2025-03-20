import streamlit as st
import datetime
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format

# Local components and configuration imports
from modules.gral_config import page_config
from modules.data_processes import basic_trafo, load_data, today_filtering
from modules.gral_comp import title, total_metric, metric_dict, colors, \
    line_plot, line_plot_cur_vs_pre, vbarplot_top_cat
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

@st.cache_data
def load_and_transform():
    # Load and transform raw data
    df = load_data("data/import_data.csv")
    df = basic_trafo(df)
    # Ensure there are no missing dates: forward and backward fill
    df['formatted_date'] = df['formatted_date'].ffill().bfill()
    return df

df = load_and_transform()

# Date filter
date_min = df['formatted_date'].min()
date_max = df['formatted_date'].max()
selected_dates = st.sidebar.date_input("Select Date Range", [date_min, date_max])
df_filtered = df[
    (df['formatted_date'] >= pd.to_datetime(selected_dates[0])) &
    (df['formatted_date'] <= pd.to_datetime(selected_dates[1]))
]

# Numeric columns
# numeric_cols = list(df_filtered.select_dtypes(include=["number"]).columns)
numeric_cols = ['CIF_USD_EQUIVALENT','QUANTITY','GROSS.WEIGHT','TOTAL.TAXES.USD','RAISED_TAX_AMOUNT_USD']

# Office filter (if desired, can be omitted for performance)
office_options = sorted(df_filtered['OFFICE'].unique())
selected_offices = st.sidebar.multiselect("Select Office(s)", options=office_options, default=office_options)
df_filtered = df_filtered[df_filtered['OFFICE'].isin(selected_offices)]

# Reference date for time comparisons
today_ref = st.sidebar.date_input("Reference Date", datetime.date(2014, 5, 25))
df_today, df_pre_year, df_cur_year = today_filtering(df_filtered, today_ref)

### MAIN DASHBOARD TABS
tabs = st.tabs(["Dashboard", "Agg Analysis", "Illicit Findings"])

# Tab 1: Dashboard – Key Metrics and Global Trends
with tabs[0]:
    st.header("Dashboard")

    st.subheader("Key Metrics")
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

    st.subheader("Global Trends")
    period_option = st.radio("Period", options=['6M', '12M', 'CW'], horizontal=True)
    for idx, var in enumerate(['CIF_USD_EQUIVALENT', 'TOTAL.TAXES.USD']):
        if period_option == 'CW':
            line_plot_cur_vs_pre(df_cur_year, df_pre_year, var, colors, idx)
        else:
            line_plot(df_filtered, var, colors, idx, today_ref, period=period_option)

# Tab 2: Aggregated Analysis – Top N Plots and Tables
with tabs[1]:

    st.header("Aggregated Analysis")

    group_col = "OFFICE"
    st.subheader(group_col)
    col_plot, col_controls = st.columns([3, 1])

    with col_controls:
        top_n = st.slider(f"Top N {group_col}", min_value=3, max_value=20, value=5, key=f"top_n_slider_{group_col}")
        selected_num_col = st.selectbox("Numeric Variable", options=numeric_cols, key=f"num_col_{group_col}")

    with col_plot:
        vbarplot_top_cat(
            df=df_filtered,
            group_col=group_col,
            num_col=selected_num_col,
            top_n=top_n,
            title=f"Top {top_n} {group_col} by {selected_num_col}"
        )

    st.markdown("---")
    group_col = "IMPORTER.TIN"
    st.subheader(group_col)
    col_plot, col_controls = st.columns([3, 1])

    with col_controls:
        top_n = st.slider(f"Top N {group_col}", min_value=3, max_value=20, value=5, key=f"top_n_slider_{group_col}")
        selected_num_col = st.selectbox("Numeric Variable", options=numeric_cols, key=f"num_col_{group_col}")

    with col_plot:
        vbarplot_top_cat(
            df=df_filtered,
            group_col=group_col,
            num_col=selected_num_col,
            top_n=top_n,
            title=f"Top {top_n} {group_col} by {selected_num_col}"
        )

    # st.markdown("---")
    # st.subheader("Detailed Aggregated Tables")
    # st.write("**Offices Activity**")
    # offices_grouped = df_filtered.groupby("OFFICE").agg({
    #     "CIF_USD_EQUIVALENT": "sum",
    #     "QUANTITY": "sum",
    #     "GROSS.WEIGHT": "sum",
    #     "TOTAL.TAXES.USD": "sum",
    #     "RAISED_TAX_AMOUNT_USD": "sum"
    # }).reset_index()
    # st.dataframe(offices_grouped)

    # st.write("**Importer Activity**")
    # importer_grouped = df_filtered.groupby("IMPORTER.TIN").agg({
    #     "CIF_USD_EQUIVALENT": "sum",
    #     "QUANTITY": "sum",
    #     "GROSS.WEIGHT": "sum",
    #     "TOTAL.TAXES.USD": "sum",
    #     "RAISED_TAX_AMOUNT_USD": "sum"
    # }).reset_index()
    # st.dataframe(importer_grouped)

# Tab 3: Illicit Findings – Flagged Operations Analysis
with tabs[2]:
    st.header("Illicit Findings")
    illicit_df = df_filtered[df_filtered['illicit'] == True]
    if not illicit_df.empty:
        st.dataframe(illicit_df)
        st.subheader("Trend: Raised Tax Amount for Illicit Operations")
        line_plot(illicit_df, 'RAISED_TAX_AMOUNT_USD', colors, 0, today_ref, period='12M')
    else:
        st.info("No illicit findings in the selected period and filters.")
