from __future__ import annotations

import importlib
import re
from typing import Type


def _snake_to_camel(s: str) -> str:
    parts = re.split(r"[_\-]+", s.strip())
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def load_pipeline_class(key: str):
    """
    --pipeline {key} 를 받아서 다음 규칙으로 파이프라인 클래스를 로딩한다.

    - module: app.pipeline.{key}_pipeline
    - class : {CamelCase(key)}Pipeline

    예:
    - key="crime" -> app.pipeline.crime_pipeline.CrimePipeline
    - key="humor" -> app.pipeline.humor_pipeline.HumorPipeline
    - key="true_crime" -> app.pipeline.true_crime_pipeline.TrueCrimePipeline
    """
    key = (key or "").strip()
    if not key:
        raise ValueError("pipeline key is empty")

    module_name = f"app.pipeline.{key}_pipeline"
    class_name = f"{_snake_to_camel(key)}Pipeline"

    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name, None)
    if cls is None:
        raise ImportError(f"Pipeline class not found: {module_name}.{class_name}")
    return cls


