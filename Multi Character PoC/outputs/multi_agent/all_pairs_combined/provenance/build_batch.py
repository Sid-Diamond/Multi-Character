"""Offline, reproducible assembly of 15 unordered pairs. Never calls model APIs.

Default verifies an existing frozen assembly, or audits current sources if absent.
--audit inventories current sources. --build creates a new assembly without overwrite.
--destination PATH supports a new revision after collecting any missing trials.
--extend adds new pairs to the existing assembly, preserving every existing run.
"""
import argparse
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import math
import shutil
from datetime import datetime, timezone
from itertools import combinations_with_replacement
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
MULTI = HOME.parent
PROJECT = MULTI.parents[1]
IDS = ('Character', 'Instance', 'Minimal', 'collective_excludes', 'collective_includes')
FRAMINGS = ('threat', 'continuity')
PAIRS = { '__'.join(x.lower() for x in p): p for p in combinations_with_replacement(IDS, 2) }
RULE = ('First 25 valid, distinct completed groups per unordered pair and framing, '
        'ordered by earliest subject API creation time (Unix seconds), then original '
        'trial path relative to outputs/multi_agent. Selection is independent of outcome.')

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def common(m):
    flat = {k: v for k, v in m['settings'].items()
            if k not in ('run_name', 'identities_per_trial', 'trials_per_group')}
    workflow = copy.deepcopy(m['workflow']['settings'])
    workflow.pop('run_name', None)
    for key in ('identities_per_trial', 'trials_per_group'):
        workflow['multi_agent'].pop(key, None)
    return {'settings': flat, 'workflow_settings': workflow,
            **{k: m[k] for k in ('source_sha256', 'judge_protocol', 'schedule',
                                  'completion', 'peer_message_count', 'incomplete_policy')},
            'workflow_sources': m['workflow']['source_sha256']}

def candidates():
    # Original trials only: assembled copies and historical conditions are excluded.
    patterns = ('1-min1-else-big/1min_1else_big/*/*/manifest.json',
                'remaining/2per-big/2_per_big/*/*/manifest.json',
                '2per-big/2_per_big/*/*/manifest.json',
                'remaining/*/*/manifest.json',
                'remaining_pairs_big/multi_agent/*/*/manifest.json',
                'colexclincl/*/manifest.json')
    return sorted({p for pattern in patterns for p in MULTI.glob(pattern)})

