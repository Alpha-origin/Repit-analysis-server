import fitz

class PortfolioService:
    async def parsePdf(self, pdf_file: bytes):
        doc = fitz.open(stream=pdf_file, filetype="pdf")

        text = ""
        for page in doc:
            text += page.get_text()

        doc.close()

        return {
            "pdf_content": text
        }
