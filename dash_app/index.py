#!/usr/bin/env python3

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

from app import app, server
from apps import by_state, countrywide

incrementals = ["Cumulative", "Incremental"]

blank_graph={'data':[], 'layout':{'margin':{"l": 0, "b": 0, "t": 0, "r": 0}}}


app.layout = html.Div([
    html.Div([
    # Row 1 Div
        html.H3("US COVID Tracking", style={'text-align':'center'})
    ], className="pretty_container"),

    # Row 2 Div
    html.Div([
        html.Div([
            html.P("This dashboard is intended to track the progress of COVID through the United States. Case reports are sourced daily from JHU and testing data is provided by the COVID tracking project",style={'display':'inline-block'})
        ],style={'width':'100%', 'display':'inline-block'})
    ], className="pretty_container"),

    # Row 3 Div
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='states-dropdown',
                    options=[{'label':incremental, 'value':incremental} for incremental in incrementals],
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
        ], className="pretty_container"),


    # Row 3
    html.Div([
        html.Div([
            html.P("Title", className="title_bar"),
            dcc.Graph(figure=blank_graph, style={'height':'30vh'})
        ],className='graph_container',style={'width':'43vw',  'float':'left',  'display':'inline-block'}),
        html.Div([
            html.P("Title", className='title_bar'),
            dcc.Graph(figure=blank_graph, style={'height':'30vh'})
        ],className='graph_container',style={'width':'43vw',  'float':'right',  'display':'inline-block'})
    ]),
    html.Div([
        html.Div([
            html.P("Title", className="title_bar"),
            dcc.Graph(figure=blank_graph, style={'height':'30vh'})
        ],className='graph_container',style={'width':'43vw',  'float':'left',  'display':'inline-block'}),
        html.Div([
            html.P("Title", className='title_bar'),
            dcc.Graph(figure=blank_graph, style={'height':'30vh'})
        ],className='graph_container',style={'width':'43vw',  'float':'right',  'display':'inline-block'})
    ])


],id="main_container")



if __name__ == '__main__':
    app.run_server(debug=True)
