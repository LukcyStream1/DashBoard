from dash import Dash, dcc, html, Input, Output
import math
import pandas as pd
import sankey
import bar
import calendar
import map


def main():
    # import and clean the dataframe
    #bike_df = pd.read_csv('combined_final.csv')
    bike_df = pd.read_csv('202208-bluebikes-tripdata.csv')
    bike_df['starttime'] = pd.to_datetime(bike_df['starttime'])
    bike_df['stoptime'] = pd.to_datetime(bike_df['stoptime'])

    # drop columns wit NA values
    bike_df.dropna(how='any', inplace=True)

    # create a year column
    bike_df['year'] = bike_df['starttime'].dt.year

    # create a month column and change from numerical to calendar names
    bike_df['month'] = bike_df['starttime'].dt.month
    bike_df['month'] = bike_df['month'].apply(lambda x: calendar.month_name[x])

    # prepare the data for the geo map
    column_mapping = {
        'start station longitude': 'station longitude',
        'start station latitude': 'station latitude',
        'starttime': 'time',
        'start station name': 'station name',
        'end station longitude': 'station longitude',
        'end station latitude': 'station latitude',
        'stoptime': 'time',
        'end station name': 'station name'
    }
    start_data_list = ['start station longitude', 'start station latitude', 'starttime', 'start station name']
    stop_data_list = ['end station longitude', 'end station latitude', 'stoptime', 'end station name']
    combined_data = map.column_mapping(bike_df, column_mapping, start_data_list, stop_data_list)

    # define the folder path for the Boston neighborhoods zip shapefile
    shp_folder_path = 'Census2020_BG_Neighborhoods'

    # Define the  crs with latitude and longitude
    crs_latlong = "EPSG:4326"

    # define the lat and lon column names
    lon_col = 'station longitude'
    lat_col = 'station latitude'

    geo_bike_df = map.create_bluebike_gdf(combined_data, shp_folder_path, crs_latlong, lat_col, lon_col)
    geo_bike_df['time'] = pd.to_datetime(geo_bike_df['time'])
    # print(geo_bike_df.columns)

    # step 1: define the app object
    app = Dash(__name__)


    # step 2: define the layout
    app.layout = html.Div([
        html.H1('BlueBike Dashboard',
                style= {'textAlign': 'center', 'font-family': 'Impact', 'font-size': '42px',
                        'color': 'CornflowerBlue'}),

        html.Div([

                # create one div for our sankey diagram and the checklist
                html.Div([
                    html.H2('BlueBike Subscriber Type to Monthly Usage'),
                    dcc.Graph(id='sankey'),
                    dcc.Checklist(id='sankey_year',
                                  options=bike_df['year'].unique(),
                                  value=[bike_df['year'].min()],
                                  inline=True),
                    html.Br()],
                style={"border-bottom":"2px black solid"}),

                # create a second div for the bar chart and date picker
                html.Div([
                    html.H2('Top 10 Most Popular Start Stations'),
                    dcc.Graph(id='barchart'),
                    dcc.DatePickerRange(
                        id='bar_date_picker',
                        min_date_allowed=bike_df['starttime'].min(),
                        max_date_allowed=bike_df['starttime'].max(),
                        end_date=bike_df['starttime'].max(),
                        start_date=bike_df['starttime'].min(),
                        display_format='YYYY-MM-DD')],
                style={})

        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle'}),

        html.Div([

            # create a third div for the map and radio items selector
            html.Div([
                html.H2('BlueBike Map'),
                dcc.Graph(id='boston_map'),
                dcc.RadioItems(
                    id='neighborhood_selection',
                    options= geo_bike_df['BlockGr202'].unique(),
                    value='Mission Hill',
                    inline=True),
                dcc.DatePickerRange(
                    id='map_date_picker',
                    min_date_allowed=geo_bike_df['time'].min(),
                    max_date_allowed=geo_bike_df['time'].max(),
                    end_date=geo_bike_df['time'].max(),
                    start_date=geo_bike_df['time'].min(),
                    display_format='YYYY-MM-DD'),
                html.Br()],
                style={"border-bottom":"2px black solid"}),

            # create a fourth div for the start and stop station selector and trip duration display
            html.Div([
                html.H2('Average Trip Duration Calculator'),
                html.Br(),
                html.Br(),
                html.H2(id='trip_duration'),
                html.Br(),
                html.Br(),
                dcc.Dropdown(id='station_1',
                             options=bike_df['start station name'].unique(),
                             value='Northeastern University - North Parking Lot',
                             clearable=False),
                dcc.Dropdown(id='station_2',
                             options=bike_df['start station name'].unique(),
                             value='Northeastern University - North Parking Lot',
                             clearable=False)],
                style={}),

        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'})
    ], style={'backgroundColor': 'AliceBlue'})


    @app.callback(
        Output('sankey', 'figure'),
        Input('sankey_year', 'value'),
    )
    def update_sankey(selected_years):
        '''
        uses the callback wrapper to create an updated sankey diagram for the selected year(s)
        :param selected_years: a list of selectred years
        :return fig: the updated plotly sankey figure
        '''
        # check to ensure that selected_years is a list, otherwise the program will not run
        if not isinstance(selected_years, list):
            selected_years = [selected_years]

        # filter the data on the years
        sankey_df = bike_df[bike_df['year'].isin(selected_years)]

        # call make_sankey to update the graph and return the figure
        fig = sankey.make_sankey(sankey_df, *['usertype', 'month'])
        fig.update_layout(
            paper_bgcolor='AliceBlue',
            plot_bgcolor='AliceBlue')
        return fig

    @app.callback(
    Output('barchart', 'figure'),
    [Input('bar_date_picker', 'start_date'),
     Input('bar_date_picker', 'end_date')]
    )
    def update_barchart(start_date, end_date):
        '''
        uses the callback wrapper to create an updated station popularity bar chart for the selected dates
        :param start_date: the datetime object that signifies the users beginning date selection
        :param end_date: the datetime object that signifies the users end date selection
        :return fig: the updated plotly bar chart figure
        '''
        # convert start and end dates to datetime objects
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # update the dataframe
        bar_df = bike_df[(bike_df['starttime'] >= start_date) & (bike_df['starttime'] <= end_date)]

        fig = bar.make_bar_popularity(bar_df, 'start station name', 'number of trips')
        fig.update_layout(
            paper_bgcolor='AliceBlue',
            plot_bgcolor='AliceBlue')

        return fig

    @app.callback(
        Output('boston_map', 'figure'),
        [Input('neighborhood_selection', 'value'),
        Input('map_date_picker', 'start_date'),
        Input('map_date_picker', 'end_date')]
    )
    def update_map(desired_neighborhood, start_date, end_date):
        '''
        uses the callback wrapper to update the geomap on the dashboard given both a selected neighborhood and date
        inputs
        :param neighborhood: the string signifying the user's singular neighborhood input
        :param start_date: the datetime object that signifies the users beginning date selection
        :param end_date:the datetime object that signifies the users end date selection
        :return fig: the updated plotly geomap figure
        '''
        # ensure the start and end dates are datetime objects
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        print(f'desired_neighborhood: {desired_neighborhood}')
        print(f'start_date: {start_date}')
        print(f'end_date: {end_date}')

        # update the dataframe
        # Filter data based on the selected neighborhood
        neighborhood_condition = geo_bike_df['BlockGr202'] == desired_neighborhood
        #print(neighborhood_condition)

        # Filter data based on start and end date
        date_condition = (geo_bike_df['time'] >= start_date) & (geo_bike_df['time'] <= end_date)

        # Apply both conditions to filter the data
        filtered_data = geo_bike_df[neighborhood_condition & date_condition]

        # Group by station name and count usages
        station_columns = ['station name', 'station latitude', 'station longitude']
        station_counts = filtered_data.groupby(station_columns).size().reset_index(name='usage_count')

        # 临时设置显示的最大列数为 None

        pd.set_option('display.max_columns', None)

        # 打印 DataFrame
        # print(filtered_data.head(5))

        # 恢复显示的最大列数为默认值（例如，20）
        # pd.set_option('display.max_columns', 20)

        print(station_counts)

        fig = map.create_scatter_mapbox_bluebike(desired_neighborhood, station_counts, lat_col='station latitude',
                                                 lon_col='station longitude')
        fig.update_layout(
            paper_bgcolor='AliceBlue',
            plot_bgcolor='AliceBlue')
        return fig


    @app.callback(
        Output('trip_duration', 'children'),
        Input('station_1', 'value'),
        Input('station_2', 'value')
    )
    def calculate_avg_duration(start_station, end_station):
        '''
        calculates the average trip duration given two station inputs, provided that a trip exists between those two
        stations
        :param start_station: the string signifying the user's selected start station name
        :param end_station: the string signifying the user's selected end station name
        :return: a string with the average expected duration of the trip
        '''
        if start_station == end_station:
            return 'Start and End station cannot be the same'
        duration_df = bike_df[(bike_df['start station name'] == start_station) &
                              (bike_df['end station name'] == end_station)]

        avg_duration = duration_df['tripduration'].mean()
        if math.isnan(avg_duration):
            return 'Sorry no trips of that type!'
        hours = int(avg_duration // 3600)
        minutes = int((avg_duration - 3600*hours) // 60)
        seconds = int(avg_duration % 60)
        return f'{hours} hrs, {minutes} mins, {seconds} secs'
    app.run(debug=True)

main()