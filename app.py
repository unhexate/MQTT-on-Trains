import gradio as gr
import folium
from folium.plugins import AntPath
import random
import pandas as pd
import os
from datetime import datetime
import threading
import time

# Step 1: Define the CSV file path for storing cities
CITIES_CSV = "cities.csv"
TRACKING_CSV = "train_tracking.csv"

# Predefined top 10 cities in India with their coordinates
TOP_CITIES = {
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Chennai": [13.0827, 80.2707],
    "Kolkata": [22.5726, 88.3639],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

# Step 2: Write cities to a CSV file if it doesn't exist
def write_cities_to_csv():
    global TOP_CITIES
    if not os.path.exists(CITIES_CSV):
        df = pd.DataFrame(list(TOP_CITIES.items()), columns=["City", "Coordinates"])
        df.to_csv(CITIES_CSV, index=False)

# Step 3: Load cities from the CSV file
def load_cities_from_csv():
    global TOP_CITIES
    df = pd.read_csv(CITIES_CSV)
    TOP_CITIES = {row["City"]: eval(row["Coordinates"]) for _, row in df.iterrows()}

# Global variables to track train movements
current_coords_1 = None
current_coords_2 = None
map_html_filename = "train_map.html"

# Step 4: Simulate two trains moving along their routes
def create_animated_map_with_two_trains():
    global current_coords_1, current_coords_2, map_html_filename

    # Load cities from CSV
    load_cities_from_csv()

    # Randomly select two unique source-destination pairs
    cities = list(TOP_CITIES.keys())
    while True:
        source_city_1, destination_city_1 = random.sample(cities, 2)
        source_city_2, destination_city_2 = random.sample(cities, 2)
        # Ensure no overlap or reverse overlap
        if ({source_city_1, destination_city_1} != {source_city_2, destination_city_2} and
            source_city_1 != destination_city_2 and source_city_2 != destination_city_1):
            break

    # Extract coordinates
    start_coords_1, end_coords_1 = TOP_CITIES[source_city_1], TOP_CITIES[destination_city_1]
    start_coords_2, end_coords_2 = TOP_CITIES[source_city_2], TOP_CITIES[destination_city_2]

    # Initialize current coordinates
    current_coords_1 = list(start_coords_1)
    current_coords_2 = list(start_coords_2)

    # Start tracking train movements
    track_trains_in_csv(start_coords_1, end_coords_1, start_coords_2, end_coords_2)

    # Return the initial map as an iframe
    return f'<iframe src="{map_html_filename}" width="100%" height="600px"></iframe>'


# Step 5: Track train coordinates in a CSV file and update every 2 seconds
def track_trains_in_csv(start_coords_1, end_coords_1, start_coords_2, end_coords_2):
    global current_coords_1, current_coords_2, map_html_filename

    # Function to calculate movement increments
    def calculate_movement_vector(start, end):
        lat_step = (end[0] - start[0]) / 100  # Increment latitude by 1/100th of the total distance
        lng_step = (end[1] - start[1]) / 100  # Increment longitude by 1/100th of the total distance
        return lat_step, lng_step

    # Movement vectors
    lat_step_1, lng_step_1 = calculate_movement_vector(start_coords_1, end_coords_1)
    lat_step_2, lng_step_2 = calculate_movement_vector(start_coords_2, end_coords_2)

    # Function to update train positions every 2 seconds
    def update_train_positions():
        global current_coords_1, current_coords_2, map_html_filename
        for _ in range(100):  # Move in 100 steps
            # Update coordinates
            current_coords_1[0] += lat_step_1
            current_coords_1[1] += lng_step_1
            current_coords_2[0] += lat_step_2
            current_coords_2[1] += lng_step_2

            # Log to CSV
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = [
                {"Timestamp": timestamp, "Train": "Train 1", "Current Coordinates": current_coords_1},
                {"Timestamp": timestamp, "Train": "Train 2", "Current Coordinates": current_coords_2}
            ]
            df = pd.DataFrame(data)
            if not os.path.exists(TRACKING_CSV):
                df.to_csv(TRACKING_CSV, index=False)
            else:
                df.to_csv(TRACKING_CSV, mode="a", header=False, index=False)

            # Regenerate map with updated train positions
            m = folium.Map(location=[(current_coords_1[0] + current_coords_2[0]) / 2,
                                     (current_coords_1[1] + current_coords_2[1]) / 2], zoom_start=6)

            # Add animated paths for both trains
            AntPath(
                locations=[start_coords_1, end_coords_1],
                dash_array=[10, 20],
                delay=1000,
                color='blue',
                pulse_color='white',
                weight=5
            ).add_to(m)

            AntPath(
                locations=[start_coords_2, end_coords_2],
                dash_array=[10, 20],
                delay=1000,
                color='red',
                pulse_color='white',
                weight=5
            ).add_to(m)

            # Add fixed source and destination markers
            folium.Marker(
                location=start_coords_1,
                popup=f"Train 1 Source",
                icon=folium.Icon(color="green", icon="play", prefix="fa")
            ).add_to(m)

            folium.Marker(
                location=end_coords_1,
                popup=f"Train 1 Destination",
                icon=folium.Icon(color="red", icon="stop", prefix="fa")
            ).add_to(m)

            folium.Marker(
                location=start_coords_2,
                popup=f"Train 2 Source",
                icon=folium.Icon(color="purple", icon="play", prefix="fa")
            ).add_to(m)

            folium.Marker(
                location=end_coords_2,
                popup=f"Train 2 Destination",
                icon=folium.Icon(color="orange", icon="stop", prefix="fa")
            ).add_to(m)

            # Add train markers at current positions
            folium.Marker(
                location=current_coords_1,
                popup="Train 1",
                icon=folium.Icon(color="blue", icon="train", prefix="fa")
            ).add_to(m)

            folium.Marker(
                location=current_coords_2,
                popup="Train 2",
                icon=folium.Icon(color="red", icon="train", prefix="fa")
            ).add_to(m)

            # Save the updated map to an HTML file
            m.save(map_html_filename)

            # Wait for 2 seconds
            time.sleep(2)

    # Start a background thread to update train positions
    threading.Thread(target=update_train_positions, daemon=True).start()


# Step 6: Gradio Interface
write_cities_to_csv()  # Ensure cities are written to CSV

with gr.Blocks() as demo:
    gr.Markdown("# 🚂 Train Route Simulator")
    gr.Markdown("Simulates two train journeys between randomly chosen cities in India.")

    with gr.Row():
        with gr.Column():
            simulate_btn = gr.Button("Simulate Train Journey")
        with gr.Column():
            map_output = gr.HTML(label="Route Animation")

    # Function to display the map in an iframe
    def display_map():
        return f'<iframe src="{map_html_filename}" width="100%" height="600px"></iframe>'

    simulate_btn.click(
        fn=create_animated_map_with_two_trains,
        inputs=[],
        outputs=map_output
    )

if _name_ == "_main_":
    demo.launch()
