"""P3 descriptive communication projection over P1, never semantic closure.

Roles are source claims/candidates, not authenticated identities or observed acts.
Quotes only delimit source spans. Predicate/argument roles come from native P1.
"""
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib
import json

ROLES = ('emitter','sender','receiver','addressee','speaker','interlocutor',
         'narrator','character','mentioned','quoted')
CONTEXT_FIELDS = {r+'_ids' for r in ROLES} | {'source_ref','situation','time','perspective_id','level_times','level_roles','role_correction'}
BOUNDARY = dict(readonly=True, decision_authority='KX108_ONLY', memory_write=False,
    canonical_write=False, semantic_resolution=False, verified_fact=False,
    execution_authorized=False, human_review_required=True, publication_permitted=False)
SPEECH = frozenset({'SAY','SPEAK','EXPLAIN','REPORT','QUOTE'})
THOUGHT = frozenset({'BELIEVE','THINK','SUPPOSE'})
NARRATIVE = frozenset({'RACONTER'})
FIRST = {'je','j\'','me','m\'','moi'}
SECOND = {'tu','te','t\'','toi'}
THIRD = {'il','elle','ils','elles','lui','leur','le','la','les'}


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':')).encode('utf-8')).hexdigest()


def validate_context(context):
    """Only caller-declared situational fields; no authority or inference inputs."""
    if context is None:return {}
    if type(context) is not dict or set(context)-CONTEXT_FIELDS:
        raise ValueError('COMMUNICATION_CONTEXT_INVALID')
    for k,v in context.items():
        if k=='level_roles':
            allowed={r+'_ids' for r in ROLES}|{'source_ref','raw_sha256'}
            if type(v) is not dict or len(v)>64:raise ValueError('COMMUNICATION_LEVEL_ROLES_INVALID')
            for sid,claim in v.items():
                if (type(sid) is not str or not 0<len(sid)<=128 or sid=='actual'
                    or type(claim) is not dict or set(claim)-allowed
                    or type(claim.get('source_ref')) is not str or not 0<len(claim['source_ref'])<=512
                    or not any(r+'_ids' in claim for r in ROLES)
                    or type(claim.get('raw_sha256')) is not str or len(claim['raw_sha256'])!=64):
                    raise ValueError('COMMUNICATION_LEVEL_ROLES_INVALID')
                validate_context({a:b for a,b in claim.items() if a!='raw_sha256'})
            continue
        if k=='level_times':
            if (type(v) is not dict or len(v)>64 or any(type(a) is not str or not 0<len(a)<=128
                or a=='actual' or type(b) is not str or not 0<len(b)<=512 for a,b in v.items())):
                raise ValueError('COMMUNICATION_LEVEL_TIMES_INVALID')
            continue
        if k=='role_correction':
            if (type(v) is not dict or set(v)!={'target_turn','role','referent_ids','source_ref'}
                or v.get('role') not in ROLES
                or any(type(v.get(a)) is not str or not 0<len(v[a])<=512 for a in ['target_turn','source_ref'])
                or type(v.get('referent_ids')) is not list or len(v['referent_ids'])>32
                or any(type(x) is not str or not 0<len(x)<=256 for x in v['referent_ids'])
                or len(set(v['referent_ids']))!=len(v['referent_ids'])):
                raise ValueError('COMMUNICATION_ROLE_CORRECTION_INVALID')
            continue
        if k.endswith('_ids'):
            if (type(v) is not list or len(v)>32
                or any(type(x) is not str or not 0<len(x)<=256 for x in v)
                or len(set(v))!=len(v)):
                raise ValueError('COMMUNICATION_PARTICIPANTS_INVALID')
        elif type(v) is not str or not 0<len(v)<=512:
            raise ValueError('COMMUNICATION_CONTEXT_VALUE_INVALID')
    if context and not context.get('source_ref'):
        raise ValueError('COMMUNICATION_CONTEXT_PROVENANCE_REQUIRED')
    return deepcopy(context)


def _binding(refs=(),status='UNKNOWN',source=None):
    return dict(refs=list(refs),status=status,source=source)


