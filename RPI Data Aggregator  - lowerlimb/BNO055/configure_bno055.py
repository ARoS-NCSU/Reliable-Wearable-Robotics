import logging
import sys
import datetime
import time
import psutil
from Adafruit_BNO055 import BNO055

print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
print("{} :: main :: Starting IMU configuration".format(str(datetime.datetime.now())[11:]))
print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
# initialize the connections
bno = BNO055.BNO055(serial_port='/dev/serial0')


# Enable verbose debug logging if -v is passed as a parameter.
if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
    logging.basicConfig(level=logging.DEBUG)

attempt = 0
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
        attempt += 1
        time.sleep(1)
    if attempt >= 10:
        print("{} :: main :: Configuration was not done!".format(
            str(datetime.datetime.now())[11:]))
        print("{} :: main :: I have tried enough... This thing won't work... Good luck debugging!".format(
            str(datetime.datetime.now())[11:]))
        sys.exit()

print(str(datetime.datetime.now())[11:] + ' :: main :: System status: {0}'.format(status))
print(str(datetime.datetime.now())[11:] + ' :: main :: Self test result (0x0F is normal): 0x{0:02X}'.format(
    self_test))
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

print('Reading BNO055 data, press Ctrl-C to quit...')

'''
 Configure Acc sampling rate to 125Hz and Gyro to 116Hz
'''
print('Setting operational mode to Config mode')
try:
    bno.set_mode(0x00)
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting operational mode to Config mode')


print('Setting Page ID to 1, where bandwidth registers are')
try:
    bno._write_byte(0x07, 0x01)
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting Page ID to 1, where bandwidth registers are')

print('Setting Acc bandwidth to 125Hz, range 16G')
try:
    bno._write_bytes(0x08, [0x13])
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting Acc bandwidth to 125Hz, range 16G')


print('Setting Gyro bandwidth to 116Hz, range 2000 dps')
try:
    bno._write_bytes(0x0A, [0x10])
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting Gyro bandwidth to 116Hz, range 2000 dps')


print('Setting back to Page ID 0')
try:
    bno._write_byte(0x07, 0x00)
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting back to Page ID 0')


print('Setting operational mode to ACC and Gyro mode (NON Fusion)')
try:
    bno.set_mode(0x05)
except:
    print('x x')
    print(' ^ ')
    print('vvv')
    print('Failed : Setting operational mode to ACC and Gyro mode (NON Fusion)')


print(' Reading...')

for k in range(0, 5):
    try:
        read = bno._read_byte(0x3D)
        print('{} :: main :: Service 0x3D ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)


print('Check operational mode: {}'.format(read)) # 5
print(' Reading...')
for k in range(0, 5):
    try:
        read = bno._write_byte(0x07, 0x01)
        print('{} :: main :: Service page 0x01, service 0x07 ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)
print('Setting Page ID to 1, where bandwidth registers are: {}'.format(read))


print(' Reading...')
for k in range(0, 5):
    try:
        read = bno._read_byte(0x08)
        print('{} :: main :: Service 0x08 ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)
print('Check Acc configuration: {}'.format(read)) # 19


print(' Reading...')
for k in range(0, 5):
    try:
        read = bno._read_byte(0x0A)
        print('{} :: main :: Service 0x0A ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)
print('Check Gyro configuration: {}'.format(read)) # 16


print(' Reading...')
for k in range(0, 5):
    try:
        read = bno._write_byte(0x07, 0x00)
        print('{} :: main :: Service page 0x00, service 0x07 ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)
print('Setting back to Page ID 0, allowing data reading: {}'.format(read))


print(' Reading...')
for k in range(0, 5):
    try:
        read = bno._read_byte(0x07)
        print('{} :: main :: Service 0x07 ok!:   {}'.format(str(datetime.datetime.now())[11:], sw))
        break
    except:
        print('Error... Trying again')
    time.sleep(0.5)
print('Check page ID: {}'.format(read)) # 0
print("{} :: config BNO055 :: Finished.".format(str(datetime.datetime.now())[11:]))