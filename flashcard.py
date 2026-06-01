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
st.set_page_config(layout="wide", page_title="Review Game App", page_icon="🎓")

# giao diện chính
st.title("Review Game")
st.markdown("##### === Triệu Kim Lanh ===")
# ================================
# INIT SESSION (KHỞI TẠO BỘ NHỚ)
# ================================
if "flashcard_data" not in st.session_state:
    st.session_state["flashcard_data"] = None
if "game_type" not in st.session_state:
    st.session_state["game_type"] = None
if "flipped_gv" not in st.session_state:
    st.session_state["flipped_gv"] = False
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

# ================================
# SIDEBAR ROLE
# ================================
st.sidebar.title("🎓 Chế độ hệ thống")
role = st.sidebar.radio("Bạn là:", ["Giảng viên", "Sinh viên"])

# ================================
# CHẾ ĐỘ: GIẢNG VIÊN
# ================================
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
            # Đọc file và lưu vào session_state tạm thời để không bị mất khi rerun
            if "raw_df" not in st.session_state:
                st.session_state["raw_df"] = pd.read_csv(uploaded_file)
            
            df = st.session_state["raw_df"]
            st.write("👉 Xem trước 3 dòng đầu của file bạn vừa upload:")
            st.dataframe(df.head(3), use_container_width=True)

            required_cols = ["question", "solution", "note"]
            if not all(col in df.columns for col in required_cols):
                st.error(f"❌ File CSV thiếu cột. Cần có đủ chính xác 3 cột tên: {required_cols}")
                st.stop()

            # Lọc phân loại
            notes = df["note"].dropna().unique().tolist()
            selected_note = st.selectbox("Lọc câu hỏi theo Phân loại (Cột Note)", notes)
            df_filtered = df[df["note"] == selected_note]

            # Chọn số lượng câu
            max_q = len(df_filtered)
            if max_q == 0:
                st.warning("Không có câu hỏi nào thuộc phân loại này!")
            else:
                num_q = st.slider("Chọn số lượng câu cho đề game", 1, max_q, min(5, max_q))
                game_type = st.radio("Chọn hình thức ôn tập", ["Flashcard", "Matching Game"])

                if st.button("🚀 KHỞI TẠO VÀ PHÁT ĐỀ"):
                    # Lấy mẫu ngẫu nhiên và lưu thẳng vào session_state chính
                    st.session_state["flashcard_data"] = df_filtered.sample(num_q).reset_index(drop=True)
                    st.session_state["game_type"] = game_type
                    
                    # Reset toàn bộ trạng thái chơi
                    st.session_state["current_card"] = 0
                    st.session_state["flipped_gv"] = False
                    st.session_state["matched"] = []
                    st.session_state["opened_cards"] = []
                    st.session_state["score"] = 0
                    st.session_state["start_time"] = None
                    if "deck" in st.session_state: del st.session_state["deck"]
                    if "shuffled_answers" in st.session_state: del st.session_state["shuffled_answers"]

                    st.success("🎉 ĐỀ ĐÃ ĐƯỢC TẠO THÀNH CÔNG! Bạn có thể xem trước ở khung phía dưới hoặc bảo Sinh viên vào làm.")
                    st.rerun()

        # --- KHU VỰC HIỂN THỊ XEM TRƯỚC (PREVIEW) ĐỘC LẬP ---
        if st.session_state["flashcard_data"] is not None:
            st.markdown("---")
            st.subheader("👀 Khung xem trước đề đang phát công khai")
            
            preview_data = st.session_state["flashcard_data"]
            st.info(f"Dạng bài đang phát: **{st.session_state['game_type']}** | Tổng số câu: **{len(preview_data)}**")
            
            # Hiển thị bảng tổng quan các câu có trong đề
            with st.expander("📄 Nhấp vào đây để xem toàn bộ danh sách câu hỏi trong đề"):
                st.dataframe(preview_data, use_container_width=True)

            # Khung Demo tính năng Lật thẻ (Chỉ dành cho chế độ Flashcard)
            if st.session_state["game_type"] == "Flashcard":
                st.markdown("**Demo hiển thị câu đầu tiên (Kiểm tra lật mặt thẻ):**")
                row_gv = preview_data.iloc[0]
                
                if st.session_state["flipped_gv"]:
                    txt_gv = row_gv['solution']
                    bg_gv = "#e3f2fd"
                    label_gv = "Mặt sau (Đáp án)"
                else:
                    txt_gv = row_gv['question']
                    bg_gv = "#f9f9f9"
                    label_gv = "Mặt trước (Câu hỏi)"
                    
                st.markdown(
                    f"""
                    <div style='border:2px solid #1e88e5; padding:30px; border-radius:10px; background:{bg_gv}; text-align:center; margin-bottom:15px;'>
                        <small style='color:gray;'>[{label_gv}]</small><br><br><span style='font-size:20px;'><b>{txt_gv}</b></span>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                if st.button("🔄 Thử bấm lật thẻ"):
                    st.session_state["flipped_gv"] = not st.session_state["flipped_gv"]
                    st.rerun()

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

# ================================
# CHẾ ĐỘ: SINH VIÊN
# ================================
else:
    st.title("🎓 Khu vực Ôn Tập Của Sinh Viên")
    
    data = st.session_state.get("flashcard_data")
    if data is None:
        st.warning("⏳ Giảng viên hiện chưa phát đề bài nào. Vui lòng đợi giảng viên bật đề!")
        st.stop()

    game_type = st.session_state.get("game_type")

    # BẮT NHẬP THÔNG TIN TRƯỚC KHI CHƠI
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
    st.sidebar.success(f"👤 Sinh viên / Nhóm: {student_name}")
    if st.sidebar.button("Đổi tài khoản"):
        st.session_state["student_info"] = None
        st.rerun()

    elapsed = int(time.time() - st.session_state["start_time"])

    # --- FLASHCARD TRẮC NGHIỆM CHỌN ĐÁP ÁN (BÊN SV) ---
    if game_type == "Flashcard":
        st.subheader("📝 Trắc nghiệm ôn tập kiến thức")
        
        if st.session_state["current_card"] >= len(data):
            st.balloons()
            st.success(f"🎉 Chúc mừng bạn đã hoàn thành bài trắc nghiệm! Điểm số: {st.session_state['score']}/{len(data)} trong {elapsed}s")
            
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
        st.markdown(
            f"""
            <div style="border-radius:12px; padding:40px; text-align:center; font-size:22px;
                        background-color: #f1f8e9; color: #2e7d32; border:2px dashed #81c784; margin-bottom:25px;">
                ❓ Câu hỏi: <b>{row['question']}</b>
            </div>
            """, unsafe_allow_html=True
        )
        
        st.write("👇 Hãy chọn đáp án chính xác nhất trong toàn bộ danh sách dưới đây:")
        
        for ans in st.session_state["shuffled_answers"]:
            if st.button(ans, key=f"ans_{ans}", use_container_width=True):
                if ans == row["solution"]:
                    st.success("🎉 Chính xác!")
                    st.session_state["score"] += 1
                    time.sleep(0.6)
                    st.session_state["current_card"] += 1
                    st.rerun()
                else:
                    st.error("❌ Sai rồi! Hãy thử chọn lại đáp án khác hoặc bấm Bỏ qua.")
        
        st.markdown("---")
        if st.button("⏩ Bỏ qua câu này (Next)"):
            st.session_state["current_card"] += 1
            st.rerun()

    # --- MATCHING GAME (CHỈ KHUNG NÀY ĐỀU NHAU) ---
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
                time.sleep(0.3)
                st.rerun()
            else:
                st.toast("Không khớp rồi, thử lại nhé!", icon="❌")
                time.sleep(0.8)
                st.session_state["opened_cards"] = []
                st.rerun()