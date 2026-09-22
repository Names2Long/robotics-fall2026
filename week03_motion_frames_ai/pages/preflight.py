import os
from pathlib import Path
import shlex
import signal
import subprocess
from datetime import datetime,timezone
from lab.evidence import preflight
from lab.session import set_response
from lab.navigation import set_stage


def render(st):
    st.title('Check your Lab 3 environment')
    st.write('Reuse the shared Docker environment. These checks distinguish installed packages from a running simulator connection.')
    st.markdown('Open the [virtual desktop](http://localhost:6080/vnc.html?autoconnect=1&resize=remote). Use Applications → Shells to open a terminal. Leave the guide open in your browser.')
    st.subheader('1. Build the workspace, then launch the simulator')
    st.write('In terminal A, run the build check. When it finishes, run the launch command and leave it running:')
    st.code('cd /workspace/week03_motion_frames_ai\nbash scripts/course_preflight.sh --setup\nbash scripts/launch_lab.sh',language='bash')
    st.subheader('2. Check the live connections')
    st.write('When Gazebo is visible and running, use the button below or run the following in a second virtual desktop terminal:')
    st.code('cd /workspace/week03_motion_frames_ai\nbash scripts/course_preflight.sh',language='bash')
    if st.button('Run live preflight checks',type='primary'):
        if os.name!='posix' or not Path('/opt/ros/jazzy/setup.bash').exists():
            st.warning('The guide is running outside the ROS container. Run the terminal command inside the virtual desktop, or continue with reference activities below.')
        else:
            script=Path(__file__).resolve().parents[1]/'scripts/course_preflight.sh'
            with st.spinner('Checking packages, simulator messages, and transforms (up to 30 seconds)...'):
                proc=subprocess.Popen(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
                try:
                    log,_=proc.communicate(timeout=30)
                    st.session_state['preflight.log']=log[-4000:]
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try: proc.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL);proc.communicate()
                    st.session_state['preflight.log']='Checks timed out. Restart the simulator and retry, or use the reference route.'
            st.rerun()
    if st.button('Refresh saved preflight'): st.rerun()
    result=preflight()
    try:
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(result.get('captured_at',''))).total_seconds()
    except (ValueError,TypeError): age=999999
    ready=bool(result.get('scope')=='live' and result.get('ready') and 0<=age<300)
    if result:
        st.caption(f"Saved {result.get('scope','older')} check: {result.get('captured_at','unknown time')}. Rerun after restarting Docker or the simulator.")
        if age>=300: st.info('This check is more than five minutes old. Rerun it or select the reference route.')
        for item in result.get('checks',[]):
            if item.get('passed'): st.success(item['check']+': passed')
            else: st.warning(item['check']+': '+item.get('detail','Not ready')+' '+item.get('recovery','Retry the check.'))
    if st.session_state.get('preflight.log'):
        with st.expander('Latest check output'): st.code(st.session_state['preflight.log'])
    if st.button('Continue to Mission 1',disabled=not ready):
        set_response(st,'environment.mode','live');set_response(st,'environment.preflight',result);set_stage(st,'mission_1')
    st.subheader('Continue while resolving a setup problem')
    st.write('You can complete the browser activities and use labeled modeled/reference evidence for Missions 1 and 2. '
             'Mission 3 still requires your implementation and passing Python tests. Any unfinished ROS verification is recorded in the submission.')
    issue=st.text_input('Briefly describe the setup problem',key='environment.issue')
    if st.button('Continue with reference activities',disabled=not issue.strip()):
        set_response(st,'environment.mode','reference');set_response(st,'environment.issue',issue);set_stage(st,'mission_1')
