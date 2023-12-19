# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import FileUtils
from opsml.registry.types.extra import CommonKwargs
from opsml.registry.types.model import (
    ApiDataSchemas,
    DataDict,
    HuggingFaceOnnxArgs,
    OnnxModelDefinition,
    TorchOnnxArgs,
)

logger = ArtifactLogger.get_logger()


class RegistryType(str, Enum):
    DATA = "data"
    MODEL = "model"
    RUN = "run"
    PIPELINE = "pipeline"
    AUDIT = "audit"
    PROJECT = "project"

    @staticmethod
    def from_str(name: str) -> "RegistryType":
        l_name = name.strip().lower()
        if l_name == "data":
            return RegistryType.DATA
        if l_name == "model":
            return RegistryType.MODEL
        if l_name == "run":
            return RegistryType.RUN
        if l_name == "pipeline":
            return RegistryType.PIPELINE
        if l_name == "project":
            return RegistryType.PROJECT
        if l_name == "audit":
            return RegistryType.AUDIT
        raise NotImplementedError()


class Metric(BaseModel):
    name: str
    value: Union[float, int]
    step: Optional[int] = None
    timestamp: Optional[int] = None


class Param(BaseModel):
    name: str
    value: Union[float, int, str]


METRICS = Dict[str, List[Metric]]
PARAMS = Dict[str, List[Param]]


class Comment(BaseModel):
    name: str
    comment: str
    timestamp: str = str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M"))

    def __eq__(self, other):  # type: ignore
        return self.__dict__ == other.__dict__


@dataclass
class CardInfo:

    """
    Class that holds info related to an Artifact Card

    Args:
        name:
            Name of card
        team:
            Team name
        user_email:
            Email
        uid:
            Unique id of card
        version:
            Version of card
        tags:
            Tags associated with card
    """

    name: Optional[str] = None
    team: Optional[str] = None
    user_email: Optional[str] = None
    uid: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class CardType(str, Enum):
    DATACARD = "data"
    RUNCARD = "run"
    MODELCARD = "model"
    PIPELINECARD = "pipeline"
    PROJECTCARD = "project"
    AUDITCARD = "audit"


class PipelineCardArgs(str, Enum):
    DATA_UIDS = "datacard_uids"
    MODEL_UIDS = "modelcard_uids"
    RUN_UIDS = "runcard_uids"


class RunCardArgs(str, Enum):
    DATA_UID = "datacard_uid"
    MODEL_UIDS = "modelcard_uids"
    PIPELINE_UID = "pipelinecard_uid"


class CardVersion(BaseModel):
    name: str
    version: str
    card_type: CardType


class AuditCardMetadata(BaseModel):
    audit_uri: Optional[str] = None
    datacards: List[CardVersion] = []
    modelcards: List[CardVersion] = []
    runcards: List[CardVersion] = []


class Description(BaseModel):
    summary: Optional[str] = None
    sample_code: Optional[str] = None
    Notes: Optional[str] = None

    @field_validator("summary", mode="before")
    @classmethod
    def load_summary(cls, summary: Optional[str]) -> Optional[str]:
        if summary is None:
            return summary

        if ".md" in summary.lower():
            try:
                mkdwn_path = FileUtils.find_filepath(name=summary)
                with open(mkdwn_path, "r", encoding="utf-8") as file_:
                    summary = file_.read()

            except IndexError as idx_error:
                logger.info(f"Could not load markdown file {idx_error}")

        return summary


@dataclass
class ModelCardUris:
    """Uri holder for ModelCardMetadata

    Args:
        modelcard_uri:
            URI of modelcard
        trained_model_uri:
            URI where model is stored
        sample_data_uri:
            URI of trained model sample data
        model_metadata_uri:
            URI where model metadata is stored
        preprocessor_uri:
            URI where preprocessor is stored
    """

    modelcard_uri: Optional[str] = None
    trained_model_uri: Optional[str] = None
    onnx_model_uri: Optional[str] = None
    model_metadata_uri: Optional[str] = None
    sample_data_uri: Optional[str] = None
    preprocessor_uri: Optional[str] = None

    model_config = ConfigDict(
        protected_namespaces=("protect_",),
        frozen=False,
    )


