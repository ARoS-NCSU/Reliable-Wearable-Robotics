clear
clc
close all

matDir = sprintf('/path/to/result_folder');
methods = { 'baye_mlp_single_cam', 'baye_gru_single_cam', 'baye_gru_single_cam', 'baye_gru_two_cam'}; 
color = {'r', 'b', 'g', 'c'};
devices = {'rpi','rpi','tobii','both'};
subIDL = [0,1,2];

figure,
for i = 1:length(methods)
    accAve = cal_accuracy(matDir, methods{i}, devices{i}, subIDL);
    plot(1:4, accAve, color{i}, 'LineWidth', 3), hold on
    scatter(1:4, accAve, color{i}, 'filled', 'LineWidth', 12, 'HandleVisibility', 'off');
    grid on
end
xticks(0.5:0.5:4.5)
xticklabels({'', 'current', '', '1s', '', '2s', '', '4s'});

legend('BMLP rpi', 'BGRU rpi', 'BGRU tobii', 'BGRU fea-fusion')
title('Prediction Accuracy')
set(gca,'FontSize', 14, 'FontWeight', 'bold')


function accAve = cal_accuracy(matDir, method, device, subIDL)
for subID = subIDL
    filename = sprintf("%s/test_cali_%s_%s_v%d.mat", matDir, method, device, subID);
    data = load(filename);
    [~, predictions] = max(data.softmax, [], 3);
    correct = predictions == squeeze(data.terrains+1);
    accuracy = mean(correct,1);
    if exist('accList','var')
        accList = cat(1, accList, accuracy);
    else
        accList = accuracy;
    end
end
accAve = mean(accList,1);
end
