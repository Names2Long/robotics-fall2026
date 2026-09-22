from lab.autosave import submission_root, _atomic
from lab.completion import mission_status,verification_summary
from lab.evidence import evidence_id
from lab.final_reflection import render_final_reflection,write_final_reflection,word_count
from lab.navigation import set_stage
from lab.submissions import write_manifest,submission_zip
from lab.session import response,set_response


def render(st):
    st.title('Review and submit Lab 3')
    status=mission_status(st)
    st.table([{'Mission':name.replace('_',' ').title(),'Status':'Saved and current' if ready else 'Needs checking or saving'} for name,ready in status.items()])
    for name,ready in status.items():
        if not ready and st.button('Return to '+name.replace('_',' '),key='return.'+name): set_stage(st,name)
    st.subheader('Evidence sources')
    st.table(verification_summary(st))
    st.caption('Modeled/reference work and pending ROS verification are identified in the manifest. They are not labeled as live measurements.')
    st.subheader('Short technical synthesis')
    st.write('In 100 to 150 words: a robot motion program can be technically correct and still fail as part of a sociotechnical system. '
             'Give one example and identify the additional evidence needed to evaluate it. Consider pedestrian expectations, accessibility, shared-space rules, or workplace practices.')
    if 'final.synthesis.widget' not in st.session_state: st.session_state['final.synthesis.widget']=response(st,'final.synthesis','')
    synthesis=st.text_area('Your synthesis',height=180,key='final.synthesis.widget');set_response(st,'final.synthesis',synthesis)
    words=word_count(synthesis);st.caption(f'{words} words; required range 100 to 150')
    reflection_ready=render_final_reflection(st)
    responses=st.session_state['responses']
    digest=evidence_id(st.session_state['student'],st.session_state.get('checked_evidence_ids',{}),synthesis,responses.get('final.course_reflection',''),status)
    ready=all(status.values()) and 100<=words<=150 and reflection_ready
    if not ready: st.info('Save any outstanding missions and complete both writing sections before preparing the submission.')
    if st.button('Prepare submission',disabled=not ready,type='primary'):
        root=submission_root();root.mkdir(parents=True,exist_ok=True)
        _atomic(root/'synthesis.md','# Technical synthesis\n\n'+synthesis.strip()+'\n')
        write_final_reflection(st)
        import json
        _atomic(root/'student.json',json.dumps(st.session_state['student'],indent=2))
        write_manifest(st);st.session_state['final.prepared_digest']=digest
    if ready and st.session_state.get('final.prepared_digest')==digest:
        try:
            archive=submission_zip()
        except (OSError,ValueError) as error:
            st.warning(str(error));return
        st.success('Submission prepared. Download a backup, then commit and push your work.')
        st.download_button('Download Lab 3 submission ZIP',data=archive,file_name='lab03_submission.zip',mime='application/zip')
        st.write('On your own computer, open a terminal in the cloned repository folder. These commands include your individual submission and final code:')
        st.code('git status\ngit add week03_motion_frames_ai/student_submission week03_motion_frames_ai/ros2_ws/src/week03_pattern week03_motion_frames_ai/ros2_ws/src/week03_camera_transform\ngit commit -m "Submit Lab 3"\ngit push',language='bash')
        st.write('Submit the link to your pushed commit through the course submission channel. In GitHub, open your repository, select the commit, and copy its URL. '
                 'Ensure your instructor has access to the repository. The ZIP is a backup or an alternative if your instructor requests it.')
        st.caption('If you change answers, code, or evidence afterward, revisit the affected mission, save it again, and prepare a fresh submission.')
