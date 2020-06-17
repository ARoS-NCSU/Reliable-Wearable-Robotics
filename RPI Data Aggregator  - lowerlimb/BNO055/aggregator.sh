#!/bin/sh
video_file="picam_"
wid="1280"
hei="720"
fps_v="25"
now=$(date +"%Y_%m_%d_%s")
video_file=$(echo "picam_${now}.h264")
data_file=$(echo "pts_${now}.dat")
echo "FPS: "$fps_v
echo "Resolution: "$wid"x"$hei""
echo "raspivid -o "$video_file" -w "$wid" -h "$hei" -fps "$fps_v" -t 5400000 -pts "$data_file" -n"
sudo ifconfig wlan0 down
sudo python3 -u /home/pi/Aggregator/configure_bno055.py & PIDIY=$!
wait $PIDIY
sudo python3 -u /home/pi/Aggregator/IMU_reader.py $now & PIDMIX=$!
raspivid -o $video_file -w $wid -h $hei -fps $fps_v -t 5400000 -pts $data_file -n & PIDIOS=$!
wait $PIDMIX

sudo killall -SIGINT raspivid
sudo python3 /home/pi/Aggregator/camlog_correction.py $now
sudo python3 /home/pi/Aggregator/continue_button.py
sudo ifconfig wlan0 up
