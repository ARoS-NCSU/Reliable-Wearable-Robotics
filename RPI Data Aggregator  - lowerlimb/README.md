# <a name="required"></a>Required packages
 * Python 3.7
 * Python Multiprocessing
 * Python Multithreading
 * [Python psutil](https://pypi.org/project/psutil/) (use pip3 here!)
 * [Python OpenCV](https://www.learnopencv.com/install-opencv-4-on-raspberry-pi/)
  * [Python Adafruit BNO055](https://learn.adafruit.com/bno055-absolute-orientation-sensor-with-raspberry-pi-and-beaglebone-black/hardware)<a name="bno055"></a> (go until the test using simpletest.py)
 * [Python PiCamera](https://picamera.readthedocs.io/en/release-1.12/install.html)

If this repo is useful for your project, please consider citing our work:

*B. Zhong, R. Luiz da Silva, M. Li, H. Huang and E. Lobaton, "Environmental Context Prediction for Lower Limb Prostheses With Uncertainty Quantification," in IEEE Transactions on Automation Science and Engineering, doi: 10.1109/TASE.2020.2993399.*

```
@ARTICLE{Zhong2020,
  author={B. {Zhong} and R. {Luiz da Silva} and M. {Li} and H. {Huang} and E. {Lobaton}},
  journal={IEEE Transactions on Automation Science and Engineering}, 
  title={Environmental Context Prediction for Lower Limb Prostheses With Uncertainty Quantification}, 
  year={2020},
  volume={},
  number={},
  pages={1-13},}
```

# Motivation for current design
**Summer 2018**

  * This repo is for a prototype for data collection. The data is required to have video synchronized with IMU values. The project demanding such data collection is the [prosthetic leg project](https://ieeexplore.ieee.org/abstract/document/8512614).
  * Use of Adafruit BNO055 board, due to it widespread use with hobbysts and scientific community there are plenty of forums and documentation exploring possible applications and issues found when using it. However, it is important to use the link [above](#bno055) which refers to an old tutorial of adafruit that uses the IMU with serial port instead of I2C. The latter one has problems of compatibility and clock speed on the raspberry Pi.
  * Use of raspberry Pi 3 Model B, same as above and also enables portability for data collection with reasonable computational power.
  * Use of USB camera, enables applications with SLAM (attempted code can be found [here](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/tree/master/USBCamera) and analysis [here](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/previous_versions.md))
  * PiCamera, better handled by raspberry Pi for CPU intense tasks (initially not applicable for SLAM since it's a rolling shutter camera, so its frames have drift for moving scenes)
  * Current software design
    * Python, expandable, easy to get started with, natural extension to machine learning applications
    * CPU and memory usage analysis confirmed that there is room for parallelization as well as increasing the time efficiency when saving the files
    * (**Summer 2019 update**) Using Linux to manage independent data collection from IMU and picamera turned out to be the best solution which is the one that has full control over the frames timestamps and hence allows synchronization with IMU readings.
    
# System notes:
  * BNO055 has to be used in non fusion mode in order to provide the readings of raw data from accelerometer and gyroscope. Therefore, the chip was configured to work in this mode and it was tested with sampling frequencies of Acc: 125Hz, Gyro: 116Hz. This board offers sampling rates up to 1000Hz but BNO055 does not offer a way to indicate that new data has arrived. Thus one has to manually check if the read values have changed to then save the reading.
  * Configurations of BNO055 have to be done separately from the actual reading script for reasons not discovered. Having the configurations and readings in the same file makes BNO055 return errors consistently. Configuration file can be found [here](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/configure_bno055.py).
  * According to the data sheet of BNO055, at power on, the dafault values are restored. Thus, every time the raspberry Pi is powered on and so BNO055, it is needed to configure the IMU.
  * Current system obtains IMU data at about 98Hz. 
  * The system was tested on frame rates from 15 to 30 fps and different image resolutions. The choice of frame rate is contingent of allowed dropped frames percentage. Please see [Performance Notes](#performance) for further details.
  * The recording is made with a [python script](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/IMU_reader.py) that collects data from the IMU and a customized version of raspivid which saves the epoch timestamp of the video frames to a file, further details [below](#setup). Both scripts are executed from [this](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/aggregator.sh) bash file.
  * A switch is required at GPIO 23 to stop the system after 2 consecutive pushes apart for at least for 0.5s. [Connections](https://www.hackster.io/hardikrathod/push-button-with-raspberry-pi-6b6928).
  * An LED may be installed for feedback purposes at GPIO 24. [Connections](https://www.hackster.io/hardikrathod/push-button-with-raspberry-pi-6b6928).   
  * The system uses a VeryGood battery (this is the brand name) that has a USB power cord with a push button on it.
  * For mechanical case design project please check [here](https://github.ncsu.edu/rdasilv2/RaspiCaseFiles/tree/master/Proj-ProstheticLeg).
  * Version 1:

<img src="https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMG_20190614_074938058.jpg width="250"  height="250">| <img src="https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMG_20190614_074941604.jpg" width="250"  height="250">| <img src="https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMG_20190614_074949320.jpg" width="250"  height="250">

# Prototype parts
 * One [Raspberry](https://www.canakit.com/raspberry-pi-3-model-b-plus-basic-kit.html) Pi Model 3.
 * Power cord for Raspberry Pi with a power button
 * One Adafruit [BNO055](https://www.adafruit.com/product/2472)
 * One [schin](https://www.amazon.com/LOPET-Lightweight-Breathable-Protective-Teenagers/dp/B07LFK5JSX/ref=pd_sbs_200_20?_encoding=UTF8&pd_rd_i=B07LFK5JSX&pd_rd_r=3fdaa09a-aaa5-4cb6-acc0-cfb46b89c2ab&pd_rd_w=90OTi&pd_rd_wg=wMomT&pf_rd_p=1c11b7ff-9ffb-4ba6-8036-be1b0afa79bb&pf_rd_r=HRSBJ836S7PAJXX4X475&psc=1&refRID=HRSBJ836S7PAJXX4X475) guard.
 * Four screws about 65mm lenght and about 3.5mm width
 * One LIPO battery
 * One [Picamera](https://www.canakit.com/raspberry-pi-camera.html) V2
 * One LED (optional)
 * One 100 ohm Resistor
 * One push button or toggle 2 stage switch (better)
 
# <a name="setup"></a>Installation/Setup notes

 * **Hardware**
	
   * Communication with IMU
   
   |**BNO055** | **RPI 3 B+** |
   |---|---|
   |PS1 | 1(3V3)|
   |SCL | 8(TXD)|
   |SDA | 10(RXD)|
   |GND | 14(GND)|
   |Vin | 17(3V3)|
   
   * **[HMI](https://www.hackster.io/hardikrathod/push-button-with-raspberry-pi-6b6928)**
   
   |**BNO055** | **RPI 3 B+**|
   |---|---|
   |LED(anode) | 18|
   |switch | 16|
   |GND | 6|
   
 * Install the required packages [above](#required). For adafruit tutorial, make sure that at simpletest.py script you use serial0 instead of ttyAMA0 (as they incorrectly show in the tutorial).
 * Make sure that the [aggregator file](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/aggregator.sh) points to the correct directory where the [IMUreader](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/IMU_reader.py) file is.
 * Make sure you configured in the [aggregator file](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/aggregator.sh) your desired video resolution and frame rate by changing the following three lines:
 ```bash
wid="1280" #video width
hei="720" #video height
fps_v="30" # frame rate
```
 * Make the [aggregator.sh](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/aggregator.sh) start from boot by editing the rc.local file as the following:
 ```bash
 sudo nano /etc/rc.local
 ```
   Then add the following command right above the line written "exit 0" as the example below (make sure it points to the directory where aggregator.sh is located):
```bash
bash /home/pi/aggregator.sh >> log.txt
exit 0
```
 * Change raspivid source code
   * checkout your own copy of the userland tree (git clone https://github.com/raspberrypi/userland.git)
   * cd userland
   * edit raspivid.c (nano host_applications/linux/apps/raspicam/RaspiVid.c) and add code in encoder_buffer_callback as detailed below:
```C
static void encoder_buffer_callback(MMAL_PORT_T *port, MMAL_BUFFER_HEADER_T *buffer)
{
   MMAL_BUFFER_HEADER_T *new_buffer;
   static int64_t base_time =  -1;
   static int64_t last_second = -1;
   // Added by Rafael
   struct timespec spec;
   // until here
```
```C
               if (pData->pstate->save_pts &&
                  !(buffer->flags & MMAL_BUFFER_HEADER_FLAG_CONFIG) &&
                  buffer->pts != MMAL_TIME_UNKNOWN &&
                  buffer->pts != pData->pstate->lasttime)
               {
                  int64_t pts;
                  if (pData->pstate->frame == 0)
                     pData->pstate->starttime = buffer->pts;
                  pData->pstate->lasttime = buffer->pts;
                  pts = buffer->pts - pData->pstate->starttime;
				  //Added by Rafael
				  clock_gettime(CLOCK_REALTIME, &spec);
				  
				  fprintf(pData->pts_file_handle, "%lld.%03lld,%ld.%09ld\n", pts / 1000, pts % 1000, (long)spec.tv_sec, spec.tv_nsec);
                  pData->pstate->frame++;
				  // until here		
               }
            }

            mmal_buffer_header_mem_unlock(buffer);
```
   * compile it (./buildme)
   * Download the [continue_button.py](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/BNO055/continue_button.py) script, in order to allow a clean shutdown of the system

# <a name="modes"></a>Feedback modes:
    
|**Mode** | **Blinking rate** |
|---|---|
|Recording | 1Hz |
|Wrapping up (may or may not happen depending on system load)| 10Hz |
|Off | 0Hz |
|Request period* | 2s off, 10s on|
* *Request period is the time after data collection has been finished(see info also [below](#protocol)). While LED is on, if the switch is hit, then the rpi will continue on. After the 10s on and no switch pressing, the RPI is shutdown.

# <a name="protocol"></a>Recording protocol

 * With the system turned off, push the button in the power cord. The system may take about 40s to be fully up.
 * After system is up, the LED shall blink in Recording mode.
 * To finish recording, press the switch twice with at least 0.5s wait in between presses.
 * After [wrapping up](#modes), the rpi will wait 2s with the LED off and then enter in request period
 * Once in request period, hit the switch if you want the rpi to continue on, wait more 10s to have it automatically shuting down otherwise. [Further info](#modes).
 * It is recommended recording sessions of about 20 minutes since the script does not check memory availability before starting. If you run out of memory the rpi will not power up again and your data will be stuck there. You may open its SD card in a Linux machine to retrieve the data or just sit and cry while formatting the SD card in case that does not work.
 * To record a new session, make sure the LED is in Off mode, then turn the rpi off and then back on using the push button on the power cord.
 * The data has to be manually taken from rpi.
 
# <a name="performance"></a> Performance Notes 

Please find the performance analysis for previous versions [here](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/previous_versions.md)

The current system has been tested in the following 4 different configurations:

 * 1 - Integrated python script
		Acquiring IMU data and launching raspivid utilizing python multiprocessing for each process (process 1: IMU reading, process 2: Save IMU data to csv, process 3: launch raspivid)
  	* Acquiring IMU data and launching raspivid utilizing python multithreading for each task (task 1: IMU reading, task 2: Save IMU data to csv, task 3: launch raspivid)
 * 2 - Bash file to launch raspivid and a python script to read IMU
  	* One python script has been written for multiprocessing and multithreading approach

All configurations were close to each other in terms of CPU load and memory usage, however, configuration 2 with multiprocessing had a slightly advantage of IMU sampling rate. Thus, this is the configuration used as indicated in the setup [above](#setup).

The system has been tested in the following frame rates: 15, 20, 25, 30.

The system has been tested in the following resolutions: 1920x1080, 1644x722, 1280x720.

For each combination above, it was done 3 recordings of 20 minutes each. The following table displays the average values collected during testing (best results in **bold** values):

|**Resolution**|**FPS**|**Acc Fs**|**Gyro Fs**|**Duration Acc**|**Duration Gyro**|**Dropped frames [%]**|**Main process**|**Save data  process**|**Mem Usage Main process**|**Mem Usage Save Imu**|
|----------|---|------|-------|-------------|--------------|------------------|-------------|------------------|----------------------|------------------|
|1920x1080 |30 |97.92 |97.68  |1720.54      |1720.54       |3.45              |41.46        |8.80              |1.49                  |1.05              |
|1920x1080 |25 |**98.56** |**98.12**  |1218.10      |1218.09       |4.43              |42.54        |8.88              |**1.42**                  |**1.02**              |
|1920x1080 |20 |98.34 |98.00  |1745.12      |1745.12       |4.06              |41.45        |8.81              |1.52                  |1.04              |
|1920x1080 |15 |98.34 |97.82  |1419.44      |1419.44       |**3.34**              |**40.82**        |**8.74**              |1.49                  |1.04              |
|1640x922  |30 |98.28 |97.90  |1918.23      |1918.22       |2.54              |**40.84**        |**8.86**              |1.51                  |1.05              |
|1640x922  |25 |98.22 |97.85  |1889.39      |1889.39       |0.48              |41.33        |8.90              |1.54                  |1.05              |
|1640x922  |20 |**98.65** |**98.20**  |1416.63      |1416.62       |**0.00**              |41.06        |8.98              |1.50                  |1.05              |
|1640x922  |15 |98.61 |98.06  |1322.57      |1322.57       |**0.00**              |41.18        |9.09              |1.49                  |1.05              |
|1280x720  |30 |**98.46** |98.00  |1467.47      |1467.46       |0.00              |41.17        |9.06              |1.50                  |1.05              |
|1280x720  |25 |98.10 |**98.07**  |1311.31      |1311.30       |0.00              |41.51        |9.11              |**1.48**                  |1.05              |
|1280x720  |20 |97.66 |98.02  |1292.45      |1292.44       |0.00              |41.19        |9.03              |**1.48**                  |**1.04**              |
|1280x720  |15 |97.73 |98.05  |1384.34      |1384.33       |0.00              |**41.14**        |**8.98**              |1.50                  |1.05              |

Choose the configuration as you wish, mind your data collection cost-benefit.

# Data Visualization

 * A matlab [file](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/Data_Visualization_Tool/visualize_data_lower_limb.m) is available for data visualization. Please refer to its [directory](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/tree/master/Data_Visualization_Tool). Change the paths in the [run_SetupDirectories](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/blob/master/Data_Visualization_Tool/visualize_data_lower_limb.m) file accordingly.
 * Convert the file from .h264 to .avi (or .mp4) using MP4Box for raspberry pi:
 	* Install gpac (to have MP4Box):
	```bash
	sudo apt-get update
	sudo apt-get install gpac
	```
	* Usage
	```bash
	MP4Box -add filename.h264 filename.avi
	```
  * It may work on Linux, but only if you use Matlab GUI (no command line).
  * For MAC users:
  	* Open .avi file with QuickTime Player, then save the converted .mov file
	```matlab
	ls([inputDir ‘’])
	```
	change to
	```matlab
	strtrim(ls([inputDir ‘’]))
	```
	Also
	```matlab
	VideoReader([inputDir videoFile])
	```
	change to
	```matlab
	VideoReader(videoFile)
	```
	Also
	```matlab
	csvread([inputDir filecamtime],1,0)
	```
	change to
	```matlab
	csvread(filecamtime,1,0)
	```
 * Visualization sample
 
 ![](https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/ezgif.com-optimize.gif)
 
