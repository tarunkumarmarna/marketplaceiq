"""
Runs the hand-written/reviewed test questions through the full pipeline,
then scores the results with RAGAS's evaluate() - faithfulness, context
precision/recall, and answer relevancy. Uses RAGAS's metrics library only,
not its TestsetGenerator (that part is fragile on non-markdown docs and
isn't needed here anyway, since the questions are already written).
"""

import json
import os
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference, LLMContextRecall, ResponseRelevancy

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from config import EMBEDDING_MODEL, GROQ_MODEL
from pipeline import answer_question

load_dotenv()


def load_test_questions():
    path = os.path.join(os.path.dirname(__file__), "test_questions.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    questions = load_test_questions()
    samples = []

    for q in questions:
        print(f"Running: {q['question']}")
        result = answer_question(q["question"])
        samples.append(
            SingleTurnSample(
                user_input=q["question"],
                response=result["answer"],
                retrieved_contexts=[c.page_content for c in result["retrieved_chunks"]],
                reference=q["expected_answer"],
            )
        )

    dataset = EvaluationDataset(samples=samples)

    # Groq as the judge model for RAGAS metrics (same "always Groq for judging"
    # rule used elsewhere in this project), local embeddings so nothing extra costs money
    evaluator_llm = LangchainLLMWrapper(ChatGroq(model=GROQ_MODEL, temperature=0))
    evaluator_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL))

    from ragas.run_config import RunConfig

    results = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            LLMContextPrecisionWithReference(),
            LLMContextRecall(),
            ResponseRelevancy(strictness=1),  # Groq doesn't support n>1, so ask for 1 variant not 3
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=RunConfig(max_workers=2, timeout=120),  # fewer concurrent calls, longer timeout - avoids hammering Groq's rate limit
    )

    df = results.to_pandas()
    out_path = os.path.join(os.path.dirname(__file__), "eval_results.csv")
    df.to_csv(out_path, index=False)

    print("\n--- Average scores ---")
    print(df[["faithfulness", "llm_context_precision_with_reference", "context_recall", "answer_relevancy"]].mean())
    print(f"\nFull results written to eval/eval_results.csv")


if __name__ == "__main__":
    main()
