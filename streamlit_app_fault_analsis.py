import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import itertools
import os
import glob
import datetime

#mpl.font_manager.fontManager.addfont('./SimHei.ttf') #临时注册新的全局字体
plt.rcParams['font.sans-serif'] = ['SimHei'] # 步骤一（替换sans-serif字体）
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 18  #设置字体大小，全局有效

#设置页面标题
st.title("故障分析")
#添加文件上传功能
st.header("文件导入")
uploaded_datafile = st.file_uploader("🟦上传故障清单",type=["xlsx","csv"])

def fig_above():
    x = df_info_aft.index.to_list()
    y1 = df_info_aft[col_list[0]]
    fig, ax1 = plt.subplots(figsize=(16, 9))
    # 调整右侧边界，使其更靠近图形的左侧，从而在图形右侧留下更多的空白。
    # 值越小，右侧空白越大。默认值为1。
    fig.subplots_adjust(right=0.8)  # 例如，将右边界设置为整个图形宽度的80%

    # 绘制第一个数据集
    ax1.plot(x, y1, 'b-')
    ax1.set_xlabel('时间')
    ax1.set_ylabel(col_list[0], color='b')
    ax1.tick_params('y', colors='b')
    plt.xticks(date_list1,np.arange(0,interval_time1,1))
    plt.grid()

    for j in range(1,len(col_list)):
        # 创建第二个Y轴
        cols = col_list[j]
        y2 = df_info_aft[cols]

        ax2 = ax1.twinx()
        ax2.plot(x, y2, color=color_list[j])
        ax2.set_ylabel(cols, color=color_list[j])
        ax2.tick_params('y', colors=color_list[j])

        # 调整ax3位置，为了不与ax2重叠
        ax2.spines['right'].set_position(('outward', 60*(j-1)))

    plt.title(tid + "@" + act_time.strftime("%Y-%m-%d %H:%M") + '故障后数据曲线')
    plt.show()
    st.pyplot(fig)
    
def fig_parallel():
    fig = plt.figure(figsize=(16,9))
    
    ax1 = plt.subplot(len(col_list),1,1)
    df_info_aft[col_list[0]].plot()
    #plt.hlines(df_info_aft['instrumentspeed'].mean(),xmax=14000,xmin=0,linestyles='-.')
    #plt.ylim(50,100)
    plt.ylabel(col_list[0])
    plt.grid()
    
    for i in range(1,len(col_list)):
        ax2 = plt.subplot(len(col_list),1,i+1, sharex=ax1)
        df_info_aft[col_list[i]].plot()
        plt.ylabel(col_list[i])
        
        plt.grid()

    plt.xlabel('时间/h')
    #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(date_list1,np.arange(0,interval_time1,1))
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.suptitle(tid + "@" + act_time.strftime("%Y-%m-%d %H:%M") + '故障后数据曲线')
    plt.show()
    st.pyplot(fig) 
