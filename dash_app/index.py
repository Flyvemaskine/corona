#!/usr/bin/env python3

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

from app import app, server
from apps import by_state, countrywide

incrementals = ["Cumulative", "Incremental"]

blank_graph={'data':[], 'layout':{'margin':{"l": 0, "b": 0, "t": 0, "r": 0}}}

metrics_list = ["% Positive", "Confirmed Cases", "Deaths"]


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
        html.Button('Clear Geography Filter', id='clear-geo', className='geo_button_hidden'),
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
            dcc.Graph(figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="positive_graph_label", className="title_bar_positive"),
            dcc.Graph(figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="cases_graph_label", className="title_bar_cases"),
            dcc.Graph(figure=blank_graph, className='regular_graph')
        ],className="graph_container"),
        html.Div([
            html.P("Title", id="deaths_graph_label", className='title_bar_deaths'),
            dcc.Graph(figure=blank_graph, className='regular_graph')
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
    Input('metrics-dropdown', 'value')]
)
def update_title_bar_labels(incremental, metric):
    first_label = [incremental + " " + metric]
    out = [(incremental + " " +  metric) for metric in metrics_list]
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




if __name__ == '__main__':
    app.run_server(debug=True)
