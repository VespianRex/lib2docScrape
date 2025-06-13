"""
Topic modeling for documentation.
"""

import logging
import os
import pickle
import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from ...processors.content.models import ProcessedContent

logger = logging.getLogger(__name__)


class Topic(BaseModel):
    """Model for a topic."""

    id: str
    name: str
    description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    weight: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopicModel(BaseModel):
    """Model for a topic model."""

    topics: dict[str, Topic] = Field(default_factory=dict)
    vectorizer: Optional[Any] = None
    model: Optional[Any] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TopicModeler:
    """
    Topic modeler for documentation.
    Provides tools for extracting topics from documentation.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the topic modeler.

        Args:
            model_path: Optional path to a saved model
        """
        self.model = TopicModel()
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
        Preprocess text for topic modeling.

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
        self, documents: list[ProcessedContent], num_topics: int = 10
    ) -> None:
        """
        Train a topic model.

        Args:
            documents: List of processed documents
            num_topics: Number of topics to extract
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

        # Create vectorizer
        vectorizer = CountVectorizer(
            max_features=10000, min_df=2, max_df=0.8, ngram_range=(1, 2)
        )

        # Create document-term matrix
        dtm = vectorizer.fit_transform(texts)

        # Create LDA model
        lda = LatentDirichletAllocation(
            n_components=num_topics,
            random_state=42,
            learning_method="online",
            max_iter=10,
        )

        # Fit LDA model
        lda.fit(dtm)

        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = {}

        for topic_idx, topic in enumerate(lda.components_):
            # Get top keywords
            top_indices = topic.argsort()[:-11:-1]
            top_keywords = [feature_names[i] for i in top_indices]

            # Create topic
            topic_obj = Topic(
                id=f"topic_{topic_idx}",
                name=f"Topic {topic_idx}",
                description=f"Automatically generated topic {topic_idx}",
                keywords=top_keywords,
                weight=float(topic.sum() / lda.components_.sum()),
            )

            topics[topic_obj.id] = topic_obj

        # Save model
        self.model = TopicModel(
            topics=topics,
            vectorizer=vectorizer,
            model=lda,
            metadata={"num_documents": len(documents), "num_topics": num_topics},
        )

        logger.info(f"Trained topic model with {num_topics} topics")

    def extract_topics(self, document: ProcessedContent) -> list[tuple[str, float]]:
        """
        Extract topics from a document.

        Args:
            document: Document to extract topics from

        Returns:
            List of (topic_id, weight) tuples
        """
        if not self.model.model:
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

        # Transform text
        vectorizer = self.model.vectorizer
        lda = self.model.model

        dtm = vectorizer.transform([text])

        # Get topic distribution
        topic_distribution = lda.transform(dtm)[0]

        # Create result
        result = []
        for i, weight in enumerate(topic_distribution):
            topic_id = f"topic_{i}"
            result.append((topic_id, float(weight)))

        # Sort by weight
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

        # Save topics
        topics_data = {
            topic_id: topic.model_dump()
            for topic_id, topic in self.model.topics.items()
        }

        # Save metadata
        metadata = self.model.metadata

        # Save model components
        with open(model_path, "wb") as f:
            pickle.dump(
                {
                    "topics": topics_data,
                    "vectorizer": self.model.vectorizer,
                    "model": self.model.model,
                    "metadata": metadata,
                },
                f,
            )

        logger.info(f"Saved topic model to {model_path}")

    def load_model(self, model_path: str) -> None:
        """
        Load a model from a file.

        Args:
            model_path: Path to the model file
        """
        with open(model_path, "rb") as f:
            data = pickle.load(f)

        # Load topics
        topics = {}
        for topic_id, topic_data in data["topics"].items():
            topics[topic_id] = Topic(**topic_data)

        # Create model
        self.model = TopicModel(
            topics=topics,
            vectorizer=data["vectorizer"],
            model=data["model"],
            metadata=data["metadata"],
        )

        logger.info(f"Loaded topic model from {model_path} with {len(topics)} topics")
