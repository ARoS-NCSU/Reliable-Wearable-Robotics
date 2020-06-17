% VisualizeDataByAggregatorLowerLimb.m
% 
% Based on XRun_visualizeTrajectory.m by Jeremy Cole.
% Takes the data from accelerometers recorded together with picamera and
% playback the two together estimating the time shift between the two based
% on the timestamps provided by the picamera.
%
% SYNTAX: VisualizeDataByAggregatorLowerLimb
%
% PARAMETERS:
%   iniFrame: This is the starting frame where the video playback will
%       begin.
%   endFrame: This is the stopping frame where video playback will end.
%   saveVideo: This is a boolean flag that denotes whether or not you want
%       to save the video playback to file. The video playback will be a .avi
%       file located in the same folder as the video file specified in
%       run_SetupDirectories.m
% INPUTS:
% Assumes that 4 files are in the workspace,
%   Acc - The 5 columns accelerometer file
%   Gyro - The 5 columns gyroscope file
%   picam -  the single column picamera file
%   video - the .avi videofile
% OUTPUTS:
%	output_playback.avi if saveVideo flag is True.
%
% Other m-files required: run_SetupDirectories
% Subfunctions: none
% MAT-files required: none
%
% See also: run_SetupDirectories.m 
% Author: Rafael L. da Silva, Edgar Lobaton, Jeremy Cole.
% Created: Apr 6, 2019; Last revision: N/A
% ChangeLog: N/A
%------------\n- BEGIN CODE ------------\n--
%% Script Initialization
clear all;clc;
run_SetupDirectories %Import file directories and names
close all;
%%
% +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
% +
% +
% +                         Parameters
% +
% +
% +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

generate_video = true; % Flag to enable video processing
saveVideo = true; %Flag denoting whether or not to save the video playback as a .avi

% +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
%%
% Obtain number of frames, function is not recommended by Mathworks
vidObj = VideoReader([inputDir videoFile]);
noFrame = vidObj.NumberOfFrames;
filecamtime = ls([inputDir '*pts*']);
camtime_array = csvread([inputDir filecamtime],1,0);
%% Detect gaps on camera timestamp and interpolate
% The first reading is guaranteed to be correct based on several
% observations we made
correct_camtime_array = false;

if correct_camtime_array
    
    standard_gap = camtime_array(2,1)-camtime_array(1,1);
    
    for k=2:length(camtime_array)
        system_timegap = (camtime_array(k,2)-camtime_array(k-1,2));
        time_elapsed = (camtime_array(k,1)-camtime_array(k-1,1))/1e3;
        if system_timegap < 0.9*standard_gap || system_timegap > 1.1*standard_gap
            camtime_array(k,2) = camtime_array(k-1,2) + time_elapsed;
        end
    end
end
%%
fprintf('The Video has %.2d frames ...\n',noFrame);
fprintf('... at a resolution of %dx%d ...\n',vidObj.Width,vidObj.Height);
% Recreate object, it's needed since the previous line uses a deprecated
% feature
vidObj = VideoReader([inputDir videoFile]); % Have to recreate it due to Matlab restrictions to NumberOfFrames
% Frame rate
fps = vidObj.FrameRate;
fprintf('... Its Frame rate is: %.2f fps\n', fps);
% Dropped frames
dropped_frames = 100-length(camtime_array(:,1))/((camtime_array(end,2)-camtime_array(1,2))*fps)*100;
fprintf('%.2f%% of frames have been dropped though ...\n', dropped_frames);
fprintf('------------\n');

%%
% Load files to workspace
fileAcc = ls([inputDir '*acc*']);
Acc = csvread([inputDir fileAcc],2,0);
tlist_acc = Acc(:,1);
% de-indetified timestamps
tlist_acc_did = tlist_acc - tlist_acc(1,1);
Acc = csvread([inputDir fileAcc],2,1,[2 1 size(Acc,1)+1 3]);

fileGyro = ls([inputDir '*gyro*']);
Gyro = csvread([inputDir fileGyro],2,0);
tlist_gyro = Gyro(:,1);
tlist_gyro_did = tlist_gyro - tlist_gyro(1,1);
Gyro = csvread([inputDir fileGyro],2,1,[2 1 size(Gyro,1)+1 3]);
%%
% IMU average sampling frequency
%Acc
samp_t_acc = zeros(length(Acc),1);
for k=1:length(tlist_acc)-1, samp_t_acc(k) = tlist_acc(k+1,1)-tlist_acc(k,1);end
sens_freq_acc = 1/mean(samp_t_acc);
fprintf('The Acc Fs is: %.2fHz\n', sens_freq_acc);
%Gyro
samp_t_gyro = zeros(length(tlist_gyro),1);
for k=1:length(tlist_gyro)-1, samp_t_gyro(k) = tlist_gyro(k+1,1)-tlist_gyro(k,1);end
sens_freq_gyro = 1/mean(samp_t_gyro);
fprintf('The Gyro Fs is: %.2fHz\n', sens_freq_gyro);
% Recording duration
fprintf('------------\n');
fprintf('The time duration of Acc is %.2fs\n',tlist_acc(end,1)-tlist_acc(1,1));
fprintf('The time duration of Gyro is %.2fs\n',tlist_gyro(end,1)-tlist_gyro(1,1));
fprintf('The time duration of Video is %.2fs\n',camtime_array(end,2)-camtime_array(1,2));
fprintf('------------\n');
% even size Acc
if rem(length(tlist_acc_did),2) == 0
    fprintf('The largest time jump in Acc is %.4f s\n',...
    max(tlist_acc_did(2:2:end)-tlist_acc_did(1:2:end)));