def project_communication(frame, *, context=None):
    """Consume native tokens, groups, units and embedding relations unchanged."""
    context=validate_context(context)
    f=asdict(frame) if is_dataclass(frame) else frame
    raw=f['raw']; sa=f.get('structural_analysis',{})
    tokens=sa.get('tokens',[]); groups=sa.get('groups',[]); units=f.get('units',[])
    out=dict(schema='BRODY_COMMUNICATION_STRUCTURE_V0', original_expression=raw,
        contexts=[],mentions=[],references=[],relations=[],uncertainties=[],surface_act=f.get('surface_act'),
        boundary=deepcopy(BOUNDARY),provenance=dict(raw_sha256=digest(raw),
        source='EXISTING_P1_STRUCTURAL_ANALYSIS',identity_status='DECLARED_NOT_AUTHENTICATED'))
    def scope(identity,kind,parent,span):
        s=dict(id=identity,kind=kind,parent_ref=parent,span=list(span),
            roles={r:_binding() for r in ROLES},unit_refs=[],
            situation=None,time=None,perspective_id=None,
            epistemic_status='DESCRIBED_NOT_VERIFIED' if parent else 'SUPPLIED_MESSAGE')
        out['contexts'].append(s);return s
    root=scope('actual','ACTUAL_MESSAGE',None,[0,len(raw)])
    for r in ROLES:
        if context.get(r+'_ids'):
            root['roles'][r]=_binding(context[r+'_ids'],'CONTEXT_DECLARED',context['source_ref'])
    for k in ('situation','time','perspective_id'):root[k]=context.get(k)
    # Delimiting punctuation only. Apostrophes never open a quotation scope.
    stack=[];quotes=[];closers={'«':'»','“':'”','"':'"'}
    for i,c in enumerate(raw):
        if stack and c==stack[-1][1]:
            start,_,parent=stack.pop()
            q=scope('quote:'+str(start),'QUOTED_CONTENT',parent,[start+1,i])
            quotes.append(q)
        elif c in closers:
            stack.append((i,closers[c],'quote:'+str(stack[-1][0]) if stack else 'actual'))
        elif c in {'»','”'}:
            out['uncertainties'].append(dict(kind='UNMATCHED_QUOTE',span=[i,i+1]))
    if stack:
        out['uncertainties'].append(dict(kind='UNCLOSED_QUOTE',span=[stack[0][0],len(raw)]))
        for start,_,parent in stack:
            q=scope('quote:'+str(start),'QUOTED_CONTENT',parent,[start+1,len(raw)])
            q['delimiter_status']='UNCLOSED';quotes.append(q)
    def quote_at(span):
        return min((q for q in quotes if q['span'][0]<=span[0] and span[1]<=q['span'][1]),
                   key=lambda q:q['span'][1]-q['span'][0],default=None)
    by_scope={s['id']:s for s in out['contexts']}
    by_unit={u['id']:u for u in units}; act_by_unit={}
    for u in units:
        if u['predicate'] in SPEECH|THOUGHT|NARRATIVE or _is_reflexive_address(u,f):
            kind='DESCRIBED_THOUGHT' if u['predicate'] in THOUGHT else 'DESCRIBED_SPEECH_ACT'
            a=scope('act:'+u['id'],kind,'actual',u['span']);act_by_unit[u['id']]=a
            a['predicate_ref']=u['id'];a['polarity']=u.get('polarity');a['modality']=u.get('modality')
            by_scope[a['id']]=a
    # Native embedded_under governs content membership; quote scopes override deixis.
    membership={}
    for u in units:
        q=quote_at(u['span']);parent=act_by_unit.get(u.get('embedded_under'))
        parent_in_quote=parent and q and q['span'][0]<=parent['span'][0] and parent['span'][1]<=q['span'][1]
        membership[u['id']]=parent['id'] if parent and (not q or parent_in_quote) else (q['id'] if q else 'actual')
        by_scope[membership[u['id']]]['unit_refs'].append(u['id'])
        if u['id'] in act_by_unit:
            act_by_unit[u['id']]['parent_ref']=membership[u['id']]
        if parent:
            out['relations'].append(dict(kind='NATIVE_EMBEDDED_CONTENT',source=parent['id'],
                target=u['id'],evidence='P1.embedded_under'))
    # Quoted content belongs to a reporting act only with a unique preceding
    # native speech predicate in its immediate outer scope and a written colon.
    for q in sorted(quotes,key=lambda s:s['span'][0]):
        start=q['span'][0]-1
        candidates=[u for u in units if u['predicate'] in SPEECH|NARRATIVE
            and u['span'][1]<=start and membership[u['id']]==q['parent_ref']
            and (':' in raw[u['span'][1]:start] or not raw[u['span'][1]:start].strip())
            and not any(x in raw[u['span'][1]:start] for x in '.!?;')
            and not any(v['id']!=u['id'] and u['span'][1]<=v['span'][0]<start for v in units)]
        if len(candidates)==1:
            q['reporting_act_ref']=act_by_unit[candidates[0]['id']]['id']
            out['relations'].append(dict(kind='QUOTED_CONTENT_OF',source=q['reporting_act_ref'],target=q['id'],evidence='P1_PREDICATE_AND_QUOTE_DELIMITERS'))
        else:out['uncertainties'].append(dict(kind='QUOTE_SPEAKER_UNESTABLISHED',scope_ref=q['id']))
    mentions={}
    for g in groups:
        if g.get('kind') not in {'NP','PRONOUN'}:continue
        span=g['span'];identity='mention:'+str(span[0])+':'+str(span[1])
        if identity in mentions:continue
        sid=membership.get(g.get('predicate_ref'),(quote_at(span) or root)['id'])
        m=dict(id=identity,text=raw[span[0]:span[1]],span=list(span),scope_ref=sid,
            group_ref=g['id'],token_refs=g.get('token_refs',[]),predicate_ref=g.get('predicate_ref'),
            function=g.get('function'),head=g.get('head'),entity_status='MENTION_NOT_VERIFIED_IDENTITY')
        mentions[identity]=m
    # P1 exposes clitic tokens even when its semantic argument is open.
    for t in tokens:
        norm=t['normalized'].replace('’',"'")
        if t.get('selected_nature')!='PRONOUN' and norm not in FIRST|SECOND|THIRD|{'nous','vous'}:continue
        span=t['span'];identity='mention:'+str(span[0])+':'+str(span[1])
        if identity not in mentions:
            host=[u for u in units if u['span'][0]>=span[1] and
                  not any(c in raw[span[1]:u['span'][0]] for c in '.!?;:«»“”"')]
            u=min(host,key=lambda u:u['span'][0],default=None)
            sid=membership[u['id']] if u else (quote_at(span) or root)['id']
            mentions[identity]=dict(id=identity,text=raw[span[0]:span[1]],span=list(span),
                scope_ref=sid,group_ref=None,token_refs=[t['id']],predicate_ref=u['id'] if u else None,
                function='CLITIC_OR_PRONOUN',head=norm,entity_status='MENTION_NOT_VERIFIED_IDENTITY')
    out['mentions']=list(mentions.values())
    def matching(u,function):
        return [m for m in out['mentions'] if m['predicate_ref']==u['id'] and m['function']==function]
    for u in units:
        a=act_by_unit.get(u['id'])
        if not a:continue
        subjects=matching(u,'SUBJECT')
        if len(subjects)==1:
            holder=_binding([subjects[0]['id']],'DESCRIBED_ROLE',subjects[0]['group_ref'])
            if u['predicate'] in THOUGHT:
                a['perspective_holder']=holder
            else:
                a['roles']['speaker']=holder
            if u['predicate'] in NARRATIVE:
                a['roles']['narrator']=deepcopy(holder)
        else:out['uncertainties'].append(dict(kind='NATIVE_SUBJECT_UNESTABLISHED',scope_ref=a['id'],predicate_ref=u['id']))
        if u['predicate'] in THOUGHT:continue
        recipients=[]
        for g in groups:
            if g.get('predicate_ref')!=u['id'] or g.get('kind')!='PP':continue
            members=[t for t in tokens if t['id'] in g.get('token_refs',[])]
            if not members or members[0]['normalized'] not in {'à','au','aux'}:continue
            recipients += [m['id'] for m in matching(u,'OBLIQUE_COMPLEMENT') if g['span'][0]<=m['span'][0] and m['span'][1]<=g['span'][1]]
        if recipients:
            a['roles']['addressee']=_binding(recipients,'GRAMMATICAL_CANDIDATES','P1_SPEECH_DATIVE_CONSTRUCTION')
        # These clitics can mark a recipient or beneficiary. Keep that ambiguity.
        clitics=[m['id'] for m in out['mentions'] if m['predicate_ref']==u['id']
            and m['function']=='CLITIC_OR_PRONOUN' and m['text'].casefold().replace('’',"'") in {'me',"m'",'te',"t'",'lui','leur'}]
        if clitics and not _is_reflexive_address(u,f):
            a['roles']['addressee']=_binding(recipients+clitics,'GRAMMATICAL_CANDIDATES','P1_DATIVE_CLITIC_CANDIDATE')
    for q in quotes:
        a=by_scope.get(q.get('reporting_act_ref'))
        if a:
            q['roles']['speaker']=deepcopy(a['roles']['speaker'])
            q['roles']['addressee']=deepcopy(a['roles']['addressee'])
    for m in out['mentions']:
        s=by_scope[m['scope_ref']]
        s['roles']['mentioned']=_merge_source_mentions(s['roles']['mentioned'],[m['id']],'P1_NATIVE_MENTION')
        norm=m['text'].casefold().replace('’',"'")
        if norm not in FIRST|SECOND|THIRD|{'nous','vous'}:continue
        # In indirect speech first/second-person deixis stays with the actual
        # utterance; it shifts only at a delimited direct quotation.
        deictic=s
        while deictic['kind'] not in {'ACTUAL_MESSAGE','QUOTED_CONTENT'}:
            deictic=by_scope[deictic['parent_ref']]
        role='speaker' if norm in FIRST else ('addressee' if norm in SECOND else None)
        bound=deictic['roles'][role] if role else _binding()
        candidates=[]
        if role:candidates=deepcopy(bound['refs'])
        elif norm in {'nous','vous'}:
            supplied=context.get('speaker_ids' if norm=='nous' else 'addressee_ids',[])
            if deictic['id']=='actual' and len(supplied)>1:candidates=deepcopy(supplied)
        else:
            candidates=[x['id'] for x in out['mentions'] if x['scope_ref']==m['scope_ref']
                and x['span'][1]<=m['span'][0] and x['group_ref']
                and x['text'].casefold() not in FIRST|SECOND|THIRD|{'nous','vous'}]
        out['references'].append(dict(mention_ref=m['id'],scope_ref=m['scope_ref'],
            deictic_scope_ref=deictic['id'],candidate_refs=candidates,
            selected_ref=candidates[0] if role and len(candidates)==1 and bound['status']=='CONTEXT_DECLARED' else None,
            status='CONTEXT_DECLARED_BINDING' if role and len(candidates)==1 and bound['status']=='CONTEXT_DECLARED' else 'OPEN_CANDIDATES',
            verified_fact=False,semantic_resolution=False,original_reference_unchanged=True))
    _complete_enunciation(out,f,context)
    out['status']='PARTIAL' if out['uncertainties'] or any(r['selected_ref'] is None for r in out['references']) else 'STRUCTURAL_COMMUNICATION_ONLY'
    return out


