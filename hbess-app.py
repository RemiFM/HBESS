import streamlit as st          # Framework for developing web apps
import numpy as np              # Operations on arrays
import pandas as pd             # Data manipulation and analysis
import altair as alt            # Plotting library
import func.hbess_tables        # Custom functions regarding Pandas Dataframe transformations
import func.hbess_visualise     # Custom functions regarding visualisation of data (plots and tables)
import func.hbess_ems           # Custom functions regarding the energy management strategy
import math                     # Advanced mathematical operations (logarithms...)
import scipy
#from scipy import integrate     # Integration techniques
import matplotlib.pyplot as plt #temporary
from io import StringIO


# Page configuration (name, description, contact...)
st.set_page_config(
    page_title="HBESS Sizing Tool",
    page_icon="🔋", #🔋⚡
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': "mailto:remi.decoster@flandersmake.be?subject=[HBESS Sizing Tool] - Get Help",
        'Report a bug': "mailto:remi.decoster@flandersmake.be?subject=[HBESS Sizing Tool] - Report a bug",
        'About': "The HBESS Sizing Tool is developed by Flanders Make as part of the SEABAT project."
    }
)

# Decrease default page margins from top & bottom
st.markdown("""
            <style>
                .block-container {
                        padding-top: 1rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
            </style>
            """, unsafe_allow_html=True)

# Don't display row numbers in tables, this gives a warning regarding serialization of dataframe to Arrow table
st.markdown("""
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """, unsafe_allow_html=True)


# Title of the web app
st.subheader('Hybrid Battery Energy Storage System (HBESS) Sizing Tool')

# Definition of the differt tabs (containers)
tab_1, tab_2, tab_3, tab_4 = st.tabs(["Define inputs", "Proposed configuration", "System comparison", "More information"])

# Definition of the columns in the first tab (containers)
col_1_1, col_1_2, col_1_3 = tab_1.columns([2,4,2], gap="medium")

# All the input fields
N_LP = int(col_1_1.radio("Number of load profiles", ('1', '2', '3', '4', '5'), horizontal=True))

col_1_1_1, col_1_1_2 = col_1_1.columns(2)
input_HE = col_1_1_1.selectbox('High Energy (HE) Cell',
                                ('NMC Samsung 94Ah', 'LTO Toshiba 23Ah', 'Custom'),
                                help='TODO', index=0, key=111)

input_HP = col_1_1_2.selectbox('High Power (HP) Cell',
                                ('NMC Samsung 94Ah', 'LTO Toshiba 23Ah', 'Custom'),
                                help='TODO', index=1, key=112)

input_load = col_1_1.selectbox('Load profile',
                                ('Tug boat 1', 'Tug boat 2', 'Sine wave', 'Custom'),
                                help='TODO', index=0, key=113)

dict_load = {
    'Tug boat 1': 'load_profiles/tug_boat_1.csv',
    'Tug boat 2': 'load_profiles/tug_boat_2.csv',
    'Sine wave': 'load_profiles/sine_wave.csv',
}

dict_cell = {
    'LTO Toshiba 23Ah': 'battery_cells/LTO_Toshiba_23Ah.csv',
    'NMC Samsung 94Ah': 'battery_cells/NMC_Samsung_94Ah.csv',
}

input_EMS = col_1_1.selectbox('Energy Management Strategy',
                               ('Split', 'Power', 'Gradient', 'Cost', 'Cost: Split', 'Cost: Limit'),
                               help='TODO',index=1, key=114)

if input_EMS == 'Split':
    input_factor = col_1_1.slider('Split factor', 0, 100, 50, 10)
else:
    input_factor = None;

col_1_1_1, col_1_1_2 = col_1_1.columns(2)
input_DOD = col_1_1_1.slider('Depth of Discharge (DoD)', 0, 100, 80, key=118, help='TODO')
input_VREF = col_1_1_1.number_input('Target voltage (V)', min_value=12, max_value=10000, value=1000, step=10, key=116, help='TODO')
input_CYCL = col_1_1_1.number_input('Number of cycles per year', min_value=1, max_value=10000, value=365, step=10, key=117, help='TODO')

