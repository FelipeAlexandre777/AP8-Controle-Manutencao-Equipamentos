import os
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, reason_code, properties):
    print("Atuador conectado. Aguardando comandos...", flush=True)
    client.subscribe("minefleet/actuators/commands", qos=1)

def on_message(client, userdata, message):
    print("COMANDO RECEBIDO PELO ATUADOR:", message.payload.decode(), flush=True)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="minefleet-actuator")
client.on_connect = on_connect
client.on_message = on_message
client.connect(os.getenv("MQTT_HOST", "localhost"), 1883, 60)
client.loop_forever()
