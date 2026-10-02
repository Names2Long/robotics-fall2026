M2_DEFAULTS={'method':'Raw/hold last','window':5,'alpha':.35,'weight_a':.25}

def hydrate(st,prefix,settings):
    for key,value in settings.items():
        widget='control.'+prefix+'.'+key
        if widget not in st.session_state: st.session_state[widget]=value

def sync_controls(st):
    m2=dict(st.session_state['mission_2_controls'])
    m3={context:dict(values) for context,values in st.session_state['mission_3_controls'].items()}
    for key in list(st.session_state):
        if key.startswith('control.m2.'): m2[key[len('control.m2.'):]]=st.session_state[key]
        for context in ('Warehouse','Assistive'):
            prefix='control.'+context+'.'
            if key.startswith(prefix): m3.setdefault(context,{})[key[len(prefix):]]=st.session_state[key]
    from simulation.scenarios import canonical_policy
    st.session_state['mission_2_controls']=m2;st.session_state['mission_3_controls']={k:canonical_policy(v) for k,v in m3.items()}

def prediction(st,activity,settings,label):
    from lab.ui import text_response
    text=text_response(st,activity+'.prediction_draft',label)
    if st.button('Save prediction for these settings',key='predict.'+activity,disabled=len(text.strip())<20):
        st.session_state['prediction_locks']={**st.session_state['prediction_locks'],activity:{'settings':dict(settings),'text':text.strip()}}
    lock=st.session_state['prediction_locks'].get(activity,{})
    ready=lock.get('settings')==settings and len(lock.get('text',''))>=20
    if ready: st.success('Prediction saved for the displayed settings. You may test now.')
    else: st.info('Write at least 20 characters and save a prediction for these settings before testing.')
    return lock.get('text','') if ready else None
