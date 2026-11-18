"""tests/reasoning/test_arithmetic_engine.py — Tests unitaires du solveur arithmétique exact.

Vérifie l'exactitude des calculs, le maintien de la précision rationnelle,
la sécurité contre l'injection de code et le rejet des divisions par zéro.
"""
from __future__ import annotations

from fractions import Fraction
import pytest

from brody.reasoning.arithmetic_engine import (
    ArithmeticEvaluationError,
    ExactArithmeticEvaluator,
    extract_arithmetic_expression,
    solve_arithmetic_query,
)


def test_basic_arithmetic_operations():
    """Valide les opérations arithmétiques de base (+, -, *, /)."""
    evaluator = ExactArithmeticEvaluator()

    assert evaluator.evaluate_expression("2 + 3")["result"] == 5
    assert evaluator.evaluate_expression("100 - 45")["result"] == 55
    assert evaluator.evaluate_expression("42 * 17")["result"] == 714
    assert evaluator.evaluate_expression("100 / 4")["result"] == 25
    assert evaluator.evaluate_expression("10 // 3")["result"] == 3
    assert evaluator.evaluate_expression("10 % 3")["result"] == 1


def test_rational_precision_no_float_drift():
    """Valide que les divisions non entières restent en fraction exacte sans dérive flottante."""
    evaluator = ExactArithmeticEvaluator()
    res = evaluator.evaluate_expression("1 / 3")
    assert res["result"] == Fraction(1, 3)
    assert res["is_rational"] is True


def test_exponentiation_bounds():
    """Valide les puissances et le bornage contre les débordements."""
    evaluator = ExactArithmeticEvaluator(max_exponent=10)
    assert evaluator.evaluate_expression("2 ** 8")["result"] == 256

    with pytest.raises(ArithmeticEvaluationError) as exc:
        evaluator.evaluate_expression("2 ** 50")
    assert "EXPONENT_TOO_LARGE" in str(exc.value)


def test_fail_closed_on_zero_division():
    """Valide le rejet immédiat fail-closed de toute division par zéro."""
    evaluator = ExactArithmeticEvaluator()
    with pytest.raises(ArithmeticEvaluationError) as exc:
        evaluator.evaluate_expression("42 / 0")
    assert "ZERO_DIVISION" in str(exc.value)


def test_security_against_arbitrary_code_execution():
    """Valide qu'aucun appel de fonction, import ou attribut n'est exécuté."""
    evaluator = ExactArithmeticEvaluator()

    forbidden_inputs = [
        "__import__('os').system('dir')",
        "eval('2+2')",
        "open('test.txt')",
        "[x for x in range(10)]",
        "lambda x: x + 1",
    ]
    for expr in forbidden_inputs:
        with pytest.raises(ArithmeticEvaluationError):
            evaluator.evaluate_expression(expr)


def test_proof_hash_determinism():
    """Valide que chaque calcul produit une empreinte de preuve déterministe."""
    evaluator = ExactArithmeticEvaluator()
    r1 = evaluator.evaluate_expression("42 * 17 + 8")
    r2 = evaluator.evaluate_expression("42 * 17 + 8")
    assert r1["result"] == 722
    assert r1["proof_hash"] == r2["proof_hash"]
    assert len(r1["proof_hash"]) == 64


def test_natural_language_expression_extraction():
    """Valide l'extraction d'expression depuis une requête en français ou anglais."""
    assert extract_arithmetic_expression("Combien font 42 * 17 + 8 ?") == "42 * 17 + 8"
    assert extract_arithmetic_expression("Calcule 125 * 8 - 45") == "125 * 8 - 45"
    assert extract_arithmetic_expression("What is 1000 / 25 ?") == "1000 / 25"
    assert extract_arithmetic_expression("Bonjour Brody") is None


def test_solve_arithmetic_query_end_to_end():
    """Valide la résolution complète d'une requête arithmétique utilisateur."""
    res = solve_arithmetic_query("Combien font 42 * 17 + 8 ?")
    assert res.reasoning_type == "ARITHMETIC"
    assert res.status == "SUCCESS"
    assert res.result_text == "Le résultat exact de 42 * 17 + 8 est 722."
    assert res.structured_payload["result"] == 722
    assert res.restitution_ready is True
    assert res.decision_authority == "KX108_ONLY"
    assert res.readonly is True
