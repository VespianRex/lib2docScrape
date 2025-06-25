#!/usr/bin/env python3
"""
Integrated LLM System Tests
SmolAgents + LiteLLM + llama.cpp for documentation validation and enhancement.
"""

from unittest.mock import patch

import pytest

from src.processors.integrated_llm_system import (
    ContentEnhancer,
    DocumentationValidator,
    LiteLLMManager,
    LocalModelManager,
    SmolAgentsDocumentationProcessor,
)


class TestLiteLLMManager:
    """Test LiteLLM integration for multiple LLM providers."""

    def test_litellm_manager_initialization(self):
        """Test LiteLLM manager initialization."""
        # RED: This should fail because class doesn't exist yet
        manager = LiteLLMManager()
        assert manager is not None
        assert hasattr(manager, "supported_models")
        assert hasattr(manager, "default_model")

    def test_model_configuration(self):
        """Test model configuration for different providers."""
        # RED: Test model configuration
        manager = LiteLLMManager()

        # Configure local llama.cpp model
        local_config = manager.configure_local_model(
            model_path="models/phi-3-mini-4k-instruct-q4_0.gguf",
            max_tokens=512,
            temperature=0.1,
        )

        assert local_config["provider"] == "llamacpp"
        assert local_config["model_path"].endswith(".gguf")
        assert local_config["max_tokens"] == 512

        # Configure OpenAI model
        openai_config = manager.configure_openai_model(
            model="gpt-3.5-turbo", api_key="test-key"
        )

        assert openai_config["provider"] == "openai"
        assert openai_config["model"] == "gpt-3.5-turbo"

    def test_model_selection_strategy(self):
        """Test intelligent model selection based on task."""
        # RED: Test model selection logic
        manager = LiteLLMManager()

        # Simple validation tasks should use local model
        validation_task = {
            "type": "content_validation",
            "content_length": 500,
            "complexity": "low",
        }
        selected_model = manager.select_model_for_task(validation_task)
        assert selected_model["provider"] == "llamacpp"

        # Complex enhancement tasks might use larger model
        enhancement_task = {
            "type": "content_enhancement",
            "content_length": 5000,
            "complexity": "high",
        }
        selected_model = manager.select_model_for_task(enhancement_task)
        # Should prefer local for privacy, but allow fallback
        assert selected_model["provider"] in ["llamacpp", "openai"]

    def test_unified_api_interface(self):
        """Test unified API interface across different providers."""
        # RED: Test unified interface
        manager = LiteLLMManager()

        # All models should respond to same interface
        prompt = "Is this documentation relevant? Content: API reference guide"

        # Test local model call
        with patch("litellm.completion") as mock_completion:
            mock_completion.return_value.choices[0].message.content = "Yes, relevant"

            response = manager.generate_response(
                prompt=prompt,
                model_config={"provider": "llamacpp", "model": "local"},
                max_tokens=50,
            )

            assert "relevant" in response.lower()
            mock_completion.assert_called_once()


