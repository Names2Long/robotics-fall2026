"""Regression checks for the simulator and evidence boundaries."""
import unittest

from experiments import interpret_recording, can_save
from handover import (
    CHECKPOINT, MODES, dispatch, event, finish, interpret, new_trial, step,
)
from lab.storage import resume_trial


class HandoverTests(unittest.TestCase):
    def tick_to(self, trial, condition):
        for _ in range(20):
            if condition(trial["state"]):
                return
            dispatch(trial, event("TICK"))
        self.fail("Autonomy did not reach the expected state.")

    def test_supplied_autonomy_changes_goal_and_requires_readiness(self):
        trial = new_trial(MODES[2], "changed")
        dispatch(trial, event("START", "blue"), source="control")
        dispatch(trial, event("READY"), source="control")
        self.tick_to(trial, lambda state: state["waiting_for_change"])
        for _ in range(8):
            dispatch(trial, event("TICK"))
        self.assertEqual(trial["state"]["position"], CHECKPOINT)
        self.assertIsNone(trial["state"]["held"])
        dispatch(trial, event("STOP"), source="control")
        dispatch(trial, event("START", "red"), source="control")
        self.tick_to(trial, lambda state: state["phase"] == "WAIT_READY")
        self.assertIsNone(trial["state"]["delivered"])
        dispatch(trial, event("READY"), source="control")
        self.assertEqual(finish(trial)["outcome"], "Correct cup handed over")
        self.assertEqual(trial["state"]["delivered"], "red")

    def test_manual_pickup_and_offer_require_the_right_locations(self):
        trial = new_trial(MODES[0])
        dispatch(trial, event("PICK", "blue"), source="control")
        self.assertIsNone(trial["state"]["held"])
        for _ in range(5):
            dispatch(trial, event("RIGHT"), source="control")
        dispatch(trial, event("PICK", "blue"), source="control")
        dispatch(trial, event("OFFER"), source="control")
        self.assertEqual(trial["state"]["phase"], "EXECUTING")
        for _ in range(5):
            dispatch(trial, event("LEFT"), source="control")
        dispatch(trial, event("OFFER"), source="control")
        dispatch(trial, event("READY"), source="control")
        self.assertEqual(trial["state"]["delivered"], "blue")

    def test_visible_stop_overrides_student_rules(self):
        trial = new_trial()
        trial["state"].update(phase="WAIT_READY", held="blue", target="blue")
        def unexpected_rule(*_):
            self.fail("Stop must bypass the student controller.")
        after, _ = step(trial["state"], event("STOP"), unexpected_rule)
        self.assertEqual(after["phase"], "CANCELLED")
        self.assertIsNone(after["delivered"])

    def test_intended_words_do_not_drive_simulation(self):
        trial = new_trial()
        transcript = "bring me the red cup"
        dispatch(trial, interpret(transcript), lambda *_: "select",
                 source="voice", intended="Bring me the blue cup", transcript=transcript)
        self.assertEqual(trial["state"]["target"], "red")
        self.assertEqual(trial["state"]["phase"], "CONFIRM")
        self.assertEqual(trial["events"][0]["intended"], "Bring me the blue cup")
        self.assertEqual(trial["events"][0]["transcript"], transcript)

    def test_misheard_permission_requires_deliberate_approval(self):
        for phrase, phase, held, unsafe_decision in (
            ("confirm", "CONFIRM", None, "begin"),
            ("ready", "WAIT_READY", "blue", "release"),
        ):
            with self.subTest(phrase=phrase):
                trial = new_trial()
                trial["state"].update(phase=phase, target="blue", held=held)
                before = trial["state"].copy()
                incoming, pending = interpret_recording(trial["state"], phrase)
                dispatch(trial, incoming, lambda *_: unsafe_decision, source="voice", intended=f"Do not {phrase}", transcript=phrase)
                self.assertEqual(pending["kind"], phrase.upper())
                self.assertEqual(trial["state"], before)
                self.assertEqual(trial["events"][-1]["event"], "REVIEW")
                dispatch(trial, event("WAIT"), lambda *_: unsafe_decision, source="control")
                self.assertEqual(trial["state"], before)

    def test_ambiguous_trial_requires_attempted_repair(self):
        trial = new_trial(scenario="ambiguous")
        run = {"trial": trial, "group": "voice"}
        decide = lambda *_: "hold"
        dispatch(trial, event("UNRECOGNIZED"), decide, source="voice", intended="Bring me the cup")
        self.assertFalse(can_save(run))
        dispatch(trial, event("UNRECOGNIZED"), decide, source="voice", intended="The blue cup")
        self.assertTrue(can_save(run))

    def test_resume_keeps_elapsed_time_and_offer_window(self):
        run = {"saved_at": 50, "last_tick": 49,
               "trial": {"opened": 10, "start": 12, "entered": 40, "finished": None}}
        resume_trial(run, now=80)
        self.assertEqual(run["trial"], {"opened": 40, "start": 42, "entered": 70, "finished": None})
        self.assertEqual(run["last_tick"], 80)


if __name__ == "__main__":
    unittest.main()
