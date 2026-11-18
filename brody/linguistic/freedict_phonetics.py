"""Verified FreeDict French pronunciations and conservative IPA candidates.

The pinned historical TEI does not declare per-entry notation. FreeDict's
project documentation specifies IPA, so decoding is explicitly conditional;
raw text, provenance, and unresolved symbols are always retained.
"""
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET


SCHEMA = 'BRODY_P6_FREEDICT_PRONUNCIATIONS_V1'
SOURCE_ID = 'freedict_fra_eng'
SOURCE_URL = 'https://raw.githubusercontent.com/freedict/fd-dictionaries/master/fra-eng/fra-eng.tei'
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
TEI_NS = 'http://www.tei-c.org/ns/1.0'
PINNED_SHA256 = 'de9eb6e5756d994bca9bdb2a91bfc2bb8d8822d3387f5a3b586acc8d42133114'
FREEDICT_IPA_DOC = (
    'https://github.com/freedict/fd-dictionaries/wiki/'
    'FreeDict-HOWTO-%E2%80%93-Writing-Text-Encoding-Initiative-XML-Files')
IPA_CHART_2015 = (
    'https://www.internationalphoneticassociation.org/IPAcharts/common_files/pdfs/'
    'pdfs_IPA_charts_HHD/IPA_chart_HHD_2015.pdf')

# IPA chart descriptions. The two graphemes g/ɡ share a documented value but
# remain distinct in the returned evidence. No spelling is canonicalized.
IPA_SYMBOL_DESCRIPTIONS = {
    'a': 'open front unrounded vowel',
    'b': 'voiced bilabial plosive',
    'c': 'voiceless palatal plosive',
    'd': 'voiced alveolar plosive',
    'e': 'close-mid front unrounded vowel',
    'ɛ': 'open-mid front unrounded vowel',
    'f': 'voiceless labiodental fricative',
    'g': 'voiced velar plosive',
    'ɡ': 'voiced velar plosive',
    'i': 'close front unrounded vowel',
    'j': 'palatal approximant',
    'k': 'voiceless velar plosive',
    'l': 'alveolar lateral approximant',
    'm': 'bilabial nasal',
    'n': 'alveolar nasal',
    'ɲ': 'palatal nasal',
    'ŋ': 'velar nasal',
    'o': 'close-mid back rounded vowel',
    'ɔ': 'open-mid back rounded vowel',
    'œ': 'open-mid front rounded vowel',
    'p': 'voiceless bilabial plosive',
    'r': 'alveolar trill',
    's': 'voiceless alveolar fricative',
    't': 'voiceless alveolar plosive',
    'u': 'close back rounded vowel',
    'v': 'voiced labiodental fricative',
    'w': 'voiced labial-velar approximant',
    'y': 'close front rounded vowel',
    'z': 'voiced alveolar fricative',
    'ɑ': 'open back unrounded vowel',
    'ə': 'mid-central vowel',
    'ɚ': 'rhotic mid-central vowel',
    'ɥ': 'voiced labial-palatal approximant',
    'ø': 'close-mid front rounded vowel',
    'ʀ': 'voiced uvular trill',
    'ʃ': 'voiceless postalveolar fricative',
    'ʒ': 'voiced postalveolar fricative',
}
IPA_VOWEL_SYMBOLS = frozenset(
    'aeiouyɛɔœɑəɚø')
DOCUMENTED_MARKS = {
    '\u0303': 'nasalized (combining tilde; attaches only to an immediately preceding IPA vowel)',
    'ˈ': 'primary stress marker (suprasegmental; not a phoneme)',
}
UNDEFINED_MARKS = {
    '(': 'parenthesized material; this FreeDict edition does not document its semantics',
    ')': 'parenthesized material; this FreeDict edition does not document its semantics',
}
AMBIGUOUS_MARKS = {
    '.': 'IPA chart uses a period as syllable break, but source occurrence is an ellipsis',
    ' ': 'source separator in the ellipsis expression; not an IPA segment',
}


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _text(element):
    return ' '.join(''.join(element.itertext()).split()) if element is not None else ''


def _find_child(parent, name):
    return next((child for child in list(parent) if _local(child.tag) == name), None)


