import pandas as pd
from lab.evidence import student_seed
from lab.navigation import set_stage
from lab.session import response,set_response,complete_mission
from lab.submissions import save_mission
from lab.completion import current_check,mission_status
from lab.ui import render_check,text_response,numeric_response
from lab.controls import hydrate,M2_DEFAULTS,prediction
from simulation.plotting import pipeline_figure
from simulation.scenarios import fusion_dataset,run_pipeline

def render(st):
    st.header('Mission 2 — Calculate, predict, filter and fuse')
    st.write('Sensor A is fast/noisy/outlier-prone. Sensor B is steadier and biased, and samples every fourth time step. Keep unrelated settings fixed when comparing a parameter.')
    st.subheader('A. Calculate before experimenting')
    st.write('For the sequence [2.0, 2.1, 8.0, 2.2, 2.3] m, calculate the final output using a window of three valid readings. Use the walkthrough formulas; do not average all five readings.')
    numeric_response(st,'mission_2.manual_average','Final moving-average output (m)')
    numeric_response(st,'mission_2.manual_median','Final median output (m)')
    numeric_response(st,'mission_2.manual_fusion','Fused output for A=1.8 m, B=2.4 m, weight on A=0.25 (m)')
    st.subheader('B. Controlled experiments')
    st.markdown('Record at least **six distinct configurations**. A suggested sequence is:\n\n- Moving average: windows 3, 7 and 11, each with weight 0.25.\n- Median: window 3 with weights 0.25, 0.50 and 0.75.\n\nThis provides a matched filter comparison and a controlled fusion comparison. You may record more configurations to find a passing estimate.')
    hydrate(st,'m2',{**M2_DEFAULTS,**st.session_state['mission_2_controls']})
    a,b,c,d=st.columns(4)
    method=a.selectbox('Sensor A filter',['Raw/hold last','Moving average','Median','Exponential'],key='control.m2.method')
    window=b.slider('Window (valid readings)',1,15,step=2,key='control.m2.window',disabled=method not in ('Moving average','Median'))
    alpha=c.slider('Exponential α',.05,1.,step=.05,key='control.m2.alpha',disabled=method!='Exponential')
    weight=d.slider('Weight on Sensor A',0.,1.,step=.05,key='control.m2.weight_a')
    st.session_state['mission_2_controls']={'method':method,'window':window,'alpha':alpha,'weight_a':weight}
    data=fusion_dataset(student_seed(st.session_state['student']['course_id'],'mission_2'));current=run_pipeline(data,method,window,alpha,weight)
    forecast=prediction(st,'mission_2',current['settings'],'Predict how these settings will affect error and response delay compared with another configuration.')
    figure=pipeline_figure(data,current);st.pyplot(figure)
    import matplotlib.pyplot as plt
    plt.close(figure)
    st.dataframe([current['metrics']],hide_index=True,width='stretch')
    st.caption('Change at 6.00 s; delay ends at the third consecutive sample within 0.15 m of the new truth. Availability counts existing estimates, including held ones—not fresh measurements.')
    rows=[{'time_s':t,'truth_m':truth,'sensor_a_m':av,'sensor_b_m':bv,'filtered_a_m':fa,'filtered_b_m':fb,'estimate_m':e} for t,truth,av,bv,fa,fb,e in zip(data['time'],data['truth'],data['sensor_a'],data['sensor_b'],current['filtered_a'],current['filtered_b'],current['estimate'])]
    with st.expander('Inspect numerical outputs / accessible table'):
        st.dataframe(rows,hide_index=True);st.download_button('Download current pipeline CSV',pd.DataFrame(rows).to_csv(index=False),'pipeline.csv','text/csv')
    if st.button('Record this configuration',disabled=forecast is None):
        attempts=list(st.session_state['mission_2_attempts'])
        if not any(a['settings']==current['settings'] for a in attempts):
            attempts.append({'attempt':len(attempts)+1,'prediction':forecast,**current});st.session_state['mission_2_attempts']=attempts
        else: st.info('Those settings are already recorded. Change a relevant setting to add a distinct experiment.')
    attempts=st.session_state['mission_2_attempts']
    if attempts:
        st.subheader('Experiment log')
        st.dataframe([{'attempt':a['attempt'],**a['settings'],**a['metrics'],'prediction':a.get('prediction','Legacy record: predict and rerun')} for a in attempts],hide_index=True,width='stretch')
        widget='field.mission_2.selected'
        if widget not in st.session_state: st.session_state[widget]=min(int(response(st,'mission_2.selected',0)),len(attempts)-1)
        selected=st.selectbox('Configuration to submit',range(len(attempts)),format_func=lambda i:f"Attempt {attempts[i]['attempt']}: {attempts[i]['settings']}",key=widget)
        set_response(st,'mission_2.selected',selected)
        st.write('The selected recorded configuration—not the unrecorded controls above—is submitted.')
    text_response(st,'mission_2.comparison','Compare your three windows and matched median/moving-average pair. Cite numerical error and delay differences.')
    text_response(st,'mission_2.responsiveness','Explain smoothing versus responsiveness using measured delays. What could the delay mean for a nearby person?')
    text_response(st,'mission_2.fusion_choice','Compare your three fusion weights numerically and justify the selected weight using both sensors’ limitations.')
    check,signature,evidence=current_check(st,'mission_2');render_check(st,check)
    if st.button('Check and save Mission 2',disabled=not check.passed,type='primary'):
        chosen=attempts[response(st,'mission_2.selected',0)]
        output=[{**row,'estimate_m':value,'filtered_a_m':fa,'filtered_b_m':fb} for row,value,fa,fb in zip(rows,chosen['estimate'],chosen['filtered_a'],chosen['filtered_b'])]
        saved_figure=pipeline_figure(data,chosen)
        save_mission('mission_2',evidence,st.session_state['responses'],state_signature=signature,rows=output,figure=saved_figure)
        plt.close(saved_figure)
        complete_mission(st,'mission_2',signature);st.success('Mission 2 saved. Review your data before continuing.')
    if mission_status(st)['mission_2'] and st.button('Continue to Mission 3'): set_stage(st,'mission_3')
