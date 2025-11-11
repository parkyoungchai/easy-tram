import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import time
from gtts import gTTS
import io
import os
import pandas as pd
import numpy as np
from datetime import datetime

# --- [🔑 필수 설정: API 키 4개 입력!] ---
GEMINI_API_KEY = "AIzaSy..."      # 👇 Gemini 키
WEATHER_API_KEY = "여기에_날씨_키"  # 👇 날씨 키
TASHU_API_KEY = "여기에_타슈_키"    # 👇 타슈 키
SHEETDB_URL = "https://sheetdb.io/api/v1/YOUR_API_KEY" # 👇 SheetDB URL

# --- [AI 설정] ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

# === 화면 설정 ===
st.set_page_config(page_title="대전 이지(Daejeon-Easy)", page_icon="🚃", layout="centered")

# 🔥 [CSS 디자인] 🔥
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    div.stButton > button {
        width: 100%; border-radius: 12px !important; height: 3.5em !important; font-weight: bold !important;
        border: 1px solid #ddd !important; transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #00C73C !important; border-color: #00C73C !important; color: white !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #009e2f !important; border-color: #009e2f !important;
    }
    div.stButton > button:has(div p:contains("방문객")) { background-color: #007BFF !important; color: white !important; }
    div.stButton > button:has(div p:contains("어르신")) { background-color: #FF4B4B !important; color: white !important; font-size: 1.3rem !important; }
    div.stButton > button:has(div p:contains("불편해요")) { background-color: #FF4B4B !important; color: white !important; }
    div.stButton > button:has(div p:contains("산책하고")) { background-color: #00C73C !important; color: white !important; }
    /* 🚨 [신규] 축제(보라)/명소(주황) 버튼 색상 */
    div.stButton > button:has(div p:contains("축제")) { background-color: #8A2BE2 !important; color: white !important; }
    div.stButton > button:has(div p:contains("명소")) { background-color: #FF8C00 !important; color: white !important; }
    
    .stTextInput > div > div > input { border-radius: 12px; }
    .stSelectbox div[data-testid="stSelectboxInline"] { max-width: 150px; font-size: 0.9em; }
    </style>
""", unsafe_allow_html=True)

# --- [다국어 텍스트 & 스마트 프롬프트] ---
TEXTS = {
    "ko": {
        "welcome": "반갑습니다! 어떤 도움이 필요하신가요?", "feedback_title": "💬 피드백 및 건의사항 보내기", "feedback_placeholder": "더 좋은 서비스를 위해 의견을 남겨주세요!", "feedback_button": "의견 보내기", "feedback_success": "✅ 소중한 의견이 안전하게 저장되었습니다!", "weather_prefix": "🌤️ 현재 대전 날씨:",
        "visitor_button": "🧳 대전 방문객", "senior_button": "👴 어르신 도우미",
        "tashu_button": "🚲 내 주변 '타슈' 찾기", "tashu_loading": "🚲 타슈 위치를 찾는 중...", "tashu_success": "✅ 실시간 타슈 {count}곳을 찾았습니다!", "tashu_expander": "📋 대여소별 잔여 대수 보기", "tashu_station_col": "대여소명", "tashu_bikes_col": "잔여대수", "tashu_mock_warning": "⚠️ 현재 '시뮬레이션 데이터'를 보여줍니다.",
        "festival_button": "🎉 대전 축제 보기", "festival_title": "🎉 대전시 추천 축제 정보", "festival_body": "대전은 1년 내내 즐거운 축제가 가득합니다!\n- **대전 0시 축제 (8월):** 대전역~중앙로 일대\n- **대전 빵 축제 (5월/10월):** 서대전공원 근처\n- **유성온천 문화축제 (5월):** 유성온천역 근처\n- **대전 사이언스 페스티벌 (10월):** 엑스포과학공원",
        "places_button": "🏞️ 대전 명소 추천", "places_title": "🏞️ 대전 추천 명소 TOP 5", "places_body": "AI 비서에게 사진이나 글로 물어보면 자세한 코스를 알려드려요!\n- **한밭수목원:** 도심 속 최대 수목원\n- **엑스포과학공원:** 한빛탑과 음악분수\n- **성심당:** 대전의 자부심, 빵지순례 필수!\n- **소제동 카페거리:** 감성적인 데이트 코스\n- **유성온천 족욕장:** 여행의 피로를 푸는 곳",
        "back_to_home": "⬅️ 첫 화면", "visitor_title": "🧳 대전 여행 가이드", "senior_title": "👴 어르신 교통 비서",
        "photo_uploader": "AI 비서에게 사진을 찍어보세요", "chat_input_placeholder": "궁금한 점을 입력하세요 (키보드 마이크 사용 가능)", "call_center_expander": "📞 상담원 연결이 필요하신가요?", "call_center_button": "👩‍💼 120 콜센터 전화하기", "ai_error": "🚨 에러 발생:", "analyzing": "분석 중...", "thinking": "생각 중...", "ai_explain_image": "이 사진을 보고 핵심 내용을 3문장으로 아주 쉽게 설명해주세요.", "ai_chat_reply": "친절하게 답변해주세요.",
        "senior_select_title": "어떤 도움이 필요하신가요?", "senior_select_info": "어르신의 상황에 꼭 맞는 경로를 추천해 드릴게요!", "senior_license_return_info": "💡 **대전시 꿀팁!** 만 65세 이상 운전면허를 반납하시면 10만 원 교통카드를 드린대요!",
        "senior_impaired_button": "🚶‍♂️ 몸이 불편해요 (계단, 언덕 피하기)", "senior_active_button": "🌳 걷기/산책하고 싶어요 (경치 좋은 길)",
        "senior_impaired_title": "👴 어르신 교통 비서 (편한 길)", "senior_active_title": "👴 어르신 산책 비서 (좋은 길)",
        "visitor_prompt": "당신은 '대전 최고의 여행 코스 플래너'입니다. [중요] 단순 길 안내가 아닌, '성심당 → 중앙시장 → 한밭수목원'처럼 **사람들이 선호하는 '여행 코스'**를 엮어서 제안해주세요. 트램+타슈+버스를 엮는 '환승 경로'도 좋습니다. '0시 축제', '빵 축제' 등 축제 정보도 꼭 함께 알려주세요.",
        "senior_impaired_prompt": "당신은 어르신을 위한 '교통 전문 비서'입니다. [매우 중요 원칙] 1. '최단 거리'보다는 걷기 편한 **'평지 길'**을 우선으로 추천해주세요. 2. **지하철**은 계단이 많아 불편하실 수 있으니, **'혹시 무릎이 불편하시다면'** 버스나 트램, 타슈를 이용하는 다른 방법도 있다고 **선택지를 함께 제안**해주세요.",
        "senior_active_prompt": "당신은 어르신을 위한 '웰빙 산책 비서'입니다. [매우 중요 원칙] 1. 사용자는 걷기를 좋아하십니다. 2. '최단 거리'보다는 조금 돌아가더라도 **'공원길, 하천변, 둘레길, 꽃길'** 등 걷기 좋은 **'산책 코스'** 위주로 추천해주세요. 3. 현재 날씨를 꼭 참고해서 오늘처럼 날씨 좋은 날은 천천히 걸어보시는 것도 좋겠네요 처럼 감성적인 추천을 해주세요. (이모티콘 절대 금지)"
    },
    # (다른 언어는 공간상 생략)
}

# --- [함수 모음] ---
def get_daejeon_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=36.35&lon=127.38&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url, timeout=3).json()
        if response.get("weather"):
            st.session_state.current_weather_text = f"{response['weather'][0]['description']}, {round(response['main']['temp'], 1)}℃"
            return st.session_state.current_weather_text
        return ""
    except: 
        st.session_state.current_weather_text = "날씨 정보 없음"
        return ""

def speak(text, lang='ko'):
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except: pass

def show_minwon_button(texts):
    with st.expander(texts["call_center_expander"]):
        st.link_button(texts["call_center_button"], "tel:120", use_container_width=True)

def ask_ai_with_retry(content, retries=3):
    last_error = None
    for _ in range(retries):
        try: return model.generate_content(content)
        except Exception as e:
            last_error = e
            time.sleep(1)
    raise last_error

def get_mock_tashu_data():
    data = {'lat': [36.3504, 36.3587, 36.3325, 36.3615, 36.3284], 'lon': [127.3845, 127.3848, 127.4342, 127.3546, 127.4213], 'station': ['(예시)시청', '(예시)정부청사', '(예시)대전역', '(예시)유성온천', '(예시)중앙로'], 'bikes': np.random.randint(3, 15, 5)}
    return pd.DataFrame(data)

def get_real_tashu_data():
    try:
        url = f"http://apis.data.go.kr/6300000/Tashu/getStationList?serviceKey={TASHU_API_KEY}&pageNo=1&numOfRows=500&type=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                df = pd.DataFrame(items)
                df = df.rename(columns={'Y_POS': 'lat', 'X_POS': 'lon', 'STATION_NAME': 'station', 'PARKING_COUNT': 'bikes'})
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                return df.dropna(subset=['lat', 'lon'])
    except: pass
    return get_mock_tashu_data()

def save_to_google_sheet(feedback_text):
    try:
        requests.post(SHEETDB_URL, json={"data": {"날짜시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "내용": feedback_text}})
        return True
    except: return False

# --- [초기화] ---
if "mode" not in st.session_state: st.session_state.mode = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None
if "show_tashu" not in st.session_state: st.session_state.show_tashu = False
if "lang" not in st.session_state: st.session_state.lang = "ko"
if "current_weather_text" not in st.session_state: st.session_state.current_weather_text = "날씨 정보 없음"
if "show_festival" not in st.session_state: st.session_state.show_festival = False
if "show_places" not in st.session_state: st.session_state.show_places = False # 🚨 명소 탭 상태

t = TEXTS.get(st.session_state.lang, TEXTS.get("ko"))

# =========================================
# [화면 1] 모드 선택
# =========================================
if st.session_state.mode is None:
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1: st.title("대전 이지 (Daejeon-Easy)")
    with c2:
        if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", use_container_width=True)
    with c3:
        if os.path.exists("한화이글스.jpg"): st.image("한화이글스.jpg", use_container_width=True)
    with c4:
        if os.path.exists("성심당.jpg"): st.image("성심당.jpg", use_container_width=True)

    with st.expander(t["feedback_title"]):
        feedback = st.text_area(t["feedback_placeholder"], height=100)
        if st.button(t["feedback_button"]):
            if feedback:
                save_to_google_sheet(feedback)
                st.success(t["feedback_success"])
                time.sleep(1)
                st.rerun()

    c_sub, c_lang = st.columns([4, 1])
    with c_sub: st.subheader(t["welcome"])
    with c_lang:
        selected_lang_name = st.selectbox("", ["한국어", "English", "日本語", "中文", "Tiếng Việt"], index=0, label_visibility="collapsed")
        st.session_state.lang = {"한국어": "ko", "English": "en", "日本語": "ja", "中文": "zh", "Tiếng Việt": "vi"}.get(selected_lang_name, "ko")

    weather = get_daejeon_weather()
    if weather: st.info(f"{t['weather_prefix']} **{weather}**")
    st.write("---")
    
    st.markdown("##### **친절한 설명 (사진/음성 질문)**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["visitor_button"], use_container_width=True):
            st.session_state.mode = "visitor"
            st.rerun()
    with c2:
        if st.button(t["senior_button"], use_container_width=True):
            st.session_state.mode = "senior_select"
            st.rerun()
    
    st.write("---")
    st.markdown("##### **지도 및 축제 정보**")
    
    # 🚨 [수정] 타슈와 축제 버튼을 나란히 배치
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["tashu_button"], use_container_width=True, type="primary"):
            st.session_state.show_tashu = not st.session_state.show_tashu
            st.session_state.show_festival = False
    with c2:
        if st.button(t["festival_button"], use_container_width=True):
            st.session_state.show_festival = not st.session_state.show_festival
            st.session_state.show_tashu = False

    if st.session_state.show_tashu:
        with st.spinner(t["tashu_loading"]):
            tashu_df = get_real_tashu_data()
        if '(예시)' in tashu_df['station'].iloc[0]:
             st.warning(t["tashu_mock_warning"])
        else:
             st.success(t["tashu_success"].format(count=len(tashu_df)))
        tashu_df['color'] = '#00C73C'
        st.map(tashu_df, latitude='lat', longitude='lon', size=40, color='color')
        with st.expander(t["tashu_expander"]):
             st.dataframe(tashu_df[['station', 'bikes']].rename(columns={'station':t["tashu_station_col"], 'bikes':t["tashu_bikes_col"]}), hide_index=True, use_container_width=True)
    
    if st.session_state.show_festival:
        st.success(f"🎉 {t['festival_title']}")
        st.markdown(t["festival_body"])

# =========================================
# [신규 화면] 어르신 상세 모드 선택
# =========================================
elif st.session_state.mode == "senior_select":
    if st.button("⬅️ " + t["back_to_home"]):
        st.session_state.mode = None
        st.rerun()
    st.title("👴 " + t["senior_button"].split("\n")[0])
    st.subheader(t["senior_select_title"])
    st.info(t["senior_license_return_info"])
    st.write("")
    if st.button(t["senior_impaired_button"], use_container_width=True):
        st.session_state.mode = "senior_impaired"
        st.rerun()
    st.write("")
    if st.button(t["senior_active_button"], use_container_width=True, type="primary"):
        st.session_state.mode = "senior_active"
        st.rerun()

# =========================================
# [화면 3] 메인 기능
# =========================================
else:
    if st.session_state.mode in ["senior_impaired", "senior_active"]:
        st.markdown("""<style> p, div, button, input { font-size: 1.3rem !important; } </style>""", unsafe_allow_html=True)

    if st.button(t["back_to_home"]):
        st.session_state.mode = None
        st.session_state.show_tashu = False
        st.session_state.chat_history = []
        st.rerun()

    # 🚨 [핵심 수정] 방문객 모드에 탭 추가!
    if st.session_state.mode == "visitor":
        st.title(t["visitor_title"])
        system_prompt = t["visitor_prompt"]
        
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t["festival_button"], use_container_width=True):
                st.session_state.show_festival = not st.session_state.show_festival
                st.session_state.show_places = False
        with c2:
            if st.button(t["places_button"], use_container_width=True):
                st.session_state.show_places = not st.session_state.show_places
                st.session_state.show_festival = False

        if st.session_state.show_festival:
            st.success(f"🎉 {t['festival_title']}")
            st.markdown(t["festival_body"])
        
        if st.session_state.show_places:
            st.success(f"🏞️ {t['places_title']}")
            st.markdown(t["places_body"])
        st.write("---")
        
    elif st.session_state.mode == "senior_impaired":
        c1, c2 = st.columns([3, 1])
        with c1: st.title(t["senior_impaired_title"])
        with c2:
             if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", width=80)
        system_prompt = t["senior_impaired_prompt"]
    else: # "senior_active"
        c1, c2 = st.columns([3, 1])
        with c1: st.title(t["senior_active_title"])
        with c2:
             if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", width=80)
        system_prompt = t["senior_active_prompt"]

    uploaded_file = st.file_uploader(t["photo_uploader"], type=["jpg", "png", "jpeg"])
    if uploaded_file:
        if st.session_state.uploaded_image != uploaded_file:
            st.session_state.chat_history = []
            st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption=t.get("photo_caption", "사진"), use_column_width=True)
        if not st.session_state.chat_history:
            with st.spinner(t["analyzing"]):
                try:
                    prompt = f"{system_prompt}\n{t['ai_explain_image']}"
                    response = ask_ai_with_retry([prompt, image])
                    st.session_state.chat_history.append({"role": "ai", "text": response.text})
                    st.rerun()
                except Exception as e: st.error(f"{t['ai_error']} {e}")

    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if message["role"] == "ai" else "user"
        avatar = "🤖"
        if st.session_state.mode.startswith("senior_") and role == "assistant":
             if os.path.exists("꿈돌이.jpg"): avatar = "꿈돌이.jpg"
             else: avatar = "🟡"
        with st.chat_message(role, avatar=avatar):
            st.write(message['text'])
            if role == "assistant" and i == len(st.session_state.chat_history) - 1:
                speak(message['text'], lang=st.session_state.lang)
                if st.session_state.mode.startswith("senior_"): show_minwon_button(t)

    user_input = st.chat_input(t["chat_input_placeholder"])
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner(t["thinking"]):
            try:
                history = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-3:]])
                prompt = f"{system_prompt}\n[현재 날씨: {st.session_state.current_weather_text}]\n[이전 대화]{history}\n[새 질문]{user_input}\n{t['ai_chat_reply']}"
                if 'image' in locals() and image: response = ask_ai_with_retry([prompt, image])
                else: response = ask_ai_with_retry(prompt)
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e: st.error(f"{t['ai_error']} {e}")