def _find_all(parent, name):
    return [child for child in list(parent) if _local(child.tag) == name]


def _explicit_language(element, parents):
    current = element
    while current is not None:
        value = current.attrib.get(XML_LANG)
        if value:
            return value.split('-', 1)[0].lower()
        current = parents.get(current)
    return None


def _source_metadata(source):
    required = ('id', 'lang', 'url', 'filename', 'bytes', 'sha256', 'license', 'source')
    if not isinstance(source, dict) or any(not source.get(key) for key in required):
        raise ValueError('P6_FREEDICT_PROVENANCE_MISSING')
    if source['id'] != SOURCE_ID or source['lang'] != 'fr' or source['url'] != SOURCE_URL:
        raise ValueError('P6_FREEDICT_SOURCE_IDENTITY_MISMATCH')
    if source['filename'] != 'freedict_fra_eng.tei' or source['license'] != 'GPL v2+':
        raise ValueError('P6_FREEDICT_SOURCE_IDENTITY_MISMATCH')
    if type(source['bytes']) is not int or source['bytes'] <= 0:
        raise ValueError('P6_FREEDICT_PROVENANCE_MISSING')
    if not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
        raise ValueError('P6_FREEDICT_PROVENANCE_MISSING')
    return {key: source[key] for key in required}


