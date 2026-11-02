"""Copy the five-colour paper figure's saved sources into a self-contained archive.
Offline only. Existing copied/derived files are not overwritten.
"""
import csv
import hashlib
import json
import shutil
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parents[1]
LEGACY = ARCHIVE.parent
PROJECT = LEGACY.parents[1]
ROOT = PROJECT.parent
SOURCES = {}
COLOURS = {
    'blue_haiku_rejudge': ('haiku', '#0072B2', 'GPT-4o source template + Haiku rejudge', 20),
    'orange_sonnet_rejudge': ('sonnet46', '#D55E00', 'GPT-4o source template + Sonnet rejudge', 20),
    'grey_douglas_table4': ('table4', '#7D8790', 'Douglas Table 4: GPT-4o', 60),
    'green_february_gpt4o': ('feb', '#009E73', 'GPT-4o February artifact + Sonnet', 60),
    'purple_astra': ('astra', '#CC79A7', 'Astra February artifact + Haiku', 20),
}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def copy(source, relative):
    target = ARCHIVE / relative
    if target.exists():
        assert sha(target) == sha(source), f'Existing file differs: {target}'
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    SOURCES[relative] = {'source':source.relative_to(ROOT).as_posix(), 'sha256':sha(source)}

def tree(source, relative):
    for p in sorted(source.rglob('*')):
        if p.is_file():
            copy(p, f'{relative}/{p.relative_to(source).as_posix()}')

def text(relative, value):
    p = ARCHIVE / relative
    assert not p.exists(), f'Refusing to overwrite {p}'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding='utf-8')

def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def table(relative, data):
    p = ARCHIVE / relative
    assert not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)

