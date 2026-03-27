"""Backup and restore API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from src.api.deps import get_backup_service, require_api_key
from src.schemas.backup import (
    BackupPreview,
    ExportOptions,
    ImportResult,
)
from src.services.backup_service import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/export")
async def export_backup(
    options: ExportOptions | None = None,
    backup_service: BackupService = Depends(get_backup_service),
    _: str = Depends(require_api_key),
) -> StreamingResponse:
    """Export database to encrypted ZIP backup.

    Returns a downloadable ZIP file with the backup data.
    """
    zip_data = await backup_service.export_backup(options)
    filename = backup_service._generate_backup_filename("0.10.0")

    return StreamingResponse(
        iter([zip_data]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_data)),
        },
    )


@router.post("/import", response_model=ImportResult)
async def import_backup(
    zip_data: bytes,
    backup_service: BackupService = Depends(get_backup_service),
    _: str = Depends(require_api_key),
) -> ImportResult:
    """Import backup from encrypted ZIP.

    Args:
        zip_data: Encrypted ZIP bytes in request body.

    Returns:
        ImportResult with status and summary.
    """
    result = await backup_service.import_backup(zip_data)
    return result


@router.post("/preview", response_model=BackupPreview | None)
async def preview_backup(
    zip_data: bytes,
    backup_service: BackupService = Depends(get_backup_service),
    _: str = Depends(require_api_key),
) -> BackupPreview | None:
    """Preview backup content without importing.

    Args:
        zip_data: Encrypted ZIP bytes in request body.

    Returns:
        BackupPreview with version and counts, or None if invalid.
    """
    preview = await backup_service.preview_backup(zip_data)
    if preview is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to parse backup file. Invalid format or wrong password.",
        )
    return preview