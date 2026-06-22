import uuid
import datetime
import json
import os

import gspread
import numpy as np
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# 조직 상수
# ---------------------------------------------------------------------------
ORG = {
    "기업금융": ["기업금융1부", "기업금융2부", "기업금융3부", "구조화금융부"],
    "CM":       ["CM1부", "CM2부", "IPO부", "CM솔루션부"],
    "대체투자": ["대체투자금융1부", "대체투자금융2부", "대체투자금융3부"],
    "투자금융": ["투자금융1부", "투자금융2부", "투자금융3부"],
    "IB직속":   ["IB솔루션부"],
}

투자구조 = ["단일 Deal", "복합 Deal"]
투자유형 = ["직접대출", "PI", "단순주선", "인수주선(사모)", "인수주선(공모)", "지급보증"]
상품유형 = ["대출및사모사채", "공모사채", "Equity", "Mezzanine", "CP및전단채"]
사업유형 = ["기업금융(CM포함)", "인수금융", "부동산담보대출", "부동산개발PF", "인프라", "자산유동화"]
리소스Book유형 = ["종금Book", "셀다운Book", "PI Book", "ECM DCM북", "메자닌Book", "채무보증Book", "Book 미사용", "그룹펀드편입"]
CIB여부 = ["그룹사>당사", "당사>그룹사", "해당사항없음"]
모험자본여부 = ["O", "X"]
당사주선투자트랜치 = ["단일순위", "선순위", "중후순위", "EBL", "Mezzanine", "Equity"]
선취수수료구분 = ["취급수수료", "인수수수료", "주선수수료", "자문수수료", "확약수수료", "기타수수료", "해당사항없음", "TBD"]
BRR등급 = ["AAA", "AA", "A+", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B-", "TBD"]
진행단계 = ["내부검토", "IB실무협의회", "종금실무협의회", "투자심의협의회", "투자심의위원회", "승인완료", "신디케이션진행"]

# ---------------------------------------------------------------------------
# 연동 매핑 상수
# ---------------------------------------------------------------------------
PRODUCT_TYPE_BY_INVEST_TYPE = {
    "직접대출":       ["대출및사모사채"],
    "PI":            ["Equity", "Mezzanine"],
    "단순주선":       ["대출및사모사채", "공모사채", "Equity", "Mezzanine", "CP및전단채"],
    "인수주선(사모)":  ["대출및사모사채", "Equity", "Mezzanine", "CP및전단채"],
    "인수주선(공모)":  ["공모사채", "Equity", "Mezzanine", "CP및전단채"],
    "지급보증":        ["대출및사모사채", "공모사채", "Equity", "Mezzanine", "CP및전단채"],
}

BOOK_TYPE_BY_PRODUCT_TYPE = {
    "대출및사모사채": ["종금Book", "셀다운Book", "채무보증Book", "Book 미사용", "그룹펀드편입"],
    "공모사채":       ["ECM DCM북", "Book 미사용", "그룹펀드편입"],
    "Equity":        ["PI Book", "ECM DCM북", "채무보증Book", "Book 미사용", "그룹펀드편입"],
    "Mezzanine":     ["PI Book", "ECM DCM북", "메자닌Book", "채무보증Book", "Book 미사용", "그룹펀드편입"],
    "CP및전단채":     ["셀다운Book", "ECM DCM북", "채무보증Book", "Book 미사용", "그룹펀드편입"],
}

YIELD_TYPE_OPTIONS = {
    "대출및사모사채": ["표면금리", "YTM", "YTC", "YTP"],
    "공모사채":       ["표면금리", "YTM", "YTC", "YTP"],
    "CP및전단채":     ["표면금리", "YTM", "YTC", "YTP"],
    "Equity":        ["목표IRR", "배당수익률", "YTM", "YTC", "YTP"],
    "Mezzanine":     ["목표IRR", "배당수익률", "YTM", "YTC", "YTP"],
}

FTP_EXEMPT_BOOKS = {"채무보증Book", "Book 미사용", "그룹펀드편입"}

# 종금Book FTP 만기 구간: 3M이하 ~ 10y (7구간)
종금Book_TENOR_KEYS   = ["3M이하", "6m", "1y", "2y", "3y", "5y", "10y"]
종금Book_TENOR_MONTHS = [3.0, 6.0, 12.0, 24.0, 36.0, 60.0, 120.0]

# IB Book FTP 만기 구간: 3M이하 ~ 3Y (4구간, 3Y 초과는 3Y 적용)
IB_BOOK_TENOR_KEYS   = ["3M이하", "1Y", "2Y", "3Y"]
IB_BOOK_TENOR_MONTHS = [3.0, 12.0, 24.0, 36.0]

BOOK_TENOR_MAP = {
    "종금Book": (종금Book_TENOR_KEYS, 종금Book_TENOR_MONTHS),
    "IB Book":  (IB_BOOK_TENOR_KEYS,  IB_BOOK_TENOR_MONTHS),
}

# 시트 저장용 전체 테너 컬럼 (두 book의 합집합)
_FTP_TENOR_ALL = 종금Book_TENOR_KEYS + [k for k in IB_BOOK_TENOR_KEYS if k not in 종금Book_TENOR_KEYS]

# ---------------------------------------------------------------------------
# 컬럼 정의
# ---------------------------------------------------------------------------
USERS_COLUMNS = ["이름", "사번", "소속"]

DEAL_COLUMNS = [
    "deal_id", "트랜치번호", "부문", "본부", "부서", "최초작성일", "입력일",
    "딜명", "상세내용/진행상황", "투자구조", "사업유형", "CIB여부", "모험자본여부",
    "전체딜규모", "진행단계", "기표예정일",
    "투자유형", "상품유형", "리소스Book유형", "당사주선/투자 트랜치",
    "당사주선/인수규모", "당사투자금액",
    "투자수익률구분", "투자수익률", "선취수수료구분", "선취수수료금액",
    "투자기간만기", "BRR등급",
]

FTP_COLUMNS = ["날짜", "book_type"] + _FTP_TENOR_ALL

# ---------------------------------------------------------------------------
# Google Sheets 연결
# ---------------------------------------------------------------------------
_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def _get_spreadsheet():
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["SHEET_ID"])


