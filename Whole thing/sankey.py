"""
File: sankey.py
Description:  A library for building sankey diagrams from a dataframe
Author: Gino Giorgianni
Date: October 8, 2023
"""
import pandas as pd
import plotly.graph_objects as go
pd.options.mode.chained_assignment = None

def _df_stacking(df, cols, values):
    """
    Creates a stacked dataframe and aggregates values so that the output is ready to be made into a sankey diagram

    :param df: a dataframe containing the columns and values that need to be stacked
    :param cols: a list of columns to be iterated over in order to be stacked
    :param values: a string containing the name of the values column
    :return final_df: a stacked and aggregated dataset
    """

    # assert that at least two columns were provided
    assert (len(cols) >= 2)

    # initialize an empty dataframe to append to
    result_df = pd.DataFrame()

    # iterate through the enumerated cols list
    for count, col in enumerate(cols):

        # ensure that we don't hit an index error by staying before len(cols)-1
        if count < len(cols) - 1:

            # create a temporary dataframe with the current column and next column renamed to 'src' and 'targ'
            # respectively
            temp_df = df[[col, cols[count + 1], values]]
            temp_df.columns = ['src', 'targ', 'values']

            # concatenate the previous dataframe together with the current temporary one
            result_df = pd.concat([result_df, temp_df], axis=0, ignore_index=True)

    # now that all the columns are stacked, we can aggregate the values of same src+targ pairs
    final_df = result_df.groupby(['src', 'targ']).agg({'values': 'sum'}).reset_index()

    return final_df


def _code_mapping(df, src, targ):
    """
    Creates an integer coding for the unique labels in each column of the dataframe (this is necessary for plotly to
    build the sankey diagram
    :param df: the dataframe being used
    :param src: the source column name
    :param targ:the target column name
    :return df: the new coded dataframe
            labels: the list of labels
    """
    # get the distinct labels from src/targ columns
    labels = list(set(list(df[src]) + list(df[targ])))

    # generate n integers for n labels
    codes = list(range(len(labels)))

    # create a map from label to code
    lc_map = dict(zip(labels, codes))

    # substitute names for codes in the dataframe
    df = df.replace({src: lc_map, targ: lc_map})

    # Return modified dataframe and list of labels
    return df, labels


def make_sankey(df, *cols, vals=None, threshold=0, **kwargs):
    """
    Create a sankey diagram from a dataframe and specified columns

    :param df: the dataframe that will be converted into a diagram
    :param vals: a list of all the columns included in the sankey diagram
    :param save: boolean indicating whether the image should be saved or not
    :param kwargs: optional parameters of the diagram to be edited
    :param threshold: the maximum value count to filter the stacked dataframe on
    :return fig: the plotly sankey figure
    """
    # create a values column based on if the vals argument was passed or not
    if vals:
        values = df[vals]
    else:
        values = [1] * len(df)

    df['values'] = values

    # stack the data
    df = _df_stacking(df, cols, 'values')

    # filter out based on value so that the diagram is not overcrowded
    df = df[df['values'] >= threshold]

    # convert df labels to integer values
    df, labels = _code_mapping(df, 'src', 'targ')

    # build the dictionary for the links of the sankey diagram
    link = {'source': df['src'], 'target': df['targ'], 'value': df['values'],
            'line': {'color': 'black', 'width': 1}}

    # create the node_thickness kwarg
    node_thickness = kwargs.get("node_thickness", 50)

    # build the dictionary for the nodes of the sankey diagram
    node = {'label': labels, 'pad': 50, 'thickness': node_thickness,
            'line': {'color': 'black', 'width': 1}}

    # build the sankey diagram
    sk = go.Sankey(link=link, node=node)
    fig = go.Figure(sk)

    return fig