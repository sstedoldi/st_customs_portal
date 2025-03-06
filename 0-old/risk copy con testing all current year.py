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
from modules.gral_comp import title, total_metric
from modules.model_scoring import prediction_scores
# local styles
from styles.basics import hide, lg_color, cont_padding
# backend comm
import requests

################################
################################
################################

### CONFIG
st.set_page_config(**page_config)

################################
################################
################################

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

################################
################################
################################

### HEADER
img = "https://clikc.wcoomd.org/pluginfile.php/1/totara_core/loginimage/21999/Banner.png"
st.image(img, use_column_width=True)
title()
st.header("Risk Management")

################################
################################
################################

### INPUTS
today = st.date_input("TODAY", 
                      datetime.date(2014, 5, 25),
                      min_value = datetime.date(2014, 1, 1),
                      max_value = datetime.date(2014, 12, 31))

st.markdown("""---""")

################################
################################

## raw data
df = load_raw_data("data/import_data.csv")

################################
################################

## transformations
df = basic_trafo(df)

################################
################################

## today filtering
df_today, df_pre_year, df_cur_year = today_filtering(df, today)

################################
################################
################################

### CONTENT

## totals - current RMS

st.header("Metrics")
st.text("Current RMS")
col1, col2, col3 = st.columns(3)

