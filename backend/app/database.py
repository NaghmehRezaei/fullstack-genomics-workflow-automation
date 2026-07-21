import json, sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH=Path('/app/data/genomics_v3.db')
DB_PATH.parent.mkdir(parents=True,exist_ok=True)

@contextmanager
def get_connection():
    conn=sqlite3.connect(DB_PATH,check_same_thread=False)
    conn.row_factory=sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            tumor_sample_id TEXT NOT NULL,
            normal_sample_id TEXT NOT NULL,
            tumor_file TEXT NOT NULL,
            normal_file TEXT NOT NULL,
            reference_fasta TEXT NOT NULL,
            reference_genome TEXT NOT NULL,
            status TEXT NOT NULL,
            current_step TEXT NOT NULL,
            progress INTEGER NOT NULL,
            error_message TEXT,
            results_json TEXT,
            workflow_engine TEXT NOT NULL,
            pipeline_name TEXT NOT NULL,
            nextflow_version TEXT,
            nextflow_run_name TEXT,
            workflow_command TEXT,
            workflow_processes_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

def create_analysis(payload, now):
    with get_connection() as conn:
        cur=conn.execute("""
        INSERT INTO analyses (
            patient_id,tumor_sample_id,normal_sample_id,tumor_file,normal_file,
            reference_fasta,reference_genome,status,current_step,progress,
            workflow_engine,pipeline_name,created_at,updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
            payload['patient_id'],payload['tumor_sample_id'],payload['normal_sample_id'],
            payload['tumor_file'],payload['normal_file'],payload['reference_fasta'],
            payload['reference_genome'],'QUEUED','WAITING_FOR_NEXTFLOW',0,
            'Nextflow','variant_calling.nf',now,now
        ))
        return int(cur.lastrowid)

def get_analysis(analysis_id):
    with get_connection() as conn:
        row=conn.execute('SELECT * FROM analyses WHERE analysis_id=?',(analysis_id,)).fetchone()
    return dict(row) if row else None

def update_analysis(analysis_id, **kwargs):
    current=get_analysis(analysis_id)
    data=dict(current)
    for key,value in kwargs.items():
        if value is not None:
            data[key]=value
    if kwargs.get('results') is not None:
        data['results_json']=json.dumps(kwargs['results'])
    if kwargs.get('workflow_processes') is not None:
        data['workflow_processes_json']=json.dumps(kwargs['workflow_processes'])
    with get_connection() as conn:
        conn.execute("""
        UPDATE analyses SET status=?,current_step=?,progress=?,error_message=?,
        results_json=?,nextflow_version=?,nextflow_run_name=?,workflow_command=?,
        workflow_processes_json=?,updated_at=? WHERE analysis_id=?
        """,(
            data['status'],data['current_step'],data['progress'],data.get('error_message'),
            data.get('results_json'),data.get('nextflow_version'),data.get('nextflow_run_name'),
            data.get('workflow_command'),data.get('workflow_processes_json'),
            data['updated_at'],analysis_id
        ))

def get_results(analysis_id):
    row=get_analysis(analysis_id)
    return json.loads(row['results_json']) if row and row.get('results_json') else []

def get_processes(analysis_id):
    row=get_analysis(analysis_id)
    return json.loads(row['workflow_processes_json']) if row and row.get('workflow_processes_json') else []
