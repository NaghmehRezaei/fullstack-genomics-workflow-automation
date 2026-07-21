from datetime import datetime,timezone
from pathlib import Path
from fastapi import BackgroundTasks,FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from .database import create_analysis,get_analysis,get_processes,get_results,initialize_database
from .models import AnalysisCreate,AnalysisRecord,VariantResult,WorkflowDetails,WorkflowProcess
from .worker import run_nextflow_analysis

BASE=Path('/app')
PIPELINE=BASE/'pipelines/variant_calling.nf'
RESULTS=BASE/'results'

app=FastAPI(
    title='Genomics Variant Calling Platform API',
    version='3.0.0',
    description='React + FastAPI + SQLite + a real Nextflow DSL2 workflow using BWA, SAMtools, and BCFtools for small-scale variant calling.'
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000','http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.on_event('startup')
def startup():
    initialize_database()

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def public_record(row):
    return AnalysisRecord(**{field:row[field] for field in AnalysisRecord.model_fields})

@app.get('/health')
def health():
    return {'status':'ok','workflow_engine':'Nextflow','pipeline':'variant_calling.nf'}

@app.post('/analyses',response_model=AnalysisRecord,status_code=201)
def submit_analysis(request:AnalysisCreate,background_tasks:BackgroundTasks):
    analysis_id=create_analysis(request.model_dump(),utc_now())
    background_tasks.add_task(
        run_nextflow_analysis,analysis_id,request.tumor_file,request.normal_file,
        request.reference_fasta,request.tumor_sample_id,request.normal_sample_id
    )
    return public_record(get_analysis(analysis_id))

@app.get('/analyses/{analysis_id}',response_model=AnalysisRecord)
def read_analysis(analysis_id:int):
    row=get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404,detail='Analysis not found.')
    return public_record(row)

@app.get('/analyses/{analysis_id}/status')
def read_status(analysis_id:int):
    row=get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404,detail='Analysis not found.')
    keys=['analysis_id','workflow_engine','pipeline_name','nextflow_version','nextflow_run_name','status','current_step','progress','error_message']
    return {key:row.get(key) for key in keys}

@app.get('/analyses/{analysis_id}/results',response_model=list[VariantResult])
def read_results(analysis_id:int):
    row=get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404,detail='Analysis not found.')
    if row['status']!='COMPLETED':
        raise HTTPException(status_code=409,detail=f"Analysis is not complete. Current status: {row['status']}")
    return [VariantResult(**item) for item in get_results(analysis_id)]

@app.get('/analyses/{analysis_id}/workflow',response_model=WorkflowDetails)
def read_workflow(analysis_id:int):
    row=get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404,detail='Analysis not found.')
    result_dir=RESULTS/str(analysis_id)
    return WorkflowDetails(
        analysis_id=analysis_id,
        workflow_engine=row['workflow_engine'],
        nextflow_version=row['nextflow_version'],
        pipeline_name=row['pipeline_name'],
        nextflow_run_name=row['nextflow_run_name'],
        command=row['workflow_command'] or '',
        trace_file=str(result_dir/'trace.txt'),
        log_file=str(result_dir/'nextflow.log'),
        report_file=str(result_dir/'report.html'),
        processes=[WorkflowProcess(**item) for item in get_processes(analysis_id)]
    )

@app.get('/analyses/{analysis_id}/workflow/log',response_class=PlainTextResponse)
def read_workflow_log(analysis_id:int):
    path=RESULTS/str(analysis_id)/'nextflow.log'
    if not path.exists():
        raise HTTPException(status_code=404,detail='Nextflow log not available yet.')
    return path.read_text(encoding='utf-8')

@app.get('/analyses/{analysis_id}/workflow/code',response_class=PlainTextResponse)
def read_workflow_code(analysis_id:int):
    if not get_analysis(analysis_id):
        raise HTTPException(status_code=404,detail='Analysis not found.')
    return PIPELINE.read_text(encoding='utf-8')

@app.get('/analyses/{analysis_id}/vcf',response_class=PlainTextResponse)
def read_vcf(analysis_id:int):
    path=RESULTS/str(analysis_id)/'combined.vcf'
    if not path.exists():
        raise HTTPException(status_code=404,detail='VCF not available.')
    return path.read_text(encoding='utf-8')
