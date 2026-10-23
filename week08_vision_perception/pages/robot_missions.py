"""Guided camera-in-the-loop missions, with automatic shared-folder evidence."""
import base64
import json
import time
from dataclasses import asdict
from perception.dataset import ROOT
from perception.vision_control import VisionSettings
from perception.robot_evidence import validate_report
from lab.autosave import save, submission_root, write_json, atomic
from lab.ui import text_response, mission_status


def terminal(st, title, commands):
    st.markdown('**'+title+'**')
    st.code('cd /workspace/week08_vision_perception\n'+commands,language='bash')


def start_simulation(st):
    st.subheader('Start the robot simulation')
    st.write('Mission 1 measured detectors on saved images. Missions 2 and 3 close the loop: Gazebo produces a new camera image after the robot moves, your saved settings change the controller, and the next command depends on that new image. No physical robot or personal camera is used.')
    st.markdown('''1. Use the course virtual desktop and the workspace checked during preflight. If you have only used the local guide, return to Preflight in the course ROS 2 environment first. Run these commands in desktop terminals, not in Windows PowerShell.
2. Launch the pillar world and leave its terminal running. The launch starts Gazebo, the camera bridge, the simulation clock bridge and a separate velocity guard. Only one lab world should run at a time.
3. In a second terminal, run the live check. It must receive changing camera frames and an advancing simulation clock. Package installation alone cannot pass this check. Continue only when all four checks print PASS.
''')
    terminal(st,'Terminal 1: start the pillar world','bash scripts/launch_vision_world.sh pillars')
    terminal(st,'Terminal 2: check the running system','bash scripts/check_vision.sh')
    st.write('Each script sources ROS and the built workspace and sets the same ROS domain and Gazebo partition. Do not start another TurtleBot world from a different lab. That can introduce duplicate camera topics or competing commands.')
    if st.button('Read live check result'):
        path = ROOT/'runtime/evidence/vision_preflight.json'
        if not path.exists(): st.warning('Run the terminal check first. No report was found in this repository.')
        else:
            report = json.loads(path.read_text())
            active_path = ROOT/'runtime/worlds/active.json'
            active = json.loads(active_path.read_text()) if active_path.exists() else {}
            current = report.get('world_run') == active and 0 <= time.time()-report.get('checked_at',0) < 300
            st.table([{'check':k,'passed':v} for k,v in report['checks'].items()])
            (st.success if current and report.get('ready') else st.warning)('Live check passed for this world' if current and report.get('ready') else 'Check missing, failed or out of date. Rerun it for the current world.')
    st.info('No image or a stopped clock means stop and fix the environment. Check that Gazebo is playing, the world terminal has no error, and you built after updating. Close old launch terminals before retrying. Do not disable the guard to make motion work.')


def controls(st,kind):
    defaults = asdict(VisionSettings(kind=kind))
    saved = st.session_state['settings'].get(kind,{})
    defaults.update(saved)
    st.subheader('Configure the supplied controller')
    st.write('You are tuning an executable ROS controller, not entering an answer that pretends to run code. Save settings, stop any previous controller with Ctrl+C, and start it again to use the new settings. Changing a slider alone does not change a running robot.')
    defaults['gain'] = st.slider('Steering gain',.05,4.,float(defaults['gain']),.05,key=kind+'.gain')
    st.caption('Angular command = minus gain times normalized image error, limited to the lab turn-rate bound. Higher gain corrects more strongly but can cause oscillation.')
    if kind == 'pillar_search':
        defaults['colors'] = st.selectbox('Requested sequence',('blue','red,green,turquoise,blue'),index=0 if defaults['colors']=='blue' else 1)
        defaults['tolerance'] = st.slider('Center tolerance',.02,.30,float(defaults['tolerance']),.01)
        defaults['hold_seconds'] = st.slider('Centered hold time (seconds)',.2,2.,float(defaults['hold_seconds']),.1)
        st.caption('A tolerance of 0.10 allows the target centroid within 10 percent of the half-image width. Three distinct centered frames and the hold time are required before advancing to the next color.')
    else:
        defaults['speed'] = st.slider('Maximum forward speed (m/s)',.03,.18,float(defaults['speed']),.01)
        defaults['roi_top'],defaults['roi_bottom'] = st.slider('Vertical region of interest as fractions of image height',0.,1.,(float(defaults['roi_top']),float(defaults['roi_bottom'])),.05)
        defaults['hue_low'],defaults['hue_high'] = st.slider('Magenta hue interval',0,179,(int(defaults['hue_low']),int(defaults['hue_high'])))
        st.caption('The region of interest is the horizontal strip used to follow the nearby line. A strip higher in the image looks farther ahead. Hue is OpenCV hue from 0 to 179, not degrees.')
    defaults['min_fraction'] = st.select_slider('Minimum selected contour fraction of region',(.0005,.001,.002,.005,.01,.02),value=float(defaults['min_fraction']),key=kind+'.area')
    if st.button('Save controller settings',key=kind+'.save'):
        config = VisionSettings(**defaults)
        st.session_state['settings'][kind] = asdict(config)
        write_json(submission_root()/kind/'settings.json',asdict(config))
        save(st)
        st.success('Saved. The next controller start reads these settings.')


