import streamlit as st
import datetime
# processing
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.2f}'.format
# ploting
# local compenents
from modules.gral_config import page_config
from modules.local_prepo import basic_trafo, load_raw_data, today_filtering
from modules.gral_comp import title, total_metric, metric_dict
from modules.gral_comp import colors, line_plot, line_plot_cur_vs_pre
from modules.model_scoring import prediction_scores
# local styles
from styles.basics import hide, lg_color, cont_padding
# backend comm
import requests

### CONFIG
st.set_page_config(**page_config)

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

### HEADER
img = "https://clikc.wcoomd.org/pluginfile.php/1/totara_core/loginimage/21999/Banner.png"
st.image(img, use_column_width=True)
title()
st.header("Risk Management")

### INPUTS
today = st.date_input("TODAY", 
                      datetime.date(2014, 5, 25),
                      min_value = datetime.date(2014, 1, 1),
                      max_value = datetime.date(2014, 12, 31))

st.markdown("""---""")

## raw data
df = load_raw_data("data/import_data.csv")

## transformations
df = basic_trafo(df)

## today filtering
df_today, df_pre_year, df_cur_year = today_filtering(df, today)

### CONTENT

## totals - current RMS

st.header("Metrics")
st.text("Current RMS")
col1, col2, col3 = st.columns(3)

with col1:
    items_cur = len(df_cur_year)
    items_pre = len(df_pre_year)
    delta = (items_cur - items_pre)/items_pre
    st.metric(label=f"ITEMS [PU]",
                     value="{:,.0f}".format(items_cur), 
                     delta="{:.2%}".format(delta))

with col2:
    total_metric(df_pre_year, 
                df_cur_year,
                'illicit', 
                'ILLICITS', 
                '', 
                'PU')

with col3:
    total_metric(df_pre_year, 
                df_cur_year,
                'RAISED_TAX_AMOUNT_USD', 
                'RAISED', 
                'THOUSANDS', 
                'U$S')

col1, col2, col3 = st.columns(3)

with col1:
    control_rate_cur = len(df_cur_year)/len(df_cur_year) #all red channels in dataset
    control_rate_pre = len(df_pre_year)/len(df_pre_year) # idem
    delta = (control_rate_cur - control_rate_pre)/control_rate_pre
    st.metric(label=f"CONTROL RATE [%]",
                     value="{:.0%}".format(control_rate_cur), 
                     delta="{:.2%}".format(delta))
    
with col2:
    det_rate_cur = df_cur_year['illicit'].sum()/len(df_cur_year)
    det_rate_pre = df_pre_year['illicit'].sum()/len(df_pre_year)
    delta = (det_rate_cur - det_rate_pre)/det_rate_pre
    st.metric(label=f"DETECTION RATE [%]",
                     value="{:.2%}".format(det_rate_cur), 
                     delta="{:.2%}".format(delta))

with col3:
    raise_rate_cur = df_cur_year['RAISED_TAX_AMOUNT_USD'].sum()/df_cur_year['TOTAL.TAXES.USD'].sum()
    raise_rate_pre = df_pre_year['RAISED_TAX_AMOUNT_USD'].sum()/df_pre_year['TOTAL.TAXES.USD'].sum()
    delta = (raise_rate_cur - raise_rate_pre)/raise_rate_pre
    st.metric(label=f"TAX RAISED RATE [%]",
                     value="{:.2%}".format(raise_rate_cur), 
                     delta="{:.2%}".format(delta))     

st.markdown("""---""")

## AI model
st.header('Fraud detection AI model')

# model metadata
@st.cache_resource
def send_post_meta_request():
    try:
        response = requests.post('http://localhost:5000/metadata')
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}


metadata = send_post_meta_request()

st.header("Model card 🤖")

col1, col2 = st.columns(2)
with col1:

    st.write("Name:", metadata["model_name"])
    st.write("Author:", metadata["author"])

with col2:
    st.write("Training Timestamp:", metadata["training_timestamp"])

# col1, col2 = st.columns(2)
# with col1:

#     st.write("Historic Data Shape:")
#     st.write("Rows: " + str(list(metadata["hist_data_shape"])[0]))
#     st.write("Columns: " + str(list(metadata["hist_data_shape"])[1]))


# with col2:
#     st.write("Development Data Shape:")
#     st.write("Rows: " + str(list(metadata["dev_data_shape"])[0]))
#     st.write("Columns: " + str(list(metadata["dev_data_shape"])[1]))

## totals - current RMS + AI 

st.header('Model testing')

