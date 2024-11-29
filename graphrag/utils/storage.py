# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage functions for the GraphRAG run module."""

import logging
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd

from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


async def _load_table_from_storage(name: str, storage: PipelineStorage) -> pd.DataFrame:
    if not await storage.has(name):
        msg = f"Could not find {name} in storage!"
        raise ValueError(msg)
    try:
        log.info("read table from storage: %s", name)
        match name.split(".")[-1]:
            case "parquet":
                return pd.read_parquet(BytesIO(await storage.get(name, as_bytes=True)))
            case "json":
                return pd.read_json(
                    StringIO(await storage.get(name)),
                    lines=False,
                    orient="records",
                )
            case "csv":
                return pd.read_csv(BytesIO(await storage.get(name, as_bytes=True)))
            case _:
                msg = f"Unknown file extension for {name}"
                log.exception(msg)
                raise
    except Exception:
        log.exception("error loading table from storage: %s", name)
        raise