with col1:
    items_ai = len(df_cur_year)
    items_df = len(df_pre_year)
    delta = (items_ai - items_df)/items_df
    st.metric(label=f"CONTROLED ITEMS [PU]",
                     value="{:,.0f}".format(items_ai), 
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
    control_rate_df = len(df_cur_year)/len(df_cur_year) #all red channels in dataset
    control_rate_pre = len(df_pre_year)/len(df_pre_year) # idem
    delta = (control_rate_df - control_rate_pre)/control_rate_pre
    st.metric(label=f"CONTROL RATE [%]",
                     value="{:.0%}".format(control_rate_df), 
                     delta="{:.2%}".format(delta))
    
with col2:
    det_rate_df = df_cur_year['illicit'].sum()/len(df_cur_year)
    det_rate_pre = df_pre_year['illicit'].sum()/len(df_pre_year)
    delta = (det_rate_df - det_rate_pre)/det_rate_pre
    st.metric(label=f"DETECTION RATE [%]",
                     value="{:.2%}".format(det_rate_df), 
                     delta="{:.2%}".format(delta))

with col3:
    raise_rate_df = df_cur_year['RAISED_TAX_AMOUNT_USD'].sum()/df_cur_year['TOTAL.TAXES.USD'].sum()
    raise_rate_ai = df_pre_year['RAISED_TAX_AMOUNT_USD'].sum()/df_pre_year['TOTAL.TAXES.USD'].sum()
    delta = (raise_rate_df - raise_rate_ai)/raise_rate_ai
    st.metric(label=f"TAX RAISED RATE [%]",
                     value="{:.2%}".format(raise_rate_df), 
                     delta="{:.2%}".format(delta))     

st.markdown("""---""")

################################
################################

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

st.header("Model card :robot_face:")

col1, col2 = st.columns(2)
with col1:

    st.write("Name:", metadata["model_name"])
    st.write("Author:", metadata["author"])

with col2:
    st.write("Training Timestamp:", metadata["training_timestamp"])

################################
################################

## Model testing

st.header('Model testing')

# current year batch test
st.text("Current year batch test")

threshold = st.slider("Risk threshold %", value=46, min_value=0, max_value=100)

col1, col2 = st.columns(2)
with col1:
    batch_size = st.number_input("Batch size", value=1000, min_value=1, max_value=2000)
with col2:
    col1, col2 = st.columns(2)
    with col1:
        sample = st.checkbox("Sample", value=True)
    if sample:
        with col2:
            sample_size = st.number_input("Sample size", value=1000, min_value=1, max_value=1000)
    else:
        sample_size = None

# batch processing
# @st.cache_resource
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

df_with_batch_pred['prediction'] = np.where(df_with_batch_pred['proba'] >= threshold/100, True, False)

prediction_scores(df_with_batch_pred, 'illicit', 'prediction')

df_ai_controls = df_with_batch_pred[df_with_batch_pred['prediction']]

################################

# totals - current RMS + AI 

st.header("Metrics :female-detective: + :robot_face:")
st.text("Current RMS + AI model")
col1, col2, col3 = st.columns(3)

with col1:
    items_ai = len(df_ai_controls)
    items_df = len(df_cur_year)
    delta = (items_ai - items_df)/items_df
    st.metric(label=f"CONTROLED ITEMS [PU]",
                     value="{:,.0f}".format(items_ai), 
                     delta="{:.2%}".format(delta))

with col2:
    total_metric(df_cur_year, 
                df_ai_controls,
                'illicit', 
                'ILLICITS', 
                '', 
                'PU')

with col3:
    total_metric(df_cur_year, 
                df_ai_controls,
                'RAISED_TAX_AMOUNT_USD', 
                'RAISED', 
                'THOUSANDS', 
                'U$S')

col1, col2, col3 = st.columns(3)

with col1:
    control_rate_ai = len(df_ai_controls)/len(df_cur_year)
    control_rate_df = len(df_cur_year)/len(df_cur_year) #all red channels in dataset
    delta = (control_rate_ai - control_rate_df)/control_rate_df
    st.metric(label=f"CONTROL RATE [%]",
                     value="{:.0%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))
    
with col2:
    control_rate_ai = df_ai_controls['illicit'].sum()/len(df_ai_controls)
    det_rate_df = df_cur_year['illicit'].sum()/len(df_cur_year)
    delta = (control_rate_ai - det_rate_df)/det_rate_df
    st.metric(label=f"DETECTION RATE [%]",
                     value="{:.2%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))

with col3:
    raise_rate_ai = df_ai_controls['RAISED_TAX_AMOUNT_USD'].sum()/df_cur_year['TOTAL.TAXES.USD'].sum()
    raise_rate_df = df_cur_year['RAISED_TAX_AMOUNT_USD'].sum()/df_cur_year['TOTAL.TAXES.USD'].sum()
    delta = (raise_rate_ai - raise_rate_df)/raise_rate_df
    st.metric(label=f"TAX RAISED RATE [%]",
                     value="{:.2%}".format(raise_rate_ai), 
                     delta="{:.2%}".format(delta))  

st.markdown("""---""")

################################
################################

## On-deman single test

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
        if results['Riesgo'] < threshold/2:
            results['Categoria'] = 'BAJO'
        elif results['Riesgo'] < threshold:
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


################################
################################

## current year batch test

st.text("New data sample batch test")

threshold_new = st.slider("Risk threshold new %", value=46, min_value=0, max_value=100)

col1, col2 = st.columns(2)
with col1:
    batch_size = st.number_input("Batch size new", value=1000, min_value=1, max_value=2000)
with col2:
    col1, col2 = st.columns(2)
    with col1:
        sample = st.checkbox("Sample new", value=True)
    if sample:
        with col2:
            sample_size = st.number_input("Sample size new", value=1000, min_value=1, max_value=1000)
    else:
        sample_size = None

df_with_batch_pred_new = predict_batch(df, batch_size=batch_size, sample_size=sample_size)

df_with_batch_pred_new['prediction'] = np.where(df_with_batch_pred_new['proba'] >= threshold_new/100, True, False)

prediction_scores(df_with_batch_pred_new, 'illicit', 'prediction')

df_ai_controls_new = df_with_batch_pred_new[df_with_batch_pred_new['prediction']]

################################

# totals - current RMS + AI 

st.header("Metrics :female-detective: + :robot_face:")
st.text("Current RMS + AI model")
col1, col2, col3 = st.columns(3)

with col1:
    items_ai = len(df_ai_controls_new)
    items_df = len(df)
    delta = (items_ai - items_df)/items_df
    st.metric(label=f"CONTROLED ITEMS [PU]",
                     value="{:,.0f}".format(items_ai), 
                     delta="{:.2%}".format(delta))

with col2:
    total_metric(df, 
                df_ai_controls_new,
                'illicit', 
                'ILLICITS', 
                '', 
                'PU')

with col3:
    total_metric(df, 
                df_ai_controls_new,
                'RAISED_TAX_AMOUNT_USD', 
                'RAISED', 
                'THOUSANDS', 
                'U$S')

col1, col2, col3 = st.columns(3)

with col1:
    control_rate_ai = len(df_ai_controls_new)/len(df)
    control_rate_df = len(df)/len(df) #all red channels in dataset
    delta = (control_rate_ai - control_rate_df)/control_rate_df
    st.metric(label=f"CONTROL RATE [%]",
                     value="{:.0%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))
    
with col2:
    control_rate_ai = df_ai_controls_new['illicit'].sum()/len(df_ai_controls_new)
    det_rate_df = df['illicit'].sum()/len(df)
    delta = (control_rate_ai - det_rate_df)/det_rate_df
    st.metric(label=f"DETECTION RATE [%]",
                     value="{:.2%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))

with col3:
    raise_rate_ai = df_ai_controls_new['RAISED_TAX_AMOUNT_USD'].sum()/df['TOTAL.TAXES.USD'].sum()
    raise_rate_df = df['RAISED_TAX_AMOUNT_USD'].sum()/df['TOTAL.TAXES.USD'].sum()
    delta = (raise_rate_ai - raise_rate_df)/raise_rate_df
    st.metric(label=f"TAX RAISED RATE [%]",
                     value="{:.2%}".format(raise_rate_ai), 
                     delta="{:.2%}".format(delta))  

st.markdown("""---""")