function [cfg_fname, res_fname] = cfg2fnames(cfg, folder)
% creates a unique filename from a cfg sent to simglucose. 
    
if nargin<2
    folder ='traces_cache';
end

dhash = DataHash(cfg);
cfg_fname = [folder filesep 'simglucose_cfg_' dhash '.yml'];
res_fname = [folder filesep 'simglucose_res_' dhash '.csv'];

