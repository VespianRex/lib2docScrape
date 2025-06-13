import asyncio
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from fastapi.templating import Jinja2Templates

from ..websockets.test_manager import test_ws_manager

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/test-dashboard")
async def test_dashboard(request: Request):
    """Render the test dashboard page"""
    return templates.TemplateResponse(request, "test_dashboard.html", {"request": request})


@router.get("/api/tests/export")
async def export_test_results(
    format: str = Query("json", description="Export format: json, csv, xml"),
    include_logs: bool = Query(False, description="Include test logs in export"),
):
    """Export test results in various formats"""
    try:
        # Get current test statistics and logs
        stats = test_ws_manager.stats.copy()
        logs = test_ws_manager.logs.copy() if include_logs else []

        # Add timestamp
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "test_statistics": stats,
            "test_logs": logs if include_logs else None,
        }

        if format.lower() == "json":
            return JSONResponse(
                content=export_data,
                headers={
                    "Content-Disposition": f"attachment; filename=test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                },
            )

        elif format.lower() == "csv":
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)

            # Write statistics
            writer.writerow(["Test Statistics"])
            writer.writerow(["Metric", "Value"])
            for key, value in stats.items():
                writer.writerow([key, value])

            # Write logs if requested
            if include_logs and logs:
                writer.writerow([])  # Empty row
                writer.writerow(["Test Logs"])
                writer.writerow(["Timestamp", "Level", "Message"])
                for log in logs:
                    writer.writerow(
                        [
                            log.get("timestamp", ""),
                            log.get("level", ""),
                            log.get("message", ""),
                        ]
                    )

            csv_content = output.getvalue()
            output.close()

            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                },
            )

        elif format.lower() == "xml":
            # Create XML content
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<test_results export_timestamp="{export_data["export_timestamp"]}">
    <statistics>
"""
            for key, value in stats.items():
                xml_content += f"        <{key}>{value}</{key}>\n"

            xml_content += "    </statistics>\n"

            if include_logs and logs:
                xml_content += "    <logs>\n"
                for log in logs:
                    xml_content += f"""        <log>
            <timestamp>{log.get("timestamp", "")}</timestamp>
            <level>{log.get("level", "")}</level>
            <message><![CDATA[{log.get("message", "")}]]></message>
        </log>
"""
                xml_content += "    </logs>\n"

            xml_content += "</test_results>"

            return Response(
                content=xml_content,
                media_type="application/xml",
                headers={
                    "Content-Disposition": f"attachment; filename=test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                },
            )

        else:
            return JSONResponse(
                content={
                    "error": f"Unsupported format: {format}. Supported formats: json, csv, xml"
                },
                status_code=400,
            )

    except Exception as e:
        return JSONResponse(
            content={"error": f"Export failed: {str(e)}"}, status_code=500
        )


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
        if report.when == "call":  # Only process the actual test result
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
            asyncio.create_task(
                test_ws_manager.add_log(
                    "INFO" if report.passed else "ERROR",
                    f"Test {report.nodeid}: {report.outcome}",
                )
            )

    return {"pytest_runtest_logreport": pytest_runtest_logreport}
