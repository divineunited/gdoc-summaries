"""
Fixtures for testing
"""
import pytest


@pytest.fixture
def sample_document():
    """Sample Google Doc response structure"""
    return {
        "title": "Test Document",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is a test document content.\n"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

@pytest.fixture
def biweekly_document():
    """Sample biweekly document with sections"""
    return {
        "title": "Biweekly Updates",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "--- UPDATE 2024-03-15 ---\nLatest update content\n"
                                }
                            },
                            {
                                "textRun": {
                                    "content": "--- UPDATE 2024-03-01 ---\nOlder update content\n"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

@pytest.fixture(autouse=True)
def no_network_calls():
    """Prevent any network calls during testing"""
    import socket
    old_socket = socket.socket

    def guard(*args, **kwargs):
        raise RuntimeError(
            "Network calls are not allowed during testing! "
            "Make sure all external calls are properly mocked."
        )

    socket.socket = guard
    yield
    socket.socket = old_socket
