import pandas as pd
from lab.evidence import student_seed
from lab.navigation import set_stage
from lab.session import response,set_response,complete_mission
from lab.submissions import save_mission
from lab.completion import current_check,mission_status
from lab.controls import prediction
from lab.ui import render_check,text_response,numeric_response
from simulation.plotting import sample_figure
from simulation.sensors import profile_for_seed,sample_metrics,static_samples

def render(st):
    st.header('Mission 1 — Characterize an imperfect sensor')
    st.write('A target is exactly 2.00 m away. You will analyze 240 readings from one assigned sensor. Before viewing them, predict what evidence would distinguish a consistently biased sensor from a noisy sensor.')
    seed=student_seed(st.session_state['student']['course_id'],'mission_1')
    forecast=prediction(st,'mission_1',{'seed':seed},'Predict how mean, bias and variance would differ for biased versus noisy readings.')
    if forecast is None: return
    set_response(st,'mission_1.prediction',forecast)
    name,config=profile_for_seed(seed);samples=static_samples(2.,240,config,seed);metrics=sample_metrics(samples,2.)
    st.write('Ignore missing values when computing statistics. Sample variance uses n−1. MAD is the median of |reading−median|; average the two middle values when their count is even. An outlier differs from the median by more than max(0.30 m, 3×1.4826×MAD).')
    st.latex(r'\bar d=\frac{1}{n}\sum d_i,\quad s^2=\frac{\sum(d_i-\bar d)^2}{n-1},\quad \text{bias}=\bar d-2.00\ \mathrm{m}')
    st.write('For [1.9, 2.0, 2.1] m, mean=2.0 m, sample variance=0.01 m² and bias=0.0 m. Variance measures spread; bias measures displacement from truth.')
    figure=sample_figure(samples,2.);st.pyplot(figure)
    import matplotlib.pyplot as plt
    plt.close(figure)
    rows=[{'sample':i,'measurement_m':v,'valid':v is not None} for i,v in enumerate(samples)]
    st.download_button('Download measurements.csv',pd.DataFrame(rows).to_csv(index=False),'mission1_measurements.csv','text/csv')
    with st.expander('Accessible measurement table'): st.dataframe(rows,hide_index=True)
    fields=(('mean','Mean (m)'),('variance','Variance (m²)'),('bias','Bias (m)'),('median','Median (m)'),('dropouts','Dropout count'),('outliers','Outlier count'))
    for key,label in fields: numeric_response(st,'mission_1.'+key,label)
    options=['Choose…','biased','noisy','quantized','outlier_prone'];widget='field.mission_1.profile'
    if widget not in st.session_state: st.session_state[widget]=response(st,'mission_1.profile','Choose…')
    selected=st.selectbox('Dominant imperfection',options,key=widget);set_response(st,'mission_1.profile',selected)
    text_response(st,'mission_1.bias_vs_variance','Compare your prediction with the statistics: why do bias and variance describe different failures?')
    text_response(st,'mission_1.more_samples','Would more samples remove this sensor’s main problem? Explain using your numerical evidence.')
    text_response(st,'mission_1.robot_consequence','Give one robot decision this imperfection could change and explain the consequence for someone affected.')
    check,signature,evidence=current_check(st,'mission_1');render_check(st,check)
    if st.button('Check and save Mission 1',disabled=not check.passed,type='primary'):
        save_mission('mission_1',evidence,st.session_state['responses'],state_signature=signature,rows=rows,figure=figure)
        complete_mission(st,'mission_1',signature);st.success('Mission 1 saved. Review your evidence before continuing.')
    if mission_status(st)['mission_1'] and st.button('Continue to Mission 2'): set_stage(st,'mission_2')