input_SOC0 = col_1_1_2.slider('Initial State of Charge (SoC)', 0, 100, 90, key=115, help='TODO')
input_PCHRG = col_1_1_2.number_input('Maximum charging power (kW)', min_value = 1.0, max_value = 10e3, value=2000.0, step=5.0, key=119, help='TODO')
input_LFTM = col_1_1_2.number_input('Expected lifetime (years)', min_value=1, max_value=200, value=20, step=1, key=120, help='TODO')

if(input_SOC0 < input_DOD): 
    st.error("The target Depth of Discharge (DoD) is larger than the Initial State of Charge (SoC)", icon="⚠️")

col_1_1_c = col_1_1.expander('Upload custom files')
col_1_1_c_1, col_1_1_c_2 = col_1_1_c.columns(2)

# Donwloading of custom file templates
col_1_1_c_1.download_button(
    label="Download template for load profiles",
    data=open('load_profiles/tug_boat_1.csv', 'r'),
    file_name='load_profile_template.csv',
    mime='text/csv',
)

col_1_1_c_2.download_button(
    label="Download template for battery cells",
    data=open('battery_cells/LTO_Toshiba_23Ah.csv', 'r'),
    file_name='battery_cell_template.csv',
    mime='text/csv',
)

# Uploading of custom files
file_load = col_1_1_c.file_uploader("Choose a file for the load profile", key=121)
if input_load == 'Custom':
    if file_load is not None and input_load:
        load_profile = func.hbess_tables.read_load_csv(file_load)
    else:
        st.warning('No custom load profile uploaded', icon="⚠️")
        load_profile = pd.DataFrame({'t': [0, 3600], 'P': [0, 0]})
else:
    load_profile = func.hbess_tables.read_load_csv(dict_load[input_load])

file_cell_HE = col_1_1_c.file_uploader("Choose a file for the High Energy (HE) cell", key=122)
if input_HE == 'Custom':
    if file_cell_HE is not None:
        cell_HE, df_OCV_HE, df_SOH_HE = func.hbess_tables.read_cell_csv(file_cell_HE)
    else:
        st.warning('No custom HE battery cell uploaded', icon="⚠️")
        cell_HE, df_OCV_HE, df_SOH_HE = func.hbess_tables.read_cell_csv('battery_cells/None.csv')
else:
    cell_HE, df_OCV_HE, df_SOH_HE = func.hbess_tables.read_cell_csv(dict_cell[input_HE])

file_cell_HP = col_1_1_c.file_uploader("Choose a file for the High Power (HP) cell", key=123)
if input_HP == 'Custom':
    if file_cell_HP is not None:
        cell_HP, df_OCV_HP, df_SOH_HP = func.hbess_tables.read_cell_csv(file_cell_HP)
    else:
        st.warning('No custom HP battery cell uploaded', icon="⚠️")
        cell_HP, df_OCV_HP, df_SOH_HP = func.hbess_tables.read_cell_csv('battery_cells/None.csv')
else:
    cell_HP, df_OCV_HP, df_SOH_HP = func.hbess_tables.read_cell_csv(dict_cell[input_HP])

# Analyse the load profiles most important parameters
P_max = load_profile['P'].max() / 1000 #kW
P_mean = load_profile['P'].mean() / 1000 #kW
PAPR = 10 * math.log((P_max ** 2) / (P_mean ** 2))
E_req = np.trapz(load_profile['P'].to_numpy(), load_profile['t'].to_numpy()) / 3600000   #Ws to kWh

# Calculate the HE and HP contributions
load_profile, df_cost = func.hbess_ems.load_sharing(load_profile, cell_HE, cell_HP, input_EMS, input_SOC0, input_VREF, input_CYCL, input_DOD, input_PCHRG, input_LFTM, input_factor)

