import gradio as gr
import folium
from folium.plugins import AntPath
import random
import csv
import os

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

CSV_FILE = "train_locations.csv"

def initialize_csv(train_a_src, train_a_dst, train_b_src, train_b_dst):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["train", "city", "latitude", "longitude"])
        writer.writeheader()
        writer.writerow({
            "train": "Train A",
            "city": train_a_src,
            "latitude": TOP_CITIES[train_a_src][0],
            "longitude": TOP_CITIES[train_a_src][1]
        })
        writer.writerow({
            "train": "Train B",
            "city": train_b_src,
            "latitude": TOP_CITIES[train_b_src][0],
            "longitude": TOP_CITIES[train_b_src][1]
        })

def update_train_locations():
    # Placeholder 
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            locations = {row['train']: [float(row['latitude']), float(row['longitude'])] for row in reader}
        return locations
    else:
        return None

def create_animated_map():
    cities = list(TOP_CITIES.keys())

    while True:
        train_a_source, train_a_destination = random.sample(cities, 2)
        train_b_source, train_b_destination = random.sample(cities, 2)
        if train_a_source != train_b_source and train_a_destination != train_b_destination:
            break

    # Initialize CSV with source coordinates if not present
    if not os.path.exists(CSV_FILE):
        initialize_csv(train_a_source, train_a_destination, train_b_source, train_b_destination)

    current_positions = update_train_locations()

    if current_positions:
        train_a_start_coords = current_positions["Train A"]
        train_b_start_coords = current_positions["Train B"]
    else:
        train_a_start_coords = TOP_CITIES[train_a_source]
        train_b_start_coords = TOP_CITIES[train_b_source]

    train_a_end_coords = TOP_CITIES[train_a_destination]
    train_b_end_coords = TOP_CITIES[train_b_destination]

    center_lat = (train_a_start_coords[0] + train_a_end_coords[0] +
                  train_b_start_coords[0] + train_b_end_coords[0]) / 4
    center_lng = (train_a_start_coords[1] + train_a_end_coords[1] +
                  train_b_start_coords[1] + train_b_end_coords[1]) / 4

    m = folium.Map(location=[center_lat, center_lng], zoom_start=6)

    AntPath(
        locations=[train_a_start_coords, train_a_end_coords],
        dash_array=[10, 20],
        delay=1000,
        color='blue',
        pulse_color='white',
        weight=5
    ).add_to(m)

    AntPath(
        locations=[train_b_start_coords, train_b_end_coords],
        dash_array=[10, 20],
        delay=1000,
        color='red',
        pulse_color='white',
        weight=5
    ).add_to(m)

    folium.Marker(
        location=train_a_start_coords,
        popup=f"Train A Source: {train_a_source}",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=train_a_end_coords,
        popup=f"Train A Destination: {train_a_destination}",
        icon=folium.Icon(color="red", icon="stop", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=train_b_start_coords,
        popup=f"Train B Source: {train_b_source}",
        icon=folium.Icon(color="purple", icon="play", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=train_b_end_coords,
        popup=f"Train B Destination: {train_b_destination}",
        icon=folium.Icon(color="orange", icon="stop", prefix="fa")
    ).add_to(m)

    return m._repr_html_()

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 🚂 Train Route Simulator")
    gr.Markdown("Simulates train journeys between two randomly chosen cities in India for **Train A** and **Train B**.")

    with gr.Row():
        with gr.Column():
            simulate_btn = gr.Button("Simulate Train Journey")
        with gr.Column():
            map_output = gr.HTML(label="Route Animation")

    simulate_btn.click(
        fn=create_animated_map,
        inputs=[],
        outputs=map_output
    )

# Run the app
if __name__ == "__main__":
    demo.launch()
