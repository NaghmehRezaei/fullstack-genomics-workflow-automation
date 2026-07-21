nextflow.enable.dsl=2

params.analysis_id = null
params.tumor = null
params.normal = null
params.genome = 'GRCh38'
params.outdir = '/app/results'

process VALIDATE_INPUTS {

    tag "analysis-${params.analysis_id}"

    publishDir params.outdir, mode: 'copy'

    input:
    path tumor
    path normal

    output:
    path "validation.txt"

    script:
    """
    echo "Analysis ID: ${params.analysis_id}" > validation.txt
    echo "Tumor file: ${tumor}" >> validation.txt
    echo "Normal file: ${normal}" >> validation.txt
    echo "Reference genome: ${params.genome}" >> validation.txt

    test -s ${tumor}
    test -s ${normal}

    echo "Input validation completed" >> validation.txt
    """
}

process CALL_MOCK_VARIANTS {

    tag "analysis-${params.analysis_id}"

    publishDir params.outdir, mode: 'copy'

    input:
    path validation_file

    output:
    path "variants.json"

    script:
    """
    cat > variants.json <<'EOF'
    [
      {
        "gene": "TP53",
        "variant": "p.R273H",
        "classification": "Pathogenic",
        "variant_type": "SNV"
      },
      {
        "gene": "EGFR",
        "variant": "p.L858R",
        "classification": "Pathogenic",
        "variant_type": "SNV"
      }
    ]
    EOF
    """
}

workflow {
    if (!params.analysis_id) {
        error "Missing --analysis_id"
    }

    if (!params.tumor) {
        error "Missing --tumor"
    }

    if (!params.normal) {
        error "Missing --normal"
    }

    tumor_ch = Channel.fromPath(params.tumor, checkIfExists: true)
    normal_ch = Channel.fromPath(params.normal, checkIfExists: true)

    validation = VALIDATE_INPUTS(tumor_ch, normal_ch)
    CALL_MOCK_VARIANTS(validation)
}