def organize_communication(rows, dialogue, *, contexts=None, closed=False):
    """Add P3 to P2 without changing current-user eligibility or P2 overlays."""
    from brody.linguistic.french_grammar import parse_utterance
    if contexts is None:contexts={}
    if type(contexts) is not dict or set(contexts)-{r['id'] for r in rows}:
        raise ValueError('COMMUNICATION_TURN_CONTEXTS_INVALID')
    for c in contexts.values():validate_context(c)
    # Reuse P2 itself for direct callers, never rebuild conversational links.
    frames={r['id']:r.get('analysis') or asdict(parse_utterance(r['text'])) for r in rows}
    if dialogue.get('schema')=='BRODY_DIALOGUE_STRUCTURE_V0':
        p2_structure=dialogue
    else:
        try:
            from apps.obsidia_api.brody_user_expression_calibration import _organize_p2_structure
            p2_rows=[dict(deepcopy(r),analysis=frames[r['id']]) for r in rows]
            p2_structure=_organize_p2_structure(p2_rows,closed=closed)
        except ImportError:
            p2_structure=dict(schema='BRODY_DIALOGUE_STRUCTURE_V0', turns=p2_rows)
    result=dict(schema='BRODY_DIALOGUE_COMMUNICATION_V0',turns=[],relations=[],versions=[],
        reference_interpretations=deepcopy(dialogue.get('reference_interpretations',[])),
        boundary=deepcopy(BOUNDARY),closed=closed,role_interpretations=[],uncertainties=[],p2_mention_links=[],provenance=dict(source='P1_AND_P2',persistence='NONE'))
    previous=None;role_states={}
    for row in rows:
        ctx=validate_context(contexts.get(row['id'],{}))
        declared=ctx.setdefault('emitter_ids',[row['emitter_id']])
        # An envelope/context conflict is not resolved by choosing either source.
        conflict=declared!=[row['emitter_id']]
        ctx.setdefault('source_ref',row['source_ref'])
        if row.get('perspective_id') is not None:ctx.setdefault('perspective_id',row['perspective_id'])
        frame=frames[row['id']]
        projection=project_communication(frame,context=None if closed else ctx)
        if conflict:
            projection['contexts'][0]['roles']['emitter']={**_binding(status='CONFLICTING_SOURCES'),
                'source_claims':[_binding([row['emitter_id']],'ENVELOPE_DECLARED',row['source_ref']),
                                 _binding(declared,'CONTEXT_DECLARED',ctx['source_ref'])]}
            projection['uncertainties'].append(dict(kind='EMITTER_CONTEXT_CONFLICT'))
            projection['status']='PARTIAL'
        item=dict(turn_ref=row['id'],session_id=row['session_id'],scope_id=row['scope_id'],
            use_status=row['use_status'],communication=projection)
        # Third-person references may concern a prior interlocutor. Keep all
        # supplied same-session candidates with source links, never select one.
        if not closed:
            local_mentions={m['id']:m for m in projection['mentions']}
            for reference in projection['references']:
                mention=local_mentions[reference['mention_ref']]
                if reference['scope_ref']!='actual' or mention['text'].casefold() not in THIRD:continue
                sources=[];reference['prior_mention_candidates']=[]
                for old_item in result['turns']:
                    if any(old_item[k]!=item[k] for k in ('session_id','scope_id')):continue
                    for old_mention in old_item['communication']['mentions']:
                        norm=old_mention['text'].casefold().replace('’',"'")
                        if old_mention['scope_ref']!='actual' or norm in FIRST|SECOND|THIRD|{'nous','vous'}:continue
                        reference['prior_mention_candidates'].append(dict(turn_ref=old_item['turn_ref'],
                            mention_ref=old_mention['id'],text=old_mention['text'],span=deepcopy(old_mention['span']),
                            source_ref=next(r['source_ref'] for r in rows if r['id']==old_item['turn_ref']),
                            raw_sha256=old_item['communication']['provenance']['raw_sha256']))
                    old_roles=old_item['communication']['contexts'][0]['roles']
                    for role in ROLES:
                        binding=old_roles[role]
                        if binding['status']!='CONTEXT_DECLARED':continue
                        for identity in binding['refs']:
                            sources.append(dict(candidate_ref=identity,turn_ref=old_item['turn_ref'],role=role,source=binding['source']))
                            if identity not in reference['candidate_refs']:reference['candidate_refs'].append(identity)
                reference['prior_participant_candidates']=sources
        _link_p2_mentions(result,row,projection,dialogue)
        if not closed and ctx.get('role_correction'):
            _record_role_correction(result,role_states,row,ctx['role_correction'])
        if not closed:_record_native_role_correction(result,role_states,row,frame,projection,frames,rows,p2_structure)
        result['role_interpretations']=deepcopy(list(role_states.values()))
        result['turns'].append(item)
        if previous and all(previous[k]==row[k] for k in ('session_id','scope_id')) and not closed:
            previous_projection=result['turns'][-2]['communication']
            if (previous_projection.get('surface_act')=='interrogative'
                    and projection.get('surface_act')!='interrogative'):
                result['relations'].append(dict(kind='QUESTION_RESPONSE_CANDIDATE',source=previous['id'],target=row['id'],
                    evidence='P1_SURFACE_ACT_AND_SUPPLIED_TURN_ORDER',verified_fact=False))
            old=previous_projection['contexts'][0]
            current=projection['contexts'][0]
            for role in ROLES:
                if old['roles'][role]['refs']!=current['roles'][role]['refs'] and role!='mentioned':
                    result['relations'].append(dict(kind=role.upper()+'_CHANGE',
                        source=previous['id'],target=row['id'],evidence='SUPPLIED_CONTEXTS_NOT_AUTHENTICATED'))
            if old['perspective_id']!=current['perspective_id']:
                result['relations'].append(dict(kind='PERSPECTIVE_CHANGE',source=previous['id'],target=row['id']))
        result['versions'].append(dict(turn_ref=row['id'],communication=deepcopy(projection),role_interpretations=deepcopy(result['role_interpretations']),
            reference_interpretations=deepcopy(next((v['reference_interpretations'] for v in dialogue.get('versions',[]) if v.get('through_turn')==row['id']),[]))))
        previous=row
    result['dialogue_relation_refs']=deepcopy(dialogue.get('relations',[]))
    result['conversation_evidence']=dict(schema=p2_structure['schema'],relations=deepcopy(p2_structure['relations']),provenance=deepcopy(p2_structure['provenance']))
    result['status']='SESSION_CLOSED' if closed else 'DESCRIPTIVE_ONLY'
    return result


