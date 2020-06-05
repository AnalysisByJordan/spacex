import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.io as pio

from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import json
import numpy as np 
import time
import requests_cache

requests_cache.install_cache('spacex_cache', backend='sqlite')

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
    useable_dict['video_link'] = data_dict[i]['links']['video_link']
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

#getting longitude/latitude from Wikipedia API---------------------------------------------
def coord_get(location):
    URL = "https://en.wikipedia.org/w/api.php"
    
    TITLE_PARAMS = {
    "action": "query",
    "format": "json",
    "list": "search",
    "srsearch": location
    }
    TITLE_R = requests.get(url=URL, params=TITLE_PARAMS)
    TITLE_DATA = TITLE_R.json()
    title = TITLE_DATA['query']['search'][0]['title']
    

    LOC_PARAMS = {
    "action": "query",
    "format": "json",
    "titles": title,
    "prop": "coordinates"
    }
    LOC_R = requests.get(url=URL, params=LOC_PARAMS)
    LOC_DATA = LOC_R.json()
    PAGES = LOC_DATA['query']['pages']
    
    for k, v in PAGES.items():
        lat = v['coordinates'][0]['lat']
        long = v['coordinates'][0]['lon']
    
    time.sleep(.2)
    return {'lat' : lat, 'long': long}


coord_list = []
for site in important_df.site_name_long:
    coord_list.append(coord_get(site))

important_df['coords'] = coord_list

unique_locations = important_df.site_name_long.unique()
geo_dict = {}
for location in unique_locations:
    geo_dict[location] = {}
    geo_dict[location]['coords'] = list(important_df[important_df['site_name_long'] == location].coords)[0]
    geo_dict[location]['launches'] = important_df.loc[important_df.site_name_long == location, 'site_name_long'].count()

lats = []
longs = []
places = []
for k, v in geo_dict.items():
    lats.append(v['coords']['lat'])
    longs.append(v['coords']['long'])
    places.append({'Place' : k, 'Total Launches' : v['launches']})

important_df = important_df.drop(['coords'], axis=1)

mapbox_access_token = "pk.eyJ1Ijoic3RlZWxtYXN0ZXI5NSIsImEiOiJja2EzMjN4bGgwanJ4M2xyM3ZyNHdodHFjIn0.orGsUUA5jJNGm3YvpklUPw"
fig0 = go.Figure(go.Scattermapbox(
        lat=lats,
        lon=longs,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=9
        ),
        text=places,
    ))

fig0.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=8.71,
            lon=-167.73
        ),
        pitch=0,
        zoom=1
    ),
    title = 'Location of SpaceX Launches',
    template = "seaborn"
)





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
fig1.update_layout(
    barmode='stack',
    title = 'Rocket Launch Success/Failures Over Time',
    template = "seaborn"
    )


#Launch Customers Pie Chart-------------------------------------------------------------------
customers = important_df.customers
all_customers = []
for cust in customers:
    for c in cust:
        all_customers.append(c)
customers_set = set(all_customers)

customers_dict = {}
for item in customers_set:
    customers_dict[item] = all_customers.count(item)

customers_df = pd.DataFrame.from_dict(data = customers_dict, orient = 'index', columns = ['Launches'])

fig2 = px.pie(customers_df, values='Launches', names=customers_df.index, title='SpaceX Customers and Number of Launches')
fig2.update_traces(textposition='inside', textinfo='percent+label')

#Launches by Nation----------------------------------------------------------------------------
nations = important_df.nationality
unique_nations = nations.unique().tolist()
nations_list = nations.tolist()

nations_dict = {}
for item in unique_nations:
    nations_dict[item] = nations_list.count(item)

nations_df = pd.DataFrame.from_dict(data = nations_dict, orient = 'index', columns = ['Nations'])
fig3 = px.pie(nations_df, values='Nations', names=nations_df.index, title='Nation Launches')
fig3.update_traces(textposition='inside', textinfo='percent+label')


#Creating dictionary for video viewing. Altering nomenclature in video links to include 'embed'...
video_df = important_df.loc[important_df['video_link'].notnull(), ['mission_name', 'video_link']]

def youtube_link(word):
    if 'feature' in word:
        for i in range(0,len(word)):
            if i < len(word) - 1 :
                if (word[i] == "v") & (word[i+1] == '='):
                    first_place = i + 2
                if word[i] == '&':
                    last_place = i
    elif 'youtube' in word:
        last_place = len(word)
        for i in range(0,len(word)):
            if word[i] == "=":
                first_place = i + 1
            if word[i] == '&':
                last_place = i + 1
    elif 'youtu.be' in word:
        last_place = len(word)
        for i in range(0,len(word)):
            if word[i] == 'e':
                first_place = i + 2
    return 'https://www.youtube.com/embed/' + word[first_place: last_place]

video_df['video_link'] = video_df['video_link'].map(youtube_link)
first_video_df = video_df.rename({'mission_name' : 'label', 'video_link': 'value'}, axis = 'columns')
first_video_dict = first_video_df.to_dict('records')





#App Building------------------------------------------------------------------------------------
app = dash.Dash(external_stylesheets=[dbc.themes.SUPERHERO])
app.layout = html.Div(children = [
    html.H1('SpaceX Dashboard', style = {'textAlign': 'center'}),
    dbc.Tabs(children = [
        dbc.Tab(label='General Metrics', children=[    
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H1("General Information", style = {'textAlign': 'center'}),
                        html.Div(
                        [   html.Div([html.P("Completed Missions: "), html.Div("95", className = 'info-num')], className = 'info'),
                            html.Div([html.P("Planned Missions Coming Up: "), html.Div("13", className = 'info-num')], className = 'info'),
                            html.Div([html.P("Number of Misions with a Landing Intent: "), html.Div("40", className = 'info-num')], className = 'info'),
                            html.Div([html.P("Number of Missions with a Successful Land: "), html.Div("20", className = 'info-num')], className = 'info'),
                        ], className = 'info-div'),
                    ], width = {"size": 8, "offset": 2}, className = 'gen-info')
                ]),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(figure = fig1), width = 4),
                        dbc.Col(dcc.Graph(figure = fig2), width = 4),
                        dbc.Col(dcc.Graph(figure = fig3), width = 4)
                    ]),
                dbc.Row(dbc.Col(dcc.Graph(figure = fig0), width = 4, style = {'height' : '100px'}), 
                    style = {
                        "paddingTop": "10px",
                        "paddingLeft": "10px"
                        })
            ]),
        ]),
        dcc.Tab(label='Launch Visuals', className = 'custom-tab', selected_className = 'custom-tab--selected', children=[  
            html.Div(className = 'video-page', children = [
                dbc.Row([
                    dbc.Col([
                        html.H2("Please Choose A Mission"), 
                        dcc.Dropdown(className = 'video-dropdown', id='options', options=first_video_dict),])
                ]),
                dbc.Row([dbc.Col([html.Iframe(id='frame', src=None)])
                ])
            ])
        ]),
        dcc.Tab(label='Raw Data', className = 'custom-tab', selected_className = 'custom-tab--selected', children=[
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
                { column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in important_df.to_dict('rows')
            ],
            tooltip_duration=None
        ),
        ])
    ])
])

@app.callback(
    Output('frame', 'src'),
    [Input('options', 'value')]
)
def change_video(option):
    return option


if __name__ == '__main__':
    app.run_server(debug=True)

