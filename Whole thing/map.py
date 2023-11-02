import geopandas as gpd
import plotly.express as px
import pandas as pd

def column_mapping(df, column_mapping, start_data_list, stop_data_list):

    # Map all the start and end columns to general names.
    # We want one large dataframe with combined data, so we are able to measure usage in our scatter
    start_data = df[start_data_list]
    start_data = start_data.rename(columns=column_mapping)

    stop_data = df[stop_data_list]
    stop_data = stop_data.rename(columns=column_mapping)

    # Concat our stop and end dataframes together
    combined_data = pd.concat([start_data, stop_data], ignore_index=True)
    return combined_data

def create_bluebike_gdf(combined_data, shp_folder_path, crs_latlong, lat_col, lon_col):
    # Read our Boston Neighborhoods zip shapefile and create a GeoDataframe
    gdf = gpd.read_file(shp_folder_path)

    # Reproject the Boston Neighborhoods GeoDataframe to the new crs *So it matches our bike station lat and long points!*
    gdf = gdf.to_crs(crs_latlong)

    # Save the transformed shapefile with latitude and longitude coordinates and create an associating GeoDataframe
    gdf.to_file('shapefile_latlong.shp')
    neighborhoods_gdf = gpd.read_file('shapefile_latlong.shp')

    # Create a GeoDataframe from our combined bike data using point geometry and our latitude and longitude points
    combined_gdf = gpd.GeoDataFrame(combined_data,
                                    geometry=gpd.points_from_xy(combined_data[lon_col],
                                                                combined_data[lat_col]))

    # Make sure both of our GeoDataFrames are projected on the same CRS
    combined_gdf.crs = neighborhoods_gdf.crs

    # Use spatial join to get a new dataframe with the bike stations in the appropriate neighborhoods
    # Note: I couldn't find a shapefile of All the Boston neighborhoods available in the bike dataset,
    # so certain neighborhood are not accommodated, like Cambridge.
    combined_neighborhoods = gpd.sjoin(combined_gdf, neighborhoods_gdf, how='right', predicate='within')

    # Collect our neighborhood names and drop any rows with NA values
    combined_neighborhoods = combined_neighborhoods.dropna(how='any')
    return combined_neighborhoods

def create_scatter_mapbox_bluebike(desired_neighborhood, station_counts, lat_col, lon_col):
    '''

    :param desired_neighborhood:
    :param start_date:
    :param end_date:
    :param geo_bike_df:
    :return:
    '''

    # if station_counts.empty:
    #     title = f'No data available for the selected neighborhood: {desired_neighborhood}'
    # else:
    #     title = f'Blue Bike Usage in {desired_neighborhood}'

    # Create a scatter mapbox
    fig = px.scatter_mapbox(station_counts,
                            lat=lat_col,
                            lon=lon_col,
                            text='station name',
                            hover_name='station name',
                            color='usage_count',
                            color_continuous_scale='Viridis',
                            title=f'Blue Bike Usage in {desired_neighborhood}')

    fig.update_layout(mapbox_style='stamen-terrain')
    fig.update_layout(mapbox_center_lat=station_counts[lat_col].mean(),
                      mapbox_center_lon=station_counts[lon_col].mean())
    fig.update_layout(mapbox_zoom=12)

    # Show the scatter mapbox
    return fig