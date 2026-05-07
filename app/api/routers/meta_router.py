from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from core import CommonResponse
from services import PortfolioService
router = APIRouter(prefix="/meta", tags=["portfolio"])

portfolio_service = PortfolioService()

@router.post("/", response_model=CommonResponse)
async def get_portfolio(
        pdf: UploadFile = File(...),
        github_url: str = Form(...),
):
    pdf_bytes = await pdf.read()

    result = await portfolio_service.parsePdf(pdf_bytes)
    print(result)
