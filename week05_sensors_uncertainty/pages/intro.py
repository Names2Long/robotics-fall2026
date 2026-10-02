from lab.navigation import set_stage
from lab.environment import checks

def render(st):
    st.title('Week 5: Sensors, Noise, and Uncertainty')
    st.write('An individual lab: characterize imperfect measurements, calculate and compare estimates, then design and test context-sensitive decisions. Docker, Gazebo and ROS are not required.')
    st.info('Discuss concepts, but write your own predictions, calculations, analyses and policies. Your Course ID selects repeatable data and is locked once you begin.')
    st.markdown('1. Review four connected walkthroughs.\n2. Characterize your assigned sensor.\n3. Predict and record controlled filter/fusion experiments.\n4. Test and revise warehouse and assistive policies.\n5. Prepare, back up and commit your individual submission.')
    student=dict(st.session_state['student'])
    for key,label in [('name','Full name'),('email','Hunter email'),('course_id','Course ID / roster identifier')]:
        widget='identity.'+key
        if widget not in st.session_state: st.session_state[widget]=student.get(key,'')
        student[key]=st.text_input(label,key=widget,disabled=key=='course_id' and st.session_state['identity_locked'])
    st.session_state['student']=student
    st.subheader('Environment check')
    rows=checks();st.dataframe([{'Check':name,'Status':'Pass' if passed else 'Fix before beginning','Detail':detail} for name,passed,detail in rows],hide_index=True,width='stretch')
    ready=all(str(v).strip() for v in student.values()) and all(v for _,v,_ in rows)
    if st.button('Begin walkthroughs',disabled=not ready,type='primary'):
        st.session_state['identity_locked']=True;set_stage(st,'concepts')
    if st.session_state['identity_locked']: st.caption('To change Course ID, preserve your submission and ask the instructor for help. Do not relabel another person’s saved attempt.')
