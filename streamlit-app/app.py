"""AI-Pilot 교육용 Streamlit 데모 앱."""
import streamlit as st

st.set_page_config(page_title="AI-Pilot Streamlit Demo", page_icon="🤖", layout="wide")

st.title("🤖 AI-Pilot Streamlit Demo")
st.caption("Claude Code 기반 PoC 교육 환경")

with st.sidebar:
    st.header("설정")
    name = st.text_input("이름", value="교육생")

st.write(f"안녕하세요, **{name}**님!")
st.info("이 파일을 Claude Code로 수정하며 실습을 진행하세요.")

if st.button("샘플 데이터 보기"):
    import pandas as pd
    df = pd.DataFrame({"x": range(10), "y": [i * i for i in range(10)]})
    st.dataframe(df, use_container_width=True)
    st.line_chart(df.set_index("x"))
