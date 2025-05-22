"""
Web-based documentation viewer for lib2docScrape.

This module provides a web-based UI for visualizing documentation and version differences.
"""
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

import fastapi
from fastapi import FastAPI, HTTPException, Query, Path, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.organizers import DocOrganizer
from src.organizers.library_version_tracker import LibraryVersionTracker
from src.processors.content.format_handler import FormatHandler, DocFormat
from src.utils.error_handler import ErrorContext, handle_error, ErrorCategory, ErrorLevel

logger = logging.getLogger(__name__)

# Models for API
class VersionInfo(BaseModel):
    """Version information."""
    version: str
    release_date: Optional[datetime] = None
    doc_url: str
    crawl_date: datetime
    changes: Optional[Dict[str, Any]] = None


class DocumentInfo(BaseModel):
    """Document information."""
    title: str
    url: str
    content_type: str
    content_format: str
    last_updated: datetime
    versions: List[str]
    topics: List[str]
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
    topics: Optional[List[str]] = None
    content_type: Optional[str] = None


class DocViewerApp:
    """Web-based documentation viewer application."""
    
    def __init__(
        self,
        doc_organizer: Optional[DocOrganizer] = None,
        version_tracker: Optional[LibraryVersionTracker] = None,
        format_handler: Optional[FormatHandler] = None,
        templates_dir: str = "templates",
        static_dir: str = "static"
    ):
        """
        Initialize the documentation viewer application.
        
        Args:
            doc_organizer: Document organizer
            version_tracker: Library version tracker
            format_handler: Format handler
            templates_dir: Templates directory
            static_dir: Static files directory
        """
        self.doc_organizer = doc_organizer or DocOrganizer()
        self.version_tracker = version_tracker or LibraryVersionTracker()
        self.format_handler = format_handler or FormatHandler()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="lib2docScrape Documentation Viewer",
            description="Web-based UI for visualizing documentation and version differences",
            version="0.1.0"
        )
        
        # Set up templates and static files
        self.templates = Jinja2Templates(directory=templates_dir)
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # Register routes
        self._register_routes()
        
        logger.info("Documentation viewer application initialized")
    
    def _register_routes(self) -> None:
        """Register application routes."""
        # Home page
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "home.html",
                {"request": request, "libraries": libraries}
            )
        
        # Library page
        @self.app.get("/library/{library}", response_class=HTMLResponse)
        async def library(request: Request, library: str):
            versions = await self._get_library_versions(library)
            if not versions:
                raise HTTPException(status_code=404, detail=f"Library {library} not found")
            
            return self.templates.TemplateResponse(
                "library.html",
                {"request": request, "library": library, "versions": versions}
            )
        
        # Version page
        @self.app.get("/library/{library}/version/{version}", response_class=HTMLResponse)
        async def version(request: Request, library: str, version: str):
            docs = await self._get_version_docs(library, version)
            if not docs:
                raise HTTPException(status_code=404, detail=f"Version {version} of library {library} not found")
            
            return self.templates.TemplateResponse(
                "version.html",
                {"request": request, "library": library, "version": version, "docs": docs}
            )
        
        # Document page
        @self.app.get("/library/{library}/version/{version}/doc/{doc_path:path}", response_class=HTMLResponse)
        async def document(request: Request, library: str, version: str, doc_path: str):
            doc = await self._get_document(library, version, doc_path)
            if not doc:
                raise HTTPException(status_code=404, detail=f"Document {doc_path} not found")
            
            return self.templates.TemplateResponse(
                "document.html",
                {"request": request, "library": library, "version": version, "doc": doc}
            )
        
        # Diff page
        @self.app.get("/diff", response_class=HTMLResponse)
        async def diff_page(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "diff.html",
                {"request": request, "libraries": libraries}
            )
        
        # Diff API
        @self.app.post("/api/diff", response_class=JSONResponse)
        async def diff(request: DiffRequest):
            diff_result = await self._get_diff(
                request.library,
                request.doc_path,
                request.version1,
                request.version2,
                request.format
            )
            if not diff_result:
                raise HTTPException(status_code=404, detail="Could not generate diff")
            
            return diff_result
        
        # Search page
        @self.app.get("/search", response_class=HTMLResponse)
        async def search_page(request: Request):
            libraries = await self._get_libraries()
            return self.templates.TemplateResponse(
                "search.html",
                {"request": request, "libraries": libraries}
            )
        
        # Search API
        @self.app.post("/api/search", response_class=JSONResponse)
        async def search(request: SearchRequest):
            results = await self._search(
                request.query,
                request.library,
                request.version,
                request.topics,
                request.content_type
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
                raise HTTPException(status_code=404, detail=f"Library {library} not found")
            
            return {"library": library, "versions": versions}
        
        @self.app.get("/api/library/{library}/version/{version}/docs", response_class=JSONResponse)
        async def api_docs(library: str, version: str):
            docs = await self._get_version_docs(library, version)
            if not docs:
                raise HTTPException(status_code=404, detail=f"Version {version} of library {library} not found")
            
            return {"library": library, "version": version, "docs": docs}
    
    async def _get_libraries(self) -> List[str]:
        """
        Get list of available libraries.
        
        Returns:
            List of library names
        """
        try:
            return self.version_tracker.get_libraries()
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_libraries",
                level=ErrorLevel.ERROR
            )
            return []
    
    async def _get_library_versions(self, library: str) -> List[VersionInfo]:
        """
        Get versions for a library.
        
        Args:
            library: Library name
            
        Returns:
            List of version information
        """
        try:
            versions = self.version_tracker.get_versions(library)
            return [
                VersionInfo(
                    version=v.version,
                    release_date=v.release_date,
                    doc_url=v.doc_url,
                    crawl_date=v.crawl_date,
                    changes=v.changes
                )
                for v in versions
            ]
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_library_versions",
                details={"library": library},
                level=ErrorLevel.ERROR
            )
            return []
    
    async def _get_version_docs(self, library: str, version: str) -> List[DocumentInfo]:
        """
        Get documents for a library version.
        
        Args:
            library: Library name
            version: Version string
            
        Returns:
            List of document information
        """
        try:
            docs = self.doc_organizer.get_documents(library, version)
            return [
                DocumentInfo(
                    title=doc.title or doc.path,
                    url=doc.url,
                    content_type=doc.content_type,
                    content_format=doc.format,
                    last_updated=doc.last_updated,
                    versions=[v.version for v in doc.versions],
                    topics=doc.topics,
                    summary=doc.summary
                )
                for doc in docs
            ]
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_version_docs",
                details={"library": library, "version": version},
                level=ErrorLevel.ERROR
            )
            return []
    
    async def _get_document(self, library: str, version: str, doc_path: str) -> Optional[Dict[str, Any]]:
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
            doc = self.doc_organizer.get_document(library, version, doc_path)
            if not doc:
                return None
            
            # Convert content to HTML if needed
            content = doc.content
            if doc.format != "html":
                from_format = DocFormat(doc.format)
                content = self.format_handler.convert(content, from_format, DocFormat.HTML)
            
            return {
                "title": doc.title or doc.path,
                "url": doc.url,
                "content_type": doc.content_type,
                "content_format": doc.format,
                "last_updated": doc.last_updated,
                "versions": [v.version for v in doc.versions],
                "topics": doc.topics,
                "summary": doc.summary,
                "content": content
            }
        except Exception as e:
            handle_error(
                e,
                "DocViewerApp",
                "_get_document",
                details={"library": library, "version": version, "doc_path": doc_path},
                level=ErrorLevel.ERROR
            )
            return None
