"""Actual camera-in-the-loop pillar search and floor-route following."""
import base64
import json
import math
import time
import uuid
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
import cv2
import rclpy
from rclpy.node import Node
from rclpy.clock import Clock, ClockType
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from perception.dataset import ROOT
from perception.vision_control import VisionSettings, VisionController, observe, VERSION


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,allow_nan=False),encoding='utf-8')
    tmp.replace(path)


class LiveVision(Node):
    def __init__(self):
        super().__init__('lab7_live_vision')
        kind = self.declare_parameter('kind','pillar_search').value
        world = self.declare_parameter('world','pillars').value
        self.world = str(world)
        settings_file = str(self.declare_parameter('settings_file','').value)
        defaults = asdict(VisionSettings(kind=kind))
        if settings_file and Path(settings_file).is_file():
            defaults.update(json.loads(Path(settings_file).read_text()))
        defaults['kind'] = kind
        self.config = VisionSettings(**defaults)
        self.program = ''
        steering = None
        if kind == 'line_following':
            from perception.line_program import STARTER,load_program
            program_path = Path(settings_file).parent/'controller.py' if settings_file else None
            self.program = program_path.read_text(encoding='utf-8') if program_path and program_path.is_file() else STARTER
            self.config,steering = load_program(self.program)
        if self.world not in (('pillars',) if kind == 'pillar_search' else ('practice','track')):
            raise ValueError('Controller and world do not match')
        self.controller = VisionController(self.config,steering)
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Twist,'/lab7/request_cmd',10)
        self.status = self.create_publisher(String,'/lab7/vision_state',10)
        self.images = {name:self.create_publisher(Image,'/lab7/'+name,2) for name in ('original','mask','annotated')}
        self.frame = 0
        self.observation = None
        self.arrived = 0.
        self.capture_stamp = 0.
        self.latest_images = {}
        self.robot_position = {}
        self.start_sim = None
        self.start_wall = time.monotonic()
        self.rows = []
        self.outcome = 'running'
        self.max_seconds = float(self.declare_parameter('max_seconds',300.).value)
        if not math.isfinite(self.max_seconds) or not 1 <= self.max_seconds <= 1800:
            raise ValueError('Maximum attempt duration must be from 1 to 1800 simulation seconds')
        self.run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
        self.directory = ROOT/'runtime/robot_runs'/kind/self.run_id
        active = ROOT/'runtime/worlds/active.json'
        self.world_run = json.loads(active.read_text()) if active.exists() else {}
        if self.world_run.get('mode') != self.world: raise ValueError('Start the matching world before this controller')
        self.create_subscription(Image,'/camera/image_raw',self.camera,qos_profile_sensor_data)
        self.create_subscription(Odometry,'/odom',self.odometry,qos_profile_sensor_data)
        self.create_timer(.1,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.get_logger().info('Waiting for live camera frames. Evidence: '+str(self.directory))

    def camera(self, msg):
        try:
            image = self.bridge.imgmsg_to_cv2(msg,'bgr8')
            image = cv2.resize(image,(480,270))
            target = self.controller.target if self.config.kind == 'pillar_search' else 'magenta'
            observation, images = observe(image,self.config,target)
        except Exception as error:
            self.observation = None
            self.get_logger().error('Frame rejected, stopping: '+str(error))
            self.command()
            return
        self.frame += 1
        self.observation = observation
        self.arrived = time.monotonic()
        self.capture_stamp = msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
        self.latest_images = images
        for name, image in images.items():
            out = self.bridge.cv2_to_imgmsg(image,'mono8' if image.ndim == 2 else 'bgr8')
            out.header = msg.header
            self.images[name].publish(out)

    def command(self, linear=0., angular=0.):
        cmd = Twist()
        cmd.linear.x,cmd.angular.z = float(linear),float(angular)
        self.publisher.publish(cmd)

    def odometry(self,msg):
        point = msg.pose.pose.position
        self.robot_position = {'odom_x':point.x,'odom_y':point.y}

    def tick(self):
        active = ROOT/'runtime/worlds/active.json'
        if active.exists() and json.loads(active.read_text()).get('run_id') != self.world_run.get('run_id'):
            self.command()
            self.outcome = 'interrupted'
            self.save()
            raise AttemptFinished()
        now = self.get_clock().now().nanoseconds/1e9
        if self.start_sim is None and self.frame: self.start_sim = now
        elapsed = max(0.,now-self.start_sim) if self.start_sim is not None else 0.
        age = now-self.capture_stamp
        fresh = self.frame > 0 and time.monotonic()-self.arrived <= 1.0 and 0 <= age <= self.config.max_age
        result = self.controller.step(self.observation, now, self.frame, fresh)
        if elapsed >= self.max_seconds or time.monotonic()-self.start_wall > max(60., self.max_seconds*5) or len(self.rows) >= 20000:
            self.outcome = 'timeout'
            result.update(state='TIMEOUT',linear=0.,angular=0.)
        if self.controller.done: self.outcome = 'complete'
        if self.outcome != 'running': result.update(linear=0.,angular=0.)
        self.command(result['linear'],result['angular'])
        row = {'elapsed':elapsed,'frame':self.frame,'capture_stamp':self.capture_stamp,
               **(self.observation or {}),**self.robot_position,**result}
        self.rows.append(row)
        status = String()
        status.data = json.dumps({'state':result['state'],'target':self.controller.target,'visited':self.controller.visited})
        self.status.publish(status)
        if len(self.rows)%20 == 0 or self.outcome != 'running': self.save()
        if self.outcome != 'running':
            self.get_logger().info('Attempt '+self.outcome+'. Stopped and saved '+str(self.directory))
            raise AttemptFinished()

    def save(self):
        images = {}
        for name,image in self.latest_images.items():
            ok, data = cv2.imencode('.png',image)
            if ok: images[name] = base64.b64encode(data.tobytes()).decode()
        self.report = {'schema':VERSION,'run_id':self.run_id,'kind':self.config.kind,'world':self.world,
                       'world_run':self.world_run,'config':asdict(self.config),'outcome':self.outcome,
                       'visited':list(self.controller.visited),'rows':self.rows,'images':images,'program':self.program}
        atomic_json(self.directory/'run.json',self.report)


class AttemptFinished(Exception): pass


def main():
    from rclpy.signals import SignalHandlerOptions
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = None
    try:
        node = LiveVision()
        rclpy.spin(node)
    except (KeyboardInterrupt, AttemptFinished): pass
    finally:
        if node:
            node.command()
            if node.outcome == 'running': node.outcome = 'interrupted'
            node.save()
            node.destroy_node()
        rclpy.try_shutdown()