def extract_freedict_pronunciations(path, source):
    """Verify a manifest-pinned TEI file, then extract raw French ``<pron>`` data.

    Each record is tied to a TEI entry and form. Multiple spellings in one form
    are kept as lemma candidates and are not cross-paired with pronunciations.
    A missing ``xml:lang`` inherits French only from the pinned ``fra-eng``
    source direction; explicit non-French entries are excluded and counted.
    """
    metadata = _source_metadata(source)
    path = Path(path)
    observed_sha = _sha256(path)
    if observed_sha != metadata['sha256']:
        raise ValueError('HOLD_SOURCE_MISMATCH')
    if path.stat().st_size != metadata['bytes']:
        raise ValueError('HOLD_SOURCE_MISMATCH')
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError('P6_FREEDICT_XML_INVALID') from exc
    if _local(root.tag) != 'TEI' or not root.tag.startswith('{' + TEI_NS + '}'):
        raise ValueError('P6_FREEDICT_TEI_ROOT_INVALID')

    header = next((node for node in root.iter() if _local(node.tag) == 'teiHeader'), None)
    header_text = _text(header)
    edition = _find_child(next((n for n in header.iter() if _local(n.tag) == 'editionStmt'), header), 'edition') if header is not None else None
    date = next((node for node in header.iter() if _local(node.tag) == 'date'), None) if header is not None else None
    version = _text(edition) or None
    source_date = date.attrib.get('when') if date is not None else None
    if not version:
        match = re.search(r'\b(\d+\.\d+(?:\.\d+)?)\b', header_text)
        version = match.group(1) if match else None

    records = []
    lexical_forms = []
    entries = [node for node in root.iter() if _local(node.tag) == 'entry']
    parents = {child: parent for parent in root.iter() for child in list(parent)}
    stats = Counter()
    pron_counts_by_lemma = defaultdict(Counter)
    for entry_index, entry in enumerate(entries, 1):
        explicit_lang = _explicit_language(entry, parents)
        if explicit_lang and explicit_lang != 'fr':
            stats['non_french_entries'] += 1
            continue
        stats['french_entries'] += 1
        entry_ref = entry.attrib.get('{http://www.w3.org/XML/1998/namespace}id') or f'entry:{entry_index:06d}'
        forms = _find_all(entry, 'form')
        senses = _find_all(entry, 'sense')
        if len(senses) > 1:
            stats['entries_with_multiple_senses'] += 1
        if not forms:
            stats['entries_without_form'] += 1
        for form_index, form in enumerate(forms, 1):
            form_lang = _explicit_language(form, parents)
            if form_lang and form_lang != 'fr':
                stats['non_french_forms'] += 1
                continue
            lemmas = [_text(node) for node in _find_all(form, 'orth')]
            lemmas = [lemma for lemma in lemmas if lemma]
            if not lemmas:
                stats['forms_without_lemma'] += 1
            form_ref = f'{entry_ref}/form:{form_index}'
            sense_refs = [sense.attrib.get('{http://www.w3.org/XML/1998/namespace}id') or
                          f'{entry_ref}/sense:{i}' for i, sense in enumerate(senses, 1)]
            lexical_form = {
                'lemma_candidates': list(lemmas),
                'language': 'fr',
                'source_id': metadata['id'],
                'source_version': version,
                'source_date': source_date,
                'source_sha256': observed_sha,
                'source_url': metadata['url'],
                'license': metadata['license'],
                'entry_ref': entry_ref,
                'entry_position': entry_index,
                'form_ref': form_ref,
                'sense_refs': list(sense_refs),
                'pronunciation_variant_refs': [],
                'pronunciation_status': 'PHONETIC_UNRESOLVED',
                'verification_status': 'SOURCE_SHA256_VERIFIED_NOTATION_UNVALIDATED',
            }
            lexical_forms.append(lexical_form)
            pronunciations = _find_all(form, 'pron')
            if not pronunciations:
                stats['forms_without_pronunciation'] += 1
            for pron_index, pron in enumerate(pronunciations, 1):
                pron_lang = _explicit_language(pron, parents)
                if pron_lang and pron_lang != 'fr':
                    stats['non_french_pronunciations'] += 1
                    continue
                raw_source_text = ''.join(pron.itertext())
                pronunciation = ' '.join(raw_source_text.split())
                if not pronunciation:
                    stats['empty_pronunciations'] += 1
                    continue
                if len(lemmas) != 1:
                    stats['ambiguous_lemma_pronunciation_bindings'] += 1
                notation = pron.attrib.get('notation') or pron.attrib.get('type')
                stats['notation_declared' if notation else 'notation_unspecified'] += 1
                lemma = lemmas[0] if len(lemmas) == 1 else None
                record = {
                    'lemma': lemma,
                    'lemma_candidates': list(lemmas),
                    'language': 'fr',
                    'pronunciation': pronunciation,
                    'raw_pronunciation': raw_source_text,
                    'notation': notation,
                    'notation_status': 'DECLARED_UNINTERPRETED' if notation else 'NOT_DECLARED_IN_SOURCE',
                    'source_id': metadata['id'],
                    'source_version': version,
                    'source_date': source_date,
                    'source_sha256': observed_sha,
                    'source_url': metadata['url'],
                    'license': metadata['license'],
                    'entry_ref': entry_ref,
                    'entry_position': entry_index,
                    'form_ref': form_ref,
                    'variant_ref': f'{entry_ref}/form:{form_index}/pron:{pron_index}',
                    'sense_refs': list(sense_refs),
                    'confidence': None,
                    'verification_status': 'SOURCE_SHA256_VERIFIED_NOTATION_UNVALIDATED',
                }
                records.append(record)
                lexical_form['pronunciation_variant_refs'].append(record['variant_ref'])
                lexical_form['pronunciation_status'] = 'SOURCE_PRONUNCIATIONS_AVAILABLE'
                if lemma is not None:
                    pron_counts_by_lemma[lemma][pronunciation] += 1
                stats['pronunciation_records'] += 1
        if forms and not any(_find_all(form, 'pron') for form in forms):
            stats['entries_without_pronunciation'] += 1

    stats['entries_total'] = len(entries)
    stats['unique_lemmas_with_pronunciation'] = len(pron_counts_by_lemma)
    stats['lemmas_with_multiple_distinct_pronunciations'] = sum(
        len(values) > 1 for values in pron_counts_by_lemma.values())
    stats['duplicate_pronunciation_records_beyond_unique_lemma_value'] = sum(
        sum(max(0, count - 1) for count in values.values()) for values in pron_counts_by_lemma.values())
    stats['unbound_pronunciation_records'] = sum(record['lemma'] is None for record in records)
    return {
        'schema': SCHEMA,
        'integrity_status': 'SOURCE_SHA256_VERIFIED',
        'source': {**metadata, 'sha256_observed': observed_sha, 'version': version,
                   'date': source_date, 'format': 'TEI_P5', 'notation_policy': 'SOURCE_UNSPECIFIED_PRESERVED'},
        'coverage': dict(sorted(stats.items())),
        'records': records,
        'lexical_forms': lexical_forms,
    }