else
    fprintf('The largest time jump in Acc is %.4f s\n',...
    max(tlist_acc_did(2:2:end)-tlist_acc_did(1:2:end-1)));
end
% even size Gyro
if rem(length(tlist_gyro_did),2) == 0
    fprintf('The largest time jump in Gyro is %.4f s\n',...
    max(tlist_gyro_did(2:2:end)-tlist_gyro_did(1:2:end)));
else
    fprintf('The largest time jump in Gyro is %.4f s\n',...
    max(tlist_gyro_did(2:2:end)-tlist_gyro_did(1:2:end-1)));
end

% even size Video
if rem(length(camtime_array),2) == 0
    fprintf('The largest time jump in Video is %.4f s\n',...
    max(camtime_array(2:2:end,2)-camtime_array(1:2:end,2)));
else
    fprintf('The largest time jump in Video is %.4f s\n',...
    max(camtime_array(2:2:end,2)-camtime_array(1:2:end-1,2)));
end
fprintf('------------\n');
%%
%  Reference signal
sig1 = Acc;
sig2 = Gyro;

%% Read Video & Visualize

if (generate_video)
    imageFig = figure(2);
    % Acc
    h1 = subplot(2,2,3); plot(tlist_acc_did,sig1); hold on;xlabel('Time [s]', 'FontSize', 20);
    title('Accelerometer', 'FontSize', 20);ylabel('$m/s^2$','Interpreter','Latex', 'FontSize', 20);
    set(gcf,'units','normalized','outerposition',[0 0 1 1]);
    rangeY = [min(sig1(:)) max(sig1(:))];
    h2 = plot([0 0],rangeY,'r-','linewidth',2); hold off;
    % Gyro
    hg = subplot(2,2,4); plot(tlist_gyro_did,sig2); hold on;xlabel('Time [s]', 'FontSize', 20);
    title('Gyroscope', 'FontSize', 20);ylabel('$deg/s$','Interpreter','Latex', 'FontSize', 20);
    set(gcf,'units','normalized','outerposition',[0 0 1 1]);
    rangeYg = [min(sig2(:)) max(sig2(:))];
    hg2 = plot([0 0],rangeYg,'r-','linewidth',2); hold off;

    % Script Initialization
    if (saveVideo)
        oldVidName = strsplit(videoFile,'.'); %Get the video file name without the file extension
        newVidName = [oldVidName{1} '_playback.avi']; %Add '_playback' to the new video name and save it as an .avi file
        v_playback = VideoWriter(newVidName);
        open(v_playback);
    end

    % Choose frame range
    ctFrame = 1; %Counter for video frame

    % "Slice" the video with the following 2 lines
    iniFrame = 140;
    endFrame = noFrame;

    %Memory saving
    clear Acc Gyro samp_t_acc samp_t_gyro sig1 sig2
    
    for i=1:endFrame
        im = readFrame(vidObj);
        if(ctFrame>=iniFrame)
            subplot(2,2,[1,2]);imshow(imrotate(im,180)); title('Recorded Video', 'FontSize', 20);
            text(50,100,num2str(ctFrame),'Color','w','FontSize',20); %show Frame # in Upper left of screen
            % Find the index of the closest signal sample
            [associated_acc_time, associated_acc_time_idx] = min(abs(tlist_acc - camtime_array(i,2)));
            [associated_gyro_time, associated_gyro_time_idx] = min(abs(tlist_gyro - camtime_array(i,2)));

            axis(h1, [[-2,2]+tlist_acc_did(associated_acc_time_idx),rangeY]);
            set(h2,'xdata',(tlist_acc_did(associated_acc_time_idx))*[1 1]);

            axis(hg, [[-2,2]+tlist_gyro_did(associated_gyro_time_idx),rangeYg]);
            set(hg2,'xdata',(tlist_gyro_did(associated_gyro_time_idx))*[1 1]);
            
            if(saveVideo) %Write image figure to video if flag is set
                writeVideo(v_playback,getframe(imageFig)); %Dimensions to keep for each frame (Height (Y-Axis),Width (X-Axis), Color Channel)
            end
        end
        ctFrame = ctFrame+1;
    end
    
    hold off;
    
    if (saveVideo)
        close(v_playback);
    end
end
return;
%------------\n- END OF CODE ------------\n--