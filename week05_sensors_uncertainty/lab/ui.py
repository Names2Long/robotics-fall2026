from lab.session import response,set_response

def text_response(st,key,label,*,height=100):
    widget='field.'+key
    if widget not in st.session_state: st.session_state[widget]=str(response(st,key,''))
    value=st.text_area(label,height=height,key=widget);set_response(st,key,value);return value

def numeric_response(st,key,label):
    widget='field.'+key
    if widget not in st.session_state: st.session_state[widget]=str(response(st,key,''))
    value=st.text_input(label,key=widget);set_response(st,key,value);return value

def render_check(st,check):
    st.dataframe([{'Requirement':x.label,'Actual':str(x.actual),'Expected':x.expected,'Status':'Pass' if x.passed else 'Not yet'} for x in check.requirements],hide_index=True,width='stretch')
    if check.passed: st.success(check.summary)
    else:
        for x in check.requirements:
            if not x.passed: st.info(f'Next: {x.label} — {x.expected}.')