def attempts(st,kind,world=None):
    prefix = kind if world is None else kind+'.'+world
    st.subheader('Inspect and retain recorded attempts')
    st.write('Stop the controller with Ctrl+C before importing. Completed attempts stop automatically. The recorder saves settings, simulation timestamps, commands and diagnostic images in the shared repository. Refresh the list after each run. Keep earlier attempts to compare settings.')
    st.button('Refresh recorded attempts',key=prefix+'.refresh')
    files = sorted((ROOT/'runtime/robot_runs'/kind).glob('*/run.json'),reverse=True)
    if world:
        def matches(path):
            try: return json.loads(path.read_text()).get('world') == world
            except (ValueError,OSError): return False
        files = [path for path in files if matches(path)]
        st.info('Required for '+world+': select your recorded attempt and press Keep this attempt in my submission. Running the controller alone does not import it into your submission.')
    selected = st.session_state['evidence'].get(kind,{}).get('reports',[])
    if not files: st.info('No recorded attempts yet. Run the controller in the virtual desktop.')
    else:
        path = st.selectbox('Recorded attempt',files,format_func=lambda p:p.parent.name,key=prefix+'.attempt')
        try:
            report = json.loads(path.read_text())
            summary = validate_report(report,kind)
            st.json(summary,expanded=True)
            st.caption('Elapsed time is simulation time. Image error is normalized horizontal offset, not metres. Line-loss events count entries into LINE_LOST. Camera waits indicate missing or stale frames. Success is not required to retain an attempt.')
            with st.expander('Settings used for this recorded attempt'):
                st.json(report['config'])
                if report.get('program'): st.code(report['program'],language='python')
            cols = st.columns(3)
            for column,name in zip(cols,('original','mask','annotated')):
                if name in report['images']: column.image(base64.b64decode(report['images'][name]),caption=name,width='stretch')
            st.write('The white mask is the selected color. The cyan rectangle is the processing region, magenta is its center, and yellow is the selected contour centroid. The most recent images may show the finish or a failure rather than the whole attempt.')
            import pandas as pd
            rows = pd.DataFrame(report['rows'])
            if 'error' in rows:
                st.line_chart(rows.set_index('elapsed')[['error']])
                st.caption('Horizontal image error over simulation seconds. Zero means centered. Positive means right of center. Gaps mean no usable centroid, not perfect centering.')
            with st.expander('Command plots and state timeline'):
                a,b = st.columns(2)
                a.line_chart(rows.set_index('elapsed')[['linear']])
                a.caption('Requested forward speed in metres per second, before the guard. Pillar search must remain at zero.')
                b.line_chart(rows.set_index('elapsed')[['angular']])
                b.caption('Requested turn rate in radians per second. Positive turns left. Compare its sign with the error above.')
                columns = [k for k in ('elapsed','frame','state','target','valid','error','linear','angular','odom_x','odom_y') if k in rows]
                st.dataframe(rows[columns],hide_index=True)
                st.caption('Each row is a controller decision. Repeated frame numbers reuse an image that is still fresh. odom_x and odom_y, when present, are wheel-based estimates rather than independent ground truth. The exported CSV retains this timeline.')
            if st.button('Keep this attempt in my submission',key=prefix+'.keep'):
                selected = [r for r in selected if r['run_id'] != report['run_id']]+[report]
                st.session_state['evidence'][kind] = {'kind':kind,'reports':selected}
                write_json(submission_root()/kind/'evidence.json',st.session_state['evidence'][kind])
                save(st)
                st.success('Attempt saved in your submission. Final export also creates its CSV and images.')
        except (ValueError,KeyError,TypeError) as error: st.info(str(error))
    if selected:
        st.table([{'attempt':r['run_id'],'world':r['world'],'outcome':r['outcome'],'gain':r['config']['gain']} for r in selected])


