#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 31 08:48:59 2026
streamlit run "/Users/trieukimlanh/Library/CloudStorage/GoogleDrive-lanhtk@hub.edu.vn/My Drive/Spyder/app/flashcard/flashcard.py"
@author: trieukimlanh
"""
import streamlit as st
import pandas as pd
import random
import time

# Cấu hình trang rộng để hiển thị các ô ghép cặp đẹp hơn
st.set_page_config(layout="wide", page_title="Review App", page_icon="🎓")

# ================================
# BỘ KHO LƯU TRỮ TRUNG GIAN (DÙNG CHUNG TOÀN HỆ THỐNG)
# ================================
@st.cache_resource
def get_global_store():
    # Khởi tạo một dictionary chung cho mọi session
    return {"flashcard_data": None, "game_type": None}

global_store = get_global_store()
# ================================
# TỐI ƯU CSS TOÀN CỤC (ĐỊNH DẠNG KHUNG FLASHCARD CHUẨN)
# ================================
st.markdown("""
    <style>
    /* Khung bo tròn chữ nhật bao quanh */
    .flashcard-box {
        border-radius: 20px !important; 
        padding: 40px 30px !important; 
        text-align: center !important; 
        min-height: 200px !important;
        background-color: var(--background-color) !important; 
        color: var(--text-color) !important;
        margin-bottom: 25px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* Màu viền riêng biệt */
    .border-question { border: 3px solid #3b82f6 !important; }
    .border-solution { border: 3px solid #10b981 !important; }

    /* Định dạng nhãn chữ nhỏ ở trên */
    .card-tag {
        font-size: 14px !important; 
        opacity: 0.7 !important; 
        font-weight: normal !important; 
        margin-bottom: 15px !important;
        text-align: center !important;
    }
    
    /* Định dạng văn bản chính (gồm cả chữ thường, markdown và công thức toán) */
    .card-text {
        font-size: 24px !important;
        font-weight: bold !important;
        line-height: 1.6 !important;
        text-align: center !important;
        display: inline-block !important;
    }
    
    /* Đồng bộ cỡ chữ cho các ký tự KaTeX/Toán học bên trong khung */
    .card-text .katex, .card-text .katex * {
        font-size: 26px !important; 
    }
    </style>
""", unsafe_allow_html=True)


# ================================
# ĐỌC THAM SỐ URL (MẶC ĐỊNH LÀ GV)
# ================================
url_params = st.query_params
url_role = url_params.get("role", "gv") 

# ================================
# INIT SESSION (KHỞI TẠO BỘ NHỚ)
# ================================
if "flashcard_data" not in st.session_state:
    st.session_state["flashcard_data"] = None
if "game_type" not in st.session_state:
    st.session_state["game_type"] = None
if "flipped_gv" not in st.session_state:
    st.session_state["flipped_gv"] = False
if "current_card_gv" not in st.session_state:
    st.session_state["current_card_gv"] = 0  
if "current_card" not in st.session_state:
    st.session_state["current_card"] = 0     
if "matched" not in st.session_state:
    st.session_state["matched"] = []
if "opened_cards" not in st.session_state:
    st.session_state["opened_cards"] = []
if "score" not in st.session_state:
    st.session_state["score"] = 0
if "student_info" not in st.session_state:
    st.session_state["student_info"] = None
if "leaderboard" not in st.session_state:
    st.session_state["leaderboard"] = []
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "quiz_feedback" not in st.session_state:
    st.session_state["quiz_feedback"] = None

# ================================
# XỬ LÝ RẼ NHÁNH TUYỆT ĐỐI THEO URL
# ================================

# NHÁNH 1: SINH VIÊN (?role=student)
if url_role == "student":
    st.title("🎓 Khu vực Ôn Tập Của Sinh Viên")
    
    # ĐỒNG BỘ TỪ KHO CHUNG VÀO SESSION CỦA SV
    if global_store["flashcard_data"] is not None and st.session_state["flashcard_data"] is None:
        st.session_state["flashcard_data"] = global_store["flashcard_data"]
        st.session_state["game_type"] = global_store["game_type"]

    data = st.session_state.get("flashcard_data")
    if data is None:
        st.warning("⏳ Giảng viên hiện chưa phát đề bài nào. Vui lòng đợi giảng viên bật đề!")
        st.stop()

    game_type = st.session_state.get("game_type")

    if st.session_state["student_info"] is None:
        st.subheader("🔒 Đăng nhập thông tin học viên")
        info_input = st.text_input("Nhập Mã số sinh viên / Tên nhóm của bạn:", placeholder="Ví dụ: SV112233")
        
        if st.button("🎯 Xác nhận & Vào học"):
            if info_input.strip() == "":
                st.error("Vui lòng nhập thông tin trước khi bắt đầu!")
            else:
                st.session_state["student_info"] = info_input.strip()
                st.session_state["start_time"] = time.time()
                st.rerun()
        st.stop()

    student_name = st.session_state["student_info"]
    elapsed = int(time.time() - st.session_state["start_time"]) if st.session_state["start_time"] is not None else 0

    # --- SV: FLASHCARD TRẮC NGHIỆM ---
    if game_type == "Flashcard":
        st.subheader("📝 Trắc nghiệm ôn tập kiến thức")
        
        if st.session_state["current_card"] >= len(data):
            st.balloons()
            st.success(f"🎉 Bạn đã hoàn thành bài trắc nghiệm! Điểm số: {st.session_state['score']}/{len(data)} trong {elapsed}s")
            
            if not any(r.get("Tên / Nhóm") == student_name and r.get("Loại bài tập") == "Flashcard (Quiz)" for r in st.session_state["leaderboard"]):
                st.session_state["leaderboard"].append({
                    "Thời gian nộp": time.strftime('%H:%M:%S - %d/%m/%Y'),
                    "Tên / Nhóm": student_name,
                    "Loại bài tập": "Flashcard (Quiz)",
                    "Kết quả điểm": f"{st.session_state['score']} / {len(data)}",
                    "Thời gian hoàn thành": f"{elapsed} giây"
                })
            
            if st.button("Làm lại từ đầu"):
                st.session_state["current_card"] = 0
                st.session_state["score"] = 0
                st.session_state["start_time"] = time.time()
                st.session_state["quiz_feedback"] = None
                if "shuffled_answers" in st.session_state: del st.session_state["shuffled_answers"]
                st.rerun()
            st.stop()

        idx = st.session_state["current_card"]
        row = data.iloc[idx]
        
        if "shuffled_answers" not in st.session_state or st.session_state.get("current_ans_idx") != idx:
            all_solutions = data["solution"].dropna().unique().tolist()
            random.shuffle(all_solutions)
            st.session_state["shuffled_answers"] = all_solutions
            st.session_state["current_ans_idx"] = idx

        st.metric("Tiến độ câu hỏi", f"{idx + 1} / {len(data)}")
        
        # --- FIX CHI TIẾT: Khóa chữ vào trong khung cho SV ---
        st.markdown(
            f"""
            <div class="flashcard-box border-question">
                <div class="card-tag">❓ Câu hỏi</div>
                <div class="card-text">{row['question']}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        if st.session_state["quiz_feedback"] is not None:
            is_correct, selected_ans = st.session_state["quiz_feedback"]
            if is_correct:
                st.success(f"🎉 **Chính xác!** Bạn đã chọn đúng đáp án: **{selected_ans}**")
            else:
                st.error(f"❌ **Sai rồi!** Bạn chọn: *{selected_ans}*. \n\n 👉 Đáp án đúng phải là: **{row['solution']}**")
            
            st.write("---")
            if st.button("⏩ Chuyển sang câu tiếp theo ngay lập tức", type="primary"):
                st.session_state["current_card"] += 1
                st.session_state["quiz_feedback"] = None
                st.rerun()
                
            time.sleep(3.0)
            st.session_state["current_card"] += 1
            st.session_state["quiz_feedback"] = None
            st.rerun()

        else:
            st.write("👇 Hãy chọn đáp án chính xác (Hệ thống ghi nhận và hiển thị kết quả trong 3 giây trước khi chuyển câu):")
            for ans in st.session_state["shuffled_answers"]:
                if st.button(ans, key=f"ans_{ans}_{idx}", use_container_width=True):
                    if ans == row["solution"]:
                        st.session_state["score"] += 1
                        st.session_state["quiz_feedback"] = (True, ans)
                    else:
                        st.session_state["quiz_feedback"] = (False, ans)
                    st.rerun()
            
            st.markdown("---")
            if st.button("⏩ Bỏ qua câu này (Next)"):
                st.session_state["current_card"] += 1
                st.rerun()

    # --- SV: MATCHING GAME ---
    elif game_type == "Matching Game":
        st.subheader("🧩 Trò chơi ghép cặp")

        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] div.stButton > button {
                height: 110px !important;
                border: 2px solid #4a148c !important;
                border-radius: 10px !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                font-weight: bold !important;
            }
            </style>
        """, unsafe_allow_html=True)

        c_score, c_time = st.columns(2)
        c_score.metric("🎯 Tiến độ ghép cặp đúng", f"{st.session_state['score']} / {len(data)}")
        c_time.metric("⏱️ Thời gian trôi qua", f"{elapsed}s")

        if "deck" not in st.session_state:
            deck = []
            for i, row in data.iterrows():
                deck.append(("Q", i, row["question"]))
                deck.append(("A", i, row["solution"]))
            random.shuffle(deck)
            st.session_state["deck"] = deck

        deck = st.session_state["deck"]

        if st.session_state["score"] == len(data):
            st.balloons()
            st.success(f"🎉 Xuất sắc! Bạn đã hoàn thành Matching Game trong {elapsed} giây!")
            
            if not any(r.get("Tên / Nhóm") == student_name and r.get("Loại bài tập") == "Matching Game" for r in st.session_state["leaderboard"]):
                st.session_state["leaderboard"].append({
                    "Thời gian nộp": time.strftime('%H:%M:%S - %d/%m/%Y'),
                    "Tên / Nhóm": student_name,
                    "Loại bài tập": "Matching Game",
                    "Kết quả điểm": f"{len(data)} / {len(data)}",
                    "Thời gian hoàn thành": f"{elapsed} giây"
                })

            if st.button("Chơi lại lượt mới"):
                del st.session_state["deck"]
                st.session_state["matched"] = []
                st.session_state["opened_cards"] = []
                st.session_state["score"] = 0
                st.session_state["start_time"] = time.time()
                st.rerun()
            st.stop()

        cols = st.columns(4)
        for i, card in enumerate(deck):
            with cols[i % 4]:
                if i in st.session_state["matched"]:
                    st.markdown("<div style='height:110px; margin-bottom:1rem; border:2px dashed #eee; border-radius:10px;'></div>", unsafe_allow_html=True) 
                elif i in st.session_state["opened_cards"]:
                    if st.button(f"📍 {card[2]}", key=f"match_{i}", use_container_width=True, type="primary"):
                        st.session_state["opened_cards"].remove(i)
                        st.rerun()
                else:
                    if st.button(card[2], key=f"match_{i}", use_container_width=True):
                        st.session_state["opened_cards"].append(i)
                        st.rerun()

        if len(st.session_state["opened_cards"]) == 2:
            c1, c2 = st.session_state["opened_cards"]
            if deck[c1][1] == deck[c2][1] and deck[c1][0] != deck[c2][0]:
                st.session_state["matched"] += [c1, c2]
                st.session_state["score"] += 1
                st.toast("Ghép chính xác! 👏", icon="✅")
                st.session_state["opened_cards"] = []
                time.sleep(1.0)  
                st.rerun()
            else:
                st.toast("Không khớp rồi, thử lại nhé!", icon="❌")
                time.sleep(2.0)  
                st.session_state["opened_cards"] = []
                st.rerun()

# NHÁNH 2: GIẢNG VIÊN (LINK MẶC ĐỊNH)
else:
    st.sidebar.title("🎓 Chế độ hệ thống")
    role = st.sidebar.radio("Bạn là:", ["Giảng viên", "Sinh viên"])

    if role == "Giảng viên":
        password = st.sidebar.text_input("Nhập password để quản lý", type="password")
        if password != "123":
            st.warning("🔒 Vui lòng nhập đúng password để truy cập quyền Giảng viên.")
            st.stop()

        st.title("👨‍🏫 Khu vực Quản lý của Giảng viên")
        tab_create, tab_results = st.tabs(["🚀 Tạo & Phát Đề", "📊 Bảng Điểm Sinh Viên"])
        
        with tab_create:
            uploaded_file = st.file_uploader("Upload file câu hỏi (CSV)", type=["csv"])

            if uploaded_file:
                if "raw_df" not in st.session_state:
                    st.session_state["raw_df"] = pd.read_csv(uploaded_file)
                
                df = st.session_state["raw_df"]
                st.write("👉 Xem trước dữ liệu file vừa upload:")
                st.dataframe(df.head(3), use_container_width=True)

                required_cols = ["question", "solution", "note"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"❌ File CSV thiếu cột. Cần có đủ chính xác 3 cột tên: {required_cols}")
                    st.stop()

                notes = df["note"].dropna().unique().tolist()
                selected_note = st.selectbox("Lọc câu hỏi theo Phân loại (Cột Note)", notes)
                df_filtered = df[df["note"] == selected_note]

                num_q = st.slider("Chọn số lượng câu cho đề game", 1, len(df_filtered), min(5, len(df_filtered))) if len(df_filtered) > 0 else 1
                game_type = st.radio("Chọn hình thức ôn tập", ["Flashcard", "Matching Game"])

                if st.button("🚀 KHỞI TẠO VÀ PHÁT ĐỀ"):
                    # Tạo dữ liệu cho bản thân GV xem trước
                    st.session_state["flashcard_data"] = df_filtered.sample(num_q).reset_index(drop=True)
                    st.session_state["game_type"] = game_type
                    
                    # LƯU VÀO KHO CHUNG ĐỂ SINH VIÊN THẤY ĐƯỢC
                    global_store["flashcard_data"] = st.session_state["flashcard_data"]
                    global_store["game_type"] = st.session_state["game_type"]
                    
                    # Reset các biến trạng thái cũ như bạn đã viết
                    st.session_state["current_card"] = 0
                    st.session_state["current_card_gv"] = 0
                    st.session_state["flipped_gv"] = False
                    st.session_state["matched"] = []
                    st.session_state["opened_cards"] = []
                    st.session_state["score"] = 0
                    st.session_state["start_time"] = None
                    st.session_state["quiz_feedback"] = None
                    if "deck" in st.session_state: del st.session_state["deck"]
                    if "deck_gv" in st.session_state: del st.session_state["deck_gv"]
                    if "shuffled_answers" in st.session_state: del st.session_state["shuffled_answers"]

                    st.success("🎉 ĐỀ ĐÃ ĐƯỢC TẠO THÀNH CÔNG VÀ PHÁT CHO LỚP!")
                    st.rerun()

            # --- PREVIEW BÊN GV ---
            if st.session_state["flashcard_data"] is not None:
                st.markdown("---")
                st.subheader("👀 Khung xem trước giao diện")
                
                preview_data = st.session_state["flashcard_data"]
                st.info(f"Dạng bài đang phát: **{st.session_state['game_type']}** | Tổng số câu: **{len(preview_data)}**")

                if st.session_state["game_type"] == "Flashcard":
                    total_gv_cards = len(preview_data)
                    idx_gv = st.session_state["current_card_gv"]
                    row_gv = preview_data.iloc[idx_gv]
                    
                    st.write(f"📌 **Đang xem câu hỏi số:** {idx_gv + 1} / {total_gv_cards}")
                    
                    if st.session_state["flipped_gv"]:
                        txt_gv = row_gv['solution']
                        label_gv = f"💡 [Mặt sau - ĐÁP ÁN CÂU {idx_gv + 1}]"
                        class_type = "border-solution"
                    else:
                        txt_gv = row_gv['question']
                        label_gv = f"❓ [Mặt trước - CÂU HỎI CÂU {idx_gv + 1}]"
                        class_type = "border-question"
                    
                    # --- FIX CHI TIẾT: Khóa chữ vào trong khung cho GV ---
                    st.markdown(
                        f"""
                        <div class="flashcard-box {class_type}">
                            <div class="card-tag">{label_gv}</div>
                            <div class="card-text">{txt_gv}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    col_prev, col_flip, col_next = st.columns([1, 2, 1])
                    with col_prev:
                        if st.button("⏪ Previous", use_container_width=True, disabled=(idx_gv == 0)):
                            st.session_state["current_card_gv"] -= 1
                            st.session_state["flipped_gv"] = False
                            st.rerun()
                    with col_flip:
                        if st.button("🔄 Lật mặt thẻ (Flip)", use_container_width=True, type="primary"):
                            st.session_state["flipped_gv"] = not st.session_state["flipped_gv"]
                            st.rerun()
                    with col_next:
                        if st.button("⏩ Next", use_container_width=True, disabled=(idx_gv == total_gv_cards - 1)):
                            st.session_state["current_card_gv"] += 1
                            st.session_state["flipped_gv"] = False
                            st.rerun()

                elif st.session_state["game_type"] == "Matching Game":
                    st.write("📊 **Giao diện lưới ô chữ (Mô phỏng hiển thị mở sẵn):**")
                    st.markdown("""
                        <style>
                        div[data-testid="stVerticalBlock"] div.stButton > button {
                            height: 110px !important;
                            border: 2px solid #4a148c !important;
                            border-radius: 10px !important;
                            white-space: normal !important;
                            word-wrap: break-word !important;
                            font-weight: bold !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)

                    if "deck_gv" not in st.session_state:
                        deck_gv = []
                        for i, row in preview_data.iterrows():
                            deck_gv.append(("Q", i, row["question"]))
                            deck_gv.append(("A", i, row["solution"]))
                        random.shuffle(deck_gv)
                        st.session_state["deck_gv"] = deck_gv
                    
                    deck_gv = st.session_state["deck_gv"]
                    cols_gv = st.columns(4)
                    for i, card in enumerate(deck_gv):
                        with cols_gv[i % 4]:
                            st.button(card[2], key=f"preview_match_{i}", use_container_width=True)

        with tab_results:
            st.subheader("📝 Kết quả làm bài của sinh viên")
            if len(st.session_state["leaderboard"]) == 0:
                st.info("Chưa có sinh viên nào hoàn thành bài tập.")
            else:
                df_leaderboard = pd.DataFrame(st.session_state["leaderboard"])
                st.dataframe(df_leaderboard, use_container_width=True)
                if st.button("🗑️ Xóa sạch bảng điểm"):
                    st.session_state["leaderboard"] = []
                    st.rerun()
                    
    else:
        st.info("💡 Bạn đang ở link quản trị nhưng chọn chế độ hiển thị xem thử của Sinh viên. Để gửi link chuẩn cho lớp, hãy dùng đường dẫn bên dưới:")
        st.code("https://lanh-reviewgame.streamlit.app/?role=student")
