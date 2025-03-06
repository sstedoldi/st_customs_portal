import streamlit as st
import datetime
# processing
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
# ploting
# import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# local compenents
from modules.gral_config import page_config
from modules.local_prepo import basic_trafo, load_raw_data
from modules.gral_comp import title, total_metric, metric_dict
# local styles
from styles.basics import hide, lg_color

### CONFIG
st.set_page_config(**page_config)

### SESSION
#

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton

### DATA

# ## reading raw data
# @st.cache_data
# def load_raw_data(raw_data_path):
#     print("loading raw data")
#     dtypes_dict = {
#     'TARIFF.CODE':str,
#     'CIF_USD_EQUIVALENT': float,
#     'QUANTITY': float,
#     'GROSS.WEIGHT': float,
#     'TOTAL.TAXES.USD': float,
#     'RAISED_TAX_AMOUNT_USD':float,
#     'illicit':bool
#     }
#     df = pd.read_csv(raw_data_path, sep=",", dtype=dtypes_dict)
#     return df

# ## basic transformations
# @st.cache_data
# def basic_trafo(df):
#     print("basic transformations")
#     # HS codes
#     df['HS02']=df['TARIFF.CODE'].str[0:2] #HS chapter
#     df['HS04']=df['TARIFF.CODE'].str[0:4] #HS Header
#     df['HS06']=df['TARIFF.CODE'].str[0:6] #HS Subheader
#     # Dates
#     df['formatted_date'] = pd.to_datetime(df[['year', 'month', 'day']], errors='coerce')
#     df['formatted_date'] = df['formatted_date'].ffill()#fillna(method='ffill') 
#     # df['week'] = df['formatted_date'].dt.week
#     df['day_of_week'] = df['formatted_date'].dt.dayofweek
#     df['formatted_date'] = pd.to_datetime(df['formatted_date']).dt.date
#     # New features
#     df.loc[:, 'scaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'QUANTITY']
#     df.loc[:, 'Wscaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'GROSS.WEIGHT']
#     df.loc[:, 'TaxRatio'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'CIF_USD_EQUIVALENT']
#     df.loc[:, 'Taxscalequantity'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'QUANTITY']

#     return df

### inputs
today = st.date_input("Today", 
                      datetime.date(2014, 5, 25),
                      min_value = datetime.date(2014, 1, 1),
                      max_value = datetime.date(2014, 12, 31))

# raw data
df = load_raw_data("data/import_data.csv")

# transformations
df = basic_trafo(df)

# today filtering
pre_year = today.year - 1
today_pre_year = (today - datetime.timedelta(days=365))
df_pre_year = df.loc[(df.formatted_date < today_pre_year) & (df.year == pre_year)].reset_index(drop=True)
df_cur_year = df.loc[(df.formatted_date < today) & (df.year > pre_year)].reset_index(drop=True)

### CONTENT

title()

## totals

# def total_metric(df_pre, df_cur, col, name, scale, unit):
#     if scale == "THOUSANDS":
#         total_pre = df_pre[col].sum()/1000
#         total_cur = df_cur[col].sum()/1000
#     elif scale == "MILLIONS":
#         total_pre = df_pre[col].sum()/1000000
#         total_cur = df_cur[col].sum()/1000000
#     else:
#         total_pre = df_pre[col].sum()
#         total_cur = df_cur[col].sum()
#         scale = ""

#     delta = (total_cur - total_pre)/total_pre
#     return st.metric(label=f"{name} {scale} [{unit}]",
#                      value="{:.0f}".format(total_cur), 
#                      delta="{:.2%}".format(delta))

col1, col2, col3 = st.columns(3)

columns = [col1, col2, col3]

# metric_dict = {
#                 'CIF':{'col':'CIF_USD_EQUIVALENT',
#                       'scale': 'MILLIONS',
#                       'unit': 'U$S'},
#                 'PACKAGES':{'col':'GROSS.WEIGHT',
#                             'scale': 'MILLIONS',
#                             'unit': 'PU'},
#                 'WEIGHT':{'col':'GROSS.WEIGHT',
#                           'scale': 'MILLIONS',
#                           'unit': 'KG'},
#                 'TAXES':{'col':'TOTAL.TAXES.USD',
#                          'scale': 'MILLIONS',
#                          'unit': 'U$S'},
#                 'ILLICITS':{'col':'illicit',
#                          'scale': '',
#                          'unit': 'PU'},
#                 'RAISED':{'col':'RAISED_TAX_AMOUNT_USD',
#                          'scale': 'THOUSANDS',
#                          'unit': 'U$S'}
#             }

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

## global trends

# cif and total taxes

vars = ['CIF_USD_EQUIVALENT', 'TOTAL.TAXES.USD']

col1, col2 = st.columns(2)

cols = [col1, col2]

with col1:

    layout = go.Layout(title="Imports trend",
                        xaxis=dict(title="MONTH"),
                        yaxis=dict(title="U$S"),
                        )

    global_fig = go.Figure(layout=layout)

# global_fig = make_subplots(rows=1,cols=2)

# for var in vars:

#     layout = go.Layout(title=var,
#                         xaxis=dict(title="MONTH"),
#                         yaxis=dict(title="U$S"),
#                         )

#     df_pre_month=df_pre_year.groupby(["month"])[var].sum().to_frame(name = df_pre_year.year[0])

#     trace = go.Scatter(x=df_pre_month.index,
#                         y=df_pre_month[df_pre_year.year[0]],
#                         mode='lines+markers',
#                         name=str(df_pre_year.year[0]))

#     global_fig.add_trace(trace, row=1, col=1)

#     df_cur_month=df_cur_year.groupby(["month"])[var].sum().to_frame(name = df_cur_year.year[0])
    
#     trace = go.Scatter(x=df_cur_month.index,
#                         y=df_cur_month[df_cur_year.year[0]],
#                         mode='lines+markers',
#                         name=str(df_cur_year.year[0]))

#     global_fig.add_trace(trace, row=1, col=2)

# st.plotly_chart(global_fig)