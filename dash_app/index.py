#!/usr/bin/env python3

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

from app import app, server
from apps import by_state, countrywide

app.layout = html.Div([
    dcc.Tabs(id='tab_container', value='countrywide', children=[
        dcc.Tab(label='US - Countrywide', value='countrywide'),
        dcc.Tab(label='State Detail', value='by_state'),
    ]),
    html.Div(id='page_details')
])

@app.callback(Output('page_details', 'children'),
              [Input('tab_container', 'value')])
def render_content(tab):
    if tab == 'countrywide':
        return countrywide.layout
    elif tab == 'by_state':
        return by_state.layout

if __name__ == '__main__':
    app.run_server(debug=True)
