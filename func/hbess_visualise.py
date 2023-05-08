import altair as alt
import numpy as np
from scipy import integrate     # Integration techniques
import pandas as pd

def energy_loadprofile(chart_data):
    E_req = np.trapz(chart_data['P'].to_numpy(), chart_data['t'].to_numpy()) / 3600000   #Ws to kWh

    return E_req



def fig_loadprofile(chart_data, height):
    ## SCALE INPUTS
    chart_data = chart_data.copy()                                  #copy of DataFrame for scaling
    chart_data.loc[:, 't'] = chart_data.loc[:, 't'] / 60            #seconds to hours
    chart_data.loc[:, 'P'] = chart_data.loc[:, 'P'] / 1000          #watts to kilowatts
    chart_data.loc[:, 'P_HE'] = chart_data.loc[:, 'P_HE'] / 1000    #watts to kilowatts
    chart_data.loc[:, 'P_HP'] = chart_data.loc[:, 'P_HP'] / 1000    #watts to kilowatts

    ## RESTRUCTURE DATAFRAME FOR VISUALISATION
    chart_data = (chart_data
                  .loc[:, ['t', 'P', 'P_HE', 'P_HP']]
                  .rename(columns = {'P':'Total demand', 'P_HE':'Contribution from HE-cells', 'P_HP':'Contribution from HP-cells'})
                  .melt('t'))

    ## CREATE CHART OBJECT
    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('t', axis = alt.Axis(title = 'Time (min)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'Power (kW)')),
        color = alt.Color('variable', sort = ['Total demand'], legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )

    return chart


def fig_cumul_energy(df_E_cum, height):
    df_E_cum['t'] *= 60 
    chart_data = df_E_cum.melt('t')

    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('t', axis = alt.Axis(title = 'Time (min)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'Energy (kWh)')),
        color = alt.Color('variable', sort = ['E_cum'], legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )
    return chart


def fig_soc(df_SOC, height):
    df_SOC['t'] *= 60 
    chart_data = df_SOC.melt('t')


    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('t', axis = alt.Axis(title = 'Time (min)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'SOC (%)'), scale=alt.Scale(domain=[0, 100])),
        color = alt.Color('variable', legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )
    return chart


def fig_voltage(df_V, height):
    df_V['t'] *= 60
    chart_data = df_V.melt('t')

    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('t', axis = alt.Axis(title = 'Time (min)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'Voltage (V)'), scale=alt.Scale(zero=False)),
        color = alt.Color('variable', legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )
    return chart

def fig_current(df_I, height):
    df_I['t'] *= 60
    chart_data = df_I.melt('t')

    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('t', axis = alt.Axis(title = 'Time (min)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'Current (A)'), scale=alt.Scale(zero=False)),
        color = alt.Color('variable', legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )
    return chart


def fig_cost(df_cost, height):
    chart_data = df_cost.melt('factor')

    chart = (
        alt.Chart(data = chart_data)
        .mark_line()
        .encode(
        x = alt.X('factor', axis = alt.Axis(title = 'Factor (?)', grid = False)),
        y = alt.Y('value', axis = alt.Axis(title = 'Cost (€)'), scale=alt.Scale(zero=False)),
        color = alt.Color('variable', legend = alt.Legend(orient = 'bottom', title = 'None', titleOpacity = 0, titlePadding = 0, titleFontSize = 0))   
        )
        .properties(
            height = height,
        )
        .interactive()
    )

    return chart

