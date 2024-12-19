from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# Load the data
df = pd.read_csv('uber_data.csv')
rides = df

# Categories reclassification
product_mapping = {
    'UberX': 'UberX', 'uberX': 'UberX', 'uberX VIP': 'UberX', 'VIP': 'UberX',
    'POOL': 'Pool', 'POOL: MATCHED': 'Pool', 'UberBLACK': 'Black', 'uberx': 'UberX',
    'uberPOOL': 'Pool', 'uberPOOL: MATCHED': 'Pool', 'Pool: MATCHED': 'Pool'
}
rides['Product Type'].replace(product_mapping, inplace=True)
rides = rides[rides['Product Type'] != 'UberEATS Marketplace']

# Function to convert features to datetime
def date_convertion(df, cols):
    for col in cols:
        df[col] = df[col].apply(lambda x: x.replace(' +0000 UTC', ''))
        df[col] = pd.to_datetime(df[col])
    return df

# Applying date conversion function to date features
rides = date_convertion(rides, ['Request Time', 'Begin Trip Time', 'Dropoff Time'])
rides['year'] = rides['Request Time'].map(lambda x: datetime.strftime(x, "%Y"))
rides['month'] = rides['Request Time'].map(lambda x: datetime.strftime(x, "%b"))
rides['weekday'] = rides['Request Time'].map(lambda x: datetime.strftime(x, "%a"))
rides['time'] = rides['Request Time'].map(lambda x: datetime.strftime(x, "%H:%M"))
rides['distance_km'] = round(rides['Distance (miles)']*1.60934, 2)
rides['amount_km'] = round(rides['Fare Amount'] / rides.distance_km, 2)
rides['request_lead_time'] = rides['Begin Trip Time'] - rides['Request Time']
rides['request_lead_time'] = rides['request_lead_time'].apply(lambda x: round(x.total_seconds() / 60, 1))
rides['trip_duration'] = rides['Dropoff Time'] - rides['Begin Trip Time']
rides['trip_duration'] = rides['trip_duration'].apply(lambda x: round(x.total_seconds() / 60, 1))

# Filtering out canceled trips
rides.loc[(rides['Trip or Order Status'] == 'CANCELED') | (rides['Trip or Order Status'] == 'DRIVER_CANCELED'), 'request_lead_time'] = np.nan
rides.loc[(rides['Trip or Order Status'] == 'CANCELED') | (rides['Trip or Order Status'] == 'DRIVER_CANCELED'), 'amount_km'] = np.nan

completed_rides = rides[(rides['Trip or Order Status'] != 'CANCELED') & (rides['Trip or Order Status'] != 'DRIVER_CANCELED')]
completed_rides = completed_rides.dropna(subset=['Dropoff Lat', 'Dropoff Lng'])

def data_analysis_choice(choice):
    result = ''
    if choice == 'a':
        result = f"Total trips: {completed_rides['Trip or Order Status'].count()}"
    elif choice == 'b':
        result = f"Total trips: {rides['Trip or Order Status'].count()}<br>"
        result += str(round(rides['Trip or Order Status'].value_counts() / rides['Trip or Order Status'].size * 100, 1))
    elif choice == 'c':
        result = "Where did most of the layoffs take place? (Map)"
    elif choice == 'd':
        pt_rides = pd.Series(completed_rides['Product Type'].value_counts().sort_index(ascending=False))
        df = pd.DataFrame(pt_rides)
        df['%'] = (completed_rides['Product Type'].value_counts().sort_index(ascending=False) / completed_rides['Product Type'].size * 100).round(1)
        df.rename(columns={'Product Type': 'Total Rides'}, inplace=True)
        result = df.to_html()
    elif choice == 'e':
        result = f"Avg. fare: {round(completed_rides['Fare Amount'].mean(), 1)} BRL<br>"
        result += f"Avg. distance: {round(completed_rides['distance_km'].mean(), 1)} km<br>"
        result += f"Avg. fare/km: {round(completed_rides['Fare Amount'].sum() / completed_rides['distance_km'].sum(), 1)} BRL/km<br>"
        result += f"Avg. time spent on trips: {round(completed_rides['trip_duration'].mean(), 1)} minutes"
    elif choice == 'f':
        result = "Days of the week highest number of rides per kilometer"
    elif choice == 'g':
        result = "Longest/shortest and most expensive/cheapest ride"
    elif choice == 'h':
        result = f"Avg. lead time before requesting a trip: {round(completed_rides['request_lead_time'].mean(), 1)} minutes"
    else:
        result = "Invalid Choice!"
    return result

@app.route("/", methods=["GET", "POST"])
def index():
    result = ''
    if request.method == 'POST':
        choice = request.form['choice']
        result = data_analysis_choice(choice)
    return render_template('index.html', result=result)

if __name__ == "__main__":
    app.run(debug=True)
