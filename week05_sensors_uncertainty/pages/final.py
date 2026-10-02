from lab.autosave import submission_root,_atomic,save
from lab.completion import mission_status
from lab.final_reflection import render_final_reflection,write_final_reflection
from lab.submissions import write_manifest,manifest_current,submission_zip
from lab.ui import text_response

def render(st):
    st.header('Final synthesis and submission')
    status=mission_status(st)
    synthesis=text_response(st,'final.synthesis','In 150–250 words, connect measurement properties, estimation choices, and deployment context. Cite evidence from all three missions.',height=180)
    words=len(synthesis.split());st.caption(f'Synthesis: {words} words')
    reflection=render_final_reflection(st)
    checks=[(m.replace('_',' ').title()+' current answers and saved evidence',v) for m,v in status.items()]
    checks.extend([('Student name, email and Course ID',all(str(v).strip() for v in st.session_state['student'].values())),('Synthesis contains 150–250 words',150<=words<=250),('Reflection contains 1–300 words',reflection)])
    st.subheader('Submission readiness')
    st.dataframe([{'Requirement':name,'Status':'Ready' if ready else 'Not yet'} for name,ready in checks],hide_index=True,width='stretch')
    if st.button('Prepare submission',disabled=not all(v for _,v in checks),type='primary'):
        write_final_reflection(st);_atomic(submission_root()/'final_synthesis.md','# Final synthesis\n\n'+synthesis.strip())
        save(st);write_manifest(st);st.success('Submission prepared and checked. Download a backup, then commit and push your own work.')
    if manifest_current(st):
        st.download_button('Download Lab 5 submission ZIP',submission_zip(st),'lab05_submission.zip','application/zip')
        st.success('Current mission files, synthesis, reflection and file hashes are ready.')
    elif (submission_root()/'manifest.json').exists(): st.warning('The previous export is stale. Resolve the readiness checklist and prepare a fresh submission.')
    st.write('On your own computer, open a terminal in the repository root. Commit the complete folder to your personal fork:')
    st.code('git status\ngit add week05_sensors_uncertainty/student_submission\ngit commit -m "Submit Lab 5"\ngit push origin main',language='bash')
    st.write('Open that commit on GitHub and submit its URL through the course submission system. Check that its file list contains your submission. The ZIP is your backup, not an automatic upload.')
