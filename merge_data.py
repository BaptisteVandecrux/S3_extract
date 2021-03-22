#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 13:45:06 2020

@author: bav
"""

# %%  Loading data
import pandas as pd
import numpy as np
import os
import subprocess

if 'data_all' in locals():
    del data_all 

for folder in os.listdir('out'):
    print(folder)
    if os.path.exists('out/'+folder+'/out1'):
        for filename in os.listdir('out/'+folder+'/out1'):
            if filename.endswith(".csv"):
                station = os.path.splitext(filename)[0]
                data1 = pd.read_csv('out/'+folder+'/out1/'+station+'.csv') 
                data1 = data1[data1.solar_flux_band_1 != -1]
        
                data2 = pd.read_csv('out/'+folder+'/out2/'+station+'.csv') 
                
                if (data1.shape[0] != data2.shape[0]):
                    print('Warning: out1 and out2 of different length')
                    
                data = pd.merge(data1,data2, how='inner',
                                left_on=['dayofyear','hour','minute'],
                                right_on=['dayofyear','hour','minute'])
                                   
                    
                data['site'] = station
                cols = list(data)
                cols.insert(0, cols.pop(cols.index('site')))
                data = data.loc[:, cols]
                if 'data_all' in locals():
                    data_all=pd.concat([data_all, data])
                else:
                    data_all=data
                    

                    
# %% section 2
out_name='S3_PROMICE_28072020'
data_all.to_csv(out_name+'.csv')

batcmd='../Dropbox-Uploader/dropbox_uploader.sh upload '+out_name+'.csv /'
result = subprocess.check_output(batcmd, shell=True)
print(result)
