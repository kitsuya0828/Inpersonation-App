import streamlit as st
import json

st.set_page_config(page_title="複数の端末でプレイする", page_icon="👥")

def join():
    if len(st.session_state["secret_word"]) > 0 and len(st.session_state["player_name"]) > 0:
        # TODO: データベースに登録
        st.session_state["role"] = "participant"
        st.session_state["registered"] = True

def host():
    if len(st.session_state["secret_word"]) > 0 and len(st.session_state["player_name"]) > 0:
        # TODO: データベースに登録
        st.experimental_set_query_params(secret_word=st.session_state["secret_word"])
        st.session_state["role"] = "host"
        st.session_state["registered"] = True

def register():
    st.markdown("# 友だちと一緒にプレイしよう！")
    st.image("static/image/ac_cat.jpg")
    player_role = st.selectbox("▼ わたしは", ["ホストではありません", "ホストです"])
    if player_role == "ホストではありません":
        st.session_state["secret_word"] = st.text_input("▼ 友だちと共通の合い言葉を入力してください", placeholder="※ 必須")
        st.session_state["player_name"] = st.text_input("▼ ニックネームを入力してください", placeholder="※ 必須")
        join_button = st.button("参加する", on_click=join)
        if join_button:
            if len(st.session_state["secret_word"]) == 0:
                st.error("１文字以上の合い言葉を入力してください", icon="🚨")
            elif len(st.session_state["player_name"]) == 0:
                st.error("１文字以上のニックネームを入力してください", icon="🚨")

    else:
        st.session_state["secret_word"] = st.text_input("▼ 友だちに共有する合い言葉を入力してください", placeholder="※ 必須")
        st.session_state["player_name"] = st.text_input("▼ ニックネームを入力してください", placeholder="※ 必須")
        with open("static/theme/name_to_path.json", encoding="utf-8") as f:
            name_to_path = json.load(f)
            st.session_state["player_theme"] = st.selectbox('▼ モノマネするお題を選んでください', name_to_path.keys())
        host_button = st.button("主催する", on_click=host)
        if host_button:
            if len(st.session_state["secret_word"]) == 0:
                st.error("１文字以上の合い言葉を入力してください", icon="🚨")
            elif len(st.session_state["player_name"]) == 0:
                st.error("１文字以上のニックネームを入力してください", icon="🚨")


if "registered" not in st.session_state:
    register()
else:
    st.markdown("# 準備はいいですか？")
    if st.session_state["role"] == "host":
        st.success(f'合い言葉「{st.session_state["secret_word"]}」または「現在のURL」を友だちに共有してください', icon="✅")

st.sidebar.header("複数の端末でプレイする")
st.sidebar.button("最初から")


st.session_state