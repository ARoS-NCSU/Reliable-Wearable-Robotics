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


class AdaFruitBNO055:

    def __init__(self, freq_samp, label):
        self._name = label
        self._time_samp = 1.0 / freq_samp
        self._th_stop_event = threading.Event()
        self._counter = 0
        self._x_old = 0
        self._y_old = 0
        self._z_old = 0

    def get_event_status_th(self):
        return self._th_stop_event.is_set()

    def get_time_samp(self):
        return self._time_samp

    def set_event_th(self):
        self._th_stop_event.set()

    def set_count_up(self):
        self._counter += 1

    def get_counter(self):
        return self._counter


class Acc(AdaFruitBNO055):

    def __init__(self, freq_samp):
        self._label = 'Acc'
        AdaFruitBNO055.__init__(self, freq_samp, self._label)
    def get_acc(self, q):
        #thlock.acquire()
        x, y, z = bno.read_accelerometer()
        if (x != self._x_old) or (y != self._y_old) or (z != self._z_old):
            t = time.time()
            #thlock.release()
            q.put((t, (x, y, z), self.get_counter()))
            self._x_old = x
            self._y_old = y
            self._z_old = z
            self.set_count_up()
        else:
            pass


class Gyro(AdaFruitBNO055):

    def __init__(self, freq_samp):
        self._label = 'Gyro'
        AdaFruitBNO055.__init__(self, freq_samp, self._label)
    def get_gyro(self, q):
        #thlock.acquire()
        x, y, z = bno.read_gyroscope()
        if (x != self._x_old) or (y != self._y_old) or (z != self._z_old):
            t = time.time()
            #thlock.release()
            q.put((t, (x, y, z), self.get_counter()))
            self._x_old = x
            self._y_old = y
            self._z_old = z
            self.set_count_up()
        else:
            pass


class Camera:

    def __init__(self, freq_samp):
        self._time_samp = 1.0 / freq_samp
        self._mp_stop_event = mp.Event()
        self._th_stop_event = threading.Event()
        self._mplock = mp.Lock()
        self._counter = 0

    def get_camera(self, cam, q):
        # print('Cam: Reading camera')
        t = time.time()
        ret, frame = cam.read()
        q.put((t, frame, self.get_counter()))

    def get_event_status_th(self):
        return self._th_stop_event.is_set()

    def get_time_samp(self):
        return self._time_samp

    def set_count_up(self):
        self._counter += 1

    def get_counter(self):
        return self._counter

    def set_event_th(self):
        self._th_stop_event.set()


def save_cam_info_th(q, ev):


    global date_now
    print('Save Cam ID: %d' % os.getpid())
    try:
        infilename = "./" + 'cam_time_' + date_now + ".csv"
        infile = open(infilename, 'w')
        writeStr = "timestamp system" + ',' + 'timestamp picam gpu'
        infile.write(writeStr + "\n")
        writeStr = "s" + ',' + '\mu s'
        infile.write(writeStr + "\n")
        infile.write(str(time.time()) + "\n")
        print('Cam Process ID: %d' % os.getpid())
    except IOError:
        print("Cannot open infile!")
        sys.exit(1)
    t0 = time.time()
    while (not ev.is_set()) or (not q.empty()):

        T0 = time.time()
        cnt_cam = 0

        collect_all = []
        while not q.empty():
            collect_all.append(q.get())
            cnt_cam += 1

        for i in range(len(collect_all)):
            collect = collect_all[i]
            writeStr = str(collect[0]) + ',' + str(collect[1])+"\n"
            infile.write(writeStr)

        tmp = time.time() - T0
        if tmp > 0.01:
            print('{} :: save_cam_info_th :: Saved cam times took: {}, to save {} items.'.format(str(datetime.datetime.now())[11:], tmp, cnt_cam))

        time.sleep(0.3)


