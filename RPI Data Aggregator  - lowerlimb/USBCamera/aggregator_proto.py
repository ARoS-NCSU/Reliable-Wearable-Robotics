'''
Golden version with the following architecture:
*Process 1(P1): Thread 1, 2: Runs IMU reading,
*Process 2(P2): Saves Acc
*Process 3(P3): Saves Gyro
*Process 4(P4): Runs camera reading
*Process 5(P5): Saves data from camera
Interrupted by Enter press
Halted execution after finishing is fixed
'''
import sys
import threading
import time
import psutil
from Queue import Queue
import operator
import multiprocessing as mp
import operator
from Adafruit_BNO055 import BNO055
import cv2
import os

class AdaFruitBNO055:


    def __init__(self, freq_samp, label):
        self._name = label
        self._time_samp = 1.0 / freq_samp
        self._th_stop_event = threading.Event()
        self._counter = 0

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
        t = time.time()
        #thlock.release()
        q.put((t, (x, y, z), self.get_counter()))


class Gyro(AdaFruitBNO055):
    def __init__(self, freq_samp):
        self._label = 'Gyro'
        AdaFruitBNO055.__init__(self, freq_samp, self._label)
    def get_gyro(self, q):
        #thlock.acquire()
        x, y, z = bno.read_gyroscope()
        tg = time.time()
        #thlock.release()
        q.put((tg, (x, y, z), self.get_counter()))


class Camera:


    def __init__(self, freq_samp):
        self._time_samp = 1.0 / freq_samp
        self._mp_stop_event = mp.Event()
        self._th_stop_event = threading.Event()
        self._mplock = mp.Lock()
        self._counter = 0

    def get_camera(self, cam, q):
        #print('Cam: Reading camera')
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

'''
def setup_camera(name, freq_samp, vert_pxl, hor_pxl):
    #infilename = "./" + name + str(time.time())
    infilename = "./" + name
    fourcc = cv2.cv.CV_FOURCC(*'XVID')
    out = cv2.VideoWriter(name + '.avi', fourcc, freq_samp, (vert_pxl, hor_pxl))
    try:
        infiletouse = open(infilename + ".csv", "a+")
        write_str = "timestamp"
        infiletouse.write(write_str + "\n")
        write_str = "ms"
        infiletouse.write(write_str + "\n")
    except IOError:
        print("Cannot open infile!")
        sys.exit(1)
    return out, infiletouse
'''

def save_Cam_info_th(q, ev):
    print('Save Cam ID: %d' % os.getpid())
    counter = 0
    name = 'Camera'
    freq_samp = 30
    vert_pxl = 640
    hor_pxl = 480
    infilename = "./" + name
    fourcc = cv2.cv.CV_FOURCC(*'XVID')
    out = cv2.VideoWriter(name + '.avi', fourcc, freq_samp, (vert_pxl, hor_pxl))
    try:
        infile2use = open(infilename + ".csv", 'w')
        write_str = "timestamp"
        infile2use.write(write_str + "\n")
        write_str = "ms"
        infile2use.write(write_str + "\n")
    except IOError:
        print("Saving: Cannot open infile!")
        sys.exit(1)

    sys.stdout.flush()
    while (not ev.is_set()) or (not q.empty()):
        #t0 = time.time()
        #print('Saving: Q state {}'.format(q.empty()))
        i = 0
        while not q.empty():
            #print('Saving: Reading queue, frame{}'.format(i))
            collect = q.get()
            data = str(collect[0])
            cnt = collect[2]
            #print('Saving: This is the saved time {}'.format(data))
            infile2use.write(data + str(cnt) + "\n")
            out.write(collect[1])
            i += 1
        a = 0.3#(1.0 / 30) - (time.time() - t0)
        if a > 0:
            time.sleep(a)
        else:
            pass
    print('Saving: finished loop')
    out.release()
    cv2.waitKey(0)

def save_Acc_info_th(q, ev):
    print('Save ACC ID: %d' % os.getpid())
    try:
        # infilename = "./" + self._name + str(time.time()) + ".csv"
        infilename = "./" + 'Acc' + '.csv'
        infile = open(infilename, 'w')
        writeStr = "timestamp" + "," + "X" + "," + "Y" + "," + "Z" + "," + "Package ID"
        infile.write(writeStr + "\n")
        writeStr = "ms" + "," + "m/(s^2)" + "," + "m/(s^2)" + "," + "m/(s^2)" + ","
        infile.write(writeStr + "\n")
    except IOError:
        print("Cannot open infile!")
        sys.exit(1)

    while not ev.is_set() or not q.empty():
        while not q.empty():
            collect = q.get()
            # thlock.acquire()
            writeStr = str(collect[0]) + "," + str(collect[1][0]) + "," + str(collect[1][1]) + "," + str(
                collect[1][2]) + "," + str(collect[2]) + "\n"
            infile.write(writeStr)
            # thlock.release()
        time.sleep(0.03)
        #time.sleep(abs(Acc.get_time_samp() - (time.time() - t0)))

