"""One policy for the guide's time sequences and the ROS behavior node."""
from dataclasses import asdict, dataclass
import math
from perception.student_code import expression

DEFAULT_RULE = "('APPROACH' if confirmed else 'STOP') if usable else loss_action"


def transition(rule, usable, confirmed, centered, loss_action):
    value = expression(rule, {"usable":usable,"confirmed":confirmed,"centered":centered,"loss_action":loss_action})
    if value not in ("STOP","SEARCH","APPROACH"): raise ValueError("Transition expression must return STOP, SEARCH or APPROACH")
    return value


@dataclass(frozen=True)
class BehaviorConfig:
    min_confidence: float = .6
    center_deadband: float = .10
    stop_area: float = .22
    stale_after: float = .6
    search_angular: float = .25
    approach_linear: float = .10
    center_gain: float = .7
    confirmation_frames: int = 3
    max_center_jump: float = .35
    loss_action: str = "STOP"
    transition_rule: str = DEFAULT_RULE

    def __post_init__(self):
        for usable in (False,True):
            for confirmed in (False,True):
                for centered in (False,True): transition(self.transition_rule,usable,confirmed,centered,self.loss_action)
        numbers = [v for v in asdict(self).values() if isinstance(v, (float, int))]
        if not all(math.isfinite(v) for v in numbers):
            raise ValueError("Policy settings must be finite")
        if not (.05 <= self.min_confidence <= 1 and .01 <= self.center_deadband <= .5 and
                .01 <= self.stop_area <= .9 and .05 <= self.stale_after <= 2 and
                0 <= self.search_angular <= .6 and 0 <= self.approach_linear <= .12 and
                0 <= self.center_gain <= 2 and type(self.confirmation_frames) is int and
                1 <= self.confirmation_frames <= 10 and .01 <= self.max_center_jump <= 2 and
                self.loss_action in ("SEARCH", "STOP")):
            raise ValueError("Policy settings are outside the lab limits")


class Policy:
    def __init__(self, config):
        self.config = config
        self.count = 0
        self.previous_offset = None
        self.last_id = None

    def step(self, observation, age_seconds, frame_id=None):
        cfg = self.config
        stop = {"state": "STOP", "linear_x": 0., "angular_z": 0.}
        if observation is None or not math.isfinite(age_seconds) or age_seconds < 0 or age_seconds > cfg.stale_after:
            self.count = 0
            self.previous_offset = None
            self.last_id = frame_id
            return {**stop, "reason": "stale_or_missing"}
        score, offset, area = [float(observation.get(k, 0)) for k in ("confidence", "center_offset", "area_fraction")]
        if not all(math.isfinite(v) for v in (score, offset, area)) or not (0 <= score <= 1 and -1 <= offset <= 1 and 0 <= area <= 1):
            self.count = 0
            return {**stop, "reason": "invalid_observation"}
        if area >= cfg.stop_area:
            self.count = 0
            self.last_id = frame_id
            return {**stop, "reason": "image_area_goal"}
        if not observation.get("detected") or score < cfg.min_confidence:
            self.count = 0
            self.previous_offset = None
            self.last_id = frame_id
            requested = transition(cfg.transition_rule,False,False,abs(offset)<=cfg.center_deadband,cfg.loss_action)
            allowed = "STOP" if requested == "APPROACH" else requested
            return {"state": allowed, "linear_x": 0.,
                    "angular_z": cfg.search_angular if allowed == "SEARCH" else 0., "reason": "no_usable_target"}
        if frame_id is None or frame_id != self.last_id:
            if self.previous_offset is not None and abs(offset-self.previous_offset) > cfg.max_center_jump:
                self.count = 0
            self.count += 1
            self.previous_offset = offset
            self.last_id = frame_id
        if self.count < cfg.confirmation_frames:
            return {**stop, "reason": "awaiting_consistent_frames"}
        centered = abs(offset) <= cfg.center_deadband
        requested = transition(cfg.transition_rule,True,True,centered,cfg.loss_action)
        if requested != "APPROACH":
            return {"state":requested,"linear_x":0.,"angular_z":cfg.search_angular if requested == "SEARCH" else 0.,"reason":"student_transition"}
        return {"state": "APPROACH", "linear_x": cfg.approach_linear if centered else 0.,
                "angular_z": 0. if centered else max(-.6, min(.6, -cfg.center_gain*offset)),
                "reason": "centered" if centered else "steering_in_place"}


