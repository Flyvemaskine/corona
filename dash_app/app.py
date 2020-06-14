import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# have to figure out the best way to get data into heroku
state_cases = pd.read_csv("by_state.csv")
states = pd.read_csv("states.csv")
states = states.State.tolist()

metrics = ['confirmed','deaths','recovered',
           'incremental_confirmed','incremental_deaths','incremental_recovered']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
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
                id='metrics-dropdown',
                options=[{'label':metric,'value':metric} for metric in metrics],
                value='confirmed'
            )
        ], style={'width':'49%', 'float':'right', 'display':'inline-block'})
    ], style={
        'borderBottom':'thin lightgrey solid',
        'backgroundColor':'rgb(250, 250, 250)',
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(id='plot-metric-state')
    ])
])

@app.callback(
    Output('plot-metric-state', 'figure'),
    [Input('states-dropdown', 'value'),
     Input('metrics-dropdown', 'value')]
)
def update_graph(state_filter, metric_column_name):
    state_cases_specific = state_cases[state_cases['province_state']==state_filter]

    return {
        'data':[dict(
            x=state_cases_specific['report_date'],
            y=state_cases_specific[metric_column_name],
            type='bar',
            #bar={
            #    'size':15,
            #    'opacity':0.9
                #,'line':{'width':0.5}, 'color':'blue'}

        )],
        'layout':dict(
            xaxis={
                'title':'Date'
            },
            yaxis={
                'title':metric_column_name,
                'type':'linear'
            },
            margin={
                'l': 40, 'b': 40, 't': 10, 'r': 0
            },
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)