#文件导入
#如果有文件上传，显示数据表格
if uploaded_datafile is not None:
    file_name = uploaded_datafile.name
    if file_name.endswith('.xlsx'):
        dfa = pd.read_excel(uploaded_datafile)
    if file_name.endswith('.csv'):
        dfa = pd.read_csv(uploaded_datafile)

    st.write('🟦原始数据：',dfa.head())

    tid_list = list(set(dfa['编号（风机编号）'].values))
    tid = st.selectbox('✅风机编号',tid_list)
    df = dfa.loc[dfa['编号（风机编号）'] == tid]
    st.write('🟦' + tid + '故障列表：',df)
    
    faultid_list = df.index.to_list()
    option1 = st.selectbox('✅故障编号',faultid_list)
    st.write('🟦故障：',df[df.index == option1])
    
    time1 = df['停机时间'][int(option1)]        

    #files = glob.glob('D:/python/simulation/故障查询/' + tid + '/' + "*.csv")
    st.header("导入详细数据")
    file = st.file_uploader("🟦导入详细数据",type=["xlsx","csv"])
    st.write('🟦数据列表：',file)
    data_file_name = file.name
    
    if time1.strftime("%Y%m") not in data_file_name:
        print('数据不含故障所在时间，请重新上传')
    else:    
        df_info = pd.read_csv(file,encoding='gbk')
    #df_info = pd.DataFrame()
    #for file in files:
        #dfx = pd.read_csv(file,encoding='gbk')
        #df_info = df_info.append(dfx)
        st.write('🟦' + tid + '详细数据：',df_info.head())

        df_info['time'] = pd.to_datetime(df_info['时间'])
        df_info = df_info.set_index('time').sort_index(ascending=True) #日期升序
        columns_list = df_info.columns.to_list()

        st.header("数据清洗")
        date_clear = st.selectbox('✅数据清洗',['是','否'])
        if date_clear=='否':
            col_list_std = st.multiselect('✅选择信号',columns_list)
            for k in range(len(col_list_std)):
                col = col_list_std[k]
                max_val = df[col].max()
                min_val = df[col].min()
                data_range = st.select_slider(col + "范围",min_val,max_val,(min_val,max_val),key = str(k+1))

                df_info[col]= df_info[col].apply(lambda x: np.nan if (x>data_range[1]) or (x<data_range[0]) else x)

        df_info.fillna(method = 'pad',inplace = True)
        #df_info = df_info.dropna(how = 'any').reset_index(drop = True)#删除空行
        interval_time = st.number_input('✅请输入故障前时长',key = '3')

        bef_time = time1 - datetime.timedelta(hours=interval_time)
        act_time = time1
        df_info_bef = df_info.truncate(bef_time,act_time)

        # 向上取整到下一个小时
        rounded_datetime = bef_time - datetime.timedelta(minutes=bef_time.minute)
        date_list = pd.date_range(rounded_datetime, periods = interval_time, freq ='1H') 

        st.header("数据可视化")
        st.write('🟦故障前数据曲线：',)
        fig1 = plt.figure(figsize=(16,9))
        ax1 = plt.subplot(311)
        df_info_bef['风速1[m/s]'].plot()
        #plt.hlines(df_info_bef['instrumentspeed'].mean(),xmax=14000,xmin=0,linestyles='-.')
        #plt.ylim(50,100)
        plt.ylabel('风速1[m/s]')
        plt.grid()

        ax2 = plt.subplot(312, sharex=ax1)
        df_info_bef['发电机有功功率反馈(PCS)[kW]'].plot()
        #plt.scatter(df_info_bef.loc[df_info_bef['扭矩百分比%']>90].index,df_info_bef.loc[df_info_bef['扭矩百分比%']>90,'instrumentspeed'],color = 'r',s=10)
        plt.ylabel('发电机有功功率反馈(PCS)[kW]')
        #plt.ylim(600,1700)
        plt.grid()

        ax3 = plt.subplot(313, sharex=ax1)
        df_info_bef['桨叶1桨距角A反馈[deg]'].plot(label = '桨叶1桨距角A')
        df_info_bef['桨叶2桨距角A反馈[deg]'].plot(label = '桨叶2桨距角A')
        df_info_bef['桨叶3桨距角A反馈[deg]'].plot(label = '桨叶3桨距角A')
        #plt.ylim(80,105)
        #plt.yticks(range(80,105,10))
        plt.ylabel('桨距角A反馈[deg]')
        plt.grid()
        plt.legend()

        plt.xlabel('时间/h')
        #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(date_list,np.arange(interval_time*(-1),0,1))
        plt.subplots_adjust(wspace=0, hspace=0)
        plt.suptitle(tid + "@" + act_time.strftime("%Y-%m-%d %H:%M") + '故障前数据曲线')
        plt.tight_layout()
        st.pyplot(fig1) 

        st.set_option('deprecation.showPyplotGlobalUse', False)#屏蔽警告

        interval_time1 = st.number_input('✅请输入故障后时长',key = '4')
        aft_time = time1 + datetime.timedelta(hours=interval_time1)
        df_info_aft = df_info.truncate(act_time,aft_time)
        # 向上取整到下一个小时
        rounded_datetime1 = act_time - datetime.timedelta(minutes=act_time.minute)
        date_list1 = pd.date_range(rounded_datetime1, periods = interval_time1, freq ='1H') 

        st.write('🟦故障前数据曲线：',)
        fig2 = plt.figure(figsize=(16,9))
        ax1 = plt.subplot(311)
        df_info_aft['风速1[m/s]'].plot()
        #plt.hlines(df_info_aft['instrumentspeed'].mean(),xmax=14000,xmin=0,linestyles='-.')
        #plt.ylim(50,100)
        plt.ylabel('风速1[m/s]')
        plt.grid()

        ax2 = plt.subplot(312, sharex=ax1)
        df_info_aft['发电机有功功率反馈(PCS)[kW]'].plot()
        #plt.scatter(df_info_aft.loc[df_info_aft['扭矩百分比%']>90].index,df_info_aft.loc[df_info_aft['扭矩百分比%']>90,'instrumentspeed'],color = 'r',s=10)
        plt.ylabel('发电机有功功率反馈(PCS)[kW]')
        #plt.ylim(600,1700)
        plt.grid()

        ax3 = plt.subplot(313, sharex=ax1)
        df_info_aft['桨叶1桨距角A反馈[deg]'].plot(label = '桨叶1桨距角A')
        df_info_aft['桨叶2桨距角A反馈[deg]'].plot(label = '桨叶2桨距角A')
        df_info_aft['桨叶3桨距角A反馈[deg]'].plot(label = '桨叶3桨距角A')
        #plt.ylim(80,105)
        #plt.yticks(range(80,105,10))
        plt.ylabel('桨距角A反馈[deg]')
        plt.grid()
        plt.legend()
        #plt.xlim(20000,)
        plt.xlabel('时间/h')
        #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(date_list1,np.arange(0,interval_time1,1))
        plt.subplots_adjust(wspace=0, hspace=0)
        plt.suptitle(tid + "@" + act_time.strftime("%Y-%m-%d %H:%M") + '故障后数据曲线')
        st.pyplot(fig2)     

        st.write('🟦故障后其他数据曲线：',)
        col_list = st.multiselect('✅选择信号',columns_list)
        st.write('🟦选择 {}。'.format(col_list))

        color_list = [
        'orange',  
        'green', 
        'red',           
        'black',                                    
        'brown',                                   
        'cyan',                         
        'gold',                          
        'gray',
        'pink',  
        'white',         
        'yellow',  
        'olive', 
        'silver',                         
        'lime',                                                 
        'khaki',                                              
        'orchid',        
        'peru',                              
        'plum',                                                      
        'salmon',                                                    
        'tan',                  
        'teal',                 
        'thistle',              
        'tomato',               
        'turquoise',            
        'violet',               
        'wheat',
        'navy',                 
        'oldlace',              
        'burlywood',                             
        'ivory']

        fig_type_list = ['堆叠','平行']
        fig_type = st.selectbox('✅图表类型',fig_type_list)
        if fig_type=='堆叠':
            fig_above()
        if fig_type=='平行':
            fig_parallel()