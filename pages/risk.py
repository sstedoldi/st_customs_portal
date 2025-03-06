################################
####### RISK MANAGEMENT ########
################################

# app
import streamlit as st
# general
import os
import datetime
# configutations
from modules.gral_config import page_config
# recourses
from modules.resources import post_meta_request, batch_post_request, single_post_request
# processing
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.2f}'.format
from modules.data_processes import load_data, basic_trafo, today_filtering
# # ploting
# import plotly.express as px
# import plotly.graph_objects as go
# local compenents
from modules.gral_comp import title, total_metric, dataframe_with_selections
from modules.model_scoring import prediction_scores
# local styles
from styles.basics import hide, lg_color, cont_padding

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
                      max_value = datetime.date(2014, 12, 24))

st.markdown("""---""")

################################
################################

## raw data
df_raw = load_data("data/import_data.csv")

# transformations
df_raw = basic_trafo(df_raw)

# today filtering
df_today, df_pre_year, df_cur_year = today_filtering(df_raw, today)

################################
################################

## sample data
df_sample = load_data("data/sample_import_data.csv", index=0)

################################
################################
################################

### CONTENT

## totals - current RMS
st.header("Metrics")
st.subheader("Current RMS")
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
                'TAX RAISED', 
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

# model_url = 'http://127.0.0.1:5000/' 
# model_url ='http://host.docker.internal:5000'
model_url ='http://18.210.14.100:5000'

meta_endpoint = os.path.join(model_url,'metadata')

metadata = post_meta_request(meta_endpoint)

print(type(metadata))
print(metadata)

if metadata:
    # Convert metadata to DataFrame
    df_meta = pd.DataFrame(metadata, index=['metadata'])
    print(df_meta.to_markdown())
    print(df_meta.info())

    # Parse and add new columns
    df_meta[['Hist rows', 'Hist columns']] = df_meta['Hist data shape'].str.strip('()').str.split(',', expand=True).astype(int)
    df_meta[['Dev rows', 'Dev columns']] = df_meta['Dev data shape'].str.strip('()').str.split(',', expand=True).astype(int)

    # Select columns for display
    basic_meta_to_show = ['Model name', 'Model algorithm', 'Author',
                          'Optimal threshold', 'ROC AUC', 'F1 score']
    more_meta_to_show = ['Hist data start', 'Hist data end', 'Hist rows',
                         'Dev data start', 'Dev data end', 'Dev rows']

    # Rename columns for display
    new_names = {'ROC AUC': 'ROC AUC [%]',
                 'Optimal threshold': 'Optimal threshold [%]',
                 'F1 score': 'F1 score [%]'}

    # Convert to percentages and round as needed
    percentage_columns = ['Optimal threshold', 'ROC AUC', 'F1 score']
    df_meta[percentage_columns] = df_meta[percentage_columns].astype(float) * 100
    df_meta['Optimal threshold'] = df_meta['Optimal threshold'].round(1)

    # Display metadata in two sections
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Model Card :robot_face:")
        st.write(df_meta[basic_meta_to_show].rename(columns=new_names).T)

        st.write("Training Timestamp")
        train_date, train_time = st.columns(2)
        with train_date:
            st.write(df_meta['Training timestamp'].iloc[0].split('_')[0])
        with train_time:
            st.write(df_meta['Training timestamp'].iloc[0].split('_')[1].replace('-', ':'))

        more_meta = st.checkbox("Show dev data information", value=False)

    if more_meta:
        st.subheader("Development and Historical Data")
        st.write(df_meta[more_meta_to_show])
else:
    st.error("No metadata available to display.")

################################
################################

## Model testing

with col2:
    st.subheader("Model testing")

    # st.write("New data sample batch test")

    threshold_new = st.slider("Risk threshold %", value=int(100*float(metadata['Optimal threshold'])), min_value=0, max_value=100)

    processing_settings = st.checkbox("Customize processing", value=False)
    if processing_settings:
        batch_size = st.number_input("Batch size new", value=1000, min_value=100, max_value=2000)
        sample = st.checkbox("Sample setting", value=False)
        if sample:
            sample_size = st.number_input("Sample size new", value=100, min_value=100, max_value=1000)
        else:
            sample_size = None
    else:
        batch_size = 1000
        sample_size = None

predict_batch_endpoint = os.path.join(model_url,'predict_batch')

@st.cache_data(show_spinner="Processing new sample events...")
def predict_batch(df_sample, batch_size, sample_size=None):
    try:
        df_sample.drop(columns=['formatted_date'], inplace=True)
    except:
        pass

    if sample_size:
        df_sample = df_sample.sample(sample_size)

    # number of batches needed
    num_batches = (len(df_sample) + batch_size - 1) // batch_size

    pred_results = pd.DataFrame()

    # batches process
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(df_sample))

        # Extract a batch of data
        batch_data = df_sample.iloc[start_idx:end_idx].to_dict()

        # Send batch request and collect results
        batch_pred_result = batch_post_request(batch_data, predict_batch_endpoint)

        # Convert dictionary to DataFrame
        batch_pred_result_df = pd.DataFrame(batch_pred_result)

        pred_results = pd.concat([pred_results, batch_pred_result_df], axis=0)

    return pred_results

df_with_batch_pred_new = predict_batch(df_sample, batch_size=batch_size, sample_size=sample_size)

df_with_batch_pred_new['prediction'] = np.where(df_with_batch_pred_new['proba'] >= threshold_new/100, True, False)

model_performance = st.checkbox("See model performance", value=False)
if model_performance:
    prediction_scores(df_with_batch_pred_new, 'illicit', 'prediction')

