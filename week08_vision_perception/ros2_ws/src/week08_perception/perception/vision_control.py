"""Live camera processing and policies, shared with tests and independent of ROS."""
from dataclasses import dataclass, asdict
import math
import cv2
import numpy as np

VERSION = 'live-vision-v1'
COLORS = {'red': [((0,100,45),(12,255,255)), ((170,100,45),(179,255,255))],
          'green': [((38,90,40),(85,255,255))],
          'turquoise': [((80,90,40),(102,255,255))],
          'blue': [((103,90,40),(137,255,255))],
          'magenta': [((140,90,40),(169,255,255))]}


@dataclass(frozen=True)
class VisionSettings:
    kind: str = 'pillar_search'
    colors: str = 'red,green,turquoise,blue'
    gain: float = 1.2
    speed: float = .16
    search_speed: float = .35
    tolerance: float = .10
    hold_seconds: float = .7
    min_fraction: float = .002
    roi_top: float = .60
    roi_bottom: float = .95
    hue_low: int = 140
    hue_high: int = 169
    saturation_low: int = 90
    value_low: int = 40
    max_age: float = .7
    finish_fraction: float = .10

    def __post_init__(self):
        if self.kind not in ('pillar_search','line_following'): raise ValueError('Unknown mission')
        targets = self.colors.split(',')
        if not targets or any(c not in ('red','green','blue','turquoise') for c in targets) or len(set(targets)) != len(targets):
            raise ValueError('Choose distinct pillar colors, separated by commas without spaces')
        numbers = (self.gain,self.speed,self.search_speed,self.tolerance,self.hold_seconds,self.min_fraction,self.roi_top,self.roi_bottom,self.max_age,self.finish_fraction)
        if not all(math.isfinite(v) for v in numbers): raise ValueError('Settings must be finite')
        if not (.05 <= self.gain <= 4 and 0 < self.speed <= .18 and 0 < self.search_speed <= .6): raise ValueError('Gain or speed outside safe range')
        if not (0 < self.tolerance <= .4 and .2 <= self.hold_seconds <= 5 and 0 < self.min_fraction < .2): raise ValueError('Invalid centering or area settings')
        if not (0 <= self.roi_top < self.roi_bottom <= 1 and self.roi_bottom-self.roi_top >= .05): raise ValueError('ROI must have positive height')
        if not (0 <= self.hue_low <= self.hue_high <= 179 and 0 <= self.saturation_low <= 255 and 0 <= self.value_low <= 255): raise ValueError('Invalid HSV bounds')
        if not (.1 <= self.max_age <= 2 and .01 <= self.finish_fraction <= .5): raise ValueError('Invalid freshness or finish setting')


def mask_for(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for low, high in ranges:
        mask |= cv2.inRange(hsv, np.array(low), np.array(high))
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))