def audit():
    reference = MULTI / '1-min1-else-big/1min_1else_big/min_2agents_n10/char/manifest.json'
    baseline = read(reference)
    files = {reference.relative_to(MULTI).as_posix(): sha(reference)}
    manifests, templates, prompts, items, issues = {}, {}, {}, [], []
    buckets = collections.defaultdict(list)
    owners, trial_hashes = {}, {}
    for mp in candidates():
        relm = mp.relative_to(MULTI).as_posix()
        m = read(mp)
        pair = tuple(sorted((a['identity'] for a in m['agents']), key=IDS.index))
        run = '__'.join(x.lower() for x in pair)
        if run not in PAIRS:
            continue
        files[relm] = sha(mp)
        manifests[relm] = {'run_name': run, 'sha256': files[relm], 'manifest': m}
        error = None
        try:
            require(m['N'] == 2 and len(m['agents']) == 2, 'Not a two-agent run')
            expected = dict(collections.Counter(pair))
            require({k:v for k,v in m['settings']['identities_per_trial'].items() if v} == expected,
                    'Manifest roster/count mismatch')
            require(m['workflow']['settings']['multi_agent']['identities_per_trial'] ==
                    m['settings']['identities_per_trial'], 'Workflow/runner composition mismatch')
            require(common(m) == common(baseline), 'Incompatible scientific settings, protocol or source hashes')
            if run in templates:
                require(m['agents'] == templates[run]['manifest']['agents'], 'Different roster order')
            templates.setdefault(run, {'source': relm, 'manifest': m})
        except (ValueError, KeyError) as e:
            error = str(e)
            issues.append({'source': relm, 'reason': error})
        for framing in FRAMINGS:
            pp = mp.parent / framing / 'prompts.json'
            prompt_error = error
            if pp.exists():
                relp = pp.relative_to(MULTI).as_posix()
                files[relp] = sha(pp)
                key = (run, framing)
                if not error:
                    if key in prompts and read(pp) != read(MULTI / prompts[key]):
                        prompt_error = 'Different rendered prompts'
                        issues.append({'source': relp, 'reason': prompt_error})
                    else:
                        prompts.setdefault(key, relp)
            else:
                prompt_error = prompt_error or 'Missing rendered prompts'
            for tp in sorted((mp.parent / framing / 'trials').glob('*.json')):
                if not tp.stem.isdigit():
                    continue
                rel = tp.relative_to(MULTI).as_posix()
                digest = sha(tp)
                files[rel] = digest
                t = read(tp)
                item = {'source': rel, 'source_manifest': relm, 'source_sha256': digest,
                        'run_name': run, 'framing': framing, 'original_trial': int(tp.stem),
                        'original_status': t.get('status'), 'H_any': t.get('H_any'),
                        'disposition': 'incomplete'}
                items.append(item)
                if t.get('status') != 'complete':
                    continue
                try:
                    require(not prompt_error, prompt_error)
                    j = t['group_judgment']
                    require(type(t.get('H_any')) is bool and t['H_any'] == j['released_label'] ==
                            (j['semantic_verdict'] and j['released_domain_gate']), 'Invalid outcome/gate')
                    require(set(t['agents']) == {a['name'] for a in m['agents']} and
                            all(a['finished'] for a in t['agents'].values()), 'Unfinished/mismatched agents')
                    require(t['judge_protocol'] == m['judge_protocol'], 'Judge protocol mismatch')
                    require(any(c['stage'] == 'judge' for c in t['calls']), 'Missing judge call')
                    times, rids = [], []
                    for c in t['calls']:
                        require(c['status'] == 'returned', 'Incomplete API call')
                        require(c['stage'] in ('subject', 'judge'), 'Unknown call stage')
                        expected_model = m['settings']['model' if c['stage']=='subject' else 'judge_model']
                        require(c['requested_model'] == expected_model, 'Requested model mismatch')
                        rid = c['raw'].get('id')
                        require(bool(rid), 'Missing response ID')
                        rids.append(rid)
                        created = c['raw'].get('created')
                        if c['stage']=='subject' and type(created) in (int,float) and math.isfinite(created):
                            times.append(created)
                    require(times and len(set(rids)) == len(rids), 'Missing timestamp/reused response')
                    item['first_subject_created'] = min(times)
                    item['first_speaker'] = next(c['agent'] for c in t['calls'] if c['stage']=='subject')
                    if digest in trial_hashes:
                        item.update(disposition='duplicate', duplicate_of=trial_hashes[digest])
                        continue
                    require(not any(rid in owners for rid in rids), 'Response reused in different trial records')
                    owners.update({rid: rel for rid in rids})
                    trial_hashes[digest] = rel
                    item['disposition'] = 'surplus'
                    buckets[run, framing].append(item)
                except (ValueError, KeyError, TypeError) as e:
                    item.update(disposition='invalid_or_incompatible', reason=str(e))
    selected, cells = [], []
    for run, pair in PAIRS.items():
        require(run in templates, f'No compatible manifest for {run}')
        for framing in FRAMINGS:
            rows = sorted(buckets[run, framing], key=lambda r:(r['first_subject_created'],r['source']))
            chosen = rows[:25]
            for n, item in enumerate(chosen, 1):
                item.update(disposition='selected', trial=n, destination=f'{run}/{framing}/trials/{n:03}.json')
                selected.append(item)
            cells.append({'run_name':run, 'identities':pair, 'framing':framing, 'target':25,
                          'available_complete':len(rows), 'selected':len(chosen),
                          'missing':25-len(chosen), 'surplus':max(0,len(rows)-25),
                          'H_any_count':sum(r['H_any'] for r in chosen)})
    return {'baseline':baseline, 'manifests':manifests, 'templates':templates, 'prompts':prompts,
            'items':items, 'selected':selected, 'cells':cells, 'source_files':files, 'issues':issues}

def csv_module(path):
    spec = importlib.util.spec_from_file_location('assembly_csv_exports', path)
    module = importlib.util.module_from_spec(spec)
    # Compile directly: no __pycache__ mutation in the source repository.
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module

