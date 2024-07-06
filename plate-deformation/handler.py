import logging
import random
import time

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
        task_id = random.randint(0, hash(time.time()))
        img = data["file"].file.read()
        logger.info("Task id: %s", task_id)
        task = Task(task_id=task_id, img=img)
        logger.debug("Publish task %s", task_id)
        self.broker.pub_task(task)
        result: str = await self.broker.sub_result(task_id)
        logger.debug("Retrieved task %s result", task_id)

        return web.json_response({"img": result})
