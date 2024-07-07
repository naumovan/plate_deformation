import io
import logging
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
        """
        Принять запрос, отправить в очередь брокера на обработку, получить результат и вернуть в теле ответа и
        в качестве HTTP-заголовка `X-Text`.
        """

        logger.info("Incoming a new request: %s", id(request))
        data = await request.post()
        task_id = uuid.uuid4().int
        img = data["file"].file.read()
        logger.info("Task id: %s", task_id)
        task = Task(task_id=task_id, img=img)
        logger.debug("Publish task %s", task_id)
        start = time.perf_counter()
        self.broker.pub_task(task)
        result = await self.broker.sub_result(task_id)
        end = time.perf_counter()
        logger.debug("Retrieved task %s result", task_id)
        logger.info("Detection got %s seconds", end - start)

        image = result[0]
        with io.BytesIO() as byte_stream:
            image.save(byte_stream, format='JPEG')
            image_bytes = byte_stream.getvalue()

        response = web.Response(body=image_bytes)
        response.headers["X-Text"] = result[1]

        return response
