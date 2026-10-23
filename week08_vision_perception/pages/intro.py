from lab.ui import changed


def render(st):
    st.title("Lab 7: Computer Vision and Learned Perception")
    st.caption("Week 8 • Individual lab • Three missions")
    st.info("A detection is evidence about what may be in an image. Reliable robot behavior depends on how that evidence was produced, how well it generalizes, and how it is used.")
    st.markdown("An assistive robot needs to locate a mug among desk equipment. Explore image operations, configure a classical color detector, inspect learned models, and compare their outputs on the same test images. You will recommend which detector deserves further testing, not claim that the robot can already grasp safely.")
    st.table([{"Part": "Preflight", "You will": "Check image operations, saving, installed ROS software and the built workspace"},
              {"Part": "Playground", "You will": "Run one image-processing step at a time with controls beside the code"},
              {"Part": "Investigation A", "You will": "Configure a classical detector and diagnose failures"},
              {"Part": "Investigation B", "You will": "Explore classification, detection and foreground segmentation"},
              {"Part": "Investigation C", "You will": "Compare the same scenes side by side and justify a recommendation"},
              {"Part": "Mission 2", "You will": "Use live camera masks to search for and center four pillars"},
              {"Part": "Mission 3", "You will": "Tune proportional steering on straight and curved floor routes"},
              {"Part": "Finish", "You will": "Explain deployment limits and write the course reflection"}])
    st.markdown("The playground and Mission 1 run in this guide. Missions 2 and 3 use ROS 2 Jazzy and Gazebo inside the course virtual desktop. Models, images and track artwork are bundled. No personal camera, physical robot, GPU or model training is required. Keep this guide open while using the desktop terminals.")
    for key, label in (("name", "Name"), ("email", "Student ID or email")):
        widget = "student."+key
        if widget not in st.session_state: st.session_state[widget] = st.session_state["student"].get(key, "")
        st.text_input(label, key=widget, on_change=changed, args=(st,))
    st.caption("You can explore before entering identity. It is required only for the final submission. Draft backups are always available in the sidebar.")
    from pages.guidance import intro
    intro(st)
