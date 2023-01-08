from typing import Any, Dict, List, Optional, Union

import numpy as np
from pandas import DataFrame
from pyarrow import Table
from pydantic import BaseModel, validator
from pyshipt_logging import ShiptLogging

from opsml_data.drift.data_drift import DriftReport
from opsml_data.registry.formatter import ArrowTable, DataFormatter
from opsml_data.registry.models import RegistryRecord
from opsml_data.registry.splitter import DataHolder, DataSplitter
from opsml_data.registry.storage import save_record_data_to_storage

logger = ShiptLogging.get_logger(__name__)


class ValidCard(BaseModel):

    data_name: str
    team: str
    user_email: str
    data: Union[np.ndarray, DataFrame, Table]
    drift_report: Optional[Dict[str, DriftReport]] = None
    data_splits: List[Dict[str, Any]] = []
    data_uri: Optional[str] = None
    drift_uri: Optional[str] = None
    version: Optional[int] = None
    feature_map: Optional[Dict[str, Union[str, None]]] = None
    data_type: Optional[str] = None
    uid: Optional[str] = None
    dependent_vars: Optional[List[str]] = None

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    @property
    def has_data_splits(self):
        return bool(self.data_splits)

    @validator("data_splits", pre=True)
    def convert_none(cls, splits):  # pylint: disable=no-self-argument
        if splits is None:
            return []

        for split in splits:
            indices = split.get("indices")
            if indices is not None and isinstance(indices, np.ndarray):
                split["indices"] = indices.tolist()

        return splits

    def overwrite_converted_data_attributes(self, converted_data: ArrowTable):
        setattr(self, "data_uri", converted_data.storage_uri)
        setattr(self, "feature_map", converted_data.feature_map)
        setattr(self, "data_type", converted_data.table_type)


class DataCard(ValidCard):
    """Create a data card class from data.

    Args:
        data (np.ndarray, pd.DataFrame, pa.Table): Data to use for
        data card.
        data_name (str): What to name the data
        team (str): Team that this data is associated with
        user_email (str): Email to associate with data card
        drift_report (pandas dataframe): Optional drift report generated by Drifter class
        data_splits (List of dictionaries): Optional list containing split logic. Defaults
        to None. Logic for data splits can be defined in the following two ways:

        You can specify as many splits as you'd like

        (1) Split based on column value (works for pd.DataFrame)
            splits = [
                {"label": "train", "column": "DF_COL", "column_value": 0}, -> "val" can also be a string
                {"label": "test",  "column": "DF_COL", "column_value": 1},
                {"label": "eval",  "column": "DF_COL", "column_value": 2},
                ]

        (2) Index slicing by start and stop (works for np.ndarray, pyarrow.Table, and pd.DataFrame)
            splits = [
                {"label": "train", "start": 0, "stop": 10},
                {"label": "test", "start": 11, "stop": 15},
                ]

        (3) Index slicing by list (works for np.ndarray, pyarrow.Table, and pd.DataFrame)
            splits = [
                {"label": "train", "indices": [1,2,3,4]},
                {"label": "test", "indices": [5,6,7,8]},
                ]

    Returns:
        Data card

    """

    def split_data(self) -> Optional[DataHolder]:

        """Loops through data splits and splits data either by indexing or
        column values

        Returns
            Class containing data splits
        """

        if not self.has_data_splits:
            return None

        data_splits: DataHolder = self._parse_data_splits()
        return data_splits

    def _parse_data_splits(self) -> DataHolder:

        data_holder = DataHolder()
        for split in self.data_splits:
            label, data = DataSplitter(split_attributes=split).split(data=self.data)
            setattr(data_holder, label, data)

        return data_holder

    def _convert_and_save_data(self, blob_path: str, version: int) -> None:

        """Converts data into a pyarrow table or numpy array and saves to gcs.

        Args:
            Data_registry (str): Name of data registry. This attribute is used when saving
            data in gcs.
        """

        converted_data: ArrowTable = DataFormatter.convert_data_to_arrow(data=self.data)
        converted_data.feature_map = DataFormatter.create_table_schema(converted_data.table)
        storage_path = save_record_data_to_storage(
            data=converted_data.table,
            data_name=self.data_name,
            version=version,
            team=self.team,
            blob_path=blob_path,
        )
        converted_data.storage_uri = storage_path.gcs_uri

        # manually overwrite
        self.overwrite_converted_data_attributes(converted_data=converted_data)

    def _save_drift(self, blob_path: str, version: int) -> None:

        """Saves drift report to gcs"""

        if bool(self.drift_report):

            storage_path = save_record_data_to_storage(
                data=self.drift_report,
                data_name="drift_report",
                version=version,
                team=self.team,
                blob_path=blob_path,
            )
            setattr(self, "drift_uri", storage_path.gcs_uri)

    def create_registry_record(self, data_registry: str, uid: str, version: int) -> RegistryRecord:

        """Creates required metadata for registering the current data card.
        Implemented with a DataRegistry object.

        Args:
            Data_registry (str): Name of data registry. This attribute is used when saving
            data in gcs.

        Returns:
            Regsitry metadata

        """
        setattr(self, "uid", uid)
        setattr(self, "version", version)
        self._convert_and_save_data(blob_path=data_registry, version=version)
        self._save_drift(blob_path=data_registry, version=version)

        return RegistryRecord(**self.__dict__)
