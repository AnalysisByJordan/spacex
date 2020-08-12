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

important_df = pd.read_pickle(r'C:\Users\steelmaster95\OneDrive\Programming\Data_Science\Python\spacex_app_v2\data_df.pkl')

#Basic Launches Information
completed_missions = important_df[important_df.upcoming == False].flight_number.count()
upcoming_missions = important_df[important_df.upcoming == True].flight_number.count()
landing_intent_missions = important_df[important_df.landing_intent == True].flight_number.count()
land_success_missions = important_df[important_df.land_success == True].flight_number.count()

#graph styling variables
plot_color = 'rgb(62, 64, 70)'
paper_color = 'rgb(62, 64, 70)'
font_dict = dict(size=14, color= 'rgb(198, 200, 209)')

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
            lon=-130.73
        ),
        pitch=0,
        zoom=1
    ),
    title = 'Location and Quantity of SpaceX Launches',
    template = "seaborn",
    paper_bgcolor = paper_color,
    plot_bgcolor = plot_color,
    font= font_dict
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
    template = "seaborn",
    paper_bgcolor = paper_color,
    plot_bgcolor = plot_color,
    font= font_dict
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
fig2.update_layout(
    paper_bgcolor = paper_color,
    plot_bgcolor = plot_color,
    font = dict(color= 'rgb(198, 200, 209)')
    )

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
fig3.update_layout(
    paper_bgcolor = paper_color,
    plot_bgcolor = plot_color,
    font = dict(size=14, color= 'rgb(198, 200, 209)')
    )


#Creating dictionary for video viewing. Altering nomenclature in video links to include 'embed'...
video_df = important_df.loc[important_df['video_link'].notnull(), ['launch_year','mission_name', 'video_link','is_tentative', 'launch_success', 
'details', 'landing_intent', 'land_success', 'landing_type', 'landing_vehicle', 'nationality', 'manufacturer', 
'payload_id', 'payload_type', 'payload_mass_lbs', 'reference_system', 'semi_major_axis_km', 'eccentricity',
'periapsis_km','apoapsis_km','inclination_deg','period_min','lifespan_years','regime', 'site_name_long']]

video_df_items = ['is_tentative', 'launch_success', 
'details', 'landing_intent', 'land_success', 'landing_type', 'landing_vehicle', 'nationality', 'manufacturer', 
'payload_id', 'payload_type', 'payload_mass_lbs', 'reference_system']
#,'semi_major_axis_km', 'eccentricity',
#'periapsis_km','apoapsis_km','inclination_deg','period_min','lifespan_years','regime', 'site_name_long'



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
video_dict = video_df.groupby('launch_year').apply(lambda s: s.drop('launch_year', 1).to_dict('records')).to_dict()

#Row creation function for individual mission data
def cardDiv(updateVar):
    return html.Div(className = 'detail-block', children = [
                html.Div(className = 'detail-var', children = updateVar),
                html.Div(id = updateVar)
            ])

cardDivs = []
for item in video_df_items:
    cardDivs.append(cardDiv(item))

def callbackOutputs(idVar):
    return Output(idVar, 'children')

missionCallbacks = []
for item in video_df_items:
    missionCallbacks.append(callbackOutputs(item))

#manufacturer - orbit graph creation
manufacturer_reference = important_df[['manufacturer', 'orbit']]
manufacturers = manufacturer_reference.manufacturer.unique()
manufacturers = [i for i in manufacturers if i] 
orbits = manufacturer_reference.orbit.unique()
orbits_dict = {}
for item in manufacturers:
    orbits_dict[item] = {}
    for orbit in orbits:
        orbits_dict[item][orbit] =  manufacturer_reference[(manufacturer_reference.manufacturer == item) & (manufacturer_reference.orbit == orbit)].orbit.count()



