import socket

nb = 1  # 0 - HIT, 1 - open HiveMQ
brokers = [str(socket.gethostbyname('vmm1.saaintertrade.com')), str(socket.gethostbyname('broker.hivemq.com'))]
ports = ['80', '1883']
usernames = ['MATZI', '']
passwords = ['MATZI', '']

broker_ip = brokers[nb]
broker_port = ports[nb]
username = usernames[nb]
password = passwords[nb]
conn_time = 0  # 0 stands for endless loop

# Topics
topic_dht = 'ABO/baby/room/dht'
topic_button = 'ABO/baby/room/button'
topic_heater_cmd = 'ABO/baby/room/heater/cmd'
topic_heater_sts = 'ABO/baby/room/heater/sts'
topic_cooler_cmd = 'ABO/baby/room/cooler/cmd'
topic_cooler_sts = 'ABO/baby/room/cooler/sts'
topic_humidifier_cmd = 'ABO/baby/room/humidifier/cmd'
topic_humidifier_sts = 'ABO/baby/room/humidifier/sts'
topic_alarm = 'ABO/baby/room/alarm'

# Thresholds
TEMP_WARNING_MIN = 18.0
TEMP_WARNING_MAX = 22.0
TEMP_ALARM_MIN = 15.0
TEMP_ALARM_MAX = 26.0
HUM_WARNING_MIN = 40.0
HUM_WARNING_MAX = 60.0
HUM_ALARM_MIN = 30.0
