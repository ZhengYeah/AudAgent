import pytest
from presidio_analyzer import AnalyzerEngine


@pytest.fixture
def message_with_pii():
    return "Contact John Doe at +1 555-123-4567 or john.doe@example.com."

def test_presidio_pii_detection(message_with_pii):
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=message_with_pii, language='en')

    for result in results:
        print(f"Entity: {result.entity_type}, Start: {result.start}, End: {result.end}, Score: {result.score}")
