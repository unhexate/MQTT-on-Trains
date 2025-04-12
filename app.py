import gradio as gr
from train_system import TrainSystem

system = TrainSystem()
unique_stations = sorted(set(system.df["Source_Station"]) | set(system.df["Destination_Station"]))

with gr.Blocks() as demo:
    gr.Markdown("## 🚆 Book Local Trains - Delay, MQTT, and Socket")

    with gr.Tab("🎟 Book Train"):
        src = gr.Dropdown(choices=unique_stations, label="Source Station")
        dst = gr.Dropdown(choices=unique_stations, label="Destination Station")
        book_btn = gr.Button("Book")
        book_output = gr.Textbox(label="Available Trains")
        book_btn.click(fn=system.book_trains, inputs=[src, dst], outputs=book_output)

    with gr.Tab("📡 MQTT Message"):
        train_name = gr.Textbox(label="Train Name")
        mqtt_msg = gr.Textbox(label="Message")
        mqtt_btn = gr.Button("Send MQTT")
        mqtt_output = gr.Textbox(label="MQTT Output")
        mqtt_btn.click(fn=system.mqtt_client.send_message, inputs=[train_name, mqtt_msg], outputs=mqtt_output)

    with gr.Tab("🔌 Socket Message"):
        socket_msg = gr.Textbox(label="Message")
        socket_btn = gr.Button("Send to Socket")
        socket_output = gr.Textbox(label="Response")
        socket_btn.click(fn=system.send_socket_data, inputs=socket_msg, outputs=socket_output)

demo.launch()
