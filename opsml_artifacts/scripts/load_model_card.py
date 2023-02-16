from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, cast

import click

from opsml_artifacts import CardRegistry, ModelCard
from opsml_artifacts.helpers.logging import ArtifactLogger
from opsml_artifacts.registry.model.types import ModelApiDef

logger = ArtifactLogger.get_logger(__name__)

BASE_SAVE_PATH = "app/onnx_model"
MODEL_FILE = "model_def.json"


@dataclass
class ModelLoaderCli:
    """Class for loading ModelCard Onnx definition"""

    storage_type: str
    versions: List[Optional[int]]
    name: Optional[str] = None
    team: Optional[str] = None
    uid: Optional[str] = None

    def __post_init__(self):
        self.registry = self._set_registry(storage_type=self.storage_type)

    def _set_registry(self, storage_type: str) -> CardRegistry:
        return CardRegistry(registry_name="model", connection_type=storage_type)

    def _set_path(self, api_def: ModelApiDef) -> Path:
        path = Path(f"{BASE_SAVE_PATH}/{self.name}/{api_def.model_version}/")
        path.mkdir(parents=True, exist_ok=True)
        return path / MODEL_FILE

    def _save_api_def(self, api_def: ModelApiDef):
        filepath = self._set_path(api_def=api_def)

        with filepath.open("w", encoding="utf-8") as file_:
            file_.write(api_def.json())
        logger.info("Saved api model def to %s", filepath)

    def load_and_save_model(self, version: Optional[int] = None):
        model_card = self.registry.load_card(name=self.name, team=self.team, version=version)
        api_def = self._get_model_api_def(model_card=model_card)
        self._save_api_def(api_def=api_def)

    def save_model_api_def_from_versions(self) -> None:
        if bool(self.versions):
            version_list = self.versions
            for version in version_list:
                self.load_and_save_model(version=version)
        else:
            self.load_and_save_model()

    def _get_model_api_def(self, model_card: ModelCard) -> ModelApiDef:
        onnx_model = model_card.onnx_model()
        api_model = onnx_model.get_api_model()

        return api_model

    def save_to_local_file(self) -> None:
        # overrides everything
        if self.uid is not None:
            self.load_and_save_model()
        self.save_model_api_def_from_versions()


@click.command()
@click.option("--name", help="Name of the model", required=False, type=str)
@click.option("--team", help="Name of team that model belongs to", required=False, type=str)
@click.option("--version", help="Version of model to load", required=False, multiple=True, type=int)
@click.option("--uid", help="Unique id of modelcard", required=False, type=str)
@click.option("--storage_type", help="Storage client for loading model", default="local", required=False, type=str)
def load_model_card_to_file(name: str, team: str, version: int, uid: str, storage_type: str):
    if uid is None:
        if not all(bool(arg) for arg in [name, team]):
            raise ValueError(
                """A uid is required if name and team are not specified
           """
            )

    model_versions = cast(tuple, version)  # version is a multiple of ints that click converts to a tuple
    versions = list(model_versions)
    loader = ModelLoaderCli(
        storage_type=storage_type,
        name=name,
        team=team,
        versions=versions,
        uid=uid,
    )
    loader.save_to_local_file()


if __name__ == "__main__":
    load_model_card_to_file()  # pylint: disable=no-value-for-parameter