def _get_or_create_ws(name: str, columns: list) -> gspread.Worksheet:
    ss = _get_spreadsheet()
    try:
        ws = ss.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=len(columns))
        ws.insert_row(columns, 1)
        return ws
    first_row = ws.row_values(1)
    if not first_row:
        ws.insert_row(columns, 1)
    elif first_row[:len(columns)] != columns:
        # 헤더 구조 변경 시 시트 초기화 후 새 헤더로 재생성 (FTP 등 구조 변경 대응)
        ws.clear()
        ws.insert_row(columns, 1)
    return ws


def _ws_to_df(ws: gspread.Worksheet, columns: list) -> pd.DataFrame:
    """시트 전체를 읽어 DataFrame으로 반환. 헤더 없으면 빈 DataFrame."""
    rows = ws.get_all_values()
    if not rows or not rows[0]:
        return pd.DataFrame(columns=columns)
    headers = rows[0]
    data = rows[1:]
    if not data:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(data, columns=headers)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def _to_str(val) -> str:
    """NaN/None을 빈 문자열로 변환"""
    if val is None:
        return ""
    try:
        if np.isnan(float(val)) if isinstance(val, (int, float)) else False:
            return ""
    except (TypeError, ValueError):
        pass
    return str(val)


# ---------------------------------------------------------------------------
# 사용자 인증 함수
# ---------------------------------------------------------------------------
ADMIN_DEPT = "IB사업추진부"

def load_users() -> pd.DataFrame:
    ws = _get_or_create_ws("users", USERS_COLUMNS)
    return _ws_to_df(ws, USERS_COLUMNS)


def get_user_info(이름: str, 사번: str) -> dict | None:
    """이름+사번으로 사용자 조회. 반환: {"role", "division", "department", "소속"} or None"""
    df = load_users()
    if df.empty:
        return None
    mask = (
        (df["이름"].astype(str).str.strip() == 이름.strip()) &
        (df["사번"].astype(str).str.strip() == 사번.strip())
    )
    matched = df[mask]
    if matched.empty:
        return None
    소속 = str(matched.iloc[0]["소속"]).strip()

    if 소속 == ADMIN_DEPT:
        return {"role": "관리자", "division": None, "department": None, "소속": 소속}

    for division, departments in ORG.items():
        if 소속 in departments:
            return {"role": "영업", "division": division, "department": 소속, "소속": 소속}

    return None  # 등록되지 않은 소속


