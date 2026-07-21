# Full-Stack Genomics Workflow Automation

A functional MVP demonstrating how a modern web application can submit, run, monitor, and display a real genomics workflow.

This project connects a React frontend, FastAPI backend, SQLite database, Docker environment, and Nextflow DSL2 pipeline into one complete workflow automation platform.

The included BWA, SAMtools, BCFtools, and Tabix pipeline uses small synthetic tumor and normal sequencing files to demonstrate real workflow execution. It is an example workload for the automation platform and is not intended to represent a clinical-grade or validated somatic variant-calling pipeline.

---

## Project purpose

Bioinformatics workflows are often executed through command-line tools, which can make them difficult for nontechnical users to submit, monitor, and troubleshoot.

I built this MVP to demonstrate how a genomic analysis can be wrapped inside a full-stack application.

A user can:

- Enter patient and sample information
- Submit tumor and normal FASTQ files
- Select a reference genome
- Start a Nextflow analysis
- Monitor workflow progress
- View process names, statuses, durations, and exit codes
- Inspect Nextflow logs and pipeline code
- Retrieve the final VCF file
- View parsed variant results in a web interface
- Access the same information through a REST API and Swagger UI

The main goal is to demonstrate full-stack workflow automation, job tracking, reproducibility, API integration, and bioinformatics pipeline orchestration.

---

## Architecture

```text
User
  ↓
React frontend
  ↓
FastAPI REST API
  ↓
SQLite analysis tracking
  ↓
Background worker
  ↓
Nextflow DSL2
  ├── INDEX_REFERENCE
  ├── ALIGN_SAMPLE
  ├── CALL_SAMPLE_VARIANTS
  └── MERGE_AND_FILTER
  ↓
BWA + SAMtools + BCFtools + Tabix
  ↓
BAM, VCF, logs, trace files, and statistics
  ↓
FastAPI result parsing
  ↓
React dashboard and Swagger UI
```

A simplified view of the platform is:

```text
React → FastAPI → SQLite → Nextflow → Bioinformatics tools → Results → React/Swagger
```

---

## What this project demonstrates

This project demonstrates how to build and connect several layers of a scientific software platform.

### Frontend

The React frontend provides a simple interface for submitting an analysis and viewing the results.

The user can enter:

- Patient ID
- Tumor sample ID
- Normal sample ID
- Tumor FASTQ path
- Normal FASTQ path
- Reference FASTA path
- Reference genome name

The frontend displays:

- Analysis ID
- Current status
- Workflow engine
- Pipeline name
- Nextflow version
- Nextflow run name
- Process status
- Process exit code
- Process duration
- Final called variants

### Backend API

The FastAPI backend:

- Receives analysis requests
- Validates submitted information
- Creates analysis records
- Stores job metadata in SQLite
- Launches the Nextflow pipeline
- Tracks workflow progress
- Reads Nextflow logs and trace files
- Parses the final VCF
- Returns workflow details and results through API endpoints

FastAPI also automatically generates Swagger documentation.

### Workflow orchestration

Nextflow DSL2 manages the scientific workflow.

Nextflow is responsible for:

- Receiving pipeline parameters
- Staging input files
- Running processes in the correct order
- Managing task dependencies
- Creating isolated work directories
- Capturing command output and errors
- Recording execution traces
- Reporting process status
- Publishing final outputs

Nextflow itself does not perform alignment or variant calling. It orchestrates the tools that perform those tasks.

### Containerization

Docker packages the backend, frontend, Java runtime, Nextflow, and bioinformatics tools into reproducible containers.

Docker Compose starts the complete application with one command.

---

## Technologies used

### Application layer

- React
- Vite
- FastAPI
- Python
- SQLite
- Nginx
- Docker
- Docker Compose

### Workflow layer

- Nextflow DSL2
- Java 21

### Bioinformatics tools

- BWA
- SAMtools
- BCFtools
- Tabix

---

## Role of each tool

### React

React provides the user-facing web interface for submitting analyses and viewing workflow results.

### FastAPI

FastAPI provides the backend REST API, receives requests, launches analyses, tracks status, parses results, and exposes the workflow through Swagger UI.

### SQLite

SQLite stores analysis metadata such as sample information, workflow status, progress, timestamps, errors, and Nextflow run information.

### Docker

Docker creates reproducible environments for the frontend and backend.

### Docker Compose

Docker Compose starts and connects the frontend and backend services.

### Java 21

Java provides the runtime required by Nextflow.

### Nextflow

Nextflow orchestrates the workflow, controls process dependencies, runs the tools, records logs, and manages outputs.

### BWA

BWA indexes the reference genome and aligns sequencing reads to the reference.

### SAMtools

SAMtools sorts, indexes, and checks the generated BAM files and creates the FASTA index.

### BCFtools

BCFtools examines the aligned reads, calls candidate variants, merges VCF files, normalizes variants, filters results, and generates statistics.

### Tabix

Tabix indexes compressed VCF files so genomic regions can be accessed efficiently.

