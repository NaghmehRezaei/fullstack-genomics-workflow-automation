nextflow.enable.dsl = 2

params.analysis_id   = null
params.tumor         = null
params.normal        = null
params.reference     = null
params.tumor_sample  = 'TUMOR'
params.normal_sample = 'NORMAL'
params.outdir        = '/app/results'

process INDEX_REFERENCE {
    tag 'reference'
    publishDir params.outdir, mode: 'copy', pattern: 'reference.*'

    input:
    path reference

    output:
    tuple path('reference.fa'), path('reference.fa.amb'), path('reference.fa.ann'),
          path('reference.fa.bwt'), path('reference.fa.pac'), path('reference.fa.sa'),
          path('reference.fa.fai')

    script:
    """
    cp ${reference} reference.fa
    bwa index reference.fa
    samtools faidx reference.fa
    """
}

process ALIGN_SAMPLE {
    tag "${sample_id}"
    publishDir params.outdir, mode: 'copy', pattern: '*.bam*'

    input:
    tuple val(sample_id), path(reads)
    tuple path(reference), path(amb), path(ann), path(bwt), path(pac), path(sa), path(fai)

    output:
    tuple val(sample_id), path("${sample_id}.bam"), path("${sample_id}.bam.bai")

    script:
    """
    bwa mem -R '@RG\\tID:${sample_id}\\tSM:${sample_id}\\tPL:ILLUMINA' ${reference} ${reads} \
      | samtools sort -o ${sample_id}.bam -
    samtools index ${sample_id}.bam
    samtools quickcheck -v ${sample_id}.bam
    """
}

process CALL_SAMPLE_VARIANTS {
    tag "${sample_id}"
    publishDir params.outdir, mode: 'copy', pattern: '*.vcf.gz*'

    input:
    tuple val(sample_id), path(bam), path(bai)
    path reference

    output:
    tuple val(sample_id), path("${sample_id}.vcf.gz"), path("${sample_id}.vcf.gz.tbi")

    script:
    """
    bcftools mpileup -f ${reference} -Ou -a FORMAT/DP,FORMAT/AD ${bam} \
      | bcftools call -mv -Oz -o ${sample_id}.vcf.gz
    tabix -p vcf ${sample_id}.vcf.gz
    """
}

process MERGE_AND_FILTER {
    tag 'tumor-normal'
    publishDir params.outdir, mode: 'copy'

    input:
    path variant_files
    path reference

    output:
    path 'combined.vcf.gz'
    path 'combined.vcf.gz.tbi'
    path 'combined.vcf'
    path 'bcftools_stats.txt'

    script:
    // Stage both VCF and TBI files, but pass only VCFs to bcftools merge.
    def vcf_list = variant_files
        .findAll { file -> file.name.endsWith('.vcf.gz') }
        .sort { file -> file.name }
        .join(' ')

    """
    bcftools merge \
        -m none \
        -Oz \
        -o merged.raw.vcf.gz \
        ${vcf_list}

    tabix -p vcf merged.raw.vcf.gz

    bcftools norm \
        -f ${reference} \
        -m -any \
        -Oz \
        -o normalized.vcf.gz \
        merged.raw.vcf.gz

    tabix -p vcf normalized.vcf.gz

    bcftools filter \
        -i 'QUAL>=20' \
        -Oz \
        -o combined.vcf.gz \
        normalized.vcf.gz

    tabix -p vcf combined.vcf.gz
    bcftools view combined.vcf.gz > combined.vcf
    bcftools stats combined.vcf.gz > bcftools_stats.txt
    """
}

workflow {
    if (!params.analysis_id) error 'Missing --analysis_id'
    if (!params.tumor) error 'Missing --tumor'
    if (!params.normal) error 'Missing --normal'
    if (!params.reference) error 'Missing --reference'

    tumor_reads = file(params.tumor, checkIfExists: true)
    normal_reads = file(params.normal, checkIfExists: true)
    reference = file(params.reference, checkIfExists: true)

    sample_ch = Channel.of(
        tuple(params.tumor_sample, tumor_reads),
        tuple(params.normal_sample, normal_reads)
    )

    indexed = INDEX_REFERENCE(reference)
    aligned = ALIGN_SAMPLE(sample_ch, indexed)

    reference_for_call = indexed.map { ref, amb, ann, bwt, pac, sa, fai -> ref }
    called = CALL_SAMPLE_VARIANTS(aligned, reference_for_call)

    // Flatten each sample's VCF/TBI pair into one staged collection.
    variant_files = called
        .map { sample_id, vcf, tbi -> [vcf, tbi] }
        .flatten()
        .collect()

    reference_for_merge = indexed.map { ref, amb, ann, bwt, pac, sa, fai -> ref }
    MERGE_AND_FILTER(variant_files, reference_for_merge)
}
