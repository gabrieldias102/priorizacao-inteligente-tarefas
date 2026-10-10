import os

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.db import Base

# No CI, TEST_DATABASE_URL aponta para um PostgreSQL de verdade.
BANCOS = ["sqlite"]
if os.environ.get("TEST_DATABASE_URL"):
    BANCOS.append("postgresql")


@pytest.mark.parametrize("banco", BANCOS)
def test_migracoes_batem_com_os_modelos(banco, tmp_path):
    url = (
        f"sqlite:///{tmp_path / 'migracoes.db'}"
        if banco == "sqlite"
        else os.environ["TEST_DATABASE_URL"]
    )
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    engine = create_engine(url)
    try:
        with engine.connect() as conexao:
            diferencas = compare_metadata(MigrationContext.configure(conexao), Base.metadata)
        assert diferencas == []
    finally:
        engine.dispose()
        command.downgrade(config, "base")