def lookup_freedict_pronunciations(extraction, lemma):
    """Return exact-case lemma matches without merging entries or senses."""
    if (not isinstance(extraction, dict) or extraction.get('schema') != SCHEMA or
            extraction.get('integrity_status') != 'SOURCE_SHA256_VERIFIED' or
            not isinstance(lemma, str) or not lemma or lemma != lemma.strip()):
        raise ValueError('P6_FREEDICT_LOOKUP_INVALID')
    return [record.copy() for record in extraction['records']
            if record['lemma'] == lemma and record['language'] == 'fr']


def lookup_freedict_lexical_forms(extraction, lemma):
    """Return exact-case French TEI form matches, including forms without pronunciation."""
    if (not isinstance(extraction, dict) or extraction.get('schema') != SCHEMA or
            extraction.get('integrity_status') != 'SOURCE_SHA256_VERIFIED' or
            extraction.get('source', {}).get('sha256_observed') != PINNED_SHA256 or
            not isinstance(lemma, str) or not lemma or lemma != lemma.strip()):
        raise ValueError('P6_FREEDICT_LOOKUP_INVALID')
    return [form.copy() for form in extraction.get('lexical_forms', [])
            if form.get('language') == 'fr' and lemma in form.get('lemma_candidates', [])]


def _notation_status(record):
    declared = record.get('notation')
    return {
        'system': 'IPA',
        'status': ('RECORD_DECLARED_IPA_HISTORICAL_CONFORMANCE_UNVERIFIED'
                   if isinstance(declared, str) and declared.upper() == 'IPA'
                   else 'PROJECT_DOCUMENTED_HISTORICAL_CONFORMANCE_UNVERIFIED'),
        'documentation': FREEDICT_IPA_DOC,
        'chart': IPA_CHART_2015,
        'basis': 'Official FreeDict HOWTO declares IPA for <pron>; this 0.4.1 source has no per-entry notation and records historical MBRODICT origin.',
    }


def _decoding_provenance(record):
    keys = ('lemma', 'language', 'notation', 'source_id', 'source_version',
            'source_date', 'source_sha256', 'source_url', 'license',
            'entry_ref', 'form_ref', 'variant_ref', 'sense_refs')
    result = {key: record.get(key) for key in keys}
    if isinstance(result.get('sense_refs'), list):
        result['sense_refs'] = list(result['sense_refs'])
    return result


def build_freedict_notation_inventory(extraction):
    """Count the verified TEI text content (including source whitespace)."""
    if (not isinstance(extraction, dict) or extraction.get('schema') != SCHEMA or
            extraction.get('integrity_status') != 'SOURCE_SHA256_VERIFIED' or
            extraction.get('source', {}).get('sha256_observed') != PINNED_SHA256):
        raise ValueError('P6_FREEDICT_INVENTORY_SOURCE_INVALID')
    counts = Counter()
    examples = defaultdict(list)
    raw_differences = 0
    total_codepoints = 0
    for record in extraction['records']:
        raw = record.get('raw_pronunciation')
        if not isinstance(raw, str):
            raise ValueError('P6_FREEDICT_RAW_PRONUNCIATION_MISSING')
        if raw != record.get('pronunciation'):
            raw_differences += 1
        total_codepoints += len(raw)
        for symbol in raw:
            counts[symbol] += 1
            if len(examples[symbol]) < 4 and record.get('lemma') not in examples[symbol]:
                examples[symbol].append(record.get('lemma'))
    rows = []
    for symbol, count in sorted(counts.items(), key=lambda pair: (-pair[1], ord(pair[0]))):
        if symbol in IPA_SYMBOL_DESCRIPTIONS:
            meaning, status, category = IPA_SYMBOL_DESCRIPTIONS[symbol], 'DOCUMENTED', 'IPA_SEGMENT_SYMBOL'
        elif symbol in DOCUMENTED_MARKS:
            meaning, status, category = DOCUMENTED_MARKS[symbol], 'DOCUMENTED', 'IPA_MARK'
        elif symbol in AMBIGUOUS_MARKS:
            meaning, status, category = AMBIGUOUS_MARKS[symbol], 'AMBIGUOUS', 'SOURCE_FORMATTING'
        elif symbol in UNDEFINED_MARKS:
            meaning, status, category = UNDEFINED_MARKS[symbol], 'UNDEFINED', 'UNSPECIFIED_SOURCE_MARK'
        else:
            meaning, status, category = None, 'UNDEFINED', 'UNMAPPED_SYMBOL'
        rows.append(dict(symbol=symbol, codepoint=f'U+{ord(symbol):04X}',
            unicode_name=unicodedata.name(symbol, '<UNNAMED>'), category=unicodedata.category(symbol),
            occurrences=count, meaning=meaning, status=status, category_role=category,
            examples=examples[symbol]))
    combining_context = Counter()
    invalid_combining = []
    decoding_statuses = Counter()
    for record in extraction['records']:
        raw = record['raw_pronunciation']
        decoding_statuses[decode_freedict_pronunciation(record)['status']] += 1
        for index, symbol in enumerate(raw):
            if symbol != '\u0303':
                continue
            base = raw[index - 1] if index else None
            if base in IPA_VOWEL_SYMBOLS:
                combining_context[base] += 1
            else:
                invalid_combining.append(dict(lemma=record.get('lemma'), raw=raw,
                    codepoint_index=index, preceding_symbol=base))
    return dict(source_sha256=PINNED_SHA256, census_scope='resolved TEI character data in raw_pronunciation; one observation per <pron> occurrence; XML markup is not counted',
        pronunciation_count=len(extraction['records']), total_codepoints=total_codepoints,
        unique_codepoints=len(rows), unique_pronunciation_strings=len({r['raw_pronunciation'] for r in extraction['records']}),
        records_differing_from_p6e_normalized_field=raw_differences,
        symbol_rows=rows, combining_tilde_context=dict(sorted(combining_context.items())),
        invalid_combining_marks=invalid_combining,
        decoder_status_counts=dict(sorted(decoding_statuses.items())))


