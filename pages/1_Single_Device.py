import streamlit as st
from audiorecorder import audiorecorder
from ddtw import DDTW
import numpy as np
import pandas as pd
import librosa
import uuid
import time

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

def extract_features(y, sr):
    "いろいろな特徴量を抽出した辞書を返す"
    features_dict = {}
    
    y_trimmed, _ = librosa.effects.trim(y=y, top_db=25) # 無音区間削除
    y = librosa.util.normalize(y_trimmed) # 正規化
    
    features_dict["chroma_stft"] = librosa.feature.chroma_stft(y=y,sr=sr).flatten()
    features_dict["chroma_cqt"] = librosa.feature.chroma_cqt(y=y,sr=sr).flatten()
    features_dict["chroma_cens"] = librosa.feature.chroma_cens(y=y,sr=sr).flatten()
    # features_dict["melspectrogram"] = librosa.feature.melspectrogram(y=y,sr=sr) # パラメータ多すぎ
    features_dict["mfcc"] = librosa.feature.mfcc(y=y,sr=sr).flatten()
    features_dict["rms"] = librosa.feature.rms(y=y).flatten()
    features_dict["spectral_centroid"] = librosa.feature.spectral_centroid(y=y,sr=sr).flatten()
    features_dict["spectral_bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr).flatten()
    features_dict["spectral_contrast"] = librosa.feature.spectral_contrast(y=y,sr=sr).flatten()
    features_dict["spectral_flatness"] = librosa.feature.spectral_flatness(y=y).flatten()
    features_dict["spectral_rolloff"] = librosa.feature.spectral_rolloff(y=y,sr=sr).flatten()
    features_dict["poly_features"] = librosa.feature.poly_features(y=y,sr=sr).flatten()
    features_dict["tonnetz"] = librosa.feature.tonnetz(y=y,sr=sr).flatten()
    features_dict["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(y=y).flatten()
    return features_dict
    

def show_result():
    st.session_state["finished"] = True
    ss_dict = st.session_state
    last_player_index = ss_dict["last_player_index"]
    result_list = []
    for player_index in range(1, last_player_index+1):
        
        player_y, player_sr = librosa.load(ss_dict[f"path_{player_index}"])
        player_features = extract_features(player_y, sr=player_sr)

        theme_y, theme_sr = librosa.load(ss_dict[f"theme_path_{player_index}"])
        theme_y_trimmed, index = librosa.effects.trim(theme_y, top_db=25)
        theme_features = extract_features(theme_y_trimmed, sr=theme_sr)
        player_name = ss_dict[f"name_{player_index}"]
        
        # DDTWを使う（DTWだと何も言わない方がスコアが高くなってしまうため）
        score = {}
        with st.spinner(f'{player_name}のスコアを計算中...'):
            for key in player_features.keys():
                gamma_mat, arrows, _ = DDTW(player_features[key], theme_features[key])
                ddtw_eval = 1 - (gamma_mat[-1][-1] / np.array(gamma_mat).max())
                score[key] = ddtw_eval
        
        score["player_name"] = player_name
        result_list.append(score)
    st.write("▼ 結果")
    df = pd.DataFrame.from_dict(result_list)
    df_i = df.set_index("player_name")
    st.dataframe(df_i)


st.set_page_config(page_title="１台の端末でプレイする", page_icon="👤")
st.sidebar.header("１台の端末でプレイする")
# st.sidebar.write(
#     """ここに説明を書く"""
# )
name_to_path = {
    "ネコ": "Meow.mp3",
    "イヌ": "Barking_of_a_dog.mp3"
}
option = st.sidebar.selectbox('モノマネするお題を選んでください', name_to_path.keys())
st.sidebar.button("最初から", on_click=reset)




if "uuid" not in st.session_state:
    st.session_state["uuid"] = str(uuid.uuid4())
if "player_index" not in st.session_state:
    st.session_state["player_index"] = 1

if "finished" not in st.session_state:
    theme_audio_file = open(f"static/theme/{name_to_path[option]}", 'rb')
    theme_audio_bytes = theme_audio_file.read()
    st.write(f"▼ お手本：{option}")
    st.audio(theme_audio_bytes)

    st.markdown("---")
    record()