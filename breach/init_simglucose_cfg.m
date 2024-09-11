
%% Default cfg
cfg = struct();

cfg.controller.type.value = 0; % 0: default, 1: PiD
cfg.controller.PID.P.value = 0.001;
cfg.controller.PID.I.value = 0.0001;
cfg.controller.PID.D.value = 0.001;
cfg.controller.target.value = 140;

cfg.patient.range = [0,29];
cfg.patient.value = 1;
cfg.meal.breakfast_time.value = 8;
cfg.meal.breakfast_time.range = [5, 9];
cfg.meal.breakfast_size.value = 50;
cfg.meal.breakfast_size.range = [40, 60];

cfg.meal.snack1_time.value = 10;
cfg.meal.snack1_time.range = [9, 11];
cfg.meal.snack1_size.value = 20;
cfg.meal.snack1_size.range = [10, 30];

cfg.meal.lunch_time.value = 12;
cfg.meal.lunch_time.range = [11, 13];
cfg.meal.lunch_size.value = 60;
cfg.meal.lunch_size.range = [50, 70];

cfg.meal.snack2_time.value = 14;
cfg.meal.snack2_time.range = [13, 15];
cfg.meal.snack2_size.value = 20;
cfg.meal.snack2_size.range = [10, 30];

cfg.meal.dinner_time.value = 18;
cfg.meal.dinner_time.range = [17, 19];
cfg.meal.dinner_size.value = 60;
cfg.meal.dinner_size.range = [50, 70];

cfg.meal.snack3_time.value = 20;
cfg.meal.snack3_time.range = [19, 21];
cfg.meal.snack3_size.value = 20;
cfg.meal.snack3_size.range = [10, 30];

%% Breach wrapper
signals = {'BG','CGM','CHO','insulin','LBGI','HBGI','Risk'};

params = {
        'patient',...
        'target',...
        'use_PID',...
        'P', 'I', 'D',...
        'breakfast_time','breakfast_size',...
        'snack1_time','snack1_size',...
        'lunch_time','lunch_size',...
        'snack2_time','snack2_size',...
        'dinner_time','dinner_size',...
        'snack3_time','snack3_size'};

p0(1) = 1;
p0(2) = cfg.controller.target.value;
p0(3) = cfg.controller.type.value;
p0(4) = cfg.controller.PID.P.value;
p0(5) = cfg.controller.PID.I.value;
p0(6) = cfg.controller.PID.D.value;
for ip = 7:numel(params)
    p0(ip) = cfg.meal.(params{ip}).value;
end


Bsimglucose  =  BreachSystem('simglucose ', ...                 % system name 
                         signals,... % signals
                         params,...   % parameters
                         p0, ...                   % default values for parameters
                         @sim_breach_simglucose);


time = (0:3:24*60)/60; % one day, in hours, sampling 3 min

Bsimglucose.SetTime(time);


Bnom = Bsimglucose.copy();
Bnom.Sim();
Bnom.PlotSignals();




