$changes = @(
    "fix-dictionary-navigation-state",
    "fix-offline-dong-sp-resolution",
    "data-cleaning-pipeline-upgrade",
    "bulk-upload-and-auto-routing",
    "hs-taxonomy-db-extension",
    "optimize-data-processing-performance",
    "optimize-multithreading-processing",
    "reorder-result-columns",
    "update-ui-new-design",
    "define-dictionary-file-spec",
    "dictionary-generation-integration",
    "dictionary-management-and-integration",
    "fix-ai-inference-uniformity",
    "fix-dictionary-generation-step1",
    "fix-dictionary-generation-step2",
    "frontend-state-persistence",
    "integrate-hscode-from-dictv2",
    "optimize-ai-inference"
)

foreach ($change in $changes) {
    if (Test-Path "openspec\changes\$change") {
        Write-Host "Archiving $change..."
        openspec archive $change --skip-specs --no-validate -y
    }
}
