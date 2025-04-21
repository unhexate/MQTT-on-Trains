import gradio as gr
import folium
from folium.plugins import AntPath
import socket
import json
import io
import csv
import hashlib

# Non-coastal cities
NON_COASTAL_CITIES = {
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

CONTROL_CENTER = "localhost"
CONTROL_CENTER_PORT = 8080

auth_key = ""

# ------------------- Communication with Control Center -------------------
def update_train_locations():
    try:
        global auth_key
        if(auth_key == ""): return
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((CONTROL_CENTER, CONTROL_CENTER_PORT))
        conn.sendall(f"GET /locations HTTP/1.1\r\nHost: localhost:8080\r\nAuthorization: Bearer {auth_key}\r\n\r\n".encode('utf-8'))
        
        buffer = bytearray(1)
        headers_raw = b""
        while not headers_raw.endswith(b"\r\n\r\n"):
            conn.recv_into(buffer, 1)
            headers_raw += buffer
        headers = headers_raw.decode().split("\r\n")
        status_line = headers[0]
        headers_dict = dict(line.split(": ", 1) for line in headers[1:] if ": " in line)
        
        if "200" in status_line and headers_dict.get("Content-Type") == "text/csv":
            length = int(headers_dict["Content-Length"])
            body = b""
            while len(body) < length:
                chunk = conn.recv(length - len(body))
                if not chunk:
                    break
                body += chunk
            conn.close()
            
            # Parse CSV content
            csv_text = body.decode()
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            locations = []
            for row in csv_reader:
                # Convert position and time values to appropriate types if needed
                locations.append({
                    "train_id": row["train_id"],
                    "pos_x": float(row["pos_x"]),
                    "pos_y": float(row["pos_y"]),
                    "time": row["time"]  # You may want to convert this to a datetime object
                })
            return locations

    except Exception as e:
        print("Error in update_train_locations:", e)

    return []

def update_routes():
    try:
        global auth_key
        if(auth_key == ""): return
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((CONTROL_CENTER, CONTROL_CENTER_PORT))
        conn.sendall(f"GET /routes HTTP/1.1\r\nHost: localhost:8080\r\nAuthorization: Bearer {auth_key}\r\n\r\n".encode('utf-8'))
        buffer = bytearray(1)
        headers_raw = b""
        while not headers_raw.endswith(b"\r\n\r\n"):
            conn.recv_into(buffer, 1)
            headers_raw += buffer
        headers = headers_raw.decode().split("\r\n")
        status_line = headers[0]
        headers_dict = dict(line.split(": ", 1) for line in headers[1:] if ": " in line)
        if "200" in status_line and headers_dict.get("Content-Type") == "application/json":
            length = int(headers_dict["Content-Length"])
            body = b""
            while len(body) < length:
                chunk = conn.recv(length - len(body))
                if not chunk:
                    break
                body += chunk
            conn.close()
            return json.loads(body.decode())
    except Exception as e:
        print("Error in update_routes:", e)
    return {}

# ------------------- Map Generator -------------------
def create_animated_map():
    global auth_key
    if(auth_key == ""): return
    train_positions = update_train_locations()
    train_routes = update_routes()

    if not train_routes or "Train A" not in train_routes or "Train B" not in train_routes:
        return "<p style='color:red;'>Error: Train routes unavailable.</p>"

    train_a_source, train_a_destination = train_routes["Train A"]
    train_b_source, train_b_destination = train_routes["Train B"]

    train_a_start_coords = NON_COASTAL_CITIES[train_a_source]
    train_b_start_coords = NON_COASTAL_CITIES[train_b_source]

    train_a_current_coords = [[loc["pos_x"],loc["pos_y"]] for loc in train_positions if loc["train_id"] == "Train A"][-1]
    train_b_current_coords = [[loc["pos_x"],loc["pos_y"]]  for loc in train_positions if loc["train_id"] == "Train B"][-1]

    train_a_current_coords = [float(x) for x in train_a_current_coords]
    train_b_current_coords = [float(x) for x in train_b_current_coords]

    train_a_end_coords = NON_COASTAL_CITIES[train_a_destination]
    train_b_end_coords = NON_COASTAL_CITIES[train_b_destination]

    # center_lat = sum([train_a_start_coords[0], train_a_end_coords[0],
    #                   train_b_start_coords[0], train_b_end_coords[0]]) / 4
    # center_lng = sum([train_a_start_coords[1], train_a_end_coords[1],
    #                   train_b_start_coords[1], train_b_end_coords[1]]) / 4

    m = folium.Map(location=[20.5937, 78.9629], zoom_start=[4.5])

    AntPath([train_a_start_coords, train_a_end_coords],
            dash_array=[10, 20], delay=1000, color='blue', pulse_color='white').add_to(m)
    AntPath([train_b_start_coords, train_b_end_coords],
            dash_array=[10, 20], delay=1000, color='red', pulse_color='white').add_to(m)

    folium.Marker(train_a_start_coords, popup=f"Train A Source: {train_a_source}",
                  icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
    folium.Marker(train_a_end_coords, popup=f"Train A Destination: {train_a_destination}",
                  icon=folium.Icon(color="red", icon="stop", prefix="fa")).add_to(m)

    folium.Marker(train_b_start_coords, popup=f"Train B Source: {train_b_source}",
                  icon=folium.Icon(color="purple", icon="play", prefix="fa")).add_to(m)
    folium.Marker(train_b_end_coords, popup=f"Train B Destination: {train_b_destination}",
                  icon=folium.Icon(color="orange", icon="stop", prefix="fa")).add_to(m)
    
    
    folium.Marker(train_a_current_coords, popup=f"Train A Current: {train_a_current_coords}",
                  icon=folium.Icon(color="blue", icon="train", prefix="fa")).add_to(m)
    folium.Marker(train_b_current_coords, popup=f"Train B Current: {train_b_current_coords}",
                  icon=folium.Icon(color="green", icon="train", prefix="fa")).add_to(m)
    
    # folium.Marker(
    #     [lat, lon], 
    #     popup=f"{train} - Current Position", 
    #     icon=folium.Icon(color='blue' if train == 'Train A' else 'green',
    #                         icon = "train", prefix="fa")
    # ).add_to(m)

    return m._repr_html_()

# ------------------- Gradio App -------------------
with gr.Blocks() as demo:
    login_status = gr.State(False)

    with gr.Column(visible=True) as login_section:
        gr.Markdown("## 🔐 Login to Continue")
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_msg = gr.Markdown("")

    with gr.Column(visible=False) as app_section:
        gr.Markdown("# 🚂 Train Route Simulator")
        gr.Markdown("Simulates train journeys between two cities in India for *Train A* and *Train B*.")
        with gr.Row():
            simulate_btn = gr.Button("Simulate Train Journey")
            map_output = gr.HTML(label="Route Animation")
            map_timer = gr.Timer(value=5.0, active=True) 

    def check_login(user, pwd):
        global auth_key
        auth_key = hashlib.sha256((user+","+pwd).encode()).digest().hex()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((CONTROL_CENTER, CONTROL_CENTER_PORT))
        conn.sendall(f"GET /login HTTP/1.1\r\nHost: localhost:8080\r\nAuthorization: Bearer {auth_key}\r\n\r\n".encode('utf-8'))

        buffer = bytearray(1)
        headers_raw = b""
        while not headers_raw.endswith(b"\r\n\r\n"):
            conn.recv_into(buffer, 1)
            headers_raw += buffer
        headers = headers_raw.decode().split("\r\n")
        status_line = headers[0]
        headers_dict = dict(line.split(": ", 1) for line in headers[1:] if ": " in line)
        if "200" in status_line:
            return True, gr.update(visible=False), gr.update(visible=True), ""
        else:
            return False, gr.update(visible=True), gr.update(visible=False), "*❌ Invalid credentials! Try again.*"

    login_btn.click(fn=check_login,
                    inputs=[username, password],
                    outputs=[login_status, login_section, app_section, login_msg])

    simulate_btn.click(fn=create_animated_map,
                       inputs=[],
                       outputs=map_output)
    map_timer.tick(fn=create_animated_map,
                       inputs=[],
                       outputs=map_output)
    

if __name__ == "__main__":
    demo.launch()