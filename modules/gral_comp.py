import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def title():
    return st.title("CustomsPortal App")

metric_dict = {
                'CIF':{'col':'CIF_USD_EQUIVALENT',
                      'scale': 'MILLIONS',
                      'unit': 'U$S'},
                'PACKAGES':{'col':'QUANTITY',
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

colors = [('blue','lightblue',), ('green', 'lightgreen',),
          ('red','pink',), ('coral', 'lightcoral',),
          ('darkblue','blue',), ('darkseagreen', 'seagreen',),]

def total_metric(df_pre, df, col, name, scale, unit):
    if scale == "THOUSANDS":
        total_pre = df_pre[col].sum()/1000
        total_cur = df[col].sum()/1000
    elif scale == "MILLIONS":
        total_pre = df_pre[col].sum()/1000000
        total_cur = df[col].sum()/1000000
    else:
        total_pre = df_pre[col].sum()
        total_cur = df[col].sum()
        scale = ""

    delta = (total_cur - total_pre)/total_pre
    return st.metric(label=f"{name} {scale} [{unit}]",
                     value="{:,.0f}".format(total_cur), 
                     delta="{:.2%}".format(delta))


def line_plot(df, var, colors, color_id, today, period='6 months'): #current vs. previews
    today = pd.to_datetime(today)
    if period=='6 months':
        ini_day = (today - pd.DateOffset(months=6))
        ini_day = pd.to_datetime(ini_day)
        df_period = df.loc[(df['formatted_date'] >= ini_day) & (df['formatted_date'] <= today)].reset_index(drop=True)
    elif period=='12 months':
        ini_day = (today - pd.DateOffset(months=12))
        ini_day = pd.to_datetime(ini_day)
        df_period = df.loc[(df['formatted_date'] >= ini_day) & (df['formatted_date'] <= today)].reset_index(drop=True)
    else:
        print(f'line plot parameter period = {period} is not valid')
        return

    df_period=df_period.groupby(['month-year'], sort=False)[var].sum().to_frame(name = var)

    layout = go.Layout(title=var,
                xaxis=dict(title="MONTH"),
                yaxis=dict(title="U$S", range=[0,None]),
                )

    trace_cur = go.Scatter(x=df_period.index,
                        y=df_period[var],
                        mode='lines+markers',
                        name=str(var),
                        line=dict(color=colors[color_id][0]))

    traces = [trace_cur]
    
    global_fig = go.Figure(data=traces, layout=layout)

    global_fig.update_yaxes(rangemode="tozero")

    return st.plotly_chart(global_fig, use_container_width=True)

def line_plot_cur_vs_pre(df, df_pre, var, colors, color_id): #current vs. previews

    df_cur_month=df.groupby(['month'], sort=False)[var].sum().to_frame(name = df.year[0])
    df_pre_month=df_pre.groupby(['month'], sort=False)[var].sum().to_frame(name = df_pre.year[0])

    layout = go.Layout(title=var,
                xaxis=dict(title="MONTH"),
                yaxis=dict(title="U$S", range=[0,None]),
                )

    trace_cur = go.Scatter(x=df_cur_month.index,
                        y=df_cur_month[df.year[0]],
                        mode='lines+markers',
                        name=str(df.year[0]),
                        line=dict(color=colors[color_id][0]))

    trace_pre = go.Scatter(x=df_pre_month.index,
                        y=df_pre_month[df_pre.year[0]],
                        mode='lines+markers',
                        name=str(df_pre.year[0]),
                        line=dict(color=colors[color_id][1]))

    traces = [trace_cur, trace_pre]
    
    global_fig = go.Figure(data=traces, layout=layout)

    global_fig.update_yaxes(rangemode="tozero")

    return st.plotly_chart(global_fig, use_container_width=True)

def dataframe_with_selections(df_sample):
    df_with_selections = df_sample.copy()
    df_with_selections.insert(0, "Seleccion", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Seleccion": st.column_config.CheckboxColumn(required=True)},
        disabled=df_sample.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Seleccion]
    return selected_rows.drop('Seleccion', axis=1)