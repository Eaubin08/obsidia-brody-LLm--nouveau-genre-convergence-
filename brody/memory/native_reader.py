"""
Obsidia native project-memory reader.

Pure readonly local retrieval over OBSIDIA_NATIVE_MEMORY_INDEX_V1.

Properties:
- local filesystem only
- no network
- no external retrieval service
- no memory write
- no canonical write
- no kernel/X108 mutation
- no ACT/verdict emission
- KX108 remains the sole decision authority

This module performs retrieval only.
It does not decide whether memory should be activated; MEMZUM owns that
cognitive activation upstream.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


import os
from brody.core.paths import BRODY_ROOT

_REPO_ROOT = BRODY_ROOT


def get_native_memory_index_path() -> Path:
    """Résout l'emplacement du fichier d'index mémoire natif de façon portable."""
    env_path = os.getenv("BRODY_NATIVE_MEMORY_INDEX_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    local_path = (
        BRODY_ROOT
        / "data"
        / "native_memory"
        / "OBSIDIA_NATIVE_MEMORY_INDEX_V1"
        / "obsidia_native_memory_records_v1.jsonl"
    )
    if local_path.is_file():
        return local_path
    sibling_path = (
        BRODY_ROOT.parent
        / "obsidia-brody"
        / "_obsidia_native_memory"
        / "OBSIDIA_NATIVE_MEMORY_INDEX_V1"
        / "obsidia_native_memory_records_v1.jsonl"
    )
    if sibling_path.is_file():
        return sibling_path
    return local_path


_DEFAULT_INDEX = get_native_memory_index_path()

_RECORD_SCHEMA = "OBSIDIA_NATIVE_MEMORY_RECORD_V1"

NATIVE_MEMORY_BOUNDARY: dict[str, Any] = {
    "readonly": True,
    "memory_authority": False,
    "memory_write": False,
    "canonical_write": False,
    "auto_promotion": False,
    "kernel_mutation": False,
    "x108_mutation": False,
    "emits_act": False,
    "emits_verdict": False,
    "allowed_to_decide": False,
    "allowed_to_act": False,
    "decision_authority": "KX108_ONLY",
}


def _fold_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(text or ""))
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Normalize dashes (en-dash, em-dash) to spaces/hyphens
    stripped = stripped.replace("–", "-").replace("—", "-")
    return stripped.lower()


def _normalize_query(query: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(query or "").replace("–", " ").replace("—", " ").strip().lower(),
    )


def _strip_intake_header(text: str) -> str:
    """Strip the # BRODY WORLD SOURCE INTAKE READONLY wrapper to expose real document content."""
    if not text:
        return ""
    raw = str(text)
    if "## Extracted text" in raw:
        raw = raw.split("## Extracted text", 1)[1]
    raw = re.sub(r"^\s*```[a-zA-Z0-9_-]*\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    return raw.strip()


def _safe_excerpt(
    text: str,
    max_chars: int = 1800,
) -> str:
    if not text:
        return ""

    cleaned = _strip_intake_header(str(text))
    return re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()[:max_chars]


def _validate_record(
    record: dict[str, Any],
    *,
    ordinal: int,
) -> None:
    if not isinstance(record, dict):
        raise ValueError(
            f"NATIVE_MEMORY_RECORD_NOT_OBJECT:{ordinal}"
        )

    if (
        record.get("schema_version")
        != _RECORD_SCHEMA
    ):
        raise ValueError(
            "NATIVE_MEMORY_SCHEMA_MISMATCH:"
            f"{ordinal}"
        )

    if record.get("readonly") is not True:
        raise ValueError(
            "NATIVE_MEMORY_NOT_READONLY:"
            f"{ordinal}"
        )

    if record.get("memory_write") is not False:
        raise ValueError(
            "NATIVE_MEMORY_WRITE_NOT_FALSE:"
            f"{ordinal}"
        )

    if (
        record.get("decision_authority")
        != "KX108_ONLY"
    ):
        raise ValueError(
            "NATIVE_MEMORY_AUTHORITY_VIOLATION:"
            f"{ordinal}"
        )

    forbidden_true = (
        "allowed_to_decide",
        "allowed_to_act",
        "kernel_mutation",
        "x108_mutation",
        "emits_act",
        "emits_verdict",
        "auto_promotion",
    )

    for key in forbidden_true:
        if record.get(key) is not False:
            raise ValueError(
                "NATIVE_MEMORY_BOUNDARY_VIOLATION:"
                f"{ordinal}:{key}"
            )


_DISTRIBUTED_CORPUS_SPECS: tuple[tuple[str, str, str, list[str]], ...] = (
    (
        "DIST-HIST-COMPRENDRE-OBSIDIA",
        "COMPRENDRE_OBSIDIA — Histoire, principes fondateurs, couches OS0..OS4 et gouvernance X-108",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\COMPRENDRE_OBSIDIA.md",
        ["obsidia", "histoire", "creation", "architecture", "cinq_os", "os0", "os1", "os2", "os3", "os4", "x108", "kx108", "brody"],
    ),
    (
        "DIST-HIST-README-COMPLET",
        "README_EXPLICATION_COMPLETE_PROJET — Synthèse globale Obsidia, composants et capacités",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\README.md",
        ["obsidia", "projet", "composition", "capacites", "architecture", "brody", "x108", "memoire"],
    ),
    (
        "DIST-HIST-ETAT-REEL-2026-09-15",
        "ETAT_REEL_2026_09_15 — État réel vérifié du projet Obsidia et jalons Septembre 2026",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\ETAT_REEL_2026_09_15.md",
        ["obsidia", "histoire", "dates", "etapes", "etat_reel", "septembre_2026", "jalons"],
    ),
    (
        "DIST-HIST-PACK-REPRISE-CHRONOLOGIE",
        "OBSIDIA_Pack_Reprise_Integral_Conversation_V1 — Chronologie intégrale d'Obsidia (Mars 2025 → Septembre 2026)",
        r"OBSIDIA_BACKUP_DISQUE_DUR_A_TRANSFERER\10_HISTORIQUE_PAR_DATE\01_RECENT_SEPTEMBRE_2026\08_AUTRES_BRANCHES_DOMAINES\OBSIDURE_REPRISE_6_PROBLEMES_2026-09-09\07_SOURCES_TRANSVERSALES\Downloads\OBSIDIA_Pack_Reprise_Integral_Conversation_V1.md",
        ["obsidia", "histoire", "creation", "chronologie", "dates", "etapes", "2025", "2026", "tableur_v7", "branche_149", "34_arbres"],
    ),
    (
        "DIST-HIST-RECOVERY-MASTER-REPORT",
        "RECOVERY_MASTER_REPORT — Rapport de récupération historique Obsidia (jalons R0/P2 Octobre 2026)",
        r"OBSIDIA_HISTORICAL_RECOVERY_MASTER\08_RAPPORTS\RECOVERY_MASTER_REPORT.md",
        ["obsidia", "histoire", "recovery_master", "chronologie", "etapes", "dates", "octobre_2026", "depots", "audit"],
    ),
    (
        "DIST-HIST-CROSS-MAPPING-V3",
        "CROSS_MAPPING_V3 — Cartographie croisée historique des dépôts, moteurs et preuves Obsidia",
        r"OBSIDIA_HISTORICAL_RECOVERY_MASTER\03_ANALYSES_HISTORIQUES\CROSS_MAPPING_V3.md",
        ["obsidia", "histoire", "depots", "audit", "cartographie", "cross_mapping", "architecture"],
    ),
    (
        "DIST-HIST-GENEALOGIE-CONCEPTUELLE",
        "GENEALOGIE_CONCEPTUELLE_TRACEABLE — Généalogie et jalons fondateurs 2025-2026 (AVDR Génération 1 Février-Mars 2026, X-108, Merkle)",
        r"OBSIDIA_HISTORICAL_RECOVERY_MASTER\ARCHIVE_STAGING_GITHUB_20261027\GENEALOGIE_CONCEPTUELLE_TRACEABLE.md",
        ["obsidia", "histoire", "genealogie", "avdr", "x108", "fevrier_2026", "mars_2026", "janvier_2026", "avril_2026", "merkle"],
    ),
    (
        "DIST-EDUC-EDUCATION-MD",
        "EDUCATION.md — Doctrine de l'éducation dans Obsidia : les 7 opérations, Oxygen vs Brody, croyances interdites D1/D2",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\EDUCATION.md",
        ["education", "brody", "oxygen", "entrainement", "naissance", "calibration", "maturation", "experience", "d1", "d2", "curriculum"],
    ),
    (
        "DIST-EDUC-14-CONTEXT-MEMORY",
        "14_CONTEXT_MEMORY_EDUCATION — Pack éducatif Brody V1 (7 modules), curriculum des 34 arbres et 8 types de leçons CIC",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\14_CONTEXT_MEMORY_EDUCATION.md",
        ["education", "brody", "pack_educatif", "curriculum", "34_arbres", "path_b", "cic", "lecons", "memoire"],
    ),
    (
        "DIST-OS-10-COGNITIVE-SYSTEM",
        "10_COGNITIVE_SYSTEM — Système cognitif Brody, couches OS, micro-core 14 signaux, 11 balances et sélecteur 21D",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\10_COGNITIVE_SYSTEM.md",
        ["cinq_os", "os0", "os1", "os2", "os3", "os4", "brody", "cognitif", "micro_core", "balances", "21d", "capacites_cognitives", "sens", "b6", "b7", "diagnostic", "incertitude"],
    ),
    (
        "DIST-OS-12-LANGUAGE-OS-TRAD-IR",
        "12_LANGUAGE_OS_TRAD_IR — Couches OS Trad (traduction langage humain → IR) et Reverse OS (structure → voix naturelle)",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\12_LANGUAGE_OS_TRAD_IR.md",
        ["cinq_os", "os_trad", "reverse_os", "os0", "os1", "os2", "os3", "os4", "ir", "langage", "sens", "b6", "b7", "incertitude", "capacites_cognitives", "diagnostic"],
    ),
    (
        "DIST-OS-25-OS3-PROOF-REPLAY",
        "25_OS3_PROOF_REPLAY_ATTESTATION — Couche OS3 : Audit formel, preuves Lean 4, TLA+, scellement Merkle et replay",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\25_OS3_PROOF_REPLAY_ATTESTATION.md",
        ["cinq_os", "os3", "preuve", "lean", "tla", "merkle", "audit", "replay", "attestation"],
    ),
    (
        "DIST-OS-TRAJETS-MD",
        "TRAJETS.md — Trajets d'exécution et de cognition à travers les couches OS0..OS4 et la porte X-108",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\TRAJETS.md",
        ["cinq_os", "os0", "os1", "os2", "os3", "os4", "trajets", "x108", "kx108", "architecture"],
    ),
    (
        "DIST-TOOLS-13-MCP-CONNECTORS",
        "13_MCP_TOOLS_CONNECTORS — Outils, connecteurs, registre d'outils et frontières d'exécution sur dépôts Git",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\13_MCP_TOOLS_CONNECTORS.md",
        ["outils", "git", "depots", "depot", "connecteurs", "mcp", "interdits", "audit", "readonly"],
    ),
    (
        "DIST-TOOLS-17-BOUNDARIES-ACTION",
        "17_BOUNDARIES_ACTION_INGRESS — Frontières d'action, outils autorisés en lecture seule vs mutations interdites sans X-108",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\17_BOUNDARIES_ACTION_INGRESS.md",
        ["outils", "git", "depots", "depot", "interdits", "boundaries", "action", "kx108", "readonly"],
    ),
    (
        "DIST-TOOLS-30-DEV-TOOLING-GIT",
        "30_DEV_TOOLING_CI_STAGING — Outillage de développement, dépôts Git, worktrees, audit en lecture seule et garde-fous",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\30_DEV_TOOLING_CI_STAGING.md",
        ["outils", "git", "depots", "depot", "worktrees", "audit", "staging", "interdits", "readonly"],
    ),
    (
        "DIST-TOOLS-SECURITE-MD",
        "SECURITE.md — Doctrine de sécurité Obsidia : séparation Brody readonly / KX108, interdictions de mutation directe",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\SECURITE.md",
        ["securite", "outils", "git", "depots", "interdits", "kx108", "x108", "readonly", "audit"],
    ),
    (
        "DIST-MATH-05-MATHEMATICS",
        "05_MATHEMATICS — Programme mathématique Obsidia / Obsidure : Navier–Stokes, Riemann, 6 problèmes du Millénaire et Lean 4",
        r"OBSIDIA_EXPLICATION_COMPLETE_PROJET\05_MATHEMATICS.md",
        ["navier", "stokes", "navier_stokes", "mathematiques", "millenaire", "obsidure", "riemann", "lean"],
    ),
    (
        "DIST-NS-CONVERSATION-RECOVERY-PASS-01",
        "NS_CONVERSATION_RECOVERY_AND_PASS_01 — Navier–Stokes 3D : bilan dyadique Littlewood-Paley, verrou NS_ANTI_PUMPING et passe NS-02",
        r"mat chexpoint ns\NS_CONVERSATION_RECOVERY_AND_PASS_01.md",
        ["navier", "stokes", "navier_stokes", "ns_anti_pumping", "anti_pumping", "littlewood_paley", "bony", "obsidure", "millenaire", "ns_02"],
    ),
    (
        "DIST-NS-GLOBAL-SURVIVOR-A147-A152",
        "NS_GLOBAL_SURVIVOR_A147_A152_COMPRESSION — Compression des survivants globaux A147–A152 et réfutation de la fermeture ODE circulaire",
        r"mat chexpoint ns\NS_GLOBAL_SURVIVOR_A147_A152_COMPRESSION.md",
        ["navier", "stokes", "navier_stokes", "a147", "a152", "survivor", "ode", "obsidure", "regularity"],
    ),
    (
        "DIST-NS-README-REPRISE-05",
        "05_NAVIER_STOKES/README_REPRISE — Statut réel BLOCKED (NS_NOT_PROVED_BY_PERSONAL_REGULARITY_ROUTE) et feuille de route Obsidure",
        r"OBSIDIA_BACKUP_DISQUE_DUR_A_TRANSFERER\10_HISTORIQUE_PAR_DATE\01_RECENT_SEPTEMBRE_2026\08_AUTRES_BRANCHES_DOMAINES\OBSIDURE_REPRISE_6_PROBLEMES_2026-09-09\05_NAVIER_STOKES\README_REPRISE.md",
        ["navier", "stokes", "navier_stokes", "blocked", "obsidure", "millenaire", "anti_pumping", "statut"],
    ),
    (
        "DIST-NS-CARD-OBSIDURE",
        "NAVIER_STOKES_CARD — Fiche canonique Navier–Stokes dans le pack Obsidure (équations, transfert HH/HL/LH, obstruction)",
        r"OBSIDIA_BACKUP_DISQUE_DUR_A_TRANSFERER\10_HISTORIQUE_PAR_DATE\01_RECENT_SEPTEMBRE_2026\08_AUTRES_BRANCHES_DOMAINES\OBSIDURE_REPRISE_6_PROBLEMES_2026-09-09\08_OBSIDURE\SUPPORTS\OBSIDUR_INPUT_V1_PACK.zip_EXTRAIT\NAVIER_STOKES_CARD.md",
        ["navier", "stokes", "navier_stokes", "obsidure", "vortex_stretching", "bony", "dissipation"],
    ),
    (
        "DIST-NS-CONTEXTE-REPRISE-MATH",
        "CONTEXTE_REPRISE_MACHINE_LISIBLE — État des 6 problèmes du Millénaire dans Obsidure (Navier–Stokes, Riemann, Yang–Mills, P vs NP, Hodge, BSD)",
        r"OBSIDIA_BACKUP_DISQUE_DUR_A_TRANSFERER\10_HISTORIQUE_PAR_DATE\01_RECENT_SEPTEMBRE_2026\08_AUTRES_BRANCHES_DOMAINES\OBSIDURE_REPRISE_6_PROBLEMES_2026-09-09\07_SOURCES_TRANSVERSALES\Downloads\Pack_Reprise_Obsidia_Mathematiques_2026-08-06.zip_EXTRAIT\Pack_Reprise_Obsidia_Mathematiques_2026-08-06\00_LIRE_EN_PREMIER\CONTEXTE_REPRISE_MACHINE_LISIBLE.md",
        ["navier", "stokes", "navier_stokes", "riemann", "millenaire", "obsidure", "mathematiques", "histoire"],
    ),
)

_MATH_MEMORY_REL_PATH = (
    r"obsidia-jarvis-advanced-integration-v0\periphery\obsidure_math_memory_readonly\MATH_MEMORY_INDEX.json"
)

_DEFAULT_INDEX_CACHE: tuple[int, list[dict[str, Any]]] | None = None


def _build_distributed_record(
    *,
    native_id: str,
    title: str,
    source_ref: str,
    text_excerpt: str,
    tags: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": _RECORD_SCHEMA,
        "native_id": native_id,
        "title": title,
        "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
        "source_ref": source_ref,
        "normalized_source_path": source_ref,
        "tags": list(tags),
        "text_excerpt": text_excerpt[:4500],
        **NATIVE_MEMORY_BOUNDARY,
    }


def _load_distributed_readonly_records() -> list[dict[str, Any]]:
    """
    Connect existing distributed readonly corpora across Desktop repositories
    into the in-memory native retrieval view without mutating the JSONL file.
    All records strictly obey _RECORD_SCHEMA and NATIVE_MEMORY_BOUNDARY.
    """
    extra: list[dict[str, Any]] = []

    for native_id, title, rel_path, tags in _DISTRIBUTED_CORPUS_SPECS:
        full_path = _DESKTOP_ROOT / rel_path
        if not full_path.exists():
            continue
        try:
            raw_text = full_path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if not raw_text:
            continue
        rec = _build_distributed_record(
            native_id=native_id,
            title=title,
            source_ref=rel_path.replace("\\", "/"),
            text_excerpt=raw_text,
            tags=tags,
        )
        _validate_record(rec, ordinal=len(extra))
        extra.append(rec)

    math_path = _DESKTOP_ROOT / _MATH_MEMORY_REL_PATH
    if math_path.exists():
        try:
            math_data = json.loads(math_path.read_text(encoding="utf-8"))
            items = math_data.get("items", []) if isinstance(math_data, dict) else []
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("id") or f"MATH_{idx}")
                nom = str(item.get("name") or item.get("nom") or item_id)
                formule = str(
                    item.get("human_definition")
                    or item.get("formal_definition_candidate")
                    or item.get("formule")
                    or ""
                )
                lean_sig = str(item.get("lean_signature_candidate") or "")
                explication = str(item.get("notes") or item.get("explication") or "")
                couche = str(item.get("type") or item.get("couche_obsidia") or "")
                domains_list = [str(d) for d in (item.get("related_domains") or [])]
                domaine = ", ".join(domains_list) or str(item.get("domaine") or "")
                statut = str(item.get("status") or item.get("statut") or "")
                mots_cles = [
                    str(k).lower()
                    for k in (
                        (item.get("mots_cles") or [])
                        + domains_list
                        + (item.get("related_metrics") or [])
                    )
                ]
                if "os0" in item_id.lower() or "os0" in explication.lower() or "os0" in formule.lower():
                    mots_cles.extend(["cinq_os", "5_os", "os0", "os1", "os2", "os3", "os4", "fractalite"])
                body = (
                    f"{nom} ({item_id}) — Type : {couche} | Domaines : {domaine} | Statut : {statut}.\n"
                    f"Définition : {formule}\n"
                    + (f"Signature Lean : {lean_sig}\n" if lean_sig else "")
                    + f"Notes : {explication}"
                )
                rec = _build_distributed_record(
                    native_id=f"DIST-MATH-{item_id}",
                    title=f"MATH_MEMORY_INDEX :: {item_id} — {nom}",
                    source_ref=f"{_MATH_MEMORY_REL_PATH.replace(chr(92), '/')}#{item_id}",
                    text_excerpt=body,
                    tags=list(dict.fromkeys(["math_memory", "obsidure"] + mots_cles)),
                )
                _validate_record(rec, ordinal=1000 + idx)
                extra.append(rec)
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    return extra