def save_IMU_info_th(qA, qG, ev):


    global date_now
    print('Save IMU PID: %d' % os.getpid())
    try:
        # infilename = "./" + self._name + str(time.time()) + ".csv"
        infilename_Acc = "./" + 'Acc_' + date_now + '.csv'
        infilename_Gyro= "./" + 'Gyro_' + date_now + ".csv"
        infile_Acc = open(infilename_Acc, 'w')
        infile_Gyro = open(infilename_Gyro, 'w')
        writeStr = "timestamp" + "," + "X" + "," + "Y" + "," + "Z" + "," + "Packet ID"  + "\n"
        infile_Acc.write(writeStr)
        infile_Gyro.write(writeStr)
        writeStr = "ms" + "," + "m/(s^2)" + "," + "m/(s^2)" + "," + "m/(s^2)" + "," + "\n"
        infile_Acc.write(writeStr)
        infile_Gyro.write(writeStr)
    except IOError:
        print("Cannot open infile!")
        sys.exit(1)

    t0 = time.time()
    while (not ev.is_set()) or (not qA.empty()) or (not qG.empty()):

        t1 = time.time()
        cnt_save_imu = 0

        collect_all = []
        while not qA.empty():
            collect_all.append(qA.get())
            cnt_save_imu += 1

        tmp = time.time() - t1
        if tmp > 0.01:
            print('{} :: save_IMU_info_th :: Emptying the Acc queue took: {}, to save {} items.'.format(
                str(datetime.datetime.now())[11:], tmp, cnt_save_imu))

        t1 = time.time()

        for i in range(len(collect_all)):
            collect = collect_all[i]
            writeStr = str(collect[0]) + "," + str(collect[1][0]) + "," + str(collect[1][1]) + "," + str(
                collect[1][2]) + "," + str(collect[2]) + "\n"
            infile_Acc.write(writeStr)

        tmp = time.time() - t1
        if tmp > 0.01:
            print('{} :: save_IMU_info_th :: Saving Acc to a file took: {}, to save {} items.'.format(
                str(datetime.datetime.now())[11:], tmp, cnt_save_imu))

        t1 = time.time()
        cnt_save_imu = 0

        collect_all = []
        while not qG.empty():
            collect_all.append(qG.get())
            cnt_save_imu += 1

        tmp = time.time() - t1
        if tmp > 0.01:
            print('{} :: save_IMU_info_th :: Emptying the Gyro queue took: {}, to save {} items.'.format(
                str(datetime.datetime.now())[11:], tmp, cnt_save_imu))

        t1 = time.time()

        for i in range(len(collect_all)):
            collect = collect_all[i]
            writeStr = str(collect[0]) + "," + str(collect[1][0]) + "," + str(collect[1][1]) + "," + str(
                collect[1][2]) + "," + str(collect[2]) + "\n"
            infile_Gyro.write(writeStr)

        tmp = time.time() - t1
        if tmp > 0.01:
            print('{} :: save_IMU_info_th :: Saving Gyro to a file took: {}, to save {} items.'.format(
                str(datetime.datetime.now())[11:], tmp, cnt_save_imu))

        tmp = time.time() - t1
        if tmp > 0.01:
            print('{} :: save_IMU_info_th :: Whole loop of saving took: {}s'.format(
                str(datetime.datetime.now())[11:], tmp))

        time.sleep(0.03)


def cam_thread(ev, q):

    global date_now
    global recording_start

    # initialize camera
    sys.stdout.flush()
    print('Cam: Camera read to start recording')

    with picamera.PiCamera() as camera:
        timestamp = 0
        camera.resolution = (1920, 1080)
        camera.framerate = 20
        camera.annotate_background = picamera.Color('black')
        camera.start_recording('cam_stream_' + date_now + '.h264')
        while not ev.is_set():

            if timestamp != camera.frame.timestamp:
                tmp = time.time()
                camera.annotate_text = str(tmp - recording_start)
                timestamp = camera.frame.timestamp
                q.put((tmp, timestamp))
        q.put((time.time(), camera.frame.timestamp))
        print('Cam: finished reading')
        camera.close()


def accel_thread(Acc, q):
    global recording_start
    print('Acc Process ID: %d' % os.getpid())
    while not event.is_set():
        thlock.acquire()
        t0 = time.time()
        Acc.get_acc(q)
        temp = Acc.get_time_samp() - (time.time() - t0)

        thlock.release()

        if Acc.get_counter == 1:
            recording_start = time.time()
        if temp > 0:
            time.sleep(temp)
        else:
            pass


