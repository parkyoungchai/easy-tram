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
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"      # 👇 Gemini 키
WEATHER_API_KEY = "49271f92ea332122245325408c2ca765"  # 👇 날씨 키
TASHU_API_KEY = "apj2d20me6jch7sl"    # 👇 타슈 키
SHEETDB_URL = "https://sheetdb.io/api/v1/YOUR_API_KEY" # 👇 SheetDB URL

# --- [AI 설정] ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

# === 화면 설정 ===
st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")

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
    .stTextInput > div > div > input { border-radius: 12px; }
    
    /* 🚨 다국어 셀렉트 박스 작게 만들기 */
    .stSelectbox div[data-testid="stSelectboxInline"] {
        max-width: 150px; /* 최대 너비 설정 */
        font-size: 0.9em; /* 글자 크기 작게 */
    }
    .stSelectbox div[data-testid="stSelectboxInline"] .st-bh {
        padding: 0.25rem 0.5rem; /* 패딩 줄이기 */
    }
    </style>
""", unsafe_allow_html=True)

# --- [다국어 텍스트 딕셔너리] ---
TEXTS = {
    "ko": {
        "welcome": "반갑습니다! 어떤 도움이 필요하신가요?",
        "feedback_title": "💬 피드백 및 건의사항 보내기",
        "feedback_placeholder": "더 좋은 서비스를 위해 의견을 남겨주세요!",
        "feedback_button": "의견 보내기",
        "feedback_success": "✅ 소중한 의견이 구글 서버에 안전하게 저장되었습니다!",
        "feedback_fail": "저장에 실패했습니다. 잠시 후 다시 시도해주세요.",
        "feedback_empty": "내용을 입력해주세요.",
        "weather_prefix": "🌤️ 현재 대전 날씨:",
        "visitor_button": "🧳 대전 방문객\n(처음 왔어요)",
        "senior_button": "👴 어르신 도우미\n(쉽게 알려줘요)",
        "tashu_button": "🚲 내 주변 '타슈' 찾기 (지도 보기)",
        "tashu_loading": "🚲 타슈 위치를 찾는 중...",
        "tashu_mock_warning": "⚠️ 현재 '시뮬레이션 데이터'를 보여줍니다.",
        "tashu_success": "✅ 실시간 타슈 {count}곳을 찾았습니다!",
        "tashu_expander": "📋 대여소별 잔여 대수 보기",
        "tashu_station_col": "대여소명",
        "tashu_bikes_col": "잔여대수",
        "back_to_home": "⬅️ 첫 화면",
        "visitor_title": "🧳 대전 여행 가이드",
        "visitor_prompt": "당신은 '대전시 관광 홍보대사'입니다. 방문객에게 트램 이용법과 맛집/명소를 활기차게 추천해주세요.",
        "senior_title": "👴 어르신 교통 비서",
        "senior_prompt": "당신은 대전의 마스코트 '꿈돌이'입니다. 어르신을 위해 이모티콘 없이 쉽고 천천히 설명해주세요.",
        "photo_uploader": "사진을 찍어보세요 (없어도 질문 가능)",
        "photo_caption": "찍은 사진",
        "analyzing": "분석 중...",
        "ai_error": "🚨 에러 발생:",
        "chat_input_placeholder": "궁금한 점을 입력하세요 (키보드 마이크 사용 가능)",
        "thinking": "생각 중...",
        "ai_explain_image": "이 사진을 보고 핵심 내용을 3문장으로 아주 쉽게 설명해주세요.",
        "ai_chat_reply": "친절하게 답변해주세요.",
        "call_center_expander": "📞 상담원 연결이 필요하신가요?",
        "call_center_button": "👩‍💼 120 콜센터 전화하기",
    },
    "en": {
        "welcome": "Hello! How can I help you?",
        "feedback_title": "💬 Send Feedback & Suggestions",
        "feedback_placeholder": "Please share your thoughts for better service!",
        "feedback_button": "Send Feedback",
        "feedback_success": "✅ Your valuable feedback has been securely saved to Google servers!",
        "feedback_fail": "Failed to save. Please try again later.",
        "feedback_empty": "Please enter content.",
        "weather_prefix": "🌤️ Current Daejeon Weather:",
        "visitor_button": "🧳 Daejeon Visitor\n(First time here)",
        "senior_button": "👴 Senior Assistant\n(Explain simply)",
        "tashu_button": "🚲 Find 'Tashu' nearby (View Map)",
        "tashu_loading": "🚲 Searching for Tashu stations...",
        "tashu_mock_warning": "⚠️ Showing 'Simulation Data' currently.",
        "tashu_success": "✅ Found {count} real-time Tashu stations!",
        "tashu_expander": "📋 View available bikes by station",
        "tashu_station_col": "Station Name",
        "tashu_bikes_col": "Bikes Available",
        "back_to_home": "⬅️ Home",
        "visitor_title": "🧳 Daejeon Travel Guide",
        "visitor_prompt": "You are a 'Daejeon Tourism Ambassador'. Enthusiastically recommend tram usage, restaurants, and attractions to visitors.",
        "senior_title": "👴 Senior Transportation Helper",
        "senior_prompt": "You are 'Kkumdori', Daejeon's mascot. Explain simply and slowly for seniors without emoticons.",
        "photo_uploader": "Take a photo (can ask without one)",
        "photo_caption": "Taken Photo",
        "analyzing": "Analyzing...",
        "ai_error": "🚨 Error occurred:",
        "chat_input_placeholder": "Enter your question (can use keyboard mic)",
        "thinking": "Thinking...",
        "ai_explain_image": "Please describe the core content of this photo in 3 simple sentences.",
        "ai_chat_reply": "Please respond kindly.",
        "call_center_expander": "📞 Need to connect with an agent?",
        "call_center_button": "👩‍💼 Call 120 Call Center",
    },
    "ja": {
        "welcome": "ようこそ！何かお手伝いしましょうか？",
        "feedback_title": "💬 フィードバックとご意見を送る",
        "feedback_placeholder": "より良いサービスのためにご意見をお聞かせください！",
        "feedback_button": "意見を送る",
        "feedback_success": "✅ 貴重なご意見がGoogleサーバーに安全に保存されました！",
        "feedback_fail": "保存に失敗しました。後でもう一度お試しください。",
        "feedback_empty": "内容を入力してください。",
        "weather_prefix": "🌤️ 現在の大田の天気:",
        "visitor_button": "🧳 大田訪問者\n(初めての方)",
        "senior_button": "👴 高齢者アシスタント\n(やさしく教えて)",
        "tashu_button": "🚲 周辺の「タシュ」を探す (地図表示)",
        "tashu_loading": "🚲 タシュの場所を検索中...",
        "tashu_mock_warning": "⚠️ 現在「シミュレーションデータ」を表示しています。",
        "tashu_success": "✅ リアルタイムのタシュ {count}ヶ所を見つけました！",
        "tashu_expander": "📋 貸出所別残台数を見る",
        "tashu_station_col": "貸出所名",
        "tashu_bikes_col": "残台数",
        "back_to_home": "⬅️ 最初に戻る",
        "visitor_title": "🧳 大田旅行ガイド",
        "visitor_prompt": "あなたは「大田市観光広報大使」です。訪問者にトラムの利用法や美味しいお店、名所を活気よくおすすめしてください。",
        "senior_title": "👴 高齢者交通アシスタント",
        "senior_prompt": "あなたは大田のマスコット「クムドリ」です。高齢者のために絵文字なしで優しくゆっくり説明してください。",
        "photo_uploader": "写真を撮る (質問だけでもOK)",
        "photo_caption": "撮った写真",
        "analyzing": "分析中...",
        "ai_error": "🚨 エラーが発生しました:",
        "chat_input_placeholder": "質問を入力してください (キーボードマイク使用可)",
        "thinking": "考え中...",
        "ai_explain_image": "この写真の核心内容を3つの簡単な文で説明してください。",
        "ai_chat_reply": "親切に答えてください。",
        "call_center_expander": "📞 オペレーターへの接続が必要ですか？",
        "call_center_button": "👩‍💼 120コールセンターに電話する",
    },
    "zh": {
        "welcome": "您好！有什么可以帮您的吗？",
        "feedback_title": "💬 提交反馈和建议",
        "feedback_placeholder": "请分享您的意见，以提供更好的服务！",
        "feedback_button": "发送意见",
        "feedback_success": "✅ 您的宝贵意见已安全保存到谷歌服务器！",
        "feedback_fail": "保存失败。请稍后再试。",
        "feedback_empty": "请输入内容。",
        "weather_prefix": "🌤️ 大田当前天气:",
        "visitor_button": "🧳 大田访客\n(第一次来)",
        "senior_button": "👴 老年人助手\n(简单告诉我)",
        "tashu_button": "🚲 查找附近的“Tashu” (查看地图)",
        "tashu_loading": "🚲 正在搜索Tashu站点...",
        "tashu_mock_warning": "⚠️ 当前显示“模拟数据”。",
        "tashu_success": "✅ 找到了{count}个实时Tashu站点！",
        "tashu_expander": "📋 查看各站点可用自行车",
        "tashu_station_col": "站点名称",
        "tashu_bikes_col": "可用数量",
        "back_to_home": "⬅️ 返回首页",
        "visitor_title": "🧳 大田旅游指南",
        "visitor_prompt": "您是“大田市旅游宣传大使”。请热情地向游客推荐电车使用方法、美食店和景点。",
        "senior_title": "👴 老年人交通助手",
        "senior_prompt": "您是大田的吉祥物“Kkumdori”。请为老年人提供简单、缓慢、不带表情符号的说明。",
        "photo_uploader": "拍照 (没有照片也可以提问)",
        "photo_caption": "所拍照片",
        "analyzing": "分析中...",
        "ai_error": "🚨 发生错误:",
        "chat_input_placeholder": "输入您的问题 (可使用键盘麦克风)",
        "thinking": "思考中...",
        "ai_explain_image": "请用3个简单的句子描述这张照片的核心内容。",
        "ai_chat_reply": "请友善地回答。",
        "call_center_expander": "📞 需要联系客服吗？",
        "call_center_button": "👩‍💼 拨打120客服中心",
    },
    "vi": {
        "welcome": "Xin chào! Tôi có thể giúp gì cho bạn?",
        "feedback_title": "💬 Gửi phản hồi và đề xuất",
        "feedback_placeholder": "Hãy chia sẻ ý kiến của bạn để dịch vụ tốt hơn!",
        "feedback_button": "Gửi phản hồi",
        "feedback_success": "✅ Phản hồi quý báu của bạn đã được lưu an toàn trên máy chủ Google!",
        "feedback_fail": "Lưu thất bại. Vui lòng thử lại sau.",
        "feedback_empty": "Vui lòng nhập nội dung.",
        "weather_prefix": "🌤️ Thời tiết hiện tại ở Daejeon:",
        "visitor_button": "🧳 Khách tham quan Daejeon\n(Lần đầu đến)",
        "senior_button": "👴 Trợ lý người cao tuổi\n(Giải thích đơn giản)",
        "tashu_button": "🚲 Tìm 'Tashu' gần đây (Xem bản đồ)",
        "tashu_loading": "🚲 Đang tìm trạm Tashu...",
        "tashu_mock_warning": "⚠️ Hiện đang hiển thị 'Dữ liệu mô phỏng'.",
        "tashu_success": "✅ Đã tìm thấy {count} trạm Tashu theo thời gian thực!",
        "tashu_expander": "📋 Xem số xe đạp có sẵn theo trạm",
        "tashu_station_col": "Tên trạm",
        "tashu_bikes_col": "Số lượng còn lại",
        "back_to_home": "⬅️ Về trang chủ",
        "visitor_title": "🧳 Hướng dẫn du lịch Daejeon",
        "visitor_prompt": "Bạn là 'Đại sứ du lịch thành phố Daejeon'. Hãy nhiệt tình giới thiệu cách sử dụng xe điện, nhà hàng và điểm tham quan cho du khách.",
        "senior_title": "👴 Trợ lý giao thông cho người cao tuổi",
        "senior_prompt": "Bạn là linh vật 'Kkumdori' của Daejeon. Vui lòng giải thích đơn giản và chậm rãi cho người cao tuổi mà không dùng biểu tượng cảm xúc.",
        "photo_uploader": "Chụp ảnh (có thể hỏi không cần ảnh)",
        "photo_caption": "Ảnh đã chụp",
        "analyzing": "Đang phân tích...",
        "ai_error": "🚨 Lỗi xảy ra:",
        "chat_input_placeholder": "Nhập câu hỏi của bạn (có thể dùng mic bàn phím)",
        "thinking": "Đang suy nghĩ...",
        "ai_explain_image": "Vui lòng mô tả nội dung chính của bức ảnh này trong 3 câu đơn giản.",
        "ai_chat_reply": "Vui lòng trả lời một cách tử tế.",
        "call_center_expander": "📞 Bạn có cần kết nối với tổng đài viên không?",
        "call_center_button": "👩‍💼 Gọi trung tâm cuộc gọi 120",
    }
}

# --- [함수 모음] ---
def get_daejeon_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=36.35&lon=127.38&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url, timeout=3).json()
        if response.get("weather"):
            desc = response["weather"][0]["description"]
            temp = round(response["main"]["temp"], 1)
            # 날씨 정보는 한국어로 고정 (API가 한국어만 제공)
            return f"{desc}, {temp}℃" 
        return ""
    except: return ""

def speak(text, lang='ko'): # 🚨 TTS 함수에 언어 인자 추가
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except: pass

def show_minwon_button(current_lang_texts): # 🚨 텍스트 인자 추가
    with st.expander(current_lang_texts["call_center_expander"]):
        st.link_button(current_lang_texts["call_center_button"], "tel:120", use_container_width=True)

def ask_ai_with_retry(content, retries=3):
    last_error = None
    for _ in range(retries):
        try:
            return model.generate_content(content)
        except Exception as e:
            last_error = e
            time.sleep(1)
    raise last_error

def get_mock_tashu_data():
    data = {'lat': [36.3504, 36.3587, 36.3325, 36.3615, 36.3284], 'lon': [127.3845, 127.3848, 127.4342, 127.3546, 127.4213], 'station': ['(예시) 대전시청', '(예시) 정부청사', '(예시) 대전역', '(예시) 유성온천', '(예시) 중앙로'], 'bikes': np.random.randint(3, 15, 5)}
    return pd.DataFrame(data)

def get_real_tashu_data():
    URL = f"http://apis.data.go.kr/6300000/Tashu/getStationList?serviceKey={TASHU_API_KEY}&pageNo=1&numOfRows=500&type=json"
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                df = pd.DataFrame(items)
                df = df.rename(columns={'Y_POS': 'lat', 'X_POS': 'lon', 'STATION_NAME': 'station', 'PARKING_COUNT': 'bikes'})
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                return df.dropna(subset=['lat', 'lon'])
        return get_mock_tashu_data()
    except: return get_mock_tashu_data()

# 구글 시트로 데이터 보내는 함수
def save_to_google_sheet(feedback_text):
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {"날짜시간": now, "내용": feedback_text}
        requests.post(SHEETDB_URL, json={"data": data})
        return True
    except:
        return False

# --- [세션 상태 초기화] ---
if "mode" not in st.session_state: st.session_state.mode = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None
if "show_tashu" not in st.session_state: st.session_state.show_tashu = False
if "lang" not in st.session_state: st.session_state.lang = "ko" # 🚨 기본 언어 설정: 한국어

# --- 현재 언어 텍스트 가져오기 ---
current_lang_texts = TEXTS[st.session_state.lang]

# =========================================
# [화면 1] 모드 선택
# =========================================
if st.session_state.mode is None:
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1: st.title("대전 Easy-Tram")
    with c2:
        if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", use_container_width=True)
    with c3:
        if os.path.exists("한화이글스.jpg"): st.image("한화이글스.jpg", use_container_width=True)
    with c4:
        if os.path.exists("성심당.jpg"): st.image("성심당.jpg", use_container_width=True)

    # 피드백 버튼
    with st.expander(current_lang_texts["feedback_title"]):
        feedback = st.text_area(current_lang_texts["feedback_placeholder"], height=100)
        if st.button(current_lang_texts["feedback_button"]):
            if feedback:
                with st.spinner(current_lang_texts["thinking"]):
                    success = save_to_google_sheet(feedback)
                    if success:
                        st.success(current_lang_texts["feedback_success"])
                    else:
                        st.error(current_lang_texts["feedback_fail"])
                time.sleep(2)
                st.rerun()
            else:
                st.warning(current_lang_texts["feedback_empty"])

    # 🚨 [신규] 다국어 선택 드롭다운 (subheader 옆에 배치)
    col_subheader, col_lang = st.columns([4, 1])
    with col_subheader:
        st.subheader(current_lang_texts["welcome"])
    with col_lang:
        # 🚨 CSS를 적용해서 작게 만듭니다.
        selected_lang_name = st.selectbox(
            "",
            options=["한국어", "English", "日本語", "中文", "Tiếng Việt"],
            index=["ko", "en", "ja", "zh", "vi"].index(st.session_state.lang),
            label_visibility="collapsed", # 라벨 숨기기
            key="lang_selector"
        )
        # 선택된 언어에 따라 세션 상태 업데이트
        lang_code_map = {"한국어": "ko", "English": "en", "日本語": "ja", "中文": "zh", "Tiếng Việt": "vi"}
        new_lang_code = lang_code_map.get(selected_lang_name, "ko")
        if new_lang_code != st.session_state.lang:
            st.session_state.lang = new_lang_code
            st.rerun() # 언어 바뀌면 새로고침하여 텍스트 다시 로드

    weather = get_daejeon_weather()
    if weather: st.info(f"{current_lang_texts['weather_prefix']} **{weather}**")
    st.write("---")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(current_lang_texts["visitor_button"], use_container_width=True):
            st.session_state.mode = "visitor"
            st.rerun()
    with c2:
        if st.button(current_lang_texts["senior_button"], use_container_width=True):
            st.session_state.mode = "senior"
            st.rerun()

    st.write("")
    if st.button(current_lang_texts["tashu_button"], use_container_width=True, type="primary"):
        st.session_state.show_tashu = not st.session_state.show_tashu

    if st.session_state.show_tashu:
        with st.spinner(current_lang_texts["tashu_loading"]):
            tashu_df = get_real_tashu_data()
        if '(예시)' in tashu_df['station'].iloc[0]:
             st.warning(current_lang_texts["tashu_mock_warning"])
        else:
             st.success(current_lang_texts["tashu_success"].format(count=len(tashu_df)))
        tashu_df['color'] = '#00C73C'
        st.map(tashu_df, latitude='lat', longitude='lon', size=40, color='color')
        with st.expander(current_lang_texts["tashu_expander"]):
             st.dataframe(tashu_df[['station', 'bikes']].rename(columns={'station':current_lang_texts["tashu_station_col"], 'bikes':current_lang_texts["tashu_bikes_col"]}), hide_index=True, use_container_width=True)
        st.write("---")

# =========================================
# [화면 2] 메인 기능
# =========================================
else:
    if st.session_state.mode == "senior":
        st.markdown("""<style> p, div, button, input { font-size: 1.3rem !important; } </style>""", unsafe_allow_html=True)

    if st.button(current_lang_texts["back_to_home"]):
        st.session_state.mode = None
        st.session_state.show_tashu = False
        st.session_state.chat_history = []
        st.rerun()

    if st.session_state.mode == "visitor":
        st.title(current_lang_texts["visitor_title"])
        system_prompt = current_lang_texts["visitor_prompt"]
    else:
        c1, c2 = st.columns([3, 1])
        with c1: st.title(current_lang_texts["senior_title"])
        with c2:
             if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", width=80)
        system_prompt = current_lang_texts["senior_prompt"]

    image = None
    uploaded_file = st.file_uploader(current_lang_texts["photo_uploader"], type=["jpg", "png", "jpeg"])

    if uploaded_file:
        if st.session_state.uploaded_image != uploaded_file:
            st.session_state.chat_history = []
            st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption=current_lang_texts["photo_caption"], use_column_width=True)

        if not st.session_state.chat_history:
            with st.spinner(current_lang_texts["analyzing"]):
                try:
                    prompt = f"{system_prompt}\n{current_lang_texts['ai_explain_image']}"
                    response = ask_ai_with_retry([prompt, image])
                    st.session_state.chat_history.append({"role": "ai", "text": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"{current_lang_texts['ai_error']} {e}")

    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if message["role"] == "ai" else "user"
        avatar = "🤖"
        if st.session_state.mode == "senior" and role == "assistant":
             if os.path.exists("꿈돌이.jpg"): avatar = "꿈돌이.jpg"
             else: avatar = "🟡"
        with st.chat_message(role, avatar=avatar):
            st.write(message['text'])
            if role == "assistant" and i == len(st.session_state.chat_history) - 1:
                speak(message['text'], lang=st.session_state.lang) # 🚨 TTS 언어 설정
                if st.session_state.mode == "senior": show_minwon_button(current_lang_texts)

    user_input = st.chat_input(current_lang_texts["chat_input_placeholder"])
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner(current_lang_texts["thinking"]):
            try:
                history = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-3:]])
                prompt = f"{system_prompt}\n[이전 대화]{history}\n[새 질문]{user_input}\n{current_lang_texts['ai_chat_reply']}"
                if image: response = ask_ai_with_retry([prompt, image])
                else: response = ask_ai_with_retry(prompt)
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"{current_lang_texts['ai_error']} {e}")