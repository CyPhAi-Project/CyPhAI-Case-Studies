init_simglucose_cfg
%% 
Btest = Bsimglucose.copy();
Btest.SetParam('use_PID',2)
Btest.SetParam('patient',0:1:29)

Btest.SetParamRanges('breakfast_size', cfg.meal.breakfast_size.range);
%Btest.SetParam('breakfast_size', cfg.meal.breakfast_size.range);
Btest.SampleDomain('breakfast_size', 2, 'grid', 'combine')
Btest.parSim()

%%
close all
R = BreachRequirement('T1D_specs.stl', {'phi_lalive', 'phi_lgood'});
R.Eval(Btest)
BreachSamplesPlot(R)
