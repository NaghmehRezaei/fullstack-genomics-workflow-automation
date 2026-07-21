import csv,gzip,re,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
from .database import update_analysis

BASE=Path('/app')
PIPELINE=BASE/'pipelines/variant_calling.nf'
RESULTS=BASE/'results'
WORK=BASE/'work'

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def nextflow_version():
    completed=subprocess.run(['nextflow','-version'],capture_output=True,text=True)
    text=completed.stdout+'\n'+completed.stderr
    match=re.search(r'version\s+([0-9.]+)',text)
    return match.group(1) if match else 'unknown'

def run_name(log_text):
    match=re.search(r'Launching `[^`]+` \[([^\]]+)\]',log_text)
    return match.group(1) if match else None

def parse_trace(path):
    if not path.exists():
        return []
    rows=[]
    with path.open(encoding='utf-8') as handle:
        for row in csv.DictReader(handle,delimiter='\t'):
            exit_code=row.get('exit')
            rows.append({
                'task_id':row.get('task_id') or row.get('hash'),
                'process':row.get('name') or row.get('process') or 'UNKNOWN',
                'status':row.get('status','UNKNOWN'),
                'exit_code':int(exit_code) if exit_code and exit_code.isdigit() else None,
                'duration':row.get('duration'),
                'workdir':row.get('workdir')
            })
    return rows

def parse_vcf(path):
    variants=[]
    samples=[]
    with gzip.open(path,'rt',encoding='utf-8') as handle:
        for line in handle:
            if line.startswith('##'):
                continue
            if line.startswith('#CHROM'):
                samples=line.rstrip().split('\t')[9:]
                continue
            if line.startswith('#'):
                continue
            fields=line.rstrip().split('\t')
            fmt=fields[8].split(':')
            for sample,value in zip(samples,fields[9:]):
                data=dict(zip(fmt,value.split(':')))
                gt=data.get('GT')
                if gt in (None,'./.','0/0'):
                    continue
                variants.append({
                    'chromosome':fields[0],
                    'position':int(fields[1]),
                    'reference':fields[3],
                    'alternate':fields[4],
                    'quality':None if fields[5]=='.' else float(fields[5]),
                    'filter':fields[6],
                    'sample':sample,
                    'genotype':gt
                })
    return variants

def run_nextflow_analysis(analysis_id,tumor_file,normal_file,reference_fasta,tumor_sample,normal_sample):
    result_dir=RESULTS/str(analysis_id)
    work_dir=WORK/str(analysis_id)
    result_dir.mkdir(parents=True,exist_ok=True)
    work_dir.mkdir(parents=True,exist_ok=True)
    trace_file=result_dir/'trace.txt'
    report_file=result_dir/'report.html'
    log_file=result_dir/'nextflow.log'
    command=[
        'nextflow','run',str(PIPELINE),
        '--analysis_id',str(analysis_id),
        '--tumor',tumor_file,
        '--normal',normal_file,
        '--reference',reference_fasta,
        '--tumor_sample',tumor_sample,
        '--normal_sample',normal_sample,
        '--outdir',str(result_dir),
        '-work-dir',str(work_dir),
        '-with-trace',str(trace_file),
        '-with-report',str(report_file)
    ]
    version=nextflow_version()
    command_text=shlex.join(command)
    try:
        update_analysis(
            analysis_id,status='RUNNING',current_step='NEXTFLOW_VARIANT_CALLING',
            progress=10,updated_at=utc_now(),nextflow_version=version,
            workflow_command=command_text
        )
        completed=subprocess.run(command,capture_output=True,text=True)
        log_text=completed.stdout+'\n'+completed.stderr
        log_file.write_text(log_text,encoding='utf-8')
        processes=parse_trace(trace_file)
        if completed.returncode != 0:
            raise RuntimeError(f'Nextflow failed with exit code {completed.returncode}. See {log_file}.')
        variants=parse_vcf(result_dir/'combined.vcf.gz')
        update_analysis(
            analysis_id,status='COMPLETED',current_step='VARIANT_CALLING_DONE',
            progress=100,updated_at=utc_now(),results=variants,
            nextflow_version=version,nextflow_run_name=run_name(log_text),
            workflow_command=command_text,workflow_processes=processes
        )
    except Exception as exc:
        update_analysis(
            analysis_id,status='FAILED',current_step='NEXTFLOW_ERROR',progress=0,
            error_message=str(exc),updated_at=utc_now(),nextflow_version=version,
            nextflow_run_name=run_name(log_text) if 'log_text' in locals() else None,
            workflow_command=command_text,workflow_processes=parse_trace(trace_file)
        )