def pillars(st):
    st.header('Mission 2: Find and center colored pillars')
    st.write('A robot surveying an unfamiliar room needs to look toward a sequence of landmarks. Four colored pillars surround this robot. Use its live camera to find each requested color, turn until it is centered, hold the view, and continue to the next color. It must not drive forward. Your goal is to explain how image evidence produces a stable turn, not to estimate the pillar distance.')
    start_simulation(st)
    st.markdown('''### How the controller works
The camera produces BGR images. The pipeline converts a central region to HSV, thresholds the requested color, removes small specks and selects the largest remaining contour. The centroid is the balance point of that contour. A similarly colored object could still fool this rule.

Normalized error is `(target_x - region_center_x) / half_region_width`. A target to the right gives positive error. ROS positive angular velocity turns left, so the controller negates the error to turn right. This is an image-space steering cue, not a world-coordinate pose.

SEARCH rotates slowly when a fresh image contains no target. CENTER turns toward an off-center target. CONFIRM requires three distinct centered frames. HOLD keeps zero speed for the selected time. NEXT changes the color. COMPLETE stops after the sequence. Missing or stale images always stop motion, even during search.

### Predict, run and compare
1. Predict the turn direction for a blue pillar on the left of the image. Choose blue only and save settings. Use the pillar world you started above. Do not launch a duplicate.
2. Start the controller in Terminal 2. Open its mask and annotated image in Terminal 3. Watch the robot turn in Gazebo and compare the selected region with the mask. Keep these terminals focused only when typing commands.
3. Stop with Ctrl+C. Keep the attempt below. Select the four-color sequence, save and run again. Change only one setting if centering is unstable. Keep an all-four-color attempt even if it does not finish.
4. Close the image viewers and stop the world with Ctrl+C before Mission 3. Wait for Gazebo to close. Do not use teleop while the controller runs.
''')
    controls(st,'pillar_search')
    terminal(st,'Terminal 2: run pillar search','bash scripts/run_vision.sh pillar_search pillars')
    terminal(st,'Terminal 3: inspect mask and centering','bash scripts/view_vision.sh')
    st.info('Emergency stop: press Ctrl+C in the controller terminal. If that terminal is unresponsive, pause Gazebo or stop the world. The separate guard sends zero within 0.4 wall-clock seconds after controller messages stop. This safeguard is for this simulation, not a physical safety certification.')
    attempts(st,'pillar_search')
    text_response(st,'pillar_search.diagnosis','Use a named saved attempt to explain one successful centering or failure. Connect the camera image, mask, centroid error and turn direction. What did changing your setting improve or worsen?')
    text_response(st,'pillar_search.evidence','For your four-color attempt, which colors were centered and which were not? Explain what the state timeline and camera evidence show. Why do a centered colored region and a stable hold not prove object identity or distance?')
    mission_status(st,'pillar_search')


def line_editor(st):
    from perception.line_program import STARTER,load_program
    st.subheader('Edit the Python code used by the ROS controller')
    st.write('This is the controller program the ROS node loads, not a written response. Edit the numeric assignments and the return expression directly. The initial gain is intentionally weak, so it may follow a straight strip but respond too slowly to bends. Predict the effect, test it, and change one choice at a time. There is no supplied best value to copy.')
    st.caption('GAIN scales the steering correction. SPEED is the maximum forward speed in m/s. ROI_TOP and ROI_BOTTOM choose the floor strip. HUE_LOW and HUE_HIGH choose magenta pixels. MIN_FRACTION rejects tiny contours. The node still limits speed to 0.18 m/s and turn rate to 0.6 rad/s and stops on stale images or missing line evidence.')
    key = 'code.line_following'
    st.session_state.setdefault(key,st.session_state['settings'].get('line_following_program',STARTER))
    source = st.text_area('ROS line-controller Python',key=key,height=440)
    if st.button('Save ROS controller code',key='line_following.save'):
        try:
            config,_ = load_program(source)
            atomic(submission_root()/'line_following/controller.py',source)
            write_json(submission_root()/'line_following/settings.json',asdict(config))
            st.session_state['settings']['line_following_program'] = source
            st.session_state['settings']['line_following'] = asdict(config)
            save(st)
            st.success('Python saved. Stop the running controller before restarting it. The next start loads this file, and each retained attempt records its exact program.')
        except (ValueError,TypeError) as error: st.error(str(error))
    st.caption('The small editor supports numeric settings and arithmetic using error and gain. Imports, arbitrary function calls and loops are not part of this steering interface. The supplied ROS node handles image acquisition, masks, timestamps and publishing. CODE_ERROR in a timeline means that the steering expression failed and motion stopped. Inspect that attempt\'s saved program before retrying.')


