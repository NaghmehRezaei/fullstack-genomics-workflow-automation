from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class AnalysisStatus(str, Enum):
    QUEUED='QUEUED'; RUNNING='RUNNING'; COMPLETED='COMPLETED'; FAILED='FAILED'

class AnalysisCreate(BaseModel):
    patient_id: str = Field(min_length=1,max_length=100)
    tumor_sample_id: str = Field(min_length=1,max_length=100)
    normal_sample_id: str = Field(min_length=1,max_length=100)
    tumor_file: str = '/app/input/reads/tumor.fastq'
    normal_file: str = '/app/input/reads/normal.fastq'
    reference_fasta: str = '/app/input/reference/toy_reference.fa'
    reference_genome: str = 'ToyGenome-v1'
    @model_validator(mode='after')
    def validate_pair(self):
        if self.tumor_sample_id == self.normal_sample_id:
            raise ValueError('Tumor and normal sample IDs must be different.')
        return self

class AnalysisRecord(BaseModel):
    analysis_id:int; patient_id:str; tumor_sample_id:str; normal_sample_id:str
    tumor_file:str; normal_file:str; reference_fasta:str; reference_genome:str
    status:AnalysisStatus; current_step:str; progress:int; error_message:Optional[str]=None
    workflow_engine:str; pipeline_name:str; nextflow_version:Optional[str]=None
    nextflow_run_name:Optional[str]=None; created_at:str; updated_at:str

class VariantResult(BaseModel):
    chromosome:str; position:int; reference:str; alternate:str
    quality:Optional[float]=None; filter:str; sample:str; genotype:Optional[str]=None

class WorkflowProcess(BaseModel):
    task_id:Optional[str]=None; process:str; status:str
    exit_code:Optional[int]=None; duration:Optional[str]=None; workdir:Optional[str]=None

class WorkflowDetails(BaseModel):
    analysis_id:int; workflow_engine:str; nextflow_version:Optional[str]=None
    pipeline_name:str; nextflow_run_name:Optional[str]=None; command:str
    trace_file:Optional[str]=None; log_file:Optional[str]=None; report_file:Optional[str]=None
    processes:list[WorkflowProcess]
