@echo off
echo Starting Smart Baby Room Monitor...

start "Data Manager" python data_manager\data_manager.py
timeout /t 2 /nobreak > nul

start "Main GUI" python gui\main_gui.py
timeout /t 1 /nobreak > nul

start "DHT Emulator" python emulators\dht_emulator.py
timeout /t 1 /nobreak > nul

start "Button Emulator" python emulators\button_emulator.py
timeout /t 1 /nobreak > nul

start "Heater Emulator" python emulators\heater_emulator.py
timeout /t 1 /nobreak > nul

start "Cooler Emulator" python emulators\cooler_emulator.py
timeout /t 1 /nobreak > nul

start "Humidifier Emulator" python emulators\humidifier_emulator.py

echo All components started!
