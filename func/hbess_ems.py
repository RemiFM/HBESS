import pandas as pd
import numpy as np
import streamlit as st
from .hbess_tables import *

def load_sharing(load_profile, cell_HE, cell_HP, method, SOC_0, V_ref, N_year, DoD, P_chrg, lifetime, factor):
    
    match method:
        case 'Split':
            #split sharing method
            load_profile = split_sharing(load_profile, factor)
            df_cost = None
        
        case 'Power':
            load_profile = power_sharing(load_profile)
            df_cost = None

        case 'Gradient':
            load_profile = gradient_sharing(load_profile)
            df_cost = None
        
        case 'Cost':
            load_profile = split_none(load_profile)
            df_cost = None

        case 'Cost: Split':
            load_profile, df_cost = cost_split(load_profile, cell_HE, cell_HP, V_ref, DoD)

        case 'Cost: Limit':
            load_profile, df_cost = cost_limit(load_profile, cell_HE, cell_HP, V_ref, DoD)
            
        case default:
            load_profile = split_none(load_profile)
            df_cost = None

    return load_profile, df_cost


def split_sharing(load_profile, factor):
    load_profile['P_HE'] = (factor/100) * load_profile['P']
    load_profile['P_HP'] = (1 - (factor/100)) * load_profile['P']
    return load_profile


def power_sharing(load_profile):
    factors = pd.DataFrame()
    factors['factor_HP'] = load_profile['P'] / (load_profile['P'].max())

    load_profile['P_HE'] = (1 - factors['factor_HP']) * load_profile['P']
    load_profile['P_HP'] = factors['factor_HP'] * load_profile['P']
    return load_profile


def gradient_sharing(load_profile):
    P_diff = load_profile['P'].diff()
    P_min = abs(P_diff.min())
    P_max = abs(P_diff.max())
    P_num = P_diff + P_min

    factors = pd.DataFrame()
    factors['factor_HP'] = P_num / (P_num.max() - P_num.min())
    factors['factor_HP'] = factors['factor_HP'].fillna(0, downcast='infer')
    factors.loc[0, 'factor_HP'] = 0.5

    load_profile['P_HE'] = (1 - factors['factor_HP']) * load_profile['P']
    load_profile['P_HP'] = factors['factor_HP'] * load_profile['P']
    return load_profile


def split_none(load_profile):
    load_profile['P_HE'] = 0.1 * load_profile['P']
    load_profile['P_HP'] = 0.2 * load_profile['P']

    return load_profile

def cost_split(load_profile, cell_HE, cell_HP, V_ref, DoD):
    temp_profile = load_profile.copy()
    df_cost = pd.DataFrame(columns=['factor', 'cost'])
    my_bar = st.progress(0, text="Operation in progress. Please wait.")
    
    for factor in range(0, 101):
        my_bar.progress(factor, text="Operation in progress. Please wait.")

        #Calculate power of each pack
        temp_profile['P_HE'] = (factor/100) * load_profile['P']
        temp_profile['P_HP'] = (1-(factor/100)) * load_profile['P']

        #Calculate total cost
        S_HE, P_HE, N_HE, C_HE, E_HE, V_HE = calculate_packs(temp_profile['P_HE'], temp_profile['t'], cell_HE, V_ref, DoD)
        S_HP, P_HP, N_HP, C_HP, E_HP, V_HP = calculate_packs(temp_profile['P_HP'], temp_profile['t'], cell_HP, V_ref, DoD)
        C_tot = C_HE + C_HP
        
        new_row = pd.DataFrame({'factor': factor, 'cost': C_tot}, index=[0])
        df_cost = pd.concat([df_cost, new_row], ignore_index=True)
    
    factor = df_cost.loc[df_cost['cost'].idxmin(), 'factor']
    load_profile['P_HE'] = (factor/100) * load_profile['P']
    load_profile['P_HP'] = (1 - (factor/100)) * load_profile['P']
    my_bar.empty()

    return load_profile, df_cost

# def cost_limit(load_profile, cell_HE, cell_HP, SOC_0, V_ref, N_year, DoD, P_chrg, lifetime)
def cost_limit(load_profile, cell_HE, cell_HP, V_ref, DoD, cost=False):
    temp_profile = load_profile.copy()
    df_cost = pd.DataFrame(columns=['factor', 'cost'])

    my_bar = st.progress(0, text="Operation in progress. Please wait.")
    P_max = load_profile['P'].max()

    for P_lim in range(0, int(P_max + round(P_max/500)), int(round(P_max/500))): 
        #print(P_lim)
        my_bar.progress(round(100*P_lim/P_max), text="Operation in progress. Please wait.")

        #Calculate the power of each pack
        temp_profile['P_HE'] = temp_profile.apply(lambda row: row['P'] if row['P'] < P_lim else P_lim, axis=1)
        temp_profile['P_HP'] = temp_profile.apply(lambda row: 0 if row['P'] < P_lim else row['P'] - P_lim, axis=1)

        #Calculate total cost
        S_HE, P_HE, N_HE, C_HE, E_HE, V_HE = calculate_packs(temp_profile['P_HE'], temp_profile['t'], cell_HE, V_ref, DoD)
        S_HP, P_HP, N_HP, C_HP, E_HP, V_HP = calculate_packs(temp_profile['P_HP'], temp_profile['t'], cell_HP, V_ref, DoD)
        C_tot = C_HE + C_HP

        new_row = pd.DataFrame({'factor': P_lim, 'cost': C_tot}, index=[0])
        df_cost = pd.concat([df_cost, new_row], ignore_index=True)

    P_lim = df_cost.loc[df_cost['cost'].idxmin(), 'factor']
    load_profile['P_HE'] = load_profile.apply(lambda row: row['P'] if row['P'] < P_lim else P_lim, axis=1)
    load_profile['P_HP'] = load_profile.apply(lambda row: 0 if row['P'] < P_lim else row['P'] - P_lim, axis=1)
    my_bar.empty()

    return load_profile, df_cost