def decode_freedict_pronunciation(record):
    """Decode chart-defined IPA symbols as candidates; never normalize glyphs.

    The project documents IPA, but this historical MBRODICT-derived file does
    not declare notation per record. Ambiguous punctuation and undefined marks
    block a whole-string result while leaving recognized segments available.
    """
    if not isinstance(record, dict):
        raise ValueError('P6_F_INVALID_PRONUNCIATION_RECORD')
    if (record.get('source_id') != SOURCE_ID or record.get('language') != 'fr' or
            record.get('source_sha256') != PINNED_SHA256 or record.get('source_version') != '0.4.1' or
            record.get('verification_status') != 'SOURCE_SHA256_VERIFIED_NOTATION_UNVALIDATED'):
        raise ValueError('P6_F_SOURCE_PROVENANCE_INVALID')
    declared_notation = record.get('notation')
    if declared_notation is not None and (
            not isinstance(declared_notation, str) or declared_notation.upper() != 'IPA'):
        return dict(schema='BRODY_P6_F_IPA_DECODING_V1',
            raw_pronunciation=record.get('raw_pronunciation'),
            provenance=_decoding_provenance(record),
            documented_notation=dict(system=None, status='DECLARED_NOTATION_UNSUPPORTED',
                declared_value=declared_notation), decoded_phonemes=[], stress_markers=[],
            unresolved_symbols=[], status='UNRESOLVED', terminal_segment_candidate=None,
            uncertainty=['DECLARED_NOTATION_HAS_NO_VERIFIED_DECODER'])
    raw = record.get('raw_pronunciation')
    if not isinstance(raw, str) or not raw:
        return dict(schema='BRODY_P6_F_IPA_DECODING_V1', raw_pronunciation=raw,
            provenance=_decoding_provenance(record),
            documented_notation=_notation_status(record), decoded_phonemes=[], stress_markers=[],
            unresolved_symbols=[], status='UNRESOLVED', terminal_segment_candidate=None,
            uncertainty=['RAW_TEI_PRONUNCIATION_UNAVAILABLE'])
    segments = []
    stresses = []
    unresolved = []
    for index, symbol in enumerate(raw):
        if symbol in IPA_SYMBOL_DESCRIPTIONS:
            segments.append(dict(symbol=symbol, ipa_value=IPA_SYMBOL_DESCRIPTIONS[symbol],
                modifiers=[], source_codepoint=f'U+{ord(symbol):04X}', raw_index=index))
            continue
        if symbol == '\u0303':
            if (segments and segments[-1]['raw_index'] == index - 1 and
                    segments[-1]['symbol'] in IPA_VOWEL_SYMBOLS and
                    'nasalized' not in segments[-1]['modifiers']):
                segments[-1]['modifiers'].append('nasalized')
                segments[-1]['raw_symbol'] = segments[-1].get('raw_symbol', segments[-1]['symbol']) + symbol
            else:
                unresolved.append(dict(symbol=symbol, codepoint=f'U+{ord(symbol):04X}', index=index,
                    status='UNDEFINED', reason='COMBINING_TILDE_NOT_IMMEDIATELY_AFTER_A_SINGLE_ALLOWED_VOWEL'))
            continue
        if symbol == 'ˈ':
            stresses.append(dict(symbol=symbol, codepoint=f'U+{ord(symbol):04X}',
                before_segment_index=len(segments), meaning='primary stress'))
            continue
        if symbol in AMBIGUOUS_MARKS:
            unresolved.append(dict(symbol=symbol, codepoint=f'U+{ord(symbol):04X}', index=index,
                status='AMBIGUOUS', reason=AMBIGUOUS_MARKS[symbol]))
            continue
        reason = UNDEFINED_MARKS.get(symbol, 'No documented IPA mapping in the verified registry.')
        unresolved.append(dict(symbol=symbol, codepoint=f'U+{ord(symbol):04X}', index=index,
            status='UNDEFINED', reason=reason))
    status = 'DECODED_CANDIDATE' if segments and not unresolved else ('PARTIAL' if segments else 'UNRESOLVED')
    terminal = None
    if status == 'DECODED_CANDIDATE':
        terminal = {key: value for key, value in segments[-1].items() if key != 'raw_index'}
    return dict(schema='BRODY_P6_F_IPA_DECODING_V1', raw_pronunciation=raw,
        provenance=_decoding_provenance(record),
        normalized_pronunciation=record.get('pronunciation'), documented_notation=_notation_status(record),
        decoded_phonemes=segments, stress_markers=stresses, unresolved_symbols=unresolved,
        status=status, terminal_segment_candidate=terminal,
        comparison_stress_policy='FULL_SEQUENCE_COMPARISON_PRESERVES_STRESS_MARKERS; SINGLE_TERMINAL_SEGMENT_COMPARISON_DOES_NOT_ASSIGN_STRESS_TO_A_SYLLABLE',
        uncertainty=['PROJECT_LEVEL_IPA_CONVENTION_DOCUMENTED', 'HISTORICAL_RECORD_CONFORMANCE_NOT_INDEPENDENTLY_VERIFIED',
            'PHONEMIC_CANDIDATES_ONLY_NOT_AUDIO_VERIFIED', 'NO_SYLLABLE_OR_METRIC_BOUNDARIES_INFERRED'])


