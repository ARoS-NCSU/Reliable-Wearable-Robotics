import sys
import threading
import time
import os
import picamera
import datetime
import RPi.GPIO as GPIO


def toggle_led():
    # Check LED state
    if GPIO.input(24) == True:
        GPIO.output(24, False)
    else:
        GPIO.output(24, True)

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button to GPIO23
GPIO.setup(24, GPIO.OUT)  # LED to GPIO24
GPIO.output(24, False)
shutdown_time = 10

#Idle time
time.sleep(2)
# Sign that continue button script is running
GPIO.output(24, True)

# Start timer to shutdown
t0 = time.time()
while True:
    if time.time() - t0 <= shutdown_time:
        button_state_is_on = not GPIO.input(23)
        if button_state_is_on is True:
            for k in range(0, 3):
                toggle_led()
                time.sleep(0.1)
            break
    else:
        os.system('sudo poweroff')
    time.sleep(0.01)

GPIO.output(24, False)
GPIO.cleanup()