# ---------------------------------------------------------------------------
# 딜 함수
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_deals() -> pd.DataFrame:
    ws = _get_or_create_ws("deals", DEAL_COLUMNS)
    df = _ws_to_df(ws, DEAL_COLUMNS)
    for col in ["전체딜규모", "당사주선/인수규모", "당사투자금액", "투자수익률", "선취수수료금액"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "투자기간만기" in df.columns:
        df["투자기간만기"] = pd.to_numeric(df["투자기간만기"], errors="coerce")
    if "트랜치번호" in df.columns:
        df["트랜치번호"] = pd.to_numeric(df["트랜치번호"], errors="coerce").astype("Int64")
    return df


def append_deal(rows: list[dict]):
    ws = _get_or_create_ws("deals", DEAL_COLUMNS)
    for row in rows:
        ws.append_row([_to_str(row.get(col, "")) for col in DEAL_COLUMNS])
    load_deals.clear()


def filter_by_view(df: pd.DataFrame, ss: dict) -> pd.DataFrame:
    level = ss.get("view_level")
    if level == "all":
        return df
    if level == "division":
        return df[df["본부"] == ss.get("selected_division")]
    return df[df["부서"] == ss.get("selected_department")]


def update_deals(edited_df: pd.DataFrame, ss_state: dict):
    full = load_deals()
    level = ss_state.get("view_level")
    if level == "all":
        mask = pd.Series([True] * len(full), index=full.index)
    elif level == "division":
        mask = full["본부"] == ss_state.get("selected_division")
    else:
        mask = full["부서"] == ss_state.get("selected_department")

    keep = full[~mask]
    save_cols = [c for c in DEAL_COLUMNS if c in edited_df.columns]
    result = pd.concat([keep, edited_df[save_cols]], ignore_index=True)

    ws = _get_or_create_ws("deals", DEAL_COLUMNS)
    ws.clear()
    clean = result.fillna("").astype(str)
    ws.update([DEAL_COLUMNS] + clean.values.tolist())
    load_deals.clear()


# ---------------------------------------------------------------------------
# FTP 함수
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_ftp() -> pd.DataFrame:
    ws = _get_or_create_ws("ftp", FTP_COLUMNS)
    df = _ws_to_df(ws, FTP_COLUMNS)
    for col in _FTP_TENOR_ALL:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def append_ftp(date: str, book_type: str, rates: dict):
    ws = _get_or_create_ws("ftp", FTP_COLUMNS)
    row = {"날짜": date, "book_type": book_type}
    row.update(rates)
    ws.append_row([_to_str(row.get(col, "")) for col in FTP_COLUMNS])
    load_ftp.clear()


def get_latest_ftp(book_type: str) -> dict | None:
    df = load_ftp()
    df = df[df["book_type"] == book_type].copy()
    if df.empty:
        return None
    # 가장 최근 날짜 중 마지막으로 입력된 행 사용 (같은 날짜 중복 입력 시 최후 행 기준)
    max_date = df["날짜"].max()
    row = df[df["날짜"] == max_date].iloc[-1]
    tenor_keys = BOOK_TENOR_MAP.get(book_type, (종금Book_TENOR_KEYS, []))[0]
    return {k: row.get(k, float("nan")) for k in tenor_keys}


def get_ftp_rate(book_type: str, maturity_months: float) -> float | None:
    rates_dict = get_latest_ftp(book_type)
    if rates_dict is None:
        return None
    tenor_keys, tenor_months = BOOK_TENOR_MAP.get(book_type, (종금Book_TENOR_KEYS, 종금Book_TENOR_MONTHS))
    try:
        rate_values = [float(rates_dict[k]) for k in tenor_keys]
    except (KeyError, TypeError, ValueError):
        return None
    if any(np.isnan(v) for v in rate_values):
        return None
    return float(np.interp(maturity_months, tenor_months, rate_values))


# ---------------------------------------------------------------------------
# 순영업수익 산출
# ---------------------------------------------------------------------------
def _holding_months(기표예정일_str, 투자기간만기, current_year: int) -> float:
    try:
        maturity = float(투자기간만기) if 투자기간만기 else 0
    except (ValueError, TypeError):
        maturity = 0

    if not 기표예정일_str or pd.isna(기표예정일_str):
        return min(maturity, 12.0)

    try:
        dt = datetime.date.fromisoformat(str(기표예정일_str))
    except ValueError:
        return min(maturity, 12.0)

    year_end = datetime.date(current_year, 12, 31)

    if dt.year > current_year:
        return 0.0
    if dt.year < current_year:
        return min(maturity, 12.0)
    remaining_days = (year_end - dt).days
    remaining_months = remaining_days / 30.44
    return min(maturity, remaining_months)


def _get_ftp_rate_from_cache(ftp_book: str, maturity_months: float, ftp_cache: dict) -> float | None:
    rates_dict = ftp_cache.get(ftp_book)
    if rates_dict is None:
        return None
    tenor_keys, tenor_months = BOOK_TENOR_MAP.get(ftp_book, (종금Book_TENOR_KEYS, 종금Book_TENOR_MONTHS))
    try:
        rate_values = [float(rates_dict[k]) for k in tenor_keys]
    except (KeyError, TypeError, ValueError):
        return None
    if any(np.isnan(v) for v in rate_values):
        return None
    return float(np.interp(maturity_months, tenor_months, rate_values))


def calc_net_revenue(row: dict | pd.Series, current_year: int = None, ftp_cache: dict = None) -> dict:
    if current_year is None:
        current_year = datetime.date.today().year

    nan = float("nan")

    def safe(val):
        try:
            v = float(val)
            return v if not np.isnan(v) else None
        except (TypeError, ValueError):
            return None

    투자금액 = safe(row.get("당사투자금액"))
    수익률 = safe(row.get("투자수익률"))
    수수료금액 = safe(row.get("선취수수료금액")) or 0.0
    만기 = safe(row.get("투자기간만기")) or 0
    book = str(row.get("리소스Book유형") or "")
    기표일 = row.get("기표예정일")

    if 투자금액 is None or 수익률 is None:
        return {"수수료수익": 수수료금액, "이자수익": nan, "자본원가": nan, "Carry손익": nan, "순영업수익": nan}

    holding = _holding_months(기표일, 만기, current_year)
    이자수익 = 투자금액 * (수익률 / 100) * (holding / 12)

    if book in FTP_EXEMPT_BOOKS:
        자본원가 = 0.0
    else:
        ftp_book = "종금Book" if book == "종금Book" else "IB Book"
        if ftp_cache is not None:
            ftp_rate = _get_ftp_rate_from_cache(ftp_book, 만기, ftp_cache)
        else:
            ftp_rate = get_ftp_rate(ftp_book, 만기)
        if ftp_rate is None:
            return {"수수료수익": 수수료금액, "이자수익": 이자수익, "자본원가": nan, "Carry손익": nan, "순영업수익": nan}
        자본원가 = 투자금액 * (ftp_rate / 100) * (holding / 12)

    Carry손익 = 이자수익 - 자본원가
    순영업수익 = 수수료금액 + Carry손익
    return {"수수료수익": 수수료금액, "이자수익": 이자수익, "자본원가": 자본원가, "Carry손익": Carry손익, "순영업수익": 순영업수익}


def add_revenue_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # FTP 데이터를 한 번만 로드해서 딜 행마다 반복 API 호출 방지
    ftp_cache = {
        "종금Book": get_latest_ftp("종금Book"),
        "IB Book": get_latest_ftp("IB Book"),
    }
    current_year = datetime.date.today().year
    results = [calc_net_revenue(row, current_year=current_year, ftp_cache=ftp_cache) for _, row in df.iterrows()]
    df["수수료수익"] = [r["수수료수익"] for r in results]
    df["이자수익"] = [r["이자수익"] for r in results]
    df["자본원가"] = [r["자본원가"] for r in results]
    df["Carry손익"] = [r["Carry손익"] for r in results]
    df["순영업수익"] = [r["순영업수익"] for r in results]
    return df


# ---------------------------------------------------------------------------
# 헬퍼: 신규딜 행 딕셔너리 생성
# ---------------------------------------------------------------------------
def make_deal_rows(common: dict, tranches: list[dict]) -> list[dict]:
    deal_id = str(uuid.uuid4())
    today = datetime.date.today().isoformat()
    rows = []
    for i, t in enumerate(tranches, start=1):
        row = {
            "deal_id": deal_id,
            "트랜치번호": i,
            "부문": "IB부문",
            "본부": common.get("본부", ""),
            "부서": common.get("부서", ""),
            "최초작성일": today,
            "입력일": today,
            "딜명": common.get("딜명", ""),
            "상세내용/진행상황": common.get("상세내용/진행상황", ""),
            "투자구조": common.get("투자구조", ""),
            "사업유형": common.get("사업유형", ""),
            "CIB여부": common.get("CIB여부", ""),
            "모험자본여부": common.get("모험자본여부", ""),
            "전체딜규모": common.get("전체딜규모", ""),
            "진행단계": common.get("진행단계", ""),
            "기표예정일": common.get("기표예정일", ""),
            "투자유형": t.get("투자유형", ""),
            "상품유형": t.get("상품유형", ""),
            "리소스Book유형": t.get("리소스Book유형", ""),
            "당사주선/투자 트랜치": t.get("당사주선/투자 트랜치", ""),
            "당사주선/인수규모": t.get("당사주선/인수규모", ""),
            "당사투자금액": t.get("당사투자금액", ""),
            "투자수익률구분": t.get("투자수익률구분", ""),
            "투자수익률": t.get("투자수익률", ""),
            "선취수수료구분": t.get("선취수수료구분", ""),
            "선취수수료금액": t.get("선취수수료금액", ""),
            "투자기간만기": t.get("투자기간만기", ""),
            "BRR등급": t.get("BRR등급", ""),
        }
        rows.append(row)
    return rows
