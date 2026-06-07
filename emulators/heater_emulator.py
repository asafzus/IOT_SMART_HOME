import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *

global clientname, heater_on
heater_on = False
r = random.randrange(1, 10000000)
clientname = 'baby_heater_' + str(r)


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
        if rc == 0:
            print('connected OK')
            self.on_connected_to_form()
        else:
            print('Bad connection Returned code=', rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        print('DisConnected result code ' + str(rc))

    def on_message(self, client, userdata, msg):
        m_decode = str(msg.payload.decode('utf-8', 'ignore'))
        mainwin.cmd_received.emit(m_decode)

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

    def subscribe_to(self, topic):
        self.client.subscribe(topic)

    def publish_to(self, topic, message):
        self.client.publish(topic, message)


class ConnectionDock(QDockWidget):

    def __init__(self, mc):
        QDockWidget.__init__(self)
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        self.eConnectbtn = QPushButton('Enable/Connect', self)
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet('background-color: gray')

        self.eSubscribeTopic = QLineEdit()
        self.eSubscribeTopic.setText(topic_heater_cmd)

        self.eStatus = QPushButton('HEATER: OFF', self)
        self.eStatus.setStyleSheet('background-color: gray; font-weight: bold;')

        formLayout = QFormLayout()
        formLayout.addRow('Turn On/Off', self.eConnectbtn)
        formLayout.addRow('Sub topic', self.eSubscribeTopic)
        formLayout.addRow('Status', self.eStatus)

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle('Heater Emulator')

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
        self.mc.subscribe_to(self.eSubscribeTopic.text())

    def update_state(self, command):
        global heater_on
        if command.strip() == 'ON':
            heater_on = True
            self.eStatus.setText('HEATER: ON')
            self.eStatus.setStyleSheet('background-color: orange; font-weight: bold;')
            self.mc.publish_to(topic_heater_sts, 'ON')
            print('Heater turned ON')
        elif command.strip() == 'OFF':
            heater_on = False
            self.eStatus.setText('HEATER: OFF')
            self.eStatus.setStyleSheet('background-color: gray; font-weight: bold;')
            self.mc.publish_to(topic_heater_sts, 'OFF')
            print('Heater turned OFF')


class MainWindow(QMainWindow):

    cmd_received = pyqtSignal(str)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()

        self.setGeometry(30, 350, 320, 160)
        self.setWindowTitle('Heater Emulator - Baby Room')

        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)
        self.cmd_received.connect(self.connectionDock.update_state)


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