# Concatenation of charging part
df_E_cum = func.hbess_tables.get_cumulative_energy(load_profile)        #Cumulative energy usage
# ###
load_profile = func.hbess_tables.add_charging(load_profile, df_E_cum, input_PCHRG)
# ###
df_E_cum = func.hbess_tables.get_cumulative_energy(load_profile)        #Cumulative energy usage


# Calculation of packs
S_HE, P_HE, N_HE, C_HE, E_HE, V_HE = func.hbess_tables.calculate_packs(load_profile['P_HE'], load_profile['t'], cell_HE, input_VREF, input_DOD)
S_HP, P_HP, N_HP, C_HP, E_HP, V_HP = func.hbess_tables.calculate_packs(load_profile['P_HP'], load_profile['t'], cell_HP, input_VREF, input_DOD)
C_tot = C_HE + C_HP
E_tot = E_HE + E_HP

###testing the tabs for multiple LP###
N = int(N_LP)

match N:
    case 1:
        print('1')
        tabs = col_1_2.tabs(["First load profile"])
    case 2:
        print('2')
        tabs = col_1_2.tabs(["First load profile", "Second load profile"])
    case 3:
        print('3')
        tabs = col_1_2.tabs(["First load profile", "Second load profile", "Third load profile"])
    case 4:
        print('4')
        tabs = col_1_2.tabs(["First load profile", "Second load profile", "Third load profile", "Fourth load profile"])
    case 5:
        tabs = col_1_2.tabs(["First load profile", "Second load profile", "Third load profile", "Fourth load profile", "Fifth load profile"])
######


# Display the load profiles metrics
col_1_2_1, col_1_2_2, col_1_2_3, col_1_2_4 = col_1_2.columns(4)
col_1_2_1.metric("Required Energy", "%0.2f kWh" % E_req)
col_1_2_2.metric("Maximum Power", "%0.2f kW" % P_max)
col_1_2_3.metric("Average Power", "%0.2f kW" % P_mean)
col_1_2_4.metric("Total Cost", "\u20ac{:,.2f}".format(C_tot))
#col_2_1_3.metric("Total Cost", "\u20ac{:,.0f}".format(C_tot)) #S_HE, P_HE, cell_HE 
#col_1_2_4.metric("Peak-to-Average Power Ratio", "%0.2f dB" % PAPR)

# Plot - Load Profile 
chart = func.hbess_visualise.fig_loadprofile(load_profile, 520)
col_1_2.altair_chart(chart, theme="streamlit", use_container_width=True)

# Display import cell information in a table
col_1_3.write(f"**High Energy (HE) Cell:** {cell_HE.iloc[0]['value']}")
col_1_3.table(func.hbess_tables.display_cell(cell_HE))
col_1_3.write(f"**High Power (HP) Cell:** {cell_HP.iloc[0]['value']}")
col_1_3.table(func.hbess_tables.display_cell(cell_HP))

# Compare the cell types and give information to user if the selection makes sense
func.hbess_tables.compare_cells(cell_HE, cell_HP)


# Layout of second tab
col_2_1, col_2_2 = tab_2.columns([1, 2], gap="medium")
col_2_1_1, col_2_1_2, col_2_1_3 = col_2_1.columns(3, gap="medium")
col_2_2_1, col_2_2_2 = col_2_2.columns(2, gap="medium")

# # Calculation of packs
# S_HE, P_HE, N_HE, C_HE, E_HE = func.hbess_tables.calculate_packs(load_profile['P_HE'], load_profile['t'], cell_HE, input_VREF, input_DOD)
# S_HP, P_HP, N_HP, C_HP, E_HP = func.hbess_tables.calculate_packs(load_profile['P_HP'], load_profile['t'], cell_HP, input_VREF, input_DOD)

# Calculation of graph information

df_SOC = func.hbess_tables.get_soc(df_E_cum, E_HE, E_HP, input_SOC0)    #SOC calculations
df_V = func.hbess_tables.get_voltage(df_SOC, df_OCV_HE, df_OCV_HP, S_HE, S_HP) #Voltage Calculations
df_I = func.hbess_tables.get_current(load_profile, df_V)

