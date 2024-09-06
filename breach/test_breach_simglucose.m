
signals = {'BG','CGM','CHO','insulin','LBGI','HBGI','Risk'};

params = {'patient',...
        'breakfast_time','breakfast_size',...
        'snack1_time','snack1_size',...
        'lunch_time','lunch_size',...
        'snack2_time','snack2_size',...
        'dinner_time','dinner_size',...
        'snack3_time','snack3_size'};

p0(1)= 1; 
for ip = 2:numel(params)
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

%% 
Btest = Bsimglucose.copy();
Btest.SetParam('patient',0:3:30)
Btest.SetParam('breakfast_size', [0 50 100],'combine'); % skip breakfast or not
Btest.Sim()

%%
close all
R = BreachRequirement('T1D_specs.stl', {'phi_lalive'})
R.Eval(Btest)
BreachSamplesPlot(R)

%%


%%
Bdom = Bsimglucose.copy();