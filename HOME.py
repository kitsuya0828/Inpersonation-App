import streamlit as st
from streamlit.logger import get_logger
from streamlit.components.v1 import html

LOGGER = get_logger(__name__)


st.set_page_config( # TODO
    page_title="ホーム | ぽいネ！",
    page_icon="🎶",
)

st.caption("新感覚ものまね採点アプリ")
st.title("ぽいネ！")
st.sidebar.success("プレイモードを選んでください")

st.markdown(
    """
    **「ぽいネ！」** は、あなたの**ものまね**を採点できるアプリです。
    
    バラエティ豊かなお題を2つのモードでプレイすることができます。
    """
)
st.info("👈 サイドバーからプレイモードを選んで「ものまね」に挑戦してみましょう！")

with st.expander("👤 シングルモード（端末１台でプレイ）", expanded=True):
# st.markdown("#### 👤 シングルモード（端末１台でプレイ）")
  single_col1, single_col2 = st.columns([2, 1])
  with single_col1:
    st.caption("▼ こんな人にオススメ！")
    st.markdown("""
        * 1人で練習したい
        * 近くにいる友だち・家族と勝負したい
    """)
  with single_col2:
    st.image("static/description/single_mode_resized.jpg")

with st.expander("👥 マルチモード（人数分の端末でプレイ）", expanded=True):
# st.markdown("#### 👥 マルチモード（人数分の端末でプレイ）")
  multi_col1, multi_col2 = st.columns([2, 1])
  with multi_col1:
    st.caption("▼ こんな人にオススメ！")
    st.markdown("""【オンラインで】友だち・家族と勝負したい""")
  with multi_col2:
    st.image("static/description/multi_mode_resized.jpg")

st.markdown("---")

# SNSシェアボタン
html("""<a href="https://twitter.com/share?ref_src=twsrc%5Etfw" class="twitter-share-button" data-size="large" data-hashtags="スティーブじょぶつ" data-url="https://kitsuya0828-inpersonation-app-app-2qumms.streamlitapp.com/" data-text="１人でも複数人でもワイワイ楽しめる！\n新感覚ものまね自動採点アプリ\n" data-lang="ja" data-show-count="false">Tweet</a><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
<div class="fb-share-button" data-href="https://kitsuya0828-inpersonation-app-app-2qumms.streamlitapp.com/" data-layout="button" data-size="large"><a target="_blank" href="https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fkitsuya0828-inpersonation-app-app-2qumms.streamlitapp.com%2F&amp;src=sdkpreparse" class="fb-xfbml-parse-ignore">シェアする</a></div><div id="fb-root"></div><script async defer crossorigin="anonymous" src="https://connect.facebook.net/ja_JP/sdk.js#xfbml=1&version=v14.0" nonce="yGPVy76g"></script>
<style type="text/css">.fb_iframe_widget > span {vertical-align: baseline !important;}</style>""")