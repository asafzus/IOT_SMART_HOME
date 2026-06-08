import paho.mqtt.client as mqtt

try:
    # paho-mqtt 2.0+
    from paho.mqtt.client import CallbackAPIVersion
    MQTT_CLIENT_INIT = lambda name: mqtt.Client(CallbackAPIVersion.VERSION1, name)
except ImportError:
    # paho-mqtt 1.x
    MQTT_CLIENT_INIT = lambda name: mqtt.Client(name, clean_session=True)
