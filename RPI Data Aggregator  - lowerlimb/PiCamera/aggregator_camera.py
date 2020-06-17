#!/usr/bin/ python
'''
Golden version with the following architecture:
*Process 1(P1): Thread 1, 2: Runs IMU reading,
*Process 2(P2): Saves Acc
*Process 3(P3): Saves Gyro
*Process 4(P4): Runs and Saves camera reading (PICamera)
Interrupted by GPIO
Halted execution after finishing is fixed
'''
import sys
import threading
import time
import psutil
import operator
import multiprocessing as mp
import operator
from Adafruit_BNO055 import BNO055
import cv2
import os
import picamera
import datetime
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray


def monitor(main_p, ):
    general_cpu = []
    cpu_cplist = []
    mem_cplist = []
    while not event.is_set():
        general_cpu.append(psutil.cpu_percent(interval=None, percpu=True))
        cpu_cplist.append(main_p.cpu_percent())
        mem_cplist.append(main_p.memory_percent())

        time.sleep(0.11)
    print('--------------')
    print('Average CPU use per core is: {}'.format([x / len(general_cpu) for x in [sum(i) for i in zip(*general_cpu)]]))
    print('--------------')
    print('Main process: Average CPU usage is: {}'.format(sum(cpu_cplist) / len(cpu_cplist)))
    print('--------------')
    print('Main process: Average Memory percentage use: {}'.format(str(sum(mem_cplist) / len(mem_cplist))))


def key_monitor():
    global date_now
    # Button counter for debouncing purposes
    stop_counter = 0

    while not event.is_set():
        button_state_is_on = input()  # not GPIO.input(23)

        # Currently finishes the program after hitting space twice
        if button_state_is_on == ' ':
            print('{} :: key_monitor :: Button Pressed !!'.format(str(datetime.datetime.now())[11:]))
            if stop_counter == 0:
                stop_counter += 1
                print('{} :: key_monitor :: button_counter:{}'.format(str(datetime.datetime.now())[11:], stop_counter))
                t0 = time.time()
            # Button debouncing
            elif (time.time() - t0 > 0.5) and (time.time() - t0 < 4) and stop_counter >= 1:
                print('{} :: key_monitor :: wrapping up !!!'.format(str(datetime.datetime.now())[11:]))
                event.set()
                cv2.destroyAllWindows()
                '''
                # Write mp4 file
                print('Converting h264 raw video format to mp4..')
                cmd = 'sudo MP4Box -add cam_stream_' + date_now + '.h264 -fps 20 output_' + \
                      date_now + '.mp4'
                os.system(cmd)
                '''
                # Turn wifi on to turn the system back to normal
                cmd = 'sudo ifconfig wlan0 up'
                os.system(cmd)
                # Indication that the system is ready to be turned off
                print('{} :: key_monitor :: Key Monitor: Finished waiting'.format(str(datetime.datetime.now())[11:]))
            elif (time.time() - t0 > 4) or (time.time() - t0 < 1):
                stop_counter = 0
                print('{} :: key_monitor :: button_counter:{}'.format(str(datetime.datetime.now())[11:], stop_counter))

        time.sleep(0.1)


def led_status():
    GPIO.output(24, True)
    while key.is_alive() or vigilant.is_alive():

        toggle_led()
        if not event.is_set():
            # Recording
            time.sleep(0.5)
        else:
            # Finished recording - writing to disk
            time.sleep(0.1)
    GPIO.output(24, False)


def toggle_led():
    # Check LED state
    if GPIO.input(24) == True:
        GPIO.output(24, False)
    else:
        GPIO.output(24, True)


if __name__ == '__main__':

    # Data ID label and formatting
    date_now = str(datetime.datetime.now()).replace(' ', '_')
    date_now = date_now.replace(':', '_')
    date_now = date_now.replace('.', '_')
    # Store when sensors started to compare with the camera
    recording_start = time.time()
    # initialize the connections
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button to GPIO23
    GPIO.setup(24, GPIO.OUT)  # LED to GPIO24
    GPIO.output(24, False)

    # Turn wifi off to avoid resynchronization gaps in data's timestamp
    '''
    cmd = 'ifconfig wlan0 down'
    os.system(cmd)
    '''

    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('{} :: main :: Starting script..'.format(str(datetime.datetime.now())[11:]))
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

    event = mp.Event()
    # create queues to share data between threads/processes
    led_event = mp.Event()


    # initialize processes
    key = threading.Thread(target=key_monitor, args=())
    led = threading.Thread(target=led_status, args=())

    # setup monitoring
    main_pid = os.getpid()
    main_p = psutil.Process(main_pid)

    vigilant = threading.Thread(target=monitor, args=(main_p, ))
    print(psutil.cpu_percent(interval=0.1, percpu=1))
    print('{} :: main :: Program started on {}'.format(str(datetime.datetime.now())[11:], date_now))

    # launch processes/threads

    key.start()
    vigilant.start()
    led.start()

    print(str(datetime.datetime.now())[11:] + ' :: main :: Main process PID: %d' % main_pid)

    with picamera.PiCamera() as camera:
        timestamp = 0
        camera.resolution = (1640, 922)
        #camera.framerate = 30
        camera.annotate_background = picamera.Color('black')
        camera.start_recording('cam_stream_' + date_now + '.h264')
        while not event.is_set():
            '''
            if timestamp != camera.frame.timestamp:
                tmp = time.time()
                camera.annotate_text = str(tmp - recording_start)
                timestamp = camera.frame.timestamp
                q.put((tmp, timestamp))
        q.put((time.time(), camera.frame.timestamp))
        '''
            camera.wait_recording(1)
        print('Cam: finished reading')
        camera.close()

    vigilant.join()
    key.join()
    led.join()