def _complete_enunciation(out, frame, context):
    """Source-bound interpretation overlays; never mutate legacy selections."""
    scopes={s['id']:s for s in out['contexts']}
    mentions={m['id']:m for m in out['mentions']}
    references={r['mention_ref']:r for r in out['references']}
    groups={g['id']:g for g in frame.get('structural_analysis',{}).get('groups',[])}
    raw=out['original_expression']
    level_roles=context.get('level_roles',{})
    def apply_level_roles(sid, claim):
        if sid not in scopes or claim['raw_sha256']!=digest(raw):
            raise ValueError('COMMUNICATION_LEVEL_ROLE_SOURCE_MISMATCH')
        for role in ROLES:
            if role+'_ids' not in claim:continue
            old=scopes[sid]['roles'][role]
            new=_binding(claim[role+'_ids'],'CONTEXT_DECLARED',claim['source_ref'])
            if old['status']=='UNKNOWN':scopes[sid]['roles'][role]=new
            else:scopes[sid]['roles'][role]=dict(refs=[],status='MULTIPLE_SOURCE_CLAIMS',source=None,
                source_claims=[deepcopy(old),new])
    for sid,claim in level_roles.items():
        if sid not in scopes:raise ValueError('COMMUNICATION_LEVEL_ROLE_SOURCE_MISMATCH')
        if scopes[sid]['kind']!='QUOTED_CONTENT':apply_level_roles(sid,claim)
    for q in out['contexts']:
        if q['kind']!='QUOTED_CONTENT':continue
        act=scopes.get(q.get('reporting_act_ref'))
        if act:
            q['roles']['speaker']=deepcopy(act['roles']['speaker'])
            q['roles']['addressee']=deepcopy(act['roles']['addressee'])
        if q['id'] in level_roles:apply_level_roles(q['id'],level_roles[q['id']])
    def valid_mention(m):
        g=groups.get(m.get('group_ref'))
        return (g is not None and list(g.get('span',[]))==m['span']
                and raw[slice(*m['span'])]==m['text'])
    def base(status='UNRESOLVED',referents=(),chain=()):
        return dict(schema='BRODY_SOURCE_BOUND_REFERENCE_V0',status=status,
            referents=list(referents),provenance=dict(raw_sha256=digest(raw),source_chain=list(chain)),
            interpretation_level='SOURCE_REFERENCE_ONLY',semantic_resolution=False,
            verified_fact=False,identity_authenticated=False,original_reference_unchanged=True)
    def resolve(mid,visited):
        if mid in visited or len(visited)>64:return base(chain=[dict(kind='REFERENCE_CYCLE',mention_ref=mid)])
        visited=visited|{mid};m=mentions.get(mid)
        if m is None:return base()
        norm=m['text'].casefold().replace('’',"'")
        if norm not in FIRST|SECOND|THIRD|{'nous','vous'}:
            if not valid_mention(m):return base()
            return base('SOURCE_BOUND_REFERENCE',[dict(kind='SOURCE_MENTION',mention_ref=mid)],
                [dict(kind='P1_MENTION',mention_ref=mid,group_ref=m['group_ref'],span=m['span'])])
        r=references.get(mid)
        if r is None:return base()
        deictic=scopes.get(r['deictic_scope_ref'])
        if deictic is None or deictic.get('delimiter_status')=='UNCLOSED':return base()
        role='speaker' if norm in FIRST else ('addressee' if norm in SECOND else None)
        if role is None:
            return base('AMBIGUOUS' if len(r['candidate_refs'])>1 else 'UNRESOLVED')
        claim=deictic['roles'][role]
        chain=[dict(kind='SITUATED_ROLE',scope_ref=deictic['id'],role=role,
                    source=claim.get('source'),status=claim['status'])]
        if claim['status']=='CONTEXT_DECLARED':
            refs=[dict(kind='DECLARED_IDENTITY',identity_ref=x) for x in claim['refs']]
            return base('SOURCE_BOUND_REFERENCE' if len(refs)==1 else ('AMBIGUOUS' if refs else 'UNRESOLVED'),refs,chain)
        if claim['status']!='DESCRIBED_ROLE' or len(claim['refs'])!=1:
            return base('AMBIGUOUS' if claim['refs'] or claim.get('source_claims') else 'UNRESOLVED',chain=chain)
        target=mentions.get(claim['refs'][0])
        if target is None or not valid_mention(target) or target['function']!='SUBJECT':return base(chain=chain)
        # A singular first person must not choose a member of a coordinated subject.
        coordinated=any(c.get('construction')=='coordinated_subject' and c.get('host')==target.get('predicate_ref')
            and len(c.get('members',[]))>1 for c in frame.get('coordinations',[]))
        if coordinated:return base('AMBIGUOUS',chain=chain)
        b=resolve(target['id'],visited)
        b['provenance']['source_chain']=chain+b['provenance']['source_chain']
        return b
    for r in out['references']:
        r['reference_binding']=resolve(r['mention_ref'],set())
        r['reference_binding']['scope_ref']=r['scope_ref']
        r['reference_binding']['deictic_scope_ref']=r['deictic_scope_ref']
    for q in out['contexts']:
        if q['kind']!='QUOTED_CONTENT':continue
        parent=scopes[q['parent_ref']]
        refs=q['roles']['speaker']['refs']
        if refs:
            parent['roles']['quoted']=_merge_source_mentions(parent['roles']['quoted'],refs,'P3_QUOTED_CONTENT_OF')
    for sid,value in context.get('level_times',{}).items():
        if sid not in scopes:raise ValueError('COMMUNICATION_TIME_SCOPE_UNKNOWN')
        scopes[sid]['time']=value
        scopes[sid]['time_source_ref']=context['source_ref']
    for q in out['contexts']:
        if q['kind']!='QUOTED_CONTENT':continue
        act=scopes.get(q.get('reporting_act_ref'))
        if act and act['time'] is not None:
            if q['time'] is None:
                q['time']=act['time'];q['time_source_ref']=act.get('time_source_ref')
            elif q['time']!=act['time']:
                q['time_claims']=[dict(time=q['time'],source_ref=q.get('time_source_ref')),
                                  dict(time=act['time'],source_ref=act.get('time_source_ref'))]
                q['time']=None
                out['uncertainties'].append(dict(kind='CONFLICTING_TIME_CLAIMS',scope_ref=q['id']))
    out['temporal_references']=[]
    for t in frame.get('structural_analysis',{}).get('tokens',[]):
        offsets={'hier':-1,"aujourd'hui":0,'demain':1}
        if t['normalized'] not in offsets:continue
        span=t['span']
        qs=[s for s in out['contexts'] if s['kind']=='QUOTED_CONTENT' and s['span'][0]<=span[0] and span[1]<=s['span'][1]]
        anchor=min(qs,key=lambda s:s['span'][1]-s['span'][0]) if qs else scopes['actual']
        known=anchor['time'] is not None and anchor.get('delimiter_status')!='UNCLOSED'
        out['temporal_references'].append(dict(token_ref=t['id'],expression=raw[slice(*span)],span=deepcopy(span),
            offset_days=offsets[t['normalized']],anchor_scope_ref=anchor['id'],
            anchor_time=anchor['time'] if known else None,
            source_ref=anchor.get('time_source_ref',context.get('source_ref')) if known else None,
            status='CONTEXT_ANCHORED' if known else 'ANCHOR_UNKNOWN',calendar_date=None,
            verified_fact=False,semantic_resolution=False))


