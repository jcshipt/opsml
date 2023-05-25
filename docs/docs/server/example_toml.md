# Example pyproject toml for `Opsml` Setup (with `Mlflow`)


```
[tool.poetry]
name = "opsml-api"
version = "0.1.0"
description = ""
authors = ["devops-ml"]

[tool.poetry.dependencies]
python = ">=3.9,<=3.11"
llvmlite = "^0.39.1"
mlflow = "^2.2.1"
numba = "^0.56.4"
pyshipt-logging = "^1.0.4"
psycopg2 = "^2.9.5"
opsml = {version = "0.3.3", extras = ["gcp-postgres", "server"]}
gcsfs = ">=2022.11.0,<2023.0.0"
google-auth = "1.35.0"
google-cloud-storage = ">=2.2.1,<3.0.0"
```