def gyros_thread(Gyro, q):
    print('Gyro ID: %d' % os.getpid())
    while not event.is_set():
        thlock.acquire()
        t0 = time.time()
        Gyro.get_gyro(q)
        temp = Gyro.get_time_samp() - (time.time() - t0)

        thlock.release()
        if temp > 0:
            time.sleep(temp)
        else:
            pass


def monitor(main_p, cam_thd, save_imu, save_cam):
    general_cpu = []
    cpu_ctlist = []
    mem_ctlist = []
    cpu_cplist = []
    mem_cplist = []
    save_imulist = []
    save_camlist = []
    mem_imulist = []
    mem_camlist = []
    while not event.is_set():
        general_cpu.append(psutil.cpu_percent(interval=None, percpu=True))
        cpu_cplist.append(main_p.cpu_percent())
        cpu_ctlist.append(cam_thd.cpu_percent())
        save_imulist.append(save_imu.cpu_percent())
        save_camlist.append(save_cam.cpu_percent())
        mem_ctlist.append(cam_thd.memory_percent())
        mem_cplist.append(main_p.memory_percent())
        mem_imulist.append(save_imu.memory_percent())
        mem_camlist.append(save_cam.memory_percent())
        time.sleep(0.11)
    print('--------------')
    print('Average CPU use per core is: {}'.format([x / len(general_cpu) for x in [sum(i) for i in zip(*general_cpu)]]))
    print('--------------')
    print('Camera task: Average CPU usage is: {}'.format(sum(cpu_ctlist) / len(cpu_ctlist)))
    print('--------------')
    print('Main process: Average CPU usage is: {}'.format(sum(cpu_cplist) / len(cpu_cplist)))
    print('--------------')
    print('Save IMU data: Average CPU usage is: {}'.format(sum(save_imulist) / len(save_imulist)))
    print('--------------')
    print('Save Cam Times: Average CPU usage is: {}'.format(sum(save_camlist) / len(save_camlist)))
    print('--------------')
    print('Camera task: Average Memory percentage use: {}'.format(str(sum(mem_ctlist) / len(mem_ctlist))))
    print('--------------')
    print('Main process: Average Memory percentage use: {}'.format(str(sum(mem_cplist) / len(mem_cplist))))
    print('--------------')
    print('Save IMU data: Average Memory percentage use: {}'.format(str(sum(mem_imulist) / len(mem_imulist))))
    print('--------------')
    print('Save Cam Times: Average Memory percentage use: {}'.format(str(sum(mem_camlist) / len(mem_camlist))))


def key_monitor():
    global date_now
    # Button counter for debouncing purposes
    stop_counter = 0

    while not event.is_set() and camera_thread.is_alive():
        button_state_is_on = input()#not GPIO.input(23)

        if button_state_is_on == ' ':
            print('{} :: key_monitor :: Button Pressed !!'.format(str(datetime.datetime.now())[11:]))
            if stop_counter == 0:
                stop_counter +=1
                print('{} :: key_monitor :: button_counter:{}'.format(str(datetime.datetime.now())[11:], stop_counter))
                t0 = time.time()
            # Button debouncing
            elif (time.time()-t0 > 0.5) and (time.time()-t0 < 4) and stop_counter >= 1:
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
            elif (time.time()-t0 > 4) or (time.time()-t0 < 1):
                stop_counter = 0
                print('{} :: key_monitor :: button_counter:{}'.format(str(datetime.datetime.now())[11:], stop_counter))

        if not camera_thread.is_alive():
            camera_thread.terminate()

        time.sleep(0.1)

