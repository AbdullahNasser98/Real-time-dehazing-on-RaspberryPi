#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Created on Sun Dec  2 17:09:33 2018
    
    @author: Fate
    """

import cv2
import math
import numpy as np
import os
import matplotlib.pyplot as plt
from imutils.video import VideoStream
import time

def Dark_channel(img,r):
    win_size = 2*r + 1
    B,G,R = cv2.split(img)
    temp = cv2.min(cv2.min(B,G),R)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(win_size,win_size))
    dark = cv2.erode(temp,kernel)
    return dark

def AL_estimation(img,dark_channel):
    h,w = img.shape[:2]
    img_size = h*w
    num_pixel = int(max(math.floor(img_size/1000),1))
    
    img_temp = img.reshape(img_size,3)
    dark_temp = dark_channel.reshape(img_size,1)
    
    index = dark_temp[:,0].argsort()
    index_use = index[img_size-num_pixel:]
    
    AL_sum = np.zeros([1,3])
    for i in range(num_pixel):
        AL_sum = AL_sum + img_temp[index_use[i]]
        
    AL = AL_sum/num_pixel
    thread = np.array([[0.95,0.95,0.95]])
    A = cv2.min(AL,thread)
    return A

def Trans_estimation(img, A, r, omega):
    #omega = 0.95
    img_temp = np.empty(img.shape, img.dtype)
    for i in range(3):
        img_temp[:,:,i] = img[:,:,i]/A[0,i]
    trans = 1 - omega*Dark_channel(img_temp, r)
    return trans

def Guided_filter(I,p,r,eps):
    mean_I = cv2.boxFilter(I, cv2.CV_64F, (r,r))
    mean_p = cv2.boxFilter(p, cv2.CV_64F, (r,r))
    corr_I = cv2.boxFilter(I*I, cv2.CV_64F, (r,r))
    corr_Ip = cv2.boxFilter(I*p, cv2.CV_64F, (r,r))
    
    var_I = corr_I - mean_I*mean_I
    cov_Ip = corr_Ip - mean_I*mean_p
    
    a = cov_Ip / (var_I + eps)
    b = mean_p - a*mean_I
    
    mean_a = cv2.boxFilter(a, cv2.CV_64F, (r,r))
    mean_b = cv2.boxFilter(b, cv2.CV_64F, (r,r))
    
    q = mean_a * I + mean_b
    
    return q

def supermaxmin(a, w):
    """
    # a: array to compute filter over
    # w: window width
    """
    maxpath, minpath = deque((0,)), deque((0,))
    lena = len(a)
    maxvalues = [None]*(lena-w+1)
    minvalues = [None]*(lena-w+1)
    for i in range(1, lena):
        if i >= w:
            maxvalues[i-w] = a[maxpath[0]]
            minvalues[i-w] = a[minpath[0]]
        if a[i] > a[i-1]:
            maxpath.pop()
            while maxpath:
                if a[i] <= a[maxpath[-1]]:
                    break
                maxpath.pop()
        else:
            minpath.pop()
            while minpath:
                if a[i] >= a[minpath[-1]]:
                    break
                minpath.pop()
        maxpath.append(i)
        minpath.append(i)
        if i == (w+maxfifo[0]):
            maxpath.popleft()
        elif i == (w + minpath[0]):
            minpath.popleft()
        maxvalues[lena-w] = a[maxpath[0]]
        minvalues[lena-w] = a[minpath[0]]
    
    return minvalues

def dehaze(img, r, n = 8, thre = 0.1, eps = 0.001, omega = 0.80):    
    #img_pro = img.astype('float64')/255
    img_pro = np.float64(img)/255
    J_dark = Dark_channel(img_pro, r)
    A = AL_estimation(img_pro, J_dark)
    t = Trans_estimation(img_pro, A, r, omega)
    
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray = np.float64(img_gray)/255
    t_ref = Guided_filter(img_gray,t,r*n,eps)
    
    t_thre = cv2.max(t_ref, thre)
    result = np.empty(img_pro.shape, img_pro.dtype)
    for i in range(3):
        result[:,:,i] = (img_pro[:,:,i]-A[0,i])/t_thre + A[0,i]
    
    return result

# extract frames from video
cap = cv2.VideoCapture("http://192.168.8.174:8000/stream.mjpg")
#cap = cv2.VideoCapture(0)
#vs = VideoStream(src=0).start()

while(True):
    _, frame = cap.read()
    #frame = cv2.resize(frame, ())

    J = dehaze(frame, 5, n=8)
    
    #cv2.imshow('before', frame)
    cv2.imshow('After',J)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    #cv2.imwrite("video_extract/video" + "_%d.png" % frame_count, frame, params)
cap.release()
cv2.destroyAllWindows()
# # dehaze every frame
# for number in range(1,frame_count+1):
#     print('Dehazing frame: No.',number)
#     im_file = os.path.join('video_extract', 'video_'+str(number)+'.png')
#     img = cv2.imread(im_file)
#     J = dehaze(img, 5, n=8)
#     im_file = os.path.join('dehazed_pic', 'video_'+str(number)+'.png')
#     #plt.imshow(img)
#     # plt.savefig(im_file)
#     cv2.imwrite(im_file,J*255)
#     # etai.write(img,im_file)

# # build video from frames
# fps = 30
# demo = cv2.imread('video_extract/video_1.png')
# demo = np.min(demo, axis = 2)
# size = demo.shape
# size = (size[1],size[0])
# print('Building Video......')
# cap = cv2.VideoWriter("target_video(dehazed)95.avi",cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, size)
# for i in range(1,frame_count+1):
#     im_file = os.path.join('dehazed_pic', 'video_'+str(i)+'.png')
#     img = cv2.imread(im_file)
#     cap.write(img)
# cap.release()

'''
img = cv2.imread('video_extract/video_1.png')
J = dehaze(img, 4, n=8)
cv2.imwrite('dehazed_pic1.png',J*255)
'''