def compare_freedict_sound_candidates(left, right):
    """Compare decoded candidates, not speech, French rhyme, or meter."""
    if (not isinstance(left, dict) or not isinstance(right, dict) or
            left.get('schema') != 'BRODY_P6_F_IPA_DECODING_V1' or
            right.get('schema') != 'BRODY_P6_F_IPA_DECODING_V1'):
        raise ValueError('P6_F_COMPARISON_INPUT_INVALID')
    if left.get('status') != 'DECODED_CANDIDATE' or right.get('status') != 'DECODED_CANDIDATE':
        return dict(status='UNRESOLVED', sequence_equal=None, terminal_segment_equal=None,
            reason='BOTH_PRONUNCIATIONS_REQUIRE_COMPLETE_UNAMBIGUOUS_DECODING')
    def sequence_key(decoded):
        return (tuple((segment['symbol'], tuple(segment['modifiers']))
                      for segment in decoded['decoded_phonemes']),
                tuple(marker['before_segment_index'] for marker in decoded['stress_markers']))
    left_source = left['documented_notation']
    right_source = right['documented_notation']
    if left_source.get('system') != right_source.get('system'):
        return dict(status='UNRESOLVED', sequence_equal=None, terminal_segment_equal=None,
            reason='NOTATION_SYSTEMS_DIFFER')
    left_terminal = left['terminal_segment_candidate']
    right_terminal = right['terminal_segment_candidate']
    terminal_equal = ((left_terminal['symbol'], tuple(left_terminal['modifiers'])) ==
                      (right_terminal['symbol'], tuple(right_terminal['modifiers'])))
    return dict(status='CANDIDATE_SYMBOL_COMPARISON',
        sequence_equal=sequence_key(left) == sequence_key(right), terminal_segment_equal=terminal_equal,
        terminal_comparison='FINAL_IPA_SEGMENT_EQUALITY_ONLY',
        comparison_stress_policy='FULL_SEQUENCE_PRESERVES_STRESS_MARKERS; TERMINAL_SEGMENT_COMPARISON_EXCLUDES_STRESS_WITHOUT_ASSIGNING_SYLLABLE',
        rhyme_established=False, meter_established=False, speech_verified=False,
        uncertainty=['HISTORICAL_NOTATION_CONFORMANCE_UNVERIFIED', 'SYMBOL_SEQUENCE_COMPARISON_IS_NOT_RHYME'])


