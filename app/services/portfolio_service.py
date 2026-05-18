from utils.pdf_parser import PdfParser


class PortfolioService:

    def __init__(self):
        self._pdf_parser = PdfParser()

    async def get_portfolio_text(self, pdf_bytes: bytes) -> str:
        """
        PDF를 정제된 plain text로 변환한다.
        이후 LLM 호출 시 이 텍스트를 프롬프트에 삽입한다.
        """
        return self._pdf_parser.parse(pdf_bytes)