def _link_p2_mentions(result, row, projection, dialogue):
    """Link existing mention identities; no new antecedent decision."""
    for m in dialogue.get('mentions',[]):
        if m.get('turn_ref')!=row['id']:continue
        provenance=m.get('provenance',{})
        if (provenance.get('raw_sha256')!=digest(row['text'])
                or provenance.get('source_ref')!=row['source_ref']):continue
        matching=[n for n in projection['mentions'] if n['span']==m.get('span') and n['text']==m.get('text')]
        if len(matching)!=1:continue
        result['p2_mention_links'].append(dict(turn_ref=row['id'],p2_mention_ref=m['id'],
            p3_mention_ref=matching[0]['id'],span=deepcopy(m['span']),source_ref=row['source_ref'],
            raw_sha256=digest(row['text']),semantic_resolution=False,verified_fact=False))


def _record_role_correction(result, states, row, correction):
    """Caller-declared correction overlay. Original turns and roles stay intact."""
    target=next((x for x in result['turns'] if x['turn_ref']==correction['target_turn']
        and x['session_id']==row['session_id'] and x['scope_id']==row['scope_id']),None)
    if target is None:
        result['uncertainties'].append(dict(kind='ROLE_CORRECTION_TARGET_UNAVAILABLE',turn_ref=row['id'],
            target_turn=correction['target_turn'],source_ref=correction['source_ref']))
        return
    role=correction['role'];key=(row['session_id'],row['scope_id'],target['turn_ref'],role)
    state=states.setdefault(key,dict(target_turn=target['turn_ref'],role=role,
        original_claim=deepcopy(target['communication']['contexts'][0]['roles'][role]),
        corrections=[],referent_ids=[],status='UNRESOLVED',verified_fact=False,semantic_resolution=False,
        identity_status='CALLER_DECLARED_NOT_AUTHENTICATED',original_role_unchanged=True))
    state['corrections'].append(dict(source_turn=row['id'],source_ref=correction['source_ref'],
        raw_sha256=digest(row['text']),referent_ids=deepcopy(correction['referent_ids'])))
    variants={tuple(sorted(c['referent_ids'])) for c in state['corrections']}
    state['status']='DECLARED_ROLE_CORRECTION' if len(variants)==1 else 'CONFLICTING_CORRECTIONS'
    state['referent_ids']=list(state['corrections'][0]['referent_ids']) if len(variants)==1 else []


