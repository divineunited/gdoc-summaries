"""Main entrypoint for script to run Gdoc Summaries for PRDs"""

from gdoc_summaries.libs import constants, summary_processor


def entrypoint() -> None:
    """Entrypoint for PRD GDoc Summaries"""
    summary_processor.process_summaries(constants.SummaryType.PRD)

if __name__ == "__main__":
    entrypoint()
