#!/usr/bin/env python3

import boto3
from boto3.dynamodb.conditions import Key
from bson import json_util
from datetime import date, datetime
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dotenv import load_dotenv
import json
import os
import pandas as pd
from pymongo import MongoClient
import re
from app import app, server
from urllib.request import urlopen
import plotly.express as px
import plotly.graph_objects as go

# Dropdowns
incrementals = ["Cumulative", "Incremental"]
metrics_list = ["% Positive", "Confirmed Cases", "Deaths"]

# Mongo stuff general
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

## AWS stuff
load_dotenv(os.path.join(os.getcwd(),"vars.env"))
AWS_KEY=os.getenv('AWS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')

AWS_KEY_DYNAMO=os.getenv('AWS_KEY_DYNAMO')
AWS_SECRET_DYNAMO=os.getenv('AWS_SECRET_DYNAMO')

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_KEY,
                  aws_secret_access_key=AWS_SECRET,
                  region_name='us-east-2')


dynamodb = boto3.client('dynamodb',
                        aws_access_key_id=AWS_KEY_DYNAMO,
                        aws_secret_access_key=AWS_SECRET_DYNAMO,
                        region_name='us-east-2')
dynamodb_r = boto3.resource('dynamodb',
                            aws_access_key_id=AWS_KEY_DYNAMO,
                            aws_secret_access_key=AWS_SECRET_DYNAMO,
                            region_name='us-east-2')




with urlopen("https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"
) as response:
    states = json.load(response)

maps_df = s3.get_object(Bucket="us-corona-tracking-data", Key="df_for_maps.csv")
maps_df = pd.read_csv(maps_df['Body'])


states_conversion = s3.get_object(Bucket="us-corona-tracking-data", Key="states.csv")
states_conversion = pd.read_csv(states_conversion['Body']).set_index(["Abbreviation"])
states_conversion_dict = states_conversion.to_dict()["State"]


states_conversion_index = states_conversion.reset_index().State.to_dict()
states_conversion_index = dict((v,k) for k,v in states_conversion_index.items())

blank_graph={'data':[], 'layout':{'margin':{"l": 0, "b": 0, "t": 0, "r": 0}}}

app.layout = html.Div([
    html.Div([
    # Row 1 Title
        html.H3("US COVID Tracking")
    ], className="row_one_container"),

    # Row 2: About
    html.Div([
        html.Div([
            html.P("This dashboard is intended to track the spread of the COVID-19 through the US. Testing data is provided by  ",style={'display':'inline-block', 'margin':'5px'}),
            html.A('The COVID Tracking Project', href='https://covidtracking.com',  target='_blank'),
            html.P("  while case reports and fatalities are provided by  ",style={'display':'inline-block', 'margin':'5px'}),
            html.A('JHU', href='https://github.com/CSSEGISandData/COVID-19',  target='_blank'),
            html.Br(),
            html.P("Clicking on states in the map below will apply a state level filter. ",style={'display':'inline-block', 'margin':'5px'})

        ], className='about_app_blurb_container')
    ], className="row_two_container"),

    html.Div(id="state_filter", style={'display':'none'}),
    # Selectors

    html.Div([
        html.Div([html.P(["Map Metric: "])], className="dropdown_label"),
        html.Div([
            dcc.Dropdown(
                id='metrics-dropdown',
                options=[{'label':metric, 'value':metric} for metric in metrics_list],
                value='Confirmed Cases'
            )
        ], className="metric_dd_container"),
        html.Div([]),
        html.Button('Clear Geography Filter', id='clear-geo', className='geo_button_visible'),
        html.Div([]),
        html.Div([html.P(["Metric Type: "])], className="dropdown_label"),
        html.Div([
            dcc.Dropdown(
                id='incremental-dropdown',
                options=[{'label':incremental,'value':incremental} for incremental in incrementals],
                value='Cumulative')
        ], className='incremental_dd_container'),

    ], className='row_three_container'),
    # Graphs

    html.Div([
        html.Div([
            html.P("Title", id="map_graph_label", className="title_bar_default"),
            dcc.Graph(id="state_map_plot", figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="positive_graph_label", className="title_bar_positive"),
            dcc.Graph(id='testing_plot', figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="cases_graph_label", className="title_bar_cases"),
            dcc.Graph(id='confirmed_cases_plot', figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="deaths_graph_label", className='title_bar_deaths'),
            dcc.Graph(id='deaths_plot', className='regular_graph')
        ],className='graph_container')
    ], className='graph_grid')


],id="main_container")

@app.callback(
    [Output('map_graph_label', 'children'),
     Output('positive_graph_label', 'children'),
     Output('cases_graph_label', 'children'),
     Output('deaths_graph_label','children')
    ],
    [Input('incremental-dropdown', 'value'),
    Input('metrics-dropdown', 'value'),
    Input('state_filter', 'children')]
)
def update_title_bar_labels(incremental, metric, state_filter):
    try:
        state_name = json.loads(state_filter)["points"][0]["customdata"][1]
    except TypeError:
        state_name = "CW"
    map_date = maps_df['Date'].max()
    first_label = [incremental + " " + metric + ": " + map_date]
    out = [(incremental + " " +  metric + " - " + state_name) for metric in metrics_list]
    out = first_label + out
    return(tuple(out))

