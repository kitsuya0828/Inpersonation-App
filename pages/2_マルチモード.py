import streamlit as st
from audiorecorder import audiorecorder
from utils import fast_ddtw
import numpy as np
import pandas as pd
import json
import librosa
import librosa.display
import time
import uuid
import plotly.graph_objs as go
import matplotlib.pyplot as plt
from PIL import Image
from google.cloud import firestore, storage
from datetime import timedelta, datetime
from streamlit.components.v1 import html

st.set_page_config(page_title="マルチモード | ぽいネ！", page_icon="static/description/favicon.png")

root_url = "https://kitsuya0828-inpersonation-app-home-aaa1x7.streamlitapp.com"
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

# データベースの初期化
db = firestore.Client.from_service_account_info(cert)
client = storage.Client.from_service_account_info(cert)


def reset():
    "セッションを初期化する"
    for key in st.session_state.keys():
        del st.session_state[key]


def reset_query_params():
    "クエリパラメータを初期化する"
    reset()
    st.experimental_set_query_params(
        session_id = ""
    )


def join():
    "Participantのための参加処理"
    if len(st.session_state["session_id"]) > 0 and len(st.session_state["user_name"]) > 0:
        # userコレクションに追加
        doc_ref_user = db.collection("user").document(
            st.session_state["session_id"])
        docs = doc_ref_user.get()
        user_info = docs.to_dict()["name_state"]

        if st.session_state["user_name"] in user_info:  # 名前が既に使用されていた場合
            st.session_state["name_already_used"] = True
            return
        elif "name_already_used" in st.session_state:  # 既に使用されていた名前を変更した場合
            del st.session_state["name_already_used"]

        user_info[st.session_state["user_name"]] = "registered"
        doc_ref_user.update({'name_state': user_info})

        st.session_state["role"] = "participant"
        st.session_state["registered"] = True


def host():
    "Hostのための開催処理"
    if len(st.session_state["session_id"]) > 0 and len(st.session_state["user_name"]) > 0:
        # sessionコレクションに追加
        doc_ref_session = db.collection("session").document(st.session_state["session_id"])
        expiration_date = (datetime.now() + timedelta(seconds=5*60))  # セッション有効期限（5分）
        doc_ref_session.set({
            'expiration_date': expiration_date.strftime('%Y-%m-%d %H:%M:%S'),
            'host_name': st.session_state["user_name"],
            'state': "valid",
            'theme': st.session_state["theme"]
        })

        # userコレクションに追加
        doc_ref_user = db.collection("user").document(st.session_state["session_id"])
        doc_ref_user.set({'name_state': {st.session_state["user_name"]: "registered"}})

        # クエリパラメータにセッションIDを指定する
        st.experimental_set_query_params(session_id=st.session_state["session_id"])
        st.session_state["deadline"] = expiration_date
        st.session_state["role"] = "host"
        st.session_state["registered"] = True


