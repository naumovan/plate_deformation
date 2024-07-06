import asyncio
import os
from contextlib import suppress

from aiohttp import web

from handler import Handler
from log import init_log
from scheduler import Scheduler


def main():
    app_port = int(os.getenv("APP_PORT", "8000"))

    init_log(stdout_level="DEBUG")
    handler = Handler()
    scheduler = Scheduler()

    async def run_background_tasks(_app):
        task = asyncio.create_task(scheduler.schedule())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    app = web.Application()
    app.cleanup_ctx.append(run_background_tasks)
    app.add_routes([web.post('/', handler.handle)])
    web.run_app(app, port=app_port)


if __name__ == '__main__':
    main()