# sample data
dtypes_dict = {
    'TARIFF.CODE':str,
    'CIF_USD_EQUIVALENT': float,
    'QUANTITY': float,
    'GROSS.WEIGHT': float,
    'TOTAL.TAXES.USD': float,
    'RAISED_TAX_AMOUNT_USD':float,
    'illicit':bool
}

st.session_state.sample = pd.read_csv('data/sample_import_data.csv', index_col=0, dtype=dtypes_dict).to_dict()

######################################################################


st.text("Current year batch test")

######################################################################
# inputs to add: sample_size, batch_size ... more filters for the data


threshold = st.slider("Risk threshold %", value=46, min_value=0, max_value=100)

col1, col2 = st.columns(2)
with col1:
    batch_size = st.number_input("Batch size", value=100, min_value=1, max_value=250)
with col2:
    col1, col2 = st.columns(2)
    with col1:
        sample = st.checkbox("Sample", value=False)
    if sample:
        with col2:
            sample_size = st.number_input("Sample size", value=500, min_value=1, max_value=1000)
    else:
        sample_size = None

# batch processing
@st.cache_resource
def send_batch_post_request(data):
    try:
        # Replace infinite and NaN values with None
        # data = {key: None if pd.isna(value) or value in [np.inf, -np.inf] else value for key, value in data.items()}

        response = requests.post('http://localhost:5000/predict_batch', json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}

@st.cache_data(show_spinner="Processing current year events...")
def predict_batch(df, batch_size, sample_size=None):
    try:
        df.drop(columns=['formatted_date'], inplace=True)
    except:
        pass

    if sample_size:
        df = df.sample(sample_size)

    # number of batches needed
    num_batches = (len(df) + batch_size - 1) // batch_size

    pred_results = pd.DataFrame()

    # batches process
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(df))

        # Extract a batch of data
        batch_data = df.iloc[start_idx:end_idx].to_dict()

        # Send batch request and collect results
        batch_pred_result = send_batch_post_request(batch_data)

        # Convert dictionary to DataFrame
        batch_pred_result_df = pd.DataFrame(batch_pred_result)

        pred_results = pd.concat([pred_results, batch_pred_result_df], axis=0)

    return pred_results

df_with_batch_pred = predict_batch(df_cur_year, batch_size=batch_size, sample_size=sample_size)

# print(df_with_batch_pred.info())

df_with_batch_pred['prediction'] = np.where(df_with_batch_pred['proba'] >= threshold/100, True, False)

prediction_scores(df_with_batch_pred, 'illicit', 'prediction')

# st.dataframe(df_with_batch_pred)

######################################################################
# add performance score and conf. matrix


##########################

st.text("On-demand single test")

# single processing
@st.cache_resource
def send_single_post_request(data):
    try:
         # Replace infinite and NaN values with None
        data = {key: None if pd.isna(value) or value in [np.inf, -np.inf] else value for key, value in data.items()}

        response = requests.post('http://localhost:5000/predict', json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}

# sample dataframe with selection
def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Seleccion", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Seleccion": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Seleccion]
    return selected_rows.drop('Seleccion', axis=1)



df = pd.DataFrame(st.session_state.sample)

ddt_result = df[['illicit', 'RAISED_TAX_AMOUNT_USD']]

selection = dataframe_with_selections(df)

if st.button('Predect selection'):
    for index, row in selection.iterrows():
        # selected row sending to predict
        data = df.loc[index].to_dict()
        # sending post request
        prediction_result = send_single_post_request(data)
        print(prediction_result)
        # processing results
        results = {}
        # results['Destinacion e item'] = df['Destinacion e item'].loc[index]
        results['Riesgo'] = 100*float(prediction_result['proba'].strip("[]"))
        if results['Riesgo'] < 23:
            results['Categoria'] = 'BAJO'
        elif results['Riesgo'] < 46:
            results['Categoria'] = 'MEDIO'
        else:
            results['Categoria'] = 'ALTO'
        # adding inspection results
        results.update(df.loc[index].to_dict())            
        print(results)
        # results = pd.DataFrame(results, index=[0])
        # showing prediction and inspection result
        st.text(f"Evaluación del ítem {index}")
        pred_col, res_col = st.columns((1, 1))
        with pred_col:
            st.text('Respuesta del modelo IA')
            st.metric(label='Riesgo %', value = round(results['Riesgo'], 2))
            st.metric(label='Categoria', value = results['Categoria'])
        with res_col:
            st.text('Resultado de la inspección')
            st.write(ddt_result.loc[index].T)
        st.markdown("""---""")
