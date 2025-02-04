from pymongo import MongoClient
import pandas as pd
import numpy as np
from scipy.signal import firwin, lfilter, filtfilt
import matplotlib.pyplot as plt


# Define FIR low-pass filter function
def fir_lowpass_filter(data, cutoff, fs, numtaps=101):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    # Design the FIR filter
    fir_coeff = firwin(numtaps, normal_cutoff)
    # Apply the FIR filter
    # filtered_data = filtfilt(fir_coeff, 1.0, data)
    filtered_data = lfilter(fir_coeff, 1.0, data)

    return filtered_data

# Define a simple moving average low-pass filter function
def moving_average_lowpass_filter(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='same')



# Step 1: Connect to MongoDB
# try:
client = MongoClient("mongodb://localhost:27017/")  # adjust host and port if needed
db = client['FuelFilter']  # replace with your database name
collection = db['DeviceGeoHistory']  # replace with your collection name

# Step 2: Define the specific vehicleNo you want to filter
specific_vehicle_no = "LL-2501"  # replace with the desired vehicle number
start_date = "2024-09-04"
end_date = "2024-09-25"
# Step 3: Fetch documents for the specific vehicleNo
documents = collection.find({"vehicleNo": specific_vehicle_no})  # query for specific vehicleNo

# Step 3: Fetch documents for the specific vehicleNo and date range
# documents = collection.find({
#     "vehicleNo": specific_vehicle_no,
#     "date": {
#         "$gte": start_date,
#         "$lte": end_date
#     }
# })
documents = collection.find({
    "vehicleNo": specific_vehicle_no,
    # "date": start_date
})

# Load data into a DataFrame
data = []
previous_fuel_level = None
for doc in documents:
    geo_data = doc.get("geoData", [])
    for item in geo_data:
        try:
            # Ensure the timestamp is correctly parsed
            timestamp = item.get("timeStamp")
            if isinstance(timestamp, dict) and "$date" in timestamp and "$numberLong" in timestamp["$date"]:
                timestamp = pd.to_datetime(timestamp["$date"]["$numberLong"], unit='ms')
            
            # Get the fuel level
            fuel_level = int(item["fuelLevelE2"]) if isinstance(item["fuelLevelE2"], dict) else item["fuelLevelE2"]
            
            # If the fuel level is 0, use the previous non-zero fuel level
            if fuel_level == 0 and previous_fuel_level is not None:
                # print("HI", previous_fuel_level, timestamp)
                fuel_level = previous_fuel_level
            else:
                previous_fuel_level = fuel_level  # Update the previous fuel level
            
            data.append({
                "timestamp": timestamp,
                # "fuelLevelE2": int(item["fuelLevelE2"]) if isinstance(item["fuelLevelE2"], dict) else item["fuelLevelE2"],
                "fuelLevelE2": fuel_level,
                "speed": float(item["speed"])
            })
        except KeyError as e:
            print(f"Missing key in JSON data: {e}")
        except Exception as e:
            print(f"Error processing item: {e}")

# Convert to DataFrame and set timestamp as index
df = pd.DataFrame(data)
df.set_index("timestamp", inplace=True)

# Resample the DataFrame to 1-minute intervals and forward fill missing data
resampled_df = df.resample("60s").mean().ffill()

cutoff_frequency = 0.01  # Define the cutoff frequency
sampling_rate = 3  # Define the sampling rate
numtaps = 101  # Define the number of filter coefficients (taps)

 # Apply filters
resampled_df['fuelLevelE2_smoothed_m']= moving_average_lowpass_filter(resampled_df['fuelLevelE2'], 20)
resampled_df['fuelLevelE2_smoothed'] = fir_lowpass_filter(resampled_df['fuelLevelE2_smoothed_m'], cutoff_frequency, sampling_rate, numtaps)
resampled_df['smoothed_fuel_level'] = resampled_df['fuelLevelE2_smoothed']


# Fuel calibration using polynomial fit

# LM-8208
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175],
#     'fuelLevelE2': [1,1,111,241,369,497,619,743,865,973,1091,1210,1327,1446,1575,1694,1813,1922,2042,2161,2279,2397,2513,2632,2749,2855,2973,3085,3201,3316,3430,3547,3662,3780,3899,3899,4022]
# })

# LI-7484
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,180,185],
#     'fuelLevelE2': [1, 1, 1, 88, 215, 342, 456, 578, 699, 821, 942, 1062, 1181, 1292, 1413, 1532, 1650, 1766, 1885, 2009, 2115, 2232, 2349, 2467, 2584, 2698, 2814, 2920, 3037, 3153, 3267, 3381, 3499, 3614, 3726, 3848, 3970, 4095]
# })

