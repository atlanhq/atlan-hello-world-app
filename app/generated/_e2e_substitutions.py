# Generated from contract/app.pkl via contract-toolkit. DO NOT EDIT.
# Regenerate with: pkl eval -m . contract/app.pkl
from __future__ import annotations

from application_sdk.testing.e2e.substitutions import MustacheSubstitutions
from pydantic import Field


class HelloWorldMustacheSubstitutions(MustacheSubstitutions):
    name: str = Field(default="World", alias="{{name}}")
    repeat_count: int = Field(default=1, alias="{{repeat_count}}")
