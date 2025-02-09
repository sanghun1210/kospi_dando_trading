import pandas as pd
import FinanceDataReader as fdr
import fundametal_analysis
from datetime import datetime, timedelta
from data_handler import StockDataHandler
import csv
from rank_tickers import rank_calculate, bollinger_techniques2, bollinger_techniques3, openai_techniques1

def get_tickers():
    #df_krx = stock.get_market_ticker_list('240818',market='ALL')
    df_krx = fdr.StockListing('KRX')
    with open('tickers.csv','w') as file :
        write = csv.writer(file)
        write.writerow(df_krx)
    return df_krx


# 행 추가 함수 정의
def add_row(df, code, name, roe, pm, ey):
    new_row = pd.DataFrame({'Code': code, 'Name': name, 'ROE': roe, 'PM': pm, 'EY': ey}, index=[0])
    comb = pd.concat([df, new_row])
    return comb

#ROE : 자본이익률
#PM : 이익수익률

def get_period():
    current_date = datetime.now()
    result_date = current_date - timedelta(days=500)

    end_date = current_date.strftime('%Y-%m-%d')
    start_date = result_date.strftime('%Y-%m-%d')
    return start_date, end_date

def get_magic_symbols(code, close_price):
    fa = fundametal_analysis.FundamentalAnalysis(code)
    roe, eps = fa.get_base_financial_data()
    pm = (eps / close_price) * 100
    ey = fa.get_earnings_yield(close_price)
    return roe, pm, ey

def save_list_to_csv(result_list, filename):
    # result_list: [(code, name), (code, name), ...] 형태의 리스트
    # filename: 저장할 파일 이름
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Code', 'Name', '확률'])  # CSV 파일의 헤더 추가
        for item in result_list:
            # Extract values from each dictionary item
            code = item.get('code')
            name = item.get('name')
            probability = item.get('probability')
            message = item.get('message')
            writer.writerow([code, name, probability])

def main():
    df_krx = get_tickers()
    start, end = get_period()
    total_df = pd.DataFrame(columns=['Code', 'Name', 'ROE', 'PM', 'EY'])
    print(len(df_krx))
    for code, name in zip(df_krx['Code'], df_krx['Name']) :
        try:
            print(code)
            data_handler = StockDataHandler(code, start, end)
            if data_handler.check_valid_data() == False:
                continue 
            daily_df = data_handler.get_daily_data()
            roe, pm, ey = get_magic_symbols(code, daily_df['trade_price'].iloc[-1])
            total_df = add_row(total_df, code, name, roe, pm, ey)
        except Exception as e:    
            print("raise error ", e)
            
            
    df_sorted = rank_calculate(total_df)
    df_sorted.to_csv('df_sorted.csv', sep='\t', encoding='utf-8')
    
    #####################
    
    df_sorted = pd.read_csv('df_sorted.csv', sep='\t', encoding='utf-8')
    print(df_sorted)
    result_list = openai_techniques1(df_sorted)
    print(result_list)
    
    save_list_to_csv(result_list, 'openai_results.csv')
    
if __name__ == "__main__":
    # execute only if run as a script
    main()
