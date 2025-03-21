import datetime
import streamlit as st
import pandas as pd

## reading raw data
@st.cache_data(show_spinner="Loading raw data")
def load_data(data_path, index=None):
    print("loading data from: ", data_path)
    dtypes_dict = {
    'TARIFF.CODE':str,
    'CIF_USD_EQUIVALENT': float,
    'QUANTITY': float,
    'GROSS.WEIGHT': float,
    'TOTAL.TAXES.USD': float,
    'RAISED_TAX_AMOUNT_USD':float,
    'illicit':bool
    }
    df = pd.read_csv(data_path, sep=",", dtype=dtypes_dict, index_col=index)
    return df

## basic transformations
@st.cache_data(show_spinner="Basic data transformations")
def basic_trafo(df):
    print("basic transformations")
    # HS codes
    df['HS02']=df['TARIFF.CODE'].str[0:2] #HS chapter
    df['HS04']=df['TARIFF.CODE'].str[0:4] #HS Header
    df['HS06']=df['TARIFF.CODE'].str[0:6] #HS Subheader
    # Dates
    df['formatted_date'] = pd.to_datetime(df[['year', 'month', 'day']], errors='coerce')
    df['formatted_date'] = df['formatted_date'].ffill()
    df['month-year'] = df['formatted_date'].dt.strftime('%b-%-y')
    df['month'] = df['formatted_date'].dt.strftime('%b')
    df['day_of_week'] = df['formatted_date'].dt.dayofweek
    # New features
    df.loc[:, 'scaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'QUANTITY']
    df.loc[:, 'Wscaleprice'] = df.loc[:,'CIF_USD_EQUIVALENT'] / df.loc[:,'GROSS.WEIGHT']
    df.loc[:, 'TaxRatio'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'CIF_USD_EQUIVALENT']
    df.loc[:, 'Taxscalequantity'] = df.loc[:,'TOTAL.TAXES.USD'] / df.loc[:,'QUANTITY']

    return df

## today filtering
@st.cache_data(show_spinner="Today filtering")
def today_filtering(df, today):
    df_today = df.loc[(df.formatted_date.dt.date <= today)]
    pre_year = today.year - 1
    today_pre_year = (today - datetime.timedelta(days=365))
    df_pre_year = df.loc[(df.formatted_date.dt.date < today_pre_year) & (df.year == pre_year)].reset_index(drop=True)
    df_cur_year = df.loc[(df.formatted_date.dt.date < today) & (df.year > pre_year)].reset_index(drop=True)

    return df_today, df_pre_year, df_cur_year