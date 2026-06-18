import datetime

import pandas as pd
import streamlit as st

import data_utils as du

st.set_page_config(page_title="IB 영업현황 관리", layout="wide")

# ---------------------------------------------------------------------------
# session_state 초기화
# ---------------------------------------------------------------------------
DEFAULTS = {
    "current_page":        "org_select",
    "role":                None,
    "user_name":           None,
    "view_level":          None,
    "selected_division":   None,
    "selected_department": None,
    "org_step":            "top",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# 공통 내비게이션 버튼 (화면 0 제외)
# ---------------------------------------------------------------------------
def render_nav_buttons(back_page: str):
    _, col_back, col_home = st.columns([6, 1, 1])
    with col_back:
        if st.button("← 뒤로", key=f"nav_back_{back_page}"):
            st.session_state.current_page = back_page
            st.rerun()
    with col_home:
        if st.button("⌂ 조직선택", key=f"nav_home_{back_page}"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ---------------------------------------------------------------------------
# 화면 0 — 조직 선택
# ---------------------------------------------------------------------------
def render_org_select():
    st.title("IB 영업현황 관리 시스템")
    st.markdown("---")
    step = st.session_state.org_step

    if step == "top":
        st.subheader("이름과 사번을 입력하세요")
        이름 = st.text_input("이름")
        사번 = st.text_input("사번")
        if st.button("로그인", type="primary"):
            if not 이름.strip() or not 사번.strip():
                st.error("이름과 사번을 모두 입력하세요.")
            else:
                info = du.get_user_info(이름.strip(), 사번.strip())
                if info is None:
                    st.error("등록된 사용자가 아닙니다. 관리자에게 문의하세요.")
                else:
                    # 이전 세션 값 초기화
                    for k in ["role", "view_level", "selected_division", "selected_department"]:
                        st.session_state.pop(k, None)
                    st.session_state.user_name = 이름.strip()
                    st.session_state.role = info["role"]
                    if info["role"] == "영업":
                        st.session_state.selected_division   = info["division"]
                        st.session_state.selected_department = info["department"]
                        st.session_state.view_level          = "department"
                        st.session_state.current_page        = "home"
                    else:
                        st.session_state.org_step = "division"
                    st.rerun()

    elif step == "division":
        name = st.session_state.get("user_name", "")
        st.subheader(f"{name}님, 조회할 범위를 선택하세요")
        divisions = list(du.ORG.keys())
        cols = st.columns(len(divisions))
        for col, div in zip(cols, divisions):
            with col:
                if st.button(div, use_container_width=True):
                    st.session_state.selected_division = div
                    st.session_state.view_level = "division"
                    st.session_state.current_page = "home"
                    st.rerun()
        st.markdown("---")
        if st.button("🏢 IB부문 통합 (전체)", use_container_width=True):
            st.session_state.view_level = "all"
            st.session_state.current_page = "home"
            st.rerun()


# ---------------------------------------------------------------------------
# 화면 1 — 홈
# ---------------------------------------------------------------------------
def render_home():
    render_nav_buttons("org_select")
    role = st.session_state.role
    dept = st.session_state.selected_department or ""
    div  = st.session_state.selected_division or ""
    view = st.session_state.view_level
    if view == "all":
        scope = "IB부문 통합"
    elif view == "division":
        scope = f"{div} 본부"
    elif view == "department":
        scope = dept
    else:
        scope = "IB부문 전체"
    st.title(f"IB 영업현황 관리 — {scope}")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📝 신규딜 입력", use_container_width=True,
                     disabled=(role == "관리자")):
            st.session_state.current_page = "new_deal"
            st.rerun()
    with c2:
        if st.button("📋 딜 리스트", use_container_width=True):
            st.session_state.current_page = "deal_list"
            st.rerun()
    with c3:
        if st.button("📈 영업 통계", use_container_width=True):
            st.session_state.current_page = "stats"
            st.rerun()
    with c4:
        if st.button("⚙️ FTP 관리", use_container_width=True,
                     disabled=(role != "관리자")):
            st.session_state.current_page = "ftp_admin"
            st.rerun()

    if role == "관리자":
        st.info("관리자 모드: 신규딜 입력은 비활성화됩니다.")


# ---------------------------------------------------------------------------
# 화면 2 — 신규딜 입력
# ---------------------------------------------------------------------------
def _tk(t_idx: int, field: str) -> str:
    return f"t{t_idx}_{field}"


def _init_tranche(t_idx: int):
    inv_key = _tk(t_idx, "투자유형")
    if inv_key not in st.session_state:
        st.session_state[inv_key] = du.투자유형[0]

    inv = st.session_state[inv_key]
    prod_list = du.PRODUCT_TYPE_BY_INVEST_TYPE.get(inv, du.상품유형)
    prod_key = _tk(t_idx, "상품유형")
    if st.session_state.get(prod_key) not in prod_list:
        st.session_state[prod_key] = prod_list[0]

    prod = st.session_state[prod_key]
    book_list = du.BOOK_TYPE_BY_PRODUCT_TYPE.get(prod, du.리소스Book유형)
    book_key = _tk(t_idx, "리소스Book유형")
    if st.session_state.get(book_key) not in book_list:
        st.session_state[book_key] = book_list[0]

    yield_list = du.YIELD_TYPE_OPTIONS.get(prod, ["표면금리"])
    yield_key = _tk(t_idx, "투자수익률구분")
    if st.session_state.get(yield_key) not in yield_list:
        st.session_state[yield_key] = yield_list[0]

    for field, default in [
        ("당사주선/투자 트랜치", du.당사주선투자트랜치[0]),
        ("당사주선/인수규모", 0.0),
        ("당사투자금액", 0.0),
        ("투자수익률", 0.0),
        ("선취수수료구분", du.선취수수료구분[0]),
        ("선취수수료금액", 0.0),
        ("투자기간만기", 12),
        ("BRR등급", du.BRR등급[0]),
    ]:
        if _tk(t_idx, field) not in st.session_state:
            st.session_state[_tk(t_idx, field)] = default


def render_tranche_section(t_idx: int, label: str, preset_tranche: str = None):
    if preset_tranche:
        st.session_state[_tk(t_idx, "당사주선/투자 트랜치")] = preset_tranche
    _init_tranche(t_idx)

    with st.expander(label, expanded=True):
        c1, c2 = st.columns(2)

        # 투자유형
        with c1:
            inv_key = _tk(t_idx, "투자유형")
            inv_val = st.selectbox(
                "투자유형", du.투자유형,
                index=du.투자유형.index(st.session_state[inv_key])
                      if st.session_state[inv_key] in du.투자유형 else 0,
                key=inv_key,
            )

        # 상품유형 (투자유형 필터)
        prod_options = du.PRODUCT_TYPE_BY_INVEST_TYPE.get(inv_val, du.상품유형)
        prod_key = _tk(t_idx, "상품유형")
        if st.session_state.get(prod_key) not in prod_options:
            st.session_state[prod_key] = prod_options[0]
        with c2:
            prod_val = st.selectbox(
                "상품유형", prod_options,
                index=prod_options.index(st.session_state[prod_key]),
                key=prod_key,
            )

        # 리소스Book유형 (상품유형 필터)
        book_options = du.BOOK_TYPE_BY_PRODUCT_TYPE.get(prod_val, du.리소스Book유형)
        book_key = _tk(t_idx, "리소스Book유형")
        if st.session_state.get(book_key) not in book_options:
            st.session_state[book_key] = book_options[0]

        c3, c4 = st.columns(2)
        with c3:
            st.selectbox(
                "리소스Book유형", book_options,
                index=book_options.index(st.session_state[book_key]),
                key=book_key,
            )
        with c4:
            tranche_key = _tk(t_idx, "당사주선/투자 트랜치")
            cur = st.session_state.get(tranche_key, du.당사주선투자트랜치[0])
            st.selectbox(
                "당사주선/투자 트랜치", du.당사주선투자트랜치,
                index=du.당사주선투자트랜치.index(cur) if cur in du.당사주선투자트랜치 else 0,
                key=tranche_key,
                disabled=(preset_tranche is not None),
            )

        c5, c6 = st.columns(2)
        with c5:
            st.number_input("당사주선/인수규모 (억원)", min_value=0.0, step=10.0,
                            key=_tk(t_idx, "당사주선/인수규모"))
        with c6:
            st.number_input("당사투자금액 (억원)", min_value=0.0, step=10.0,
                            key=_tk(t_idx, "당사투자금액"))

        # 투자수익률구분 (상품유형 필터, 당사투자금액=0이면 비활성)
        yield_options = du.YIELD_TYPE_OPTIONS.get(prod_val, ["표면금리"])
        yield_key = _tk(t_idx, "투자수익률구분")
        if st.session_state.get(yield_key) not in yield_options:
            st.session_state[yield_key] = yield_options[0]

        invest_amt = st.session_state.get(_tk(t_idx, "당사투자금액"), 0.0)
        yield_disabled = (invest_amt == 0.0)

        c7, c8 = st.columns(2)
        with c7:
            st.selectbox(
                "투자수익률구분", yield_options,
                index=yield_options.index(st.session_state[yield_key]),
                key=yield_key,
                disabled=yield_disabled,
            )
        with c8:
            st.number_input("투자수익률 (%)", min_value=0.0, max_value=100.0, step=0.1,
                            key=_tk(t_idx, "투자수익률"),
                            disabled=yield_disabled)

        c9, c10 = st.columns(2)
        with c9:
            fee_key = _tk(t_idx, "선취수수료구분")
            cur_fee = st.session_state.get(fee_key, du.선취수수료구분[0])
            st.selectbox(
                "선취수수료구분", du.선취수수료구분,
                index=du.선취수수료구분.index(cur_fee) if cur_fee in du.선취수수료구분 else 0,
                key=fee_key,
            )
        with c10:
            st.number_input("선취수수료금액 (억원)", min_value=0.0, step=1.0,
                            key=_tk(t_idx, "선취수수료금액"))

        c11, c12 = st.columns(2)
        with c11:
            st.number_input("투자기간만기,셀다운예정기간 (월)", min_value=1, step=1,
                            key=_tk(t_idx, "투자기간만기"))
        with c12:
            brr_key = _tk(t_idx, "BRR등급")
            cur_brr = st.session_state.get(brr_key, du.BRR등급[0])
            st.selectbox(
                "BRR등급", du.BRR등급,
                index=du.BRR등급.index(cur_brr) if cur_brr in du.BRR등급 else 0,
                key=brr_key,
            )


def render_new_deal():
    render_nav_buttons("home")
    st.title("신규딜 입력")
    st.markdown("---")

    st.subheader("딜 공통 정보")
    c1, c2 = st.columns(2)
    with c1:
        딜명 = st.text_input("딜명 *", key="nd_딜명")
    with c2:
        진행단계_val = st.selectbox("진행단계", du.진행단계, key="nd_진행단계")

    상세내용 = st.text_area("상세내용/진행상황", height=100, key="nd_상세내용")

    c3, c4 = st.columns(2)
    with c3:
        투자구조_val = st.selectbox("투자구조", du.투자구조, key="nd_투자구조")
    with c4:
        사업유형_val = st.selectbox("사업유형", du.사업유형, key="nd_사업유형")

    c5, c6 = st.columns(2)
    with c5:
        CIB_val = st.selectbox("CIB여부", du.CIB여부, key="nd_CIB여부")
    with c6:
        모험_val = st.selectbox("모험자본여부", du.모험자본여부, key="nd_모험자본여부")

    c7, c8 = st.columns(2)
    with c7:
        전체딜규모_val = st.number_input("전체딜규모 (억원)", min_value=0.0, step=10.0,
                                        key="nd_전체딜규모")
    with c8:
        기표예정일_val = st.date_input("기표예정일", key="nd_기표예정일")

    st.markdown("---")

    if 투자구조_val == "복합 Deal":
        st.subheader("트랜치별 정보")
        if "nd_selected_tranches" not in st.session_state:
            st.session_state.nd_selected_tranches = [du.당사주선투자트랜치[1], du.당사주선투자트랜치[5]]
        selected_tranches = st.multiselect(
            "트랜치 선택 (2개 이상)",
            du.당사주선투자트랜치,
            key="nd_selected_tranches",
        )
        if len(selected_tranches) < 2:
            st.warning("복합 Deal은 최소 2개 트랜치를 선택해야 합니다.")
        for i, tranche_type in enumerate(selected_tranches, start=1):
            render_tranche_section(i, f"트랜치 {i} — {tranche_type}", preset_tranche=tranche_type)
        tranche_count = len(selected_tranches)
    else:
        st.subheader("투자 정보")
        render_tranche_section(1, "투자 정보")
        tranche_count = 1

    st.markdown("---")

    if st.button("💾 저장", type="primary"):
        if not 딜명.strip():
            st.error("딜명을 입력하세요.")
            return

        ss = st.session_state
        common = {
            "본부": ss.get("selected_division", ""),
            "부서": ss.get("selected_department", ""),
            "딜명": 딜명.strip(),
            "상세내용/진행상황": 상세내용,
            "투자구조": 투자구조_val,
            "사업유형": 사업유형_val,
            "CIB여부": CIB_val,
            "모험자본여부": 모험_val,
            "전체딜규모": 전체딜규모_val,
            "진행단계": 진행단계_val,
            "기표예정일": 기표예정일_val.isoformat() if 기표예정일_val else "",
        }

        tranche_fields = [
            "투자유형", "상품유형", "리소스Book유형", "당사주선/투자 트랜치",
            "당사주선/인수규모", "당사투자금액",
            "투자수익률구분", "투자수익률",
            "선취수수료구분", "선취수수료금액",
            "투자기간만기", "BRR등급",
        ]
        tranches = [{f: ss.get(_tk(i, f), "") for f in tranche_fields}
                    for i in range(1, int(tranche_count) + 1)]

        du.append_deal(du.make_deal_rows(common, tranches))

        # 입력 state 정리
        for i in range(1, int(tranche_count) + 1):
            for f in tranche_fields:
                st.session_state.pop(_tk(i, f), None)
        for k in ["nd_딜명", "nd_상세내용", "nd_tranche_count"]:
            st.session_state.pop(k, None)

        st.success(f"✅ '{딜명.strip()}' 딜이 저장됐습니다.")
        st.session_state.current_page = "deal_list"
        st.rerun()


# ---------------------------------------------------------------------------
# 화면 3 — 딜 리스트
# ---------------------------------------------------------------------------
def render_deal_list():
    render_nav_buttons("home")
    st.title("딜 리스트")

    ss = st.session_state
    df = du.load_deals()
    if df.empty:
        st.info("등록된 딜이 없습니다.")
        return

    df = du.filter_by_view(df, ss)
    if df.empty:
        st.info("조회 가능한 딜이 없습니다.")
        return

    df = du.add_revenue_columns(df)

    # 트랜치 표시 컬럼 (당사주선/투자 트랜치 값 표시)
    df["트랜치"] = df["당사주선/투자 트랜치"].fillna("").apply(lambda x: x.strip() if x.strip() else "-")

    # FTP 적용 유형 및 원가율 컬럼
    def _ftp_info(row):
        book = str(row.get("리소스Book유형") or "")
        if book in du.FTP_EXEMPT_BOOKS:
            return "미적용", "-"
        ftp_book = "종금Book" if book == "종금Book" else "IB Book"
        try:
            m = float(row.get("투자기간만기") or 0)
        except (TypeError, ValueError):
            return ftp_book + " FTP", "-"
        if m <= 0:
            return ftp_book + " FTP", "-"
        rate = du.get_ftp_rate(ftp_book, m)
        return ftp_book + " FTP", (f"{rate:.2f}" if rate is not None else "-")

    ftp_cols = [_ftp_info(row) for _, row in df.iterrows()]
    df["FTP유형"] = [x[0] for x in ftp_cols]
    df["FTP원가율"] = [x[1] for x in ftp_cols]

    selected_stages = st.multiselect(
        "진행단계 필터 (미선택 시 전체 표시)", du.진행단계, key="dl_stage_filter"
    )
    if selected_stages:
        df = df[df["진행단계"].isin(selected_stages)]

    df = df.sort_values(
        ["최초작성일", "deal_id", "트랜치번호"], ascending=[False, True, True]
    ).reset_index(drop=True)

    if "기표예정일" in df.columns:
        df["기표예정일"] = pd.to_datetime(df["기표예정일"], errors="coerce").dt.date

    for col in ["순영업수익", "Carry손익", "수수료수익", "이자수익", "자본원가"]:
        if col in df.columns:
            df[col] = df[col].map(
                lambda x: f"{x:.2f}" if pd.notna(x) and str(x) != "nan" else "-"
            )

    column_order = [c for c in [
        "최초작성일", "입력일", "부서", "진행단계", "딜명", "투자구조", "트랜치",
        "사업유형", "상품유형", "투자유형",
        "전체딜규모", "당사주선/투자 트랜치", "당사주선/인수규모", "리소스Book유형", "당사투자금액", "투자기간만기",
        "투자수익률구분", "투자수익률", "FTP유형", "FTP원가율", "Carry손익",
        "선취수수료구분", "선취수수료금액",
        "순영업수익",
        "BRR등급", "CIB여부", "모험자본여부", "기표예정일",
        "상세내용/진행상황",
    ] if c in df.columns]

    col_config = {
        "deal_id":              None,
        "부문":                 None,
        "입력일":               st.column_config.TextColumn("마지막수정일", disabled=True),
        "수수료수익":           None,
        "투자구조":             st.column_config.SelectboxColumn(options=du.투자구조),
        "사업유형":             st.column_config.SelectboxColumn(options=du.사업유형),
        "상품유형":             st.column_config.SelectboxColumn(options=du.상품유형),
        "투자유형":             st.column_config.SelectboxColumn(options=du.투자유형),
        "리소스Book유형":       st.column_config.SelectboxColumn(options=du.리소스Book유형),
        "당사주선/투자 트랜치": st.column_config.SelectboxColumn(options=du.당사주선투자트랜치),
        "CIB여부":             st.column_config.SelectboxColumn(options=du.CIB여부),
        "모험자본여부":         st.column_config.SelectboxColumn(options=du.모험자본여부),
        "BRR등급":             st.column_config.SelectboxColumn(options=du.BRR등급),
        "진행단계":             st.column_config.SelectboxColumn(options=du.진행단계),
        "선취수수료구분":       st.column_config.SelectboxColumn(options=du.선취수수료구분),
        "전체딜규모":           st.column_config.NumberColumn("전체딜규모(억원)", format="%.1f"),
        "당사주선/인수규모":    st.column_config.NumberColumn("당사주선/인수규모(억원)", format="%.1f"),
        "당사투자금액":         st.column_config.NumberColumn("당사투자금액(억원)", format="%.1f"),
        "투자수익률":           st.column_config.NumberColumn("투자수익률(%)", format="%.2f"),
        "선취수수료금액":       st.column_config.NumberColumn("선취수수료금액(억원)", format="%.2f"),
        "투자기간만기":         st.column_config.NumberColumn("투자기간만기,셀다운예정기간(월)", format="%d"),
        "트랜치번호":           None,
        "트랜치":               st.column_config.TextColumn("트랜치#", disabled=True),
        "FTP유형":              st.column_config.TextColumn("FTP유형", disabled=True),
        "FTP원가율":            st.column_config.TextColumn("FTP원가율", disabled=True),
        "기표예정일":           st.column_config.DateColumn("기표예정일"),
        "순영업수익":           st.column_config.TextColumn("순영업수익(억원)", disabled=True),
        "Carry손익":            st.column_config.TextColumn("Carry손익(억원)", disabled=True),
        "이자수익":             None,
        "자본원가":             None,
        "부서":                 st.column_config.TextColumn("부서", disabled=True),
        "최초작성일":           st.column_config.TextColumn("최초작성일", disabled=True),
    }

    edited = st.data_editor(
        df,
        column_order=column_order,
        column_config=col_config,
        use_container_width=True,
        num_rows="fixed",
        key="dl_editor",
    )

    if st.button("💾 변경사항 저장", type="primary"):
        save_df = edited.drop(
            columns=["순영업수익", "이자수익", "자본원가", "Carry손익", "수수료수익", "트랜치", "FTP유형", "FTP원가율"], errors="ignore"
        )

        # 변경된 행만 마지막수정일(입력일) 갱신
        today = datetime.date.today().isoformat()
        orig_full = du.load_deals()
        skip_cols = {"deal_id", "트랜치번호", "최초작성일", "입력일"}
        compare_cols = [c for c in save_df.columns if c not in skip_cols]
        try:
            orig_idx = orig_full.set_index(["deal_id", "트랜치번호"])
            for i in save_df.index:
                did = str(save_df.at[i, "deal_id"])
                tno = save_df.at[i, "트랜치번호"]
                try:
                    orig_row = orig_idx.loc[(did, tno)]
                    changed = any(
                        str(save_df.at[i, c]) != str(orig_row.get(c, ""))
                        for c in compare_cols if c in orig_idx.columns
                    )
                except KeyError:
                    changed = True
                if changed:
                    save_df.at[i, "입력일"] = today
        except Exception:
            pass

        du.update_deals(save_df, ss)
        st.success("변경사항이 저장됐습니다.")
        st.rerun()


# ---------------------------------------------------------------------------
# 화면 4 — 영업 통계
# ---------------------------------------------------------------------------
def _hbar(series: "pd.Series", x_title: str, height: int = 260,
          x_max: float = None, integer_axis: bool = False):
    """수평 막대 차트 (Altair). series.index = 카테고리, series.values = 수치."""
    import altair as alt
    df_plot = series.reset_index()
    df_plot.columns = ["category", "value"]
    scale = alt.Scale(domainMin=0) if x_max is None else alt.Scale(domainMin=0, domainMax=x_max)
    axis  = alt.Axis(format="d", tickMinStep=1) if integer_axis else alt.Axis(format=".2f")
    tip_fmt = "d" if integer_axis else ".2f"
    return (
        alt.Chart(df_plot)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", scale=scale, axis=axis, title=x_title),
            y=alt.Y("category:N", sort=None, title=""),
            tooltip=["category:N", alt.Tooltip("value:Q", format=tip_fmt)],
        )
        .properties(height=height)
    )


