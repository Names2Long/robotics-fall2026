from __future__ import annotations
import argparse,hmac,os
from lab.autosave import load_state,save,STATE_KEYS
from lab.navigation import LABELS,current_stage,render_progress,set_stage
from lab.session import initialize,sync_widgets
from lab.controls import sync_controls
from lab.completion import refresh_completion
from lab_config import LAB
from pages import concepts,final,intro,mission_1,mission_2,mission_3

PAGES={'intro':intro.render,'concepts':concepts.render,'mission_1':mission_1.render,'mission_2':mission_2.render,'mission_3':mission_3.render,'final':final.render}

def run_smoke_test():
    from missions import mission_1 as m1,mission_2 as m2,mission_3 as m3
    from simulation.scenarios import fusion_dataset,run_pipeline,evaluate_rule,BASELINES
    from simulation.sensors import profile_for_seed,sample_metrics,static_samples
    seed=2026;name,config=profile_for_seed(seed);metrics=sample_metrics(static_samples(2.,240,config,seed),2.)
    responses={'mission_1.'+key:metrics[field] for key,field in [('mean','mean'),('variance','variance'),('bias','bias'),('median','median'),('dropouts','dropout_count'),('outliers','outlier_count')]}
    responses.update({'mission_1.profile':name,'mission_1.prediction':'A prediction before viewing sensor data.'})
    for mission,keys in [('mission_1',m1.REFLECTIONS),('mission_2',m2.REFLECTIONS),('mission_3',m3.REFLECTIONS)]:
        responses.update({mission+'.'+k:'An evidence-based explanation of measurements, comparisons, delays, people and limitations. '*3 for k in keys})
    responses.update({'mission_2.'+k:v for k,v in m2.CALCULATIONS.items()})
    assert m1.evaluate(metrics,name,responses).passed
    data=fusion_dataset(seed);attempts=[]
    for method,window,weight in [('Moving average',w,.25) for w in (3,7,11)]+[('Median',3,w) for w in (.25,.5,.75)]:
        attempts.append({'attempt':len(attempts)+1,'prediction':'I predict a measurable trade-off in error and delay.',**run_pipeline(data,method,window,.35,weight)})
    assert any(m2.evaluate(attempts,i,responses).passed for i in range(len(attempts)))
    histories={};results={};controls={}
    for context in BASELINES:
        histories[context]=[]
        for margin in (BASELINES[context]['margin'],BASELINES[context]['margin']+.05):
            settings={**BASELINES[context],'margin':margin};r=evaluate_rule(settings,context,seed);r['prediction']='I predict a more conservative decision with increased margin.';histories[context].append(r)
        results[context]=histories[context][-1];controls[context]=results[context]['settings']
    assert m3.evaluate(results,responses,histories,controls).passed
    print('Week 5 lab smoke test passed.')

def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title,page_icon='📡',layout='wide');initialize(st)
    if not st.session_state.get('loaded_autosave'):
        saved=load_state()
        for key in STATE_KEYS:
            if key in saved: st.session_state[key]=saved[key]
        for key in ('recovery_note','recovery_blocked'):
            if key in saved: st.session_state[key]=saved[key]
        if saved.get('student',{}).get('course_id') and saved.get('responses'): st.session_state['identity_locked']=True
        if not st.session_state['mission_3_controls']:
            st.session_state['mission_3_controls']={context:r['settings'] for context,r in st.session_state['mission_3_results'].items() if 'settings' in r}
        st.session_state['loaded_autosave']=True
    if st.session_state.get('recovery_blocked'):
        st.error(st.session_state['recovery_note']);st.stop()
    if st.session_state.get('recovery_note'): st.sidebar.warning(st.session_state['recovery_note'])
    st.sidebar.caption('Lab 5 persistence update: 2026-10-05. Streamlit email signup is optional and not part of the course.')
    if st.session_state.get('legacy_evidence'):
        import json
        from lab.autosave import json_ready
        st.sidebar.download_button('Download earlier experiment archive',json.dumps(json_ready(st.session_state['legacy_evidence']),indent=2,allow_nan=False),'lab5_earlier_experiments.json','application/json')
    sync_widgets(st);sync_controls(st);status=refresh_completion(st)
    render_progress(st)
    identity=all(str(v).strip() for v in st.session_state['student'].values())
    visited=set(st.session_state['visited_stages'])
    access={'intro':True,'concepts':identity,'mission_1':identity and len(st.session_state['reviewed_walkthroughs'])==4,
            'mission_2':status['mission_1'] or 'mission_2' in visited,'mission_3':status['mission_2'] or 'mission_3' in visited,'final':all(status.values()) or 'final' in visited}
    password=os.environ.get(LAB.instructor_password_env,'')
    if password:
        with st.sidebar.expander('Instructor navigation'):
            entered=st.text_input('Instructor password',type='password')
            st.session_state['instructor_navigation']=bool(entered and hmac.compare_digest(entered,password))
            st.caption('Navigation override only: it never creates completed evidence. Use WEEK05_SUBMISSION_DIR outside the starter for instructor trials.')
    instructor=st.session_state.get('instructor_navigation',False)
    with st.sidebar.expander('Lab navigation',expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage],key='nav.'+stage,disabled=not (access[stage] or instructor) or stage==current_stage(st),width='stretch'): set_stage(st,stage)
        st.caption('Saved missions: '+str(sum(status.values()))+'/3. You may revisit work; changed evidence must be checked again.')
    stage=current_stage(st)
    if not access.get(stage,False) and not instructor:
        st.info('Complete the preceding activity before opening this page. Your saved work is retained.')
    else: PAGES[stage](st)
    if stage!='intro' and st.button('Back',key='back.stage'):
        set_stage(st,LAB.stages[max(0,LAB.stages.index(stage)-1)])
    try:
        save(st);st.sidebar.caption('Answers, settings and experiments saved locally. Commit/push separately for a remote backup.')
    except OSError as error: st.sidebar.error('Autosave failed: '+str(error)+'. Keep this session open and download/copy your work before closing.')

def main():
    parser=argparse.ArgumentParser(description=LAB.title);parser.add_argument('--smoke-test',action='store_true');parser.add_argument('--preflight',action='store_true');args=parser.parse_args()
    if args.smoke_test: run_smoke_test()
    elif args.preflight:
        from lab.environment import preflight
        raise SystemExit(0 if preflight() else 1)
    else: run_streamlit_app()

if __name__=='__main__': main()
