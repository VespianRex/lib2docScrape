"""
Web-based documentation viewer for lib2docScrape.

This module provides a web-based UI for visualizing documentation and version differences.
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.organizers.doc_organizer import DocumentOrganizer
from src.organizers.library_version_tracker import LibraryVersionTracker
from src.processors.content.format_handler import (
    FormatHandler,
)

# Ensure FormatHandler is imported
from src.utils.error_handler import ErrorLevel, handle_error

logger = logging.getLogger(__name__)


class DocViewerConfig(BaseModel):
    """Configuration for the DocViewer."""

    # Configuration fields
    docs_dir: str = "docs"
    templates_dir: str = "templates"
    static_dir: str = "static"


# Models for API
class VersionInfo(BaseModel):
    """Version information."""

    version: str
    release_date: Optional[datetime] = None
    doc_url: str
    crawl_date: datetime
    changes: Optional[dict[str, Any]] = None


class DocumentInfo(BaseModel):
    """Document information."""

    title: str
    url: str
    content_type: str
    content_format: str
    last_updated: datetime
    versions: list[str]
    topics: list[str]
    summary: Optional[str] = None


class DiffRequest(BaseModel):
    """Request for diff between versions."""

    library: str
    doc_path: str
    version1: str
    version2: str
    format: str = "html"


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    library: Optional[str] = None
    version: Optional[str] = None
    topics: Optional[list[str]] = None
    content_type: Optional[str] = None


class DocViewer:
    """Main application for the documentation viewer."""

    def __init__(
        self,
        doc_organizer: Optional[DocumentOrganizer] = None,  # Corrected type hint
        library_tracker: Optional[LibraryVersionTracker] = None,
        config: Optional[DocViewerConfig] = None,
        format_handler: Optional[
            FormatHandler
        ] = None,  # Added format_handler parameter
        templates_dir: Optional[str] = None,
        static_dir: Optional[str] = None,
    ) -> None:
        """Initialize the DocViewer."""
        self.config = config or DocViewerConfig()
        self.doc_organizer = (
            doc_organizer or DocumentOrganizer()
        )  # Corrected instantiation
        self.library_tracker = library_tracker or LibraryVersionTracker()
        self.format_handler = (
            format_handler or FormatHandler()
        )  # Initialize format_handler

        # Create FastAPI app
        self.app = FastAPI(
            title="lib2docScrape Documentation Viewer (Complete)",
            description="Web-based UI for visualizing documentation and version differences",
            version="0.1.0",
        )

        # Set up templates and static files
        # Use provided dirs or fall back to defaults relative to this file
        current_module_dir = os.path.dirname(__file__)
        self.templates_dir = templates_dir or os.path.join(
            current_module_dir, "templates"
        )
        self.static_dir = static_dir or os.path.join(current_module_dir, "static")

        # Ensure these directories exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)
            logger.info(f"Created templates directory: {self.templates_dir}")
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir, exist_ok=True)
            logger.info(f"Created static directory: {self.static_dir}")

        self.templates = Jinja2Templates(directory=self.templates_dir)
        self.app.mount("/static", StaticFiles(directory=self.static_dir), name="static")

        # Register routes
        self._register_routes()

        logger.info("Documentation viewer (complete) application initialized")

    async def _search(
        self,
        query: str,
        library: Optional[str] = None,
        version: Optional[str] = None,
        topics: Optional[list[str]] = None,
        content_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Perform a search using the document organizer.
        """
        logger.debug(
            f"DocViewer._search called with query: '{query}', library: {library}, version: {version}"
        )

        try:
            # Use the document organizer's search method
            search_results = self.doc_organizer.search(query)

            # Convert results to the expected format
            formatted_results = []
            for doc_id, score, matches in search_results:
                if doc_id in self.doc_organizer.documents:
                    doc_metadata = self.doc_organizer.documents[doc_id]
                    formatted_results.append(
                        {
                            "doc_id": doc_id,
                            "title": doc_metadata.title,
                            "url": doc_metadata.url,
                            "category": doc_metadata.category,
                            "score": score,
                            "matches": matches,
                            "tags": doc_metadata.tags,
                            "last_updated": doc_metadata.last_updated.isoformat()
                            if doc_metadata.last_updated
                            else None,
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []

    async def _get_diff(
        self,
        library: str,
        doc_path: str,
        version1: str,
        version2: str,
        format: str = "html",
    ) -> Optional[dict[str, str]]:
        """
        Get diff between two document versions using the document organizer.
        """
        logger.debug(
            f"DocViewer._get_diff called for {library}/{doc_path} between {version1} and {version2}"
        )

        try:
            # Find document by URL/path
            doc_id = None
            for did, metadata in self.doc_organizer.documents.items():
                if doc_path in metadata.url or library in metadata.url:
                    doc_id = did
                    break

            if not doc_id:
                logger.warning(f"Document not found for {library}/{doc_path}")
                return None

            # Get document versions
            versions = self.doc_organizer.get_document_versions(doc_id)

            # Find the requested versions
            v1_data = None
            v2_data = None

            for version in versions:
                if version.version_id == version1:
                    v1_data = version.changes
                elif version.version_id == version2:
                    v2_data = version.changes

            if not v1_data or not v2_data:
                logger.warning(f"Versions {version1} or {version2} not found")
                return None

            # Simple diff implementation
            v1_content = str(v1_data.get("content", {}).get("formatted_content", ""))
            v2_content = str(v2_data.get("content", {}).get("formatted_content", ""))

            return {
                "version1": version1,
                "version2": version2,
                "content1": v1_content,
                "content2": v2_content,
                "diff_html": f"<div>Diff between {version1} and {version2}</div>",
            }

        except Exception as e:
            logger.error(f"Error generating diff: {e}")
            return None

    def _register_routes(self) -> None:
        """Register application routes."""

        # Home page
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "home.html", {"request": request, "libraries": libraries}
            )

        # Library page
        @self.app.get("/library/{library}", response_class=HTMLResponse)
        async def library(request: Request, library: str):
            versions = await self._get_library_versions(library)
            if not versions:
                raise HTTPException(
                    status_code=404, detail=f"Library {library} not found"
                )

            return self.templates.TemplateResponse(
                "library.html",
                {"request": request, "library": library, "versions": versions},
            )

        # Version page
        @self.app.get(
            "/library/{library}/version/{version}", response_class=HTMLResponse
        )
        async def version(request: Request, library: str, version: str):
            docs = await self._get_version_docs(library, version)
            if not docs:
                raise HTTPException(
                    status_code=404,
                    detail=f"Version {version} of library {library} not found",
                )

            return self.templates.TemplateResponse(
                "version.html",
                {
                    "request": request,
                    "library": library,
                    "version": version,
                    "docs": docs,
                },
            )

        # Document page
        @self.app.get(
            "/library/{library}/version/{version}/doc/{doc_path:path}",
            response_class=HTMLResponse,
        )
        async def document(request: Request, library: str, version: str, doc_path: str):
            doc = await self._get_document(library, version, doc_path)
            if not doc:
                raise HTTPException(
                    status_code=404, detail=f"Document {doc_path} not found"
                )

            return self.templates.TemplateResponse(
                "document.html",
                {
                    "request": request,
                    "library": library,
                    "version": version,
                    "doc": doc,
                },
            )

        # Diff page
        @self.app.get("/diff", response_class=HTMLResponse)
        async def diff_page(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "diff.html", {"request": request, "libraries": libraries}
            )

        # Diff API
        @self.app.post("/api/diff", response_class=JSONResponse)
        async def diff(request: DiffRequest):
            diff_result = await self._get_diff(
                request.library,
                request.doc_path,
                request.version1,
                request.version2,
                request.format,
            )
            if not diff_result:
                raise HTTPException(status_code=404, detail="Could not generate diff")

            return diff_result

        # Search page
        @self.app.get("/search", response_class=HTMLResponse)
        async def search_page(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "search.html", {"request": request, "libraries": libraries}
            )

        # Search API
        @self.app.post("/api/search", response_class=JSONResponse)
        async def search(request: SearchRequest):
            results = await self._search(
                request.query,
                request.library,
                request.version,
                request.topics,
                request.content_type,
            )
            return {"results": results}

        # API endpoints
        @self.app.get("/api/libraries", response_class=JSONResponse)
        async def api_libraries():
            libraries = await self._get_libraries()
            return {"libraries": libraries}

        @self.app.get("/api/library/{library}/versions", response_class=JSONResponse)
        async def api_versions(library: str):
            versions = await self._get_library_versions(library)
            if not versions:
                raise HTTPException(
                    status_code=404, detail=f"Library {library} not found"
                )

            return {"library": library, "versions": versions}

        @self.app.get(
            "/api/library/{library}/version/{version}/docs", response_class=JSONResponse
        )
        async def api_docs(library: str, version: str):
            docs = await self._get_version_docs(library, version)
            if not docs:
                raise HTTPException(
                    status_code=404,
                    detail=f"Version {version} of library {library} not found",
                )

            return {"library": library, "version": version, "docs": docs}

    async def _get_libraries(self) -> list[str]:
        """
        Get list of available libraries.

        Returns:
            List of library names
        """
        try:
            # Extract unique library names from document URLs
            libraries = set()
            for metadata in self.doc_organizer.documents.values():
                # Extract library name from URL (simple heuristic)
                url_parts = metadata.url.split("/")
                for part in url_parts:
                    if part and not part.startswith(("http", "https", "www")):
                        libraries.add(part)
                        break
            return list(libraries)
        except Exception as e:
            handle_error(e, "DocViewerApp", "_get_libraries", level=ErrorLevel.ERROR)
            return []

    async def _get_library_versions(self, library: str) -> list[VersionInfo]:
        """
        Get versions for a library.

        Args:
            library: Library name

        Returns:
            List of version information
        """
        try:
            # Get versions from documents that match the library
            versions = []
            for metadata in self.doc_organizer.documents.values():
                if library.lower() in metadata.url.lower():
                    for version in metadata.versions:
                        versions.append(
                            VersionInfo(
                                version=version.version_id,
                                release_date=None,  # Not available in current structure
                                doc_url=metadata.url,
                                crawl_date=version.timestamp,
                                changes=None,  # Could include version.changes if needed
                            )
                        )
            return versions
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_library_versions",
                details={"library": library},
                level=ErrorLevel.ERROR,
            )
            return []

    async def _get_version_docs(self, library: str, version: str) -> list[DocumentInfo]:
        """
        Get documents for a library version.

        Args:
            library: Library name
            version: Version string

        Returns:
            List of document information
        """
        try:
            # Adapt the document organizer to work with library/version concept
            # For now, we'll return all documents that match the library name in their URL
            docs = []
            for _doc_id, metadata in self.doc_organizer.documents.items():
                if library.lower() in metadata.url.lower():
                    docs.append(
                        DocumentInfo(
                            title=metadata.title,
                            url=metadata.url,
                            content_type="text/html",  # Default content type
                            content_format="html",  # Default format
                            last_updated=metadata.last_updated,
                            versions=[v.version_id for v in metadata.versions],
                            topics=metadata.tags,  # Use tags as topics
                            summary=f"Document in category: {metadata.category}",
                        )
                    )
            return docs
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_version_docs",
                details={"library": library, "version": version},
                level=ErrorLevel.ERROR,
            )
            return []

    async def _get_document(
        self, library: str, version: str, doc_path: str
    ) -> Optional[dict[str, Any]]:
        """
        Get a document.

        Args:
            library: Library name
            version: Version string
            doc_path: Document path

        Returns:
            Document information and content
        """
        try:
            # Find document by path and library
            doc_id = None
            for did, metadata in self.doc_organizer.documents.items():
                if doc_path in metadata.url and library.lower() in metadata.url.lower():
                    doc_id = did
                    break

            if not doc_id:
                return None

            metadata = self.doc_organizer.documents[doc_id]

            # Get the latest version content
            content = ""
            if metadata.versions:
                latest_version = metadata.versions[-1]
                content_data = latest_version.changes.get("content", {})
                content = content_data.get(
                    "formatted_content", content_data.get("text", "")
                )

            return {
                "title": metadata.title,
                "url": metadata.url,
                "content_type": "text/html",
                "content_format": "html",
                "last_updated": metadata.last_updated.isoformat()
                if metadata.last_updated
                else None,
                "versions": [v.version_id for v in metadata.versions],
                "topics": metadata.tags,
                "summary": f"Document in category: {metadata.category}",
                "content": content,
            }
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_document",
                details={"library": library, "version": version, "doc_path": doc_path},
                level=ErrorLevel.ERROR,
            )
            return None

    def get_document_list(self):
        """
        Get a list of all documents.

        Returns:
            List of document information
        """
        documents = []
        for doc_id, metadata in self.doc_organizer.documents.items():
            documents.append(
                {
                    "doc_id": doc_id,
                    "title": metadata.title,
                    "url": metadata.url,
                    "category": metadata.category,
                    "last_updated": metadata.last_updated.isoformat()
                    if metadata.last_updated
                    else None,
                    "versions": len(metadata.versions),
                }
            )
        return documents

    def get_document(self, doc_id):
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document information and content
        """
        if doc_id not in self.doc_organizer.documents:
            return None

        metadata = self.doc_organizer.documents[doc_id]
        content = ""
        if metadata.versions:
            latest_version = metadata.versions[-1]
            content_data = latest_version.changes.get("content", {})
            content = content_data.get(
                "formatted_content", content_data.get("text", "")
            )

        return {
            "doc_id": doc_id,
            "title": metadata.title,
            "url": metadata.url,
            "content": content,
            "category": metadata.category,
            "tags": metadata.tags,
            "last_updated": metadata.last_updated.isoformat()
            if metadata.last_updated
            else None,
        }

    def get_version_history(self, doc_id):
        """
        Get version history for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of version information
        """
        if doc_id not in self.doc_organizer.documents:
            return []

        versions = self.doc_organizer.get_document_versions(doc_id)
        return [
            {
                "version_id": v.version_id,
                "timestamp": v.timestamp.isoformat(),
                "hash": v.hash,
            }
            for v in versions
        ]


# Module-level FastAPI app instance
# Get the directory of the current file for default template/static paths
_current_file_dir = os.path.dirname(__file__)
_DEFAULT_TEMPLATES_DIR = os.path.join(_current_file_dir, "templates")
_DEFAULT_STATIC_DIR = os.path.join(_current_file_dir, "static")

# Instantiate DocViewer to get the app
# This ensures that 'app' is available for import by tests
doc_viewer_instance = DocViewer(
    doc_organizer=DocumentOrganizer(),  # Use the placeholder
    templates_dir=_DEFAULT_TEMPLATES_DIR,
    static_dir=_DEFAULT_STATIC_DIR,
)
app = doc_viewer_instance.app
