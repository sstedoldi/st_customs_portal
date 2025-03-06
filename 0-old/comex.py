import streamlit as st
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

### styles
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton

### content

## reading raw data
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

## group by ______ (country, office, hscode, importer)
# filters
# totals: anual, delta vs. previews year
# plot trends 

def main():
    print("comex page executed")
    title()
    st.header("Comex information")

if __name__ == "__main__":
    main()