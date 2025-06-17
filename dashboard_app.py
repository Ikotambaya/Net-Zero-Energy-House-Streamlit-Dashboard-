import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import time # For a small delay for user feedback

# --- IMPORTANT: st.set_page_config MUST BE THE VERY FIRST STREAMLIT COMMAND ---
st.set_page_config(layout="wide", page_title="Net-Zero House Dashboard")
# -----------------------------------------------------------------------------

# --- Configuration for Database and CSV Paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
db_file = 'Net_zero_house_data.db'
csv_file = 'Net_zero_house_data.csv' # Your CSV file
db_path = os.path.join(script_dir, db_file)
csv_path = os.path.join(script_dir, csv_file)

# Fallback for environments where __file__ is not defined or paths are tricky
if not os.path.exists(db_path) and not os.path.exists(csv_path):
    st.error(f"Neither database '{db_file}' nor CSV '{csv_file}' found in '{script_dir}'.")
    st.stop() # Stop the app if essential files are missing

# --- Database Creation Function ---
def create_db_from_csv(csv_filepath, db_filepath):
    """
    Creates an SQLite database from the Net_zero_house_data.csv file.
    """
    conn = None
    try:
        st.info("Database not found. Creating database from CSV...")
        progress_bar = st.progress(0)

        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        # Drop tables if they exist to ensure a clean slate
        cursor.execute("DROP TABLE IF EXISTS HourlyOutdoorReadings;")
        cursor.execute("DROP TABLE IF EXISTS HourlyZoneReadings;")
        cursor.execute("DROP TABLE IF EXISTS Zones;")
        cursor.execute("DROP TABLE IF EXISTS Measurements;")
        conn.commit()

        # Create Tables (Based on your previous schema)
        cursor.execute("""
            CREATE TABLE Zones (
                ZoneID INTEGER PRIMARY KEY,
                ZoneName TEXT NOT NULL UNIQUE,
                ZoneDescription TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE Measurements (
                MeasurementID INTEGER PRIMARY KEY,
                MeasurementName TEXT NOT NULL UNIQUE,
                Unit TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE HourlyOutdoorReadings (
                ReadingID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT NOT NULL,
                Air_temperature REAL,
                Relative_humidity REAL,
                Wind_speed REAL,
                Wind_direction REAL,
                Barometric_pressure REAL,
                Precipitation REAL,
                Solar_radiation REAL,
                Outdoor_CO2 REAL
            );
        """)
        cursor.execute("""
            CREATE TABLE HourlyZoneReadings (
                ReadingID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT NOT NULL,
                ZoneID INTEGER NOT NULL,
                MeasurementID INTEGER NOT NULL,
                Value REAL,
                FOREIGN KEY (ZoneID) REFERENCES Zones(ZoneID),
                FOREIGN KEY (MeasurementID) REFERENCES Measurements(MeasurementID)
            );
        """)
        conn.commit()
        progress_bar.progress(20)
        time.sleep(0.1) # Small delay for visual feedback

        # Read CSV into DataFrame
        df = pd.read_csv(csv_filepath, parse_dates=['Timestamp'])
        progress_bar.progress(40)
        time.sleep(0.1)

        # Populate Zones and Measurements tables
        zones = {} # To map zone names to IDs
        measurements = {} # To map measurement names to IDs

        # Dynamically find zone and measurement columns in CSV
        # Assumes format like 'Z1_temp', 'Z2_CO2'
        zone_measurement_cols = [col for col in df.columns if '_' in col and col != 'Outdoor_CO2']

        # Extract unique zone names
        unique_zones = sorted(list(set([col.split('_')[0] for col in zone_measurement_cols])))
        for i, zone_name in enumerate(unique_zones):
            cursor.execute("INSERT INTO Zones (ZoneName, ZoneDescription) VALUES (?, ?);", (zone_name, f"Zone {zone_name} in Net-Zero House"))
            zones[zone_name] = cursor.lastrowid # Store ZoneID

        # Extract unique measurement names
        # Filter out "Outdoor_" prefixed columns from zone_measurement_cols
        unique_measurements_set = set()
        for col in zone_measurement_cols:
            parts = col.split('_')
            if len(parts) >= 2: # Ensure it's not just a zone name
                measurement_name = '_'.join(parts[1:]) # e.g., 'temp', 'humidity'
                unique_measurements_set.add(measurement_name)

        # Add specific outdoor measurements and other known ones
        # You might need to refine this based on your exact CSV column names
        known_measurements = {
            'temp': '°C', 'humidity': '%', 'CO2': 'ppm',
            'Air_temperature': '°C', 'Relative_humidity': '%', 'Wind_speed': 'm/s',
            'Wind_direction': '°', 'Barometric_pressure': 'hPa', 'Precipitation': 'mm',
            'Solar_radiation': 'W/m²', 'Outdoor_CO2': 'ppm' # Explicit outdoor measurements
        }
        for meas_name, unit in known_measurements.items():
            if meas_name not in unique_measurements_set: # Add if not already processed from zone columns
                unique_measurements_set.add(meas_name)

        # Insert measurements into DB
        for meas_name in sorted(list(unique_measurements_set)):
            unit = known_measurements.get(meas_name, '') # Get unit or empty string if not found
            cursor.execute("INSERT INTO Measurements (MeasurementName, Unit) VALUES (?, ?);", (meas_name, unit))
            measurements[meas_name] = cursor.lastrowid # Store MeasurementID

        conn.commit()
        progress_bar.progress(60)
        time.sleep(0.1)

        # Populate HourlyOutdoorReadings
        outdoor_cols = [
            'Timestamp', 'Air_temperature', 'Relative_humidity', 'Wind_speed',
            'Wind_direction', 'Barometric_pressure', 'Precipitation', 'Solar_radiation',
            'Outdoor_CO2'
        ]
        # Ensure only columns present in DF are used for insertion
        actual_outdoor_cols = [col for col in outdoor_cols if col in df.columns]
        outdoor_data = df[actual_outdoor_cols].values.tolist()

        # Create placeholders for the INSERT statement
        placeholders = ', '.join(['?' for _ in actual_outdoor_cols])
        cols_for_insert = ', '.join(actual_outdoor_cols)

        cursor.executemany(
            f"INSERT INTO HourlyOutdoorReadings ({cols_for_insert}) VALUES ({placeholders});",
            outdoor_data
        )
        conn.commit()
        progress_bar.progress(80)
        time.sleep(0.1)

        # Populate HourlyZoneReadings
        for _, row in df.iterrows():
            timestamp = row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S') # Ensure consistent format

            for col_name in zone_measurement_cols:
                zone_name, measurement_name = col_name.split('_', 1) # Split only on first underscore
                zone_id = zones.get(zone_name)
                measurement_id = measurements.get(measurement_name)
                value = row[col_name]

                if pd.notna(value) and zone_id is not None and measurement_id is not None:
                    cursor.execute(
                        "INSERT INTO HourlyZoneReadings (Timestamp, ZoneID, MeasurementID, Value) VALUES (?, ?, ?, ?);",
                        (timestamp, zone_id, measurement_id, value)
                    )
        conn.commit()
        progress_bar.progress(100)
        time.sleep(0.5) # Give progress bar time to complete
        progress_bar.empty() # Remove progress bar
        st.success("Database created successfully from CSV!")

    except FileNotFoundError:
        st.error(f"Error: CSV file not found at {csv_filepath}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred during database creation: {e}")
        st.stop()
    finally:
        if conn:
            conn.close()

