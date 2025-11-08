import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS  # TTS 함수 내에서만 사용 (전역 변수로 사용하지 않음)
import os
import io

# --- [1. 필수 설정] ---------------------------------------------------------
# 👇 6번째 줄: Gemini API 키를 넣어주세요!
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')
# ---------------------------------------------------------------------------

# === 세션 상태 및 도우미 함수 ===
# 세션 상태 초기화 (메인 로직보다 먼저 실행되어야 함)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
    
# 🔊 AI가 말하게 하는 함수 (모바일 호환성 최적화)
def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except Exception:
        st.warning("🔊 (소리 재생이 원활하지 않을 수 있습니다. 재생 버튼을 눌러보세요.)")

# 📞 민원 버튼 함수
def show_minwon_button():
    with st.expander("📞 그래도 궁금한 게 남으셨나요?"):
        st.write("아래 버튼을 누르면 대전시 상담원(120)에게 바로 전화 연결됩니다.")
        st.link_button("👩‍💼 상담원 전화 연결 (120)", "tel:120", use_container_width=True)

# === 화면(UI) 구성 ===
st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")
st.title("🚃 대전 Easy-Tram")
st.subheader("어르신, 궁금한 것을 찍어보세요")

uploaded_file = st.file_uploader("사진 찍기", type=["jpg", "png", "jpeg"])

# 파일 업로드 처리 및 이미지 저장
if uploaded_file:
    # 🚨 파일이 새로 업로드되면, 바이트 형태로 저장하여 이미지 변수 에러를 방지합니다.
    if uploaded_file.getvalue() != st.session_state.uploaded_image_bytes:
        st.session_state.chat_history = []
        st.session_state.uploaded_image_bytes = uploaded_file.getvalue()

    # 저장된 바이트 데이터에서 PIL Image 객체를 생성합니다.
    image = Image.open(io.BytesIO(st.session_state.uploaded_image_bytes))
    st.image(image, caption='찍은 사진', use_column_width=True)

    # --- [1차 분석] ---
    if not st.session_state.chat_history:
        with st.spinner('AI 비서가 사진을 보고 있습니다...'):
            try:
                prompt = """
                당신은 친절하고 예의 바른 '교통 안내 비서'입니다.
                사진을 보고 핵심 내용을 쉬운 표준어 존댓말로 3~5문장으로 설명해주세요.
                '어르신,' 하고 부르며 시작하고, (절대로 영어로 대답하지 마세요.)
                """
                
                response = model.generate_content([prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun() # 새로고침해서 답변 보여주기

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

    # 대화 기록 표시
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "ai":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message['text'])
                if i == len(st.session_state.chat_history) - 1:
                     speak(message['text'])
                     show_minwon_button()
        else:
             with st.chat_message("user", avatar="👤"):
                st.write(message['text'])

    # --- [추가 질문 기능] ---
    # *st.chat_input을 사용하면 Enter 키를 눌러도 질문이 전송됩니다.*
    user_input = st.chat_input("궁금한 점을 적거나, 키보드의 마이크 버튼을 눌러 말씀해보세요")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner('답변을 생각 중입니다...'):
            try:
                # 이전 대화와 현재 이미지를 기반으로 답변 생성
                follow_up_prompt = f"어르신 질문: '{user_input}'\n이전 대화를 참고하여 쉽고 친절하게 답변해주세요. (한국어만 사용)"
                
                # 이미지 객체를 다시 생성해야 함 (Streamlit의 특성)
                current_image = Image.open(io.BytesIO(st.session_state.uploaded_image_bytes))
                
                response = model.generate_content([follow_up_prompt, current_image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")