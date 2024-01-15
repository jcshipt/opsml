# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import json
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pyarrow as pa
from pydantic import BaseModel, model_validator
from opsml.types import CommonKwargs

from opsml.helpers.logging import ArtifactLogger

logger = ArtifactLogger.get_logger()


def check_for_dirs(data_dir: Path) -> List[str]:
    """Checks if data_dir contains subdirectories and returns a list of subdirectories

    Args:
        data_dir:
            Path to data directory

    Returns:
        List of subdirectories
    """
    dirs = [x.as_posix() for x in data_dir.iterdir() if x.is_dir()]
    return dirs


def get_metadata_filepath(data_dir: Path, split: Optional[str]) -> Path:
    """Loads metadata file from data_dir or subdirectory of data_dir

    Args:
        data_dir:
            Path to data directory
        split:
            Optional split to use for the dataset. If not provided, all images in the data_dir will be used.

    Returns:
        `ImageMetadata`
    """
    search_path = data_dir

    if split is not None:
        search_path = data_dir / split

    for p in search_path.rglob("*.jsonl"):
        if p.name == "metadata.jsonl":
            return p

    raise ValueError(f"Could not find metadata.jsonl in {data_dir} or subdirectories")


class FileRecord(BaseModel):
    """Base record to associate with file

    Args:
        filepath:
            Path to the file relative to root directory
        size:
            Size of the file. This is inferred automatically if filepath is provided.

    """

    filepath: Path
    size: int

    @model_validator(mode="before")
    @classmethod
    def check_args(cls, data_args: Dict[str, Any]) -> Dict[str, Any]:
        filepath: Optional[Union[str, Path]] = data_args.get("filepath")
        size: Optional[int] = data_args.get("size")

        if isinstance(filepath, str):
            filepath = Path(filepath)

        # if reloading record
        if all([filepath, size]):
            return data_args

        # Check image exists
        assert filepath, "Filepath is required"

        assert filepath.exists(), f"Image file {filepath} does not exist"
        data_args["size"] = filepath.stat().st_size

        return data_args

    def to_arrow(self, data_dir: str, split_label: Optional[str] = None) -> Any:
        """Create pyarrow record"""
        raise NotImplementedError


class Metadata(BaseModel):
    """Base class for metadata"""

    records: List[FileRecord]

    def write_to_file(self, filepath: Path) -> None:
        """Write image metadata to jsonl file

        Args:
            filepath:
                Filepath to write metadata jsonl. Filename of metadata path should be `metadata.jsonl`

        """
        assert filepath.name == "metadata.jsonl", "Filename must be metadata.jsonl"

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", encoding="utf-8") as file_:
            for record in self.records:
                record = record.model_dump()
                record["filepath"] = record["filepath"].as_posix()
                json.dump(record, file_)
                file_.write("\n")

    @classmethod
    def load_from_file(cls, filepath: Path) -> None:
        """Load image metadata from jsonl file

        Args:
            filepath:
                Filepath to load metadata jsonl. Filename of metadata path should be `metadata.jsonl`

        """
        raise NotImplementedError

    @cached_property
    def size(self) -> int:
        """Total size of all images in metadata"""
        return sum([record.size for record in self.records])


class Dataset(BaseModel):
    """Create an image dataset from a directory of images.
    User can also provide a split that indicates the subdirectory of images to use.
    It is expected that each split contains a metadata.jsonl built from the ImageMetadata class.
    ImageData was built to have parity with HuggingFace.

    Args:
        data_dir:
            Root directory for images.

            For example, you the image file is located at either:
             - `images/train/my_image.png`
             - `images/my_image.png`
            Then the data_dir should be `images/`
        shard_size:
            Size of shards to use for dataset. Default is 512MB.
        batch_size:
            Batch size for dataset. Default is 1000.
        splits:
            Dictionary of splits to use for dataset. If no splits are provided, then the
            data_dir or subdirs will be used as the split. It is expected that each split contains a
            metadata.jsonl built from the ImageMetadata class. It is recommended to allow opsml
            to create the splits for you.
    """

    data_dir: Path
    shard_size: str = "512MB"
    batch_size: int = 1000
    splits: Dict[Optional[str], Metadata] = {}

    def split_data(self) -> None:
        """Creates data splits based on subdirectories of data_dir and supplied split value

        Returns:
            None
        """
        if bool(self.splits):
            return

        splits = check_for_dirs(self.data_dir)

        if bool(splits):
            for split in splits:
                self.splits[split] = self._load_metadata_from_file(self.data_dir, split)
        else:
            self.splits[None] = self._load_metadata_from_file(self.data_dir, None)

    @property
    def arrow_schema(self) -> pa.Schema:
        """Returns schema for ImageDataset records"""
        raise NotImplementedError

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @property
    def data_type(self) -> str:
        return CommonKwargs.UNDEFINED.value