#App Construction-----------------------------------------------------------------------------------
app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG])
app.layout = html.Div(className = 'main-div', children = [
    html.H1('SpaceX Dashboard', style = {'textAlign': 'center'}),
    dbc.Tabs(children = [
        dbc.Tab(label='General Metrics', children=[    
            html.Div([
                html.Div([
                    html.Div([
                        html.H1("General Information", style = {'textAlign': 'center'}),
                        html.Div(
                        [   html.Div([html.P("Completed Missions: "), html.Div(completed_missions, className = 'info-num')], className = 'info'),
                            html.Div([html.P("Planned Missions Coming Up: "), html.Div(upcoming_missions, className = 'info-num')], className = 'info'),
                            html.Div([html.P("Number of Misions with a Landing Intent: "), html.Div(landing_intent_missions, className = 'info-num')], className = 'info'),
                            html.Div([html.P("Number of Missions with a Successful Land: "), html.Div(land_success_missions, className = 'info-num')], className = 'info'),
                        ], className = 'info-div'),
                    ], className = 'gen-info')
                ]),
                html.Div(className = 'graph-grid', children = 
                    [
                        html.Div(dcc.Graph(figure = fig1), className = 'small_graph'),
                        html.Div(dcc.Graph(figure = fig2), className = 'small_graph'),
                        html.Div(dcc.Graph(figure = fig3), className = 'small_graph'),
                        html.Div(dcc.Graph(figure = fig0), className = 'small_graph'), 
                        html.Div(className = 'manu_dropdown', children = [
                            dbc.Label("Choose a Manufacturer", html_for = "orbit_manu_dd"),
                            dcc.Dropdown(
                                options = [{'label': k, 'value': k} for k in manufacturers], id = 'orbit_manu_dd', value = 'SpaceX')
                        ]),
                    html.Div(dcc.Graph(id='manu_graph'), className = 'large_graph')
                ]),
            ], className = "Tab_One"),
        ]),
        dcc.Tab(label='Launch Visuals', className = 'custom-tab', selected_className = 'custom-tab--selected', children=[  
            html.Div(className = 'video-page', children = [
                html.Div(className = 'selection_row', children = [
                    html.Div(className = 'selection-box', children = [
                        html.H2("Mission Selection"),
                        html.Div(className = "mission_selection", children = [
                            html.Div(className = 'launch_year_dropdown', children = [
                                dbc.Label("Choose a Launch Year", html_for = "launches_years"), 
                                dcc.Dropdown(className = 'video-dropdown', id='launches_years', options=[{'label': k, 'value': k} for k in video_dict.keys()], value = '2016'),
                            ]),
                            html.Div(className = 'middle-space'),
                            html.Div(className = 'mission_dropdown', children = [
                                dbc.Label("Choose a Mission", html_for = "missions"), 
                                dcc.Dropdown(className = 'video-dropdown', id = 'missions', value = 'SES-9')
                            ]),
                        ])
                    ])
                ]),
                html.Div(className = 'lower-half', children = [
                    html.Div(className = 'video-div', children = [
                        html.H2('Mission Video'),
                        html.Iframe(className = "mission_video", id='frame', src=None)
                    ]),
                    html.Div(className = 'middle-piece'),
                    html.Div(className = 'video-details', children = [
                        html.H2(className = 'mission-h1', children = 'Mission Details'),
                        html.Div(className = 'card-divs', children = cardDivs),
                    ]),
                ]),
            ])
        ]),
        dcc.Tab(label='Raw Data', className = 'custom-tab', selected_className = 'custom-tab--selected', children=[
            html.Div(className = 'dt-div', children = [
                html.H2('Explore the raw data'),
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in important_df.columns],
                    data=important_df.to_dict('records'),
                    style_cell = {
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': 0,
                        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                        'color': 'white',
                        'backgroundColor': 'rgb(79, 81, 88)'
                    },
                    style_table = {
                        'overflowX': 'auto',
                        'overflowY': 'auto',
                        'max_height': '80vh',
                        'max_width': '95vw'
                    },
                    style_header={
                        'backgroundColor': 'rgb(58, 60, 65)',
                        'fontWeight': 'bold'
                    },
                    tooltip_data=[
                        { column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in important_df.to_dict('rows')
                    ],
                    tooltip_duration=None
                ),
                html.Div(className = 'bot-div')
            ])
        ])
    ])
])

@app.callback(
    Output('manu_graph', 'figure'),
    [Input('orbit_manu_dd', 'value')]
)
def select_orbit_manu(selected_manu):
    df = pd.DataFrame.from_dict(orbits_dict[selected_manu], orient='index', columns = ['Launch Contracts'])
    df['Orbit Type'] = df.index
    fig = px.bar(df, x = 'Orbit Type', y = 'Launch Contracts', title = 'Payload Manufacturer vs. Orbit Type')
    fig.update_layout(
    paper_bgcolor = paper_color,
    plot_bgcolor = plot_color,
    font = dict(size=14, color= 'rgb(198, 200, 209)')
    )
    return fig

@app.callback(
    Output('missions', 'options'),
    [Input('launches_years', 'value')]
)
def select_mission(selected_year):
    return [{'label': v['mission_name'], 'value' : v['mission_name']} for v in video_dict[selected_year]]

@app.callback(
    Output('frame', 'src'),
    [Input('missions', 'value'),
    Input('launches_years', 'value')]
)
def select_video(mission_value, year_value):
    for key in video_dict[year_value]:
        if key['mission_name'] == mission_value:
            src = key['video_link']
    return src

@app.callback(
    [Output('is_tentative', 'children'),
    Output('launch_success', 'children'),
    Output('details', 'children'),
    Output('landing_intent', 'children'),
    Output('land_success', 'children'),
    Output('landing_type', 'children'),
    Output('landing_vehicle', 'children'),
    Output('nationality', 'children'),
    Output('manufacturer', 'children'),
    Output('payload_id', 'children'),
    Output('payload_type', 'children'),
    Output('payload_mass_lbs', 'children'),
    Output('reference_system', 'children')],
    [Input('missions', 'value'),
    Input('launches_years', 'value')]
)
def missionDetail(mission_value, year_value):
    for key in video_dict[year_value]:
        if key['mission_name'] == mission_value:
            tentativeVar = key['is_tentative']
            successVar = key['launch_success']
            failReasonVar = key['details']
            intentVar = key['landing_intent']
            landSucVar = key['land_success']
            landTypeVar = key['landing_type']
            landVehVar = key['landing_vehicle']
            nationVar = key['nationality']
            manuVar = key['manufacturer']
            payIdVar = key['payload_id']
            payTypeVar = key['payload_type']
            payMassVar = key['payload_mass_lbs']
            referenceVar = key['reference_system']
    return "{}".format(tentativeVar), "{}".format(successVar), "{}".format(failReasonVar), "{}".format(intentVar), "{}".format(landSucVar), "{}".format(landTypeVar), "{}".format(landVehVar), "{}".format(nationVar), "{}".format(manuVar), "{}".format(payIdVar), "{}".format(payTypeVar), "{}".format(payMassVar), "{}".format(referenceVar),

if __name__ == '__main__':
    app.run_server(debug=True)

