matDir = sprintf('../../../data/walking_intention_dataset_post/results');
% the method and device combinations to be evaluated and compared
methods = { 'baye_mlp_single_cam', 'baye_gru_single_cam', 'baye_gru_single_cam', 'baye_gru_two_cam'}; 
devices = {'rpi','rpi','tobii','both'};

% subjuect ids to be evaluated: from the leave one subject out cross validation
subIDL = [0,1,2];
color = {'r', 'b', 'g', 'c'};

figure,
for i = 1:length(methods)
    T = load_cat_all(matDir, methods{i}, devices{i}, subIDL);
    [accB, confB] = cal_acc_conf(T.caliprobs(:), T.correct(:), 10, 100);
    line([0, 1], [0, 1], 'Color', 'black', 'LineStyle','--', 'LineWidth', 2, 'HandleVisibility', 'off'); hold on
    plot(confB, accB, color{i}, 'LineWidth', 3)
    scatter(confB, accB, color{i}, 'filled', 'LineWidth', 12, 'HandleVisibility', 'off'); hold off 
    grid on
end
legend('BMLP rpi', 'BGRU rpi', 'BGRU tobii', 'BGRU fea-fusion')
title('Reliability Diagram')
set(gca,'FontSize', 14, 'FontWeight', 'bold')


% calculate reliability diagrams
function [accB, confB] = cal_acc_conf(calibrated_prob, correct, nbins, min_n_samples)
[~,~,bin] = histcounts(calibrated_prob, nbins);
for k = 1:nbins
    idx = find(bin == k);
    sizeB(k) = length(idx);
    accB(k) = mean(correct(idx));
    confB(k) = mean(calibrated_prob(idx));
end

% only keep intervals where sizeB is large enough so that accB is reliable 
idx = find(sizeB > min_n_samples);
sizeB = sizeB(idx);
accB = accB(idx);
confB = confB(idx);
end

% load and orgnize data
function T = load_cat_all(matDir, method, device, subIDL)
for subID = subIDL
    filename = sprintf("%s/test_cali_%s_%s_v%d.mat", matDir, method, device, subID);
    data = load(filename);
    [~, predictions] = max(data.softmax, [], 3);
    correct = predictions == squeeze(data.terrains(:,end,:)+1);
    if exist('T','var')
        T.caliprobs = cat(1, T.caliprobs, data.caliprobs);
        T.correct = cat(1, T.correct, correct);
    else
        T.caliprobs = data.caliprobs;
        T.correct = correct;
    end
end
end
