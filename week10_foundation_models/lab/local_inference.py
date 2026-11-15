"""Persistent CPU worker. Reads local jobs and generates from pinned local weights."""
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from lab.evidence import atomic, write_json
from lab.local_config import MODEL_CONFIG, LANGUAGE_SYSTEM, VISION_PREPROCESSING, model_dir, scene_path
from lab.worker_lock import worker_lock


def load_model(kind):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoProcessor, AutoModelForImageTextToText
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    folder = str(model_dir(kind))
    if kind == "language":
        processor = AutoTokenizer.from_pretrained(folder, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(folder, local_files_only=True, dtype=torch.float32)
    else:
        processor = AutoProcessor.from_pretrained(folder, local_files_only=True)
        processor.image_processor.size = {"longest_edge": VISION_PREPROCESSING["longest_edge"]}
        processor.image_processor.do_image_splitting = VISION_PREPROCESSING["image_splitting"]
        model = AutoModelForImageTextToText.from_pretrained(folder, local_files_only=True, dtype=torch.float32)
    model.eval()
    return processor, model


def generate(kind, request, loaded, status_path, cancel_path, prefix_cache=None):
    import torch
    import transformers
    from transformers import StoppingCriteria, StoppingCriteriaList
    processor, model = loaded
    prompt = request["prompt"]
    start = time.perf_counter()
    image_digest = None
    system = LANGUAGE_SYSTEM
    model_input = prompt
    if kind == "language":
        if request.get("task") == "robot":
            from simulation.robot_room import ROBOT_SYSTEM, model_message
            system = ROBOT_SYSTEM
            model_input = model_message(prompt, request["robot_state"])
        messages = [{"role": "system", "content": system}, {"role": "user", "content": model_input}]
        inputs = processor.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    else:
        from PIL import Image
        path = scene_path(request["case"])
        image_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        photo = Image.open(path).convert("RGB")
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
        rendered = processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = processor(text=rendered, images=[photo], return_tensors="pt")
    input_tokens = inputs["input_ids"].shape[1]
    reused = 0
    generation_options = {}
    if prefix_cache is not None:
        token_ids = inputs["input_ids"][0].tolist()
        previous = prefix_cache.get("input_ids", [])
        for old, new in zip(previous, token_ids[:-1]):
            if old != new:
                break
            reused += 1
        past = prefix_cache.get("past_key_values")
        if past is not None:
            past.crop(reused)
            generation_options["past_key_values"] = past
        generation_options.update(return_dict_in_generate=True, use_cache=True)
    constraint = None
    if request.get("task") == "robot":
        from simulation.robot_room import allowed_commands
        command_tokens = [processor.encode(space + variant, add_special_tokens=False) + [processor.eos_token_id]
                          for command in allowed_commands(request["robot_state"]) for variant in (command, command.title(), command.lower())
                          for space in ("", " ", "\n", "\n\n")]
        def constraint(batch_id, input_ids):
            prefix = input_ids[input_tokens:].tolist()
            return sorted({tokens[len(prefix)] for tokens in command_tokens if tokens[:len(prefix)] == prefix and len(tokens) > len(prefix)})

    class Progress(StoppingCriteria):
        def __init__(self):
            self.last = 0

        def __call__(self, input_ids, scores, **kwargs):
            count = input_ids.shape[1] - input_tokens
            now = time.perf_counter()
            if now - self.last > .8:
                write_json(status_path, {**request.get("progress", {}), "status": "generating", "tokens": count, "seconds": round(now-start, 1)})
                self.last = now
            return cancel_path.exists() or now - start > 180

    write_json(status_path, {**request.get("progress", {}), "status": "generating", "tokens": 0})
    limit = 24 if request.get("task") == "robot" else 96 if kind == "language" else 80
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=limit, do_sample=False,
                                stopping_criteria=StoppingCriteriaList([Progress()]),
                                prefix_allowed_tokens_fn=constraint,
                                **generation_options,
                                pad_token_id=processor.eos_token_id if kind == "language" else processor.tokenizer.eos_token_id)
    if prefix_cache is not None:
        prefix_cache.update(input_ids=token_ids, past_key_values=output.past_key_values)
        output = output.sequences
    if cancel_path.exists():
        raise InterruptedError("Cancelled by student")
    elapsed = time.perf_counter() - start
    if elapsed > 180:
        raise TimeoutError("Generation exceeded three minutes. Try a shorter prompt or restart the model worker.")
    tokens = output[0, input_tokens:]
    text = processor.decode(tokens, skip_special_tokens=True) if kind == "language" else processor.tokenizer.decode(tokens, skip_special_tokens=True)
    if not text.strip():
        raise ValueError("The model returned an empty answer. Retry with a short, specific prompt.")
    return {**request, "output": text.strip(), "model": MODEL_CONFIG[kind]["id"], "model_revision": MODEL_CONFIG[kind]["revision"],
            "system_prompt": system if kind == "language" else "", "model_input": model_input, "image_sha256": image_digest,
            "image_preprocessing": VISION_PREPROCESSING if kind == "vision" else None,
            "generated_tokens": len(tokens), "max_new_tokens": limit, "generation_seconds": round(elapsed, 3),
            "truncated": len(tokens) >= limit, "decoding": "greedy", "device": "cpu", "live_inference": True,
            "library_versions": {"torch": torch.__version__, "transformers": transformers.__version__},
            "output_constraint": "one supplied robot command" if request.get("task") == "robot" else None,
            "reused_prefix_tokens": reused,
            "completed_at": datetime.now(timezone.utc).isoformat()}


