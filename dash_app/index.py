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
from app import app, server
#from apps import by_state, countrywide
from urllib.request import urlopen
import plotly.express as px

# Dropdowns
incrementals = ["Cumulative", "Incremental"]
metrics_list = ["% Positive", "Confirmed Cases", "Deaths"]

# Mongo stuff general
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

with urlopen("https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"
) as response:
    states = json.load(response)

by_state_collection = db['plots']
maps_collection = db['maps']

states_conversion = pd.read_csv("states.csv").set_index(["Abbreviation"])
states_conversion_dict = states_conversion.to_dict()["State"]


blank_graph={'data':[], 'layout':{'margin':{"l": 0, "b": 0, "t": 0, "r": 0}}}

app.layout = html.Div([
    html.Div([
    # Row 1 Title
        html.H3("US COVID Tracking")
    ], className="row_one_container"),

    # Row 2: About
    html.Div([
        html.Div([
            html.P("This dashboard is intended to track the progress of COVID through the United States. Case reports are sourced daily from JHU and testing data is provided by the COVID tracking project",style={'display':'inline-block'})
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
    ], className='graph_grid'),
    html.Div(id='state-filter', style={'display':'none'})


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
    first_label = [incremental + " " + metric + " - " + state_name]
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
    mongo_query_out = [doc for doc in by_state_collection.find({"state_name":state_filter}, {'_id':0})]
    incremental = str.lower(incremental) + "_plots"
    out = (mongo_query_out[0][incremental]["testing"], mongo_query_out[0][incremental]["confirmed"], mongo_query_out[0][incremental]["deaths"])
    return out

@app.callback(
    Output('state_map_plot', 'figure'),
    [Input('incremental-dropdown', 'value'),
     Input('metrics-dropdown', 'value')])
def create_map(incremental, metric):
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


    mongo_query_out = [doc for doc in maps_collection.find({"Incremental":incremental}, {'_id':0})]
    df_to_plot = pd.DataFrame(mongo_query_out)
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
    fig.update_layout(clickmode='event')
    return(fig)


@app.callback(
    Output('state_filter', 'children'),
    [Input('state_map_plot', 'clickData'),
     Input('clear-geo', 'n_clicks')])
def display_click_data(clickData, n_clicks):
    #if clickData == None: return(None)
    #return(clickData["points"][0]["customdata"][0])
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'state_map_plot':
        return json.dumps(clickData, indent=2)
    else:
        return None

@app.callback(
    Output('clear-geo', 'className'),
    [Input('state_map_plot', 'clickData'),
     Input('clear-geo', 'n_clicks')])
def display_click_data(clickData, n_clicks):
    #if clickData == None: return(None)
    #return(clickData["points"][0]["customdata"][0])
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'state_map_plot':
        return 'geo_button_visible'
    else:
        return 'geo_button_hidden'



if __name__ == '__main__':
    app.run_server(debug=True)
