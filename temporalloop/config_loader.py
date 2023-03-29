from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

import yaml

from temporalloop.config import LOGGING_CONFIG, Config


@dataclass
class TemporalConfigSchema:
    host: str = field(default="localhost:7233")
    namespace: str = field(default="default")


@dataclass
class LoggingConfigSchema:
    use_colors: bool = field(default=True)
    log_config: Optional[Union[dict[str, Any], str]] = field(
        default_factory=lambda: LOGGING_CONFIG
    )
    level: str = field(default="INFO")


@dataclass
class WorkerConfigSchema:
    interceptors: Optional[list[str]] = field(default=None)
    activities: Optional[list[str]] = field(default=None)
    workflows: Optional[list[str]] = field(default=None)
    queue: str = field(default="")
    name: str = field(default="")
    converter: Optional[str] = field(default=None)
    factory: Optional[str] = field(default=None)


@dataclass
class ConfigSchema:
    temporalio: TemporalConfigSchema = field(default_factory=TemporalConfigSchema)
    logging: LoggingConfigSchema = field(default_factory=LoggingConfigSchema)
    workers: list[WorkerConfigSchema] = field(default_factory=list)
    interceptors: list[str] = field(default_factory=list)
    converter: Optional[str] = field(default=None)
    default_factory: str = field(default="temporalloop.worker:WorkerFactory")


def load_config_from_yaml(file_path: str) -> Config:
    with open(file_path, "r", encoding="utf-8") as file:
        config_dict = yaml.safe_load(file)
    return config_from_dict(config_dict)


def config_from_dict(config_dict: Dict[str, Any]) -> Config:
    config = ConfigSchema()
    if "temporalio" in config_dict:
        config.temporalio = TemporalConfigSchema(**config_dict["temporalio"])
    if "logging" in config_dict:
        config.logging = LoggingConfigSchema(**config_dict["logging"])
    if "workers" in config_dict:
        config.workers = [
            WorkerConfigSchema(**worker) for worker in config_dict["workers"]
        ]
    if "interceptors" in config_dict:
        config.interceptors = config_dict["interceptors"]
    if "converter" in config_dict:
        config.converter = config_dict["converter"]
    if "default_factory" in config_dict:
        config.default_factory = config_dict["default_factory"]

    return Config(
        host=config.temporalio.host,
        namespace=config.temporalio.namespace,
        factory=config.default_factory,
        converter=config.converter,
        log_level=config.logging.level,
        use_colors=config.logging.use_colors,
        log_config=config.logging.log_config,
        workers=[x.__dict__ for x in config.workers],
        interceptors=config.interceptors,
    )
