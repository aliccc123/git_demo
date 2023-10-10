import pandas as pd
sz = pd.read_csv(filepath_or_buffer="sz300001.csv", encoding="gbk",
                 parse_dates=["交易日期"], usecols=['交易日期', '股票代码', '开盘价', '最高价', '最低价', '收盘价', '涨跌幅'])
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', None)
# 将数据按照日期从小到大排序
sz.sort_values(by=["交易日期"], inplace=True)
sz.reset_index(inplace=True, drop=True)

# 计算涨跌幅
sz["我的涨跌幅"] = sz["收盘价"].pct_change()
# print(sz[["涨跌幅", "我的涨跌幅"]])
# print(sz[abs(sz["我的涨跌幅"]-sz["涨跌幅"]) > 0.0001])
# exit(0)

sz['复权因子'] = (sz['涨跌幅']+1).cumprod()
# print(sz)
# print(sz[['涨跌幅', '复权因子', '收盘价']])
#
sz['后复权_收盘价'] = sz['复权因子']*(sz.iloc[0]['收盘价']/sz.iloc[0]['复权因子'])
# print(sz['后复权_收盘价'])
# exit(0)


sz['后复权_开盘价'] = sz['开盘价']/sz['收盘价']*sz['后复权_收盘价']
sz['后复权_最高价'] = sz['最高价']/sz['收盘价']*sz['后复权_收盘价']
sz['后复权_最低价'] = sz['最低价']/sz['收盘价']*sz['后复权_收盘价']
# print(sz[['后复权_收盘价', '后复权_开盘价', '后复权_最高价', '后复权_最低价']])

sz['前复权_收盘价'] = sz['复权因子']*(sz.iloc[-1]['收盘价']/sz.iloc[-1]['复权因子'])
print(sz[['收盘价', '前复权_收盘价']])
exit(0)
sz['前复权_开盘价'] = sz['开盘价']/sz['收盘价']*sz['前复权_收盘价']
sz['前复权_最高价'] = sz['最高价']/sz['收盘价']*sz['前复权_收盘价']
sz['前复权_最低价'] = sz['最低价']/sz['收盘价']*sz['前复权_收盘价']
# print(sz[['前复权_收盘价', '前复权_开盘价', '前复权_最高价', '前复权_最低价']])

# 均线策略
ma_long = 50
ma_short = 5
# 短期均线
sz['ma_short'] = sz['后复权_收盘价'].rolling(ma_short, min_periods=1).mean()
# 长期均线
sz['ma_long'] = sz['后复权_收盘价'].rolling(ma_long, min_periods=1).mean()

# 买入：当短期均线大于长期均线，并且前一日的短期均线小于等于前一日的长期均线
condition1 = sz['ma_short'] > sz['ma_long']
condition2 = sz['ma_short'].shift(1) <= sz['ma_long'].shift(1)
sz.loc[condition1 & condition2, 'signal'] = 1


# 卖出：当短期均线小于长期均线，并且前一日的短期均线大于等于前一日的长期均线
condition1 = sz['ma_short'] < sz['ma_long']
condition2 = sz['ma_short'].shift(1) >= sz['ma_long'].shift(1)
sz.loc[condition1 & condition2, 'signal'] = 0
# 删除无关的列
sz.drop(['ma_short', 'ma_long'], axis=1, inplace=True)

sz = sz[['股票代码', '交易日期', '开盘价', '收盘价', '最高价', '最低价', '涨跌幅', '后复权_开盘价', '后复权_收盘价', '后复权_最高价', '后复权_最低价', 'signal']]
# 设置应是满仓还是空仓
sz['pos'] = sz['signal'].shift()
sz['pos'].fillna(method="ffill", inplace=True)
sz['pos'].fillna(value=0, inplace=True)
# 找出开盘涨停的日期
cond_not_buy = sz['后复权_开盘价'] > sz['后复权_收盘价'].shift(1)*1.097
sz.loc[cond_not_buy & (sz['pos'] == 1), 'pos'] = None
# 找出开盘跌停的日期
cond_not_sell = sz['后复权_开盘价'] < sz['后复权_收盘价'].shift(1)*0.93
sz.loc[cond_not_sell & (sz['pos'] == 0), 'pos'] = None
sz['pos'].fillna(method='ffill', inplace=True)
# print(sz[sz['交易日期'] > pd.to_datetime('20150501')][['交易日期', '涨跌幅', 'signal', 'pos']])
# # print(sz[sz['交易日期'] > pd.to_datetime('20150501')][['交易日期', '涨跌幅', 'signal', 'pos']])
# exit(0)
# 截取上市一年之后的股票数据，一年股票交易天数约为250天
sz = sz.iloc[250-1:]
sz.iloc[0, -1] = 0
sz.reset_index(inplace=True, drop=True)
# print(sz)