class TestLocalModelManager:
    """Test local model management with llama.cpp."""

    def test_local_model_initialization(self):
        """Test local model initialization."""
        # RED: Test local model setup
        manager = LocalModelManager()

        # Should support small models for bundling
        small_models = manager.get_supported_small_models()
        assert len(small_models) > 0

        # Should have models under 4B parameters
        for model in small_models:
            assert model["parameters"] < 4_000_000_000
            assert model["size_mb"] < 3000  # Reasonable for bundling

    def test_model_performance_testing(self):
        """Test model performance evaluation."""
        # RED: Test performance testing framework
        manager = LocalModelManager()

        test_prompts = [
            "Is this API documentation? Content: FastAPI is a web framework",
            "Should we keep this? Content: License: MIT",
            "Relevance score for: Installation guide with examples",
        ]

        # Test model performance
        performance_results = manager.test_model_performance(
            model_path="models/test-model.gguf",
            test_prompts=test_prompts,
            expected_responses=["yes", "no", "high"],
        )

        assert "accuracy" in performance_results
        assert "avg_response_time" in performance_results
        assert "memory_usage" in performance_results
        assert performance_results["accuracy"] >= 0.0

    def test_model_bundling_criteria(self):
        """Test criteria for bundling models with the application."""
        # RED: Test bundling decision logic
        manager = LocalModelManager()

        # Test model that should be bundled
        small_model = {
            "name": "phi-3-mini-4k-instruct-q4_0",
            "size_mb": 2300,
            "parameters": 3_800_000_000,
            "accuracy_score": 0.85,
            "response_time_ms": 150,
        }

        should_bundle = manager.should_bundle_model(small_model)
        assert should_bundle == True

        # Test model that's too large
        large_model = {
            "name": "llama-2-7b-q4_0",
            "size_mb": 4200,
            "parameters": 7_000_000_000,
            "accuracy_score": 0.92,
            "response_time_ms": 300,
        }

        should_bundle = manager.should_bundle_model(large_model)
        assert should_bundle == False


class TestSmolAgentsDocumentationProcessor:
    """Test SmolAgents integration for documentation processing."""

    def test_smolagents_workflow_creation(self):
        """Test SmolAgents workflow creation."""
        # RED: Test workflow setup
        processor = SmolAgentsDocumentationProcessor()

        assert processor is not None
        assert hasattr(processor, "agent")
        assert hasattr(processor, "tools")

        # Should have essential tools
        tool_names = [tool.__name__ for tool in processor.tools]
        assert "validate_content_relevance" in tool_names
        assert "enhance_documentation" in tool_names
        assert "generate_summary" in tool_names

    def test_content_validation_tool(self):
        """Test content validation tool."""
        # RED: Test validation tool
        processor = SmolAgentsDocumentationProcessor()

        # Test relevant content
        relevant_content = (
            "# API Reference\n\nComplete guide to using the FastAPI framework"
        )
        validation_result = processor.validate_content_relevance(
            content=relevant_content,
            repository_context={"type": "api_documentation", "priority": "high"},
        )

        assert validation_result["is_relevant"] == True
        assert validation_result["confidence"] > 0.7
        assert "reasoning" in validation_result

        # Test irrelevant content
        irrelevant_content = "# License\n\nMIT License"
        validation_result = processor.validate_content_relevance(
            content=irrelevant_content,
            repository_context={"type": "legal", "priority": "minimal"},
        )

        assert validation_result["is_relevant"] == False
        assert "reasoning" in validation_result

    def test_documentation_enhancement_tool(self):
        """Test documentation enhancement tool."""
        # RED: Test enhancement tool
        processor = SmolAgentsDocumentationProcessor()

        basic_content = "FastAPI is fast"
        enhanced_content = processor.enhance_documentation(
            content=basic_content,
            enhancement_type="expand",
            target_audience="developers",
        )

        assert len(enhanced_content) > len(basic_content)
        assert "FastAPI" in enhanced_content
        assert enhanced_content != basic_content

    def test_batch_processing_workflow(self):
        """Test batch processing of multiple content items."""
        # RED: Test batch processing
        processor = SmolAgentsDocumentationProcessor()

        content_batch = [
            {
                "url": "https://example.com/api",
                "content": "API documentation for developers",
                "repository_context": {"type": "api_documentation"},
            },
            {
                "url": "https://example.com/license",
                "content": "MIT License text",
                "repository_context": {"type": "legal"},
            },
            {
                "url": "https://example.com/tutorial",
                "content": "Getting started tutorial",
                "repository_context": {"type": "tutorial"},
            },
        ]

        results = processor.process_content_batch(content_batch)

        assert len(results) == 3
        assert all("validation_result" in result for result in results)
        assert all("enhancement_suggestion" in result for result in results)


