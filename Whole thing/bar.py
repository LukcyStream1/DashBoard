import plotly.express as px


def make_bar_popularity(df, col_name, count_name, threshold=10):
    '''
    creates a bar chart of the top x items given a dataframe and a specified column
    :param df: a dataframe containing the column to turn into a bar chart
    :param col_name: a string with the name of the column to groupby
    :param count_name: what to name the counted values
    :param threshold: top x bars to show on the final bar chart output (default is top 10)
    :return fig: the completed plotly bar chart
    '''

    # Count the instances of each category
    count_data = df[col_name].value_counts().reset_index()
    count_data.columns = [col_name, count_name]

    # use sort values to get the top X values
    count_data = count_data.sort_values(by=count_name, ascending=False).head(threshold)

    # create the bar chart
    fig = px.bar(count_data, x=col_name, y=count_name, text=count_name)

    return fig