def load_native_memory_index(
    index_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Load and validate the native readonly project-memory index.
    When loading the default runtime index, also attaches the validated
    distributed readonly corpus records across the Obsidia repositories.
    """
    global _DEFAULT_INDEX_CACHE

    is_default = index_path is None
    path = (
        Path(index_path)
        if index_path is not None
        else _DEFAULT_INDEX
    )

    if not path.exists():
        raise FileNotFoundError(
            f"NATIVE_MEMORY_INDEX_NOT_FOUND:{path}"
        )

    if is_default:
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            mtime_ns = -1
        if _DEFAULT_INDEX_CACHE is not None and _DEFAULT_INDEX_CACHE[0] == mtime_ns:
            return [dict(r) for r in _DEFAULT_INDEX_CACHE[1]]

    records: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as fh:
        for ordinal, raw_line in enumerate(fh):
            if not raw_line.strip():
                continue

            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "NATIVE_MEMORY_INVALID_JSON:"
                    f"{ordinal}:{exc}"
                ) from exc

            _validate_record(
                record,
                ordinal=ordinal,
            )

            records.append(record)

    if is_default:
        existing_ids = {str(r.get("native_id") or "") for r in records}
        for dist_rec in _load_distributed_readonly_records():
            did = str(dist_rec.get("native_id") or "")
            if did and did not in existing_ids:
                records.append(dist_rec)
                existing_ids.add(did)

    ids = [
        str(record.get("native_id") or "")
        for record in records
    ]

    if any(not value for value in ids):
        raise ValueError(
            "NATIVE_MEMORY_EMPTY_NATIVE_ID"
        )

    if len(ids) != len(set(ids)):
        raise ValueError(
            "NATIVE_MEMORY_DUPLICATE_NATIVE_ID"
        )

    if is_default:
        try:
            _DEFAULT_INDEX_CACHE = (path.stat().st_mtime_ns, [dict(r) for r in records])
        except OSError:
            pass

    return records


_QUERY_TOKEN_STOPWORDS = frozenset({
    "dans", "depuis", "avec", "pour", "sans", "sous", "chez", "entre", "vers",
    "apres", "avant", "concernant", "explique", "raconte", "parle", "quels",
    "quelles", "quel", "quelle", "quoi", "comment", "pourquoi", "peux", "peut",
    "sont", "etre", "avoir", "faire", "fait", "plus", "moins", "tres", "bien",
    "trop", "tout", "tous", "toute", "toutes", "cette", "cet", "ces", "mais",
    "donc", "alors", "comme", "leurs", "leur", "notre", "votre", "meme",
})


def _extract_query_tokens(q_folded: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9][a-z0-9_-]*", q_folded)
    tokens: list[str] = []
    for tok in raw_tokens:
        tok = tok.strip("_-")
        if not tok or tok in _QUERY_TOKEN_STOPWORDS:
            continue
        if len(tok) >= 3 or any(ch.isdigit() for ch in tok) or tok in {"os", "ns", "ir"}:
            if tok not in tokens:
                tokens.append(tok)
            if "-" in tok:
                for sub in tok.split("-"):
                    if len(sub) >= 3 and sub not in _QUERY_TOKEN_STOPWORDS and sub not in tokens:
                        tokens.append(sub)
    return tokens


def _score_record(
    *,
    q_norm: str,
    q_underscore: str,
    record: dict[str, Any],
) -> int:
    """
    Preserve the proven historical ranking semantics over the native schema,
    augmented with accent-folded and multi-token co-occurrence scoring so
    multi-term natural queries retrieve specific corpus documents.

    Weights (exact phrase):
      title substring       +160
      source/path substring +150
      body substring        +120
      underscore tag        +130
      exact tag             +130
      tag substring         +100
      underscore substring  +100
    """

    title_raw = str(record.get("title") or "").lower()
    path_raw = str(record.get("source_ref") or "").lower()
    body_raw = _strip_intake_header(str(record.get("text_excerpt") or "")).lower()
    tags_raw = [str(tag).lower() for tag in (record.get("tags") or [])]

    title = _fold_text(title_raw)
    path = _fold_text(path_raw)
    body = _fold_text(body_raw)
    tags = [_fold_text(t) for t in tags_raw]

    q_folded = _fold_text(q_norm)
    q_under_folded = _fold_text(q_underscore)

    score = 0

    if q_norm in title_raw or (q_folded and q_folded in title):
        score += 160

    if q_norm in path_raw or (q_folded and q_folded in path):
        score += 150

    if q_norm in body_raw or (q_folded and q_folded in body):
        score += 120

    if q_underscore in tags_raw or (q_under_folded and q_under_folded in tags):
        score += 130

    if any(q_norm == tag for tag in tags_raw) or any(q_folded == tag for tag in tags):
        score += 130

    if any(q_norm in tag for tag in tags_raw) or any(q_folded in tag for tag in tags):
        score += 100

    if any(q_underscore in tag for tag in tags_raw) or any(q_under_folded in tag for tag in tags):
        score += 100

    # Multi-token scoring when query contains multiple words or specific terms
    tokens = _extract_query_tokens(q_folded)
    if len(tokens) >= 2 or (len(tokens) == 1 and score == 0):
        matched_tokens = 0
        token_score = 0
        # Give higher weight to specific domain tokens over the generic project name
        for tok in tokens:
            is_generic = tok in {"obsidia", "brody", "projet", "jarjar"}
            w_title = 15 if is_generic else 55
            w_tag = 15 if is_generic else 50
            w_path = 10 if is_generic else 35
            w_body = 10 if is_generic else 30

            tok_hit = False
            if tok in title:
                token_score += w_title
                tok_hit = True
            if any(tok == t or tok in t for t in tags):
                token_score += w_tag
                tok_hit = True
            if tok in path:
                token_score += w_path
                tok_hit = True
            if tok in body:
                token_score += w_body
                tok_hit = True
            if tok_hit:
                matched_tokens += 1

        # Require at least one non-generic token hit when non-generic tokens exist
        non_generic = [t for t in tokens if t not in {"obsidia", "brody", "projet", "jarjar"}]
        if non_generic:
            has_specific_hit = any(
                (t in title) or (t in path) or (t in body) or any(t in tag for tag in tags)
                for t in non_generic
            )
            if has_specific_hit:
                score += token_score
                if matched_tokens >= 2:
                    score += matched_tokens * 35
        else:
            score += token_score

    # ── Temporal window boost & non-period deprioritization ──
    q_is_jan = ("janvier" in q_folded or "2026-01" in q_folded or "spec 12" in q_folded)
    q_is_feb = ("fevrier" in q_folded or "2026-02" in q_folded)
    q_is_mar = ("mars" in q_folded or "2026-03" in q_folded or "x108 standard" in q_folded or "x108_standard" in q_folded)
    q_is_apr = ("avril" in q_folded or "2026-04" in q_folded or "p1 freeze" in q_folded or "p1_freeze" in q_folded)
    has_temporal_period = ("2026" in q_folded and (q_is_jan or q_is_feb or q_is_mar or q_is_apr)) or ("periode" in q_folded and "2026" in q_folded)
    is_exclusive = any(w in q_folded for w in ("uniquement", "seulement", "exclusivement", "ne repete pas", "ne répète pas", "sans repeter", "sans répéter"))

    if has_temporal_period:
        rec_combined = f"{title} {path} {body}"
        rec_jan = bool(re.search(r"\b(2026-01|202601\d{2}|janvier\s+2026|spec\s+12|p111_p113)\b", rec_combined))
        rec_feb = bool(re.search(r"\b(2026-02|202602\d{2}|fevrier\s+2026)\b", rec_combined))
        rec_mar = bool(re.search(r"\b(2026-03|202603\d{2}|mars\s+2026|x108_standard|standard\s+x-?108|integral_kernel_0_9_3)\b", rec_combined))
        rec_apr = bool(re.search(r"\b(2026-04|202604\d{2}|avril\s+2026|p1-freeze|p1_freeze|p2_roadmap|17blocs|audit_3_domains|rfc3161)\b", rec_combined))

        period_hit = (q_is_jan and rec_jan) or (q_is_feb and rec_feb) or (q_is_mar and rec_mar) or (q_is_apr and rec_apr) or (rec_jan or rec_mar or rec_apr)

        if period_hit:
            score += 280
        elif is_exclusive:
            if "pack_reprise" in rec_combined or "etat_reel_2026_09" in rec_combined or ("2025" in title and "2026" not in title):
                score = 0
            else:
                score = max(0, score - 160)

    return score


def query_native_memory(
    query: str,
    records: Iterable[dict[str, Any]] | None = None,
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """
    Query native memory using the parity-proven deterministic ranking.

    Empty queries fail closed and return no material.
    """

    q_norm = _normalize_query(query)

    if not q_norm:
        return []

    if limit <= 0:
        return []

    q_underscore = q_norm.replace(
        " ",
        "_",
    )

    material = (
        list(records)
        if records is not None
        else load_native_memory_index()
    )

    matched: list[
        tuple[int, dict[str, Any]]
    ] = []

    for record in material:
        score = _score_record(
            q_norm=q_norm,
            q_underscore=q_underscore,
            record=record,
        )

        if score > 0:
            matched.append(
                (score, record)
            )

    # Stable descending score ordering deliberately preserves index order
    # on equal scores, matching the parity-proven historical behavior.
    matched.sort(
        key=lambda item: -item[0]
    )

    q_folded = _fold_text(q_norm)
    has_temporal_multi_month = "2026" in q_folded and ("janvier" in q_folded or "fevrier" in q_folded) and ("avril" in q_folded or "mars" in q_folded)

    final_matched = matched[:limit]
    if has_temporal_multi_month and len(matched) > limit:
        has_jan = any("spec_12" in _fold_text(r.get("title") or "") or "2026-01" in _fold_text(f"{r.get('title')} {r.get('source_ref')}") for _, r in final_matched)
        has_mar = any("x108_standard" in _fold_text(r.get("title") or "") or "mars" in _fold_text(f"{r.get('title')} {r.get('source_ref')}") or "2026-03" in _fold_text(f"{r.get('title')} {r.get('source_ref')}") for _, r in final_matched)

        if not has_jan:
            jan_cand = next(((s, r) for s, r in matched[limit:] if "spec_12" in _fold_text(r.get("title") or "") or "2026-01" in _fold_text(f"{r.get('title')} {r.get('source_ref')}")), None)
            if jan_cand:
                final_matched = final_matched[:-1] + [jan_cand]
        if not has_mar:
            mar_cand = next(((s, r) for s, r in matched[limit:] if "x108_standard" in _fold_text(r.get("title") or "") or "mars" in _fold_text(f"{r.get('title')} {r.get('source_ref')}") or "2026-03" in _fold_text(f"{r.get('title')} {r.get('source_ref')}")), None)
            if mar_cand:
                final_matched = final_matched[:-1] + [mar_cand]

    items: list[dict[str, Any]] = []

    for rank, (score, record) in enumerate(
        final_matched,
        1,
    ):
        tags = list(
            record.get("tags") or []
        )

        excerpt = _safe_excerpt(
            record.get("text_excerpt") or "",
            max_chars=1800,
        )

        source_ref = str(
            record.get("source_ref") or ""
        )

        path = str(
            record.get("normalized_source_path")
            or source_ref
        )

        items.append({
            "rank": rank,
            "id": record.get("native_id"),
            "title": record.get("title", ""),
            "source": (
                record.get("source_type")
                or "OBSIDIA_NATIVE_MEMORY_V1"
            ),
            "path": path,
            "tags": tags,
            "score": score,
            "excerpt": excerpt,
            "source_ref": source_ref,

            # Explicitly retain non-sovereignty on each surfaced item.
            "readonly": True,
            "memory_write": False,
            "emits_act": False,
            "decision_authority": "KX108_ONLY",
        })

    return items


def build_native_memory_retrieval_snapshot(
    query: str,
    *,
    memory_required: bool,
    limit: int = 8,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Build the provider-neutral readonly retrieval envelope.

    MEMZUM decides `memory_required` upstream.
    This function only obeys that activation signal.
    """

    base: dict[str, Any] = {
        "schema_version": (
            "OBSIDIA_NATIVE_MEMORY_RETRIEVAL_V1"
        ),
        "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
        "query": str(query or ""),
        "query_normalized": _normalize_query(query),
        "memory_required": bool(memory_required),
        "selected_items_count": 0,
        "selected_items": [],
        "index_record_count": 0,
        **NATIVE_MEMORY_BOUNDARY,
    }

    if not memory_required:
        return {
            **base,
            "status": "MEMORY_NOT_REQUIRED",
            "material_quality": "NOT_REQUIRED",
        }

    if not base["query_normalized"]:
        return {
            **base,
            "status": "MEMORY_REQUIRED_EMPTY_QUERY",
            "material_quality": "NO_MATERIAL",
        }

    try:
        records = load_native_memory_index(
            index_path=index_path,
        )
    except FileNotFoundError:
        return {
            **base,
            "status": "MEMORY_REQUIRED_NO_NATIVE_SOURCE",
            "material_quality": "NO_MATERIAL",
        }
    except (ValueError, OSError):
        return {
            **base,
            "status": "MEMORY_REQUIRED_INVALID_NATIVE_SOURCE",
            "material_quality": "NO_MATERIAL",
        }

    items = query_native_memory(
        query,
        records,
        limit=limit,
    )

    if not items:
        return {
            **base,
            "status": "MEMORY_REQUIRED_EMPTY",
            "material_quality": "NO_MATERIAL",
            "index_record_count": len(records),
        }

    return {
        **base,
        "status": "MEMORY_USABLE",
        "material_quality": "USABLE_MATERIAL",
        "selected_items_count": len(items),
        "selected_items": items,
        "index_record_count": len(records),
    }


__all__ = [
    "NATIVE_MEMORY_BOUNDARY",
    "load_native_memory_index",
    "query_native_memory",
    "build_native_memory_retrieval_snapshot",
]
