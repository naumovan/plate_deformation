import logging
import multiprocessing
from typing import Callable


logger = logging.getLogger(__name__)


class Worker:
    """
    Запускается в отдельном процессе. Выполняет задачу `func` в методе `work`, извлекая входные параметры из
    `input_queue` и добавляя результаты детекции в `output_queue`.
    """

    input_queue: multiprocessing.Queue
    output_queue: multiprocessing.Queue
    func: Callable

    def __init__(self, input_queue: multiprocessing.Queue, output_queue: multiprocessing.Queue, func: Callable):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.func = func

    def work(self):
        while True:
            try:
                task = self.input_queue.get()
                result = self.func(task.img)
                task.img = result
                self.output_queue.put_nowait(task)
            except Exception as exc:
                logger.error(exc)
                raise exc
