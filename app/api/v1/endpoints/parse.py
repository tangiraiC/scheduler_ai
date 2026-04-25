from __future__ import annotations

import inspect

from fastapi import APIRouter, HTTPException

from app.schemas.parse import ParseRequest, ParseResponse
from app.services.extraction_service import ExtractionService, ExtractionServiceError

router = APIRouter()
extraction_service = ExtractionService()


@router.post("", response_model=ParseResponse)
async def parse_text(payload: ParseRequest) -> ParseResponse:
    try:
        extraction_result = extraction_service.extract(payload.raw_text)
        if inspect.isawaitable(extraction_result):
            extraction_result = await extraction_result

        extracted_data = extraction_result.get("data", extraction_result)

        return ParseResponse(
            status="success",
            extracted_data=extracted_data,
        )
    except ExtractionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected parse failure: {exc}",
        ) from exc
