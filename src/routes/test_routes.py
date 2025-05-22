import os
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from ..websockets.test_manager import test_ws_manager
from typing import Dict

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/test-dashboard")
async def test_dashboard(request: Request):
    """Render the test dashboard page"""
    return templates.TemplateResponse(
        "test_dashboard.html",
        {"request": request}
    )

@router.get("/api/tests/export")
async def export_test_results():
    """Export test results in various formats"""
    # TODO: Implement export functionality
    return {"message": "Export functionality coming soon"}

@router.websocket("/ws/tests")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for test monitoring"""
    await test_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await test_ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        test_ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        test_ws_manager.disconnect(websocket)

# Initialize test monitoring hooks
def init_test_monitoring():
    """Initialize test monitoring hooks for pytest"""
    def pytest_runtest_logreport(report):
        """Hook for test result reporting"""
        if report.when == 'call':  # Only process the actual test result
            # Update test status
            if report.passed:
                test_ws_manager.stats["passed"] += 1
            elif report.failed:
                test_ws_manager.stats["failed"] += 1
            elif report.skipped:
                test_ws_manager.stats["skipped"] += 1
            
            test_ws_manager.stats["total"] += 1
            
            # Send updates via WebSocket
            asyncio.create_task(test_ws_manager.update_status(test_ws_manager.stats))
            asyncio.create_task(test_ws_manager.add_log(
                "INFO" if report.passed else "ERROR",
                f"Test {report.nodeid}: {report.outcome}"
            ))

    return {
        "pytest_runtest_logreport": pytest_runtest_logreport
    }