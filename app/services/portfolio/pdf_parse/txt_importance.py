import re
from .dict import SECTION_TYPE_MAP

# 중요도 판별 임계값
IMPORTANCE_THRESHOLD = 5

# 장식용 문자 패턴 (구분선, 특수문자, 유니코드 박스 드로잉 문자 등)
DECORATIVE_PATTERN = re.compile(
    r'^[\s\-_=\|●•·▪▫◦◆◇★☆✓✔✗✘/\\|+*#~`^<>{}()\[\]'
    r'─-╿'   # BOX DRAWING (─, │, ┌ 등)
    r'▀-▟'   # BLOCK ELEMENTS (█, ▓ 등)
    r'■-◿'   # GEOMETRIC SHAPES (■, ▲ 등)
    r']{3,}$'
)

# 페이지 번호 패턴 ("Page N" 형식만 — 단독 숫자는 is_noise_block의 길이 조건이 커버)
PAGE_NUMBER_PATTERN = re.compile(r'^page\s*\d+$', re.IGNORECASE)


def is_noise_block(text: str) -> bool:
    """노이즈 블록 여부 판별 — True면 제거 대상"""
    stripped = text.strip()

    # 1. 빈 텍스트
    if not stripped:
        return True

    # 2. 너무 짧음 (1글자, 공백 제거 기준)
    if len(stripped.replace(" ", "")) < 2:
        return True

    # 3. 장식용 문자만으로 구성
    if DECORATIVE_PATTERN.match(stripped):
        return True

    # 4. 페이지 번호
    if PAGE_NUMBER_PATTERN.match(stripped):
        return True

    return False


def score_block(block: dict) -> int:
    """
    블록의 중요도 점수 계산.
    font_size, is_bold, indent, 섹션 키워드 포함 여부로 판단.
    높을수록 헤더/섹션 제목일 가능성 높음.
    """
    score = 0
    text = block.get("text", "").strip()
    font_size = block.get("font_size", 0)
    is_bold = block.get("is_bold", False)
    indent = block.get("indent", 999)

    # 폰트 크기
    if font_size >= 18:
        score += 5
    elif font_size >= 14:
        score += 3
    elif font_size >= 12:
        score += 1

    # 볼드
    if is_bold:
        score += 3

    # 들여쓰기 없음 (좌측 정렬 = 섹션 제목 가능성)
    if indent == 0:
        score += 2

    # 섹션 키워드 포함 여부
    text_lower = text.lower()
    for keywords in SECTION_TYPE_MAP.values():
        if any(kw in text_lower for kw in keywords):
            score += 3
            break

    return score


def is_section_header(block: dict) -> bool:
    """블록이 섹션 헤더인지 판별"""
    return score_block(block) >= IMPORTANCE_THRESHOLD
