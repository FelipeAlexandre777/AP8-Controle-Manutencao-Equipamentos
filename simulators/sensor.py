import json, os, random, time
import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="minefleet-sensor")
client.connect(os.getenv("MQTT_HOST", "localhost"), 1883, 60)
client.loop_start()
try:
    while True:
        sample = {"vehicle_id": "CAM-042",
                  "temperature_c": round(random.uniform(75, 112), 1),
                  "oil_pressure_bar": round(random.uniform(2, 5), 2),
                  "speed_kmh": round(random.uniform(0, 38), 1),
                  "fuel_percent": round(random.uniform(15, 95), 1),
                  "timestamp": time.time()}
        client.publish("minefleet/sensors/telemetry", json.dumps(sample), qos=1)
        print("Telemetria publicada:", sample, flush=True)
        time.sleep(3)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
