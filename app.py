import streamlit as st

st.title("🚀 나의 첫 웹 서비스")
st.write("반갑습니다! 이 사이트는 Streamlit으로 배포되었습니다.")

name = st.text_input("당신의 이름은 무엇인가요?")
if name:
    st.write(f"{name}님, 웹 배포 성공을 축하드립니다!")r