# --- Check for DB existence and create if necessary ---
if not os.path.exists(db_path):
    # This call is outside of @st.cache_data as it modifies the file system
    create_db_from_csv(csv_path, db_path)

# --- Database Connection and Data Extraction Function (remains the same) ---
@st.cache_data # Cache the data to avoid re-running the query every time the app updates
def get_data_from_db(query):
    """Fetches data from the SQLite database using a given SQL query."""
    conn = None
    df = pd.DataFrame() # Initialize an empty DataFrame
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
    except sqlite3.Error as e:
        st.error(f"Database error: {e}. Please ensure '{db_file}' is accessible.")
        st.write(f"Attempted to connect to: {db_path}")
        st.stop() # Stop the app if cannot connect after creation attempt
    finally:
        if conn:
            conn.close()
    return df

@st.cache_data
def get_zones_and_measurements():
    """Fetches all available zones and measurements from the database."""
    zones_df = get_data_from_db("SELECT ZoneID, ZoneName FROM Zones ORDER BY ZoneName;")
    measurements_df = get_data_from_db("SELECT MeasurementID, MeasurementName, Unit FROM Measurements ORDER BY MeasurementName;")
    return zones_df, measurements_df

# --- Define Global Queries ---
query_outdoor_temp = """
SELECT
    STRFTIME('%Y-%m-%d %H', Timestamp) AS ReadingHour,
    Air_temperature AS TemperatureC
FROM
    HourlyOutdoorReadings
ORDER BY
    ReadingHour;
"""