def observe(image, config, target='blue'):
    if image is None or image.ndim != 3 or image.shape[2] != 3: raise ValueError('Expected a BGR camera image')
    h, w = image.shape[:2]
    if config.kind == 'pillar_search':
        x0,x1,y0,y1 = round(.05*w),round(.95*w),round(.12*h),round(.88*h)
        ranges = COLORS[target]
    else:
        x0,x1,y0,y1 = 0,w,round(config.roi_top*h),round(config.roi_bottom*h)
        ranges = [((config.hue_low,config.saturation_low,config.value_low),(config.hue_high,255,255))]
    crop = image[y0:y1,x0:x1].copy()
    if not crop.size: raise ValueError('Empty image region')
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = mask_for(hsv, ranges)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidate = max(contours, key=cv2.contourArea) if contours else None
    fraction = cv2.contourArea(candidate)/mask.size if candidate is not None else 0.
    valid = fraction >= config.min_fraction
    cx = cy = error = None
    annotated = image.copy()
    cv2.rectangle(annotated,(x0,y0),(x1-1,y1-1),(255,200,0),1)
    cv2.line(annotated,((x0+x1)//2,y0),((x0+x1)//2,y1),(255,0,255),1)
    if valid:
        moments = cv2.moments(candidate)
        if moments['m00'] <= 0: valid = False
        else:
            cx,cy = moments['m10']/moments['m00'],moments['m01']/moments['m00']
            error = (cx-crop.shape[1]/2)/(crop.shape[1]/2)
            cv2.circle(annotated,(round(cx+x0),round(cy+y0)),5,(0,255,255),2)
    red_fraction = float(np.count_nonzero(mask_for(hsv, COLORS['red']))/mask.size) if config.kind == 'line_following' else 0.
    observation = {'valid': bool(valid), 'error': float(error) if error is not None else None,
                   'fraction': float(fraction), 'finish': red_fraction >= config.finish_fraction,
                   'red_fraction': red_fraction, 'target': target,
                   'roi': [x0,y0,x1-x0,y1-y0], 'centroid_roi': [cx,cy] if valid else None}
    return observation, {'original':image.copy(), 'mask':mask, 'annotated':annotated}


class VisionController:
    def __init__(self, config, steering=None):
        self.config = config
        self.steering = steering or (lambda error,gain:-gain*error)
        self.targets = config.colors.split(',')
        self.visited = []
        self.state = 'WAIT_CAMERA'
        self.centered_frames = self.finish_frames = 0
        self.last_frame = None
        self.hold_since = None
        self.done = False

    @property
    def target(self):
        return self.targets[min(len(self.visited),len(self.targets)-1)]

    def step(self, observation, now, frame_id, fresh=True):
        linear = angular = 0.
        if self.done: self.state = 'COMPLETE'
        elif not fresh or observation is None:
            self.state = 'WAIT_CAMERA'
            self.centered_frames = self.finish_frames = 0
            self.hold_since = None
        elif self.config.kind == 'pillar_search':
            if observation['target'] != self.target:
                self.state = 'WAIT_TARGET_FRAME'
            elif not observation['valid']:
                self.state = 'SEARCH'
                angular = self.config.search_speed
                self.centered_frames = 0
                self.hold_since = None
            else:
                error = observation['error']
                if not isinstance(error,(int,float)) or not math.isfinite(error):
                    self.state = 'INVALID'
                    return {'state':self.state,'linear':0.,'angular':0.}
                if abs(error) > self.config.tolerance:
                    self.state = 'CENTER'
                    angular = max(-.45,min(.45,-self.config.gain*error))
                    self.centered_frames = 0
                    self.hold_since = None
                else:
                    if frame_id != self.last_frame: self.centered_frames += 1
                    self.state = 'CONFIRM'
                    if self.centered_frames >= 3:
                        self.state = 'HOLD'
                        if self.hold_since is None: self.hold_since = now
                        if now-self.hold_since >= self.config.hold_seconds:
                            self.visited.append(self.target)
                            self.centered_frames = 0
                            self.hold_since = None
                            self.done = len(self.visited) == len(self.targets)
                            self.state = 'COMPLETE' if self.done else 'NEXT'
        else:
            if frame_id != self.last_frame:
                self.finish_frames = self.finish_frames+1 if observation['finish'] else 0
            if self.finish_frames >= 3:
                self.done = True
                self.state = 'COMPLETE'
            elif observation['valid'] and isinstance(observation['error'],(float,int)) and math.isfinite(observation['error']):
                error = observation['error']
                self.state = 'TRACK'
                try:
                    requested = self.steering(error,self.config.gain)
                    if not isinstance(requested,(int,float)) or not math.isfinite(requested): raise ValueError('Invalid steering result')
                    angular = max(-.6,min(.6,requested))
                    linear = self.config.speed*max(.25,1-.7*abs(error))
                except (ArithmeticError,TypeError,ValueError,OverflowError):
                    self.state = 'CODE_ERROR'
                    linear = angular = 0.
            else: self.state = 'LINE_LOST'
        self.last_frame = frame_id
        return {'state':self.state,'linear':float(linear),'angular':float(angular)}


def bounded_command(linear, angular):
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (linear,angular)): return 0.,0.
    return max(-.18,min(.18,linear)),max(-.6,min(.6,angular))
