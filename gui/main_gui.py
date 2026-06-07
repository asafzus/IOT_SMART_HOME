import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

import math
import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *

# Color palette - soft baby room theme
BG           = '#F0F8FF'
PANEL        = '#E8F4FD'
HEADER_BG    = '#BBDEFB'
BORDER       = '#90CAF9'
TEXT_PRIMARY = '#1565C0'
COLOR_NORMAL  = '#43A047'
COLOR_WARNING = '#FB8C00'
COLOR_ALARM   = '#E53935'
COLOR_OFF     = '#90A4AE'

global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = 'baby_gui_' + str(r)


class Mqtt_client():

    def __init__(self):
        self.broker = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.on_connected_to_form = ''

    def set_on_connected_to_form(self, f):
        self.on_connected_to_form = f

    def set_broker(self, v):
        self.broker = v

    def set_port(self, v):
        self.port = v

    def set_clientName(self, v):
        self.clientname = v

    def set_username(self, v):
        self.username = v

    def set_password(self, v):
        self.password = v

    def on_log(self, client, userdata, level, buf):
        print('log: ' + buf)

    def on_connect(self, client, userdata, flags, rc):
        global CONNECTED
        if rc == 0:
            CONNECTED = True
            self.on_connected_to_form()
        else:
            print('Bad connection rc=', rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        global CONNECTED
        CONNECTED = False

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        m_decode = str(msg.payload.decode('utf-8', 'ignore'))
        mainwin.message_received.emit(topic, m_decode)

    def connect_to(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_start()

    def stop_listening(self):
        self.client.loop_stop()

    def subscribe_to(self, topic):
        self.client.subscribe(topic)

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)


class GaugeWidget(QFrame):
    # Arc dial gauge: 210° start, -240° clockwise sweep (like a speedometer)
    _START = 210
    _SPAN  = -240

    def __init__(self, title, unit, min_val, max_val, warn_min, warn_max, alarm_min, alarm_max):
        super().__init__()
        self.title     = title
        self.unit      = unit
        self.min_val   = float(min_val)
        self.max_val   = float(max_val)
        self.warn_min  = float(warn_min)
        self.warn_max  = float(warn_max)
        self.alarm_min = float(alarm_min)
        self.alarm_max = float(alarm_max)
        self.value     = None

        self.setStyleSheet(f'background-color: {PANEL}; border-radius: 12px; border: 2px solid {BORDER};')
        self.setMinimumSize(280, 220)

    def _color_for(self, v):
        if v is None:
            return QColor(COLOR_OFF)
        if v < self.alarm_min or v > self.alarm_max:
            return QColor(COLOR_ALARM)
        if v < self.warn_min or v > self.warn_max:
            return QColor(COLOR_WARNING)
        return QColor(COLOR_NORMAL)

    def update_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx = w // 2
        top = 32            # space reserved for title above the arc
        avail = h - top - 14
        r = min(w // 2 - 22, avail - 10)
        cy = top + r + 4

        arc_w  = 15
        arc_rect = QRect(cx - r, cy - r, r * 2, r * 2)

        # Background arc
        pen = QPen(QColor('#D0D8DF'), arc_w, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(arc_rect, self._START * 16, self._SPAN * 16)

        # Colored value arc
        color = self._color_for(self.value)
        if self.value is not None:
            pct = (self.value - self.min_val) / (self.max_val - self.min_val)
            pct = max(0.0, min(1.0, pct))
            filled = int(self._SPAN * pct) * 16
            pen = QPen(color, arc_w, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.drawArc(arc_rect, self._START * 16, filled)

        # Title
        p.setPen(QColor(TEXT_PRIMARY))
        p.setFont(QFont('Arial', 11, QFont.Bold))
        p.drawText(QRect(0, 6, w, 22), Qt.AlignCenter, self.title)

        # Value text
        val_str = f'{self.value}{self.unit}' if self.value is not None else '--'
        p.setPen(color)
        p.setFont(QFont('Arial', 23, QFont.Bold))
        p.drawText(QRect(cx - 90, cy - 20, 180, 42), Qt.AlignCenter, val_str)

        # Status text
        if self.value is not None:
            if self.value < self.alarm_min or self.value > self.alarm_max:
                status = 'ALARM'
            elif self.value < self.warn_min or self.value > self.warn_max:
                status = 'WARNING'
            else:
                status = 'NORMAL'
        else:
            status = 'NO DATA'
        p.setFont(QFont('Arial', 9, QFont.Bold))
        p.drawText(QRect(cx - 60, cy + 25, 120, 18), Qt.AlignCenter, status)

        # Min / max labels at arc endpoints
        p.setPen(QColor('#78909C'))
        p.setFont(QFont('Arial', 8))
        off = r + 18
        end_deg = self._START + self._SPAN   # = -30
        for deg, label in ((self._START, str(int(self.min_val))), (end_deg, str(int(self.max_val)))):
            lx = cx + int(off * math.cos(math.radians(deg)))
            ly = cy - int(off * math.sin(math.radians(deg)))
            p.drawText(QRect(lx - 18, ly - 8, 36, 16), Qt.AlignCenter, label)

        p.end()


class DeviceWidget(QFrame):

    def __init__(self, name, icon, active_color):
        super().__init__()
        self.active_color = active_color
        self._is_on = False

        self.setStyleSheet(f'background-color: {PANEL}; border-radius: 12px; border: 2px solid {BORDER};')
        self.setMinimumSize(160, 140)
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.iconLabel = QLabel(icon)
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.iconLabel.setStyleSheet('font-size: 40px; border: none; background: transparent;')

        self.nameLabel = QLabel(name)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.setStyleSheet(f'color: {TEXT_PRIMARY}; font-size: 13px; font-weight: bold; border: none; background: transparent;')

        self.statusLabel = QLabel('OFF')
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setFixedWidth(70)
        self.statusLabel.setStyleSheet(f'color: white; font-size: 12px; font-weight: bold; border: none; padding: 3px 8px; border-radius: 6px; background-color: {COLOR_OFF};')

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.statusLabel, alignment=Qt.AlignCenter)

        # start grayed out
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(0.35)
        self.iconLabel.setGraphicsEffect(effect)

    def set_active(self, is_on):
        effect = QGraphicsOpacityEffect()
        if is_on:
            effect.setOpacity(1.0)
            self.statusLabel.setText('ON')
            self.statusLabel.setStyleSheet(f'color: white; font-size: 12px; font-weight: bold; border: none; padding: 3px 8px; border-radius: 6px; background-color: {self.active_color};')
            self.setStyleSheet(f'background-color: {PANEL}; border-radius: 12px; border: 2px solid {self.active_color};')
        else:
            effect.setOpacity(0.35)
            self.statusLabel.setText('OFF')
            self.statusLabel.setStyleSheet(f'color: white; font-size: 12px; font-weight: bold; border: none; padding: 3px 8px; border-radius: 6px; background-color: {COLOR_OFF};')
            self.setStyleSheet(f'background-color: {PANEL}; border-radius: 12px; border: 2px solid {BORDER};')
        self.iconLabel.setGraphicsEffect(effect)


class AlarmLogWidget(QFrame):

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background-color: {PANEL}; border-radius: 12px; border: 2px solid {BORDER};')

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 10)
        outer.setSpacing(8)

        headerRow = QHBoxLayout()
        title = QLabel('Alarm Log')
        title.setStyleSheet(f'color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold; border: none; background: transparent;')

        self.clearBtn = QPushButton('Clear')
        self.clearBtn.setFixedSize(64, 28)
        self.clearBtn.setStyleSheet(f'''
            QPushButton {{
                background-color: {HEADER_BG};
                color: {TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {BORDER}; }}
        ''')
        self.clearBtn.clicked.connect(self.clear_log)

        headerRow.addWidget(title)
        headerRow.addStretch()
        headerRow.addWidget(self.clearBtn)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet('border: none; background: transparent;')
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cardsContainer = QWidget()
        self.cardsContainer.setStyleSheet('background: transparent;')
        self.cardsLayout = QVBoxLayout(self.cardsContainer)
        self.cardsLayout.setContentsMargins(0, 0, 4, 0)
        self.cardsLayout.setSpacing(5)
        self.cardsLayout.addStretch()

        self.scrollArea.setWidget(self.cardsContainer)

        outer.addLayout(headerRow)
        outer.addWidget(self.scrollArea)

    def add_card(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')

        if message.startswith('ALARM'):
            left_color = COLOR_ALARM
            bg_color = '#FFEBEE'
            level = 'ALARM'
        elif message.startswith('WARNING'):
            left_color = COLOR_WARNING
            bg_color = '#FFF8E1'
            level = 'WARNING'
        else:
            left_color = COLOR_NORMAL
            bg_color = '#F1F8E9'
            level = 'INFO'

        card = QFrame()
        card.setStyleSheet(f'background-color: {bg_color}; border-radius: 8px; border-left: 5px solid {left_color};')

        cardLayout = QHBoxLayout(card)
        cardLayout.setContentsMargins(10, 8, 10, 8)
        cardLayout.setSpacing(10)

        timeLabel = QLabel(timestamp)
        timeLabel.setFixedWidth(58)
        timeLabel.setStyleSheet('color: #78909C; font-size: 11px; border: none; background: transparent;')

        levelLabel = QLabel(level)
        levelLabel.setFixedWidth(62)
        levelLabel.setAlignment(Qt.AlignCenter)
        levelLabel.setStyleSheet(f'color: white; background-color: {left_color}; border-radius: 4px; font-size: 11px; font-weight: bold; padding: 2px 4px;')

        text = message
        for prefix in ('ALARM: ', 'WARNING: ', 'INFO: '):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break

        msgLabel = QLabel(text)
        msgLabel.setWordWrap(True)
        msgLabel.setStyleSheet('color: #37474F; font-size: 12px; border: none; background: transparent;')

        cardLayout.addWidget(timeLabel)
        cardLayout.addWidget(levelLabel)
        cardLayout.addWidget(msgLabel, stretch=1)

        self.cardsLayout.insertWidget(self.cardsLayout.count() - 1, card)
        QTimer.singleShot(50, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def clear_log(self):
        while self.cardsLayout.count() > 1:
            item = self.cardsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class MainWindow(QMainWindow):

    message_received = pyqtSignal(str, str)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.mc.set_on_connected_to_form(self.on_connected)
        self.message_received.connect(self.route_message)

        self.setWindowTitle('Smart Baby Room Monitor')
        self.setMinimumSize(920, 720)
        self.setStyleSheet(f'background-color: {BG};')

        central = QWidget()
        self.setCentralWidget(central)
        mainLayout = QVBoxLayout(central)
        mainLayout.setContentsMargins(16, 16, 16, 16)
        mainLayout.setSpacing(12)

        # Title
        titleBar = QLabel('🍼  Smart Baby Room Monitor')
        titleBar.setAlignment(Qt.AlignCenter)
        titleBar.setFixedHeight(52)
        titleBar.setStyleSheet(f'''
            background-color: {HEADER_BG};
            color: {TEXT_PRIMARY};
            font-size: 20px;
            font-weight: bold;
            border-radius: 10px;
            padding: 8px;
        ''')

        # Gauges row
        gaugesRow = QHBoxLayout()
        gaugesRow.setSpacing(12)
        self.tempGauge = GaugeWidget(
            'Temperature', '°C', 0, 40,
            TEMP_WARNING_MIN, TEMP_WARNING_MAX,
            TEMP_ALARM_MIN, TEMP_ALARM_MAX
        )
        self.humGauge = GaugeWidget(
            'Humidity', '%', 0, 100,
            HUM_WARNING_MIN, HUM_WARNING_MAX,
            HUM_ALARM_MIN, 100
        )
        gaugesRow.addWidget(self.tempGauge)
        gaugesRow.addWidget(self.humGauge)

        # Devices row
        devicesRow = QHBoxLayout()
        devicesRow.setSpacing(12)
        self.heaterWidget    = DeviceWidget('HEATER',     '🔥', COLOR_ALARM)
        self.coolerWidget    = DeviceWidget('COOLER',     '❄️', '#29B6F6')
        self.humidifierWidget= DeviceWidget('HUMIDIFIER', '💧', '#42A5F5')
        devicesRow.addStretch()
        devicesRow.addWidget(self.heaterWidget)
        devicesRow.addWidget(self.coolerWidget)
        devicesRow.addWidget(self.humidifierWidget)
        devicesRow.addStretch()

        # Status row
        statusRow = QHBoxLayout()
        statusRow.setSpacing(12)

        self.systemStatusLabel = QLabel('System: DISARMED')
        self.systemStatusLabel.setStyleSheet(f'''
            color: {COLOR_ALARM};
            font-size: 14px;
            font-weight: bold;
            background-color: {PANEL};
            border-radius: 8px;
            border: 2px solid {BORDER};
            padding: 8px 16px;
        ''')

        self.brokerLabel = QLabel(f'Broker: {broker_ip}')
        self.brokerLabel.setStyleSheet(f'color: {TEXT_PRIMARY}; font-size: 12px; background: transparent; border: none;')

        self.connectBtn = QPushButton('Connect to Broker')
        self.connectBtn.setFixedHeight(40)
        self.connectBtn.setStyleSheet(f'''
            QPushButton {{
                background-color: {COLOR_ALARM};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 24px;
            }}
            QPushButton:hover {{ background-color: #C62828; }}
        ''')
        self.connectBtn.clicked.connect(self.on_connect_click)

        statusRow.addWidget(self.systemStatusLabel)
        statusRow.addStretch()
        statusRow.addWidget(self.brokerLabel)
        statusRow.addWidget(self.connectBtn)

        # Alarm log
        self.alarmLog = AlarmLogWidget()

        mainLayout.addWidget(titleBar)
        mainLayout.addLayout(gaugesRow)
        mainLayout.addLayout(devicesRow)
        mainLayout.addLayout(statusRow)
        mainLayout.addWidget(self.alarmLog, stretch=1)

    def on_connect_click(self):
        self.mc.set_broker(broker_ip)
        self.mc.set_port(int(broker_port))
        self.mc.set_clientName(clientname)
        self.mc.set_username(username)
        self.mc.set_password(password)
        self.mc.connect_to()
        self.mc.start_listening()

    def on_connected(self):
        self.connectBtn.setText('Connected  ✓')
        self.connectBtn.setStyleSheet(f'''
            QPushButton {{
                background-color: {COLOR_NORMAL};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 24px;
            }}
        ''')
        self.mc.subscribe_to(topic_dht)
        self.mc.subscribe_to(topic_button)
        self.mc.subscribe_to(topic_heater_sts)
        self.mc.subscribe_to(topic_cooler_sts)
        self.mc.subscribe_to(topic_humidifier_sts)
        self.mc.subscribe_to(topic_alarm)

    def route_message(self, topic, message):
        if topic == topic_dht:
            try:
                parts = message.split(' ')
                temp = float(parts[1])
                hum = float(parts[3])
                self.tempGauge.update_value(temp)
                self.humGauge.update_value(hum)
            except (IndexError, ValueError):
                pass

        elif topic == topic_button:
            armed = message.strip() == 'ARM'
            status = 'ARMED' if armed else 'DISARMED'
            color = COLOR_NORMAL if armed else COLOR_ALARM
            self.systemStatusLabel.setText(f'System: {status}')
            self.systemStatusLabel.setStyleSheet(f'''
                color: {color};
                font-size: 14px;
                font-weight: bold;
                background-color: {PANEL};
                border-radius: 8px;
                border: 2px solid {BORDER};
                padding: 8px 16px;
            ''')

        elif topic == topic_heater_sts:
            self.heaterWidget.set_active(message.strip() == 'ON')

        elif topic == topic_cooler_sts:
            self.coolerWidget.set_active(message.strip() == 'ON')

        elif topic == topic_humidifier_sts:
            self.humidifierWidget.set_active(message.strip() == 'ON')

        elif topic == topic_alarm:
            self.alarmLog.add_card(message)


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
