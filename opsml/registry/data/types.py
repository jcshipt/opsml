# pylint: disable=protected-access
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import BaseModel, ConfigDict

from opsml.registry.image.dataset import ImageDataset

ValidData = Union[np.ndarray, pd.DataFrame, pl.DataFrame, pa.Table, ImageDataset]  # type: ignore


def get_class_name(object_: object) -> str:
    """Parses object to get the fully qualified class name.
    Used during type checking to avoid unnecessary imports.

    Args:
        object_:
            object to parse
    Returns:
        fully qualified class name
    """
    klass = object_.__class__
    module = klass.__module__
    if module == "builtins":
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + klass.__qualname__


# need for old v1 compat
class AllowedTableTypes(str, Enum):
    NDARRAY = "ndarray"
    ARROW_TABLE = "Table"
    PANDAS_DATAFRAME = "PandasDataFrame"
    POLARS_DATAFRAME = "PolarsDataFrame"
    DICTIONARY = "Dictionary"
    IMAGE_DATASET = "ImageDataset"


class AllowedDataType(str, Enum):
    PANDAS = "pandas.core.frame.DataFrame"
    PYARROW = "pyarrow.lib.Table"
    POLARS = "polars.dataframe.frame.DataFrame"
    NUMPY = "numpy.ndarray"
    IMAGE = "ImageDataset"
    DICT = "dict"
    SQL = "sql"
    PROFILE = "profile"
    TRANSFORMER_BATCH = "transformers.tokenization_utils_base.BatchEncoding"
    STRING = "str"
    TORCH_TENSOR = "torch.Tensor"
    TENSORFLOW_TENSOR = "tensorflow.python.framework.ops.EagerTensor"


class ArrowTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table: Union[pa.Table, np.ndarray]  # type: ignore
    storage_uri: Optional[str] = None
    feature_map: Optional[Dict[str, Any]] = None


def check_data_type(data: ValidData) -> str:
    """Checks that the data type is one of the allowed types

    Args:
        data:
            data to check

    Returns:
        data type
    """
    class_name = get_class_name(data)

    if isinstance(data, dict):
        return AllowedDataType.DICT.value
    if isinstance(data, ImageDataset):
        return AllowedDataType.IMAGE.value
    if isinstance(data, np.ndarray):
        return AllowedDataType.NUMPY.value
    if isinstance(data, pd.DataFrame):
        return AllowedDataType.PANDAS.value
    if isinstance(data, pl.DataFrame):
        return AllowedDataType.POLARS.value
    if isinstance(data, pa.Table):
        return AllowedDataType.PYARROW.value
    if isinstance(data, str):
        return AllowedDataType.STRING.value
    if class_name == AllowedDataType.TRANSFORMER_BATCH.value:
        return AllowedDataType.TRANSFORMER_BATCH.value
    if class_name == AllowedDataType.TORCH_TENSOR.value:
        return AllowedDataType.TORCH_TENSOR.value
    if class_name == AllowedDataType.TENSORFLOW_TENSOR.value:
        return AllowedDataType.TENSORFLOW_TENSOR.value

    raise ValueError(
        f"""Data must be one of the following types: numpy array, pandas dataframe, 
        polars dataframe, pyarrow table, or ImageDataset. Received {str(type(data))}
        """
    )
