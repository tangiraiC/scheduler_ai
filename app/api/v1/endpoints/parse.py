from fastapi import APIRouter

from app.models.request_models import ParseRequest
from app.models.response_models import ParseResponse
from app.services.extraction_service import ExtractionService

router = APIRouter()


@router.post("", response_model=ParseResponse)
async def parse_text(payload: ParseRequest) -> ParseResponse:
    extractor = ExtractionService()
    extracted_data = extractor.extract(payload.text)
    return ParseResponse(input_text=payload.text, extracted_data=extracted_data)
