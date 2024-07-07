import asyncio
import logging
import multiprocessing

import pickle

from broker import Broker
from detection.base import extract_and_process_crops, detect_symbols, postprocess_symbols
from worker import Worker


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, broker: Broker):
        self.broker = broker
        self.queue_stage_1 = asyncio.Queue()
        self.queue_stage_2 = asyncio.Queue()
        self.queue_stage_3 = asyncio.Queue()

        self.input_queue_stage_1 = multiprocessing.Queue()
        self.output_queue_stage_1 = multiprocessing.Queue()
        self.worker_1 = Worker(
            func=extract_and_process_crops,
            input_queue=self.input_queue_stage_1,
            output_queue=self.output_queue_stage_1,
        )

        self.input_queue_stage_2 = multiprocessing.Queue()
        self.output_queue_stage_2 = multiprocessing.Queue()
        self.worker_2 = Worker(
            func=detect_symbols,
            input_queue=self.input_queue_stage_2,
            output_queue=self.output_queue_stage_2,
        )

        self.input_queue_stage_3 = multiprocessing.Queue()
        self.output_queue_stage_3 = multiprocessing.Queue()
        self.worker_3 = Worker(
            func=postprocess_symbols,
            input_queue=self.input_queue_stage_3,
            output_queue=self.output_queue_stage_3,
        )

        self.process_1 = multiprocessing.Process(target=self.worker_1.work)
        self.process_2 = multiprocessing.Process(target=self.worker_2.work)
        self.process_3 = multiprocessing.Process(target=self.worker_3.work)

        self.process_1.start()
        self.process_2.start()
        self.process_3.start()

    def __del__(self):
        for process in [self.process_1, self.process_2]:
            if process.is_alive():
                process.terminate()
                process.join(timeout=3)

    async def schedule(self):
        while True:
            try:
                task = await self.broker.sub_task()
                task.img = pickle.loads(task.img)
                self.queue_stage_1.put_nowait(task)
            except Exception as exc:
                logger.error(exc)
            await asyncio.sleep(0)

    async def stage_1(self):
        while True:
            while self.queue_stage_1.empty():
                await asyncio.sleep(0)
            task = self.queue_stage_1.get_nowait()

            self.input_queue_stage_1.put_nowait(task)
            while self.output_queue_stage_1.empty():
                await asyncio.sleep(0)
            result = self.output_queue_stage_1.get()

            self.queue_stage_2.put_nowait(result)
            await asyncio.sleep(0)

    async def stage_2(self):
        while True:
            while self.queue_stage_2.empty():
                await asyncio.sleep(0)
            task = self.queue_stage_2.get_nowait()

            self.input_queue_stage_2.put_nowait(task)
            while self.output_queue_stage_2.empty():
                await asyncio.sleep(0)
            result = self.output_queue_stage_2.get()

            self.queue_stage_3.put_nowait(result)
            await asyncio.sleep(0)

    async def stage_3(self):
        while True:
            while self.queue_stage_3.empty():
                await asyncio.sleep(0)
            task = self.queue_stage_3.get_nowait()
            plate = task.img

            self.input_queue_stage_3.put_nowait(task)
            while self.output_queue_stage_3.empty():
                await asyncio.sleep(0)
            result = self.output_queue_stage_3.get()

            self.broker.pub_result(result, plate)