df_ai_controls_new = df_with_batch_pred_new[df_with_batch_pred_new['prediction']]

################################

# totals - current RMS + AI 

st.header("Metrics :female-detective: + :robot_face:")
st.subheader("Current RMS + AI model")

col1, col2, col3 = st.columns(3)

with col1:
    items_ai = len(df_ai_controls_new)
    items_df = len(df_sample)
    delta = (items_ai - items_df)/items_df
    st.metric(label=f"CONTROLED ITEMS [PU]",
                     value="{:,.0f}".format(items_ai), 
                     delta="{:.2%}".format(delta))

with col2:
    total_metric(df_sample, 
                df_ai_controls_new,
                'illicit', 
                'ILLICITS', 
                '', 
                'PU')

with col3:
    total_metric(df_sample, 
                df_ai_controls_new,
                'RAISED_TAX_AMOUNT_USD', 
                'TAX RAISED', 
                'THOUSANDS', 
                'U$S')

col1, col2, col3 = st.columns(3)

with col1:
    control_rate_ai = len(df_ai_controls_new)/len(df_sample)
    control_rate_df = len(df_sample)/len(df_sample) #all red channels in dataset
    delta = (control_rate_ai - control_rate_df)/control_rate_df
    st.metric(label=f"CONTROL RATE [%]",
                     value="{:.0%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))
    
with col2:
    control_rate_ai = df_ai_controls_new['illicit'].sum()/len(df_ai_controls_new)
    det_rate_df = df_sample['illicit'].sum()/len(df_sample)
    delta = (control_rate_ai - det_rate_df)/det_rate_df
    st.metric(label=f"DETECTION RATE [%]",
                     value="{:.2%}".format(control_rate_ai), 
                     delta="{:.2%}".format(delta))

with col3:
    raise_rate_ai = df_ai_controls_new['RAISED_TAX_AMOUNT_USD'].sum()/df_sample['TOTAL.TAXES.USD'].sum()
    raise_rate_df = df_sample['RAISED_TAX_AMOUNT_USD'].sum()/df_sample['TOTAL.TAXES.USD'].sum()
    delta = (raise_rate_ai - raise_rate_df)/raise_rate_df
    st.metric(label=f"TAX RAISED RATE [%]",
                     value="{:.2%}".format(raise_rate_ai), 
                     delta="{:.2%}".format(delta))  

st.markdown("""---""")

################################
################################

## On-deman single test

st.header("On-demand tests")

predict_endpoint = os.path.join(model_url,'predict')

# sample dataframe with selection

ddt_result = df_sample[['illicit', 'RAISED_TAX_AMOUNT_USD']]

selection = dataframe_with_selections(df_sample)

if st.button('Predict selection'):
    for index, row in selection.iterrows():
        # selected row sending to predict
        data = df_sample.loc[index].to_dict()
        # sending post request
        prediction_result = single_post_request(data, predict_endpoint)
        print(prediction_result)
        # processing results
        results = {}
        results['Risk'] = 100*float(prediction_result['proba'].strip("[]"))
        if results['Risk'] < threshold_new/2:
            results['Category'] = 'LOW 🟩'
        elif results['Risk'] < threshold_new:
            results['Category'] = 'MEDIUM 🟧'
        else:
            results['Category'] = 'HIGH 🟥'
        # adding inspection results
        results.update(df_sample.loc[index].to_dict())            
        print(results)

        # showing prediction and inspection result
        st.text(f"Item {index} evaluation")
        pred_col, res_col = st.columns(2)
        with pred_col:
            st.text('IA Model output')
            st.metric(label='Risk %', value = round(results['Risk'], 2))
            st.metric(label='Category', value = results['Category'])
        with res_col:
            st.text('Inspection results')
            st.write(ddt_result.loc[index].T)
        # processing explanation
        feature_importance = pd.DataFrame(prediction_result['expla'], index=['relevance']).T
        feature_importance['relevance'] = pd.to_numeric(feature_importance['relevance'])
        feature_importance['relevance'] = feature_importance['relevance']
        pos_importance = feature_importance.loc[feature_importance['relevance']>0]\
                                            .sort_values(by='relevance', ascending=False)
        pos_importance['%'] = round(100*pos_importance['relevance']/pos_importance['relevance'].sum(),0)
        neg_importance = feature_importance.loc[feature_importance['relevance']<0]\
                                            .sort_values(by='relevance', ascending=True)
        neg_importance['relevance'] = -neg_importance['relevance']
        neg_importance['%'] = round(100*neg_importance['relevance']/neg_importance['relevance'].sum(),0)
        pos_vars, neg_vars = st.columns(2)
        with pos_vars:
            st.text('Risky variables ⚠️')
            st.dataframe(pos_importance['%'].head(5))

            # fig = px.pie(pos_importance,
            #              values=pos_importance['%'],
            #              names=pos_importance.index,
            #              color=pos_importance.index,
            #              width=300,
            #              height=300)
            # fig.update_traces(showlegend=False)
            # st.plotly_chart(fig, use_container_width=True)
        with neg_vars:
            st.text('Safe variables 👍')
            st.dataframe(neg_importance['%'].head(5))
            # fig = px.pie(neg_importance,
            #              values=neg_importance['%'],
            #              names=neg_importance.index,
            #              color=neg_importance.index,
            #              width=300,
            #              height=300)
            # fig.update_traces(showlegend=False)
            # st.plotly_chart(fig, use_container_width=True)

        st.markdown("""---""")

