#!/usr/bin/env python3

from bson import json_util
from datetime import date, datetime
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import json
import pandas as pd
from pymongo import MongoClient
import re

from app import app

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

env_vars = open("vars.env", "r")
mongo_read = re.search(r'.*=(.*)\n',env_vars.readlines()[1])[1]
mongo_client_uri = "mongodb://corona_dash_app_ro:" + mongo_read + "@ds263248.mlab.com:63248/heroku_7ggf57x7?retryWrites=false"

client = MongoClient(mongo_client_uri)
db=client["heroku_7ggf57x7"]
by_state_collection = db['by_state']

states = pd.read_csv("states.csv")
states = states.State.tolist()

incrementals = ['Cumulative' ,'Incremental']

layout = html.Div([
        # Row 1 Dropdowns
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='states-dropdown',
                    options=[{'label':state, 'value':state} for state in states],
                    value='New York'
                )
            ],
            style={'width':'49%', 'display':'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id='incremental-dropdown',
                    options=[{'label':incremental,'value':incremental} for incremental in incrementals],
                    value='Cumulative'
                )
            ], style={'width':'49%', 'float':'right',  'display':'inline-block'})
        ], style={
            'borderBottom':'thin lightgrey solid',
            'backgroundColor':'rgb(250, 250, 250)',
            'padding': '10px 5px'
        }),

        # Row 2 Graphs
        html.Div([
            dcc.Graph(id='plot-cases-state',  style={'height':'40vh'}),
            dcc.Graph(id='plot-deaths-state',  style={'height':'40vh'})
        ], style={'columnCount':2, 'width': '100%'}),
        # Row 3 Graphs
        html.Div([
            dcc.Graph(id='plot-testing-rate', style={'height':'40vh'}),
            dcc.Graph(id='plot-tests-administered', style={'height':'40vh'})
        ], style={'columnCount':2, 'width': '100%'}),

        html.Div(id='cached-query', style={'display':'none'})

], style = {'width': '100%', 'display:':'inline-block'})


@app.callback(Output('cached-query', 'children'),
              [Input('states-dropdown', 'value')])
def fetch_query(state_filter):
    mongo_query_out = [doc for doc in by_state_collection.find({"state_name":state_filter}, {'_id':0})]
    return(json.dumps(mongo_query_out, default=json_serial))

@app.callback(
Output('plot-cases-state', 'figure'),
    [Input('cached-query', 'children'),
     Input('incremental-dropdown', 'value')]
)
def update_graph_cases(cached_query, incremental):
    incremental = str.lower(incremental) + "_plots"
    cached_query = json.loads(cached_query)
    return cached_query[0][incremental]["confirmed"]

@app.callback(
    Output('plot-deaths-state', 'figure'),
    [Input('cached-query', 'children'),
     Input('incremental-dropdown', 'value')]
)
def update_graph_deaths(cached_query, incremental):
    incremental = str.lower(incremental) + "_plots"
    cached_query = json.loads(cached_query)
    return cached_query[0][incremental]["deaths"]

@app.callback(
    Output('plot-testing-rate', 'figure'),
    [Input('cached-query', 'children'),
     Input('incremental-dropdown', 'value')]
)
def update_graph_testing_rate(cached_query, incremental):
    incremental = str.lower(incremental) + "_plots"
    cached_query = json.loads(cached_query)
    return cached_query[0][incremental]["testing_rate"]

@app.callback(
    Output('plot-tests-administered', 'figure'),
    [Input('cached-query', 'children'),
     Input('incremental-dropdown', 'value')]
)
def update_graph_tests_administered(cached_query, incremental):
    incremental = str.lower(incremental) + "_plots"
    cached_query = json.loads(cached_query)
    return cached_query[0][incremental]["tests_administered"]
