from html import escape

from sqlalchemy.orm import Session

from app.core.config import settings
from app.generation.client import GeminiTextGenerator, TextGenerator
from app.generation.context import ContextBuilder
from app.generation.models import BuiltContext, GeneratedAnswer
from app.reranking.service import RerankingService
from app.generation.citations import resolve_citations

NO_ANSWER = "I don't know based on the provided documents."

class GenerationService:
    """Retrieves reranked evidence, builds context, and generates an answer."""
    def __init__(
        self,
        *,
        reranking_service: RerankingService | None = None,
        context_builder: ContextBuilder | None = None,
        generator: TextGenerator | None = None,
    ) -> None:
        self.reranking_service = reranking_service or RerankingService()
        self.context_builder = context_builder or ContextBuilder()
        self.generator = generator or GeminiTextGenerator()

    def answer(self, question: str, db: Session) -> GeneratedAnswer:
        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        reranked_chunks = self.reranking_service.search(
            cleaned_question,
            db,
            top_k=settings.generation_context_top_k,
            candidate_k=settings.reranker_candidate_k,
        )

        context = self.context_builder.build(reranked_chunks)

        if not context.chunks:
            return GeneratedAnswer(
                answer=NO_ANSWER,
                context=context,
            )

        prompt = self._build_prompt(
            question=cleaned_question,
            context=context,
        )

        answer = self.generator.generate(prompt)

        try:
            citations = resolve_citations(
                answer,
                context,
                require_citations=(answer != NO_ANSWER),
            )
        except RuntimeError:
            repair_prompt = f"""
        Rewrite the draft answer below.

        Use only the retrieved documents already provided.
        Keep only claims supported by those documents.
        Add valid citations immediately after each factual claim, using only
        the available labels [1] through [{len(context.chunks)}].
        Return only the revised answer.

        <retrieved_documents>
        {context.text}
        </retrieved_documents>

        <draft_answer>
        {answer}
        </draft_answer>
        """.strip()

            answer = self.generator.generate(repair_prompt)

            citations = resolve_citations(
                answer,
                context,
                require_citations=(answer != NO_ANSWER),
            )

        return GeneratedAnswer(
            answer=answer,
            context=context,
            citations=citations,
        )

    @staticmethod
    def _build_prompt(*, question: str, context: BuiltContext) -> str:
        return f"""
<question>
{escape(question)}
</question>

<retrieved_documents>
{context.text}
</retrieved_documents>

Answer the question using only the retrieved documents.
""".strip()