@app.callback(
    Output('map_graph_label', 'className'),
    [Input('metrics-dropdown', 'value')]
)
def update_title_bar_labels(metric):
    if metric == "% Positive":
        out = "title_bar_positive"
    elif metric == "Deaths":
        out = "title_bar_deaths"
    elif metric == "Confirmed Cases":
        out = "title_bar_cases"
    return(out)

@app.callback(
     [Output('testing_plot', 'figure'),
      Output('confirmed_cases_plot', 'figure'),
      Output('deaths_plot', 'figure')],
    [Input('incremental-dropdown', 'value'),
    Input('state_filter', 'children')]
)
def update_graph_testing_rate(incremental, state_filter):
    try:
        state_filter = json.loads(state_filter)["points"][0]["customdata"][0]
    except TypeError:
        state_filter = "Countrywide"

    table = dynamodb_r.Table('bar_plots')
    bar_plots= table.query(
            KeyConditionExpression=Key('state_name').eq(state_filter)
    )['Items'][0]
    incremental = str.lower(incremental) + "_plots"
    out = (bar_plots[incremental]["testing"],
           bar_plots[incremental]["confirmed"],
           bar_plots[incremental]["deaths"])
    return out

def find_state_index(full_state_name):
    return(int(states_conversion_index[full_state_name]))

def add_selected_data(map, index_number="Countrywide"):
    if index_number=="Countrywide":
        return(map)
    else:
        go_map = go.Figure(map.to_dict())
        go_map = go_map.update_traces(selectedpoints=[index_number], selected={"marker":{"opacity": 0.5}})
        return(go_map)

@app.callback(
    Output('state_map_plot', 'figure'),
    [Input('incremental-dropdown', 'value'),
     Input('metrics-dropdown', 'value'),
     Input('clear-geo', "n_clicks")],
     [State('state_filter', 'children')])
def create_map(incremental, metric, n_clicks, state_filter):
    try:
        state_filter = int(json.loads(state_filter)['points'][0]['pointIndex'])
    except TypeError:
        state_filter = "Countrywide"

    if metric == "% Positive":
        col_to_plot = "%Positive"
        colors = "Purpor"
        format_type = ":.1f%"
    elif metric == "Confirmed Cases":
        col_to_plot="Cases"
        colors="Greens"
        format_type = ":,.0f"
    else:
        col_to_plot = "Deaths"
        colors = "Blues"
        format_type = ":,.0f"


    df_to_plot = maps_df[maps_df["Incremental"]==incremental]
    df_to_plot['color_field'] = df_to_plot[col_to_plot]/max(df_to_plot[col_to_plot])

    if metric == "% Positive":
        fig = px.choropleth_mapbox(df_to_plot, geojson=states, locations='id', color='color_field',
                                   color_continuous_scale=colors,
                                   range_color=(0, 0.5),
                                   mapbox_style="carto-positron",
                                   zoom=2.5, center = {"lat": 37.0902, "lon": -95.7129},
                                   opacity=0.5,
                                   hover_data={'State':True,
                                               'id':False,
                                               'color_field':False,
                                                col_to_plot:format_type})
    else:
        fig = px.choropleth_mapbox(df_to_plot, geojson=states, locations='id', color='color_field',
                                   color_continuous_scale=colors,
                                   #range_color=(0, 40),
                                   mapbox_style="carto-positron",
                                   zoom=2.5, center = {"lat": 37.0902, "lon": -95.7129},
                                   opacity=0.5,
                                   hover_data={'State':True,
                                               'id':False,
                                               'color_field':False,
                                                col_to_plot:format_type}
                                  )



    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      coloraxis_showscale=False)
    fig.update_layout(clickmode='event+select')
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] != 'clear-geo':
        fig = add_selected_data(fig, state_filter)

    return(fig)


# Grabs map query
@app.callback(
    Output('state_filter', 'children'),
    [Input('state_map_plot', 'selectedData'),
     Input('clear-geo', 'n_clicks')])
def display_click_data(selectedData, n_clicks):
    #if clickData == None: return(None)
    #return(clickData["points"][0]["customdata"][0])
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'state_map_plot':
        return json.dumps(selectedData, indent=2)
    else:
        return None

# Sets Geo button to Invisible
@app.callback(
    Output('clear-geo', 'className'),
    [Input('state_map_plot', 'selectedData'),
    Input('clear-geo', 'n_clicks')])
def display_click_data(selectedData, n_clicks):
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'clear-geo':
        return('geo_button_hidden')
    elif selectedData != None:
        return("geo_button_visible")
    else:
        return 'geo_button_hidden'


if __name__ == '__main__':
    app.run_server(debug=True)
