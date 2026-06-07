import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database'))

import paho.mqtt.client as mqtt
import time
import random
from datetime import datetime
from mqtt_init import *
from db import create_table, insert_reading

armed = False
last_relay_status = 'OFF'


def time_format():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '  Manager|> '


def on_log(client, userdata, level, buf):
    print('log: ' + buf)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(time_format() + 'connected OK')
    else:
        print(time_format() + 'Bad connection Returned code=' + str(rc))


def on_disconnect(client, userdata, flags, rc=0):
    print(time_format() + 'DisConnected result code ' + str(rc))


def on_message(client, userdata, msg):
    global armed, last_relay_status
    topic = msg.topic
    m_decode = str(msg.payload.decode('utf-8', 'ignore'))
    print(time_format() + 'message from: ' + topic + ' | ' + m_decode)

    if topic == topic_button:
        handle_button(client, m_decode)

    elif topic == topic_dht:
        handle_dht(client, m_decode)

    elif topic == topic_heater_sts:
        print(time_format() + 'Heater status updated: ' + m_decode.strip())

    elif topic == topic_cooler_sts:
        print(time_format() + 'Cooler status updated: ' + m_decode.strip())

    elif topic == topic_humidifier_sts:
        print(time_format() + 'Humidifier status updated: ' + m_decode.strip())


def handle_button(client, message):
    global armed
    if message.strip() == 'ARM':
        armed = True
        alert = 'INFO: System ARMED by parent'
        print(time_format() + alert)
        send_msg(client, topic_alarm, alert)
    elif message.strip() == 'DISARM':
        armed = False
        alert = 'INFO: System DISARMED by parent'
        print(time_format() + alert)
        send_msg(client, topic_alarm, alert)
        send_msg(client, topic_heater_cmd, 'OFF')
        send_msg(client, topic_cooler_cmd, 'OFF')
        send_msg(client, topic_humidifier_cmd, 'OFF')


def handle_dht(client, message):
    global last_relay_status
    try:
        parts = message.split(' ')
        temp = float(parts[1])
        hum = float(parts[3])
    except (IndexError, ValueError):
        print(time_format() + 'Failed to parse DHT message: ' + message)
        return

    alert_level, alert_message = evaluate_thresholds(temp, hum)

    heater_cmd = 'ON' if armed and temp < TEMP_WARNING_MIN else 'OFF'
    cooler_cmd = 'ON' if armed and temp > TEMP_WARNING_MAX else 'OFF'
    humidifier_cmd = 'ON' if armed and hum < HUM_WARNING_MIN else 'OFF'
    send_msg(client, topic_heater_cmd, heater_cmd)
    send_msg(client, topic_cooler_cmd, cooler_cmd)
    send_msg(client, topic_humidifier_cmd, humidifier_cmd)

    send_msg(client, topic_alarm, alert_level + ': ' + alert_message)

    print(time_format() + alert_level + ' | Temp=' + str(temp) + ' Hum=' + str(hum) + ' Heater=' + heater_cmd + ' Cooler=' + cooler_cmd + ' Humidifier=' + humidifier_cmd)

    insert_reading(temp, hum, 'H:' + heater_cmd + '/C:' + cooler_cmd + '/HUM:' + humidifier_cmd, alert_level, alert_message)


def evaluate_thresholds(temp, hum):
    if temp < TEMP_ALARM_MIN or temp > TEMP_ALARM_MAX:
        return 'ALARM', 'Temperature critical: ' + str(temp) + 'C'
    if hum < HUM_ALARM_MIN:
        return 'ALARM', 'Humidity critical: ' + str(hum) + '%'
    if temp < TEMP_WARNING_MIN or temp > TEMP_WARNING_MAX:
        return 'WARNING', 'Temperature out of safe range: ' + str(temp) + 'C (safe: ' + str(TEMP_WARNING_MIN) + '-' + str(TEMP_WARNING_MAX) + 'C)'
    if hum < HUM_WARNING_MIN or hum > HUM_WARNING_MAX:
        return 'WARNING', 'Humidity out of safe range: ' + str(hum) + '% (safe: ' + str(HUM_WARNING_MIN) + '-' + str(HUM_WARNING_MAX) + '%)'
    return 'INFO', 'Safe - Temp: ' + str(temp) + 'C, Humidity: ' + str(hum) + '%'


def send_msg(client, topic, message):
    print(time_format() + 'Sending: [' + topic + '] ' + message)
    client.publish(topic, message)


def client_init():
    r = random.randrange(1, 10000000)
    cname = 'baby_manager_' + str(r)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, cname, clean_session=True)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.on_message = on_message
    if username != '':
        client.username_pw_set(username, password)
    print(time_format() + 'Connecting to broker ' + broker_ip)
    client.connect(broker_ip, int(broker_port))
    return client


def main():
    create_table()
    client = client_init()
    client.loop_start()
    client.subscribe(topic_dht)
    client.subscribe(topic_button)
    client.subscribe(topic_heater_sts)
    client.subscribe(topic_cooler_sts)
    client.subscribe(topic_humidifier_sts)
    print(time_format() + 'Data Manager running. Subscribed to all topics.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(time_format() + 'Interrupted by keyboard')
    client.loop_stop()
    client.disconnect()
    print(time_format() + 'Data Manager stopped')


if __name__ == '__main__':
    main()