# Fetch zones and measurements once when the app starts.
zones_df, measurements_df = get_zones_and_measurements()
zone_names = zones_df['ZoneName'].tolist() if not zones_df.empty else []
measurement_names = measurements_df['MeasurementName'].tolist() if not measurements_df.empty else []


# --- Streamlit App Layout and Content ---

st.title("🏡 Net-Zero House Data Dashboard")
st.markdown("Explore hourly sensor data from a net-zero house, alongside outdoor environmental conditions.")

# --- Sidebar for User Selections ---
st.sidebar.header("Dashboard Controls")

selected_zone_name = st.sidebar.selectbox(
    "Select a Zone:",
    options=zone_names,
    index=zone_names.index('Z1') if 'Z1' in zone_names else (0 if zone_names else None)
)
selected_zone_id = zones_df[zones_df['ZoneName'] == selected_zone_name]['ZoneID'].iloc[0] if selected_zone_name else None


selected_measurement_name = st.sidebar.selectbox(
    "Select a Measurement Type for Zone Data:",
    options=measurement_names,
    index=measurement_names.index('temp') if 'temp' in measurement_names else (0 if measurement_names else None)
)
selected_measurement_info = measurements_df[
    (measurements_df['MeasurementName'] == selected_measurement_name)
]
selected_measurement_id = selected_measurement_info['MeasurementID'].iloc[0] if not selected_measurement_info.empty else None
selected_measurement_unit = selected_measurement_info['Unit'].iloc[0] if not selected_measurement_info.empty else ""


# --- Main Content Area ---

# 1. Overall Key Performance Indicators (KPIs)
st.markdown("---")
st.subheader("Key Performance Indicators (KPIs)")
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

avg_outdoor_temp = get_data_from_db("SELECT AVG(Air_temperature) FROM HourlyOutdoorReadings;").iloc[0,0]
if pd.notna(avg_outdoor_temp):
    kpi_col1.metric("Avg. Outdoor Temp (All Time)", f"{avg_outdoor_temp:.2f} °C")
else:
    kpi_col1.metric("Avg. Outdoor Temp (All Time)", "N/A")

avg_zone_temp = None
if selected_zone_id is not None:
    avg_zone_temp_query = f"""
    SELECT AVG(HZR.Value)
    FROM HourlyZoneReadings AS HZR
    WHERE HZR.ZoneID = {selected_zone_id} AND HZR.MeasurementID = (SELECT MeasurementID FROM Measurements WHERE MeasurementName = 'temp');
    """
    avg_zone_temp = get_data_from_db(avg_zone_temp_query).iloc[0,0]

if pd.notna(avg_zone_temp):
    kpi_col2.metric(f"Avg. {selected_zone_name} Temp (All Time)", f"{avg_zone_temp:.2f} °C")
else:
    kpi_col2.metric(f"Avg. {selected_zone_name} Temp (All Time)", "N/A")

max_co2 = None
if selected_zone_id is not None:
    max_co2_query = f"""
    SELECT MAX(HZR.Value)
    FROM HourlyZoneReadings AS HZR
    WHERE HZR.ZoneID = {selected_zone_id} AND HZR.MeasurementID = (SELECT MeasurementID FROM Measurements WHERE MeasurementName = 'CO2');
    """
    max_co2 = get_data_from_db(max_co2_query).iloc[0,0]

if pd.notna(max_co2):
    kpi_col3.metric(f"Max {selected_zone_name} CO2 (All Time)", f"{max_co2:.2f} ppm")
else:
    kpi_col3.metric(f"Max {selected_zone_name} CO2 (All Time)", "N/A")


# 2. Temperature Trends: Selected Zone vs Outdoor
st.markdown("---")
st.subheader(f"Temperature Trends: {selected_zone_name} vs. Outdoor")
st.markdown("Daily average temperatures to observe seasonal and daily patterns.")

