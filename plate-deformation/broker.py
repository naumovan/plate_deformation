import asyncio
import PIL.Image

from utils import Task


class Broker:
    """
    Брокер сообщений, реализованный по паттерну PubSub.
    """

    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.result_queue = {}

    def pub_task(self, task: Task):
        self.result_queue[task.task_id] = None
        self.task_queue.put_nowait(task)

    def pub_result(self, task: Task, plate: str):
        self.result_queue[task.task_id] = (task.img, plate)

    async def sub_task(self) -> Task:
        while self.task_queue.empty():
            await asyncio.sleep(0)

        return self.task_queue.get_nowait()

    async def sub_result(self, task_id: int) -> (PIL.Image.Image, str):
        while self.result_queue[task_id] is None:
            await asyncio.sleep(0)

        return self.result_queue.pop(task_id)
