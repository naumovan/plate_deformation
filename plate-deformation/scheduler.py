import asyncio
import logging
import multiprocessing

import pickle

from broker import Broker
from detection.base import ...  # TODO add imports of functions
from worker import Worker


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, broker: Broker):
        self.broker = broker
        self.stage_one_queue = asyncio.Queue()
        self.stage_two_queue = asyncio.Queue()

        self.input_queue_model_1 = multiprocessing.Queue()
        self.output_queue_model_1 = multiprocessing.Queue()
        self.worker_1 = Worker(
            func=...,  # TODO add function
            input_queue=self.input_queue_model_1,
            output_queue=self.output_queue_model_1,
        )

        self.input_queue_model_2 = multiprocessing.Queue()
        self.output_queue_model_2 = multiprocessing.Queue()
        self.worker_2 = Worker(
            func=...,  # TODO add function
            input_queue=self.input_queue_model_2,
            output_queue=self.output_queue_model_2,
        )

        self.process_1 = multiprocessing.Process(target=self.worker_1.work)
        self.process_2 = multiprocessing.Process(target=self.worker_2.work)
        self.process_1.start()
        self.process_2.start()

    def __del__(self):
        for process in [self.process_1, self.process_2]:
            if process.is_alive():
                process.terminate()
                process.join(timeout=3)

    async def schedule(self):
        while True:
            task = await self.broker.sub_task()
            task.img = pickle.loads(task.img)
            self.stage_one_queue.put_nowait(task)
            await asyncio.sleep(0)

    async def stage_one(self):
        while True:
            while self.stage_one_queue.empty():
                await asyncio.sleep(0)
            task = self.stage_one_queue.get_nowait()

            self.input_queue_model_1.put_nowait(task)
            while self.output_queue_model_1.empty():
                await asyncio.sleep(0)
            result = self.output_queue_model_1.get()

            self.stage_two_queue.put_nowait(result)
            await asyncio.sleep(0)

    async def stage_two(self):
        while True:
            while self.stage_two_queue.empty():
                await asyncio.sleep(0)
            task = self.stage_two_queue.get_nowait()

            self.input_queue_model_2.put_nowait(task)
            while self.output_queue_model_2.empty():
                await asyncio.sleep(0)
            result = self.output_queue_model_2.get()

            task.img = pickle.dumps(result.img).hex()
            self.broker.pub_result(task)
