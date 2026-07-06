# SPDX-License-Identifier: MIT
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

DEFAULT_OUTPUT = (Path("~/Documents/Claude Session Exports")).expanduser()
CONFIG_PATH = (Path("~/.config/claude-session-exporter/config.toml")).expanduser()
_DEFAULT_SOURCES = ["cowork", "claude-code"]


@dataclass
class Config:
    output_dir: Path
    sources: list[str]
    emoji_headers: bool
    include_subagents: bool


def _defaults_toml() -> dict:
    return {
        "output_dir": str(DEFAULT_OUTPUT),
        "sources": _DEFAULT_SOURCES,
        "emoji_headers": False,
        "include_subagents": True,
    }


def load(path: Path | None = None) -> Config:
    path = path or CONFIG_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomli_w.dumps(_defaults_toml()), encoding="utf-8")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        output_dir=Path(data.get("output_dir", str(DEFAULT_OUTPUT))).expanduser(),
        sources=list(data.get("sources", _DEFAULT_SOURCES)),
        emoji_headers=bool(data.get("emoji_headers", False)),
        include_subagents=bool(data.get("include_subagents", True)),
    )


def set_output(output_dir: str, path: Path | None = None) -> Config:
    path = path or CONFIG_PATH
    cfg = load(path)
    data = _defaults_toml()
    data.update(
        {
            "output_dir": str(Path(output_dir).expanduser()),
            "sources": cfg.sources,
            "emoji_headers": cfg.emoji_headers,
            "include_subagents": cfg.include_subagents,
        }
    )
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return load(path)