class TestDocumentationValidator:
    """Test documentation validation with integrated LLM system."""

    def test_validator_initialization(self):
        """Test validator initialization with LLM backend."""
        # RED: Test validator setup
        validator = DocumentationValidator(
            llm_manager=LiteLLMManager(), model_preference="local"
        )

        assert validator is not None
        assert validator.model_preference == "local"

    def test_content_validation_with_context(self):
        """Test content validation with repository context."""
        # RED: Test validation with context
        validator = DocumentationValidator()

        content_item = {
            "content": "Complete API reference with examples",
            "url": "https://github.com/user/repo/docs/api.md",
            "repository_context": {
                "documentation_system": "mkdocs",
                "quality_score": 0.8,
                "source_priority": "high",
            },
        }

        validation_result = validator.validate_with_context(content_item)

        assert "is_relevant" in validation_result
        assert "confidence" in validation_result
        assert "context_boost" in validation_result
        assert "llm_reasoning" in validation_result

    def test_validation_performance_optimization(self):
        """Test validation performance optimization."""
        # RED: Test performance optimization
        validator = DocumentationValidator()

        # Small content should use local model
        small_content = "API docs"
        model_choice = validator.choose_optimal_model(
            content=small_content, task_complexity="low"
        )
        assert model_choice["provider"] == "llamacpp"

        # Large content might use more powerful model if needed
        large_content = "A" * 5000  # Large content
        model_choice = validator.choose_optimal_model(
            content=large_content, task_complexity="high"
        )
        # Should still prefer local for privacy
        assert model_choice["provider"] in ["llamacpp", "openai"]


class TestContentEnhancer:
    """Test content enhancement capabilities."""

    def test_content_enhancement_strategies(self):
        """Test different content enhancement strategies."""
        # RED: Test enhancement strategies
        enhancer = ContentEnhancer()

        # Test expansion strategy
        basic_content = "FastAPI is a web framework"
        expanded = enhancer.enhance_content(
            content=basic_content, strategy="expand", target_length=200
        )
        assert len(expanded) > len(basic_content)

        # Test summarization strategy
        long_content = "A" * 1000 + " FastAPI documentation " + "B" * 1000
        summarized = enhancer.enhance_content(
            content=long_content, strategy="summarize", target_length=100
        )
        assert len(summarized) < len(long_content)
        assert "FastAPI" in summarized

    def test_documentation_generation(self):
        """Test automatic documentation generation."""
        # RED: Test doc generation
        enhancer = ContentEnhancer()

        code_snippet = """
        def create_user(name: str, email: str) -> User:
            '''Create a new user with name and email.'''
            return User(name=name, email=email)
        """

        generated_docs = enhancer.generate_documentation(
            code=code_snippet, doc_type="api_reference"
        )

        assert "create_user" in generated_docs
        assert "name" in generated_docs
        assert "email" in generated_docs
        assert len(generated_docs) > len(code_snippet)


class TestIntegratedWorkflow:
    """Test complete integrated workflow."""

    def test_end_to_end_processing(self):
        """Test complete end-to-end processing workflow."""
        # RED: Test complete workflow
        from src.processors.enhanced_github_analyzer import EnhancedGitHubAnalyzer

        # Step 1: Analyze repository structure
        github_analyzer = EnhancedGitHubAnalyzer()
        repo_structure = github_analyzer.analyze_repository_structure(
            repo_url="https://github.com/test/repo",
            file_tree=["README.md", "docs/api.md", "examples/demo.py"],
        )

        # Step 2: Process with SmolAgents + LiteLLM
        processor = SmolAgentsDocumentationProcessor()

        content_items = [
            {
                "content": "API documentation content",
                "url": "docs/api.md",
                "repository_context": repo_structure.to_dict(),
            }
        ]

        results = processor.process_content_batch(content_items)

        assert len(results) == 1
        assert "validation_result" in results[0]
        assert "enhancement_suggestion" in results[0]

        # Step 3: Validate results
        validator = DocumentationValidator()
        final_validation = validator.validate_batch_results(results)

        assert "overall_quality" in final_validation
        assert "recommendations" in final_validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
