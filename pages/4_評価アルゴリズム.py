import streamlit as st

st.set_page_config(page_title="評価アルゴリズム", page_icon="static/description/favicon.png")

st.header("ものまね評価のアルゴリズムについて")

st.info('やや専門的な内容になります。興味のある方はぜひご覧ください', icon="ℹ️")

st.markdown("突然ですが、あなたはイヌとネコの声を識別できますか？")
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
**ぽいネ！** では、以下の2つの音響特徴量に基づいて、ものまねの評価を行っています。

---

## 1. Chroma Energy Normalized (CENS)
""")

st.image("static/description/cens_dog_cat.png")

st.markdown("""
音名を周波数軸としてパワーの分布を表現した特徴量を**クロマベクトル**といいます。
クロマベクトルを算出する方法はいくつかありますが、[1]ではSTFTやCQTよりも**CENS**が音楽の特性を
最も安定的に表現できるとされていました。
[2]にクロマベクトルについての非常に分かりやすい解説があったので紹介させていただきます。

[1] [鼻歌検索のための音楽特徴量の抽出と評価](https://proceedings-of-deim.github.io/DEIM2022/papers/C21-4.pdf)

[2] [クロマベクトルって何？ - Speaker Deck](https://speakerdeck.com/fkubota/kuromabekutorututehe)

---
## 2. Zero Crossing Rate (ZCR)
""")

st.image("static/description/zcr_dog_cat.png")

st.markdown("""
波形の中で正の値と負の値がどれくらい切り替わっているか、つまり振幅が0を通過する頻度を表現する
音響特徴量が**ZCR**です。ZCRは音声のnoisinessと捉えられるそうです。[1]では、
高音が多い楽曲では波形の間隔が狭くなってしまうため適切でないとされていましたが、音声認識や
音楽情報検索でよく使われる特徴量であるため、使用することにしました。
（英語ですが）[3]にZCRの求め方と詳しい解説が掲載されていたので紹介させていただきます。

[3] [Zero Crossing Rate - an overview | ScienceDirect Topics](https://www.sciencedirect.com/topics/engineering/zero-crossing-rate)

---
これらの特徴量を用いて、2つの音声の類似度を求めるにはどうすればよいでしょうか？

時系列データ同士の距離・類似度を求める手法としてはユークリッド距離やマンハッタン距離が有名だと思いますが、
これらの方法では形状が同じで位相がずれているデータに対して距離が大きくなってしまいます。

---
## DTW (Dynamic Time Warping)

**DTW**（動的時間伸縮法）は、2つの時系列の各点の距離を総当たりで求めた上で、2つの時系列
が最短となるパスを見つけます。これにより、時系列同士の長さや周期が違っても類似度を求める
ことができます。直観的で分かりやすい解説記事を2つほど紹介させていただきます。

[4] [DTW\(Dynamic Time Warping\)動的時間伸縮法 – S\-Analysis](https://data-analysis-stats.jp/%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92/dtwdynamic-time-warping%E5%8B%95%E7%9A%84%E6%99%82%E9%96%93%E4%BC%B8%E7%B8%AE%E6%B3%95/)

[5] [動的時間伸縮法 / DTW \(Dynamic Time Warping\) を可視化する \- StatsFragments](https://sinhrks.hatenablog.com/entry/2014/11/14/232603)

---
## DDTW (Derivative DTW)

DTWが数値の誤差そのものに着目していたのに対し、**DDTW**は時系列の変化具合に着目した手法です。
DDTWは、上昇トレンドや下降トレンドなどの形状を捉えた情報を加味して類似度を計測することができます。
[6]に分かりやすい解説記事を紹介させていただきます。

[6] [時系列データを比較する方法\-Derivative DTW, DTW\- \- Qiita](https://qiita.com/tee_shizuoka/items/2ac9e6eda39664ca8345)

#### Fast DDTW

類似度の計算時間を短くするために、DDTWを高速にした実装が**Fast DDTW**です。
DDTWの時間計算量はDTWと同じく$$O(n^2)$$ですが、動的計画法を用いたFast DTWは$$O(n)$$
と非常に高速です。[7]のGitHubのソースコードを参考に、**ぽいネ！** でもFast DDTWを採用しました。

[7] [z2e2/fastddtw](https://github.com/z2e2/fastddtw)

""")

