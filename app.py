import gradio as gr
import json
import os
import socket
import random
import folium
from folium.plugins import AntPath

# ----------------------------
# User Storage
# ----------------------------
USER_DB = "users.json"
if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f:
        json.dump({}, f)

def save_user(email, password):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    if email in users:
        return "User already exists."
    users[email] = {"password": password}
    with open(USER_DB, "w") as f:
        json.dump(users, f)
    return "Sign up successful! Please login."

def verify_user(email, password):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    return users.get(email, {}).get("password") == password

# ----------------------------
# Dummy Train App Helpers
# ----------------------------

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

def create_animated_map():
    cities = list(TOP_CITIES.keys())
    train_a_source, train_a_destination = random.sample(cities, 2)
    train_b_source, train_b_destination = random.sample(cities, 2)

    train_a_start_coords = TOP_CITIES[train_a_source]
    train_a_end_coords = TOP_CITIES[train_a_destination]
    train_b_start_coords = TOP_CITIES[train_b_source]
    train_b_end_coords = TOP_CITIES[train_b_destination]

    center_lat = (train_a_start_coords[0] + train_a_end_coords[0] +
                  train_b_start_coords[0] + train_b_end_coords[0]) / 4
    center_lng = (train_a_start_coords[1] + train_a_end_coords[1] +
                  train_b_start_coords[1] + train_b_end_coords[1]) / 4

    m = folium.Map(location=[center_lat, center_lng], zoom_start=6)

    AntPath([train_a_start_coords, train_a_end_coords], color='blue').add_to(m)
    AntPath([train_b_start_coords, train_b_end_coords], color='red').add_to(m)

    folium.Marker(train_a_start_coords, tooltip="Train A Start").add_to(m)
    folium.Marker(train_a_end_coords, tooltip="Train A End").add_to(m)
    folium.Marker(train_b_start_coords, tooltip="Train B Start").add_to(m)
    folium.Marker(train_b_end_coords, tooltip="Train B End").add_to(m)

    return m._repr_html_()

# ----------------------------
# Gradio App UI
# ----------------------------

with gr.Blocks() as app:
    state = gr.State(value="home")  # states: home, signin, login, app
    logged_user = gr.State(value="")

    # HOME PAGE
    with gr.Column(visible=True) as home_screen:
        gr.Markdown("## 👋 Welcome to the Train Simulator")
        gr.Markdown("Choose an option to continue:")
        go_login = gr.Button("🔐 Login")
        go_signup = gr.Button("📝 Sign Up")

    # SIGNUP SCREEN
    with gr.Column(visible=False) as signup_screen:
        gr.Markdown("### 📝 Create an Account")
        signup_email = gr.Textbox(label="Email")
        signup_pass = gr.Textbox(label="Password", type="password")
        signup_btn = gr.Button("Sign Up")
        signup_msg = gr.Textbox(label="Status", interactive=False)
        back_to_home1 = gr.Button("⬅️ Back")

    # LOGIN SCREEN
    with gr.Column(visible=False) as login_screen:
        gr.Markdown("### 🔐 Log In")
        login_email = gr.Textbox(label="Email")
        login_pass = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_msg = gr.Textbox(label="Status", interactive=False)
        back_to_home2 = gr.Button("⬅️ Back")

    # MAIN APP
    with gr.Column(visible=False) as app_screen:
        gr.Markdown("# 🚂 Train Route Simulator")
        gr.Markdown("Simulates train journeys between random Indian cities.")
        simulate_btn = gr.Button("Simulate Trains")
        map_output = gr.HTML()
        logout_btn = gr.Button("Logout")

    # ---------- Logic ----------

    def switch_state(new_state):
        return {
            home_screen: gr.update(visible=new_state == "home"),
            signup_screen: gr.update(visible=new_state == "signup"),
            login_screen: gr.update(visible=new_state == "login"),
            app_screen: gr.update(visible=new_state == "app")
        }

    def signup(email, pwd):
        msg = save_user(email, pwd)
        return msg, "login" if "successful" in msg else "signup"

    def login(email, pwd):
        if verify_user(email, pwd):
            return "✅ Logged in!", "app", email
        return "❌ Invalid credentials.", "login", ""

    def logout():
        return "home", ""

    # ---------- Events ----------

    go_login.click(lambda: "login", outputs=state)
    go_signup.click(lambda: "signup", outputs=state)
    back_to_home1.click(lambda: "home", outputs=state)
    back_to_home2.click(lambda: "home", outputs=state)

    signup_btn.click(signup, inputs=[signup_email, signup_pass], outputs=[signup_msg, state])
    login_btn.click(login, inputs=[login_email, login_pass], outputs=[login_msg, state, logged_user])
    logout_btn.click(logout, outputs=[state, logged_user])
    simulate_btn.click(create_animated_map, outputs=map_output)

    state.change(fn=switch_state, inputs=state, outputs=[
        home_screen, signup_screen, login_screen, app_screen
    ])

app.launch()
