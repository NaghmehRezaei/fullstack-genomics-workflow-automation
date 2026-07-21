# Genomics Variant Calling Platform MVP v3

This version runs a genuine small-scale variant-calling workflow in Nextflow DSL2.

Tools actually executed:
- BWA index and BWA-MEM alignment
- SAMtools sort, index, faidx, and quickcheck
- BCFtools mpileup, call, merge, norm, filter, view, and stats

The included synthetic tumor FASTQ has one known SNV at chrToy:100 T>A. The normal FASTQ keeps the reference allele.

Run:
```bash
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up --force-recreate
```

Open:
- React: http://localhost:3000
- Swagger: http://localhost:8000/docs

Swagger exposes:
- GET /analyses/{id}/workflow — engine, Nextflow version, run name, exact command, process trace, exit codes, durations
- GET /analyses/{id}/workflow/code — exact Nextflow DSL2 source
- GET /analyses/{id}/workflow/log — real Nextflow console log
- GET /analyses/{id}/vcf — produced VCF
- GET /analyses/{id}/results — parsed variants

This is a technically real teaching workflow using tiny synthetic data. It is not a validated clinical pipeline and must not be used for patient care.

## v3.0.1 corrections

- Stages each `.vcf.gz` together with its `.tbi` index for the merge task.
- Passes only `.vcf.gz` files to `bcftools merge`.
- Reads Nextflow 26 trace process names from the `name` column, eliminating `UNKNOWN` labels.
