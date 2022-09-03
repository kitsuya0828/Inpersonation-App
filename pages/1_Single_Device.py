import streamlit as st
from audiorecorder import audiorecorder
import numpy as np
import librosa
import uuid
import json


def next():
    st.session_state["player_index"] += 1

def reset():
    for key in st.session_state.keys():
        del st.session_state[key]

def record():
    player_index = st.session_state.player_index
    st.markdown(f"### {player_index}人目")
    player_name = st.text_input("プレイヤー名を入力してください", f"プレイヤー{player_index}")
    audio = audiorecorder("クリックして録音する", "録音中...", f"recorder_{player_index}")

    if len(audio) > 0:
        st.audio(audio)
        
        file_name = f"static/audio/{st.session_state.uuid}_{player_index}.mp3"
        wav_file = open(file_name, "wb")
        wav_file.write(audio.tobytes())
        
        st.session_state[f"theme_path_{player_index}"] = f"static/theme/{name_to_path[option]}"
        st.session_state[f"path_{player_index}"] = file_name
        st.session_state[f"name_{player_index}"] = player_name
    st.markdown("---")
    
    col1, col2 = st.columns([1,1])
    with col1:
        if f"path_{player_index}" in st.session_state:
            st.button("次の人に進む", on_click=next)
    with col2:
        if f"path_{player_index}" in st.session_state:
            st.session_state["last_player_index"] = player_index
        else:
            st.session_state["last_player_index"] = player_index-1
        st.button("結果を見る", on_click=show_result)

def show_result():
    ss_dict = st.session_state
    last_player_index = ss_dict["last_player_index"]
    result_dict = {}
    for player_index in range(1, last_player_index+1):
        
        player_y, player_sr = librosa.load(ss_dict[f"path_{player_index}"])
        player_feature = librosa.feature.spectral_centroid(player_y, sr=player_sr)

        theme_y, theme_sr = librosa.load(ss_dict[f"theme_path_{player_index}"])
        theme_feature = librosa.feature.spectral_centroid(theme_y, sr=theme_sr)
        
        ac, wp = librosa.sequence.dtw(player_feature, theme_feature)
        eval = 1 - (ac[-1][-1] / np.array(ac).max())
        player_name = ss_dict[f"name_{player_index}"]
        if player_name in result_dict:
            player_name += f"({player_index}人目)"
        result_dict[player_name] = eval
    st.write("▼ 結果")
    st.write(result_dict)


st.set_page_config(page_title="１台の端末でプレイする", page_icon="👤")
st.sidebar.header("１台の端末でプレイする")
st.sidebar.write(
    """ここに説明を書く"""
)
name_to_path = {
    "ネコ": "Meow.mp3",
    "イヌ": "Barking_of_a_dog.mp3"
}
option = st.sidebar.selectbox('モノマネするお題を選んでください', name_to_path.keys())
st.sidebar.button("最初から", on_click=reset)


theme_audio_file = open(f"static/theme/{name_to_path[option]}", 'rb')
theme_audio_bytes = theme_audio_file.read()
st.write(f"▼ お手本：{option}")
st.audio(theme_audio_bytes)

st.markdown("---")

if "uuid" not in st.session_state:
    st.session_state["uuid"] = str(uuid.uuid4())
if "player_index" not in st.session_state:
    st.session_state["player_index"] = 1

record()

