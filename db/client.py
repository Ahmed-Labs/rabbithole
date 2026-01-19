from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neo4j import Driver, GraphDatabase

Params = Dict[str, Any]


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> Neo4jConfig:
        try:
            return cls(
                uri=os.environ["NEO4J_URI"],
                user=os.environ["NEO4J_USER"],
                password=os.environ["NEO4J_PASSWORD"],
            )
        except KeyError as e:
            raise RuntimeError(f"Missing environment variable: {e.args[0]}")


class Neo4jClient:
    def __init__(self, cfg: Neo4jConfig):
        self.cfg = cfg
        self._driver: Driver = GraphDatabase.driver(
            cfg.uri, auth=(cfg.user, cfg.password)
        )

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> Neo4jClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def run_write(self, cypher: str, params: Optional[Params] = None) -> None:
        params = params or {}

        def work(tx):
            tx.run(cypher, **params).consume()

        with self._driver.session() as session:
            session.execute_write(work)

    def run_read(self, cypher: str, params: Optional[Params] = None) -> list[dict]:
        params = params or {}

        def _work(tx):
            result = tx.run(cypher, **params)
            return [r.data() for r in result]

        with self._driver.session() as session:
            return session.execute_read(_work)