def led_status():

    GPIO.output(24, True)
    while camera_thread.is_alive() or save_imu_thread.is_alive() or save_cam_thread.is_alive() or acc_thread.is_alive() \
            or gyro_thread.is_alive() or key.is_alive() or vigilant.is_alive():

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
    bno = BNO055.BNO055(serial_port='/dev/serial0')
    # Initialize the BNO055 and stop if something went wrong.
    while True:

        try:
            # Initialize the BNO055 and stop if something went wrong.
            if not bno.begin():
                raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
            # Print system status and self test result.
            status, self_test, error = bno.get_system_status()
            break
        except Exception as e:
            print("{} :: main :: Got error: {}".format(str(datetime.datetime.now())[11:], e))
            print("{} :: main :: Sleeping 1s before retrying".format(str(datetime.datetime.now())[11:]))
            time.sleep(1)

    # Print system status and self test result.
    status, self_test, error = bno.get_system_status()
    print(str(datetime.datetime.now())[11:] + ' :: main :: System status: {0}'.format(status))
    print(str(datetime.datetime.now())[11:] + ' :: main :: Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
    # Print out an error if system status is in error mode.
    if status == 0x01:
        print(str(datetime.datetime.now())[11:] + ' :: main :: System error: {0}'.format(error))
        print('{} :: main :: See datasheet section 4.3.59 for the meaning.')
    # Print BNO055 software revision and other diagnostic data.
    sw, bl, accel, mag, gyro = bno.get_revision()
    print('{} :: main :: Software version:   {}'.format(str(datetime.datetime.now())[11:], sw))
    print('{} :: main :: Bootloader version: {}'.format(str(datetime.datetime.now())[11:], bl))
    print(str(datetime.datetime.now())[11:] + ' :: main :: Accelerometer ID:   0x{0:02X}'.format(accel))
    print(str(datetime.datetime.now())[11:] + ' :: main :: Magnetometer ID:    0x{0:02X}'.format(mag))
    print(str(datetime.datetime.now())[11:] + ' :: main :: Gyroscope ID:       0x{0:02X}\n'.format(gyro))
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('{} :: main :: Starting IMU test..'.format(str(datetime.datetime.now())[11:]))
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    sys.stdout.flush()

    thlock = threading.Lock()
    accel = Acc(125)
    gyros = Gyro(116)

    # create queues to share data between threads/processes
    ImageQ = mp.Queue(0)
    AccQ = mp.Queue(0)
    GyroQ = mp.Queue(0)
    CamQ = mp.Queue(0)
    event = mp.Event()
    led_event = mp.Event()

    # initialize processes
    camera_thread = mp.Process(target=cam_thread, args=(event, CamQ))
    acc_thread = threading.Thread(target=accel_thread, args=(accel, AccQ))
    gyro_thread = threading.Thread(target=gyros_thread, args=(gyros, GyroQ))
    save_imu_thread = mp.Process(target=save_IMU_info_th, args=(AccQ, GyroQ, event))
    save_cam_thread = mp.Process(target=save_cam_info_th, args=(CamQ, event))
    key = threading.Thread(target=key_monitor, args=())
    led = threading.Thread(target=led_status, args=())

    # setup monitoring
    main_pid = os.getpid()
    main_p = psutil.Process(main_pid)

    camera_thread_pid = camera_thread.pid
    camera_th_p = psutil.Process(camera_thread_pid)

    save_imu_thread_pid = save_imu_thread.pid
    save_imu_p = psutil.Process(save_imu_thread_pid)

    save_cam_thread_pid = save_cam_thread.pid
    save_cam_p = psutil.Process(save_cam_thread_pid)

    vigilant = threading.Thread(target=monitor, args=(main_p, camera_th_p, save_imu_p, save_cam_p))
    print(psutil.cpu_percent(interval=0.1, percpu=1))
    print('{} :: main :: Program started on {}'.format(str(datetime.datetime.now())[11:], date_now))

    # launch processes/threads

    camera_thread.start()
    save_imu_thread.start()
    save_cam_thread.start()
    acc_thread.start()
    gyro_thread.start()
    key.start()
    vigilant.start()
    led.start()

    print(str(datetime.datetime.now())[11:] + ' :: main :: Main process PID: %d' % main_pid)

    camera_thread.join()
    acc_thread.join()
    gyro_thread.join()
    save_imu_thread.join()
    save_cam_thread.join()
    vigilant.join()
    key.join()
    led.join()