class ModelCardMetadata(BaseModel):
    """Create modelcard metadata

    Args:
        description:
            Description for your model
        onnx_model_data:
            Pydantic model containing onnx data schema
        onnx_model_def:
            Pydantic model containing OnnxModel definition
        model_type:
            Type of model
        data_schema:
            Optional dictionary of the data schema used in model training
        onnx_args:
            Optional pydantic model containing either Torch or HuggingFace args for model conversion to onnx.
        runcard_uid:
            RunCard associated with the ModelCard
        pipelinecard_uid:
            Associated PipelineCard
        uris:
            ModelCardUris object containing all uris associated with ModelCard
    """

    description: Description = Description()
    onnx_model_data: Optional[DataDict] = None
    onnx_model_def: Optional[OnnxModelDefinition] = None
    sample_data_type: str = CommonKwargs.UNDEFINED.value
    model_type: str = CommonKwargs.UNDEFINED.value
    model_class: str = CommonKwargs.UNDEFINED.value
    task_type: str = CommonKwargs.UNDEFINED.value
    preprocessor_name: str = CommonKwargs.UNDEFINED.value
    onnx_args: Optional[Union[TorchOnnxArgs, HuggingFaceOnnxArgs]] = None
    data_schema: Optional[ApiDataSchemas] = None
    runcard_uid: Optional[str] = None
    pipelinecard_uid: Optional[str] = None
    auditcard_uid: Optional[str] = None
    uris: ModelCardUris = ModelCardUris()

    model_config = ConfigDict(protected_namespaces=("protect_",))


@dataclass
class DataCardUris:
    """Data uri holder for DataCardMetadata

    Args:
        data_uri:
            Location where converted data is stored
        datacard_uri:
            Location where DataCard is stored
        profile_uri:
            Location where profile is stored
        profile_html_uri:
            Location where profile html is stored
    """

    data_uri: Optional[str] = None
    datacard_uri: Optional[str] = None
    profile_uri: Optional[str] = None
    profile_html_uri: Optional[str] = None


class DataCardMetadata(BaseModel):

    """Create a DataCard metadata

    Args:
        description:
            Description for your data
        feature_map:
            Map of features in data (inferred when converting to pyarrow table)
        feature_descriptions:
            Dictionary of features and their descriptions
        additional_info:
            Dictionary of additional info to associate with data
            (i.e. if data is tokenized dataset, metadata could be {"vocab_size": 200})
        data_uri:
            Location where converted pyarrow table is stored
        runcard_uid:
            Id of RunCard that created the DataCard
        pipelinecard_uid:
            Associated PipelineCard
        uris:
            DataCardUris object containing all uris associated with DataCard
    """

    description: Description = Description()
    feature_map: Optional[Dict[str, Optional[Any]]] = None
    data_type: str = "undefined"
    feature_descriptions: Dict[str, str] = {}
    additional_info: Dict[str, Union[float, int, str]] = {}
    runcard_uid: Optional[str] = None
    pipelinecard_uid: Optional[str] = None
    auditcard_uid: Optional[str] = None
    uris: DataCardUris = DataCardUris()

    @field_validator("feature_descriptions", mode="before")
    @classmethod
    def lower_descriptions(cls, feature_descriptions: Dict[str, str]) -> Dict[str, str]:
        if not bool(feature_descriptions):
            return feature_descriptions

        feat_dict = {}
        for feature, description in feature_descriptions.items():
            feat_dict[feature.lower()] = description.lower()

        return feat_dict


NON_PIPELINE_CARDS = [card.value for card in CardType if card.value not in ["pipeline", "project", "audit"]]

AuditSectionType = Dict[str, Dict[int, Dict[str, str]]]


@dataclass
class StoragePath:
    uri: str


@dataclass
class HuggingFaceStorageArtifact:
    model_interface: Any
    metadata: ModelCardMetadata
    to_onnx: bool = False
    model_uri: Optional[str] = None
    preprocessor_uri: Optional[str] = None
    onnx_uri: Optional[str] = None
