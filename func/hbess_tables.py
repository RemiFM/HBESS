import pandas as pd
import ast
import streamlit as st
import math
import scipy

def read_cell_csv(file):
    # Read the .csv file and create a Dataframe
    df_cell = pd.read_csv(file)

    # Control validity of .csv file:
    if (df_cell.shape != (12, 3) or list(df_cell.columns) != ['parameter', 'value', 'unit']):
        # Error handling
        st.error('The uploaded file (battery cell) is not in the correct format', icon="⚠️")
        df_cell = pd.read_csv('battery_cells/None.csv')
        #raise Exception('The uploaded file (cell information) is not in the correct format')

    # Convert the string representations of the lists to Python lists
    OCV = ast.literal_eval(df_cell.iloc[8]['value'])
    OCV_SOC = ast.literal_eval(df_cell.iloc[9]['value'])
    SOH = ast.literal_eval(df_cell.iloc[10]['value'])
    SOH_N = ast.literal_eval(df_cell.iloc[11]['value'])

    # Create a DataFrame containing the lists
    df_OCV = pd.DataFrame({'OCV': OCV, 'SOC': OCV_SOC})
    df_SOH = pd.DataFrame({'SOH': SOH, 'N': SOH_N})

    # Print the Dataframes in the terminal
    if False:
        print(df_cell.to_string())
        print(df_OCV.to_string())
        print(df_SOH.to_string())

    return df_cell, df_OCV, df_SOH


def read_load_csv(file):
    df_load = pd.read_csv(file)
    
    # Control validity of .csv file: exactly two columns, at least two rows, and the correct headers
    if (df_load.shape[1] != 2) or (df_load.shape[0] < 2) or (list(df_load.columns) != ['time (s)', 'power (W)']):
        st.error('The uploaded file (load profile) is not in the correct format', icon="⚠️")
        df_load = pd.DataFrame({'t': [0, 3600], 'P': [0, 0]});
    
    else:
        # Rename the columns
        df_load = df_load.rename(columns={'time (s)': 't', 'power (W)': 'P'})

    return df_load

def display_cell(pd_cell):
    cell_formatted = pd.DataFrame({'parameter': ['Rated capacity', 'Nominal voltage', 'Power capacity', 'Maximum C-rates', 'Cost density', 'Weight density'],
                                   'value': ['{} Ah'.format(pd_cell.iloc[2]['value']),
                                   '{} V'.format(pd_cell.iloc[3]['value'], 2),
                                   '{} Wh'.format(round(float(pd_cell.iloc[3]['value']) * float(pd_cell.iloc[2]['value']), 2)),
                                   '{} / {}'.format(round(float(pd_cell.iloc[6]['value']) / float(pd_cell.iloc[2]['value']), 2), round(float(pd_cell.iloc[7]['value']) / float(pd_cell.iloc[2]['value']), 2)),
                                   '{} €/kWh'.format(round(1000 * float(pd_cell.iloc[5]['value']) / (float(pd_cell.iloc[3]['value']) * float(pd_cell.iloc[2]['value'])), 2)),
                                   '{} kg/kWh'.format(round(1000*float(pd_cell.iloc[4]['value']) / (float(pd_cell.iloc[3]['value']) * float(pd_cell.iloc[2]['value'])), 2))
                                ]})
    
    return cell_formatted

def compare_cells(he_cell, hp_cell):
    if ((round(float(hp_cell.iloc[3]['value']) * float(hp_cell.iloc[2]['value']), 2)) > (round(float(he_cell.iloc[3]['value']) * float(he_cell.iloc[2]['value']), 2))):
        #HP cell contains more energy than HP cell
        st.info('The selected high power (HP) cell contains more energy than the high energy (HE) cell', icon="ℹ️")

    if (round(float(he_cell.iloc[6]['value']) / float(he_cell.iloc[2]['value']), 2)) > (round(float(hp_cell.iloc[6]['value']) / float(hp_cell.iloc[2]['value']), 2)):
        #HE cell has a higher discharge rate
        st.info('The selected high power (HP) cell has a lower discharge rate than the high energy (HE) cell', icon="ℹ️")

    if False and (round(float(he_cell.iloc[7]['value']) / float(he_cell.iloc[2]['value']), 2)) > (round(float(hp_cell.iloc[7]['value']) / float(hp_cell.iloc[2]['value']), 2)):
        #HE cell has a higher charge rate
        st.info('The selected high power (HP) cell has a lower charge rate than the high energy (HE) cell', icon="ℹ️")

    return None