# LM-2501
calibration_data = pd.DataFrame({
    'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165],
    'fuelLevelE2': [1, 49, 166, 310, 453, 591, 723, 855, 985, 1114, 1244, 1351, 1477, 1599, 1723, 1843, 1964, 2084, 2205, 2326, 2433, 2555, 2675, 2798, 2919, 3035, 3165, 3289, 3413, 3540, 3669, 3792, 3925, 4095]
})

# LM-8209
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 20, 25, 30, 35, 40, 45, 50, 55, 59, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 178],
#     'fuelLevelE2': [74,76,84,219,360,500,640,778,916,1053,1316,1445,1573,1697,1826,1954,2082,2210,2337,2466,2593,2715,2843,2968,3095,3222,3348,3475,3602,3730,3858,3927,4058]
# })

# LN-7944
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
#     'fuelLevelE2': [1, 86, 458, 834, 1189, 1562, 1924, 2266,2626, 2981,3334,3687,4063]
# })

# LN-8059
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175],
#     'fuelLevelE2': [1, 2, 172, 303, 433, 559, 685, 809, 936, 1047, 1165, 1286, 1411, 1533, 1655, 1778, 1902, 2014, 2131, 2251, 2366,2490, 2607, 2727, 2840, 2958, 3076, 3193, 3311, 3429, 3550, 3667, 3787, 3911, 4039, 4095]
# })

# # LN-8236
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,180],
#     'fuelLevelE2': [1, 1, 86, 214, 338, 463, 578, 699, 819, 937, 1054, 1173, 1285, 1399, 1515, 1629, 1746, 1862, 1976, 2086, 2197, 2310, 2425, 2536, 2650, 2762, 2868, 2983, 3099, 3210, 3325, 3440, 3554, 3668, 3787, 3907, 4030]
# })

#  PY-1382
# calibration_data = pd.DataFrame({
#     'Actual Liter': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
#     'fuelLevelE2': [1,192, 571, 922, 1281, 1626, 1978, 2325, 2660, 3007, 3359, 3717, 4090]
# })

coefficients = np.polyfit(calibration_data['fuelLevelE2'], calibration_data['Actual Liter'], deg=2)
poly_func = np.poly1d(coefficients)
resampled_df['fuel_liters'] = poly_func(resampled_df['smoothed_fuel_level'])
resampled_df['fuel_liters_Raw'] = poly_func(resampled_df['fuelLevelE2'])

# Plotting Fuel Level and Speed
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# Plot fuel level
ax1.plot(resampled_df.index, resampled_df['fuelLevelE2'], label="Raw Fuel Data", color="blue")
# ax1.plot(resampled_df.index, resampled_df['smoothed_fuel_level'], color='green', label='Smoothed Fuel Level')
ax1.set_xlabel('Time')
ax1.set_ylabel('Raw Fuel Level (mm)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.legend(loc="upper right")
ax1.grid()

# Plot speed
# ax2.plot(resampled_df.index, resampled_df['fuelLevelE2'], label="Raw Fuel Data", color="blue")
ax2.plot(resampled_df.index, resampled_df['smoothed_fuel_level'], color='green', label='Smoothed Fuel Level')

# ax2.plot(resampled_df.index, resampled_df['speed'], label="Raw Speed Data", color="orange")
# ax2.plot(resampled_df.index, resampled_df['smoothed_speed'], label="Smoothed Speed Data", color="red", linestyle='--')
ax2.set_xlabel('Time')
ax2.set_ylabel('Smoothed Fuel Level (mm)', color='orange')
ax2.tick_params(axis='y', labelcolor='orange')
ax2.legend(loc="upper right")
ax2.grid()

plt.suptitle('Raw Fuel Level and Filtered Fuel Level (mm)')
plt.tight_layout()
plt.show()

# Plot calibrated fuel level and speed
# Plotting Fuel Level and Speed
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# Speed on secondary axis
# ax2 = plt.gca().twinx()
ax1.plot(resampled_df.index, resampled_df['fuel_liters_Raw'], color='red', label='Raw Fuel Level (ltr)', linewidth=2)
ax1.set_xlabel('Time')
ax1.set_ylabel('Raw Fuel Level (Liters)', color='red')
# ax2.set_ylim(0)

ax2.plot(resampled_df.index, resampled_df['fuel_liters'], color='blue', label='Calibrated Fuel Level (Liters)', linewidth=2)
ax2.set_xlabel('Time')
ax2.set_ylabel('Filtered Fuel Level (Liters)', color='blue')
ax2.grid()
# plt.ylim(0)
# plt.grid(True)

# ax1.set_xlabel('Time')
# ax1.set_ylabel('Fuel Level', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.legend(loc="upper right")
ax1.grid()



plt.suptitle('Raw Fuel Level and Calibrated Fuel Level (Liters)')
ax1.legend(loc="lower left")
ax2.legend(loc="upper right")
plt.tight_layout()
plt.show()