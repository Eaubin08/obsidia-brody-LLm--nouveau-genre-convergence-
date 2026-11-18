"""P4: inspect native linguistic candidates under existing P1/P2/P3 constraints.

No tokenization, grammatical rule engine, lexical acquisition or authority here.
A rejected morphological assignment is impossible only in its native NP slot.
Other categories, senses, contexts and source expressions remain untouched.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
from brody.linguistic.primitives import UtteranceFrame
from brody.linguistic.french_grammar import (
    _assess_noun_adjective_agreement, _assess_determiner_noun_agreement,
    _NOMINAL_AGREEMENT_RULE_SPECS,
)
from brody.linguistic.communication import digest, project_communication

BOUNDARY = dict(readonly=True, decision_authority='KX108_ONLY', memory_write=False,
                canonical_write=False, verified_fact=False, semantic_resolution=False,
                execution_authorized=False, human_review_required=True,
                publication_permitted=False)

def _check_boundary(value):
    if not isinstance(value,dict) or value.get('readonly') is not True or value.get('decision_authority')!='KX108_ONLY' or value.get('memory_write') is not False:
        raise ValueError('P4_NATIVE_BOUNDARY_REQUIRED')
    if any(value.get(k) is True for k in ('canonical_write','verified_fact','semantic_resolution','execution_authorized','allowed_to_act','allowed_to_decide','publication_permitted')):
        raise ValueError('P4_AUTHORITY_OR_FACT_PROMOTION_FORBIDDEN')

def _is_pos(reading, category):
    return reading.get('pos') in ({'noun','nom','NOM'} if category=='NOUN' else {'adjective','adj','ADJ'})

def decipher_frame(frame, *, communication=None):
    """Project one native frame; do not accept client text as independent proof."""
    if not isinstance(frame,UtteranceFrame):raise TypeError('P4_NATIVE_FRAME_REQUIRED')
    sa=frame.structural_analysis
    if sa.get('schema')!='BRODY_STRUCTURAL_LANGUAGE_V0':raise ValueError('P4_P1_STRUCTURE_REQUIRED')
    _check_boundary(sa.get('boundary'))
    raw_hash=hashlib.sha256(frame.raw.encode('utf-8')).hexdigest()
    if sa.get('original')!=frame.raw or sa.get('provenance',{}).get('source_sha256')!=raw_hash:
        raise ValueError('P4_P1_SOURCE_MISMATCH')
    tokens={t['id']:t for t in sa['tokens']}
    if len(tokens)!=len(sa['tokens']):raise ValueError('P4_DUPLICATE_TOKEN_REF')
    p3=project_communication(frame) if communication is None else communication
    _check_boundary(p3.get('boundary'))
    if (p3.get('schema')!='BRODY_COMMUNICATION_STRUCTURE_V0' or p3.get('original_expression')!=frame.raw
            or p3.get('provenance',{}).get('raw_sha256')!=digest(frame.raw)):
        raise ValueError('P4_P3_SOURCE_MISMATCH')
    out=dict(schema='BRODY_STRUCTURAL_DECIPHERING_V0', original_expression=frame.raw,
             tokens=deepcopy(sa['tokens']),groups=[],predicates=[asdict(u) for u in frame.units],
             dependencies=deepcopy(sa['dependencies']),structural_clause_relations=deepcopy(sa.get('structural_clause_relations',[])),
             candidates=[],constraints=[],compatible_candidates=[],open_candidates=[],eliminated_candidates=[],
             native_agreements=deepcopy(sa['agreements']),source_contradictions=list(frame.contradictions),
             source_ambiguities=list(frame.ambiguities),clause_relations=deepcopy(sa.get('clause_relations',[])),
             ambiguities=deepcopy(sa['alternatives']),unresolved=deepcopy(sa['unresolved']),
             communication_references=deepcopy(p3['references']),communication_contexts=deepcopy(p3['contexts']),
             source_corpus=deepcopy(sa['provenance']['corpus']),semantic_resolution=False,
             boundary=deepcopy(BOUNDARY),provenance=dict(p1_source_sha256=raw_hash,
             p1_structure_sha256=digest(sa),p3_structure_sha256=digest(p3),persistence='NONE'),
             rule_definitions={r['id']:deepcopy(r) for r in sa['rule_definitions']})
    def constraint(candidate,rule,status,input_refs,implementation):
        cid='constraint:'+str(len(out['constraints'])+1)
        inp,result,conditions,impl=_NOMINAL_AGREEMENT_RULE_SPECS[rule]
        out['rule_definitions'].setdefault(rule,dict(id=rule,input=inp,output=result,conditions=conditions,
            implementation='app/semantic/lattice/french_grammar.py::'+impl,
            authority_created=False,semantic_truth_created=False))
        out['constraints'].append(dict(id=cid,candidate_ref=candidate['id'],rule_id=rule,
            status=status,input_refs=input_refs,implementation='app/semantic/lattice/french_grammar.py::'+implementation,
            verified_fact=False,semantic_resolution=False))
        candidate['constraint_refs'].append(cid)
        if status=='INCOMPATIBLE':candidate['elimination_refs'].append(cid)
    for g in sa['groups']:
        out['groups'].append(dict(id=g['id'],raw=g['raw'],span=deepcopy(g['span']),kind=g['kind'],
            function=g['function'],predicate_ref=g.get('predicate_ref'),parent=g['parent'],
            native_head=g.get('head'),head_token_ref=g.get('head_token_ref'),
            native_head_selection=deepcopy(g.get('head_selection')),source_rule=g['source_rule'],
            source_group_ref=g['id'],semantic_resolution=False))
        if g['kind']!='NP':continue
        heads=deepcopy(g.get('head_candidates',[]))
        if g.get('head_token_ref') and not any(h['token_ref']==g['head_token_ref'] for h in heads):
            heads.append(dict(token_ref=g['head_token_ref'],head=g['head'],modifier_token_refs=[
                c['head_token_ref'] for c in sa['groups'] if c.get('parent')==g['id'] and c['kind']=='ADJP' and c.get('head_token_ref')]))
        first=tokens[g['token_refs'][0]] if g['token_refs'] else {}
        determiner=first if first.get('selected_nature')=='DETERMINER' else None
        for head in heads:
            token=tokens[head['token_ref']]
            noun_readings=[(i,r) for i,r in enumerate(token['nature_analyses']) if _is_pos(r,'NOUN')]
            for index,reading in noun_readings or [(None,None)]:
                candidate=dict(id='candidate:'+str(len(out['candidates'])+1),kind='NOMINAL_MORPHOLOGICAL_ASSIGNMENT',
                    group_ref=g['id'],head_token_ref=token['id'],head=token['normalized'],
                    morphology=deepcopy(reading),reading_ref=None if index is None else token['id']+'/nature_analyses/'+str(index),
                    modifier_token_refs=deepcopy(head.get('modifier_token_refs',[])),
                    native_selection_support=g.get('head_token_ref')==token['id'],
                    scope='THIS_NATIVE_NOMINAL_CONSTRUCTION',constraint_refs=[],elimination_refs=[],
                    verified_fact=False,semantic_resolution=False,lexical_status=token['lexical_status'])
                if determiner:
                    constraint(candidate,'written_determiner_and_corpus_noun_alternatives',
                        _assess_determiner_noun_agreement(determiner['normalized'],[reading] if reading else []),
                        [determiner['id'],candidate['reading_ref'] or token['id']], '_assess_determiner_noun_agreement')
                for mid in candidate['modifier_token_refs']:
                    modifier=tokens[mid]
                    adjective_readings=[a for a in modifier['nature_analyses'] if _is_pos(a,'ADJECTIVE')]
                    constraint(candidate,'corpus_morphological_alternatives',
                        _assess_noun_adjective_agreement([reading] if reading else [],adjective_readings),
                        [candidate['reading_ref'] or token['id'],mid+'/nature_analyses'], '_assess_noun_adjective_agreement')
                statuses=[c['status'] for c in out['constraints'] if c['id'] in candidate['constraint_refs']]
                candidate['status']=('ELIMINATED' if candidate['elimination_refs'] else
                    'COMPATIBLE_NOT_PROVEN' if statuses and all(s=='COMPATIBLE' for s in statuses) else 'OPEN_INSUFFICIENT_EVIDENCE')
                out['candidates'].append(candidate)
                bucket={'ELIMINATED':'eliminated_candidates','COMPATIBLE_NOT_PROVEN':'compatible_candidates','OPEN_INSUFFICIENT_EVIDENCE':'open_candidates'}[candidate['status']]
                out[bucket].append(candidate['id'])
        surviving=[c for c in out['candidates'] if c['group_ref']==g['id'] and c['status']!='ELIMINATED']
        if len({c['head_token_ref'] for c in surviving})>1:
            out['ambiguities'].append(dict(kind='P4_COMPATIBLE_HEAD_ALTERNATIVES',group_ref=g['id'],
                candidate_refs=[c['id'] for c in surviving],selection=None,semantic_resolution=False))
    out['status']='PARTIAL' if sa['status']=='PARTIAL' or out['source_ambiguities'] or any(a['status']!='COMPATIBLE' for a in out['native_agreements']) or out['source_contradictions'] or out['unresolved'] or out['ambiguities'] or any(c['status']!='COMPATIBLE_NOT_PROVEN' for c in out['candidates']) else 'STRUCTURAL_CONSTRAINTS_ASSESSED'
    return out

def decipher_dialogue(dialogue):
    """Reuse P2's explicit revisions; absence of selection is not elimination."""
    if dialogue.get('schema')!='BRODY_DIALOGUE_STRUCTURE_V0':raise ValueError('P4_P2_STRUCTURE_REQUIRED')
    _check_boundary(dialogue.get('boundary'))
    out=dict(schema='BRODY_DIALOGUE_DECIPHERING_V0',reference_candidates=deepcopy(dialogue['reference_candidates']),
        reference_interpretations=deepcopy(dialogue['reference_interpretations']),versions=deepcopy(dialogue['versions']),
        eliminated_references=[],uncertainties=deepcopy(dialogue['uncertainties']),
        boundary=deepcopy(BOUNDARY),provenance=dict(p2_structure_sha256=digest(dialogue),persistence='NONE'))
    relations=dialogue['relations'];mentions={m['id']:m for m in dialogue['mentions']};turns={t['turn_ref']:t for t in dialogue['turns']}
    references={r['anaphor_ref']:r for r in dialogue['reference_candidates']}
    def checked_mention(identity):
        m=mentions.get(identity)
        if not m:return None
        t=turns.get(m.get('turn_ref'));p=m.get('provenance',{})
        if (not t or not t.get('structure_available') or t.get('use_status')!='CURRENT_USER_TURN'
                or identity not in t.get('mention_refs',[]) or t.get('frame_sha256')!=p.get('frame_sha256')
                or not t.get('frame_sha256') or not t.get('source_ref') or t['source_ref']!=p.get('source_ref')
                or not t.get('raw_sha256') or t['raw_sha256']!=p.get('raw_sha256')
                or any(t.get(k)!=m.get(k) for k in ('emitter_id','session_id','scope_id','perspective_id'))):return None
        return m
    def native_revision(interpretation,revision,relation,chosen):
        anaphor=checked_mention(interpretation['anaphor_ref']);target=checked_mention(chosen)
        source=turns.get(revision.get('source_turn'))
        if (not anaphor or not target or not source or dialogue.get('closed')
                or source.get('use_status')!='CURRENT_USER_TURN' or not source.get('structure_available')
                or not source.get('frame_sha256') or source.get('raw_sha256')!=revision.get('raw_sha256')
                or source.get('source_ref')!=revision.get('source_ref')
                or target.get('kind')!='NOMINAL' or not target.get('eligible_for_binding')
                or anaphor.get('kind')!='ANAPHOR' or not anaphor.get('eligible_for_binding')
                or not target['order']<anaphor['order']<source['order']):return False
        scope=('emitter_id','session_id','scope_id','perspective_id')
        if any(anaphor.get(k)!=target.get(k) or anaphor.get(k)!=source.get(k) for k in scope):return False
        p=interpretation.get('provenance',{})
        if any(p.get(k)!=anaphor.get(k) for k in scope):return False
        if any(p.get(k)!=anaphor['provenance'].get(k) for k in ('source_ref','raw_sha256','frame_sha256')):return False
        for identity in relation.get('focus_mentions',[])+relation.get('rejected_mentions',[]):
            mention=checked_mention(identity)
            if not mention or mention['turn_ref']!=revision['source_turn']:return False
        return bool(relation.get('focus_mentions') and relation.get('rejected_mentions'))
    for interpretation in dialogue['reference_interpretations']:
        if interpretation.get('status')!='SOURCE_BOUND_REFERENCE_INTERPRETATION' or interpretation.get('verified_fact') is not False or interpretation.get('semantic_resolution') is not False:continue
        ref=references.get(interpretation['anaphor_ref'],{});candidates=ref.get('candidate_refs',[])
        chosen=interpretation.get('selected_ref')
        if chosen not in candidates:continue
        validated=[]
        for revision in interpretation.get('revisions',[]):
            pointer=revision.get('clarification_ref','');parts=pointer.split('/')
            if len(parts)!=2 or parts[0]!='relations' or not parts[1].isdigit():continue
            index=int(parts[1])
            if index>=len(relations):continue
            relation=relations[index]
            if (relation.get('kind')!='CLARIFICATION' or relation.get('status')!='SOURCE_BOUND_CLARIFICATION'
                or interpretation['anaphor_ref'] not in relation.get('target_reference_refs',[])
                or relation.get('candidate_selection_refs')!=[chosen] or revision.get('selected_ref')!=chosen
                or not relation.get('source_ref') or revision.get('source_ref')!=relation['source_ref']
                or revision.get('source_turn')!=relation.get('source_turn')
                or not revision.get('raw_sha256') or revision['raw_sha256']!=relation.get('raw_sha256')):continue
            if not native_revision(interpretation,revision,relation,chosen):continue
            rejected=set(revision.get('excluded_antecedent_refs',[])) & set(relation.get('excluded_antecedent_refs',[]))
            validated.append((pointer,rejected,revision))
        for pointer,rejected,revision in validated:
            for candidate in sorted(rejected & set(candidates)-{chosen}):
                rejected_mention=checked_mention(candidate);anaphor=checked_mention(interpretation['anaphor_ref'])
                if (not rejected_mention or not rejected_mention.get('eligible_for_binding')
                    or not rejected_mention['order']<anaphor['order']
                    or any(rejected_mention.get(k)!=anaphor.get(k) for k in ('emitter_id','session_id','scope_id','perspective_id'))):continue
                out['eliminated_references'].append(dict(anaphor_ref=interpretation['anaphor_ref'],candidate_ref=candidate,
                    selected_ref=chosen,basis='P2_EXPLICIT_SOURCE_BOUND_EXCLUSION',constraint_ref=pointer,
                    provenance=deepcopy(revision),scope='SUPPLIED_SESSION_ONLY_NOT_FACTUAL',
                    semantic_resolution=False,verified_fact=False))
    return out
