# Property-Based Tests for lib2docScrape

This directory contains property-based tests for the lib2docScrape library using the Hypothesis framework.

## Installation

To run these tests, you need to install the Hypothesis package:

```bash
pip install hypothesis
```

Or install from the requirements file:

```bash
pip install -r tests/property/requirements.txt
```

## Running the Tests

To run all property-based tests:

```bash
python -m pytest tests/property/
```

To run a specific test file:

```bash
python -m pytest tests/property/test_url_properties.py
```

## Test Files

- `test_url_properties.py`: Tests for URL handling and validation
- `test_content_processing.py`: Tests for content processing
- `test_backend_selection.py`: Tests for backend selection

## What is Property-Based Testing?

Property-based testing is a testing methodology where instead of writing specific test cases, you define properties that should hold true for all valid inputs. The testing framework (Hypothesis in this case) then generates random inputs and checks if the properties hold.

This approach can find edge cases that you might not have thought of when writing traditional unit tests.

## Adding New Property-Based Tests

To add a new property-based test:

1. Create a new test file in this directory
2. Import the Hypothesis framework: `from hypothesis import given, strategies as st`
3. Define strategies for generating test inputs
4. Write test functions decorated with `@given` to specify which strategies to use
5. Assert properties that should hold true for all inputs

For more information on Hypothesis, see the [official documentation](https://hypothesis.readthedocs.io/).