####
#df_cost = func.hbess_ems.cost_limit(load_profile, cell_HE, cell_HP, input_VREF, input_DOD)
#st.dataframe(df_cost)
####

# Display of metrics
col_2_1_1.metric("Required Energy", "%1.0f kWh" % E_req) #load_profile
col_2_1_1.metric("Number of HE Cells", "%i" % N_HE) #S_HE, P_HE
col_2_1_1.metric("HE Pack Energy", "%1.0f kWh" % E_HE) #S_HE, P_HE, cell_HE 
col_2_1_2.metric("Maximum Power", "%1.0f kW" % P_max) #load_profile
col_2_1_2.metric("Number of HP Cells", "%i" % N_HP) #S_HP, P_HP
col_2_1_2.metric("HP Pack Energy", "%1.0f kWh" % E_HP) #S_HP, P_HP, cell_HP
col_2_1_3.metric("Average Power", "%1.0f kW" % P_mean) #load_profile
col_2_1_3.metric("Total Cost", "\u20ac{:,.0f}".format(C_tot)) #S_HE, P_HE, cell_HE 
col_2_1_3.metric("Total Energy", "%1.0f kWh" % E_tot)

# Display of configurations
col_2_1.write("")
col_2_1.subheader("Breakdown of Battery Packs")

col_2_1_4, col_2_1_5 = col_2_1.columns(2)
with col_2_1_4:
    st.write('**High Energy (HE) Pack**')
    st.write('- Cells in series: ', S_HE, '\n',
             '- Cells in parallel: ', P_HE, '\n',
             '- Total energy: ', E_HE, ' kWh', '\n',
             '- Nominal voltage: ', V_HE, ' V', '\n',
             '- Minimum voltage: ', df_V['V_HE'].min(), ' V', '\n',
             '- Maximum voltage: ', df_V['V_HE'].max(), ' V', '\n',
             '- Maximum current: ', df_I['I_HE'].max(), ' A', '\n'
             '- Cost: ', C_HE, ' €')

with col_2_1_5:
    st.write('**High Power (HP) Pack**')
    st.write('- Cells in series: ', S_HP, '\n',
             '- Cells in parallel: ', P_HP, '\n',
             '- Total energy: ', E_HP, ' kWh', '\n',
             '- Nominal voltage: ', V_HP, ' V', '\n',
             '- Minimum voltage: ', df_V['V_HP'].min(), ' V', '\n',
             '- Maximum voltage: ', df_V['V_HP'].max(), ' V', '\n',
             '- Maximum current: ', df_I['I_HP'].max(), ' A', '\n'
             '- Cost: ', C_HP, ' €')







#Plots
chart = func.hbess_visualise.fig_loadprofile(load_profile, 320)

# col_2_2_1.write('**Load profile**')
# col_2_2_1.altair_chart(chart, theme="streamlit", use_container_width=True)

col_2_2_1.write('**Energy Usage**')
chart = func.hbess_visualise.fig_cumul_energy(df_E_cum, 320)
col_2_2_1.altair_chart(chart, theme="streamlit", use_container_width=True)

col_2_2_1.write('**Voltage**')
chart = func.hbess_visualise.fig_voltage(df_V, 320)
col_2_2_1.altair_chart(chart, theme="streamlit", use_container_width=True)


col_2_2_2.write('**State of Charge**')
chart = func.hbess_visualise.fig_soc(df_SOC, 320)
col_2_2_2.altair_chart(chart, theme="streamlit", use_container_width=True)

col_2_2_2.write('**Current**')
chart = func.hbess_visualise.fig_current(df_I, 320)
col_2_2_2.altair_chart(chart, theme="streamlit", use_container_width=True)



if df_cost is not None:
    chart = func.hbess_visualise.fig_cost(df_cost, 320)
    col_2_2_1.altair_chart(chart, theme="streamlit", use_container_width=True)