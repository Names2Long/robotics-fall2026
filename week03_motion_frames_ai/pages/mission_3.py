from pathlib import Path
import sys
from lab.ai_log import assigned_pattern,load_lock,lock_original,write_diff
from lab.evidence import ai_evaluation,evidence_id
from lab.session import response,set_response,complete_mission
from lab.navigation import set_stage
from lab.submissions import save_mission,snapshot_pattern_source
from lab.ui import render_check
from missions.mission_3 import evaluate,current_hash

ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=ROOT/'ros2_ws/src/week03_pattern'
sys.path.insert(0,str(SOURCE_ROOT))
from week03_pattern.checks import SPECIFICATIONS


def answer(st,key,label,height=110):
    full=f'mission_3.{key}'; widget=f'm3.{key}'
    if widget not in st.session_state: st.session_state[widget]=str(response(st,full,''))
    value=st.text_area(label,key=widget,height=height);set_response(st,full,value)
    return value


def render(st):
    st.title('Mission 3: AI-assisted motion programming')
    st.write('Specify a motion pattern, ask an AI assistant for help, inspect its response, then implement and test your program. '
             'You will edit Python files in the shared workspace and keep evidence of your decisions.')
    lock=load_lock()
    if lock and not lock.get('integrity_valid'):
        st.error('The original AI record is missing, changed, or unreadable. Keep the files and restore the original record from your backup before continuing.')
        return
    identity=str(st.session_state.get('student',{}).get('course_id',''))
    pattern=lock.get('pattern') or response(st,'mission_3.assigned_pattern') or assigned_pattern(identity)
    st.info(f"Your pattern: {pattern.replace('_',' ')}. {SPECIFICATIONS[pattern]}")
    st.write('Use the robot body frame: +x forward, positive turning left. Speeds must stay within 0.22 m/s and 0.80 rad/s. '
             'Use positive durations, at most 30 seconds per segment and 60 seconds total. Plan in a clear 2 m by 2 m area. '
             'The course checks each intended distance within 0.02 m, angle within 0.04 rad, and arc radius within 0.02 m. '
             'Live checkpoint tolerances are 0.15 m and 0.20 rad because measured motion may differ from the ideal model.')
    st.header('A. Specify before prompting')
    spec=response(st,'mission_3.saved_specification','')
    if not spec and not lock:
        draft=answer(st,'specification','Describe the intended sequence, speeds, stopping behavior, and measurable success criteria.')
        if st.button('Save specification',disabled=not draft.strip()):
            set_response(st,'mission_3.saved_specification',draft)
            set_response(st,'mission_3.assigned_pattern',pattern);st.rerun()
        st.info('Save your specification to open the AI interaction step.');return
    st.write(spec or 'The specification is preserved with your original AI interaction.')
    st.header('B. Preserve the original AI interaction')
    if not lock:
        st.write('This is a ROS 2 Jazzy Python package. You implement only `build_pattern`. The course already supplies `pattern_node.py`, which calls your function, repeatedly publishes each returned segment to `/student_cmd_vel`, records checkpoints, and sends zero velocity when execution ends.')
        st.code('/workspace/week03_motion_frames_ai/ros2_ws/src/week03_pattern/week03_pattern/pattern_node.py',language='text')
        with st.expander('See the wrapper responsibilities'):
            st.code('''segments = build_pattern(name)
validate(segments)
for segment in segments:
    repeatedly_publish(segment.linear_x, segment.angular_z, segment.duration)
publish_zero_velocity()
record_path_and_stop_evidence()''',language='python')
            st.write('The wrapper does not decide your geometry. Your segment list determines the path. The course guard separately checks and forwards the commands.')
        st.write('Use an AI assistant of your choice. Include your saved specification and this interface in your prompt:')
        st.code(f"This is a ROS 2 Jazzy Python package. Implement only build_pattern(pattern_name: str) -> list[Segment] for '{pattern}' in the existing pattern.py.\nThe course-provided pattern_node.py calls this function, publishes the returned segments repeatedly through /student_cmd_vel, and sends the final zero command.\nUse the existing Segment class with linear_x (m/s), angular_z (rad/s), and duration (s).\nReturn the ordered segments for the assigned specification and raise ValueError for an unknown pattern name.\nStay within 0.22 m/s, 0.80 rad/s, 30 seconds per segment, and 60 seconds total.\nDo not replace the wrapper or course checks. Explain assumptions and propose tests.",language='text')
        prompt=answer(st,'original_prompt','Paste your exact prompt',160)
        output=answer(st,'original_output','Paste the complete original response without editing it',220)
        source=answer(st,'original_source','Paste the original pattern.py code only, without Markdown fences',220)
        if st.button('Preserve original AI interaction',disabled=not all(x.strip() for x in (prompt,output,source))):
            try:
                lock_original(identity,spec,prompt,output,source)
            except (OSError,ValueError) as error:
                st.error(f'Could not preserve the AI record: {error}. Copy these fields to a document before closing the guide.')
                return
            st.rerun()
        st.caption('Preserve these originals before editing. They are stored separately from your final code.');return
    if not lock.get('integrity_valid'):
        st.error('The preserved AI files have changed or are missing. Restore the original files before proceeding.');return
    st.success(f"Original interaction preserved at {lock['locked_at']}.")
    st.header('C. Inspect before running')
    st.write('Read the generated code. Identify each speed and duration, the order of segments, and the coordinate convention. '
             'Ask the assistant to explain unfamiliar syntax, but keep its original response intact. Follow-up interactions can be described in your disclosure.')
    answer(st,'assumptions','What assumptions did the AI make about motion, units, frames, or timing?')
    answer(st,'problems','What errors, omissions, or uncertain claims did you identify? Explain what you checked even if the code initially looked correct.')
    answer(st,'test_plan','Before running: describe a pattern behavior test, a velocity-limit test, and a stop test. Give expected results.')
    st.header('D. Implement and revise')
    st.write('In the virtual desktop editor or VS Code connected to the container, open this existing file. '
             'It contains a Segment class and an unfinished build_pattern function:')
    st.code('/workspace/week03_motion_frames_ai/ros2_ws/src/week03_pattern/week03_pattern/pattern.py')
    st.write('Keep the Segment class. Replace the NotImplementedError in build_pattern with your reviewed implementation. '
             'Return a list of Segment objects for your assigned pattern. Reject an unknown pattern name with ValueError. '
             'The wrapper handles ROS publication and the final stop. You do not need to recreate those parts.')
    st.code('''# Syntax example only: a short straight segment, not a complete assignment.
Segment(linear_x=0.10, angular_z=0.0, duration=1.0)''',language='python')
    st.latex(r't_{\rm straight}=d/v,\qquad t_{\rm turn}=|\Delta\theta/\omega|,\qquad R=|v/\omega|')
    st.write('Use these relationships to choose durations. For arcs, choose v and ω together to obtain the specified radius. '
             'Keep a note for each significant revision: what changed, why, and which test checks it.')
    answer(st,'modifications','Document your significant changes and the reason for each.')
    st.header('E. Add tests and run the evaluator')
    st.write('In the same editor, create test/test_student_pattern.py inside the week03_pattern package. '
             'Add at least two tests specific to your assigned geometry, such as segment order, leg distance, turning sign, or heading. '
             'The seven supplied tests check basic structure and limits. Use this structure and replace the comment with assertions:')
    st.markdown('''**Test ideas in pseudocode**

```text
segments = build assigned pattern
assert number of segments is expected
assert first segment moves forward
assert turn signs and segment order match the specification
assert speed multiplied by duration gives each required distance
assert angular speed multiplied by duration gives each required angle
assert every speed stays inside the course limits
assert the command after total duration is zero
```
''')
    st.code('''import os
import unittest
from week03_pattern.pattern import build_pattern

class MyPatternTests(unittest.TestCase):
    def test_my_pattern_geometry(self):
        segments = build_pattern(os.environ["WEEK03_ASSIGNED_PATTERN"])
        # Add assertions for your assigned pattern.
        self.fail("Replace this line with your geometry assertions")

    def test_my_pattern_order(self):
        # Check another property with a known expected result.
        self.fail("Replace this line with your order assertions")''',language='python')
    st.write('Save this exact file as `/workspace/week03_motion_frames_ai/ros2_ws/src/week03_pattern/test/test_student_pattern.py`. In a second virtual desktop terminal, run from the lab folder. This evaluates Python code and writes a report. It does not move the robot:')
    st.code('cd /workspace/week03_motion_frames_ai\npython3 scripts/evaluate_ai_pattern.py',language='bash')
    st.write('Each evaluator run executes all seven supplied tests and every student test in `test_student_pattern.py` once. It also checks the exact assigned geometry, command bounds, and the wrapper stop decision. At least two student tests and nine passing tests total are required.')
    st.header('F. Test with ROS')
    st.write('Keep Gazebo and the guard running in the first terminal. Start from a clear area and stop any teleoperation or other motion node. '
             'In the second terminal, build the package and run:')
    st.code('source /opt/ros/jazzy/setup.bash\ncd /workspace/week03_motion_frames_ai/ros2_ws\ncolcon build --packages-select week03_pattern --symlink-install\nsource install/setup.bash\nexport ROS_DOMAIN_ID=25\ncd ..\npython3 scripts/run_assigned_pattern.py',language='bash')
    st.write('Watch the robot and compare its path with your specification. The wrapper records checkpoint poses and checks low velocity after the final stop. '
             'After a complete run, `run_assigned_pattern.py` automatically refreshes the same evaluation report with current live evidence. '
             'For an optional interruption test, rerun and press Ctrl+C while it is moving, then observe whether it stops. '
             'That run is recorded separately and does not count as completing the whole pattern. After an interruption test, '
             'complete a fresh full run to obtain current live completion evidence.')
    result=ai_evaluation()
    if st.button('Refresh test evidence'): st.rerun()
    if result:
        st.table([
            {'Check':'pattern.py implementation found','Result':'Pass' if result.get('implementation_present') else 'Missing'},
            {'Check':'test/test_student_pattern.py found','Result':'Pass' if result.get('student_test_file_present') else 'Missing at the required path'},
            {'Check':'Student test methods','Result':f"{result.get('student_test_count',0)} found; 2 required"},
            {'Check':'All automated tests','Result':f"{'Pass' if result.get('unit_tests_passed') else 'Not yet'}: {result.get('test_count',0)} passing; 9 required"},
            *[{'Check':label,'Result':'Pass' if result.get(key) else 'Not verified / needs work'} for key,label in (
                ('shape_check_passed','Assigned geometry'),('commands_bounded','Command limits'),
                ('model_stop_passed','Stop decision'),('integration_passed','Live motion and stop'))]
        ])
        if not result.get('student_test_file_present'):
            st.error('Create `/workspace/week03_motion_frames_ai/ros2_ws/src/week03_pattern/test/test_student_pattern.py`, add at least two `test_...` methods, and rerun the evaluator. A total of 7 means only the supplied tests were found.')
        with st.expander('Test output'): st.code(result.get('unit_test_output',''))
        st.caption('After any source or test change, rerun the evaluator. A live run must also match the current source.')
    pending=st.checkbox('Live verification is pending because my ROS run could not complete',value=bool(response(st,'mission_3.live_pending',False)))
    set_response(st,'mission_3.live_pending',pending)
    if pending: answer(st,'live_issue','Record the error, what you tried, and which live behavior remains unverified.')
    st.caption('You may submit with documented pending live verification once the code and model tests pass. This does not claim that ROS execution succeeded.')
    st.header('G. Explain your evidence')
    answer(st,'evidence_analysis','In one response, explain what the important tests establish, cite results, explain what they do not establish, and identify one additional test or condition you would need.',170)
    answer(st,'ai_disclosure','Which AI tool did you use, for what purpose, and what did you personally review, change, and verify?')
    responses=st.session_state['responses'];check=evaluate(result,lock,responses,SOURCE_ROOT);render_check(st,check)
    relevant={k:v for k,v in responses.items() if k.startswith('mission_3.')}
    current_id=evidence_id(result,lock,relevant,current_hash(SOURCE_ROOT))
    if st.button('Check and save Mission 3',disabled=not check.passed,type='primary'):
        save_mission('mission_3',{'evidence_id':current_id,'ai_evaluation':result,'ai_lock':lock,
            'live_verification_pending':not result.get('integration_passed'),
            'check':[r.__dict__ for r in check.requirements]},responses)
        snapshot_pattern_source();write_diff(SOURCE_ROOT/'week03_pattern/pattern.py')
        complete_mission(st,'mission_3',current_id);st.rerun()
    if check.passed and st.session_state.get('checked_evidence_ids',{}).get('mission_3')==current_id:
        st.success('Mission 3 saved with the original AI record, revisions, code, tests, and verification status.')
        if st.button('Continue to final submission',type='primary'): set_stage(st,'final')
