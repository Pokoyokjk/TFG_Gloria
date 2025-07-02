# ─── server/utils/evaluación_RAG.py ──────────────────────────────────────────
import re
from typing import Dict, List
from .RAG import rag_with_sparql          # importa tu función RAG

# ── Evaluador ultraligero ────────────────────────────────────────────────
class SimpleEvaluator:
    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def evaluate(self, candidate: str, reference: str) -> Dict[str, float]:
        cand_tok = self._tokens(candidate)
        ref_tok  = self._tokens(reference)
        cand_set, ref_set = set(cand_tok), set(ref_tok)
        inter, union = cand_set & ref_set, cand_set | ref_set

        exact = float(candidate.strip() == reference.strip())
        prec  = len(inter) / len(cand_set) if cand_set else 0.0
        rec   = len(inter) / len(ref_set)  if ref_set  else 0.0
        f1    = 2*prec*rec/(prec+rec) if prec+rec else 0.0
        jacc  = len(inter) / len(union) if union else 0.0
        len_ratio = len(cand_tok) / len(ref_tok) if ref_tok else 0.0
        diversity = len(cand_set) / len(cand_tok) if cand_tok else 0.0

        return {
            "ExactMatch": exact,
            "Precision":  prec,
            "Recall":     rec,
            "F1":         f1,
            "Jaccard":    jacc,
            "LenRatio":   len_ratio,
            "Diversity":  diversity,
        }

_evaluator = SimpleEvaluator()

# ── Función que utiliza RAG y devuelve métricas ───────────────────────────
def evaluate_rag_model(question: str, reference_answer: str) -> Dict[str, float]:
    """
    Ejecuta el RAG para question, compara con reference_answer
    y devuelve: {'answer': ...,  métrica1: ..., ...}
    """
    generated_answer = rag_with_sparql(question)
    metrics = _evaluator.evaluate(generated_answer, reference_answer)
    return {"answer": generated_answer,**metrics}

# ─────────────────────────────  EVALUACIÓN EN BLOQUE  ──────────────────────
from statistics import mean

def evaluate_batch(samples: list[dict]) -> dict:
    """
    `samples` = [{"question": "...", "expected_answer": "..."} , ...]
    Devuelve {"results":[{...}], "averages":{métrica: valor}}
    """
    all_results: list[dict] = []
    for s in samples:
        row = evaluate_rag_model(s["question"], s["expected_answer"])
        # conserva pregunta y ref también
        row["question"] = s["question"]
        row["reference"] = s["expected_answer"]
        all_results.append(row)

    # calcular medias (solo de campos numéricos)
    if not all_results:
        return {"results": [], "averages": {}}

    numeric_keys = [k for k in all_results[0].keys()
                    if isinstance(all_results[0][k], (int, float))]
    averages = {f"avg_{k}": mean(r[k] for r in all_results) for k in numeric_keys}

    return {"results": all_results, "averages": averages}
