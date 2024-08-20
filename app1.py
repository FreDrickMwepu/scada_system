import streamlit as st
import serial
import time
import pandas as pd
import altair as alt
import numpy as np  
from streamlit_option_menu import option_menu

# Set up page configuration
st.set_page_config(page_title="UNIVERSITY SCADA DASHBOARD", page_icon=":bar_chart:")

# Hide Streamlit menu
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Constants for serial communication
SERIAL_PORT = '/dev/tty.usbmodem141201'
BAUD_RATE = 9600
TIMEOUT = 1

# Function to get serial connection
@st.cache_resource
def get_serial_connection():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        return ser
    except serial.SerialException as e:
        st.error(f"Error: {e}")
        return None

# Function to send command to Arduino and get response
def send_command(ser, command):
    if ser:
        ser.write(command.encode())
        time.sleep(0.1)  # Wait for Arduino to process the command
        return ser.readline().decode().strip()
    return "Error: No serial connection"

# Initialize session state for storing data
def initialize_session_state():
    if 'data' not in st.session_state:
        st.session_state.data = pd.DataFrame(columns=['timestamp', 'current'])

# Display the latest current reading
def display_current_reading():
    if not st.session_state.data.empty:
        latest_current = st.session_state.data['current'].iloc[-1]
        st.metric(label="Current", value=f"{latest_current:.2f} A")

# Display the current readings chart
def display_current_chart():
    if not st.session_state.data.empty:
        chart = alt.Chart(st.session_state.data).mark_line(point=alt.OverlayMarkDef(color='#1EEC11', size=70)).encode(
            x=alt.X('timestamp:T', title='Hours', axis=alt.Axis(labelColor='#ffffff', titleColor='#ffffff', grid=True, tickSize=5, tickColor='#ffffff')),
            y=alt.Y('current:Q', title='Current (A)', axis=alt.Axis(labelColor='#ffffff', titleColor='#ffffff', grid=True, tickSize=5, tickColor='#ffffff')),
            tooltip=[alt.Tooltip('timestamp:T', title='Date Time'), alt.Tooltip('current:Q', title='Current (A)')]
        ).properties(
            width=600,
            height=300,
            title=alt.TitleParams(text='Current Over Time', color='#ffbf00', fontSize=17, anchor='middle', align='center'),
            background='rgba(255, 255, 255, 0)',
            padding={'top': 50, 'right': 10}
        ).configure_axis(
            gridColor='#ffffff',
            gridOpacity=0.5,
            domainColor='#ffffff',
            domainWidth=1,
            tickColor='#ffffff',
            tickWidth=1,
            labelFont='Arial',
            labelFontSize=12,
            titleFont='Arial',
            titleFontSize=12
        ).configure_title(
            fontSize=17,
            font='Arial',
            anchor='middle',
            color='#ffbf00'
        ).configure_view(
            strokeWidth=0
        )
        st.altair_chart(chart)

# Read current value from Arduino and update session state
def read_current(ser):
    current_str = send_command(ser, "READ")
    try:
        current = float(current_str)
        new_data = pd.DataFrame({'timestamp': [pd.Timestamp.now()], 'current': [current]})
        st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
    except ValueError:
        st.error(f"Invalid current reading: {current_str}")

# Control system for bulbs and current monitoring
def system_control(ser):
    st.subheader("Bulb Control")
    cols = st.columns(5)
    for i in range(5):
        if cols[i].button(f"Button {i}"):
            response = send_command(ser, f"TOGGLE{i}")
            st.write(f"Control System Response: {response}")

    st.subheader("Bulb Status")
    status = send_command(ser, "STATUS")
    if status:
        states = status.split(',')
        status_cols = st.columns(5)
        for i, state in enumerate(states):
            status_cols[i].write(f"BULD-BUTTON {i}: {state}")

    st.subheader("Current Monitoring")
    if st.button("Read Current"):
        read_current(ser)
    display_current_reading()
    display_current_chart()

# Current monitoring section
def current_monitoring(ser):
    st.subheader("Current Monitoring")
    if st.button("Read Current"):
        read_current(ser)
    display_current_reading()
    display_current_chart()

# Function for data analytics and reporting
def data_analytics():
    st.subheader("Data Analytics and Reporting")
    
    if st.session_state.data.empty:
        st.write("No data available for analytics.")
        return
    
    # Use the current readings from session state
    df = st.session_state.data.copy()
    
    # Display data
    st.write("Data Overview")
    st.dataframe(df)
    
    # Display chart
    st.write("Data Chart")
    chart = alt.Chart(df).mark_line().encode(
        x='timestamp:T',
        y='current:Q'
    )
    st.altair_chart(chart, use_container_width=True)
    
    # Display summary statistics
    st.write("Summary Statistics")
    st.write(df.describe())

# Main function to run the Streamlit app
def main():
    st.title("UNIVERSITY SCADA DASHBOARD")
    st.markdown("Monitor and Control System Parameters")

    ser = get_serial_connection()
    initialize_session_state()

    selected = option_menu(
        menu_title=None,
        options=["System Control", "Current Monitoring", "Report and Data Analytics"],
        icons=["gear", "current-line" , "bar-chart"],
        orientation="horizontal",
    )

    if selected == "Current Monitoring":
        current_monitoring(ser)
    elif selected == "System Control":
        system_control(ser)
    elif selected == "Report and Data Analytics":
        data_analytics()
    else:
        st.error("Invalid selection")

    # Add a very big button to control the power state
    st.subheader("Power Control")
    if st.button("Toggle Power", key="power_button", help="Toggle the power state of the component connected to pin 7"):
        response = send_command(ser, "POWER")
        st.write(f"Power Control Response: {response}")

if __name__ == "__main__":
    main()