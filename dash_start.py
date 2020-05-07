import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import json
import numpy as np 

url = "https://api.spacexdata.com/v3/launches"
data = requests.get(url)
data_dict = data.json()

# Condensing info from json into a useable/relevant dataframe----------------------------------------------
useable_list = []
useful_fields = ['flight_number', 'mission_name', 'upcoming', 'launch_year', 'launch_date_unix', 
                 'launch_date_utc','launch_date_local', 'is_tentative', 'launch_success', 'details']
for i in range(len(data_dict)):
    useable_dict = {}
    for field in useful_fields:
        useable_dict[field] = data_dict[i][field]
    useable_dict['rocket_name'] = data_dict[i]['rocket']['rocket_name']
    useable_dict['rocket_type'] = data_dict[i]['rocket']['rocket_type']
    for key in data_dict[i]['rocket']['first_stage']['cores'][0].keys():
        useable_dict[key] = data_dict[i]['rocket']['first_stage']['cores'][0][key]
    pay_list = []
    for key in data_dict[i]['rocket']['second_stage']['payloads'][0].keys():
        pay_list.append(key)
    pay_list.remove('orbit_params')
    for key in pay_list:
        useable_dict[key] = data_dict[i]['rocket']['second_stage']['payloads'][0][key]
    for key in data_dict[i]['rocket']['second_stage']['payloads'][0]['orbit_params'].keys():
        useable_dict[key] = data_dict[i]['rocket']['second_stage']['payloads'][0]['orbit_params'][key]
    if data_dict[i]['rocket']['fairings'] is not None:
        for key in data_dict[i]['rocket']['fairings'].keys():
            useable_dict[key] = data_dict[i]['rocket']['fairings'][key]
    else:
        for key in data_dict[0]['rocket']['fairings'].keys():
            useable_dict[key] = np.nan
    for key in data_dict[i]['launch_site'].keys():
        useable_dict[key] = data_dict[i]['launch_site'][key]
    if data_dict[i]['launch_success'] == False:
        for key in data_dict[i]['launch_failure_details'].keys():
            useable_dict[key] = data_dict[i]['launch_failure_details'][key]
    else:
        for key in data_dict[0]['launch_failure_details'].keys():
            useable_dict[key] = np.nan   
    useable_list.append(useable_dict)

important_df = pd.DataFrame.from_dict(useable_list)

# Launch success/failure data grab------------------------------------------------------------
dates = [datetime.strptime(x,'%Y-%m-%dT%H:%M:%S.%fZ') for x in important_df.launch_date_utc]
years = [ x.year for x in dates]
year_fail_df = pd.DataFrame(data = years, columns = ['years'])
year_fail_df['launch_success'] = important_df.launch_success
unique_years = year_fail_df['years'].unique()
launch_dict = {}
for year in unique_years:
    launch_dict[year] = {}
    launch_dict[year]['launches'] = year_fail_df.loc[year_fail_df.years == year, 'years'].count()
    launch_dict[year]['failures'] = year_fail_df.loc[(year_fail_df.years == year) & (year_fail_df.launch_success == False), 'launch_success'].count()
    launch_dict[year]['success'] = year_fail_df.loc[(year_fail_df.years == year) & (year_fail_df.launch_success == True), 'launch_success'].count()
launch_df = pd.DataFrame.from_dict(data = launch_dict, orient = 'index', columns = ['launches', 'failures', 'success'])

fig1 = go.Figure(data=[
    go.Bar(name='failures', x=launch_df.index, y=launch_df.failures, marker_color = 'red'),
    go.Bar(name='successes', x=launch_df.index, y=launch_df.success, marker_color = 'lightslategray')
])

fig1.update_layout(barmode='stack')


app = dash.Dash(__name__)
app.layout = html.Div(
    children = [ 
        html.H1('SpaceX Dashboard', style = {'textAlign': 'center'}), 
        html.P('Explore the raw data'),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in important_df.columns],
            data=important_df.to_dict('records'),
            style_cell = {
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
                'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
            },
            style_table = {
                'overflowX': 'auto',
                'overflowY': 'auto',
                'max_height': '600px',
                'max_width': '800px'
            },
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in important_df.to_dict('rows')
            ],
            tooltip_duration=None
        ),
        html.Div([dcc.Graph(figure = fig1)]),
    ]
)
if __name__ == '__main__':
    app.run_server(debug=True)

