import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *
from mqtt_utils import MQTT_CLIENT_INIT

global clientname, CONNECTED, armed
CONNECTED = False
armed = False
r = random.randrange(1, 10000000)
clientname = 'baby_button_' + str(r)


class Mqtt_client():

    def __init__(self):
        self.broker = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
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
            mainwin.connected.emit()
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
        self.client = MQTT_CLIENT_INIT(self.clientname)
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
            self.client.publish(topic, message, retain=True)
        else:
            print('Not connected')


class ConnectionDock(QDockWidget):

    def __init__(self, mc):
        QDockWidget.__init__(self)
        self.mc = mc

        self.eConnectbtn = QPushButton('Enable/Connect', self)
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet('background-color: gray')

        self.ePublisherTopic = QLineEdit()
        self.ePublisherTopic.setText(topic_button)

        self.eArmBtn = QPushButton('ARM SYSTEM', self)
        self.eArmBtn.setToolTip('Click to ARM or DISARM the baby room monitor')
        self.eArmBtn.clicked.connect(self.push_button_click)
        self.eArmBtn.setStyleSheet('background-color: red; font-weight: bold; font-size: 14px;')

        self.eStatusLabel = QLineEdit()
        self.eStatusLabel.setText('DISARMED')
        self.eStatusLabel.setReadOnly(True)
        self.eStatusLabel.setStyleSheet('color: red; font-weight: bold;')

        formLayout = QFormLayout()
        formLayout.addRow('Turn On/Off', self.eConnectbtn)
        formLayout.addRow('Pub topic', self.ePublisherTopic)
        formLayout.addRow('Button', self.eArmBtn)
        formLayout.addRow('System Status', self.eStatusLabel)

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle('Button Emulator')

    def on_connected(self):
        self.eConnectbtn.setStyleSheet('background-color: green')
        # Publish current state immediately to overwrite any stale retained message
        state = 'ARM' if armed else 'DISARM'
        self.mc.publish_to(self.ePublisherTopic.text(), state)

    def on_button_connect_click(self):
        self.mc.set_broker(broker_ip)
        self.mc.set_port(int(broker_port))
        self.mc.set_clientName(clientname)
        self.mc.set_username(username)
        self.mc.set_password(password)
        self.mc.connect_to()
        self.mc.start_listening()

    def push_button_click(self):
        global armed
        armed = not armed
        if armed:
            self.mc.publish_to(self.ePublisherTopic.text(), 'ARM')
            self.eArmBtn.setText('DISARM SYSTEM')
            self.eArmBtn.setStyleSheet('background-color: green; font-weight: bold; font-size: 14px;')
            self.eStatusLabel.setText('ARMED')
            self.eStatusLabel.setStyleSheet('color: green; font-weight: bold;')
            print('System ARMED')
        else:
            self.mc.publish_to(self.ePublisherTopic.text(), 'DISARM')
            self.eArmBtn.setText('ARM SYSTEM')
            self.eArmBtn.setStyleSheet('background-color: red; font-weight: bold; font-size: 14px;')
            self.eStatusLabel.setText('DISARMED')
            self.eStatusLabel.setStyleSheet('color: red; font-weight: bold;')
            print('System DISARMED')


class MainWindow(QMainWindow):

    connected = pyqtSignal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()

        self.setGeometry(30, 100, 320, 180)
        self.setWindowTitle('Button Emulator - Baby Room')

        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)
        self.connected.connect(self.connectionDock.on_connected)


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
