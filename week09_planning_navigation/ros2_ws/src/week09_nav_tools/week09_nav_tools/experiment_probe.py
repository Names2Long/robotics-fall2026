"""Bounded ComputePathToPose + common FollowPath experiment recorder."""
import json
import math
from pathlib import Path
import time
import yaml
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav_msgs.msg import Path as PathMessage, Odometry
from nav2_msgs.action import ComputePathToPose, FollowPath
from sensor_msgs.msg import LaserScan
from lifecycle_msgs.srv import GetState
from tf2_ros import Buffer, TransformListener, TransformException
from planning.core import cell_to_world, GOAL, fingerprint, path_length, densify, distance_to_path, obstacle_clearance, make_map, TRIAL_TIMEOUT
from planning.social import trajectory_metrics, refine


class Probe(Node):
    def __init__(self):
        super().__init__('lab8_experiment_probe')
        self.declare_parameter('request','')
        self.declare_parameter('output','')
        self.request = json.loads(Path(self.get_parameter('request').value).read_text())
        self.output = Path(self.get_parameter('output').value)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer,self)
        self.samples = []
        self.scan_min = math.inf
        self.last_scan_wall = 0.0
        self.tf_wall = 0.0
        self.speed = 0.0
        self.create_subscription(Odometry,'/odom',self.odometry,10)
        self.create_subscription(LaserScan,'/scan',self.scan,10)
        self.create_timer(.1,self.sample)
        self.stop_pub = self.create_publisher(TwistStamped,'/cmd_vel',10)
        self.path_pub = self.create_publisher(PathMessage,'/lab8/planned_path',10)

    def scan(self,msg):
        values = [v for v in msg.ranges if math.isfinite(v) and msg.range_min <= v <= msg.range_max]
        if values:
            self.scan_min = min(self.scan_min,min(values))
            self.last_scan_wall = time.monotonic()

    def odometry(self,msg):
        self.speed = math.hypot(msg.twist.twist.linear.x,msg.twist.twist.linear.y)

    def sample(self):
        try:
            tf = self.buffer.lookup_transform('map','base_footprint',rclpy.time.Time())
            p = tf.transform.translation
            self.tf_wall = time.monotonic()
            self.samples.append(dict(t=self.get_clock().now().nanoseconds/1e9,x=p.x,y=p.y,speed_mps=self.speed))
        except TransformException:
            pass

    def wait(self,future,seconds):
        deadline = time.monotonic()+seconds
        while rclpy.ok() and not future.done() and time.monotonic()<deadline:
            rclpy.spin_once(self,timeout_sec=.1)
        if not future.done():
            raise TimeoutError('Action response deadline exceeded')
        return future.result()

    def pose(self,x,y,yaw=0):
        p = PoseStamped()
        p.header.frame_id = 'map'
        p.header.stamp = self.get_clock().now().to_msg()
        p.pose.position.x,p.pose.position.y = float(x),float(y)
        p.pose.orientation.z,p.pose.orientation.w = math.sin(yaw/2),math.cos(yaw/2)
        return p

    def wait_active(self,name):
        self.progress(f'Waiting for {name} lifecycle activation')
        client = self.create_client(GetState,f'/{name}/get_state')
        if not client.wait_for_service(timeout_sec=30):
            raise RuntimeError(f'{name} lifecycle service is unavailable')
        deadline = time.monotonic()+60
        while time.monotonic()<deadline:
            response = self.wait(client.call_async(GetState.Request()),5)
            if response.current_state.id == 3:
                return
            # Spin while the lifecycle manager finishes startup.
            until = time.monotonic()+.5
            while time.monotonic()<until:
                rclpy.spin_once(self,timeout_sec=.1)
        raise RuntimeError(f'{name} did not become active. Inspect launch.log.')

    def progress(self,message):
        self.get_logger().info(message)
        path = self.output.parent/'progress.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'message':message,'wall_time':time.time()}))
        temporary.replace(path)

    def execute(self):
        req = self.request
        row = dict(req,kind='social' if req.get('people') else 'navigation',trajectory=[],status='environment_error')
        row.pop('grid',None)
        try:
            self.progress('Waiting for Nav2 planning and path-following actions')
            compute = ActionClient(self,ComputePathToPose,'/compute_path_to_pose')
            follow = ActionClient(self,FollowPath,'/follow_path')
            if not compute.wait_for_server(timeout_sec=75) or not follow.wait_for_server(timeout_sec=30):
                raise RuntimeError('Nav2 actions are unavailable. Inspect launch.log before counting this as a planner outcome.')
            deadline = time.monotonic()+30
            self.progress('Waiting for map-frame robot position and lidar')
            while time.monotonic()<deadline and (not self.samples or not self.last_scan_wall):
                rclpy.spin_once(self,timeout_sec=.1)
            if not self.samples or not self.last_scan_wall:
                raise RuntimeError('No map-frame pose or lidar scan')
            self.wait_active('planner_server')
            self.wait_active('controller_server')
            self.wait_active('velocity_smoother')
            self.wait_active('collision_monitor')
            self.progress('Nav2 ready. Preparing the requested path')
            config_file = self.output.parent/'nav2.yaml'
            params = yaml.safe_load(config_file.read_text())['controller_server']['ros__parameters']
            row['controller_config'] = params
            row['controller_hash'] = fingerprint(params)
            points = req.get('path',[])
            if req['planner'] == 'nav2':
                goal = ComputePathToPose.Goal()
                goal.goal = self.pose(*cell_to_world(GOAL))
                goal.planner_id = 'GridBased'
                began = time.monotonic()
                handle = self.wait(compute.send_goal_async(goal),15)
                if not handle.accepted:
                    raise RuntimeError('Nav2 rejected planning request')
                result = self.wait(handle.get_result_async(),30)
                row['planning_roundtrip_s'] = time.monotonic()-began
                duration = result.result.planning_time
                row['planning_s'] = duration.sec+duration.nanosec/1e9
                row['planner_error_code'] = int(result.result.error_code)
                points = [(p.pose.position.x,p.pose.position.y) for p in result.result.path.poses]
                if result.status != 4 or len(points)<2:
                    row['status'] = 'planning_failed'
                    row['error'] = getattr(result.result,'error_msg','') or f"Nav2 planning error {row['planner_error_code']}"
                    return row
            if len(points)<2:
                row['status'] = req.get('planning_status','planning_failed')
                return row
            if req.get('people') and req['condition'] != 'baseline':
                self.progress('Computing the human-aware potential-field path')
                points,field_status = refine(points,req['grid'],req['people'],req['field_config'])
                row['field_status'] = field_status
                if not points:
                    row['status'] = 'field_'+field_status
                    return row
            row['path'] = points
            row['planned_length_m'] = path_length(points)
            points = densify(points)
            message = PathMessage()
            message.header.frame_id = 'map'
            message.header.stamp = self.get_clock().now().to_msg()
            for i,p in enumerate(points):
                a,b = (p,points[i+1]) if i<len(points)-1 else (points[i-1],p)
                message.poses.append(self.pose(*p,math.atan2(b[1]-a[1],b[0]-a[0])))
            self.path_pub.publish(message)
            goal = FollowPath.Goal()
            goal.path,goal.controller_id,goal.goal_checker_id = message,'FollowPath','goal_checker'
            self.samples.clear()
            self.scan_min = math.inf
            handle = self.wait(follow.send_goal_async(goal),15)
            if not handle.accepted:
                row['status'] = 'controller_rejected'
                return row
            result = handle.get_result_async()
            began = time.monotonic()
            sim_start = self.get_clock().now().nanoseconds/1e9
            deadline = began+req.get('timeout_s',TRIAL_TIMEOUT)*3
            last_report = 0
            forced_status = None
            while not result.done() and time.monotonic()<deadline:
                rclpy.spin_once(self,timeout_sec=.1)
                elapsed = self.get_clock().now().nanoseconds/1e9-sim_start
                if time.monotonic()-last_report>=5:
                    gap = f"{math.dist((self.samples[-1]['x'],self.samples[-1]['y']),cell_to_world(GOAL)):.2f} m" if self.samples else 'awaiting first execution checkpoint'
                    self.progress(f'Following path: {elapsed:.0f} simulated seconds, estimated goal distance {gap}')
                    last_report = time.monotonic()
                if time.monotonic()-self.last_scan_wall>3 or time.monotonic()-self.tf_wall>3:
                    forced_status = 'environment_error'
                    break
                if self.scan_min < .10:
                    forced_status = 'scan_proximity_stop'
                    break
                if elapsed>req.get('timeout_s',TRIAL_TIMEOUT):
                    forced_status = 'timeout'
                    break
            if not result.done():
                self.wait(handle.cancel_goal_async(),5)
                row['status'] = forced_status or 'wall_timeout'
            else:
                answer = result.result()
                row['status'] = 'succeeded' if answer.status == 4 else 'controller_failed'
                row['controller_error_code'] = int(answer.result.error_code)
                if answer.status != 4:
                    row['error'] = getattr(answer.result,'error_msg','') or f"Nav2 controller error {row['controller_error_code']}"
            row['trajectory'] = self.samples
            row.update(trajectory_metrics(self.samples,req.get('people',())))
            row['minimum_lidar_range_m'] = self.scan_min if math.isfinite(self.scan_min) else None
            if self.samples:
                end = self.samples[-1]
                row['goal_error_m'] = math.dist((end['x'],end['y']),cell_to_world(GOAL))
                row['mean_tracking_error_m'] = sum(distance_to_path((s['x'],s['y']),points) for s in self.samples)/len(self.samples)
                raw_map = make_map(req['map'])
                row['minimum_static_clearance_m'] = min(obstacle_clearance((s['x'],s['y']),raw_map) for s in self.samples)
                if row['status']=='succeeded' and row['goal_error_m']>.4:
                    row['status'] = 'goal_error_exceeded'
            row['pose_source'] = 'AMCL map-frame estimate, not simulation ground truth. Speed uses odometry twist.'
            row['collision_measure'] = 'lidar proximity proxy, not physical contact detection'
        except Exception as exc:
            row['status'],row['error'] = 'environment_error',f'{type(exc).__name__}: {exc}'
        finally:
            self.progress('Finishing trial: '+row['status'])
            for _ in range(3):
                msg = TwistStamped()
                msg.header.stamp = self.get_clock().now().to_msg()
                self.stop_pub.publish(msg)
                rclpy.spin_once(self,timeout_sec=.05)
            self.output.parent.mkdir(parents=True,exist_ok=True)
            self.output.write_text(json.dumps(row,indent=2),encoding='utf-8')
        return row


def main():
    rclpy.init()
    node = Probe()
    try:
        result = node.execute()
        print(json.dumps({'status':result['status'],'output':str(node.output)}))
    finally:
        node.destroy_node()
        rclpy.shutdown()
