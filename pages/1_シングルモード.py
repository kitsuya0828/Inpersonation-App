import streamlit as st
from audiorecorder import audiorecorder
from utils import DDTW
import numpy as np
import pandas as pd
import librosa
import librosa.display
import uuid
import json
import plotly.graph_objs as go
import matplotlib.pyplot as plt
from PIL import Image
from streamlit.components.v1 import html

def next():
    "プレイヤー番号を更新する"
    st.session_state["player_index"] += 1


def reset():
    "セッションを初期化する"
    for key in st.session_state.keys():
        del st.session_state[key]


def record():
    "音声を録音する"
    player_index = st.session_state.player_index
    st.header(f"{player_index}人目の番です！")
    player_name = st.text_input("プレイヤー名を入力してください", f"プレイヤー{player_index}")
    audio = audiorecorder("クリックして録音する", "録音中...", f"recorder_{player_index}")

    if len(audio) > 0:
        st.audio(audio)

        file_name = f"static/audio/{st.session_state.uuid}_{player_index}.wav"
        wav_file = open(file_name, "wb")
        wav_file.write(audio.tobytes())
        
        st.session_state[f"theme_{player_index}"] = option
        st.session_state[f"theme_path_{player_index}"] = f"static/theme/{name_to_path[option]}"
        st.session_state[f"path_{player_index}"] = file_name
        st.session_state[f"name_{player_index}"] = player_name
    st.markdown("---")

    col1, col2 = st.columns([1, 1])  # 2列
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

    y_trimmed, _ = librosa.effects.trim(y=y, top_db=25)  # 無音区間削除
    y = librosa.util.normalize(y_trimmed)  # 正規化

    # features_dict["chroma_stft"] = librosa.feature.chroma_stft(y=y,sr=sr)
    # features_dict["chroma_cqt"] = librosa.feature.chroma_cqt(y=y,sr=sr)
    fig, ax = plt.subplots(2, 1, figsize=(5, 10))
    features_dict["chroma_cens"] = librosa.feature.chroma_cens(y=y, sr=sr)
    librosa.display.specshow(features_dict["chroma_cens"], y_axis='chroma', x_axis='time', ax=ax[0])

    # features_dict["melspectrogram"] = librosa.feature.melspectrogram(y=y,sr=sr) # パラメータ多い
    # features_dict["mfcc"] = librosa.feature.mfcc(y=y,sr=sr)
    # features_dict["rms"] = librosa.feature.rms(y=y)
    # features_dict["spectral_centroid"] = librosa.feature.spectral_centroid(y=y,sr=sr)
    # features_dict["spectral_bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    # features_dict["spectral_contrast"] = librosa.feature.spectral_contrast(y=y,sr=sr)
    # features_dict["spectral_flatness"] = librosa.feature.spectral_flatness(y=y)
    # features_dict["spectral_rolloff"] = librosa.feature.spectral_rolloff(y=y,sr=sr)
    # features_dict["poly_features"] = librosa.feature.poly_features(y=y,sr=sr)
    # features_dict["tonnetz"] = librosa.feature.tonnetz(y=y,sr=sr)
    
    features_dict["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(y=y)
    ax[1].plot(features_dict["zero_crossing_rate"][0])
    features_path = f"static/tmp/{uuid.uuid4()}.png"
    plt.savefig(features_path)
    
    for k, v in features_dict.items():
        features_dict[k] = v.flatten()  # 多次元配列を1次元配列に変換する（改善の余地あり）
    return features_dict, y, features_path


def show_result():
    st.session_state["finished"] = True
    ss_dict = st.session_state
    last_player_index = ss_dict["last_player_index"]
    result_list = []
    added_theme = {}
    fig = go.Figure()
    features_paths = []

    for player_index in range(1, last_player_index+1):
        player_name = ss_dict[f"name_{player_index}"]
        player_y, player_sr = librosa.load(ss_dict[f"path_{player_index}"])
        player_y_trimmed, _ = librosa.effects.trim(player_y, top_db=25)
        player_features, new_player_y, player_features_path = extract_features(player_y_trimmed, sr=player_sr)
        
        fig.add_trace(
            go.Scatter(
                x=[i for i in range(len(new_player_y))],
                y=new_player_y,
                name=player_name
            )
        )
        features_paths.append((player_name, player_features_path))
        
        theme_y, theme_sr = librosa.load(ss_dict[f"theme_path_{player_index}"])
        theme_y_trimmed, index = librosa.effects.trim(theme_y, top_db=25)
        theme_features, new_theme_y, theme_features_path = extract_features(theme_y_trimmed, sr=theme_sr)
        if ss_dict[f"theme_{player_index}"] not in added_theme:
            fig.add_trace(
                go.Scatter(
                    x=[i for i in range(len(new_theme_y))],
                    y=new_theme_y,
                    name=ss_dict[f"theme_{player_index}"]
                )
            )
            added_theme[ss_dict[f"theme_{player_index}"]] = True
            features_paths.append((ss_dict[f"theme_{player_index}"], theme_features_path))
        
        # DDTWを使う（DTWだと何も言わない方がスコアが高くなってしまうため）
        score = {}
        with st.spinner(f'{player_name}のスコアを計算中...'):
            for key in player_features.keys():
                gamma_mat, arrows, _ = DDTW(
                    player_features[key], theme_features[key])
                ddtw_eval = 1 - (gamma_mat[-1][-1] / np.array(gamma_mat).max())
                score[key] = ddtw_eval
        score["player_name"] = player_name
        result_list.append(score)

    st.header("結果発表")
    df = pd.DataFrame.from_dict(result_list)
    df['total_score'] = (3 * df["chroma_cens"] + 7 * df["zero_crossing_rate"]) / 10
    df_indexed = df.set_index("player_name")

    df_sorted = df_indexed.sort_values(by="total_score", ascending=False)
    st.balloons()
    cols = st.columns(last_player_index)
    sorted_names = df_sorted.index
    for i in range(last_player_index):
        name = sorted_names[i]
        cols[i].metric(f"{i+1}位：{name}", f"{int(df_sorted.at[name, 'total_score'] * 100)} 点")
    
    st.caption("▼ 音声波形")
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("▼ クロマ特徴量(CENS) & Zero-crossing rate(ZCR)")
    chroma_cens_cols = st.columns(len(features_paths))
    for i, (name, features_path) in enumerate(features_paths):
        chroma_cens_cols[i].caption(name)
        chroma_cens_cols[i].image(features_path)
    
    st.caption("▼ DDTWスコア")
    st.table(df_sorted)
    
    st.markdown("---")
    st.button("もう一度プレイする", on_click=reset)
    html(f"""<a href="https://twitter.com/share?ref_src=twsrc%5Etfw" class="twitter-share-button" data-size="large" data-hashtags="スティーブじょぶつ" data-url="https://kitsuya0828-inpersonation-app-app-2qumms.streamlitapp.com/" data-text="新感覚ものまね自動採点アプリ「ManeCo」で{5}人中\n{1}位になりました" data-lang="ja" data-show-count="false">Tweet</a><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>""")
    


st.set_page_config(page_title="１台の端末でプレイする", page_icon="👤")
st.sidebar.header("１台の端末でプレイする")

# {動物名: 音声ファイルパス}
with open("static/theme/name_to_path.json", encoding="utf-8") as f:
    name_to_path = json.load(f)
option = st.sidebar.selectbox('モノマネするお題を選んでください', name_to_path.keys())
theme_audio_file_ = open(f"static/theme/{name_to_path[option]}", 'rb')
theme_audio_bytes_ = theme_audio_file_.read()
st.sidebar.audio(theme_audio_bytes_)
st.sidebar.button("最初から", on_click=reset)

# {動物名：画像ファイルパス}
with open("static/image/name_to_image.json", encoding="utf-8") as f:
    name_to_image = json.load(f)

# セッションを管理するUUID
if "uuid" not in st.session_state:
    st.session_state["uuid"] = str(uuid.uuid4())

# セッションが始まった時にプレイヤー番号をリセットする
if "player_index" not in st.session_state:
    st.session_state["player_index"] = 1

# 結果表示画面でないとき
if "finished" not in st.session_state:
    # お手本の音声
    theme_audio_file = open(f"static/theme/{name_to_path[option]}", 'rb')
    theme_image_file = Image.open(f"static/image/{name_to_image[option]}")
    theme_audio_bytes = theme_audio_file.read()
    
    theme_col1, theme_col2 = st.columns([1,1])
    with theme_col1:
        st.image(theme_image_file)
    with theme_col2:
        st.caption("お題は…")
        st.header(f"「{option}」")
        st.audio(theme_audio_bytes)

    st.markdown("---")

    record()    # 録音画面

#テスト