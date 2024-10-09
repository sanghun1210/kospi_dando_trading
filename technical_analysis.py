#볼린저 추세추종기번
#주가의 %b와 주가의 MFI가 기준값보다 높게 상승
# %b가 0.8 MFi(10) 80보다 커야 한다.
import pandas as pd
import numpy as np


# 볼린저 밴드와 %b 계산
def calculate_bollinger_bands(df, window=20):
    df['MA'] = df['trade_price'].rolling(window).mean()
    df['STD'] = df['trade_price'].rolling(window).std()
    df['Upper_Band'] = df['MA'] + (df['STD'] * 2)
    df['Lower_Band'] = df['MA'] - (df['STD'] * 2)
    df['%b'] = (df['trade_price'] - df['Lower_Band']) / (df['Upper_Band'] - df['Lower_Band'])
    return df

# MFI(10) 계산
def calculate_mfi(df, window=10):
    # Typical Price
    df['Typical_Price'] = (df['high_price'] + df['low_price'] + df['trade_price']) / 3

    # Raw Money Flow
    df['Raw_Money_Flow'] = df['Typical_Price'] * df['volume']

    # Positive and Negative Money Flow
    df['Positive_Flow'] = np.where(df['Typical_Price'] > df['Typical_Price'].shift(1), df['Raw_Money_Flow'], 0)
    df['Negative_Flow'] = np.where(df['Typical_Price'] < df['Typical_Price'].shift(1), df['Raw_Money_Flow'], 0)

    # Money Flow Ratio
    df['Money_Flow_Ratio'] = df['Positive_Flow'].rolling(window).sum() / df['Negative_Flow'].rolling(window).sum()

    # MFI
    df['MFI'] = 100 - (100 / (1 + df['Money_Flow_Ratio']))

    return df

def bolin_check2(df) :
    # 볼린저 밴드 및 %b 계산
    df = calculate_bollinger_bands(df)
    
    # MFI 계산
    df = calculate_mfi(df)

    # %b > 0.8 and MFI > 80 필터링
    print(df['%b'].iloc[-1], df['MFI'].iloc[-1])
    if (df['%b'].iloc[-1] > 0.75) and (df['MFI'].iloc[-1] > 80) :
        print('wow')
        return True
    return False



    
    