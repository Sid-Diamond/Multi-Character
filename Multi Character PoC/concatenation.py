"""Optional future pooling of separately saved experiments.

This is deliberately outside the run pipeline. Before implementation, define
compatibility checks for prompts, models, judges, labels, and trial provenance.
"""


def combine_runs(run_folders, output_folder):
    """Combine compatible saved runs while retaining their source run identities."""
    raise NotImplementedError("Run concatenation criteria have not been defined")
