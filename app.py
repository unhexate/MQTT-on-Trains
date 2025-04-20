import gradio as gr
import folium
from folium.plugins import AntPath
import socket
import json
import time
import threading
import csv
import random
import os

CONTROL_CENTER = "locahost"
CONTROL_CENTER_PORT = 8080

NON_COASTAL_CITIES = {
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

def update_train_locations():
    http_request = "GET /locations HTTP/1.1\r\nHost: localhost:8080\r\n\r\n"
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("localhost", 8080))
    conn.sendall(http_request.encode('utf-8'))

    buffer = bytearray(1)
    http_res_encoded = b''
    while http_res_encoded[-4:] != b'\r\n\r\n':
        conn.recv_into(buffer, 1)
        http_res_encoded += buffer

    http_res = http_res_encoded.decode('utf-8').split('\r\n')
    http_res_headers = dict(map(lambda x: x.split(': '), http_res[1:-2]))

    if http_res[0].split()[1] == '200' and http_res_headers['Content-Type'] == 'application/json':
        payload_encoded = b""
        for _ in range(int(http_res_headers["Content-Length"])):
            conn.recv_into(buffer, 1)
            payload_encoded += buffer
        return json.loads(payload_encoded.decode('utf-8'))

def update_routes():
    http_request = "GET /routes HTTP/1.1\r\nHost: localhost:8080\r\n\r\n"
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("localhost", 8080))
    conn.sendall(http_request.encode('utf-8'))

    buffer = bytearray(1)
    http_res_encoded = b''
    while http_res_encoded[-4:] != b'\r\n\r\n':
        conn.recv_into(buffer, 1)
        http_res_encoded += buffer

    http_res = http_res_encoded.decode('utf-8').split('\r\n')
    http_res_headers = dict(map(lambda x: x.split(': '), http_res[1:-2]))

    if http_res[0].split()[1] == '200' and http_res_headers['Content-Type'] == 'application/json':
        payload_encoded = b""
        for _ in range(int(http_res_headers["Content-Length"])):
            conn.recv_into(buffer, 1)
            payload_encoded += buffer
        return json.loads(payload_encoded.decode('utf-8'))

# Global variable to store train routes
train_routes = {}

def generate_train_assignments():
    cities = list(NON_COASTAL_CITIES.keys())
    assignments = {}
    for train in ["Train A", "Train B"]:
        src, dest = random.sample(cities, 2)
        assignments[train] = [src, dest]
    return assignments

def simulate_train_movement():
    global train_routes
    train_routes = generate_train_assignments()
    train_positions = {
        train: NON_COASTAL_CITIES[route[0]]
        for train, route in train_routes.items()
    }
    destinations = {
        train: NON_COASTAL_CITIES[route[1]]
        for train, route in train_routes.items()
    }

    with open("train_positions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Train", "Latitude", "Longitude", "Timestamp"])

    for _ in range(20):
        for train in ["Train A", "Train B"]:
            lat, lon = train_positions[train]
            lat_end, lon_end = destinations[train]

            lat += (lat_end - lat) * 0.05
            lon += (lon_end - lon) * 0.05
            train_positions[train] = [lat, lon]

            with open("train_positions.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([train, lat, lon, time.time()])

        time.sleep(2)

def create_animated_map():
    threading.Thread(target=simulate_train_movement, daemon=True).start()
    return "<h3>🚆 Simulation started. CSV is updating...</h3>"

def render_map_from_csv():
    if not os.path.exists("train_positions.csv"):
        return "<h4>🛑 No data yet. Start simulation first.</h4>"

    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5)
    train_positions = {}

    with open("train_positions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            train = row["Train"]
            lat = float(row["Latitude"])
            lon = float(row["Longitude"])
            train_positions[train] = (lat, lon)

    for train, (lat, lon) in train_positions.items():
        folium.Marker(
            [lat, lon], 
            popup=f"{train} - Current Position", 
            icon=folium.Icon(color='blue' if train == 'Train A' else 'green')
        ).add_to(m)

    # Draw animated route lines (source -> destination)
    for train, (src_name, dest_name) in train_routes.items():
        src_coords = NON_COASTAL_CITIES[src_name]
        dest_coords = NON_COASTAL_CITIES[dest_name]
        AntPath([src_coords, dest_coords], color="red" if train == 'Train A' else "orange").add_to(m)
        folium.Marker(src_coords, popup=f"{train} - Source: {src_name}", icon=folium.Icon(color="gray")).add_to(m)
        folium.Marker(dest_coords, popup=f"{train} - Destination: {dest_name}", icon=folium.Icon(color="darkred")).add_to(m)

    return m._repr_html_()

def login_user(username, password):
    if username == "admin" and password == "admin123":
        return gr.update(visible=True), gr.update(visible=False), "✅ Login successful!"
    else:
        return gr.update(visible=False), gr.update(visible=True), "❌ Invalid credentials. Try again."

with gr.Blocks() as app:
    gr.Markdown("# 🚆 Train Control Center - Login")

    with gr.Column(visible=True) as login_section:
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status", interactive=False)

    with gr.Column(visible=False) as simulation_section:
        gr.Markdown("## 🎯 Train Simulation Dashboard")
        start_btn = gr.Button("Start Train Simulation")
        refresh_btn = gr.Button("🔁 Refresh Map")
        map_display = gr.HTML()

    login_btn.click(fn=login_user, inputs=[username, password],
                    outputs=[simulation_section, login_section, login_status])

    start_btn.click(fn=create_animated_map, outputs=map_display)
    refresh_btn.click(fn=render_map_from_csv, outputs=map_display)

if __name__ == "__main__":
    app.launch()
