function [t_out, X,p, status] = sim_breach_simglucose(Sys, t_in, p) 
%
%  [t_out,X,p] = sim_breach_glucose(Sys,p,t_in) 
%  
%  Inputs: Sys, p and t_in are provided by Breach. 
%  - Sys is a structure with information about signals and parameters. In
%  particular,  Sys.ParamList is a cell of signals and parameter names such
%  that:
%     - Sys.ParamList(1:Sys.DimX) returns names of all signals
%     - Sys.ParamList(Sys.DimX+1:Sys.DimP) returns the names of constant parameters    
%  -  p is an array of length Sys.DimX+Sys.DimP. 
%  -  t_in is of the form [0 t_in(end)]  or [0 t_in(2) ... t_in(end)], strictly increasing
% 
%  Outputs:  simfn has to return the following:    
%      - t_out must be such that t_out(1) =0 and t_out(end) = t_in(end). 
%        In addition, if t_in has more than two elements, then t_out must be
%        equal to t_in. Otherwise, t_out can have as many elements as
%        returned by the simulation.
%     - X must be of dimensions (Sys.DimX, t_out). The rows of X must
%     contain simulation results for signals named in Sys.ParamList(1:DimX)
%    -  p is the same as p unless the simulator changes it (outputs scalars
%           in addition to signals)

% recover parameters from p - for legacy reason, the first elements in p
% are for signals, and parameters start at index Sys.DimX+1 = 3


try
    % sim time
    t_out = [0:3:24*60]/60;

    % Patient
    cfg.patient.value = p(8);

    % Controller
    cfg.controller.target.value = p(9);
    cfg.controller.type.value = p(10);
    cfg.controller.PID.P.value = p(11);
    cfg.controller.PID.I.value = p(12);
    cfg.controller.PID.D.value = p(13);

    % Meal
    cfg.meal.breakfast_time.value = p(14);
    cfg.meal.breakfast_size.value = p(15);

    cfg.meal.snack1_time.value = p(16);
    cfg.meal.snack1_size.value = p(17);

    cfg.meal.lunch_time.value = p(18);
    cfg.meal.lunch_size.value = p(19);

    cfg.meal.snack2_time.value = p(20);
    cfg.meal.snack2_size.value = p(21);

    cfg.meal.dinner_time.value = p(22);
    cfg.meal.dinner_size.value = p(23);

    cfg.meal.snack3_time.value = p(24);
    cfg.meal.snack3_size.value = p(25);
    [cfg_fname, res_fname] = cfg2fname(cfg);
    cfg.out = res_fname;

    WriteYaml(cfg_fname, cfg);
    pause(.1)

    if exist(res_fname, 'file')~=2
        cmd = ['python simglucose_breach_wrapper.py ' cfg_fname];
        [status, output] = system(['python simglucose_breach_wrapper.py ' cfg_fname]);
    end

    % format outputs as expected by Breach
    X = csvread(res_fname,1,1)';
    status = 0; % everything went well, should be -1 otherwise
catch ME
    warning(ME.identifier, '%s', ME.message);
    X = zeros([Sys.DimX numel(t_out)]);
    status = -1;
end