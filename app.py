import streamlit as st
import datetime
# processing
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
# ploting
# local compenents
from modules.gral_config import page_config
from modules.data_processes import basic_trafo, load_data, today_filtering
from modules.gral_comp import title, total_metric, metric_dict
from modules.gral_comp import colors, line_plot, line_plot_cur_vs_pre
# local styles
from styles.basics import hide, lg_color, cont_padding

### CONFIG
st.set_page_config(**page_config)

### SESSION

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # superior line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

### HEADER
img = "https://clikc.wcoomd.org/pluginfile.php/1/totara_core/loginimage/21999/Banner.png"
st.image(img, use_column_width=True)
title()

### INPUTS
today = st.date_input("TODAY", 
                      datetime.date(2014, 5, 25),
                      min_value = datetime.date(2014, 1, 1),
                      max_value = datetime.date(2014, 12, 31))

st.markdown("""---""")

## raw data
df = load_data("data/import_data.csv")

## transformations
df = basic_trafo(df)

## today filtering
df_today, df_pre_year, df_cur_year = today_filtering(df, today)

### CONTENT

## totals
st.header("Metrics")
col1, col2, col3 = st.columns(3)

columns = [col1, col2, col3]

count = 0
for metric in metric_dict:
    with columns[count]:
        total_metric(df_pre_year, 
                    df_cur_year,
                    metric_dict[metric]['col'], 
                    metric, 
                    metric_dict[metric]['scale'], 
                    metric_dict[metric]['unit'])
        count += 1
        if count >= 3:
            count =0

st.markdown("""---""")

## global trends
col1, col2 = st.columns([0.5,0.5])
with col1:
    st.header("Global trends")
with col2:
    radio_btn = st.radio("Period",
                        options=['6 months', '12 months', 'vs. previews year'],
                        horizontal=True)
# main trends

vars = ['CIF_USD_EQUIVALENT', 'TOTAL.TAXES.USD']
for id, var in enumerate(vars):
    if radio_btn == 'vs. previews year':
        line_plot_cur_vs_pre(df_cur_year, df_pre_year, var, colors, id)
    else:
        line_plot(df, var, colors, id, today, period=radio_btn)

# other trends

vars = ['illicit','RAISED_TAX_AMOUNT_USD','QUANTITY','GROSS.WEIGHT']

col1, col2 = st.columns([0.5,0.5])

columns = [col1, col2]

count = 0
for id, var in enumerate(vars, start=2):
    with columns[count]:
        if radio_btn == 'vs. previews year':
            line_plot_cur_vs_pre(df_cur_year, df_pre_year, var, colors, id)
        else:
            line_plot(df, var, colors, id, today, period=radio_btn)

        count += 1
        if count >= 2:
            count =0