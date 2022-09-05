import secrets
import streamlit as st
from audiorecorder import audiorecorder
from ddtw import DDTW
from database import DB
import numpy as np
import pandas as pd
import json
import librosa
import time
from datetime import timedelta, datetime
from streamlit.components.v1 import html

st.set_page_config(page_title="複数の端末でプレイする", page_icon="👥")

@st.cache
def get_secrets():
    cert = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    return cert

def reset():
    "セッションを初期化する"
    for key in st.session_state.keys():
        del st.session_state[key]

def join():
    if len(st.session_state["secret_word"]) > 0 and len(st.session_state["player_name"]) > 0:
        # TODO: データベースに登録
        # データベースの情報を参照して、合い言葉のセッションが有効かチェックする
        # 無効ならエラー表示＋最初から入力し直すリンク
        st.session_state["role"] = "participant"
        st.session_state["registered"] = True

def host():
    if len(st.session_state["secret_word"]) > 0 and len(st.session_state["player_name"]) > 0:
        # TODO: データベースに登録
        st.experimental_set_query_params(
            secret_word=st.session_state["secret_word"],
            theme=st.session_state["player_theme"]
        )
        st.session_state["role"] = "host"
        st.session_state["registered"] = True

def register():
    st.markdown("# 友だちと一緒にプレイしよう！")
    st.image("static/image/ac_cat.jpg")
    query_params_dict = st.experimental_get_query_params()
    player_role = st.selectbox("▼ わたしは", ["ホストではありません", "ホストです"])
    if player_role == "ホストではありません":
        if "secret_word" in query_params_dict:
            st.session_state["secret_word"] = query_params_dict["secret_word"][0]
            st.write(f"▼ 共通の合い言葉は「{st.session_state['secret_word']}」に設定されました")
        else:
            st.session_state["secret_word"] = st.text_input("▼ 友だちと共通の合い言葉を入力してください", placeholder="※ 必須")
        if "theme" in query_params_dict:
            st.session_state["player_theme"] = query_params_dict["theme"][0]
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

def count_down(ts):
    with st.empty():
        while ts:
            mins, secs = divmod(ts, 60)
            time_now = '{:02d}:{:02d}'.format(mins, secs)
            # st.header(f"{time_now}")
            st.metric("制限時間", f"{time_now}")
            time.sleep(1)
            ts -= 1
    st.warning("セッションの有効期限が切れています", icon="⚠️")
    st.session_state["expired"] = True

def record():
    "音声を録音する"
    audio = audiorecorder("クリックして録音する", "録音中...", f"recorder")

    if len(audio) > 0:
        st.audio(audio)

        file_name = f"static/audio/sample.mp3"
        wav_file = open(file_name, "wb")
        wav_file.write(audio.tobytes())

    st.markdown("---")
    st.button("結果を見る", on_click=show_result)

def extract_features(y, sr):
    "いろいろな特徴量を抽出した辞書を返す"
    features_dict = {}
    y_trimmed, _ = librosa.effects.trim(y=y, top_db=25)  # 無音区間削除
    y = librosa.util.normalize(y_trimmed)  # 正規化
    features_dict["chroma_cens"] = librosa.feature.chroma_cens(y=y, sr=sr)
    features_dict["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(
        y=y)
    for k, v in features_dict.items():
        features_dict[k] = v.flatten()  # 多次元配列を1次元配列に変換する（改善の余地あり）
    return features_dict

def show_result():
    if "expired" in st.session_state:
        return
    st.session_state["finished"] = True
    ss_dict = st.session_state

    player_y, player_sr = librosa.load(f"static/audio/sample.mp3")
    player_features = extract_features(player_y, sr=player_sr)

    theme_y, theme_sr = librosa.load(ss_dict[f"theme_path"])
    theme_y_trimmed, index = librosa.effects.trim(theme_y, top_db=25)
    theme_features = extract_features(theme_y_trimmed, sr=theme_sr)
    player_name = ss_dict[f"player_name"]
    
    result_list = []
    score = {}
    with st.spinner(f'{player_name}のスコアを計算中...'):
        for key in player_features.keys():
            gamma_mat, arrows, _ = DDTW(
                player_features[key], theme_features[key])
            ddtw_eval = 1 - (gamma_mat[-1][-1] / np.array(gamma_mat).max())
            score[key] = ddtw_eval
    score["player_name"] = player_name
    result_list.append(score)

    st.write("▼ 結果")
    df = pd.DataFrame.from_dict(result_list)
    df['total_score'] = (3 * df["chroma_cens"] + 7 *
                         df["zero_crossing_rate"]) / 10
    df_indexed = df.set_index("player_name")

    df_sorted = df_indexed.sort_values(by="total_score", ascending=False)
    st.balloons()
    st.dataframe(df_sorted)    # デバッグ用


if "registered" not in st.session_state:
    register()
else:
    st.markdown("# 準備はいいですか？")
    if "deadline" not in st.session_state:
        td = timedelta(seconds=60)
        st.session_state["deadline"] = datetime.now() + td
    if st.session_state["role"] == "host":
        st.success(f'合い言葉「{st.session_state["secret_word"]}」または「現在のURL」を友だちに共有してください', icon="✅")
    
    with open("static/theme/name_to_path.json", encoding="utf-8") as f:
        name_to_path = json.load(f)
    name = st.session_state['player_theme']
    st.session_state["theme_path"] = f"static/theme/{name_to_path[name]}"
    st.write(f"▼ お手本：{name}")
    theme_audio_file = open(f"static/theme/{name_to_path[name]}", 'rb')
    theme_audio_bytes = theme_audio_file.read()
    st.audio(theme_audio_bytes)
    
    record()
    
    st.markdown("---")
    if "finished" not in st.session_state:
        count_down((st.session_state["deadline"] - datetime.now()).seconds)

def upload():
    db = DB(get_secrets())
    db.firestore_add("test", "さっき")

st.button("upload", on_click=upload)

# サイドバー
st.sidebar.header("複数の端末でプレイする")
# st.sidebar.button("最初から入力し直す", on_click=reset)
# st.sidebar.markdown("[最初からプレイする](https://kitsuya0828-inpersonation-app-app-azumamulti-challenge-u1f74q.streamlitapp.com/Multiple_Devices/)")
html('<a href="https://kitsuya0828-inpersonation-app-app-azumamulti-challenge-u1f74q.streamlitapp.com/Multiple_Devices/" target="_blank">最初からプレイする</a>')

st.session_state