def save_Gyro_info_th(q, ev):
    print('Save Gyro ID: %d' % os.getpid())
    try:
        # infilename = "./" + self._name + str(time.time()) + ".csv"
        infilename = "./" + 'Gyro' + ".csv"
        infile = open(infilename, 'w')
        writeStr = "timestamp" + "," + "X" + "," + "Y" + "," + "Z" + "," + "Package ID"
        infile.write(writeStr + "\n")
        writeStr = "ms" + "," + "m/(s^2)" + "," + "m/(s^2)" + "," + "m/(s^2)" + ","
        infile.write(writeStr + "\n")
    except IOError:
        print("Cannot open infile!")
        sys.exit(1)

        # t0 = time.time()
    while not ev.is_set() or not q.empty():
        while not q.empty():
            collect = q.get()
            # thlock.acquire()
            writeStr = str(collect[0]) + "," + str(collect[1][0]) + "," + str(collect[1][1]) + "," + str(
                collect[1][2]) + "," + str(collect[2]) + "\n"
            infile.write(writeStr)
            # thlock.release()
        time.sleep(0.03)
        #time.sleep(abs(Gyro.get_time_samp() - (time.time() - t0)))

def cam_thread(ImageQ, ev):
    # initialize camera
    cap = cv2.VideoCapture(0)
    # initialize sensors
    cam = Camera(30.0)
    sys.stdout.flush()
    print('Cam: Process ID: %d' % os.getpid())
    print('Cam: Camera read to start recording')
    while not ev.is_set():
        t0 = time.time()
        cam.get_camera(cap, ImageQ)
        cam.set_count_up()
        a = cam.get_time_samp()-(time.time()-t0)
        if a > 0:
            time.sleep(a)
        else:
            pass
    print('Cam: finished reading')
    cap.release()

def accel_thread(Acc, q):
    print('Acc Process ID: %d' % os.getpid())
    while not event.is_set():
        thlock.acquire()
        t0 = time.time()
        Acc.get_acc(q)
        a = Acc.get_time_samp()-(time.time()-t0)
        Acc.set_count_up()
        thlock.release()
        if a > 0:
            time.sleep(a)
        else:
            pass


def gyros_thread(Gyro, q):
    print('Gyro ID: %d' % os.getpid())
    while not event.is_set():
        thlock.acquire()
        t0 = time.time()
        Gyro.get_gyro(q)
        a = Gyro.get_time_samp()-(time.time()-t0)
        Gyro.set_count_up()
        thlock.release()
        if a > 0:
            time.sleep(a)
        else:
            pass


def monitor(cpu_sp, cam_thd, current_p, save_acc, save_gyro):
    general_cpu = []
    cpu_splist = []
    mem_splist = []
    cpu_ctlist = []
    mem_ctlist = []
    cpu_cplist = []
    mem_cplist = []
    save_acclist = []
    save_gyrolist = []
    mem_acclist = []
    mem_gyrolist = []
    while not event.is_set():
        general_cpu.append(psutil.cpu_percent(interval=None, percpu=True))
        cpu_splist.append(cpu_sp.cpu_percent())
        cpu_ctlist.append(cam_thd.cpu_percent())
        cpu_cplist.append(current_p.cpu_percent())
        save_acclist.append(save_acc.cpu_percent())
        save_gyrolist.append(save_gyro.cpu_percent())
        mem_splist.append(cpu_sp.memory_percent())
        mem_ctlist.append(cam_thd.memory_percent())
        mem_cplist.append(current_p.memory_percent())
        mem_cplist.append(save_acc.memory_percent())
        mem_acclist.append(save_acc.memory_percent())
        mem_gyrolist.append(save_gyro.memory_percent())
        time.sleep(0.11)
    print('--------------')
    print('Average CPU use per core is: {}'.format([x / len(general_cpu) for x in [sum(i) for i in zip(*general_cpu)]]))
    print('--------------')
    print('Save Image process: Average CPU usage is: {}'.format(sum(cpu_splist) / len(cpu_splist)))
    print('--------------')
    print('Camera task: Average CPU usage is: {}'.format(sum(cpu_ctlist) / len(cpu_ctlist)))
    print('--------------')
    print('Main process: Average CPU usage is: {}'.format(sum(cpu_cplist) / len(cpu_cplist)))
    print('--------------')
    print('Save Acc: Average CPU usage is: {}'.format(sum(save_acclist) / len(save_acclist)))
    print('--------------')
    print('Save Gyro: Average CPU usage is: {}'.format(sum(save_gyrolist) / len(save_gyrolist)))
    print('--------------')
    print('Save Image process: Average Memory percentage use: {}'.format(str(sum(mem_splist) / len(mem_splist))))
    print('--------------')
    print('Camera task: Average Memory percentage use: {}'.format(str(sum(mem_ctlist) / len(mem_ctlist))))
    print('--------------')
    print('Main process: Average Memory percentage use: {}'.format(str(sum(mem_cplist) / len(mem_cplist))))
    print('--------------')
    print('Save Acc: Average Memory percentage use: {}'.format(str(sum(mem_acclist) / len(mem_acclist))))
    print('--------------')
    print('Save Gyro: Average Memory percentage use: {}'.format(str(sum(mem_gyrolist) / len(mem_gyrolist))))

