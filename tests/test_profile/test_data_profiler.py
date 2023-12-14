import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split
from ydata_profiling import ProfileReport

from opsml.profile.profile_data import DataProfiler
from opsml.registry import CardRegistries, DataCard


def test_datacard_create_data_profile_pandas(
    db_registries: CardRegistries,
    iris_data: pd.DataFrame,
):
    # create data card
    registry = db_registries.data

    iris_data["date_"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    data_card = DataCard(
        data=iris_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
    )

    data_card.create_data_profile()

    # should raise logging info if called again
    data_card.create_data_profile()

    registry.register_card(data_card)

    assert data_card.metadata.uris.profile_uri is not None

    data_card = registry.load_card(uid=data_card.uid)
    data_card.load_profile()

    assert data_card.data_profile is not None


def test_datacard_create_data_profile_polars(
    db_registries: CardRegistries,
    iris_data_polars: pd.DataFrame,
):
    # create data card
    registry = db_registries.data
    data_card = DataCard(
        data=iris_data_polars,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
    )

    # test non-sample path
    data_card.create_data_profile()

    # test sampling path
    data_card.create_data_profile(sample_perc=0.5)

    # should raise logging info if called again
    data_card.create_data_profile()

    registry.register_card(data_card)

    assert data_card.metadata.uris.profile_uri is not None

    data_card = registry.load_card(uid=data_card.uid)
    data_card.load_profile()

    assert data_card.data_profile is not None


def test_feed_data_profile(
    db_registries: CardRegistries,
    iris_data: pd.DataFrame,
):
    profile = ProfileReport(iris_data, title="Profiling Report")
    data_card = DataCard(
        data=iris_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_profile=profile,
    )

    # test profiling with sample
    data_card = DataCard(
        data=iris_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
    )

    data_card.create_data_profile(sample_perc=0.50)
    assert data_card.data_profile is not None


def test_compare_data_profile(
    db_registries: CardRegistries,
    iris_data: pd.DataFrame,
):
    # Split indices
    indices = np.arange(iris_data.shape[0])

    # usual train-val split
    train_idx, test_idx = train_test_split(indices, test_size=0.2, train_size=None)

    data_card = DataCard(
        data=iris_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=[
            {"label": "train", "indices": train_idx},
            {"label": "test", "indices": test_idx},
        ],
    )

    splits = data_card.split_data()

    train_profile = DataProfiler.create_profile_report(splits.train.X, name="train")
    test_profile = DataProfiler.create_profile_report(splits.test.X, name="test")

    comparison = DataProfiler.compare_reports([train_profile, test_profile])

    assert isinstance(comparison, ProfileReport)


def test_datacard_numpy_profile_fail(test_array: np.ndarray):
    data_card = DataCard(
        data=test_array,
        name="test_array",
        team="mlops",
        user_email="mlops.com",
    )

    with pytest.raises(ValueError):
        data_card.create_data_profile()