def compare_freedict_variant_sets(left_decodings, right_decodings):
    """Retain all alternative pairings and refuse a verdict if they conflict."""
    if (not isinstance(left_decodings, (list, tuple)) or not left_decodings or
            not isinstance(right_decodings, (list, tuple)) or not right_decodings):
        raise ValueError('P6_F_VARIANT_SET_EMPTY')
    pairs = [compare_freedict_sound_candidates(left, right)
             for left in left_decodings for right in right_decodings]
    if any(pair['status'] != 'CANDIDATE_SYMBOL_COMPARISON' for pair in pairs):
        return dict(status='UNRESOLVED', comparisons=pairs, sequence_equal=None,
            terminal_segment_equal=None, reason='ONE_OR_MORE_ALTERNATIVES_UNRESOLVED')
    sequence_values = {pair['sequence_equal'] for pair in pairs}
    terminal_values = {pair['terminal_segment_equal'] for pair in pairs}
    conflict = len(sequence_values) > 1 or len(terminal_values) > 1
    return dict(status='AMBIGUOUS_VARIANTS' if conflict else 'CANDIDATE_SYMBOL_COMPARISON',
        comparisons=pairs, sequence_equal=(None if conflict else next(iter(sequence_values))),
        terminal_segment_equal=(None if conflict else next(iter(terminal_values))),
        reason='ALTERNATIVE_COMPARISONS_CONFLICT' if conflict else None,
        rhyme_established=False, meter_established=False, speech_verified=False)


def bind_freedict_pronunciations(extraction, lemma_bindings):
    """Prepare explicit line-to-lemma bindings; this performs no tokenization."""
    if (not isinstance(extraction, dict) or extraction.get('schema') != SCHEMA or
            extraction.get('integrity_status') != 'SOURCE_SHA256_VERIFIED' or
            not isinstance(lemma_bindings, (list, tuple)) or len(lemma_bindings) > 512):
        raise ValueError('P6_FREEDICT_BINDING_INVALID')
    source = extraction.get('source')
    if not isinstance(source, dict) or source.get('sha256_observed') != source.get('sha256'):
        raise ValueError('P6_FREEDICT_BINDING_INVALID')
    bindings = []
    selected = {}
    seen = set()
    for binding in lemma_bindings:
        if (not isinstance(binding, dict) or not isinstance(binding.get('line_ref'), str) or
                not binding['line_ref'] or not isinstance(binding.get('lemma'), str) or
                not binding['lemma'] or binding['lemma'] != binding['lemma'].strip()):
            raise ValueError('P6_FREEDICT_BINDING_INVALID')
        key = (binding['line_ref'], binding['lemma'])
        if key in seen:
            raise ValueError('P6_FREEDICT_BINDING_INVALID')
        seen.add(key)
        bindings.append({'line_ref': key[0], 'lemma': key[1]})
        for record in lookup_freedict_pronunciations(extraction, key[1]):
            selected[record['variant_ref']] = record
    return {
        'schema': 'BRODY_P6_FREEDICT_WORD_BINDINGS_V1',
        'source': source.copy(),
        'bindings': bindings,
        'records': list(selected.values()),
    }