def build(a, dest, extend=False):
    if extend:
        prior = read(dest/'provenance/audit.json')
        inventory = read(dest/'provenance/artifact_sha256.json')
        archived_builder = dest/'provenance/revisions/14_pairs/provenance/build_batch.py'
        for rel, digest in inventory.items():
            path = archived_builder if rel == 'provenance/build_batch.py' else dest/rel
            require(sha(path)==digest, f'Prior assembly changed: {rel}')
        previous = {i['destination']:i for i in prior['all_source_trials'] if i['disposition']=='selected'}
        proposed = {i['destination']:i for i in a['selected']}
        require(all(key in proposed and proposed[key]['source_sha256']==old['source_sha256']
                    and proposed[key]['source']==old['source'] for key,old in previous.items()),
                'Extension would change an existing selected trial')
        old_runs = {i['run_name'] for i in previous.values()}
        require(all(sum(i['run_name']==run for i in a['selected']) ==
                    sum(i['run_name']==run for i in previous.values()) for run in old_runs),
                'Extension only supports adding new pairs; use a fresh revision to fill existing runs')
        require(any(not (dest/run).exists() for run in PAIRS), 'No new pair to add')
    else:
        require(not (dest/'analysis').exists() and not (dest/'queue_info').exists() and
                all(not (dest/run).exists() for run in PAIRS), 'Refusing to overwrite an existing assembly')
    for rel,digest in a['source_files'].items():
        require(sha(MULTI/rel)==digest, f'Source changed since audit: {rel}')
    dest.mkdir(parents=True,exist_ok=True)
    prov = dest/'provenance'
    prov.mkdir(exist_ok=True)
    if Path(__file__).resolve() != (prov/'build_batch.py').resolve():
        shutil.copyfile(__file__, prov/'build_batch.py')
    exporter_source = HOME/'provenance/csv_exports.py'
    if not exporter_source.exists():
        exporter_source = PROJECT/'csv_exports.py'
    if exporter_source.resolve() != (prov/'csv_exports.py').resolve():
        shutil.copyfile(exporter_source, prov/'csv_exports.py')
    exporter = csv_module(prov/'csv_exports.py')
    utc = datetime.now(timezone.utc).isoformat()
    aggregation = {'artifact_type':'offline_concatenation', 'created_utc':utc, 'selection_rule':RULE,
        'target_per_framing':25, 'original_trials_byte_preserved':True,
        'execution_note':'Original roster order and first-speaker rotation resets at source-run boundaries are preserved. Renumbering does not imply continuous alternation.',
        'budget_note':'Source max_cost applies per original run; this assembled dataset has no execution budget. Exported costs cover selected calls only.',
        'not_for_paid_resume':True}
    shared = common(a['baseline'])['workflow_settings']
    shared['multi_agent']['trials_per_group'] = {f:25 for f in FRAMINGS}
    entries, statuses, archive_map = [], {}, {}
    for run,pair in PAIRS.items():
        folder = dest/run
        template = a['templates'][run]['manifest']
        m = copy.deepcopy(template)
        rows = [i for i in a['selected'] if i['run_name']==run]
        cells = [c for c in a['cells'] if c['run_name']==run]
        counts = {f:sum(i['framing']==f for i in rows) for f in FRAMINGS}
        if extend and folder.exists():
            existing = read(folder/'manifest.json')
            for record in existing['aggregation']['source_manifests']:
                archive_map[record['source']] = f"{run}/{record['archived_manifest']}"
            for item in rows:
                item['archived_source_manifest'] = archive_map[item['source_manifest']]
            entries.append({'run_name':run,'identities_per_trial':existing['settings']['identities_per_trial']})
            statuses[run]='complete' if len(rows)==50 else 'partial'
            continue
        source_records=[]
        for index,(rel,record) in enumerate(sorted((k,v) for k,v in a['manifests'].items() if v['run_name']==run),1):
            archive = f'{run}/provenance/manifests/source_{index:03}.json'
            target=dest/archive
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(MULTI/rel,target)
            archive_map[rel]=archive
            source_records.append({'source':rel,'sha256':record['sha256'],
                'archived_manifest':f'provenance/manifests/source_{index:03}.json',
                'selected_trials':sum(i['source_manifest']==rel for i in rows),
                'original_run_name':record['manifest']['settings']['run_name']})
        settings=copy.deepcopy(shared)
        settings['run_name']=run
        settings['multi_agent']['identities_per_trial']=m['settings']['identities_per_trial']
        m['settings'].update(run_name=run,trials_per_group={f:25 for f in FRAMINGS})
        m['workflow']['settings']=settings
        m['schedule']='round_robin_rotating_first_agent_with_source_batch_resets'
        m['aggregation']={**aggregation,'selected_counts':counts,
                          'missing_counts':{f:25-counts[f] for f in FRAMINGS},
                          'source_root_relative_to_dataset':'..',
                          'source_manifests':source_records,'trial_sources':'provenance/trial_sources.csv'}
        write(folder/'manifest.json',m)
        for framing in FRAMINGS:
            (folder/framing/'trials').mkdir(parents=True,exist_ok=True)
            source=a['prompts'].get((run,framing))
            if source:
                shutil.copyfile(MULTI/source,folder/framing/'prompts.json')
        for item in rows:
            shutil.copyfile(MULTI/item['source'],dest/item['destination'])
            item['archived_source_manifest']=archive_map[item['source_manifest']]
        summary=[]
        for framing in (*FRAMINGS,'pooled'):
            selected=[i for i in rows if framing=='pooled' or i['framing']==framing]
            n=len(selected); positives=sum(i['H_any'] for i in selected)
            summary.append({'framing':framing,'attempts':n,'valid_groups':n,'incomplete_groups':0,
                            'H_any_count':positives,'H_any_rate':positives/n if n else None,
                            'target_groups':50 if framing=='pooled' else 25,
                            'missing_groups':(50 if framing=='pooled' else 25)-n})
        write(folder/'summary.json',summary)
        exporter.export_run(folder,'multi_agent',settings,dest.name)
        exporter.write_csv(folder/'provenance/trial_sources.csv',rows)
        write(folder/'provenance/source_manifests.json',source_records)
        entries.append({'run_name':run,'identities_per_trial':m['settings']['identities_per_trial']})
        statuses[run]='complete' if len(rows)==50 else 'partial'
    exporter.concatenate(dest,list(PAIRS))
    exporter.write_csv(prov/'trial_sources.csv',a['selected'])
    exporter.write_csv(dest/'analysis/coverage.csv',a['cells'])
    gaps=[c for c in a['cells'] if c['missing']]
    write(dest/'analysis/gaps.json',{'target_groups':len(PAIRS)*50,'selected_groups':len(a['selected']),
        'missing_groups':sum(c['missing'] for c in gaps),'cells':gaps,
        'excluded_pairs':[]})
    write(dest/'queue_info/queue.json',{'format_version':1,'batch_name':dest.name,'settings':shared,
        'runs':entries,'source_sha256':a['baseline']['workflow']['source_sha256'],'aggregation':aggregation})
    write(dest/'queue_info/queue_status.json',{'status':'partial' if gaps else 'complete','current_run':None,
        'updated_utc':utc,'runs':statuses,'artifact_type':'offline_concatenation',
        'selected_groups':len(a['selected']),'missing_groups':sum(c['missing'] for c in gaps)})
    with (dest/'queue_info/events.jsonl').open('a' if extend else 'w',encoding='utf-8') as stream:
        stream.write(json.dumps({'utc':utc,'event':'batch_extended_offline' if extend else 'batch_assembled_offline',
            'selected_groups':len(a['selected']),'missing_groups':sum(c['missing'] for c in gaps)})+'\n')
    write(prov/'audit.json',{'created_utc':utc,'selection_rule':RULE,'source_root':'..',
        'counts':dict(collections.Counter(i['disposition'] for i in a['items'])),
        'cells':a['cells'],'all_source_trials':a['items'],'source_file_sha256':a['source_files'],
        'issues':a['issues'],'source_manifest_archives':archive_map,
        'builder_sha256':sha(prov/'build_batch.py'),'csv_exporter_sha256':sha(prov/'csv_exports.py')})
    lines=['# Combined two-agent identity pairs','',
        f'{len(a["selected"])} selected groups across {len(PAIRS)} unordered pairs; target {len(PAIRS)*50}. All five identities and all 15 unordered pairings are included.','',
        RULE,'','| Pair | Threat | Continuity | Missing |','| --- | ---: | ---: | ---: |']
    for run in PAIRS:
        cells=[c for c in a['cells'] if c['run_name']==run]
        lines.append(f'| {run} | {cells[0]["selected"]}/25 | {cells[1]["selected"]}/25 | {sum(c["missing"] for c in cells)} |')
    lines += ['', 'Each pair has a consolidated manifest, original source manifests under `provenance/manifests/`, prompts, byte-preserved trials, summary, trial/diagnostic CSVs and a source map. Source paths in provenance are relative to the parent `outputs/multi_agent/` directory.',
        '', '`analysis/trials.csv` and `analysis/diagnostics.csv` concatenate the pair exports. `coverage.csv` and `gaps.json` record targets and shortfalls. Missing outcomes are never imputed. Incomplete, surplus, duplicate and incompatible records are inventoried in `provenance/audit.json` and remain in their original folders.',
        '', aggregation['execution_note'], '', aggregation['budget_note'],
        '', 'Generation/workflow source hashes remain in manifests. Builder and exporter hashes are recorded separately. No inference or rejudgment occurred. Queue files describe an offline artifact; do not use this directory to resume a paid experiment.',
        '', 'Run `python provenance/build_batch.py` to verify the frozen assembly and source hashes. `--audit` audits current source data without changing the assembly. To fill gaps later, build a fresh sibling revision with `--build --destination ../all_pairs_combined_v2`. Discovery uses original collection folders, excluding prior combined copies and legacy conditions.',
        '', 'The original 14-pair assembly was extended in place with Includes + Excludes on 27 October 2026. Its 700 selected trial files and all 14 existing run folders were unchanged. Previous combined metadata and the original builder are archived under `provenance/revisions/14_pairs/`; the queue event history records both operations.', '']
    (dest/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    # Freeze every derived artifact; future source discovery cannot change verification.
    inventory={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()
               and p != prov/'artifact_sha256.json'}
    write(prov/'artifact_sha256.json',inventory)
    verify(dest)

def verify(dest):
    a=read(dest/'provenance/audit.json')
    inventory=read(dest/'provenance/artifact_sha256.json')
    for rel,digest in inventory.items():
        require(sha(dest/rel)==digest,f'Artifact hash mismatch: {rel}')
    for rel,digest in a['source_file_sha256'].items():
        require(sha(MULTI/rel)==digest,f'Source hash changed: {rel}')
    chosen=[i for i in a['all_source_trials'] if i['disposition']=='selected']
    expected={i['destination'] for i in chosen}
    require({p.relative_to(dest).as_posix() for p in dest.glob('*/*/trials/*.json')}==expected,
            'Unexpected/missing destination trials')
    for item in chosen:
        require(sha(dest/item['destination'])==item['source_sha256'],'Copied trial hash mismatch')
    for rel,archive in a['source_manifest_archives'].items():
        require(sha(dest/archive)==a['source_file_sha256'][rel],'Archived manifest mismatch')
    for run in PAIRS:
        expected_count=sum(i['run_name']==run for i in chosen)
        for name in ('trials.csv','diagnostics.csv'):
            with (dest/run/name).open(encoding='utf-8-sig',newline='') as stream:
                rows=list(csv.DictReader(stream))
            require(len(rows)==expected_count,'Run CSV row count mismatch')
            require(all(r['status']=='complete' and (dest/run/r['source']).is_file() for r in rows),'Invalid run CSV record')
    for name in ('trials.csv','diagnostics.csv'):
        with (dest/'analysis'/name).open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.DictReader(stream))
        require(len(rows)==len(chosen)==len({(r['run_name'],r['trial_id']) for r in rows}),'Analysis CSV count/uniqueness mismatch')
        require(all((dest/'analysis'/r['source']).is_file() for r in rows),'Broken analysis source link')
    return {'verified_groups':len(chosen),'missing_groups':sum(c['missing'] for c in a['cells']),
            'dispositions':a['counts']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--build',action='store_true')
    mode.add_argument('--audit',action='store_true')
    mode.add_argument('--extend',action='store_true')
    parser.add_argument('--destination',type=Path,default=HOME)
    args=parser.parse_args()
    dest=args.destination.resolve()
    if not args.build and not args.audit and not args.extend and (dest/'provenance/audit.json').exists():
        print(json.dumps(verify(dest),indent=2))
    else:
        result=audit()
        if args.build or args.extend:
            build(result,dest,extend=args.extend)
        print(json.dumps({'selected_groups':len(result['selected']),
            'cells':result['cells'],'issues':result['issues'],
            'dispositions':dict(collections.Counter(i['disposition'] for i in result['items'])),
            'built':args.build or args.extend},indent=2))
