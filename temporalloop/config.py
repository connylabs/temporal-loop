#!/usr/bin/env python3
import json
import logging
import logging.config
import sys
from typing import Any, Callable, Optional, Sequence, Type, Union, cast

import yaml
from temporalio.converter import DataConverter
from temporalio.worker import Interceptor

from temporalloop.importer import ImportFromStringError, import_from_string
from temporalloop.worker import WorkerFactory, WorkerFactoryType

LOG_LEVELS: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "temporalloop.logutils.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
        },
    },
    "loggers": {
        "temporalio": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "temporalloop": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "temporalloop.error": {"level": "INFO"},
    },
}

logger: logging.Logger = logging.getLogger("temporalloop.error")


# pylint: disable=too-many-arguments,too-many-instance-attributes,dangerous-default-value
class WorkerConfig:
    def __init__(
        self,
        *,
        name: str,
        factory: Union[Type[WorkerFactoryType], str] = "",
        queue: str = "default-queue",
        host: str = "",
        namespace: str = "",
        activities: Sequence[Union[Callable[..., Any], str]] = [],
        workflows: Sequence[Union[Type[Any], str]] = [],
        interceptors: Sequence[Union[Interceptor, str]] = [],
        converter: Union[DataConverter, str, None] = None,
        behavior: str = "merge",
    ) -> None:
        self.name = name
        self.host: str = host
        self.namespace: str = namespace
        self.factory = WorkerFactory
        self._factory = factory
        self._workflows = workflows
        self._activities = activities
        self._interceptors = interceptors
        self._converter = converter
        self.converter: Optional[DataConverter] = None
        self.queue = queue
        self.workflows: Sequence[Type[Any]] = []
        self.interceptors: Sequence[Type[Interceptor]] = []
        self.activities: Sequence[Callable[..., Any]] = []
        self.loaded = False
        self.behavior = behavior

    def _merge(self, config: "Config") -> None:
        if not self.host:
            self.host = config.host
        if not self.namespace:
            self.namespace = config.namespace
        if not self._factory:
            self._factory = config.factory
        if not self._converter:
            self._converter = config.converter
        if not self._interceptors:
            self._interceptors = config.interceptors

    def load(self, global_config: Optional["Config"] = None) -> None:
        assert not self.loaded
        if self.behavior == "merge" and global_config is not None:
            self._merge(global_config)

        self.activities = self._load_functions(self._activities)
        self.workflows = self._load_functions(self._workflows)
        self.interceptors = self._load_functions(self._interceptors)
        self.converter = cast(DataConverter, self._load_function(self._converter))
        self.factory = self._load_function(self._factory)
        self.loaded = True

    def _load_functions(self, functions: Sequence[Any]) -> Sequence[Any]:
        return [self._load_function(f) for f in functions]

    def _load_function(self, function: Any) -> Any:
        if isinstance(function, str):
            try:
                function = import_from_string(function)
            except ImportFromStringError as e:
                logger.error(e)
                sys.exit(1)
        return function


class Config:
    def __init__(
        self,
        host: str = "localhost:7233",
        namespace: str = "default",
        factory: Union[Type[WorkerFactoryType], str] = WorkerFactory,
        log_config: Optional[Union[dict[str, Any], str]] = LOGGING_CONFIG,
        log_level: Optional[Union[str, int]] = None,
        interceptors: Sequence[Union[Type[Interceptor], str]] = [],
        converter: Union[DataConverter, str, None] = None,
        use_colors: Optional[bool] = None,
        workers: Sequence[Union[WorkerConfig, dict[str, Any]]] = [],
        limit_concurrency: Optional[int] = None,
    ):
        self.host = host
        self.namespace: str = namespace
        self.factory = factory
        self.log_config = log_config
        self.log_level = log_level
        self.use_colors = use_colors
        self.limit_concurrency = limit_concurrency
        self._interceptors = interceptors
        self._workers = workers
        self.workers: list[WorkerConfig] = []
        self.converter = converter
        self.interceptors: Sequence[Interceptor] = []
        self.loaded = False

        self.configure_logging()

    def configure_logging(self) -> None:
        if self.log_config is not None:
            if isinstance(self.log_config, dict):
                if self.use_colors in (True, False):
                    self.log_config["formatters"]["default"][
                        "use_colors"
                    ] = self.use_colors
                logging.config.dictConfig(self.log_config)
            elif self.log_config.endswith(".json"):
                with open(self.log_config, encoding="utf-8") as file:
                    loaded_config = json.load(file)
                    logging.config.dictConfig(loaded_config)
            elif self.log_config.endswith((".yaml", ".yml")):
                with open(self.log_config, encoding="utf-8") as file:
                    loaded_config = yaml.safe_load(file)
                    logging.config.dictConfig(loaded_config)
            else:
                # See the note about fileConfig() here:
                # https://docs.python.org/3/library/logging.config.html#configuration-file-format
                logging.config.fileConfig(
                    self.log_config, disable_existing_loggers=False
                )

        if self.log_level is not None:
            if isinstance(self.log_level, str):
                log_level = LOG_LEVELS[self.log_level]
            else:
                log_level = self.log_level
            logging.getLogger("temporalloop.error").setLevel(log_level)
            logging.getLogger("temporalloop").setLevel(log_level)
            logging.getLogger("temporalio").setLevel(log_level)
            logging.getLogger("root").setLevel(log_level)
            logging.getLogger("temporalloop.worker").setLevel(log_level)

    def load(self) -> None:
        assert not self.loaded
        for worker in self._workers:
            if isinstance(worker, dict):
                worker = WorkerConfig(**worker)
            if isinstance(worker, WorkerConfig):
                worker.load(self)
            self.workers.append(worker)
        self.loaded = True
