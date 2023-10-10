import pandas as pd
import datetime

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
# 显示所有行
pd.set_option('display.max_rows', None)

df1 = pd.read_csv(filepath_or_buffer='sh600000上.csv', encoding='gbk')
df2 = pd.read_csv(filepath_or_buffer='sh600000下.csv', encoding='gbk')

df = df1._append(df2, ignore_index=True)
df = df[['股票代码', '交易日期', '开盘价', '最高价', '最低价', '收盘价', '涨跌幅', '后复权价', '前复权价']]
df.drop_duplicates(keep='first', inplace=True, ignore_index=True)
df['交易日期'] = pd.to_datetime(df['交易日期'])
df.sort_values(by=['交易日期'], inplace=True, ignore_index=True)
# print(df)
# exit(0)

# sum = 0
# for i in df:
#     print(i['交易日期'])
#     if i['交易日期'].dt.dayofweek == 1:
#         sum += i['涨跌幅']
# average = sum/df.shape[0]
# print(average)
# print(df['交易日期'].dt.year)

#
# print(sum/df.shape[0])
# print(df[df['涨跌幅']>0.05]['涨跌幅'].count())
# print((df[(df['交易日期'].dt.year == 2016)]['涨跌幅']+1).prod()-1)
# print(df[df['交易日期'].dt.dayofweek == 1]['涨跌幅'].mean())
#
df['最近20个交易日最高价'] = df['最高价'].rolling(20).max()
df['最近20个交易日最低价'] = df['最低价'].rolling(20).max()
condition = df['收盘价'] > df['最高价'].rolling(window=20).max().shift(1)
# df['zuida'] = df['收盘价'].rolling(window=20, min_periods=1).max()
# print(condition)
df.loc[condition, '标记点'] = '买入点'

condition = df['收盘价'] < df['最低价'].rolling(20).min().shift(1)
df.loc[condition, '标记点'] = '卖出点'
print(df)
# df['最近20个交易日最高价'] = df['最高价'].rolling(20).max()
# idx = df[df['收盘价'] > df['最近20个交易日最高价'].shift()].index
# print(idx)
# df['最近20个交易日最高价'] = df['最高价'].rolling(20).max()
# print(df['收盘价'] > df['最近20个交易日最高价'].shift())

# condition = df['收盘价'].shift > df['最近20个交易日最高价']
# print(condition)
# df.loc[condition, '标记点'] = 1
# print(df)