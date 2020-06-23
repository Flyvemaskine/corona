#!/usr/bin/env python3

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import json
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import re

from app import app

env_vars = open("vars.env", "r")
mongo_read = re.search(r'.*=(.*)\n',env_vars.readlines()[1])[1]
mongo_client_uri = "mongodb://corona_dash_app_ro:" + mongo_read + "@ds263248.mlab.com:63248/heroku_7ggf57x7?retryWrites=false"

client = MongoClient(mongo_client_uri)
db=client["heroku_7ggf57x7"]
by_country_collection = db['by_country']

state_table_collection = db['state_table']
state_table_cols = [doc for doc in state_table_collection.find({"Incremental":"Incremental"}, {'_id':0, 'Incremental':0})][0].keys()

mongo_query_out = [doc for doc in by_country_collection.find({"country_name":"US"})]

blank_graph={'data':[], 'layout':{'margin':{"l": 0, "b": 0, "t": 0, "r": 0}}}

incrementals = ["Incremental", "Cumulative"]

states_df = pd.read_csv("states.csv")
map_metrics = ['Cases', 'Deaths', '%Positive']

layout = html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='map-metrics-dropdown',
                    options=[{'label':map_metric, 'value':map_metric} for map_metric in map_metrics],
                    value='Cases'
                )
            ], style={'width':'49%', 'display':'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    id='incremental-dropdown',
                    options=[{'label':incremental,'value':incremental} for incremental in incrementals],
                    value='Incremental'
                )
            ], style={'width':'49%', 'float':'right',  'display':'inline-block'})
        ], style={
            'borderBottom':'thin lightgrey solid',
            'backgroundColor':'rgb(250, 250, 250)',
            'padding': '10px 5px'
        }),
        html.Div([
            dcc.Graph(id='state-map', style={'height':'40vh'}),
            dash_table.DataTable(
                id='state-table',
                columns=[{'name':i, 'id':i} for i in state_table_cols],
                style_table={'width': '100%', 'overflowY':'scroll', 'height':'40vh'},
                sort_action="native",
                style_cell={'font_family':'HelveticaNeue'}
            )
        ], style={'columnCount':2, 'width': '100%'}),
        # Row
        html.Div([
            dcc.Graph(id='plot-cases-country', style={'height':'40vh'}),
            dcc.Graph(id='plot-deaths-country', style={'height':'40vh'}),
            dcc.Graph(id='plot-recovered-country', style={'height':'40vh'}),
            dcc.Graph(id='plot-active-country', style={'height':'40vh'})
        ], style={'columnCount':4, 'width': '100%'})

], style = {'width': '100%', 'display:':'inline-block'})




@app.callback(
    Output('plot-cases-country', 'figure'),
    [Input('incremental-dropdown', 'value')]
)
def update_graph_cases(incremental):
    incremental = str.lower(incremental) + "_plots"
    return mongo_query_out[0][incremental]["confirmed"]

@app.callback(
    Output('plot-deaths-country', 'figure'),
    [Input('incremental-dropdown', 'value')]
)
def update_graph_deaths(incremental):
    incremental = str.lower(incremental) + "_plots"
    return mongo_query_out[0][incremental]["deaths"]

@app.callback(
    Output('plot-recovered-country', 'figure'),
    [Input('incremental-dropdown', 'value')]
)
def update_graph_recovered(incremental):
    incremental = str.lower(incremental) + "_plots"
    return mongo_query_out[0][incremental]["recovered"]

@app.callback(
    Output('plot-active-country', 'figure'),
    [Input('incremental-dropdown', 'value')]
)
def update_graph_active(incremental):
    incremental = str.lower(incremental) + "_plots"
    return mongo_query_out[0][incremental]["active"]


@app.callback(
    Output('state-table', 'data'),
    [Input('incremental-dropdown', 'value')]
)
def update_state_table(incremental):
    mongo_query_out = [doc for doc in state_table_collection.find({"Incremental":incremental}, {'_id':0, 'Incremental':0})]
    return mongo_query_out

@app.callback(
    Output('state-map', 'figure'),
    [Input('incremental-dropdown', 'value'),
     Input('map-metrics-dropdown', 'value')]
)
def update_state_table(incremental, map_metric):
    mongo_query_out = [doc for doc in state_table_collection.find({"Incremental":incremental}, {'_id':0, 'Incremental':0})]
    df_to_plot = pd.DataFrame(mongo_query_out)
    df_to_plot = df_to_plot.merge(states_df, how='left', left_on=['State'], right_on=["State"])
    df_to_plot['color_field'] = df_to_plot[map_metric]/max(df_to_plot[map_metric])

    fig = None

    fig = px.choropleth(df_to_plot, locations="Abbreviation",
                    locationmode='USA-states',
                    scope="usa",
                    color='color_field',
                    hover_data=[map_metric, 'State'],
                    color_continuous_scale=px.colors.sequential.Plasma) \
                .update_layout(coloraxis_showscale=False, margin_t=10, margin_b=10, margin_l=10, margin_r=10)


    return fig
