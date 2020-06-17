%This script sets the variables necessary for saving data to and reading
%data from a Dataset folder.

%% Parameters associated with Kamigami datasets %%

%Directories
inputDir = 'C:\Users\rdasilv2\Gdrive\Backup Rafael\Documents\NC State\Research Related\ML and DSP\Proj - Lower Limb Prosthesis\data\Session08\'; 
%Input Directory for Dataset

%Files
videoFile = ls([inputDir 'picam_*']); %Video File for dataset
