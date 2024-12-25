"""Main entrypoint for script to run Gdoc Summaries for TDDs"""

from gdoc_summaries.libs import constants, summary_processor


def entrypoint() -> None:
    """Entrypoint for TDD GDoc Summaries"""
    summary_processor.process_summaries(constants.SummaryType.TDD)

if __name__ == "__main__":
    entrypoint()
