# NLP Processing for lib2docScrape

This directory contains NLP (Natural Language Processing) tools for processing documentation content.

## Features

- **Document Categorization**: Automatically categorize documentation pages using NLP techniques
- **Topic Modeling**: Extract topics from documentation content
- **Keyword Extraction**: Extract important keywords from documentation

## Usage

### Document Categorization

```python
from src.processors.nlp.categorizer import DocumentCategorizer

# Create categorizer
categorizer = DocumentCategorizer()

# Train model with documents
categorizer.train_model(documents, num_categories=10)

# Categorize a document
categories = categorizer.categorize_document(document)

# Save model
categorizer.save_model("categories.pkl")

# Load model
categorizer = DocumentCategorizer(model_path="categories.pkl")
```

### Topic Modeling

```python
from src.processors.nlp.topic_modeling import TopicModeler

# Create topic modeler
topic_modeler = TopicModeler()

# Train model with documents
topic_modeler.train_model(documents, num_topics=10)

# Extract topics from a document
topics = topic_modeler.extract_topics(document)

# Save model
topic_modeler.save_model("topics.pkl")

# Load model
topic_modeler = TopicModeler(model_path="topics.pkl")
```

## Command Line Interface

The NLP tools can be used from the command line:

```bash
# Categorize library documentation
python -m src.main library categorize -n library_name -c 10

# Extract topics from library documentation
python -m src.main library topics -n library_name -t 10
```

## Dependencies

- scikit-learn: Machine learning library for NLP
- nltk: Natural Language Toolkit for text processing

## Implementation Details

### Document Categorization

The document categorization uses the following techniques:

1. Text preprocessing (lowercase, remove special characters, remove stopwords)
2. TF-IDF vectorization to convert text to numerical features
3. Dimensionality reduction with SVD (Singular Value Decomposition)
4. K-means clustering to group similar documents
5. Keyword extraction from cluster centroids to label categories

### Topic Modeling

The topic modeling uses the following techniques:

1. Text preprocessing (lowercase, remove special characters, remove stopwords)
2. Count vectorization to create document-term matrix
3. Latent Dirichlet Allocation (LDA) to extract topics
4. Keyword extraction from topic distributions to label topics
