import pandas as pd
from lab.evidence import student_seed
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.completion import current_check,mission_status
from lab.ui import render_check,text_response
from lab.controls import hydrate,prediction
from simulation.scenarios import evaluate_rule,BASELINES,SAFETY_DISTANCE,METHODS,canonical_policy

def _controls(st,context):
    st.subheader(context+' robot')
    st.write('A controlled warehouse aisle: stops delay work; unsafe motion can damage equipment.' if context=='Warehouse' else 'An assistive robot near people with varied mobility: unsafe movement can injure; repeated unnecessary stops can reduce access and trust.')
    st.caption(f'Fixed evaluation safety distance: {SAFETY_DISTANCE[context]:.2f} m. Your stopping threshold does not change what the evaluator considers unsafe.')
    if st.button('Load supplied baseline',key='baseline.'+context):
        st.session_state['mission_3_controls']={**st.session_state['mission_3_controls'],context:dict(BASELINES[context])}
        for k,v in BASELINES[context].items(): st.session_state['control.'+context+'.'+k]=v
    saved=st.session_state['mission_3_controls'].get(context,BASELINES[context]);hydrate(st,context,saved)
    key=lambda name:'control.'+context+'.'+name
    a,b,c=st.columns(3)
    settings={'threshold':a.slider('Stopping threshold (m)',.55,1.25,step=.05,key=key('threshold')),
              'margin':b.slider('Caution margin (m)',0.,.45,step=.05,key=key('margin')),
              'weight_a':c.slider('Weight on Sensor A',0.,1.,step=.05,key=key('weight_a')),
              'filter_method':a.selectbox('Filter',list(METHODS),key=key('filter_method')),
              'window':b.slider('Window (valid readings)',1,11,step=2,key=key('window'),disabled=st.session_state[key('filter_method')] not in ('Moving average','Median')),
              'confirmations':c.slider('Readings at/below stop boundary before STOP',1,4,key=key('confirmations')),
              'missing_policy':st.selectbox('If both current readings are missing',['Stop','Insufficient evidence','Move'],key=key('missing_policy'))}
    settings=canonical_policy(settings)
    st.session_state['mission_3_controls']={**st.session_state['mission_3_controls'],context:settings}
    forecast=prediction(st,'mission_3.'+context,settings,'Predict which scenarios will challenge this policy and how error rates and delay will compare with a previous policy.')
    if st.button('Test '+context+' policy',key='test.'+context,disabled=forecast is None):
        result=evaluate_rule(settings,context,student_seed(st.session_state['student']['course_id'],'mission_3_'+context.lower()))
        result['prediction']=forecast
        histories=dict(st.session_state['mission_3_attempts']);history=list(histories.get(context,[]))
        if not any(r['settings']==settings for r in history): history.append(result)
        histories[context]=history;st.session_state['mission_3_attempts']=histories
        st.session_state['mission_3_results']={**st.session_state['mission_3_results'],context:result}
    history=st.session_state['mission_3_attempts'].get(context,[])
    if history:
        st.dataframe([{'attempt':i+1,**r['settings'],**r['metrics'],'prediction':r.get('prediction','')} for i,r in enumerate(history)],hide_index=True,width='stretch')
    result=st.session_state['mission_3_results'].get(context)
    if result:
        if result.get('data_version')!=2 or 'traces' not in result:
            st.info('Your earlier policy evidence is retained. Predict and rerun it to obtain the updated scenario checks.')
            st.dataframe([result.get('metrics',{})],hide_index=True)
            return
        if result['settings']!=settings: st.warning('These are results for earlier settings. Retest the displayed policy before saving.')
        st.write('Last tested settings:',result['settings'])
        st.dataframe([{**result['metrics'],'overall':'Pass' if result['passed'] else 'Revise'}],hide_index=True,width='stretch')
        st.dataframe(result['scenarios'],hide_index=True,width='stretch')
        criteria=result['criteria'];st.caption(f"Required: false-safe ≤ {criteria['false_safe_limit']:.0%}; unnecessary stop ≤ {criteria['unnecessary_stop_limit']:.0%}; delay ≤ {criteria['delay_limit']} s; zero dangerous-command events.")
        st.subheader('Replay / inspect scenario evidence')
        scenario=st.selectbox('Scenario',list(result['traces']),key='replay.'+context)
        rows=result['traces'][scenario];frame=pd.DataFrame(rows)
        st.line_chart(frame.set_index('time_s')[['truth_m','sensor_a_m','sensor_b_m','estimate_m']])
        index=st.slider('Time sample',0,len(rows)-1,0,key='cursor.'+context)
        row=rows[index];st.write(f"At {row['time_s']:.2f} s: {row['decision']} — {row['reason']}")
        st.dataframe([row],hide_index=True)
        with st.expander('Full numerical trace / keyboard-accessible alternative'): st.dataframe(frame,hide_index=True)
        st.download_button('Download '+context+' scenario CSV',frame.to_csv(index=False),context.lower()+'_'+scenario+'.csv','text/csv',key='csv.'+context)

def render(st):
    st.header('Mission 3 — Design, revise and test decisions')
    st.write('Test a predicted baseline and at least one distinct revised policy in each context. Every test runs all seven scenarios. Defaults may pass, but a pass alone does not replace the required experiment and explanation.')
    st.code('''if both CURRENT sensor readings are missing:
    apply your missing-data rule (STOP / INSUFFICIENT / MOVE)
elif no estimate exists:
    STOP
elif estimate <= stopping_threshold + margin:
    STOP after the required confirmation count; otherwise SLOW
elif estimate <= stopping_threshold + margin + 0.35 m:
    SLOW
else:
    MOVE''',language='text')
    st.write('Ground truth is not supplied to this rule; it is used only to evaluate it. False-safe means MOVE at/below the fixed safety distance. An unnecessary stop means STOP at least 0.65 m beyond that distance. Detection delay measures the time to STOP or abstain after each unsafe episode begins.')
    st.warning('This is a decision simulation, not a moving robot. Dangerous-command events count MOVE or SLOW when truth is ≤0.45 m; they are a risk proxy, not simulated physical collisions. INSUFFICIENT means abstain from movement. Held estimates are not fresh readings.')
    tabs=st.tabs(['Warehouse','Assistive'])
    with tabs[0]: _controls(st,'Warehouse')
    with tabs[1]: _controls(st,'Assistive')
    text_response(st,'mission_3.error_costs','Who bears false-safe and unnecessary-stop costs in each setting? Compare baseline and revised results, including numerical metrics.')
    text_response(st,'mission_3.context_comparison','Compare the two final policies. Explain at least two parameter differences with quantitative evidence and consequences for people.')
    text_response(st,'mission_3.limitations','What do these seven tests establish and not establish? Name a stakeholder to consult and one additional test before deployment.')
    check,signature,evidence=current_check(st,'mission_3');render_check(st,check)
    if st.button('Check and save Mission 3',disabled=not check.passed,type='primary'):
        rows=[{'context':context,'scenario':name,**row} for context,result in st.session_state['mission_3_results'].items() for name,trace in result['traces'].items() for row in trace]
        save_mission('mission_3',evidence,st.session_state['responses'],state_signature=signature,rows=rows)
        complete_mission(st,'mission_3',signature);st.success('Mission 3 saved. Review your metrics before continuing.')
    if mission_status(st)['mission_3'] and st.button('Continue to submission'): set_stage(st,'final')