def rollout(request, loaded, status_path, cancel_path):
    """Generate and check every one-cell action, keeping the prompt fixed."""
    from simulation.robot_room import initial_state, evaluate, MAX_STEPS
    state = initial_state()
    if request["robot_state"] != state:
        raise ValueError("A comparison run must start at the initial position.")
    steps, path = [], [state["position"][:]]
    start = time.perf_counter()
    prefix_cache = {}
    for index in range(MAX_STEPS):
        if cancel_path.exists():
            raise InterruptedError("Generation stopped")
        progress = {"robot_state": state, "path": path, "step": index+1, "limit": MAX_STEPS,
                    "last_action": steps[-1]["model"]["output"] if steps else "None yet",
                    "completed_steps": index, "run_seconds": round(time.perf_counter()-start, 1),
                    "mean_action_seconds": round(sum(row["model"]["generation_seconds"] for row in steps[-5:]) / min(5, len(steps)), 2) if steps else None}
        step_request = {**request, "job_id": request["job_id"] + "-step-" + str(index+1), "robot_state": state, "progress": progress}
        proposal = generate("language", step_request, loaded, status_path, cancel_path, prefix_cache)
        proposal.pop("progress", None)
        result = evaluate(proposal, state)
        steps.append({"model": proposal, "simulation": result})
        state = result["after"]
        path.append(state["position"][:])
        write_json(status_path, {**progress, "status": "generating", "robot_state": state,
                                 "path": path, "completed_steps": index+1,
                                 "last_action": proposal["output"]})
        if state["finished"]:
            break
    return {**request, "steps": steps, "output": " → ".join(s["model"]["output"] for s in steps),
            "model": MODEL_CONFIG["language"]["id"], "model_revision": MODEL_CONFIG["language"]["revision"],
            "system_prompt": steps[0]["model"]["system_prompt"], "live_inference": True,
            "output_constraint": "directional rollout v4", "generation_seconds": round(time.perf_counter()-start, 3)}


def serve(kind, queue):
    with worker_lock(queue) as acquired:
        if acquired:
            serve_locked(kind, queue)


def serve_locked(kind, queue):
    # Exclusive ownership means an existing claim came from a worker that exited.
    for claim in queue.glob("*.claimed"):
        try:
            claim.rmdir()
        except OSError:
            pass
    loaded = None
    idle_since = time.monotonic()
    while time.monotonic() - idle_since < 600:
        for path in sorted(queue.glob("*.request.json")):
            job_id = path.name.split(".")[0]
            status = queue / (job_id + ".status.json")
            result = queue / (job_id + ".result.json")
            cancel = queue / (job_id + ".cancel")
            if result.exists() or cancel.exists():
                continue
            try:
                (queue / (job_id + ".claimed")).mkdir()
            except FileExistsError:
                # A worker surviving a guide restart may already own this job.
                continue
            idle_since = time.monotonic()
            try:
                request = json.loads(path.read_text())
                if loaded is None:
                    write_json(status, {"status": "loading", "message": "Loading local model into CPU memory"})
                    loaded = load_model(kind)
                if cancel.exists():
                    raise InterruptedError("Cancelled by student")
                response = rollout(request, loaded, status, cancel) if request.get("task") == "robot" else generate(kind, request, loaded, status, cancel)
                write_json(result, {"status": "complete", "record": response})
            except Exception as error:
                if isinstance(error, InterruptedError):
                    from lab.local_jobs import cancellation_status
                    failure = cancellation_status(cancel)
                else:
                    failure = {"status": "error", "error": str(error),
                               "reason": "generation_timeout" if isinstance(error, TimeoutError) else "model_error"}
                write_json(result, failure)
            idle_since = time.monotonic()
        time.sleep(.2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=MODEL_CONFIG)
    parser.add_argument("queue", type=Path)
    args = parser.parse_args()
    serve(args.kind, args.queue)