def key_monitor():
    while not event.is_set() and (camera_thread.is_alive() or save_camera_process.is_alive()):
        if raw_input() == '':
            print('Key Monitor: Exit requested!')
            event.set()
            cv2.destroyAllWindows()
        if not camera_thread.is_alive():
            camera_thread.terminate()
            #save_acc_thread.terminate()
            #save_gyro_thread.terminate()
        if not save_camera_process.is_alive():
            save_camera_process.terminate()
        time.sleep(0.1)
    print('Key Monitor: Finished waiting')

if __name__ == '__main__':


    # initialize the connections
    bno = BNO055.BNO055(serial_port='/dev/ttyAMA0')
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
            print("Got error: {}".format(e))
            print("Sleeping 1s before retrying")
            time.sleep(1)

    # Print system status and self test result.
    status, self_test, error = bno.get_system_status()
    print('System status: {0}'.format(status))
    print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
    # Print out an error if system status is in error mode.
    if status == 0x01:
        print('System error: {0}'.format(error))
        print('See datasheet section 4.3.59 for the meaning.')
    # Print BNO055 software revision and other diagnostic data.
    sw, bl, accel, mag, gyro = bno.get_revision()
    print('Software version:   {0}'.format(sw))
    print('Bootloader version: {0}'.format(bl))
    print('Accelerometer ID:   0x{0:02X}'.format(accel))
    print('Magnetometer ID:    0x{0:02X}'.format(mag))
    print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('Starting IMU test..')
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    sys.stdout.flush()

    thlock = threading.Lock()
    accel = Acc(125)
    gyros = Gyro(116)

    # create queues to share data between threads/processes
    ImageQ = mp.Queue(0)
    AccQ = mp.Queue(0)
    GyroQ = mp.Queue(0)
    event = mp.Event()

    # initialize processes
    camera_thread = mp.Process(target=cam_thread, args=(ImageQ, event))
    acc_thread = threading.Thread(target=accel_thread, args=(accel, AccQ))
    gyro_thread = threading.Thread(target=gyros_thread, args=(gyros, GyroQ))
    save_acc_thread = mp.Process(target=save_Acc_info_th, args=(AccQ, event))
    save_gyro_thread = mp.Process(target=save_Gyro_info_th, args=(GyroQ, event))
    save_camera_process = mp.Process(target=save_Cam_info_th, args=(ImageQ, event))
    key = threading.Thread(target=key_monitor, args=())

    # setup monitoring
    main_pid = os.getpid()
    main_p = psutil.Process(main_pid)

    save_camera_process_pid = save_camera_process.pid
    save_camera_p = psutil.Process(save_camera_process_pid)

    camera_thread_pid = camera_thread.pid
    camera_th_p = psutil.Process(camera_thread_pid)

    save_acc_thread_pid = save_acc_thread.pid
    save_acc_p = psutil.Process(save_acc_thread_pid)

    save_gyro_thread_pid = save_gyro_thread.pid
    save_gyro_p = psutil.Process(save_gyro_thread_pid)

    vigilant = threading.Thread(target=monitor, args=(save_camera_p, camera_th_p, main_p, save_acc_p, save_gyro_p))

    print(psutil.cpu_percent(interval=0.1, percpu=1))
    print('Program started')

    # launch processes/threads

    camera_thread.start()
    save_camera_process.start()

    save_acc_thread.start()
    save_gyro_thread.start()
    acc_thread.start()
    gyro_thread.start()
    vigilant.start()
    key.start()
    print('Main process PID: %d' % main_pid)

    camera_thread.join()
    save_camera_process.join()
    '''
    acc_thread.join()
    gyro_thread.join()
    save_acc_thread.join()
    save_gyro_thread.join()
    '''
    vigilant.join()
    key.join()