def line(st):
    st.header('Mission 3: Follow a marked route with the camera')
    st.write('An indoor delivery robot follows a painted route. Your task is to keep the magenta line in the camera region centered while moving forward, then stop when the red finish panel is seen. Start on a straight practice strip before trying the curved route. The controller uses no map or lidar and does not know its physical distance from an obstacle.')
    st.image(str(ROOT/'assets/robot_worlds/track.png'),caption='Full route viewed from above. Magenta marks the route and red marks the finish.',width=450)
    st.markdown('''### From a line mask to steering
The downward-looking camera sees a strip of floor. The pipeline thresholds magenta in a region of interest, selects the largest contour and computes its centroid. The same normalized error as Mission 2 gives a proportional turn command. Forward speed decreases for large errors. Higher gain may correct a bend sooner but may also create left-right oscillation.

TRACK moves only with a fresh, valid line observation. LINE_LOST stops when no adequate contour remains. WAIT_CAMERA stops when frames are missing or stale. A red region covering the finish fraction in three distinct frames latches COMPLETE. The red marker is a supplied simulation cue, not a calibrated physical stopping distance. Practice has no finish marker, so end it with Ctrl+C.

If the line is lost, the robot deliberately stops rather than guessing a safe route. Inspect the final mask. Stop the controller and restart the world before retrying. A route completion is useful evidence, but no completion or speed threshold is required for submission.
''')
    line_editor(st)
    st.divider()
    st.subheader('Part 1: Practice on a straight strip')
    st.markdown('''1. Stop the Mission 2 controller, viewers and world. Predict the effect of the starting gain and save the Python code above.
2. In Terminal 1 launch practice. In Terminal 2 run the live check, then start the controller only if all checks pass. In Terminal 3 open the mask and annotated view.
3. Observe the selected line, error and motion. End the practice controller with Ctrl+C after a useful run. Practice has no finish panel.
4. **Before starting the track, import your practice attempt below.** Press Refresh recorded attempts, select the practice run and press Keep this attempt in my submission. Confirm that a practice row appears in the retained-attempt table. An unsuccessful attempt is acceptable evidence.''')
    terminal(st,'Terminal 1: fresh straight practice world','bash scripts/launch_vision_world.sh practice')
    terminal(st,'Terminal 2: check, then practice','bash scripts/check_vision.sh\nbash scripts/run_vision.sh line_following practice')
    terminal(st,'Terminal 3: inspect the live output','bash scripts/view_vision.sh')
    attempts(st,'line_following','practice')
    st.divider()
    st.subheader('Part 2: Experiment on the curved track')
    st.markdown('''1. Confirm that you kept a practice attempt. Stop the controller, viewers and practice world. These are separate worlds, not two controllers running together.
2. Launch the track in Terminal 1. Repeat the live check and start the track controller in Terminal 2. Run the image viewers in Terminal 3 again.
3. Test the saved starting program on the bends. If correction is weak, think about the gain and steering expression. If it oscillates, think about gain, speed and look-ahead region. Inspect the mask before blaming the controller.
4. Stop all three terminals before each reset. Edit one choice in the Python code above, save, relaunch the track and rerun for a comparable starting pose. Keep at least two track attempts with different programs so you can compare what changed. No particular gain or perfect completion is required.
5. Import your track attempts below just as you did for practice. Use their recorded programs, error plots and state timelines to answer the questions.''')
    terminal(st,'Terminal 1: fresh curved route','bash scripts/launch_vision_world.sh track')
    terminal(st,'Terminal 2: check, then curved route','bash scripts/check_vision.sh\nbash scripts/run_vision.sh line_following track')
    terminal(st,'Terminal 3: reopen the mask and annotated view','bash scripts/view_vision.sh')
    attempts(st,'line_following','track')
    text_response(st,'line_following.comparison','Compare your saved practice and track attempts. Identify the settings and an observed straight or curved segment. Use the mask, error and commands to explain stable tracking, oscillation or line loss. If you changed a setting, what evidence supports its effect?')
    text_response(st,'line_following.limits','Describe one stop or failure from your attempts and whether it began in the image processing, control or missing information. What additional sensing and tests would be needed for a real delivery robot around people?')
    mission_status(st,'line_following')
