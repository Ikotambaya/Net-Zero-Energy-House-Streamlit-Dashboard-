# 🏡 Net-Zero House Data Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://merylwlsjhhrjwdbniha5r.streamlit.app/)

An interactive Streamlit dashboard designed to visualize and analyze sensor data from a net-zero house, alongside corresponding outdoor environmental conditions. This project aims to provide insights into indoor climate, energy efficiency, and environmental quality.

---

## ✨ Features

* **Dynamic Data Loading:** Automatically generates an SQLite database from a CSV file upon first run, ensuring easy setup and portability.
* **Interactive Visualizations:** Powered by Plotly Express, allowing for zoom, pan, and hover functionalities on all graphs.
* **Zone Selection:** Seamlessly switch between different zones within the house (e.g., Z1, Z2, Z12+13) to view specific sensor data.
* **Measurement Selection:** Choose various measurement types (e.g., temperature, CO2, humidity) to analyze trends within selected zones.
* **Key Performance Indicators (KPIs):** Displays crucial metrics like average outdoor temperature, average zone temperature, and maximum zone CO2 levels.
* **Comparative Analysis:** Visualizes indoor temperature against outdoor conditions to highlight insulation effectiveness and HVAC performance.
* **Clean & Intuitive UI:** Built with Streamlit for a user-friendly and responsive interface.

---

## 🚀 How to Run Locally

Follow these steps to get the dashboard up and running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/NetZeroHouse_StreamlitDashboard.git](https://github.com/YOUR_USERNAME/NetZeroHouse_StreamlitDashboard.git)
    cd NetZeroHouse_StreamlitDashboard
    ```
    (Replace `YOUR_USERNAME` with your actual GitHub username)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ensure the data file is present:**
    Make sure `Net_zero_house_data.csv` is in the root directory of the project. This CSV file will be used to generate the SQLite database (`Net_zero_house_data.db`) on the first run.

5.  **Run the Streamlit app:**
    ```bash
    streamlit run dashboard_app.py
    ```
    Your default web browser should automatically open the dashboard at `http://localhost:8501`.

    * **Note:** On the first run, the app will display a progress bar as it creates the SQLite database from the CSV. Subsequent runs will be faster as the database will already exist.

---

## 📊 Data Source

The data used in this dashboard originates from a comprehensive dataset of a net-zero house's sensor readings and corresponding outdoor weather conditions.
* `Net_zero_house_data.csv`: Contains hourly readings including indoor zone temperatures, CO2 levels, humidity, and various outdoor environmental parameters (air temperature, humidity, wind speed, solar radiation, etc.).

---

## 🛠️ Technologies Used

* **Python:** The core programming language.
* **Streamlit:** For building the interactive web application.
* **Pandas:** For data manipulation and analysis.
* **Plotly Express:** For creating beautiful, interactive data visualizations.
* **SQLite3:** For managing the structured database on the backend.
* **Git & GitHub:** For version control and project hosting.

---

## 📁 Project Structure

NetZeroHouse_StreamlitDashboard/
├── dashboard_app.py          # Main Streamlit application script
├── Net_zero_house_data.csv   # Raw sensor data in CSV format
├── requirements.txt          # Python dependencies
├── .gitignore                # Specifies intentionally untracked files to ignore
└── README.md                 # This README file

---

## 💡 Future Enhancements

* **Date Range Selector:** Allow users to filter data by specific date ranges.
* **Additional Plots:** Implement more specialized plots (e.g., heatmaps for zone temperature distribution, energy consumption trends).
* **Anomaly Detection:** Integrate basic anomaly detection for unusual sensor readings.
* **Machine Learning Integration:** Predict future indoor conditions or energy usage.
* **Improved Responsiveness:** Further optimize for mobile viewing.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
(You might need to create a LICENSE file in your repo later if you want a formal license).

---

## ✉️ Contact

For any questions or feedback, feel free to reach out or open an issue on this repository.

---