def decide(observation, age_seconds, config):
    """Single fresh observation, including the confirmation requirement."""
    return Policy(config).step(observation, age_seconds)


SCENARIOS = ("visible", "low_confidence", "missing", "stale", "false_target", "occluded", "alternating", "stopping", "steering", "unstable_center")


def sequence(name, seed=None):
    base = {"detected": True, "confidence": .9, "center_offset": .02, "area_fraction": .10}
    if seed:
        base.update(seed)
    if name != "visible":
        # Isolate policy effects without a particular detector's box already meeting the goal.
        base.update(center_offset=.02,area_fraction=.10,detected=True,confidence=.9)
    events = []
    for index in range(25):
        obs = dict(base)
        age = .05
        target = True
        if 6 <= index < 16:
            if name == "low_confidence": obs["confidence"] = .2
            if name == "missing": obs = None
            if name == "stale": age = 1.5
            if name == "false_target":
                obs.update(confidence=.95, detected=True, center_offset=0., area_fraction=.1)
                target = False
            if name == "occluded": obs.update(detected=False, confidence=.1)
            if name == "alternating": obs.update(detected=index % 2 == 0, confidence=.9 if index % 2 == 0 else .1)
        if name == "stopping" and index >= 12: obs["area_fraction"] = .4
        if name == "steering": obs["center_offset"] = -.6 if index < 8 else (.6 if index < 16 else 0.)
        if name == "unstable_center" and 6 <= index < 16: obs["center_offset"] = -.7 if index % 2 else .7
        events.append({"time": round(index*.1, 2), "frame_id": index, "observation": obs, "age": age, "true_target": target})
    return events


def evaluate_sequences(config, seed=None):
    timelines, summaries = [], []
    for name in SCENARIOS:
        policy = Policy(config)
        first_usable = first_motion = None
        incorrect = unnecessary = unsafe = 0
        for event in sequence(name, seed):
            obs = event["observation"]
            command = policy.step(obs, event["age"], event["frame_id"])
            moving = command["linear_x"] > 0
            any_motion = moving or abs(command["angular_z"]) > 0
            unusable = obs is None or event["age"] > config.stale_after or not obs["detected"] or obs["confidence"] < config.min_confidence
            goal = obs is not None and obs["area_fraction"] >= config.stop_area
            incorrect += moving and not event["true_target"]
            # In simulation, usable visible target away from the goal is a ground-truth opportunity.
            opportunity = not unusable and not goal and event["true_target"] and abs(obs["center_offset"]) <= config.center_deadband
            unnecessary += opportunity and command["state"] == "STOP"
            unsafe += (any_motion and (obs is None or event["age"] > config.stale_after or goal)) or (moving and unusable)
            if opportunity and first_usable is None: first_usable = event["time"]
            if moving and first_motion is None: first_motion = event["time"]
            timelines.append({"scenario": name, "time": event["time"], "confidence": obs["confidence"] if obs else 0.,
                              "age": event["age"], "true_target": event["true_target"], **command})
            timelines[-1].update(center_offset=obs["center_offset"] if obs else None,
                                 area_fraction=obs["area_fraction"] if obs else None)
        summaries.append({"scenario": name, "incorrect_approach_steps": incorrect,
                          "stopped_opportunity_steps": unnecessary, "constraint_violations": unsafe,
                          "initial_action_delay_s": round(first_motion-first_usable, 2) if first_motion is not None and first_usable is not None else None})
    return {"config": asdict(config), "seed": seed, "summaries": summaries, "timeline": timelines,
            "safety_invariants_passed": all(r["constraint_violations"] == 0 for r in summaries)}