def render_stats():
    render_nav_buttons("home")

    ss = st.session_state
    _dept = ss.get("selected_department") or ""
    _div  = ss.get("selected_division") or ""
    if ss.get("view_level") == "all":
        _scope = "IB부문 통합"
    elif _dept:
        _scope = _dept
    elif _div:
        _scope = _div
    else:
        _scope = "IB부문 전체"
    st.title(f"{_scope} 영업통계")
    df = du.load_deals()
    if df.empty:
        st.info("등록된 딜이 없습니다.")
        return

    df = du.filter_by_view(df, ss)
    if df.empty:
        st.info("조회 가능한 딜이 없습니다.")
        return

    df = du.add_revenue_columns(df)

    unique_deals  = df["deal_id"].nunique()
    total_arrange = pd.to_numeric(df["당사주선/인수규모"], errors="coerce").sum()
    total_invest  = pd.to_numeric(df["당사투자금액"], errors="coerce").sum()
    total_fee     = pd.to_numeric(df["선취수수료금액"], errors="coerce").sum()
    total_nr      = pd.to_numeric(df["순영업수익"], errors="coerce").sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("전체 딜 수",       f"{unique_deals:,}건")
    c2.metric("당사 총 주선금액", f"{total_arrange:,.0f}억원")
    c3.metric("당사 총 투자금액", f"{total_invest:,.0f}억원")
    c4.metric("선취수수료 합계",  f"{total_fee:,.1f}억원")
    c5.metric("순영업수익 합계",  f"{total_nr:,.1f}억원" if pd.notna(total_nr) else "-")

    st.markdown("---")

    df_first = (df.sort_values("트랜치번호")
                  .groupby("deal_id").first().reset_index())

    # ── 행1: 진행단계별 딜 수 / 사업유형별 딜 수 ──
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("진행단계별 딜 수")
        stage_counts = (df_first.groupby("진행단계")["deal_id"]
                                .count()
                                .reindex(du.진행단계, fill_value=0))
        st.altair_chart(_hbar(stage_counts, "딜 수", x_max=10, integer_axis=True), use_container_width=True)

    with col_r:
        st.subheader("사업유형별 딜 수")
        biz_counts = (df_first.groupby("사업유형")["deal_id"]
                               .count()
                               .reindex(du.사업유형, fill_value=0))
        st.altair_chart(_hbar(biz_counts, "딜 수", x_max=10, integer_axis=True), use_container_width=True)

    # ── 행2: 투자유형별 당사투자금액 합계 ──
    col_l2, _ = st.columns(2)
    with col_l2:
        st.subheader("투자유형별 당사투자금액 합계 (억원)")
        inv_sum = (pd.to_numeric(df["당사투자금액"], errors="coerce")
                     .groupby(df["투자유형"]).sum()
                     .reindex(du.투자유형, fill_value=0))
        st.altair_chart(_hbar(inv_sum, "억원"), use_container_width=True)

    # ── 본부별 통계: 부서별 차트 (view_level = division 일 때만) ──
    if ss.get("view_level") == "division":
        st.markdown("---")
        st.subheader(f"{ss.get('selected_division', '')} 본부 — 부서별 현황")

        dept_list = du.ORG.get(ss.get("selected_division", ""), [])

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**부서별 순영업수익 (억원)**")
            dept_nr = (pd.to_numeric(df["순영업수익"], errors="coerce")
                         .groupby(df["부서"]).sum()
                         .reindex(dept_list, fill_value=0))
            st.altair_chart(_hbar(dept_nr, "억원"), use_container_width=True)

        with col_d2:
            st.markdown("**부서별 당사주선/인수규모 (억원)**")
            dept_size = (pd.to_numeric(df["당사주선/인수규모"], errors="coerce")
                           .groupby(df["부서"]).sum()
                           .reindex(dept_list, fill_value=0))
            st.altair_chart(_hbar(dept_size, "억원"), use_container_width=True)

    st.markdown("---")
    st.subheader("진행단계별 요약")
    summary = df.groupby("진행단계").agg(
        딜수=("deal_id", "nunique"),
        주선인수규모합계=("당사주선/인수규모", "sum"),
        당사투자금액합계=("당사투자금액", "sum"),
        선취수수료합계=("선취수수료금액", "sum"),
        순영업수익합계=("순영업수익", "sum"),
    ).reindex(du.진행단계).fillna(0)
    _summary_col_config = {
        "딜수":             st.column_config.NumberColumn("딜수", format="%d"),
        "주선인수규모합계":  st.column_config.NumberColumn("주선/인수규모합계(억원)", format="%,.0f"),
        "당사투자금액합계":  st.column_config.NumberColumn("당사투자금액합계(억원)", format="%,.0f"),
        "선취수수료합계":    st.column_config.NumberColumn("선취수수료합계(억원)", format="%.1f"),
        "순영업수익합계":    st.column_config.NumberColumn("순영업수익합계(억원)", format="%.1f"),
    }
    st.dataframe(summary, use_container_width=True, column_config=_summary_col_config)

    if ss.get("view_level") == "division":
        st.markdown("---")
        st.subheader("부서별 요약")
        dept_list = du.ORG.get(ss.get("selected_division", ""), [])
        dept_summary = df.groupby("부서").agg(
            딜수=("deal_id", "nunique"),
            주선인수규모합계=("당사주선/인수규모", "sum"),
            당사투자금액합계=("당사투자금액", "sum"),
            선취수수료합계=("선취수수료금액", "sum"),
            순영업수익합계=("순영업수익", "sum"),
        ).reindex(dept_list).fillna(0)
        st.dataframe(dept_summary, use_container_width=True, column_config=_summary_col_config)

    if ss.get("view_level") == "all":
        st.markdown("---")
        st.subheader("본부별 요약")
        div_list = list(du.ORG.keys())
        div_summary = df.groupby("본부").agg(
            딜수=("deal_id", "nunique"),
            주선인수규모합계=("당사주선/인수규모", "sum"),
            당사투자금액합계=("당사투자금액", "sum"),
            선취수수료합계=("선취수수료금액", "sum"),
            순영업수익합계=("순영업수익", "sum"),
        ).reindex(div_list).fillna(0)
        st.dataframe(div_summary, use_container_width=True, column_config=_summary_col_config)


