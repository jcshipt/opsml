from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

import numpy as np
import pandas as pd
import pyarrow as pa

from opsml_data.registry.models import ArrowTable


class ArrowFormatter(ABC):
    @staticmethod
    @abstractmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]):
        """Converts data to pyarrow"""

    @staticmethod
    @abstractmethod
    def validate_data(data: Union[pa.Table, np.ndarray]):
        """Validate data to formatter"""


class PandasFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:
        """Convert pandas dataframe to pyarrow table

        Args:
            data (pd.DataFrame): Pandas dataframe to convert

        Returns
            ArrowTable pydantic class containing table and table type
        """

        pa_table = pa.Table.from_pandas(data, preserve_index=False)

        return ArrowTable(
            table=pa_table,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: pd.DataFrame):
        if isinstance(data, pd.DataFrame):
            return True
        return False


class NumpyFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:

        """Convert numpy array to pyarrow table

        Args:
            data (np.ndarray): Numpy array to convert.
            Assumes data is in shape (rows, columns).

        Returns
            Numpy array
        """

        return ArrowTable(
            table=data,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: np.ndarray):
        if isinstance(data, np.ndarray):
            return True
        return False


class ArrowTableFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:

        """Take pyarrow table and returns pyarrow table

        Args:
            data (pyarrow table): Pyarrow table

        Returns
            ArrowTable pydantic class containing table and table type
        """

        return ArrowTable(
            table=data,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: pa.Table):
        if isinstance(data, pa.Table):
            return True
        return False


# Run tests for data formatter
class DataFormatter:
    @staticmethod
    def convert_data_to_arrow(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:

        """
        Converts a pandas dataframe or numpy array into a py arrow table.
        Args:
            data: Pandas dataframe or numpy array.
        Returns:
            py arrow table
        """

        converter = next(
            (
                arrow_formatter
                for arrow_formatter in ArrowFormatter.__subclasses__()
                if arrow_formatter.validate_data(data=data)
            )
        )

        return converter.convert(data=data)

    @staticmethod
    def create_table_schema(data: Union[pa.Table, np.ndarray]) -> Dict[str, Optional[str]]:
        """
        Generates a schema (column: type) from a py arrow table.
        Args:
            data: py arrow table.
        Returns:
            schema: Dict[str,str]
        """

        feature_map: Dict[str, Optional[str]] = {}
        if isinstance(data, pa.Table):
            schema = data.schema

            for feature, type_ in zip(schema.names, schema.types):
                feature_map[feature] = str(type_)

        elif isinstance(data, np.ndarray):
            feature_map["numpy_dtype"] = str(data.dtype)

        else:
            feature_map["data_dtype"] = None

        return feature_map
