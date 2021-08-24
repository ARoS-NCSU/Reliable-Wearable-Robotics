# History notes from previous prototype version.

The notes on performance and issues described here are related to the commit [here](https://github.ncsu.edu/rdasilv2/ARoSDataAggregator/commit/5598b821ff537ce78f771577c214465eac14bd0d#diff-b994b6f73d027855218a03676174ea9c)

CPU and memory usage analysis confirmed that there is room for parallelization as well as increasing the time efficiency when saving the files.

**USB Camera** 

The table below shows the performance for a python script running on a single thread.

Peripherals tested | CPU load [%] | Memory Usage [%] | Reading time [ms] | Save to file [ms] |
|---|---|---|---|---|
BNO055 (acc+gyro) | ~5.7 | ~1 | ~6ms | 0.074 |
USB camera (frames) | ~99.27 | 5.7 | ~14 | ~49 |
USB camera (video) | ~99.65 | ~6.8 | ~13 | ~35 |
BNO055 + USB camera (frames) | ~92 | 5.8 | ~15 | ~55 |
BNO055 + USB camera (video) | ~91 | 6.8 | ~13 | ~34 |

* The following software architecture:
  * Process 1 (P1): Thread 1, 2: Runs IMU reading,  
  * Process 2 (P2): Saves Acc
  * Process 3 (P3): Saves Gyro
  * Process 4 (P2): Runs USB camera reading
  * Process 5 (P3): Saves data from camera

Required the following system usage: 

Peripherals tested | CPU load [%] | Memory Usage [%] |
|---|---|---|
P1 (IMU, main process)| ~32| 4.4 |
P2 (Save Acc)| ~32 | 4.4 |
P3 (Save Gyro)| ~32 | 4.4 |
P4 (Read Camera)| ~32 | 4.4 |
P5 (Save Camera)| ~32 | 4.4 |
System (per core) | ~23, ~42.6, ~71, ~37.7 | - |

  * The concurrency is making some readings of IMU being repeated. Locking and releasing the respective threads diminish signficantly the occurence of this issue but does not eliminate it. Reducing the overhead due to inter process communication is needed. Overhead is denominated here as the effect of causing the intervals of IMU readings be above 10ms. The initial tests show the occurrence of duplicate readings of ~9% of the readings. While overhead (readings above 10ms) is around 1% of the total readings. The first rate is still pretty high.

**Pi Camera**

* The script was able to tested for up to 90 min recording on the desk (longer testing was not attempted due to memory constraints, after that, the system had still 50MB available for recording, 90min generated a 450MB). The command "top" in Linux shows one python process with a CPU load ranging from 102 to 104% and other three processes with CPU usage capped around 40% for one process and less than 15% to the others.
Looking at the profiling output of the following given processes:

  * Process 1 (P1), Thread 1, 2, Runs IMU reading,  
  * Process 2 (P2), Saves Acc
  * Process 3 (P3), Saves Gyro
  * Process 4 (P4), Runs camera reading and saves data from camera

It could be observed the following resources usage: 

Peripherals tested | CPU load [%] | Memory Usage [%] |
|---|---|---|
P1 (IMU, main process)| ~16| ~5 |
P2 (Save Acc)| ~16 | ~5 |
P3 (Save Gyro)| ~16 | ~5 |
P4 (Read and Save Camera)| ~16 | ~5 |
System (per core) | ~18, ~24, ~68, ~9.5 | - |

This makes one conclude that the 102% of CPU usage shown by "top" potentially reflects a process being computed by more than one core. The test was conducted with Wifi On, so we can say that lack of power is not an issue for this system configuration. The video is being recorded in H264 format which does not have timestamp information. Currently, this format is being converted to MP4 after the data collection is finished by using MP4Box application for Linux. This software converts the H264 video to MP4 and estimates the frames timestamp by interpolation based on the given frame rate which is 30 frames per second. Therefore, it looks initially as a good solution to make the system read only the initial and final timestamp and interpolate between them in the same way that MP4box does, given that the 30 fps rate was always obtained as an average.

**Performance comparison of data aggregator using PiCamera for Prosthetic leg project**

|                                  |                              |                             |                             |                              | 
|----------------------------------|------------------------------|-----------------------------|-----------------------------|------------------------------| 
| Resolution [pixels]              | 512x512                      | 640x480                     | 1080x1080                   | 1920x1080                    | 
| CPU usage per core [%]           | [10.18, 10.39, 94.26, 14.27] | [10.75, 12.11, 97.59, 7.38] | [15.69, 12.88, 9.11, 96.93] | [14.65, 94.25, 13.67, 13.53] | 
| CPU usage, camera:               | 24.99                        | 23.77                       | 27.96                       | 28.76                        | 
| CPU usage, main, IMU reading:    | 24.99                        | 23.77                       | 27.96                       | 28.76                        | 
| CPU usage, save Acc              | 24.99                        | 23.77                       | 27.96                       | 28.76                        | 
| CPU usage, save Gyro             | 24.99                        | 23.77                       | 27.96                       | 28.76                        | 
| Memory usage, camera:            | 4.81                         | 4.84                        | 4.78                        | 4.85                         | 
| Memory usage, main, IMU reading: | 4.81                         | 4.84                        | 4.78                        | 4.85                         | 
| Memory usage, save Acc           | 4.81                         | 4.84                        | 4.78                        | 4.85                         | 
| Memory usage, save Gyro          | 4.81                         | 4.84                        | 4.78                        | 4.85                         | 

# Difficulties found during development process

Some issues have been found due to high processing load from camera reading and also IMU data reading. 

**USB camera**

1.  Power supply has to have a stable 5V output for 2.5A. Many power supplies in the lab do not meet this requirement, the voltage drops due to high current request from the raspberry Pi, which generates a warning of undervoltage from OS. Consequently, the OS constraints the access to memory and processing bandwidth, therefore, the processes that handle camera reading and saving video are killed. The warning and killing action can be seen in the kernel log. The power supply from CanaKit can handle the power consuption for data collection.
    
2. The raspberry Pi needs an efficient temperature dissipation mechanism, since once recording for more than approximately 7 minutes (even with Wi-Fi off), the Pi activates an overtemperature warning and due to a similar mechanism described in the previous item, the Pi kills the camera related process at around 12 minutes. For the actual data collection, some cooling mechanism may be needed, but before of attempting that it is worth trying a thermal dissipator.
    
3.  Question: The current software architecture may be offering unnecessary overhead. Two separate scripts have been tested, one with IMU reading only and another one with camera reading only. Each script was saving the data read also in the same format as in the previous item. It was observed that the CPU load was slighly lower in one of the processes with higher memory consumption though. However, the overtemperature warning was created earlier and in 3 attempts the camera process was killed in around 5 minutes. Therefore, the unified script still performs better.
    
4. A thermal dissipator was attempted for the data collection using a USB camera. The overtemperature warning has not being activated but the respective processeses have been killed due to overload in memory according to kernel logs. The odds of this is that the memory usage (returned by the profiling method ran with the related 5 processes) was showing a memory usage of around 5% for each process.

**Pi Camera**

Use openCV with PiCamera to paralleize camera reading and frames storage (more on future work).
 **(Summer 2019 update)** This has been explored and initial setup has shown that 20 FPS could be obtained. This frame rate could be enhanced since this rate was obtained in a single loop that was taking the pictures and also saving them to a file. If the writing to file is moved to a separate thread, there is a potential of increase in the frame rate.


# Testing

**Test LIPO batteries VeryGood autonomy**
 * The battery lasted for approximately 3hrs with wifi on. The size of the mp4 file generated was 563MB.
    
**Compare data collection system IMU to another IMU data for sanity testing**
   * The comparison can be seen in the following pictures. The x,y axis from one IMU was 90^o shifted from the other, due to a misplacement in the position of the sensors.
  * General view Accelerometer:
      ![alt text](https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMUraspi_comparison1.png)
  * Zoom in:
      ![alt text](https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMUraspi_comparison1_zoom.png)
  * General view Gyroscope:
      ![alt text](https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMUraspi_comparison2.png)
  * Zoom in:
      ![alt text](https://github.com/ARoS-NCSU/Reliable-Wearable-Robotics/blob/master/RPI%20Data%20Aggregator%20%20-%20lowerlimb/pics/IMUraspi_comparison2_zoom.png)
      
  * Observations:
    * Some samples are being recorded twice from the ADAfruit. Each read sample could be compared to the previous one to avoid this problem.
    * The scale of the two IMU are slightly different, what explains the difference in the range shown in the pictures.

# System characteriscs / known issues / future work

  * Initial prototype inconsistently reads IMU with 10ms intervals and camera with 30ms intervals. On average, the IMU is read with 100Hz and the camera with 30fps.
  * The concurrency is making some readings of IMU being repeated. Locking and releasing the respective threads diminish signficantly the occurence of this issue but does not eliminate it. Reducing the overhead due to inter process communication is needed. Overhead is denominated here as the effect of causing the intervals of IMU readings be above 10ms. The initial tests show the occurrence of duplicate readings of ~9% of the readings. While overhead (readings above 10ms) is around 1% of the total readings. The first rate is still pretty high. Further exploration can be found at:
    https://github.ncsu.edu/aros/ARoS-Docs/edit/master/Reports/Rafael%20da%20Silva/ReportJuly14th/0-Report.md
    **Summer 2019 update** 
     This issue has been fixed in the Fall 2018.

Overall, for the data collection system, further enhancements can be done such as:
 1. Combine PiCamera APIs with OpenCV APIs in order to separate frame reading from frame recording and with that paralelize those tasks to explore computational capapilities of the Pi. In order to do that, according to this source:
 https://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python
 It is necessary to install OpenCV with H264 codec in order to make the API VideoWriter be compatible with such format. The example in the above link works but the video playback is faster than the actual motion what could be an indication of lower frame rate recording due to lack of resources on the Pi or some codec/format mismatch.
 **Summer 2019 update** This experiment was done. FourACC codec supports writing to h264 file even though it shows a warning for that. Images do not look good though, maybe further tweaking could enhance it.

2. Attempt USB camera architecture with multiprocessing namespace or manager. Less likely to improve current performace and make the system viable though.
 Due to time constraints, I believe that both approaches above may be taken in a second moment. With this study I believe we have gained enough insights about system limitations and possible extentions, which points to the architecture using the PiCamera. Using raspberry Pi for SLAM for example, which would require a regular camera like a USB one, may not be feasible, at least not with something as high as 30 FPS.
 
3. A mechanic packaging needs to be developed in order to encapsulate everything. The camera can go embeded with the IMU on top of the foot to allow the user to wear pants for example. The packaging also needs to have room for the LIPO batteries. So far our VeryGood batteries have been shown to be effective and its shape fits nicely to the purposes of data collection
**Summer 2019 update** The design was developed [here].(https://github.ncsu.edu/rdasilv2/RaspiCaseFiles/tree/master/Proj-ProstheticLeg)

4. A few tweaks in the software are needed to make it able to be started/stopped from a switch
**Summer 2019 update** It is currently supported.