def _merge_source_mentions(binding, refs, source):
    """Keep contextual identities and text mentions as separate source claims."""
    if binding['status'] in {'CONTEXT_DECLARED','MULTIPLE_SOURCE_CLAIMS'}:
        claims=deepcopy(binding.get('source_claims',[binding]))
        previous=next((c for c in claims if c['status']=='SOURCE_MENTIONS' and c['source']==source),None)
        if previous is None:claims.append(_binding(refs,'SOURCE_MENTIONS',source))
        else:previous['refs'].extend(x for x in refs if x not in previous['refs'])
        return dict(refs=list(dict.fromkeys(binding['refs']+list(refs))),status='MULTIPLE_SOURCE_CLAIMS',
            source=None,source_claims=claims)
    return _binding(list(dict.fromkeys(binding['refs']+list(refs))),'SOURCE_MENTIONS',source)


def _communication_intent_unit(unit, frame):
    """Consume native predicates and the written first-person reflexive pair."""
    if not (unit.get('subject') in {'je',"j'"} and unit.get('polarity')=='positive'
            and unit.get('verb_form')=='FINITE' and unit.get('tense_aspect')=='PRESENT'
            and unit.get('embedded_under') is None and unit.get('modality') is None
            and unit.get('pragmatic')=='ASSERTED'):return False
    return unit['predicate']=='SPEAK' or _is_reflexive_address(unit,frame)