---

## Workflow steps

The Nextflow pipeline contains four main processes.

### 1. `INDEX_REFERENCE`

This process prepares the reference genome.

It performs:

```bash
bwa index reference.fa
samtools faidx reference.fa
```

Outputs include:

- BWA reference index files
- FASTA index file

These files are required for alignment and downstream genomic analysis.

### 2. `ALIGN_SAMPLE`

This process runs once for the tumor sample and once for the normal sample.

BWA-MEM aligns FASTQ reads to the reference genome:

```bash
bwa mem reference.fa sample.fastq
```

The aligned reads are piped into SAMtools:

```bash
samtools sort -o sample.bam
```

SAMtools then creates a BAM index:

```bash
samtools index sample.bam
```

The BAM file is checked with:

```bash
samtools quickcheck
```

Outputs include:

- Tumor BAM
- Tumor BAM index
- Normal BAM
- Normal BAM index

### 3. `CALL_SAMPLE_VARIANTS`

This process runs separately for the tumor and normal BAM files.

BCFtools examines the alignments:

```bash
bcftools mpileup
```

Candidate variants are then called:

```bash
bcftools call
```

The result is written as a compressed VCF file.

Tabix creates the VCF index:

```bash
tabix -p vcf sample.vcf.gz
```

Outputs include:

- Tumor VCF
- Tumor VCF index
- Normal VCF
- Normal VCF index

### 4. `MERGE_AND_FILTER`

This process combines the tumor and normal VCF files.

It performs:

- VCF merging
- Variant normalization
- Simple quality filtering
- VCF indexing
- Human-readable VCF generation
- BCFtools statistics generation

Outputs include:

- `combined.vcf.gz`
- `combined.vcf.gz.tbi`
- `combined.vcf`
- `bcftools_stats.txt`

---

## Example workflow execution

A successful run contains the following completed processes:

```text
INDEX_REFERENCE
ALIGN_SAMPLE (TUMOR)
ALIGN_SAMPLE (NORMAL)
CALL_SAMPLE_VARIANTS (TUMOR)
CALL_SAMPLE_VARIANTS (NORMAL)
MERGE_AND_FILTER (tumor-normal)
```

Each process is displayed with:

- Status
- Exit code
- Duration

A successful workflow ends with:

```text
COMPLETED
VARIANT_CALLING_DONE
Progress: 100%
```

---

## API endpoints

FastAPI exposes the following endpoints.

### Health check

```http
GET /health
```

### Submit an analysis

```http
POST /analyses
```

### Read an analysis record

```http
GET /analyses/{analysis_id}
```

### Read the current analysis status

```http
GET /analyses/{analysis_id}/status
```

### Read parsed results

```http
GET /analyses/{analysis_id}/results
```

### Read workflow execution details

```http
GET /analyses/{analysis_id}/workflow
```

### Read the Nextflow log

```http
GET /analyses/{analysis_id}/workflow/log
```

### Read the Nextflow pipeline code

```http
GET /analyses/{analysis_id}/workflow/code
```

### Read the final VCF

```http
GET /analyses/{analysis_id}/vcf
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

---

## Project structure

```text
fullstack-genomics-workflow-automation/
│
├── README.md
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── worker.py
│   │
│   └── pipelines/
│       ├── main.nf
│       └── variant_calling.nf
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   │
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── main.jsx
│       └── styles.css
│
└── input/
    ├── reads/
    │   ├── tumor.fastq
    │   └── normal.fastq
    │
    ├── reference/
    │   └── toy_reference.fa
    │
    └── truth_variant.json
```

---

## How to run the project

### Requirements

Install:

- Docker Desktop
- Docker Compose
- Git

No local installation of Nextflow, Java, BWA, SAMtools, or BCFtools is required because they are installed inside the backend container.

### 1. Clone the repository

```bash
git clone https://github.com/NaghmehRezaei/fullstack-genomics-workflow-automation.git
```

Enter the project directory:

```bash
cd fullstack-genomics-workflow-automation
```

### 2. Build the containers

```bash
docker compose build --no-cache
```

### 3. Start the platform

```bash
docker compose up
```

### 4. Open the web interface

```text
http://localhost:3000
```

### 5. Open Swagger UI

```text
http://localhost:8000/docs
```

### 6. Start an analysis

The frontend is preconfigured with synthetic input files:

```text
Tumor FASTQ:
/app/input/reads/tumor.fastq

Normal FASTQ:
/app/input/reads/normal.fastq