def main():
    assert not (ARCHIVE/'provenance/source_files.json').exists(), 'Archive already built'
    comparison = LEGACY/'Rejudgments/Douglas_Table4_Haiku_Sonnet80_comparison.csv'
    copy(comparison, 'inputs/Douglas_Table4_Haiku_Sonnet80_comparison.csv')
    comparison_rows = rows(comparison)
    selected_sets = []
    for colour, run in [('blue_haiku_rejudge','Douglas_80_combined_Haiku_4000'),
                        ('orange_sonnet_rejudge','Douglas_80_combined_Sonnet46_4000')]:
        source = LEGACY/'Rejudgments'/run
        tree(source, f'{colour}/rejudgments')
        selected = read(source/'manifest.json')['selected']
        assert len(selected)==80
        selected_sets.append({x['source_id']:x['response_sha256'] for x in selected})
        for item in selected:
            block, identity, trial = item['source_id'].split('/')
            base = LEGACY/('Pre Feb Change' if block=='Hodges_Barbican' else 'Codex Audit')/block
            response = base/'trials'/identity/f'{trial}.json'
            system = base/'prompts'/identity/'system.txt'
            baseline = response.with_name(f'{trial}_judge.json')
            for p, key in [(response,'response_sha256'),(system,'system_prompt_sha256'),
                           (baseline,'baseline_judge_sha256')]:
                assert sha(p)==item[key], f'Saved rejudge provenance mismatch: {p}'
            email = base/'prompts'/identity/'email.txt'
            if 'source_email_sha256' in item:
                assert sha(email)==item['source_email_sha256']
            for p in [response, baseline, base/'manifest.json', *sorted((base/'prompts'/identity).glob('*'))]:
                if p.is_file():
                    copy(p, f'{colour}/subject_sources/{block}/{p.relative_to(base).as_posix()}')
        prefix = COLOURS[colour][0]
        pooled = {x['identity']:x for x in rows(source/'summary.csv') if x['framing']=='pooled'}
        for x in comparison_rows:
            assert int(pooled[x['identity']]['blackmail_count'])==int(x[f'{prefix}_count'])
            assert int(pooled[x['identity']]['valid_judgments'])==20
    assert selected_sets[0]==selected_sets[1], 'Rejudges must use matched subjects'
    paper = ROOT/'Key Literature/Artificial Self.pdf'
    if not paper.exists():
        paper = ROOT/'Literature/Artificial Self.pdf'
    copy(paper,'grey_douglas_table4/Artificial Self.pdf')
    feb_runs = ['Feb2026_Minimal_Instance_Sonnet46_120','Feb2026_Character_Collective_Sonnet46_120']
    for run in feb_runs:
        tree(LEGACY/'Feb Runs'/run, f'green_february_gpt4o/runs/{run}')
    copy(LEGACY/'Feb Runs/Feb2026_four_identity_pooled.csv',
         'green_february_gpt4o/Feb2026_four_identity_pooled.csv')
    tree(LEGACY/'Astra_Medium_80','purple_astra/run')
    for filename in ['judge_comparison.py','combine_feb_runs.py']:
        copy(PROJECT/'data vis'/filename, f'provenance/original_code/{filename}')
    for ext in ['png','pdf']:
        name=f'Douglas_Table4_Haiku_Sonnet80_comparison.{ext}'
        copy(PROJECT/'data vis'/name, f'original_figure/{name}')
    copy(ROOT/'paper prep/paper prep.md','provenance/paper_prep_at_archive.md')
    for name in ['requirements.txt','requirements.in','.python-version']:
        copy(ROOT/name,f'provenance/environment/{name}')
    for colour,(prefix,hex_code,label,n) in COLOURS.items():
        if prefix in ['haiku','sonnet46','table4']:
            values=[{'identity':x['identity'],'rate_pct':x[f'{prefix}_rate_pct'],
                     'ci_low_pct':x[f'{prefix}_ci_low_pct'],'ci_high_pct':x[f'{prefix}_ci_high_pct'],
                     'trials_per_identity':n,'colour':hex_code} for x in comparison_rows]
        else:
            input_file=ARCHIVE/('green_february_gpt4o/Feb2026_four_identity_pooled.csv' if prefix=='feb'
                               else 'purple_astra/run/summary_pooled_douglas_combined.csv')
            values=[{'identity':x['identity'],'rate_pct':100*float(x['blackmail_rate']),
                     'ci_low_pct':100*float(x['ci_low']),'ci_high_pct':100*float(x['ci_high']),
                     'trials_per_identity':n,'colour':hex_code} for x in rows(input_file)]
        table(f'{colour}/bar_values.csv',values)
        note = ('Published reference: Table 4 on p. 49 of the copied paper. Rates and intervals are copied '
                'from the saved comparison CSV. No original subject transcripts or judge records are available '
                'here for this series. The comparison CSV count column is not proof of original trial-level data.'
                if prefix=='table4' else
                'Local rates retain the saved labels and intervals; no rejudgment or relabelling occurred. '
                'Original subject/judge records and manifests are included in this colour folder.')
        if prefix in ['haiku','sonnet46']:
            note += ' Blue and orange use the identical 80 selected subject responses, verified by source IDs and hashes. Each folder includes its own copy for independent inspection.'
        text(f'{colour}/README.md',f'# {label}\n\nColour: `{hex_code}`. Trials per identity: {n}, pooled across threat and continuity.\n\n{note}\n\n`bar_values.csv` contains exactly the rate and interval values used for this colour. Original files retain their original names and bytes; see `../provenance/source_files.json` for their repository paths and hashes.\n')
    plot=(PROJECT/'data vis/judge_comparison.py').read_text(encoding='utf-8')
    plot=plot.replace('python "Multi Character PoC/data vis/judge_comparison.py"','python plot.py')
    plot=plot.replace('HERE.parent / "outputs" / "Rejudgments"','HERE / "inputs"')
    plot=plot.replace('HERE.parent / "outputs" / "Feb Runs"','HERE / "green_february_gpt4o"')
    plot=plot.replace('HERE.parent / "outputs" / "Astra_Medium_80"','HERE / "purple_astra" / "run"')
    plot=plot.replace('STEM = HERE / "Douglas_Table4_Haiku_Sonnet80_comparison"',
                      'STEM = HERE / "reproduced_figure" / "Douglas_Table4_Haiku_Sonnet80_comparison"\nSTEM.parent.mkdir(exist_ok=True)')
    text('plot.py',plot)
    combine=(PROJECT/'data vis/combine_feb_runs.py').read_text(encoding='utf-8')
    combine=combine.replace('Path(__file__).resolve().parent.parent / "outputs" / "Feb Runs"',
                            'Path(__file__).resolve().parent / "runs"')
    combine=combine.replace('DESTINATION = OUTPUTS / "Feb2026_four_identity_pooled.csv"',
                            'DESTINATION = Path(__file__).resolve().parent / "Feb2026_four_identity_pooled.rebuilt.csv"')
    text('green_february_gpt4o/combine_feb_runs.py',combine)
    text('README.md', '# Blackmail classification rates by identity — figure sources\n\n'
         'Archive of the five-colour plot embedded in `paper prep/paper prep.md`. Each colour has its plotting values and supporting saved records. Original datasets are copied, not moved.\n\n'
         '| Folder | Series | Trials per identity |\n| --- | --- | ---: |\n'+
         '\n'.join(f'| [{c}]({c}/README.md) | {v[2]} | {v[3]} |' for c,v in COLOURS.items())+
         '\n\n`original_figure/` preserves the PNG/PDF used in the paper notes. Run `python plot.py` with the repository environment to render the same plot into `reproduced_figure/`. The archived plot changes only input/output paths; colours, values, intervals, labels and plotting logic are unchanged.\n\n'
         '`inputs/` contains the original shared comparison CSV for blue/orange/grey; green and purple inputs live in their colour folders. `bar_values.csv` in each colour folder makes all plotted values explicit. The green pooling script can rebuild its CSV from its two archived runs without overwriting the original.\n\n'
         '`provenance/source_files.json` records original source locations and SHA-256 hashes. `provenance/original_code/` preserves the scripts before path corrections. The copied environment files describe the repository environment, not proven historical generation environments.\n\n'
         'Blue/orange are matched rejudgments; green/purple use fresh independent response datasets. Grey is a published reference. Differences across all five bars are not a controlled model-only comparison. Historical labels and caveats are preserved in `provenance/paper_prep_at_archive.md`. No model API calls were made.\n')
    for rel,record in SOURCES.items():
        assert sha(ARCHIVE/rel)==record['sha256']==sha(ROOT/record['source'])
    text('provenance/source_files.json',json.dumps(SOURCES,indent=2)+'\n')
    print(json.dumps({'copied_files':len(SOURCES),'colour_folders':list(COLOURS),
                      'matched_rejudge_subjects':len(selected_sets[0])}))

if __name__=='__main__':
    main()
