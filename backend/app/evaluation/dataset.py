import json
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

class EvaluationCase(BaseModel):
    """One manually labeled evaluation question."""
    id: str
    question: str
    relevant_chunk_ids: list[int] = Field(default_factory=list)
    answerable: bool = True

    @model_validator(mode="after")
    def validate_case(self):
        if self.answerable and not self.relevant_chunk_ids:
            raise ValueError(
                "Answerable cases must include relevant_chunk_ids."
            )

        if len(self.relevant_chunk_ids) != len(
            set(self.relevant_chunk_ids)
        ):
            raise ValueError(
                "relevant_chunk_ids must not contain duplicates."
            )

        return self


def load_evaluation_cases(file_path: str | Path) -> list[EvaluationCase]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset does not exist: {path}"
        )

    raw_data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(raw_data, list):
        raise ValueError(
            "Evaluation dataset must contain a JSON list."
        )

    cases = [
        EvaluationCase.model_validate(item)
        for item in raw_data
    ]

    case_ids = [case.id for case in cases]

    if len(case_ids) != len(set(case_ids)):
        raise ValueError(
            "Evaluation case IDs must be unique."
        )

    return cases