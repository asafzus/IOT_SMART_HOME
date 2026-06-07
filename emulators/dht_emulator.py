import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

import random
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *

global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = 'baby_dht_' + str(r)
update_rate = 5000  # ms


class Mqtt_client():

    def __init__(self):
        self.broker = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.on_connected_to_form = ''

    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form

    def set_broker(self, value):
        self.broker = value

    def set_port(self, value):
        self.port = value

    def set_clientName(self, value):
        self.clientname = value

    def set_username(self, value):
        self.username = value

    def set_password(self, value):
        self.password = value

    def on_log(self, client, userdata, level, buf):
        print('log: ' + buf)

    def on_connect(self, client, userdata, flags, rc):
        global CONNECTED
        if rc == 0:
            print('connected OK')
            CONNECTED = True
            self.on_connected_to_form()
        else:
            print('Bad connection Returned code=', rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        global CONNECTED
        CONNECTED = False
        print('DisConnected result code ' + str(rc))

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        m_decode = str(msg.payload.decode('utf-8', 'ignore'))
        print('message from:' + topic, m_decode)

    def connect_to(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        print('Connecting to broker ', self.broker)
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_start()

    def stop_listening(self):
        self.client.loop_stop()

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)
        else:
            print('Not connected')


class ConnectionDock(QDockWidget):

    def __init__(self, mc):
        QDockWidget.__init__(self)
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        self.eConnectbtn = QPushButton('Enable/Connect', self)
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet('background-color: gray')

        self.ePublisherTopic = QLineEdit()
        self.ePublisherTopic.setText(topic_dht)

        self.Temperature = QLineEdit()
        self.Temperature.setReadOnly(True)

        self.Humidity = QLineEdit()
        self.Humidity.setReadOnly(True)

        # test buttons
        self.btnTempHigh = QPushButton('Temp Too High (27C)')
        self.btnTempHigh.clicked.connect(lambda: mainwin.set_test_values(27.0, None))
        self.btnTempHigh.setStyleSheet('background-color: orange;')

        self.btnTempLow = QPushButton('Temp Too Low (13C)')
        self.btnTempLow.clicked.connect(lambda: mainwin.set_test_values(13.0, None))
        self.btnTempLow.setStyleSheet('background-color: lightblue;')

        self.btnHumHigh = QPushButton('Humidity Too High (65%)')
        self.btnHumHigh.clicked.connect(lambda: mainwin.set_test_values(None, 65.0))
        self.btnHumHigh.setStyleSheet('background-color: lightyellow;')

        self.btnHumLow = QPushButton('Humidity Too Low (25%)')
        self.btnHumLow.clicked.connect(lambda: mainwin.set_test_values(None, 25.0))
        self.btnHumLow.setStyleSheet('background-color: lightyellow;')

        self.btnNormal = QPushButton('Reset to Normal (20C, 50%)')
        self.btnNormal.clicked.connect(lambda: mainwin.set_test_values(20.0, 50.0))
        self.btnNormal.setStyleSheet('background-color: lightgreen;')

        formLayout = QFormLayout()
        formLayout.addRow('Turn On/Off', self.eConnectbtn)
        formLayout.addRow('Pub topic', self.ePublisherTopic)
        formLayout.addRow('Temperature (C)', self.Temperature)
        formLayout.addRow('Humidity (%)', self.Humidity)
        formLayout.addRow('', self.btnTempHigh)
        formLayout.addRow('', self.btnTempLow)
        formLayout.addRow('', self.btnHumHigh)
        formLayout.addRow('', self.btnHumLow)
        formLayout.addRow('', self.btnNormal)

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle('DHT Sensor')

    def on_connected(self):
        self.eConnectbtn.setStyleSheet('background-color: green')

    def on_button_connect_click(self):
        self.mc.set_broker(broker_ip)
        self.mc.set_port(int(broker_port))
        self.mc.set_clientName(clientname)
        self.mc.set_username(username)
        self.mc.set_password(password)
        self.mc.connect_to()
        self.mc.start_listening()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()

        self.temp_current = 20.0
        self.hum_current = 50.0

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)

        self.setGeometry(30, 600, 340, 320)
        self.setWindowTitle('DHT Emulator - Baby Room')

        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

    def set_test_values(self, temp, hum):
        if temp is not None:
            self.temp_current = temp
        if hum is not None:
            self.hum_current = hum

    def update_data(self):
        self.temp_current += random.uniform(-0.8, 0.8)
        self.hum_current += random.uniform(-2.0, 2.0)
        self.temp_current = round(self.temp_current, 1)
        self.hum_current = round(max(10.0, min(90.0, self.hum_current)), 1)

        current_data = 'Temperature: ' + str(self.temp_current) + ' Humidity: ' + str(self.hum_current)
        self.connectionDock.Temperature.setText(str(self.temp_current))
        self.connectionDock.Humidity.setText(str(self.hum_current))
        self.mc.publish_to(self.connectionDock.ePublisherTopic.text(), current_data)
        print('Published: ' + current_data)


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
