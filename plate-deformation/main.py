import asyncio
import os
from contextlib import suppress

from aiohttp import web

from broker import Broker
from handler import Handler
from log import init_log
from scheduler import Scheduler


def main():
    app_port = int(os.getenv("APP_PORT", "8000"))

    init_log(stdout_level="DEBUG")

    broker = Broker()
    handler = Handler(broker)
    scheduler = Scheduler(broker)

    async def run_background_tasks(_app):
        tasks = [
            asyncio.create_task(scheduler.schedule()),
            asyncio.create_task(scheduler.stage_1()),
            asyncio.create_task(scheduler.stage_2()),
            asyncio.create_task(scheduler.stage_3()),
        ]
        yield
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

    app = web.Application()
    app.cleanup_ctx.append(run_background_tasks)
    app.add_routes([web.post('/', handler.handle)])
    web.run_app(app, port=app_port)


if __name__ == '__main__':
    main()
