from matplotlib import pyplot as plt
from matplotlib.path import Path 
import numpy as np
import matplotlib.patches as patches
import pylab

def find_all(arr, test):
    """ 
    find_all(arr, test) -> list of tuples
    
    Return a list containing the indices of the objects in **arr** that satisfy **test**.
    
    Parameters
    ----------
    arr: 2D NumPy array
    test: boolean function
    """
    indices = []
    for i in range(arr.shape[0]):
        for index, item in enumerate(arr[i]):
            if test(item):
                indices.append((i, index))
    return indices

def draw_matrix(arr, color_code={}):
    """
    Draws **arr** as a grid and colors it according to **key**.
    
    Parameters
    ----------
    arr: 2D NumPy array
    color_code: dictionary
    """
    
    # create figure and subplot
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
        
    # format the subplot
    ax.set_xlim(0, arr.shape[1])
    ax.set_ylim(0, arr.shape[0])

    ax.set_xticks([])
    ax.set_yticks([])

    # draw the grid
    for i in range(arr.shape[0]):
        ax.plot([0, arr.shape[1]], [i, i], color='#424242')
    for j in range(arr.shape[1]):
        ax.plot([j, j], [0, arr.shape[0]], color='#424242')
    
    # color the cells
    codes = [Path.MOVETO,
         Path.LINETO,
         Path.LINETO,
         Path.LINETO,
         Path.CLOSEPOLY,
         ]
    
    for key in color_code:
        indices = find_all(arr, lambda x: x == key)
        verts_list = [[(idx[1], idx[0]), (idx[1]+1, idx[0]), (idx[1]+1, idx[0]+1), (idx[1], idx[0]+1), (0, 0)] for idx in indices]
        path_list = [Path(verts, codes) for verts in verts_list]
        
        for path in path_list:
            patch = patches.PathPatch(path, facecolor=color_code[key], lw=1)
            ax.add_patch(patch)
            
    # set the origin on the upper-left corner
    x = pylab.gca()
    ax.set_ylim(ax.get_ylim()[::-1]) 