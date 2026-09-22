from __future__ import annotations
import hashlib
from pathlib import Path
from lab.frame_learning import valid_snapshot
from lab.models import RequirementResult,make_check

REFLECTIONS=("frame_context","initial_analysis","improved_changes","synthesis")


def current_hash(source):
    source=Path(source);return hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else ""


def evaluate(result,lock,responses,source):
    snapshot=responses.get("mission_2.snapshot",{})
    preserved=bool(lock.get("integrity_valid"))
    file_present=Path(source).exists() and bool(result.get("file_present"))
    fresh=bool(result.get("source_sha256") and result.get("source_sha256")==current_hash(source))
    tests=bool(result.get("unit_tests_passed") and result.get("test_count",0)>=5)
    revised=bool(result.get("source_differs_from_original"))
    live=bool(result.get("live_passed"))
    pending=bool(responses.get("mission_2.live_pending") and str(responses.get("mission_2.live_issue","")).strip())
    analysis=all(str(responses.get(f"mission_2.{key}","")).strip() for key in REFLECTIONS)
    requirements=[
        RequirementResult("snapshot","Frame snapshot selected",valid_snapshot(snapshot),snapshot.get("source","missing"),"live or reference"),
        RequirementResult("original","Initial AI response preserved",preserved,"preserved" if preserved else "missing or changed","preserved"),
        RequirementResult("file","Camera transform implementation found",file_present,file_present,"true"),
        RequirementResult("fresh","Evaluation matches current implementation",fresh,"current" if fresh else "rerun evaluator","current"),
        RequirementResult("tests","Course camera-transform tests pass",tests,result.get("test_count",0),">=5 passing"),
        RequirementResult("revision","Implementation revised from initial AI code",revised,revised,"true"),
        RequirementResult("live","Live transform verified or documented pending",live or pending,"verified" if live else ("pending" if pending else "no evidence"),"verified or documented pending"),
        RequirementResult("analysis","Frame, AI, test, and consequence analysis complete",analysis,"complete" if analysis else "unfinished","complete"),
    ]
    return make_check("You connected frame evidence, AI revision, tests, and consequences.",requirements)
