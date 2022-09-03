import librosa
import numpy as np

def DDTW(Q, C):
    """
    Args:
        Q (np.array or list): 一つ目の波形
        C (np.array or list): 二つ目の波形

    Returns:
        gamma_mat (np.array): DDTWを計算するための行列
        arrows (np.array): 各時点で←・↙︎・↓のどのマスが最小だったかを示す記号を保存する行列
        ddtw (float): DDTW
    """
    Q, C = np.array(Q), np.array(C)
    assert Q.shape[0] > 3, "一つ目の波形のフォーマットがおかしいです。"
    assert C.shape[0] > 3, "二つ目の波形のフォーマットがおかしいです。"

    # 3.1 Algorithm details の式
    def _Dq(q):
        return ((q[1] - q[0]) + (q[2] - q[0]) / 2) / 2

    # 二つの時点間の距離
    def _gamma(x, y):
        return abs(_Dq(x) - _Dq(y))

    # 各変数
    n, m = Q.shape[0] - 2, C.shape[0] - 2
    gamma_mat = np.zeros((n, m))
    arrows = np.array(np.zeros((n, m)), dtype=str)  # 可視化用の行列でDDTWの値とは無関係

    # 一番左下のスタート地点
    gamma_mat[0, 0] = _gamma(Q[0:3], C[0:3])

    # 一列目を計算
    for i in range(1, n):
        gamma_mat[i, 0] = gamma_mat[i - 1, 0] + _gamma(Q[i - 1 : i + 2], C[0:3])
        arrows[i, 0] = "↓"

    # 一行目を計算
    for j in range(1, m):
        gamma_mat[0, j] = gamma_mat[0, j - 1] + _gamma(Q[0:3], C[j - 1 : j + 2])
        arrows[0, j] = "←"

    # 残りのマスを計算
    for i in range(1, n):
        for j in range(1, m):
            # DDTWを求めるためのマトリクスを埋める
            d_ij = _gamma(Q[i - 1 : i + 2], C[j - 1 : j + 2])
            gamma_mat[i, j] = d_ij + np.min(
                [gamma_mat[i - 1, j - 1], gamma_mat[i - 1, j], gamma_mat[i, j - 1]]
            )
            square_index = np.argmin(
                [gamma_mat[i - 1, j - 1], gamma_mat[i - 1, j], gamma_mat[i, j - 1]]
            )
            # 矢印を書くための行列(DDTWの値とは関係無い処理)
            if (square_index) == 0:
                arrows[i, j] = "↙︎"
            elif square_index == 1:
                arrows[i, j] = "↓"
            elif square_index == 2:
                arrows[i, j] = "←"

    return gamma_mat, arrows, gamma_mat[n - 1, m - 1]