# 计算资金曲线（简单方法）
# 先计算资金曲线每天的涨幅
sz['equity_change'] = sz['涨跌幅']*sz['pos']
# print(sz['equity_change'])
# exit(0)
# 计算资金曲线
sz['equity_curve'] = (sz['equity_change']+1).cumprod()

# # sz['equity_curve'] = (sz['equity_change'] + 1).cumprod()
#
# print(sz['equity_curve'])
# exit(0)

# 计算资金曲线实际方法
sz = sz[['交易日期', '股票代码', '开盘价', '最高价', '最低价', '收盘价', '涨跌幅', 'pos']]
# print(sz)
initial_money = 1000000  # 初始资金
slippage = 0.01  # 滑点，默认为0.01
c_rate = 5.0/10000  # 手续费 commission fees 默认为万分之五
t_rate = 1.0/1000  # 印花税 默认为千分之一

# 第一天的情况
sz.at[0, 'hold_num'] = 0  # 持有股票数量
sz.at[0, 'stock_value'] = 0  # 持有股票价值
sz.at[0, 'actual_pos'] = 0   # 每天的实际仓位
sz.at[0, 'cash'] = initial_money    # 每天持有的现金
sz.at[0, 'equity'] = initial_money  # 总资产 = 股票价值 + 现金

# print(sz)
# exit(0)

# 第一天之后的情况
for i in range(1, sz.shape[0]):
    hold_num = sz.at[i-1, 'hold_num']
    # 判断
    if abs((sz.at[i, '收盘价'] / sz.at[i-1, '收盘价'] - 1) - sz.at[i, '涨跌幅']) > 0.001:
        stock_value = sz.at[i - 1, 'stock_value']
        # 交易所会公布除权之后的价格
        last_price = sz.at[i, '收盘价'] / (sz.at[i, '涨跌幅'] + 1)
        hold_num = stock_value / last_price
        hold_num = int(hold_num)

    # 判断是否需要加仓减仓
    if sz.at[i, 'pos'] != sz.at[i-1, 'pos']:
        theory_num = sz.at[i-1, 'equity']*sz.at[i, 'pos']/sz.at[i, '开盘价']
        theory_num = int(theory_num)
        # 加仓
        if theory_num >= hold_num:
            buy_num = theory_num - hold_num
            buy_num = int(buy_num/100)*100

            buy_cash = buy_num*(sz.at[i, '开盘价'] + slippage)

            commission = round(buy_cash*c_rate, 2)  # 手续费
            if commission < 5 and commission != 0:
                commission = 5

            sz.at[i, 'hold_num'] = hold_num + buy_num
            sz.at[i, 'cash'] = sz.at[i-1, 'cash'] - buy_cash - commission
            sz.at[i, '手续费'] = commission
        else:   # 减仓
            sell_num = hold_num - theory_num

            sell_cash = sell_num*(sz.at[i, '开盘价'] - slippage)
            commission = round(max(c_rate * sell_cash, 5), 2)   # 手续费
            tax = round(t_rate * sell_cash, 2)  # 印花税
            sz.at[i, 'hold_num'] = hold_num - sell_num
            sz.at[i, 'cash'] = sz.at[i-1, 'cash'] + sell_cash - commission - tax
            sz.at[i, '手续费'] = commission
            sz.at[i, '印花税'] = tax

            # print(sz.iloc[50:100][['交易日期', '开盘价', 'pos', 'hold_num', 'cash', '手续费', '印花税']])
            # exit(0)
    else:
        sz.at[i, 'cash'] = sz.at[i-1, 'cash']
        sz.at[i, 'hold_num'] = sz.at[i-1, 'hold_num']

    sz.at[i, 'stock_value'] = sz.at[i, 'hold_num']*sz.at[i, '收盘价']
    sz.at[i, 'equity'] = sz.at[i, 'stock_value'] + sz.at[i, 'cash']
    sz.at[i, 'actual_pos'] = sz.at[i, 'stock_value']/sz.at[i, 'equity']

sz = sz[['交易日期', '收盘价', 'pos', 'hold_num', 'cash', 'stock_value', 'equity', 'actual_pos', '手续费', '印花税']]
print(sz)





