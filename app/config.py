# app/config.py

import yaml
from dataclasses import dataclass
from typing import Dict

@dataclass
class VectorDBConfig:
    persist_directory: str
    embedding_model: str
    inference_mode: str

@dataclass
class OllamaConfig:
    default_model: str

@dataclass
class LoggingConfig:
    level: str
    format: str

@dataclass
class Config:
    user_agent: str
    vector_db: VectorDBConfig
    ollama: OllamaConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, filepath: str) -> 'Config':
        with open(filepath, 'r') as file:
            config_dict = yaml.safe_load(file)

        return cls(
            user_agent=config_dict.get('user_agent', 'MyStandaloneScript/1.0'),
            vector_db=VectorDBConfig(**config_dict.get('vector_db', {})),
            ollama=OllamaConfig(**config_dict.get('ollama', {})),
            logging=LoggingConfig(**config_dict.get('logging', {}))
        )