def register():
    "情報登録のための処理"
    register_col1, register_col2 = st.columns([5, 1])
    with register_col1:
        st.header("オンラインで友だちと一緒にプレイしよう！")
    with register_col2:
        st.image("static/description/multi_mode_register.jpg")
    st.info("👈 遊び方はサイドバーをご覧ください")
    query_params_dict = st.experimental_get_query_params()

    if "session_id" in query_params_dict:
        # sessionコレクションを参照
        try:
            doc_ref_session = db.collection("session").document(query_params_dict["session_id"][0])
            docs = doc_ref_session.get()
            session_info = docs.to_dict()
            expiration_date = datetime.strptime(
                session_info["expiration_date"], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expiration_date:  # セッションの有効期限切れ
                st.error(f'セッションの有効期限（{session_info["expiration_date"]}）が切れています', icon="🚨")
                st.button("もう一度最初からプレイする", on_click=reset_query_params)
            else:
                st.session_state["session_id"] = query_params_dict["session_id"][0]
                st.session_state["user_name"] = st.text_input("▼ ニックネームを入力してください", placeholder="※ 必須")
                st.session_state["theme"] = session_info["theme"]
                st.session_state["deadline"] = expiration_date
                join_button = st.button("参加する", on_click=join)
                if join_button:
                    if len(st.session_state["user_name"]) == 0:
                        st.error("１文字以上のニックネームを入力してください", icon="🚨")
                    if "name_already_used" in st.session_state:
                        st.error("このニックネームは既に使用されています", icon="🚨")

        except Exception as e:
            print(e)
            st.error("無効なセッションです", icon="🚨")

    else:
        st.session_state["session_id"] = str(uuid.uuid4())  # セッションのID
        st.session_state["user_name"] = st.text_input("▼ ニックネームを入力してください", placeholder="※ 必須")
        with open("static/theme/name_to_path.json", encoding="utf-8") as f:
            name_to_path = json.load(f)
            st.session_state["theme"] = st.selectbox('▼ モノマネするお題を選んでください', name_to_path.keys())
        
        # 試聴用
        with open("static/image/name_to_image.json", encoding="utf-8") as f:
            name_to_image = json.load(f)
        try_theme_image_file = Image.open(f"static/image/{name_to_image[st.session_state['theme']]}")
        
        try_theme_audio_file_ = open(f"static/theme/{name_to_path[st.session_state['theme']]}", 'rb')
        try_theme_audio_bytes_ = try_theme_audio_file_.read()
        
        try_col1, try_col2 = st.columns([1, 1])
        with try_col1:
            st.image(try_theme_image_file)
        with try_col2:
            st.caption("▼ 試聴する")
            st.audio(try_theme_audio_bytes_)
        
        host_button = st.button("主催する", on_click=host)
        if host_button:
            if len(st.session_state["user_name"]) == 0:
                st.error("１文字以上のニックネームを入力してください", icon="🚨")


def count_down(ts):
    "カウントダウンタイマーを表示する"
    with st.empty():
        while ts:
            mins, secs = divmod(ts, 60)
            time_now = '{:02d}:{:02d}'.format(mins, secs)
            st.metric("制限時間", f"{time_now}")
            time.sleep(1)
            ts -= 1
    if "recorded" in st.session_state:  # もし録音済みならば結果画面を表示する
        show_result()
    else:
        st.warning("セッションの有効期限が切れています", icon="⚠️")
        st.session_state["expired"] = True


def update_submission_info():
    "セッション全員の提出状況をアップデートして表示する"
    doc_ref_user = db.collection("user").document(
        st.session_state["session_id"])
    docs = doc_ref_user.get()
    submission_info = docs.to_dict()["name_state"]
    if "recorded" not in st.session_state:
        submission_info[st.session_state["user_name"]] = "recorded"
        doc_ref_user.update({
            'name_state': submission_info
        })
    st.session_state["recorded"] = submission_info


def record():
    "音声を録音する"
    audio = audiorecorder("録音を開始する", "録音を停止する", "recorder")
    
    if len(audio) > 6 * 10**4:
        st.error("録音を短くしてください（目安：5秒以内）", icon="🚨")
    elif len(audio) > 0:
        st.audio(audio)

        file_name = f"static/audio/{st.session_state['tmp_id']}.wav"
        wav_file = open(file_name, "wb")
        wav_file.write(audio.tobytes())

        # 音声をバケットにアップロード
        bucket = client.bucket(f'{cert["project_id"]}.appspot.com')
        blob = bucket.blob(f'audio/{st.session_state["session_id"]}/{st.session_state["user_name"]}.wav')
        blob.upload_from_filename(file_name)

        update_submission_info()

    st.markdown("---")

    if "recorded" in st.session_state and "expired" not in st.session_state:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("最新の提出状況", on_click=update_submission_info)
        with col2:
            st.button("結果を見る", on_click=show_result)
        
        # 他のプレイヤーの「提出済み」or「未提出」を表示
        japanized_recorded = {key: "提出済み" if val == "recorded" else "未提出" for key, val in st.session_state["recorded"].items()}
        st.table(pd.DataFrame([japanized_recorded], index=[(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')]))


def extract_features(y, sr):
    "2つの特徴量を抽出した辞書とグラフを返す"
    features_dict = {}
    y_trimmed, _ = librosa.effects.trim(y=y, top_db=25)  # 無音区間削除
    y = librosa.util.normalize(y_trimmed)  # 正規化
    
    fig, ax = plt.subplots(2, 1, figsize=(8, 12))
    features_dict["chroma_cens"] = librosa.feature.chroma_cens(y=y, sr=sr)
    librosa.display.specshow(features_dict["chroma_cens"], y_axis='chroma', x_axis='time', ax=ax[0])
    
    features_dict["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(y=y)
    ax[1].plot(features_dict["zero_crossing_rate"][0])

    features_path = f"static/tmp/{uuid.uuid4()}.png"
    plt.savefig(features_path)

    for k, v in features_dict.items():
        features_dict[k] = v.flatten()  # 多次元配列を1次元配列に変換する
    return features_dict, y, features_path


def show_result():
    st.session_state["finished"] = True
    update_submission_info()
    ss_dict = st.session_state
    name_state_dict = ss_dict["recorded"]

    result_list = []
    name_path_dict = {}
    features_paths = []
    added_theme = {}
    fig = go.Figure()
    
    for name, state in name_state_dict.items():
        if state == "recorded":
            tmp_file_name = f"static/audio/{name}_{st.session_state['tmp_id']}.wav"
            bucket = client.bucket(f'{cert["project_id"]}.appspot.com')
            blob = bucket.blob(f"audio/{ss_dict['session_id']}/{name}.wav")
            blob.download_to_filename(tmp_file_name)

            player_y, player_sr = librosa.load(tmp_file_name)
            player_features, new_player_y, player_features_path = extract_features(player_y, sr=player_sr)
            name_path_dict[name] = tmp_file_name
            
            fig.add_trace(
                go.Scatter(
                    x=[i for i in range(len(new_player_y))],
                    y=new_player_y,
                    name=name
                )
            )
            features_paths.append((name, player_features_path))     
            

            with open("static/theme/name_to_path.json", encoding="utf-8") as f:
                name_to_path = json.load(f)
            theme_y, theme_sr = librosa.load(f"static/theme/{name_to_path[ss_dict['theme']]}")
            theme_features, new_theme_y, theme_features_path = extract_features(theme_y, sr=theme_sr)
            name_path_dict[ss_dict['theme']] = f"static/theme/{name_to_path[ss_dict['theme']]}"
            if ss_dict["theme"] not in added_theme:
                fig.add_trace(
                    go.Scatter(
                        x=[i for i in range(len(new_theme_y))],
                        y=new_theme_y,
                        name=ss_dict[f"theme"]
                    )
                )
                added_theme[ss_dict["theme"]] = True
                features_paths.append((ss_dict["theme"], theme_features_path))
            
            
            score = {}
            with st.spinner(f'{name}のスコアを計算中...'):
                for key in player_features.keys():
                    # fast DDTW
                    distance, _, D_max = fast_ddtw(player_features[key], theme_features[key])
                    ddtw_eval = 1 - (distance / D_max)
                    
                    score[key] = ddtw_eval
            score["player_name"] = name
            result_list.append(score)

    st.header("結果発表")
    df = pd.DataFrame.from_dict(result_list)
    df['total_score'] = (3 * df["chroma_cens"] + 7 * df["zero_crossing_rate"]) / 10
    df.columns = ["CENS", "ZCR", "プレイヤー名", "合計得点"]
    df_indexed = df.set_index("プレイヤー名")

    df_sorted = df_indexed.sort_values(by="合計得点", ascending=False)
    st.balloons()
    sorted_names = df_sorted.index
    cols = st.columns(len(sorted_names))
    my_standing = "?"
    for i in range(len(sorted_names)):
        name = sorted_names[i]
        cols[i].metric(f"{i+1}位：{name}", f"{int(df_sorted.at[name, '合計得点'] * 100)} 点")
        if name == st.session_state["user_name"]:
            my_standing = i + 1
            
    
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
    st.button("もう一度最初からプレイする", on_click=reset_query_params)
    html(f"""<a href="https://twitter.com/share?ref_src=twsrc%5Etfw" class="twitter-share-button" data-size="large" data-hashtags="ぽいネ" data-url="{root_url}" data-text="新感覚ものまね自動採点アプリ「ぽいネ！」で\n{len(sorted_names)}人中{my_standing}位になりました" data-lang="ja" data-show-count="false">Tweet</a><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>""")


st.sidebar.header("複数の端末でプレイする")
st.sidebar.button("最初からプレイする", on_click=reset_query_params)

st.sidebar.markdown("---")
st.sidebar.caption("▼ 遊び方")
st.sidebar.markdown("""
    1. 【ホストのみ】がお題を決めて「主催する」を押す
    2. 【ホストのみ】生成された（ブラウザの）URLを参加者に共有
    3. 【参加者のみ】URLにアクセスしてプレイヤー名を入力する
    4. お題の音声をよく聴いてから「録音を開始する」でスタート
    5. 「録音を停止する」を押してストップ
    6. 「最新の提出状況」をチェックして全員が「提出済み」になるのを待つ
    7. 「結果を見る」を押す
""")

if "registered" not in st.session_state or ("session_id" in st.session_state and st.session_state["session_id"] == ""):
    reset()
    register()
else:
    if "finished" not in st.session_state:
        if st.session_state["role"] == "host":
            st.success(f'URLの作成に成功しました。ブラウザに表示されているURLを友だちに共有してください。', icon="✅")

        st.session_state["tmp_id"] = uuid.uuid4()   # 録音音声の一時保存用ID

        with open("static/theme/name_to_path.json", encoding="utf-8") as f:
            name_to_path = json.load(f)
        theme_name = st.session_state['theme']
        st.session_state["theme_path"] = f"static/theme/{name_to_path[theme_name]}"
        theme_audio_file = open(f"static/theme/{name_to_path[theme_name]}", 'rb')
        theme_audio_bytes = theme_audio_file.read()
        
        # {動物名：画像ファイルパス}
        with open("static/image/name_to_image.json", encoding="utf-8") as f:
            name_to_image = json.load(f)
        theme_image_file = Image.open(f"static/image/{name_to_image[theme_name]}")
        
        theme_col1, theme_col2 = st.columns([1, 1])
        with theme_col1:
            st.image(theme_image_file)
        with theme_col2:
            st.caption("お題は…")
            st.header(f"「{theme_name}」")
            st.audio(theme_audio_bytes)

    if "finished" not in st.session_state:
        record()
        st.markdown("---")
    
    if "finished" not in st.session_state:
        count_down((st.session_state["deadline"] - datetime.now()).seconds)

st.markdown("---")