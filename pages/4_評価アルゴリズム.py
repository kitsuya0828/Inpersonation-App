import streamlit as st

st.set_page_config(page_title="評価アルゴリズム", page_icon="📊")

st.header("ものまね評価のアルゴリズムについて")

st.info('やや専門的な内容になります。興味のある方はぜひご覧ください', icon="ℹ️")

st.markdown("あなたはイヌとネコの声を識別できますか？")
st.image("static/description/dog_cat.png")
st.markdown("""
人間であれば音声を耳で聞くだけで簡単に識別できると思います。
では、人間がどうやってそのように識別できているか説明できますか？\n
イヌやネコの声に対する固定観念を無くしてみると、「イヌの方が**声が大きい**」
「ネコの方が**声が高い**」などといった特徴があると言えます。
あるいは両者の**音色**の違いにも着目できるかもしれません。（音の三要素）\n

一方でコンピュータは、音声から直接イヌやネコの特徴を掴むことができないため、
扱いやすいように数値にする必要があります。このように音の特徴を表した数値を
**音響特徴量**といいます。\n

イメージしやすい「声の大きさ」と「声の高さ」以外にも様々な音響特徴量が提案されています。
**ManeCo（まねこ）** では、以下の3つの音響特徴量に基づいて、ものまねの評価を行っています。

---

## 1. Chroma Energy Normalized (CENS)

音名を周波数軸としてパワーの分布を表現した特徴量を**クロマベクトル**といいます。
クロマベクトルを算出する方法はいくつかありますが、[1]ではSTFTやCQTよりも**CENS**が音楽の特性を
最も安定的に表現できるとされていました。
[2]にクロマベクトルについての非常に分かりやすい解説があったので紹介させていただきます。

[1] [鼻歌検索のための音楽特徴量の抽出と評価](https://proceedings-of-deim.github.io/DEIM2022/papers/C21-4.pdf)

[2] [クロマベクトルって何？ - Speaker Deck](https://speakerdeck.com/fkubota/kuromabekutorututehe)

---
## 2. Zero Crossing Rate (ZCR)
波形の中で正の値と負の値がどれくらい切り替わっているか、つまり振幅が0を通過する頻度を表現する
音響特徴量が**ZCR**です。ZCRは音声のnoisinessと捉えられるそうです。[1]では、
高音が多い楽曲では波形の間隔が狭くなってしまうため適切でないとされていましたが、音声認識や
音楽情報検索でよく使われる特徴量であるため、使用することにしました。
（英語ですが）[3]にZCRの求め方と詳しい解説が掲載されていたので紹介させていただきます。

[3] [Zero Crossing Rate - an overview | ScienceDirect Topics](https://www.sciencedirect.com/topics/engineering/zero-crossing-rate)

---
## 3. メル周波数ケプストラム係数 (MFCC)





---
以上3つの特徴量を用いて、2つの音声の類似度を求めるにはどうすればよいでしょうか？


---
## DTW (Dynamic Time Warping)

---
## DDTW (Derivative DTW)

""")

