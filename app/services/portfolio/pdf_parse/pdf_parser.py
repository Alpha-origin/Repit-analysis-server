import fitz
import re
from collections import Counter
from services.portfolio.pdf_parse.txt_importance import is_noise_block, is_section_header

# 노션 PDF 특유의 불릿 문자 패턴
BULLET_PATTERN = re.compile(r'^[◽◼▪▫•·‣⁃▸▹►▻➤➢➣➔→⇒※✦✧✱✲✳✴✵]+\s*')

# 최소 폰트 크기 — 이 미만은 footer/워터마크로 간주해 제거
MIN_FONT_SIZE = 8.0


class PdfParser:
    """
    PDF bytes를 받아 LLM에 넘길 정제된 plain text를 반환한다.

    파이프라인:
        1. PyMuPDF로 페이지별 블록 추출 (font_size, is_bold, indent, text 포함)
        2. 소형 폰트 블록 제거 (노션 footer 등)
        3. 헤더/푸터 감지 및 제거 (페이지 반복 텍스트)
        4. 노이즈 블록 필터링 (빈칸, 장식문자 등)
        5. 불릿 문자 정리 후 plain text 조립
    """

    # 헤더/푸터 판단 기준: 전체 페이지의 이 비율 이상 반복되면 제거
    REPEATED_TEXT_THRESHOLD = 0.4

    def parse(self, pdf_bytes: bytes) -> str:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            total_pages = len(doc)

            # 1단계: 모든 페이지에서 블록 추출 (소형 폰트 제거 포함)
            all_pages_blocks = []
            for page in doc:
                blocks = self._extract_blocks(page)
                all_pages_blocks.append(blocks)

        # 2단계: 헤더/푸터 텍스트 감지
        repeated_texts = self._detect_repeated_texts(all_pages_blocks, total_pages)

        # 3단계: 필터링 + plain text 조립
        result_lines = []
        _prev_ends_mid_word = False  # 직전 블록이 단어 중간에서 끊겼는지

        for blocks in all_pages_blocks:
            seen_in_page = set()  # 같은 페이지 내 중복 블록만 제거

            for block in blocks:
                text = block["text"].strip()

                # 헤더/푸터 반복 텍스트 제거
                if text in repeated_texts:
                    _prev_ends_mid_word = False
                    continue

                # 불릿 문자 제거
                text = BULLET_PATTERN.sub('', text).strip()

                # 노이즈 블록 제거
                if is_noise_block(text):
                    _prev_ends_mid_word = False
                    continue

                # 같은 페이지 내 완전히 동일한 블록 중복 제거
                if text in seen_in_page:
                    _prev_ends_mid_word = False
                    continue
                seen_in_page.add(text)

                # 섹션 헤더면 앞에 빈 줄 추가해서 구분
                if is_section_header(block):
                    result_lines.append("")
                    result_lines.append(f"[{text}]")
                else:
                    # 페이지 경계 단어 분리 복원:
                    # 직전 블록이 mid_word로 끝났고, 현재 텍스트가 짧은 음절 조각이면 이어붙임
                    # 조건: 직전 라인이 있고 + 헤더가 아니고 + 현재 텍스트가 3글자 이하(음절 파편)
                    if (result_lines
                            and result_lines[-1]
                            and not result_lines[-1].startswith("[")
                            and _prev_ends_mid_word
                            and len(text.replace(" ", "")) <= 2):
                        result_lines[-1] += text
                    else:
                        result_lines.append(text)

                _prev_ends_mid_word = block.get("ends_mid_word", False)

        return self._clean_output("\n".join(result_lines))

    def _extract_blocks(self, page: fitz.Page) -> list[dict]:
        """
        페이지에서 블록 단위로 텍스트와 메타정보 추출.
        fitz의 get_text("dict")는 blocks > lines > spans 구조.
        - 같은 라인의 스팬들은 공백 없이 이어붙임 (노션 PDF 특성상 단어가 스팬으로 쪼개짐)
        - 라인 간은 스페이스로 구분
        - MIN_FONT_SIZE 미만 블록은 footer로 간주해 스킵
        """
        raw = page.get_text("dict")
        blocks = []

        for block in raw.get("blocks", []):
            # 이미지 블록 등 type != 0은 텍스트 블록이 아님
            if block.get("type") != 0:
                continue

            block_text_parts = []
            font_sizes = []
            is_bold = False
            indent = None

            for line in block.get("lines", []):
                line_spans = line.get("spans", [])
                if not line_spans:
                    continue

                # 같은 라인의 스팬은 그대로 이어붙임
                # 노션은 링크/이탤릭/코드 등 서식 경계마다 스팬을 쪼개지만
                # 공백은 스팬 내부에 포함되어 있으므로 추가 공백 없이 연결
                line_text = "".join(span.get("text", "") for span in line_spans)

                for span in line_spans:
                    font_sizes.append(span.get("size", 0))

                    # fitz flags: bold = bit 4 (16)
                    if span.get("flags", 0) & 16:
                        is_bold = True

                    # 들여쓰기: 첫 스팬의 x 좌표
                    if indent is None:
                        indent = round(span.get("origin", (0, 0))[0])

                block_text_parts.append(line_text)

            if not font_sizes:
                continue

            avg_font_size = sum(font_sizes) / len(font_sizes)

            # 소형 폰트 블록 제거 (노션 footer: size=7.5)
            if avg_font_size < MIN_FONT_SIZE:
                continue

            # 라인들을 이어붙임 (노션 PDF는 같은 블록 내 라인이 한 문장의 줄바꿈)
            # 연결 규칙:
            #   - 앞 라인이 공백으로 끝남 → 그냥 이어붙임 (공백 이미 포함)
            #   - 앞 라인이 공백 없이 끝나고 뒷 라인이 짧은 조각(3자 이하) → 단어 파편, 공백 없이 붙임
            #   - 앞 라인이 공백 없이 끝나고 뒷 라인이 긴 텍스트 → 새 항목, 스페이스 삽입
            full_text = ""
            for part in block_text_parts:
                if not part.strip():
                    continue
                if full_text:
                    prev_ends_space = full_text[-1].isspace()
                    next_starts_space = part[0].isspace()
                    if prev_ends_space or next_starts_space:
                        full_text += part
                    elif len(part.replace(" ", "")) <= 2:
                        # 짧은 조각(2자 이하) → 단어 파편으로 간주, 공백 없이 붙임
                        full_text += part
                    else:
                        # 긴 텍스트 → 스페이스로 구분
                        full_text += " " + part
                else:
                    full_text = part
            full_text = full_text.strip()

            if full_text:
                # ends_mid_word: 블록의 마지막 문자가 영문자로 끝남
                # (한글 완성 음절로 끝나면 단어가 완결된 것이므로 제외)
                # → 다음 블록/페이지의 첫 텍스트가 이 영문 단어의 나머지일 수 있음
                last_char = full_text[-1] if full_text else ''
                ends_mid_word = last_char.isalpha() and ord(last_char) < 0xAC00
                blocks.append({
                    "text": full_text,
                    "font_size": avg_font_size,
                    "is_bold": is_bold,
                    "indent": indent if indent is not None else 0,
                    "ends_mid_word": ends_mid_word,
                })

        return blocks

    def _detect_repeated_texts(self, all_pages_blocks: list, total_pages: int) -> set:
        """
        전체 페이지에서 일정 비율 이상 반복되는 텍스트를 헤더/푸터로 판단.
        단, 페이지가 2장 이하면 감지 스킵.
        """
        if total_pages <= 2:
            return set()

        text_counter = Counter()
        for blocks in all_pages_blocks:
            # 페이지당 중복 카운트 방지
            page_texts = {b["text"].strip() for b in blocks}
            text_counter.update(page_texts)

        threshold = total_pages * self.REPEATED_TEXT_THRESHOLD
        return {text for text, count in text_counter.items() if count >= threshold}

    def _clean_output(self, text: str) -> str:
        """연속된 빈 줄 정리"""
        # 3줄 이상 연속 빈 줄 → 2줄로 압축
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
