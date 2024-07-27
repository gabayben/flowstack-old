"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/debug.py
"""

from collections import defaultdict
from datetime import datetime, timezone
import json
from pprint import pformat
from typing import Any, Iterator, Literal, Mapping, NotRequired, Optional, Sequence, TypedDict, Union
from uuid import UUID, uuid5

from pydantic import BaseModel

from flowstack.flows.channels import Channel
from flowstack.flows.channels.utils import read_channels
from flowstack.flows.checkpoints import CheckpointMetadata
from flowstack.flows.constants import HIDDEN
from flowstack.flows.typing import PregelExecutableTask

class TaskPayload(TypedDict):
    id: str
    name: str
    input: Any
    triggers: list[str]

class TaskResultPayload(TypedDict):
    id: str
    name: str
    result: list[tuple[str, Any]]

class CheckpointPayload(TypedDict):
    values: dict[str, Any]
    metadata: CheckpointMetadata
    config: NotRequired[Optional[dict[str, Any]]]

class DebugOutputBase(BaseModel):
    timestamp: str
    step: int
    type: str
    payload: dict[str, Any]

class DebugOutputTask(DebugOutputBase):
    type: Literal["task"]
    payload: TaskPayload

class DebugOutputTaskResult(DebugOutputBase):
    type: Literal["task_result"]
    payload: TaskResultPayload

class DebugOutputCheckpoint(DebugOutputBase):
    type: Literal["checkpoint"]
    payload: CheckpointPayload

DebugOutput = Union[DebugOutputTask, DebugOutputTaskResult, DebugOutputCheckpoint]

TASK_NAMESPACE = UUID("6ba7b831-9dad-11d1-80b4-00c04fd430c8")

def map_debug_tasks(
    step: int, tasks: list[PregelExecutableTask]
) -> Iterator[DebugOutputTask]:
    ts = datetime.now(timezone.utc).isoformat()
    for task in tasks:
        if task.config is not None and HIDDEN in task.config.get("tags", []):
            continue

        task.config = task.config or {}
        metadata = task.config["metadata"].copy()
        metadata.pop("thread_ts", None)

        yield {
            "type": "task",
            "timestamp": ts,
            "step": step,
            "payload": {
                "id": str(uuid5(TASK_NAMESPACE, json.dumps((task.name, step, metadata)))),
                "name": task.name,
                "input": input,
                "triggers": task.triggers,
            },
        }

def map_debug_task_results(
    step: int,
    tasks: list[PregelExecutableTask],
    stream_channels_list: Sequence[str],
) -> Iterator[DebugOutputTaskResult]:
    ts = datetime.now(timezone.utc).isoformat()
    for task in tasks:
        if task.config is not None and HIDDEN in task.config.get("tags", []):
            continue

        task.config = task.config or {}
        metadata = task.config["metadata"].copy()
        metadata.pop("thread_ts", None)

        yield {
            "type": "task_result",
            "timestamp": ts,
            "step": step,
            "payload": {
                "id": str(uuid5(TASK_NAMESPACE, json.dumps((task.name, step, metadata)))),
                "name": task.name,
                "result": [w for w in task.writes if w[0] in stream_channels_list],
            },
        }

def map_debug_checkpoint(
    step: int,
    channels: Mapping[str, Channel],
    stream_channels: Union[str, Sequence[str]],
    metadata: CheckpointMetadata,
    **config,
) -> Iterator[DebugOutputCheckpoint]:
    ts = datetime.now(timezone.utc).isoformat()
    yield {
        "type": "checkpoint",
        "timestamp": ts,
        "step": step,
        "payload": {
            "config": config,
            "values": read_channels(channels, stream_channels),
            "metadata": metadata,
        },
    }

def print_step_tasks(step: int, next_tasks: list[PregelExecutableTask]) -> None:
    n_tasks = len(next_tasks)
    print(
        f"[{step}:tasks] "
        + f"Starting step {step} with {n_tasks} task{'s' if n_tasks != 1 else ''}:\n"
        + "\n".join(
            f"- {task.name} -> {pformat(task.input)}"
            for task in next_tasks
        )
    )

def print_step_writes(
    step: int, writes: Sequence[tuple[str, Any]], whitelist: Sequence[str]
) -> None:
    by_channel: dict[str, list[Any]] = defaultdict(list)
    for channel, value in writes:
        if channel in whitelist:
            by_channel[channel].append(value)
    print(
        f"[{step}:writes] "
        + f"Finished step {step} with writes to {len(by_channel)} channel{'s' if len(by_channel) != 1 else ''}:\n"
        + "\n".join(
            f"- {name} -> {', '.join(pformat(v) for v in vals)}"
            for name, vals in by_channel.items()
        )
    )

def print_step_checkpoint(
    step: int, channels: Mapping[str, Channel], whitelist: Sequence[str]
) -> None:
    print(
        f"[{step}:checkpoint] "
        + f"State at the end of step {step}:\n"
        + pformat(read_channels(channels, whitelist), depth=3)
    )