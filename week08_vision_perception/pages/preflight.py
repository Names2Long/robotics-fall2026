from lab.preflight import is_current, run_checks


def render(st):
    st.header('Preflight: check software, images and saving')
    st.write('Before starting, check that the guide can read the images, run all three vision models and save your work. In the course ROS 2 environment, this also checks the ROS packages, Gazebo integration, camera robot model and built Lab 7 workspace. Gazebo does not need to be running yet.')
    st.markdown('''### Prepare the robot software once
Use the course virtual desktop for the complete lab. If you have just updated Lab 7, open a terminal inside that desktop and build the workspace before running preflight. Wait for all three packages to finish. These commands build software only, they do not launch a robot.''')
    st.code('cd /workspace/week08_vision_perception\nsource /opt/ros/jazzy/setup.bash\ncd ros2_ws\ncolcon build --symlink-install',language='bash')
    st.markdown('''1. Press **Run preflight now**. The first run also prepares the model predictions for the image collection, so it can take longer than later page changes.
2. Read the results. Continue when all required checks pass. Resolve any ROS software failures before starting Mission 2.
3. If a check fails, follow its message. Start the guide with this lab\'s launcher if packages are missing. For a missing asset or saving error, send the exact failed-check message to your instructor. Preserve your submission folder before updating files.''')
    st.caption('Software being installed does not prove that the simulation is working. Mission 2 starts Gazebo and checks live camera frames, simulation time and the command guard. Mission 3 repeats the live check after each world reset.')
    if st.button('Run preflight now', key='preflight.run', type='primary'):
        with st.spinner('Checking images, model execution and saving. Preparing reusable predictions on the first run.'):
            st.session_state['settings']['preflight_report'] = run_checks()
    report = st.session_state['settings'].get('preflight_report')
    if is_current(report):
        st.success('Software and image checks passed. Continue to the playground.' if report.get('robot_software_ready') else 'Image activities ready. Robot software is not verified in this local guide.')
        if not report.get('robot_software_ready'):
            st.warning('Before Mission 2, open this guide in the course ROS 2 environment and rerun preflight there. Do not interpret the local image checks as robot readiness.')
    elif report:
        from lab.preflight import RUN_ID
        if report.get('run_id') != RUN_ID:
            st.info('This report is from an earlier server launch. Run the check again for this launch.')
        else:
            st.error('Resolve the failed checks below before continuing.')
    else:
        st.info('Run the check before continuing.')
    if report:
        st.dataframe(report.get('checks', []), hide_index=True, width='stretch')