Reference FASTA:
/app/input/reference/toy_reference.fa
```

Click:

```text
Start Nextflow Variant Calling
```

The analysis should progress from queued to completed.

### 7. Stop the platform

Press:

```text
Ctrl+C
```

Then run:

```bash
docker compose down
```

---

## Example API response

A completed analysis returns information similar to:

```json
{
  "analysis_id": 1,
  "patient_id": "PATIENT-105",
  "tumor_sample_id": "TUMOR",
  "normal_sample_id": "NORMAL",
  "reference_genome": "ToyGenome-v1",
  "status": "COMPLETED",
  "current_step": "VARIANT_CALLING_DONE",
  "progress": 100,
  "error_message": null,
  "workflow_engine": "Nextflow",
  "pipeline_name": "variant_calling.nf",
  "nextflow_version": "26.04.6",
  "nextflow_run_name": "example_nextflow_run"
}
```

---

## Example result

The synthetic dataset is designed to produce a small test variant result.

An example result may include:

```text
Sample: TUMOR
Chromosome: chrToy
Position: 100
Reference allele: T
Alternative allele: A
Genotype: 1/1
```

This output proves that the platform successfully executed real bioinformatics commands and returned the generated VCF-derived result through the application.

---

## Troubleshooting demonstrated during development

One of the most important development steps involved debugging the final VCF merge process.

The initial merge task failed because the compressed VCF files were staged without their Tabix index files.

After the index files were added, the next version incorrectly passed both the VCF files and `.tbi` index files directly to `bcftools merge`.

The incorrect command looked like:

```bash
bcftools merge TUMOR.vcf.gz TUMOR.vcf.gz.tbi NORMAL.vcf.gz NORMAL.vcf.gz.tbi
```

BCFtools interpreted the `.tbi` files as VCF inputs and failed.

The workflow was corrected so that:

- Both VCF and Tabix index files are staged in the task directory
- Only files ending in `.vcf.gz` are passed to `bcftools merge`
- The matching `.tbi` files remain available beside the VCF files

The corrected command uses only:

```bash
bcftools merge TUMOR.vcf.gz NORMAL.vcf.gz
```

This debugging process demonstrated:

- Reading Nextflow logs
- Inspecting process exit codes
- Reviewing `.command.sh` and `.command.err`
- Understanding Nextflow file staging
- Correcting channel and process input behavior
- Rebuilding Docker images
- Verifying code inside a container

---

## Important limitation

This repository is a functional educational and portfolio MVP.

It is not intended for:

- Clinical diagnosis
- Medical decision-making
- Production oncology analysis
- Regulatory use
- Validated somatic variant calling
- Real patient data

The current example workflow calls variants separately in the tumor and normal samples with BCFtools and then merges the resulting VCF files.

This is useful for demonstrating:

- Full-stack integration
- Workflow submission
- Nextflow orchestration
- Bioinformatics tool execution
- Job tracking
- Logging
- Error handling
- VCF parsing
- REST API design
- Web-based result display

It is not equivalent to a validated matched tumor-normal somatic calling workflow.

---

## Production improvements

A production-level implementation could include:

- GATK Mutect2
- nf-core/sarek
- Duplicate marking
- Base-quality score recalibration
- Read-group validation
- Sample identity checks
- Tumor-normal contamination estimation
- Panel of normals
- Germline population resources
- Orientation-bias filtering
- Somatic variant filtering
- Variant annotation with VEP or SnpEff
- Quality-control reports
- MultiQC
- Workflow unit tests
- Integration tests
- CI/CD
- Version-pinned containers
- Cloud execution
- HPC execution
- Object storage
- PostgreSQL
- Authentication
- Role-based access control
- Audit logging
- Secure file upload
- Encrypted storage
- Reference genome version management
- Workflow provenance
- Formal validation

---

## Why this project matters

This project demonstrates that a genomics workflow can be treated as part of a larger software platform rather than as an isolated command-line script.

The application connects:

- User experience
- Backend API design
- Database tracking
- Background job execution
- Workflow orchestration
- Scientific tools
- Containerization
- Error handling
- Logs
- Reproducible outputs
- Result visualization

The main achievement is the successful integration of a real Nextflow workflow into a complete web application.

---

## Skills demonstrated

- Full-stack application development
- React development
- FastAPI development
- REST API design
- SQLite integration
- Docker
- Docker Compose
- Nextflow DSL2
- Workflow orchestration
- BWA
- SAMtools
- BCFtools
- Tabix
- FASTQ processing
- BAM processing
- VCF processing
- Background job execution
- Workflow monitoring
- Log parsing
- Error handling
- Debugging
- Reproducible scientific software
- Bioinformatics platform design

---

## Future direction

The next version of this platform could support multiple genomics workflows instead of a single demonstration pipeline.

Examples include:

- Germline variant calling
- Somatic variant calling
- Bulk RNA-seq
- Single-cell RNA-seq
- Spatial transcriptomics
- Quality-control pipelines
- Variant annotation
- Multi-omics analysis

The platform could route each submitted dataset to the correct workflow while using the same React, FastAPI, database, Docker, and Nextflow architecture.

---

## Disclaimer

This software is provided for educational, research demonstration, and portfolio purposes only.

It is not validated for clinical, diagnostic, therapeutic, or regulatory use.

Do not use this project to process identifiable patient data or make medical decisions.

---

## Author

**Naghmeh Rezaei**

GitHub: https://github.com/NaghmehRezaei