def _is_reflexive_address(unit,frame):
    if unit.get('lemma')!='adresser':return False
    tokens=frame.get('structural_analysis',{}).get('tokens',[])
    index=next((i for i,t in enumerate(tokens) if t['span'][0]==unit['span'][0]),None)
    expected={'je':{'me',"m'"},"j'":{'me',"m'"},'tu':{'te',"t'"},'nous':{'nous'},'vous':{'vous'}}.get(unit.get('subject'),{'se',"s'"})
    return (index is not None and index>0 and tokens[index-1]['normalized'] in expected
            and 'PRONOUN' in tokens[index-1]['nature_candidates'])


def _declared_speaker(projection):
    role=projection['contexts'][0]['roles']['speaker']
    return tuple(role['refs']) if role['status']=='CONTEXT_DECLARED' and len(role['refs'])==1 else None


def _record_native_role_correction(result, states, row, frame, projection, frames, rows, p2):
    """Interpret P1 constituent contrast in existing P2 context, never parse raw."""
    sa=frame.get('structural_analysis',{});contrasts=sa.get('constituent_contrasts',[])
    if not contrasts:return
    def hold(kind):
        result['uncertainties'].append(dict(kind=kind,turn_ref=row['id'],source_ref=row['source_ref'],
            p1_contrast_refs=[c['id'] for c in contrasts],semantic_resolution=False,verified_fact=False))
    if len(contrasts)!=1:return hold('NATIVE_ROLE_CONTRAST_AMBIGUOUS')
    if (row.get('use_status')!='CURRENT_USER_TURN' or frame.get('contradictions')
            or frame.get('surface_act')=='interrogative'
            or any(c['kind']=='QUOTED_CONTENT' for c in projection['contexts'])
            or any(r['kind'] in {'CONDITIONS','REPORTS','BELIEVES'} for r in frame.get('relations',[]))):
        return hold('NATIVE_ROLE_CONTEXT_UNSUPPORTED')
    units=frame.get('units',[]);contrast=contrasts[0]
    if units and (len(units)!=1 or not _communication_intent_unit(units[0],frame)
                  or contrast['host_predicate_ref']!=units[0]['id']):
        return hold('NATIVE_ROLE_INTENT_UNRESOLVED')
    actor=_declared_speaker(projection)
    emitter=projection['contexts'][0]['roles']['emitter']
    if emitter['status']!='CONTEXT_DECLARED' or emitter['refs']!=[row['emitter_id']]:
        return hold('NATIVE_ROLE_EMITTER_CONFLICT')
    if actor is None:return hold('NATIVE_ROLE_SPEAKER_UNRESOLVED')
    groups={g['id']:g for g in sa.get('groups',[])}
    a=groups.get(contrast['proposed_group_ref']);b=groups.get(contrast['rejected_group_ref'])
    if not a or not b or not contrast.get('same_construction'):
        return hold('NATIVE_ROLE_CONSTRUCTION_UNRESOLVED')
    if a['kind']=='PP' and b['kind']=='PP':
        if a['head']!='à' or b['head']!='à':return hold('NATIVE_ROLE_NOT_A_RECIPIENT')
        def member(g):
            refs=g.get('fragment_member_refs')
            if refs is None:refs=[x['id'] for x in groups.values() if x.get('parent')==g['id'] and x['kind']=='NP']
            return groups.get(refs[0]) if len(refs)==1 else None
        proposed,rejected=member(a),member(b)
    elif not units and a['kind']==b['kind']=='NP':
        proposed,rejected=a,b
    else:return hold('NATIVE_ROLE_NOT_A_RECIPIENT')
    if proposed is None or rejected is None:return hold('NATIVE_ROLE_GROUP_AMBIGUOUS')
    def signature(g,structure=None):
        token_map={t['id']:t for t in (structure or sa).get('tokens',[])}
        return tuple(token_map[r]['normalized'] for r in g.get('token_refs',[]) if r in token_map)
    def label(g):return signature(g)
    if not label(proposed) or not label(rejected) or label(proposed)==label(rejected):
        return hold('NATIVE_ROLE_REFERENCE_UNRESOLVED')
    negation=any(d['relation']=='CONSTITUENT_NEGATION' and d['head']==b['id']
                 and d['dependent']==contrast['negator_ref'] for d in sa['dependencies'])
    if not negation:return hold('NATIVE_ROLE_NEGATION_UNPROVEN')
    # P2 supplies source-order relations. Its scope gates are strengthened here;
    # these links never establish identity or factual agreement.
    by_id={r['id']:r for r in rows};paths={row['id']:[]};changed=True
    packets={t['turn_ref']:t['communication'] for t in result['turns']};packets[row['id']]=projection
    positions={r['id']:i for i,r in enumerate(rows)}
    def eligible_node(identity):
        node=by_id.get(identity);packet=packets.get(identity)
        return (node is not None and packet is not None
            and node.get('use_status')=='CURRENT_USER_TURN'
            and all(node.get(k)==row.get(k) for k in ['emitter_id','session_id','scope_id','perspective_id'])
            and _declared_speaker(packet)==actor
            and packet['contexts'][0]['perspective_id']==projection['contexts'][0]['perspective_id']
            and packet['contexts'][0]['roles']['emitter']['status']=='CONTEXT_DECLARED'
            and packet['contexts'][0]['roles']['emitter']['refs']==[node['emitter_id']])
    while changed:
        changed=False
        for rel in p2.get('relations',[]):
            if rel.get('kind') not in {'CONTINUES','QUESTION_RESPONSE_CANDIDATE','REFORMULATION_CANDIDATE'}:continue
            source,target=rel.get('source_turn'),rel.get('target_turn')
            if (target in paths and source not in paths and eligible_node(source) and eligible_node(target)
                    and positions[source]<positions[target]):
                paths[source]=[deepcopy(rel)]+paths[target];changed=True
    matches=[]
    for old in result['turns']:
        old_row=by_id[old['turn_ref']]
        if (old['turn_ref'] not in paths or any(old_row.get(k)!=row.get(k)
                for k in ['emitter_id','session_id','scope_id','perspective_id'])
                or old_row.get('use_status')!='CURRENT_USER_TURN'
                or _declared_speaker(old['communication'])!=actor
                or old['communication']['contexts'][0]['perspective_id']!=projection['contexts'][0]['perspective_id']
                or old['communication']['contexts'][0]['roles']['emitter']['status']!='CONTEXT_DECLARED'
                or old['communication']['contexts'][0]['roles']['emitter']['refs']!=[old_row['emitter_id']]):continue
        old_frame=frames[old['turn_ref']];old_sa=old_frame.get('structural_analysis',{})
        if (old_sa.get('constituent_contrasts') or old_frame.get('contradictions')
                or any(c['kind']=='QUOTED_CONTENT' for c in old['communication']['contexts'])):continue
        for unit in old_frame.get('units',[]):
            if not _communication_intent_unit(unit,old_frame):continue
            scope=next((c for c in old['communication']['contexts'] if c.get('predicate_ref')==unit['id']
                        and c['kind']=='DESCRIBED_SPEECH_ACT' and c['parent_ref']=='actual'),None)
            if scope is None or scope['roles']['addressee'].get('source_claims'):continue
            old_groups=old_sa.get('groups',[])
            for pg in old_groups:
                if pg['kind']!='PP' or pg.get('predicate_ref')!=unit['id'] or pg.get('head')!='à':continue
                nps=[g for g in old_groups if g.get('parent')==pg['id'] and g['kind']=='NP']
                if len(nps)!=1 or signature(nps[0],old_sa)!=label(rejected):continue
                role=scope['roles']['addressee']
                mention_refs={m['id'] for m in old['communication']['mentions']
                    if m.get('group_ref')==nps[0]['id'] and m.get('span')==nps[0]['span']}
                if role['status']!='GRAMMATICAL_CANDIDATES' or not mention_refs.intersection(role['refs']):continue
                matches.append((old,scope,nps[0],paths[old['turn_ref']]))
    if len(matches)!=1:return hold('NATIVE_ROLE_TARGET_AMBIGUOUS' if matches else 'NATIVE_ROLE_TARGET_UNRESOLVED')
    old,scope,original,path=matches[0]
    def source_mention(g,turn):
        text=by_id[turn]['text'];span=g['span']
        return dict(turn_ref=turn,group_ref=g['id'],span=deepcopy(span),text=text[slice(*span)],
            head=g.get('head'),token_refs=deepcopy(g.get('token_refs',[])),source_ref=by_id[turn]['source_ref'],
            raw_sha256=digest(text),token_norms=list(signature(g,frames[turn]['structural_analysis'])),verified_fact=False)
    proposal=source_mention(proposed,row['id']);rejection=source_mention(rejected,row['id'])
    antecedent=source_mention(original,old['turn_ref'])
    # A word-label correspondence is a contextual interpretation, not real identity.
    key=(row['session_id'],row['scope_id'],old['turn_ref'],scope['id'],'addressee')
    state=states.setdefault(key,dict(target_turn=old['turn_ref'],target_scope_ref=scope['id'],role='addressee',
        original_claim=deepcopy(scope['roles']['addressee']),original_role_unchanged=True,
        corrections=[],referent_ids=[],proposed_mentions=[],rejected_mentions=[],
        p1_contrast_refs=[],p2_relation_refs=[],role_status='GRAMMATICAL_CANDIDATES',role_resolution=False,
        possible_roles=['ADDRESSEE','UNRESOLVED_OBLIQUE'],verified_fact=False,semantic_resolution=False))
    correction=dict(source_turn=row['id'],proposed=proposal,rejected=rejection,antecedent=antecedent,
        contrast_ref=contrast['id'],p1_source_hash=sa['provenance']['source_sha256'],
        source_ref=row['source_ref'],actor_claim=list(actor),
        omitted_predicate=not bool(units),omitted_preposition=a['kind']=='NP',
        role_basis='P1_PP_AND_P2_TARGET_SLOT' if a['kind']=='PP' else 'P2_TARGET_SLOT_FOR_P1_NOMINAL_ELLIPSIS')
    state['corrections'].append(correction)
    state['p1_contrast_refs'].append(dict(turn_ref=row['id'],contrast_ref=contrast['id'],
        proposed_group_ref=a['id'],rejected_group_ref=b['id'],raw_sha256=digest(row['text'])))
    state['p2_relation_refs'].extend(r for r in path if r not in state['p2_relation_refs'])
    variants={tuple(c['proposed']['token_norms']) for c in state['corrections']}
    state['status']='SOURCE_BOUND_ROLE_INTERPRETATION' if len(variants)==1 else 'CONFLICTING_CORRECTIONS'
    state['proposed_mentions']=[proposal] if len(variants)==1 else []
    state['rejected_mentions']=[c['rejected'] for c in state['corrections']]
