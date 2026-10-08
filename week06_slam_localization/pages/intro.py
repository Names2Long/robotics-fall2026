def render(st):
    st.title("Week 6: SLAM and Mapping")
    st.markdown("In this individual lab, you will use ROS 2 packages to build and evaluate occupancy-grid maps. You will not implement SLAM from scratch. You will compare two exploration routes in the same TurtleBot3 House world.")
    st.info("This is individual work. Your maps, observations, explanations, and submission artifacts must come from your own runs.")
    st.subheader("Learning objectives")
    st.markdown("- Explain how LiDAR, odometry, pose estimates, and an occupancy grid interact.\n- Build and save a map using SLAM.\n- Compare exploration strategies using quantitative and visual evidence.\n- Identify map limitations, uncertain regions, and possible effects of motion error.")
    st.subheader("The route through this lab")
    st.write("Three guided tutorials prepare you for two mapping runs. Save a route prediction before each run, then compare it with visual and measured evidence. You can revisit earlier pages from Lab navigation.")
    student = dict(st.session_state["student"])
    for key, label in (("name", "Full name"), ("email", "Hunter email")):
        widget = "student." + key
        if widget not in st.session_state: st.session_state[widget] = student.get(key, "")
        student[key] = st.text_input(label, key=widget)
    st.caption("These fields identify your individual submission. They do not sign you up for email or advertisements.")
    st.session_state["student"] = student
    st.write("The guided tutorials are for exploration and explanation. They do not require written answers. Mission predictions and analyses are saved as you work.")
