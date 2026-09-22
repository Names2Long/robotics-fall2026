"""One bounded trial. Called by the guide inside the course container."""
from __future__ import annotations
import json
import math
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation.kinematics import SEQUENCES, integrate_sequence, pose_error


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    name, trial_id, prediction_id, destination = sys.argv[1:]
    segments = SEQUENCES[name]
    rclpy.init()
    node = Node("mission1_motion_trial")
    pub = node.create_publisher(Twist, "/student_cmd_vel", 10)
    readings = []
    def receive(msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        readings.append((time.monotonic(), {"x": p.x, "y": p.y,
            "theta": math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))},
            abs(msg.twist.twist.linear.x), abs(msg.twist.twist.angular.z)))
    node.create_subscription(Odometry, "/odom", receive, qos_profile_sensor_data)
    def pump(seconds, v=0., w=0.):
        end = time.monotonic()+seconds
        while time.monotonic() < end and rclpy.ok():
            msg = Twist(); msg.linear.x = float(v); msg.angular.z = float(w)
            pub.publish(msg)
            rclpy.spin_once(node, timeout_sec=.02)
            time.sleep(.02)
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        print("Waiting for the command guard and odometry", flush=True)
        deadline = time.monotonic()+10
        while time.monotonic()<deadline and (not readings or pub.get_subscription_count()==0):
            pump(.1)
        if not readings or pub.get_subscription_count()==0:
            raise RuntimeError("No fresh odometry or command subscriber. Start the simulator and course guard.")
        pump(.5)
        print("Returning the robot to its starting position", flush=True)
        reset_ok = False
        for suffix in ("set_pose/blocking", "set_pose"):
            try:
                result = subprocess.run(["gz", "service", "-s", f"/world/default/{suffix}",
                    "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean", "--timeout", "5000",
                    "--req", 'name: "burger", position: {x: -2.0, y: -0.5, z: 0.01}, orientation: {w: 1.0}'],
                    capture_output=True, text=True, timeout=7)
                if result.returncode==0 and "data: true" in result.stdout:
                    reset_ok = True
                    break
            except subprocess.TimeoutExpired:
                pass
        if not reset_ok:
            raise RuntimeError("Gazebo could not reset the robot. Restart the simulator or use modeled evidence.")
        readings.clear()
        pump(1)
        if not readings or time.monotonic()-readings[-1][0]>.5:
            raise RuntimeError("Odometry did not resume after reset.")
        start = dict(readings[-1][1]); readings.clear()
        started = time.monotonic()
        print("Running the motion sequence", flush=True)
        for segment in segments:
            pump(segment.duration, segment.linear_x, segment.angular_z)
            if not readings or time.monotonic()-readings[-1][0]>.5:
                raise RuntimeError("Odometry became stale during motion.")
            pump(.25)  # explicit stop between stages
        motion_end = time.monotonic()
        stop_start = time.monotonic()
        pump(.6)
        stopped = readings and readings[-1][0]>=stop_start and readings[-1][2]<.02 and readings[-1][3]<.05
        if not stopped:
            raise RuntimeError("The final stop could not be confirmed in fresh odometry.")
        def relative(p):
            dx, dy = p["x"]-start["x"], p["y"]-start["y"]
            c, s = math.cos(start["theta"]), math.sin(start["theta"])
            angle = p["theta"]-start["theta"]
            return {"x": c*dx+s*dy, "y": -s*dx+c*dy, "theta": math.atan2(math.sin(angle), math.cos(angle))}
        end = readings[-1][1]; observed = relative(end)
        if name == "straight" and observed["x"] < .05:
            raise RuntimeError("No meaningful forward motion was observed. Check the command bridge or use modeled evidence.")
        if name != "straight" and observed["theta"] < .15:
            raise RuntimeError("No meaningful left turn was observed. Check the command bridge or use modeled evidence.")
        samples = [[0.,0.,0.]] + [list(relative(p).values()) for _,p,_,_ in readings]
        payload = {"sequence_id":name,"trial_id":trial_id,"prediction_id":prediction_id,
            "captured_at":datetime.now(timezone.utc).isoformat(),"source":"live","completed":True,
            "stop_sent":True,"stop_observed":True,"live_verified":True,"reset_acknowledged":True,
            "measurement_frame":"odom","start_pose":start,"end_pose":end,"observed_pose":observed,
            "predicted_pose":integrate_sequence(segments),"samples":samples,
            "duration":motion_end-started, **pose_error(integrate_sequence(segments),observed)}
        target = Path(destination); temp=target.with_suffix(".tmp")
        temp.write_text(json.dumps(payload,indent=2),encoding="utf-8"); temp.replace(target)
        print("Motion and stop evidence saved",flush=True)
    finally:
        if rclpy.ok():
            pump(.3)
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
