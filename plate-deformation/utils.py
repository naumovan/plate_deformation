from dataclasses import dataclass


@dataclass
class Task:
    task_id: int
    img: bytes
