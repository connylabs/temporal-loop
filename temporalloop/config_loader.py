from typing import Any, Dict, Optional, Union

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from temporalloop.config import LOGGING_CONFIG, Config


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)


class LoggingConfigSchema(BaseConfig):
    use_colors: bool = Field(default=True)
    log_config: Optional[Union[dict[str, Any], str]] = Field(
        default_factory=lambda: LOGGING_CONFIG
    )
    level: str = Field(default="INFO")


class WorkerConfigSchema(BaseConfig):
    interceptors: Optional[list[str]] = Field(default=None)
    activities: Optional[list[str]] = Field(default=[])
    workflows: Optional[list[str]] = Field(default=[])
    queue: str = Field(default="")
    name: str = Field(default="")
    converter: Optional[str] = Field(default=None)
    factory: Optional[str] = Field(default=None)
    pre_init: Optional[list[str]] = Field(default=None)


class TemporalConfigSchema(BaseConfig):
    host: str = Field(default="localhost:7233")
    namespace: str = Field(default="default")
    workers: list[WorkerConfigSchema] = Field(default_factory=list)
    interceptors: list[str] = Field(default_factory=list)
    converter: Optional[str] = Field(default=None)
    default_factory: str = Field(default="temporalloop.worker:WorkerFactory")
    pre_init: list[str] = Field(default_factory=list)


class ConfigSchema(BaseConfig):
    temporalio: TemporalConfigSchema = Field(default_factory=TemporalConfigSchema)
    logging: LoggingConfigSchema = Field(default_factory=LoggingConfigSchema)


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
    # if "workers" in config_dict:
    #     config.workers = [
    #         WorkerConfigSchema(**worker) for worker in config_dict["workers"]
    #     ]
    # if "interceptors" in config_dict:
    #     config.interceptors = config_dict["interceptors"]
    # if "converter" in config_dict:
    #     config.converter = config_dict["converter"]
    # if "default_factory" in config_dict:
    #     config.default_factory = config_dict["default_factory"]

    return Config(
        host=config.temporalio.host,
        namespace=config.temporalio.namespace,
        factory=config.temporalio.default_factory,
        converter=config.temporalio.converter,
        log_level=config.logging.level,
        use_colors=config.logging.use_colors,
        log_config=config.logging.log_config,
        workers=[
            x.__dict__
            for x in config.temporalio.workers  # pylint: disable=not-an-iterable
        ],
        interceptors=config.temporalio.interceptors,
        pre_init=config.temporalio.pre_init,
    )