if selected_zone_id is not None and not measurements_df.empty:
    zone_temp_query = f"""
    SELECT
        STRFTIME('%Y-%m-%d %H', HZR.Timestamp) AS ReadingHour,
        HZR.Value AS TemperatureC
    FROM
        HourlyZoneReadings AS HZR
    WHERE
        HZR.ZoneID = {selected_zone_id} AND HZR.MeasurementID = (SELECT MeasurementID FROM Measurements WHERE MeasurementName = 'temp')
    ORDER BY
        ReadingHour;
    """
    zone_temp_df = get_data_from_db(zone_temp_query)

    outdoor_temp_df_plot = get_data_from_db(query_outdoor_temp)

    if not zone_temp_df.empty and not outdoor_temp_df_plot.empty:
        zone_temp_df['ReadingHour'] = pd.to_datetime(zone_temp_df['ReadingHour'])
        outdoor_temp_df_plot['ReadingHour'] = pd.to_datetime(outdoor_temp_df_plot['ReadingHour'])

        merged_temp_for_plot_df = pd.merge(
            zone_temp_df.set_index('ReadingHour').resample('D').mean().reset_index(),
            outdoor_temp_df_plot.set_index('ReadingHour').resample('D').mean().reset_index(),
            on='ReadingHour',
            suffixes=('_Zone', '_Outdoor')
        )

        merged_temp_for_plot_df.rename(columns={
            'TemperatureC_Zone': f'{selected_zone_name} Temp (°C)',
            'TemperatureC_Outdoor': 'Outdoor Temp (°C)'
        }, inplace=True)

        fig_temp = px.line(merged_temp_for_plot_df, x='ReadingHour',
                           y=[f'{selected_zone_name} Temp (°C)', 'Outdoor Temp (°C)'],
                           title=f'Daily Average Temperature: {selected_zone_name} vs. Outdoor',
                           labels={'value': 'Temperature (°C)', 'ReadingHour': 'Date'},
                           hover_data={'ReadingHour': '|%Y-%m-%d', 'value': ':.2f'})

        fig_temp.update_layout(hovermode="x unified")
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.warning(f"No temperature data available for {selected_zone_name} or Outdoor for plotting.")
else:
    st.error("Error fetching zone/measurement data for temperature trend plot. Check Zone/Measurement IDs.")


# 3. Selected Zone Measurement Trend (Hourly Data)
st.markdown("---")
st.subheader(f"Hourly Trend for {selected_measurement_name} in {selected_zone_name}")
st.markdown("Observe the hourly fluctuations of the selected measurement within the chosen zone.")

if selected_zone_id is not None and selected_measurement_id is not None:
    selected_zone_measurement_query = f"""
    SELECT
        STRFTIME('%Y-%m-%d %H', HZR.Timestamp) AS ReadingHour,
        HZR.Value AS Value
    FROM
        HourlyZoneReadings AS HZR
    WHERE
        HZR.ZoneID = {selected_zone_id} AND HZR.MeasurementID = {selected_measurement_id}
    ORDER BY
        ReadingHour;
    """
    selected_measurement_df = get_data_from_db(selected_zone_measurement_query)

    if not selected_measurement_df.empty:
        selected_measurement_df['ReadingHour'] = pd.to_datetime(selected_measurement_df['ReadingHour'])

        fig_selected_measurement = px.line(selected_measurement_df, x='ReadingHour', y='Value',
                                           title=f'Hourly {selected_measurement_name} in {selected_zone_name}',
                                           labels={'Value': f'{selected_measurement_name} ({selected_measurement_unit})', 'ReadingHour': 'Date/Time'},
                                           hover_data={'ReadingHour': '|%Y-%m-%d %H:00', 'Value': ':.2f'})

        fig_selected_measurement.update_layout(hovermode="x unified")
        st.plotly_chart(fig_selected_measurement, use_container_width=True)
    else:
        st.warning(f"No data available for '{selected_measurement_name}' in '{selected_zone_name}'.")
else:
    st.error("Error fetching data for selected zone measurement trend. Check Zone/Measurement IDs.")

st.markdown("---")
st.info("💡 Use the sidebar controls to explore different zones and measurements.")