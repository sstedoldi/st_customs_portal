import streamlit as st
import datetime
# processing
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
# ploting
import plotly.express as px
import plotly.graph_objects as go
# local compenents
from modules.gral_config import page_config
from modules.gral_comp import title
# local styles
from styles.basics import hide, lg_color

### site configuration
st.set_page_config(**page_config)

### session state
#

### styles
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton

### content
# reading raw data
@st.cache_data
def load_raw_data(raw_data_path):
    print("loading raw data")
    dtypes_dict = {
    'TARIFF.CODE':str,
    'CIF_USD_EQUIVALENT': float,
    'QUANTITY': float,
    'GROSS.WEIGHT': float,
    'TOTAL.TAXES.USD': float,
    'RAISED_TAX_AMOUNT_USD':float,
    'illicit':bool
    }
    df = pd.read_csv(raw_data_path, sep=",", dtype=dtypes_dict)
    return df

## basic transformations
@st.cache_data
def basic_trafo(df):
    print("basic transformations")
    # HS codes
    df['HS02']=df['TARIFF.CODE'].str[0:2] #HS chapter
    df['HS04']=df['TARIFF.CODE'].str[0:4] #HS Header
    df['HS06']=df['TARIFF.CODE'].str[0:6] #HS Subheader
    # Dates
    df['formatted_date'] = pd.to_datetime(df[['year', 'month', 'day']], errors='coerce')
    df['formatted_date'] = df['formatted_date'].fillna(method='ffill') 
    df['day_of_week'] = df['formatted_date'].dt.dayofweek
    df['formatted_date'] = pd.to_datetime(df['formatted_date']).dt.date
    # New features
    df.loc[:, 'scaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'QUANTITY']
    df.loc[:, 'Wscaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'GROSS.WEIGHT']
    df.loc[:, 'TaxRatio'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'CIF_USD_EQUIVALENT']
    df.loc[:, 'Taxscalequantity'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'QUANTITY']
    return df

### inputs
today = st.date_input("Today", 
                      datetime.date(2014, 5, 25),
                      min_value = datetime.date(2014, 1, 1),
                      max_value = datetime.date(2014, 12, 31))

# raw data
df = load_raw_data("data/import_data.csv")

st.dataframe(df)
describe_raw = st.checkbox("Describe",
                            value=False,
                            key="describe_data")

if describe_raw:
    st.dataframe(df.describe())

# transformations
df = basic_trafo(df)

# today filtering
pre_year = today.year - 1
today_pre_year = (today - datetime.timedelta(days=365))
df_pre_year = df.loc[(df.formatted_date < today_pre_year) & (df.year == pre_year)]
df_cur_year = df.loc[(df.formatted_date < today) & (df.year > pre_year)]

## totals
# anual, delta vs. previews year (CIF, QUANT, TONs, TAXES)
# plot trends

def total_metric(df_pre, df_cur, col, name, scale, unit):
    if scale == "THOUSANDS":
        total_pre = df_pre[col].sum()/1000
        total_cur = df_cur[col].sum()/1000
    elif scale == "MILLIONS":
        total_pre = df_pre[col].sum()/1000000
        total_cur = df_cur[col].sum()/1000000
    else:
        total_pre = df_pre[col].sum()
        total_cur = df_cur[col].sum()
        scale = ""

    delta = (total_cur - total_pre)/total_pre
    return st.metric(label=f"{name} {scale} [{unit}]",
                     value="{:.0f}".format(total_cur), 
                     delta="{:.2%}".format(delta))

col1, col2, col3 = st.columns(3)

columns = [col1, col2, col3]

metric_dict = {
                'CIF':{'col':'CIF_USD_EQUIVALENT',
                      'scale': 'MILLIONS',
                      'unit': 'U$S'},
                'PACKAGES':{'col':'GROSS.WEIGHT',
                            'scale': 'MILLIONS',
                            'unit': 'PU'},
                'WEIGHT':{'col':'GROSS.WEIGHT',
                          'scale': 'MILLIONS',
                          'unit': 'KG'},
                'TAXES':{'col':'TOTAL.TAXES.USD',
                         'scale': 'MILLIONS',
                         'unit': 'U$S'},
                'ILLICITS':{'col':'illicit',
                         'scale': '',
                         'unit': 'PU'},
                'RAISED':{'col':'RAISED_TAX_AMOUNT_USD',
                         'scale': 'THOUSANDS',
                         'unit': 'U$S'}
            }


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


# # CIF
# with col1:
#     total_metric(df_pre_year, 
#                 df_cur_year,
#                 metric_dict.i, 
#                 metric_dict.i.col, 
#                 metric_dict.i.col.scale, 
#                 metric_dict.i.col.unit)
    
# # QUANTITY
# with col2:
#     total_metric(df_pre_year, 
#                 df_cur_year, 
#                 "QUANTITY", 
#                 "PACKAGES", 
#                 "MILLIONS",
#                 "PU")
# # TONS
# with col3:
#     total_metric(df_pre_year, 
#                 df_cur_year, 
#                 "GROSS.WEIGHT", 
#                 "WEIGHT", 
#                 "MILLIONS",
#                 "KG")

# cif, qua, ton, tax, infra, r_tax = st.columns(6)

# def main():
#     title()
#     # raw data
#     df = load_raw_data("data/import_data.csv")
#     print(df.info())

#     st.dataframe(df)
#     describe_raw = st.checkbox("Describe",
#                               value=False,
#                               key="describe_data")
#                             #   on_change=describe,
#                             #   args=(df,))
    
#     if describe_raw:
#         st.dataframe(df.describe())

    

# if __name__ == "__main__":
#     main()
