"""
Document categorization using NLP techniques.
"""

import logging
import os
import pickle
import re
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer

from ...processors.content.models import ProcessedContent

logger = logging.getLogger(__name__)


class Category(BaseModel):
    """Model for a document category."""

    id: str
    name: str
    description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CategoryModel(BaseModel):
    """Model for a category model."""

    categories: dict[str, Category] = Field(default_factory=dict)
    vectorizer: Optional[Any] = None
    classifier: Optional[Any] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DocumentCategorizer:
    """
    Document categorizer using NLP techniques.
    Provides tools for categorizing documents using NLP.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the categorizer.

        Args:
            model_path: Optional path to a saved model
        """
        self.model = CategoryModel()
        self.stopwords = self._load_stopwords()

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def _load_stopwords(self) -> set[str]:
        """
        Load stopwords for text processing.

        Returns:
            Set of stopwords
        """
        try:
            from nltk.corpus import stopwords

            return set(stopwords.words("english"))
        except (ImportError, LookupError):
            # Fallback to a basic set of stopwords
            return {
                "a",
                "an",
                "the",
                "and",
                "or",
                "but",
                "if",
                "because",
                "as",
                "what",
                "which",
                "this",
                "that",
                "these",
                "those",
                "then",
                "just",
                "so",
                "than",
                "such",
                "both",
                "through",
                "about",
                "for",
                "is",
                "of",
                "while",
                "during",
                "to",
                "from",
                "in",
                "on",
                "at",
                "by",
                "with",
                "without",
                "not",
                "no",
                "nor",
                "be",
                "am",
                "are",
                "was",
                "were",
                "been",
                "being",
                "have",
                "has",
                "had",
                "having",
                "do",
                "does",
                "did",
                "doing",
                "would",
                "should",
                "could",
                "ought",
                "i",
                "you",
                "he",
                "she",
                "it",
                "we",
                "they",
                "me",
                "him",
                "her",
                "us",
                "them",
                "my",
                "your",
                "his",
                "its",
                "our",
                "their",
                "mine",
                "yours",
                "hers",
                "ours",
                "theirs",
            }

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for NLP.

        Args:
            text: Text to preprocess

        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters and digits
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\d+", " ", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove stopwords
        words = text.split()
        words = [word for word in words if word not in self.stopwords]

        return " ".join(words)

    def train_model(
        self, documents: list[ProcessedContent], num_categories: int = 10
    ) -> None:
        """
        Train a categorization model.

        Args:
            documents: List of processed documents
            num_categories: Number of categories to create
        """
        # Extract text from documents
        texts = []
        for doc in documents:
            title = doc.title or ""
            content = (
                doc.content.get("text", "") if isinstance(doc.content, dict) else ""
            )
            text = f"{title} {content}"
            texts.append(self._preprocess_text(text))

        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=10000, min_df=2, max_df=0.8, ngram_range=(1, 2)
        )

        # Create dimensionality reduction
        svd = TruncatedSVD(n_components=100)
        normalizer = Normalizer(copy=False)

        # Create clustering
        kmeans = KMeans(n_clusters=num_categories, random_state=42)

        # Create pipeline
        pipeline = Pipeline(
            [
                ("tfidf", vectorizer),
                ("svd", svd),
                ("normalizer", normalizer),
                ("kmeans", kmeans),
            ]
        )

        # Fit pipeline
        pipeline.fit(texts)

        # Extract keywords for each category
        feature_names = vectorizer.get_feature_names_out()
        centroids = svd.inverse_transform(kmeans.cluster_centers_)

        # Create categories
        categories = {}
        for i in range(num_categories):
            # Get top keywords
            centroid = centroids[i]
            ordered_indices = np.argsort(centroid)[::-1]
            keywords = [feature_names[idx] for idx in ordered_indices[:10]]

            # Create category
            category = Category(
                id=f"category_{i}",
                name=f"Category {i}",
                description=f"Automatically generated category {i}",
                keywords=keywords,
            )

            categories[category.id] = category

        # Save model
        self.model = CategoryModel(
            categories=categories,
            vectorizer=vectorizer,
            classifier=pipeline,
            metadata={
                "num_documents": len(documents),
                "num_categories": num_categories,
            },
        )

        logger.info(f"Trained categorization model with {num_categories} categories")

    def categorize_document(
        self, document: ProcessedContent
    ) -> list[tuple[str, float]]:
        """
        Categorize a document.

        Args:
            document: Document to categorize

        Returns:
            List of (category_id, confidence) tuples
        """
        if not self.model.classifier:
            raise ValueError("Model not trained")

        # Extract text from document
        title = document.title or ""
        content = (
            document.content.get("text", "")
            if isinstance(document.content, dict)
            else ""
        )
        text = f"{title} {content}"
        text = self._preprocess_text(text)

        # Predict category
        pipeline = self.model.classifier
        vectorizer = self.model.vectorizer

        # Transform text
        X = vectorizer.transform([text])

        # Get cluster distances
        kmeans = pipeline.named_steps["kmeans"]
        svd = pipeline.named_steps["svd"]
        normalizer = pipeline.named_steps["normalizer"]

        X_svd = svd.transform(X)
        X_normalized = normalizer.transform(X_svd)

        # Get distances to centroids
        distances = kmeans.transform(X_normalized)[0]

        # Convert distances to confidences
        confidences = 1 / (1 + distances)
        confidences = confidences / confidences.sum()

        # Create result
        result = []
        for i, confidence in enumerate(confidences):
            category_id = f"category_{i}"
            result.append((category_id, float(confidence)))

        # Sort by confidence
        result.sort(key=lambda x: x[1], reverse=True)

        return result

    def save_model(self, model_path: str) -> None:
        """
        Save the model to a file.

        Args:
            model_path: Path to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)

        # Save categories
        categories_data = {
            cat_id: cat.model_dump() for cat_id, cat in self.model.categories.items()
        }

        # Save metadata
        metadata = self.model.metadata

        # Save model components
        with open(model_path, "wb") as f:
            pickle.dump(
                {
                    "categories": categories_data,
                    "vectorizer": self.model.vectorizer,
                    "classifier": self.model.classifier,
                    "metadata": metadata,
                },
                f,
            )

        logger.info(f"Saved categorization model to {model_path}")

    def load_model(self, model_path: str) -> None:
        """
        Load a model from a file.

        Args:
            model_path: Path to the model file
        """
        with open(model_path, "rb") as f:
            data = pickle.load(f)

        # Load categories
        categories = {}
        for cat_id, cat_data in data["categories"].items():
            categories[cat_id] = Category(**cat_data)

        # Create model
        self.model = CategoryModel(
            categories=categories,
            vectorizer=data["vectorizer"],
            classifier=data["classifier"],
            metadata=data["metadata"],
        )

        logger.info(
            f"Loaded categorization model from {model_path} with {len(categories)} categories"
        )
