import logging
import random
import time
import uuid

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from broker import Broker
from utils import Task


logger = logging.getLogger(__name__)


class Handler:
    broker: Broker

    def __init__(self, broker: Broker):
        self.broker = broker

    async def handle(self, request: Request) -> Response:
        logger.info("Incoming a new request: %s", id(request))
        data = await request.post()
        task_id = uuid.uuid4().int
        img = data["file"].file.read()
        logger.info("Task id: %s", task_id)
        task = Task(task_id=task_id, img=img)
        logger.debug("Publish task %s", task_id)
        start = time.perf_counter()
        self.broker.pub_task(task)
        result: str = await self.broker.sub_result(task_id)
        end = time.perf_counter()
        logger.debug("Retrieved task %s result", task_id)
        logger.info("Detection got %s seconds", end - start)

        return web.json_response({"img": result})
