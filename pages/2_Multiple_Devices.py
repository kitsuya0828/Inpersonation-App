import streamlit as st
from audiorecorder import audiorecorder
from ddtw import DDTW
import numpy as np
import pandas as pd
import json
import librosa
import time
import uuid
from google.cloud import firestore, storage
from datetime import timedelta, datetime

st.set_page_config(page_title="複数の端末でプレイする", page_icon="👥")

root_url = "https://kitsuya0828-inpersonation-app-app-azumamulti-challenge-u1f74q.streamlitapp.com"
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

db = firestore.Client.from_service_account_info(cert)
client = storage.Client.from_service_account_info(cert)


def reset():
    "セッションを初期化する"
    for key in st.session_state.keys():
        del st.session_state[key]


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
    st.markdown("# オンラインで友だちと一緒にプレイしよう！")
    st.image("static/image/ac_cat.jpg")
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
                st.components.v1.html(f'<a href="{root_url}/Multiple_Devices/" target="_blank">ホストになる</a>')
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
    audio = audiorecorder("クリックして録音する", "録音中...", f"recorder")

    if len(audio) > 0:
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
    "いろいろな特徴量を抽出した辞書を返す"
    features_dict = {}
    y_trimmed, _ = librosa.effects.trim(y=y, top_db=25)  # 無音区間削除
    y = librosa.util.normalize(y_trimmed)  # 正規化
    features_dict["chroma_cens"] = librosa.feature.chroma_cens(y=y, sr=sr)
    features_dict["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(y=y)
    for k, v in features_dict.items():
        features_dict[k] = v.flatten()  # 多次元配列を1次元配列に変換する（改善の余地あり）
    return features_dict


def show_result():
    st.session_state["finished"] = True
    update_submission_info()
    ss_dict = st.session_state
    name_state_dict = ss_dict["recorded"]

    result_list = []
    for name, state in name_state_dict.items():
        if state == "recorded":
            bucket = client.bucket(f'{cert["project_id"]}.appspot.com')
            blob = bucket.blob(f"audio/{ss_dict['session_id']}/{name}.wav")
            blob.download_to_filename(
                f"static/audio/{name}_{st.session_state['tmp_id']}.wav")

            player_y, player_sr = librosa.load(f"static/audio/{name}_{st.session_state['tmp_id']}.wav")
            player_features = extract_features(player_y, sr=player_sr)

            with open("static/theme/name_to_path.json", encoding="utf-8") as f:
                name_to_path = json.load(f)
            theme_y, theme_sr = librosa.load(
                f"static/theme/{name_to_path[ss_dict['theme']]}")
            theme_features = extract_features(theme_y, sr=theme_sr)

            score = {}
            with st.spinner(f'{name}のスコアを計算中...'):
                for key in player_features.keys():
                    gamma_mat, arrows, _ = DDTW(
                        player_features[key], theme_features[key])
                    ddtw_eval = 1 - (gamma_mat[-1][-1] / np.array(gamma_mat).max())
                    score[key] = ddtw_eval
            score["player_name"] = name
            result_list.append(score)

    st.write("▼ 結果")
    df = pd.DataFrame.from_dict(result_list)
    df['total_score'] = (3 * df["chroma_cens"] + 7 * df["zero_crossing_rate"]) / 10
    df_indexed = df.set_index("player_name")

    df_sorted = df_indexed.sort_values(by="total_score", ascending=False)
    st.balloons()
    st.dataframe(df_sorted)    # TODO: リッチにする


if "registered" not in st.session_state:
    reset()
    register()
else:
    if "finished" not in st.session_state:
        st.markdown("# Are you ready?")
        if st.session_state["role"] == "host":
            st.success(f'URLの作成に成功しました。現在のURLを友だちに共有してください。', icon="✅")

        st.session_state["tmp_id"] = uuid.uuid4()   # 録音音声の一時保存用ID

        with open("static/theme/name_to_path.json", encoding="utf-8") as f:
            name_to_path = json.load(f)
        theme_name = st.session_state['theme']
        st.session_state["theme_path"] = f"static/theme/{name_to_path[theme_name]}"
        st.write(f"▼ お手本：{theme_name}")
        theme_audio_file = open(f"static/theme/{name_to_path[theme_name]}", 'rb')
        theme_audio_bytes = theme_audio_file.read()
        st.audio(theme_audio_bytes)

    if "finished" not in st.session_state:
        record()
        st.markdown("---")
    
    if "finished" not in st.session_state:
        count_down((st.session_state["deadline"] - datetime.now()).seconds)

st.sidebar.header("複数の端末でプレイする")

st.markdown("---")
st.components.v1.html(
    f'<a href="{root_url}/Multiple_Devices/" target="_blank">最初からプレイする</a>')

# st.session_state
