from __future__ import annotations

def initialize(st):
    defaults={'stage':'intro','student':{'name':'','email':'','course_id':''},'responses':{},'completed_missions':[],'checked_evidence_ids':{},'mission_2_attempts':[],'mission_3_results':{},'mission_3_attempts':{},'mission_2_controls':{},'mission_3_controls':{},'prediction_locks':{},'visited_stages':['intro'],'walkthrough_index':0,'reviewed_walkthroughs':[],'identity_locked':False}
    for k,v in defaults.items(): st.session_state.setdefault(k,v)
    st.session_state.setdefault('legacy_evidence',{})

def response(st,key,default=''): return st.session_state.get('responses',{}).get(key,default)

def set_response(st,key,value):
    st.session_state['responses']={**st.session_state['responses'],key:value}

def sync_widgets(st):
    for key in list(st.session_state):
        if key.startswith('field.'): set_response(st,key[6:],st.session_state[key])
        elif key.startswith('identity.'):
            name=key[9:]
            if name!='course_id' or not st.session_state['identity_locked']:
                st.session_state['student']={**st.session_state['student'],name:st.session_state[key]}

def complete_mission(st,mission_id,eid):
    if mission_id not in st.session_state['completed_missions']:
        st.session_state['completed_missions']=[*st.session_state['completed_missions'],mission_id]
    st.session_state['checked_evidence_ids']={**st.session_state['checked_evidence_ids'],mission_id:eid}
