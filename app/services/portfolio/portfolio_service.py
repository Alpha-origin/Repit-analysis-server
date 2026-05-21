from services.portfolio.pdf_parse.pdf_parser import PdfParser


class PortfolioService:

    def __init__(self):
        self._pdf_parser = PdfParser()

    async def get_portfolio_text(self, pdf_bytes: bytes) -> str:
        pdf_data = self._pdf_parser.parse(pdf_bytes)
        return pdf_data