# ---------------------------------------------------------------------------
# 화면 5 — FTP 관리
# ---------------------------------------------------------------------------
def render_ftp_admin():
    if st.session_state.role != "관리자":
        st.error("관리자만 접근 가능합니다.")
        return

    render_nav_buttons("home")
    st.title("FTP 관리")

    tab1, tab2 = st.tabs(["종금Book FTP", "IB Book FTP"])

    for tab, book_type in zip([tab1, tab2], ["종금Book", "IB Book"]):
        with tab:
            latest = du.get_latest_ftp(book_type)
            if latest:
                st.subheader("현재 적용 FTP")
                st.dataframe(
                    pd.DataFrame([latest], index=["금리(%)"],
                                 columns=du.FTP_TENOR_KEYS),
                    use_container_width=True,
                )
            else:
                st.info("등록된 FTP 데이터가 없습니다.")

            st.markdown("---")
            st.subheader("신규 FTP 입력")

            with st.form(f"ftp_form_{book_type}"):
                기준일 = st.date_input("기준 날짜", value=datetime.date.today())
                st.markdown("**만기별 금리 (%) 입력**")
                c1, c2, c3 = st.columns(3)
                cycle = [c1, c2, c3, c1, c2, c3, c1, c2, c3]
                tenor_inputs = {}
                for col, tenor in zip(cycle, du.FTP_TENOR_KEYS):
                    default_val = float(latest.get(tenor, 3.0)) if latest else 3.0
                    tenor_inputs[tenor] = col.number_input(
                        tenor, min_value=0.0, max_value=30.0,
                        value=default_val, step=0.01, format="%.2f",
                        key=f"ftp_{book_type}_{tenor}",
                    )
                submitted = st.form_submit_button("💾 저장")

            if submitted:
                du.append_ftp(기준일.isoformat(), book_type, tenor_inputs)
                st.success(f"{book_type} FTP ({기준일}) 저장됐습니다.")
                st.rerun()

            st.markdown("---")
            ftp_df = du.load_ftp()
            hist = ftp_df[ftp_df["book_type"] == book_type].sort_values(
                "날짜", ascending=False
            )
            if not hist.empty:
                st.subheader("입력 이력")
                st.dataframe(
                    hist[["날짜"] + du.FTP_TENOR_KEYS].reset_index(drop=True),
                    use_container_width=True,
                )


# ---------------------------------------------------------------------------
# 라우터
# ---------------------------------------------------------------------------
PAGE_MAP = {
    "org_select": render_org_select,
    "home":       render_home,
    "new_deal":   render_new_deal,
    "deal_list":  render_deal_list,
    "stats":      render_stats,
    "ftp_admin":  render_ftp_admin,
}

PAGE_MAP.get(st.session_state.get("current_page", "org_select"), render_org_select)()
