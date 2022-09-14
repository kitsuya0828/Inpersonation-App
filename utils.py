import numpy as np
import numpy
import librosa
import plotly.graph_objs as go
from collections import defaultdict


# GitHub: https://github.com/z2e2/fastddtw
def est_derivatives(sig):
    '''
    Computing drivative differences between dx and dy
    Arguments:
           sig -- signal, numpy array of shape ( n,  )
    Result:
         d_sig -- estimated derivatives of input signal, numpy array of shape ( n-2,  )
    '''
    assert len(sig) >= 3, '''The length of your signal should be 
                           greater than 3 to implement DDTW.'''
    if type(sig) != numpy.ndarray :
        sig = np.array(sig)
    d_0 = sig[:-2]
    d_1 = sig[1:-1]
    d_2 = sig[2:]
    d_sig = ((d_1 - d_0) + (d_2 - d_0)/2)/2
    return d_sig


def generate_window(len_d_sig1, len_d_sig2, K):
    '''
    generate reduced search space
    Arguments:
           len_d_sig1 -- length of signal 1, scalar
           len_d_sig2 -- length of signal 2, scalar
                    K -- window size is 2 * K, scalar
    Result:
               window -- reduced search space, a python generator
    '''
    for i in range(len_d_sig1):
        lb = i - K
        ub = i + K
        if lb < 0 and ub < len_d_sig2:
            for j in range(ub):
                yield (i + 1, j + 1)
        elif lb >= 0 and ub < len_d_sig2:
            for j in range( lb, ub ):
                yield (i + 1, j + 1)
        elif lb < 0 and ub >= len_d_sig2:
            for j in range(len_d_sig2):
                yield (i + 1, j + 1)
        elif lb >= 0 and ub >= len_d_sig2:
            for j in range( lb, len_d_sig2):
                yield (i + 1, j + 1)


def fast_ddtw(signal_1, signal_2, K = 10):
    '''
    Arguments:
        signal_1 -- first time series, numpy array of shape ( n1,  )
        signal_2 -- second time series, numpy array of shape ( n2,  )
    Results:
        ddtw -- distance matrix, numpy array of shape ( n1 - 2, n2 - 2 )
        ddtw_traceback -- traceback matrix, numpy array of shape ( n1 - 2, n2 - 2 )
    ''' 
   
    d_sig1 = est_derivatives(signal_1)
    d_sig2 = est_derivatives(signal_2)
    
    len_d_sig1, len_d_sig2 = len(d_sig1), len(d_sig2)
    if K > abs(len_d_sig1 -  len_d_sig2):
        window = generate_window( len_d_sig1, len_d_sig2, K )
    else:
        K = 2*abs(len_d_sig1 -  len_d_sig2)
        window = generate_window( len_d_sig1, len_d_sig2, K)
        print('input K is not a good choice... selected K = ', K, 'instead.')
    
    D = defaultdict(lambda: (float('inf'),))
    D_max = 0   # maximum of the distance matrix
    D[0, 0] = (0, 0, 0)
    for i, j in window:
        dt = abs(d_sig1[i-1] - d_sig2[j-1])
        D[i, j] = min((D[i-1, j][0]+dt, i-1, j), (D[i, j-1][0]+dt, i, j-1),
                      (D[i-1, j-1][0]+dt, i-1, j-1), key=lambda a: a[0])
        D_max = max(D_max, D[i, j][0])
    path = []
    i, j = len_d_sig1, len_d_sig2
    while not (i == j == 0):
        path.append((i-1, j-1))
        i, j = D[i, j][1], D[i, j][2]
    path.reverse()
    return (D[len_d_sig1, len_d_sig2][0], path, D_max)


def get_line_chart(name_path_dict: dict):
    fig = go.Figure()
    for name, path in name_path_dict.items():
        y, sr = librosa.load(path)
        fig.add_trace(
            go.Scatter(x=[i for i in range(len(y))],
            y=y,
            name=name)
        )
    return fig
