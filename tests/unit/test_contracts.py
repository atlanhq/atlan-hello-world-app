"""Round-trip serialisation tests for the Hello World contracts.

Every Input / Output dataclass that crosses a Temporal task boundary must
survive ``model_dump_json`` → ``model_validate_json`` without losing fields
or changing types. These tests pin that invariant so a schema-breaking
change to ``contracts.py`` or ``contract/app.pkl`` fails CI before it ships.
"""

from application_sdk.contracts.types import FileReference
from pydantic import BaseModel

from app.contracts import (
    GenerateGreetingsInput,
    GenerateGreetingsOutput,
    HelloWorldInput,
    HelloWorldOutput,
    SummarizeInput,
    SummarizeOutput,
)


def _round_trip(obj: BaseModel, cls: type[BaseModel]) -> BaseModel:
    return cls.model_validate_json(obj.model_dump_json())


def _sample_file_ref(path: str = "/tmp/greetings.jsonl") -> FileReference:
    return FileReference(local_path=path)


class TestHelloWorldInput:
    def test_defaults_round_trip(self) -> None:
        decoded = _round_trip(HelloWorldInput(), HelloWorldInput)
        assert decoded.name == "World"
        assert decoded.repeat_count == 1
        assert decoded.output_dir == ""

    def test_custom_values_round_trip(self) -> None:
        original = HelloWorldInput(name="Atlan", repeat_count=5, output_dir="/tmp/hello")
        decoded = _round_trip(original, HelloWorldInput)
        assert decoded.name == "Atlan"
        assert decoded.repeat_count == 5
        assert decoded.output_dir == "/tmp/hello"


class TestHelloWorldOutput:
    def test_defaults_round_trip(self) -> None:
        decoded = _round_trip(HelloWorldOutput(), HelloWorldOutput)
        assert decoded.message == ""
        assert decoded.record_count == 0
        assert decoded.output_file is None

    def test_with_values_round_trip(self) -> None:
        original = HelloWorldOutput(
            message="Hello, Atlan!",
            record_count=3,
            output_file=_sample_file_ref("/tmp/out.jsonl"),
        )
        decoded = _round_trip(original, HelloWorldOutput)
        assert decoded.message == "Hello, Atlan!"
        assert decoded.record_count == 3
        assert decoded.output_file is not None
        assert decoded.output_file.local_path == "/tmp/out.jsonl"


class TestGenerateGreetingsContracts:
    def test_input_defaults(self) -> None:
        decoded = _round_trip(GenerateGreetingsInput(), GenerateGreetingsInput)
        assert decoded.name == "World"
        assert decoded.repeat_count == 1
        assert decoded.output_dir == ""

    def test_input_values(self) -> None:
        original = GenerateGreetingsInput(name="Atlan", repeat_count=7, output_dir="/tmp/raw")
        decoded = _round_trip(original, GenerateGreetingsInput)
        assert decoded.name == "Atlan"
        assert decoded.repeat_count == 7
        assert decoded.output_dir == "/tmp/raw"

    def test_output_defaults(self) -> None:
        decoded = _round_trip(GenerateGreetingsOutput(), GenerateGreetingsOutput)
        assert decoded.greetings_file is None
        assert decoded.record_count == 0

    def test_output_with_file(self) -> None:
        original = GenerateGreetingsOutput(greetings_file=_sample_file_ref(), record_count=4)
        decoded = _round_trip(original, GenerateGreetingsOutput)
        assert decoded.greetings_file is not None
        assert decoded.greetings_file.local_path == "/tmp/greetings.jsonl"
        assert decoded.record_count == 4


class TestSummarizeContracts:
    def test_input_round_trip(self) -> None:
        original = SummarizeInput(greetings_file=_sample_file_ref())
        decoded = _round_trip(original, SummarizeInput)
        assert decoded.greetings_file is not None
        assert decoded.greetings_file.local_path == "/tmp/greetings.jsonl"

    def test_output_round_trip(self) -> None:
        original = SummarizeOutput(message="Hello, Atlan!", record_count=3)
        decoded = _round_trip(original, SummarizeOutput)
        assert decoded.message == "Hello, Atlan!"
        assert decoded.record_count == 3