def calculate_packs(load, time, cell, V_ref, DoD):
    E_req = scipy.integrate.cumtrapz(load.to_numpy(), time.to_numpy(), initial=0).max() / 3600 #Wh
    E_cell = float(cell.iloc[3]['value']) * float(cell.iloc[2]['value']) #Wh
    N_min = (E_req / E_cell) / (DoD / 100)

    S = round(V_ref / float(cell.iloc[3]['value'])) #string length (series)
    V_pack = S * float(cell.iloc[3]['value'])
    P = math.ceil(N_min / S) #number of strings (parallel)

    N = S * P #total number of cells
    C = N * float(cell.iloc[5]['value']) #eur
    E = round(N * float(cell.iloc[3]['value']) * float(cell.iloc[2]['value']) / 1000, 2) #kWh
    V = V_pack

    return S, P, N, C, E, V

def get_cumulative_energy(load_profile):
    t_h = load_profile['t'].to_numpy() / 3600 #s to h
    E_cum = scipy.integrate.cumtrapz(load_profile['P'].to_numpy(), t_h, initial=0) / 1000     #kWh
    E_HE_cum = scipy.integrate.cumtrapz(load_profile['P_HE'].to_numpy(), t_h, initial=0) / 1000  #kWh
    E_HP_cum = scipy.integrate.cumtrapz(load_profile['P_HP'].to_numpy(), t_h, initial=0) / 1000  #kWh

    df_E_cum = pd.DataFrame({'t': t_h, 'E_cum': E_cum, 'E_HE_cum': E_HE_cum, 'E_HP_cum': E_HP_cum})
    return df_E_cum

def get_soc(df_E_cum, E_HE, E_HP, SOC0):
    df_SOC = df_E_cum.copy().drop(columns=['E_cum']).rename(columns={'E_HE_cum': 'SOC_HE', 'E_HP_cum': 'SOC_HP'})
    df_SOC['SOC_HE'] = (SOC0) - 100*(df_SOC['SOC_HE'] / E_HE)
    df_SOC['SOC_HP'] = (SOC0) - 100*(df_SOC['SOC_HP'] / E_HP)

    return df_SOC

def get_voltage(df_SOC, df_OCV_HE, df_OCV_HP, S_HE, S_HP):
    #High energy pack
    SOC = df_OCV_HE['SOC'].to_numpy()
    OCV = df_OCV_HE['OCV'].to_numpy()
    SOC_TO_OCV = scipy.interpolate.interp1d(SOC, OCV, kind='linear', fill_value='extrapolate') #y = f(x)

    SOC = df_SOC['SOC_HE'].to_numpy() / 100
    V_HE = S_HE * SOC_TO_OCV(SOC)

    #High power pack
    SOC = df_OCV_HP['SOC'].to_numpy()
    OCV = df_OCV_HP['OCV'].to_numpy()
    SOC_TO_OCV = scipy.interpolate.interp1d(SOC, OCV, kind='linear', fill_value='extrapolate') #y = f(x)

    SOC = df_SOC['SOC_HP'].to_numpy() / 100
    V_HP = S_HP * SOC_TO_OCV(SOC)
    
    df_V = pd.DataFrame({'t': df_SOC['t'], 'V_HE': V_HE, 'V_HP': V_HP})

    return df_V

def get_current(load_profile, df_V):
    #I = P / V
    I_HE = load_profile['P_HE'] / df_V['V_HE']
    I_HP = load_profile['P_HP'] / df_V['V_HP']
    I = I_HE + I_HP

    df_I = pd.DataFrame({'t': df_V['t'], 'I': I, 'I_HE': I_HE, 'I_HP': I_HP})

    return df_I

def add_charging(load_profile, df_E_cum, P_chrg):
    E_cum = df_E_cum['E_cum'].iloc[-1]          #kWh
    E_HE_cum = df_E_cum['E_HE_cum'].iloc[-1]    #kWh
    E_HP_cum = df_E_cum['E_HP_cum'].iloc[-1]    #kWh

    P_HE_chrg = (E_HE_cum / E_cum) * float(P_chrg) * -1000 #W
    P_HP_chrg = (E_HP_cum / E_cum) * float(P_chrg) * -1000 #W

    t_start = load_profile['t'].iloc[-1]        #s
    t_chrg = (E_cum / float(P_chrg)) * 3600     #s

    new_row = pd.DataFrame({'t': [t_start], 'P': [-1000*float(P_chrg)], 'P_HE': [P_HE_chrg], 'P_HP': [P_HP_chrg]})
    load_profile = pd.concat([load_profile, new_row], ignore_index=True)
    new_row = pd.DataFrame({'t': [t_start + t_chrg], 'P': [-1000*float(P_chrg)], 'P_HE': [P_HE_chrg], 'P_HP': [P_HP_chrg]})
    load_profile = pd.concat([load_profile, new_row], ignore_index=True)

    print(f't_start: {t_start}\nt_end: {t_start+t_chrg}\nP_chrg: {-1000*float(P_chrg)} W\nP_HE_chrg: {P_HE_chrg} W\nP_HP_chrg: {P_HP_chrg} W')
    print(load_profile.tail().to_string())

    return load_profile
##