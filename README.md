# Fuel Filter System 🚗⛽
This project processes and filters fuel level data for vehicles using Finite Impulse Response (FIR) filtering and Moving Average filters. It retrieves data from MongoDB, applies signal processing techniques, and visualizes fuel level trends over time.

## Features
✅ Connects to MongoDB to fetch vehicle fuel level data
✅ Applies FIR low-pass filtering to smooth fuel level readings
✅ Uses Moving Average filtering for additional smoothing
✅ Resamples fuel level data at 1-minute intervals
✅ Performs fuel calibration using polynomial regression
✅ Generates plots to visualize raw vs. filtered fuel data

## Technologies Used
Python (pandas, NumPy, SciPy, Matplotlib)
MongoDB (for storing and retrieving vehicle fuel history)
Usage
To use this script, ensure you have MongoDB running and install the required Python libraries:

pip install pymongo pandas numpy scipy matplotlib

Run the script:
python fir.py
