"""brody/reasoning/arithmetic_engine.py — Solveur arithmétique exact déterministe.

Fournit des calculs arithmétiques stricts, reproductibles et vérifiables,
sans arrondi flottant opaque et sans appel à un modèle génératif.
"""
from __future__ import annotations

import ast
import hashlib
import operator
import re
from fractions import Fraction
from typing import Any

from brody.reasoning.contracts import REASONING_BOUNDARY, ReasoningResult

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_EXPONENT = 100
_MAX_RESULT_DIGITS = 1000


class ArithmeticEvaluationError(ValueError):
    """Erreur levée lors d'un calcul arithmétique invalide ou non autorisé."""


class ExactArithmeticEvaluator:
    """Solveur d'expressions arithmétiques pures par AST sécurisé."""

    def __init__(self, *, max_exponent: int = _MAX_EXPONENT):
        self.max_exponent = max_exponent

    def evaluate_expression(self, expression: str) -> dict[str, Any]:
        """Évalue une expression arithmétique pure et retourne un résultat prouvable."""
        cleaned = expression.strip()
        if not cleaned:
            raise ArithmeticEvaluationError("EMPTY_EXPRESSION")

        try:
            tree = ast.parse(cleaned, mode="eval")
        except SyntaxError as exc:
            raise ArithmeticEvaluationError(f"SYNTAX_ERROR:{exc.msg}") from exc

        val = self._eval_node(tree.body)

        # Calcul de l'empreinte de preuve
        proof_payload = f"ARITHMETIC_PROOF:{cleaned}={val}"
        proof_hash = hashlib.sha256(proof_payload.encode("utf-8")).hexdigest()

        return {
            "expression": cleaned,
            "result": val,
            "result_str": str(val),
            "is_exact_integer": isinstance(val, int),
            "is_rational": isinstance(val, (int, Fraction)),
            "proof_hash": proof_hash,
            **REASONING_BOUNDARY,
        }

    def _eval_node(self, node: ast.AST) -> int | float | Fraction:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ArithmeticEvaluationError(f"UNSUPPORTED_CONSTANT_TYPE:{type(node.value).__name__}")

        if isinstance(node, ast.UnaryOp):
            op_func = _SAFE_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ArithmeticEvaluationError(f"UNSUPPORTED_UNARY_OPERATOR:{type(node.op).__name__}")
            operand = self._eval_node(node.operand)
            return op_func(operand)

        if isinstance(node, ast.BinOp):
            op_func = _SAFE_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ArithmeticEvaluationError(f"UNSUPPORTED_BINARY_OPERATOR:{type(node.op).__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)

            if isinstance(node.op, ast.Pow):
                if isinstance(right, int) and right > self.max_exponent:
                    raise ArithmeticEvaluationError(f"EXPONENT_TOO_LARGE:{right}")
                if isinstance(right, int) and right < 0:
                    return Fraction(1, left ** abs(right))

            if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if right == 0:
                    raise ArithmeticEvaluationError("ZERO_DIVISION")

            # Maintien de l'exactitude rationnelle pour les divisions entières
            if isinstance(node.op, ast.Div):
                if isinstance(left, int) and isinstance(right, int):
                    if left % right == 0:
                        return left // right
                    return Fraction(left, right)

            res = op_func(left, right)
            if isinstance(res, int) and len(str(res)) > _MAX_RESULT_DIGITS:
                raise ArithmeticEvaluationError("RESULT_OVERFLOW")
            return res

        raise ArithmeticEvaluationError(f"FORBIDDEN_AST_NODE:{type(node).__name__}")


def extract_arithmetic_expression(query: str) -> str | None:
    """Extrait l'expression mathématique d'une requête en langage naturel."""
    norm = str(query or "").strip()
    # Supprimer les mots de commande usuels
    prefixes = (
        r"^(?:combien\s+font|combien\s+vaut|calcule[rz]?|évalue[rz]?|calculer|évaluer|quelle\s+est\s+la\s+valeur\s+de)\s+",
        r"^(?:calculate|compute|evaluate|what\s+is)\s+",
    )
    for p in prefixes:
        norm = re.sub(p, "", norm, flags=re.IGNORECASE).strip()

    # Supprimer les signes de ponctuation finale
    norm = norm.rstrip("?.! ")

    # Si ce qui reste ressemble à une expression arithmétique
    if re.search(r"^[0-9\s\+\-\*\/\(\)\.\,\%]+$", norm):
        # Convertir les virgules décimales si nécessaire
        expr = norm.replace(",", ".")
        return expr
    return None


def solve_arithmetic_query(query: str) -> ReasoningResult:
    """Résout une demande de calcul arithmétique et génère une enveloppe de résultat vérifiable."""
    expr = extract_arithmetic_expression(query)
    evaluator = ExactArithmeticEvaluator()

    if not expr:
        return ReasoningResult(
            reasoning_type="ARITHMETIC",
            status="FAIL_CLOSED",
            query=query,
            result_text="Aucune expression arithmétique valide détectée.",
            restitution_ready=False,
            unknowns=["ARITHMETIC_EXPRESSION_MISSING"],
        )

    try:
        eval_result = evaluator.evaluate_expression(expr)
        result_val = eval_result["result"]
        result_text = f"Le résultat exact de {expr} est {result_val}."

        return ReasoningResult(
            reasoning_type="ARITHMETIC",
            status="SUCCESS",
            query=query,
            result_text=result_text,
            structured_payload=eval_result,
            premises_count=1,
            conclusions_count=1,
            proof_hash=eval_result["proof_hash"],
            restitution_ready=True,
        )
    except ArithmeticEvaluationError as exc:
        return ReasoningResult(
            reasoning_type="ARITHMETIC",
            status="FAIL_CLOSED",
            query=query,
            result_text=f"Calcul arithmétique impossible : {exc}",
            structured_payload={"expression": expr, "error": str(exc)},
            restitution_ready=False,
            unknowns=[f"ARITHMETIC_ERROR:{exc}"],
        )
