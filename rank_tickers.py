import pandas as pd
from datetime import datetime, timedelta
from data_handler import StockDataHandler

from technical_analysis import bolin_check2, bolin_check3
from query_openai import check_gpt

def rank_calculate(df):
    df['ROE_Rank'] = df['ROE'].rank(ascending=False, method='min')

    # PM 기준으로 등수 매기기
    df['PM_Rank'] = df['PM'].rank(ascending=False, method='min')
    #df['EY_Rank'] = df['EY'].rank(ascending=False, method='min')

    # 두 등수의 합산 등수 매기기
    df['Total_Rank'] = df['ROE_Rank'] + df['PM_Rank']
    #df['Total_Rank'] = df['ROE_Rank'] + df['EY_Rank']

    # 합산 등수로 정렬
    df_sorted = df.sort_values('Total_Rank')
    
    #print(df_sorted)
    return df_sorted

def get_period():
    current_date = datetime.now()
    result_date = current_date - timedelta(days=500)

    end_date = current_date.strftime('%Y-%m-%d')
    start_date = result_date.strftime('%Y-%m-%d')
    return start_date, end_date

def bollinger_techniques2(df):
    count = 0
    result_list = []  # 결과를 담을 리스트 선언
    for code, name in zip(df['Code'], df['Name']) :
        try:
            if count > 500 :
                return 
            
            count = count + 1
            #print(code, count)
            start, end = get_period()
            formatted_number = str(code).zfill(6)
            print(formatted_number)
            data_handler = StockDataHandler(formatted_number, start, end)
            if data_handler.check_valid_data() == False:
                continue 
            
            daily_df = data_handler.get_daily_data()
            if bolin_check2(daily_df):
                print('wow:' + str(code))
                result_list.append((str(code), str(name)))  
                print(result_list)
        
        except Exception as e:    
            print("raise error ", e)
            count = count + 1
            
    print(result_list) 
    return result_list

def bollinger_techniques3(df):
    count = 0
    result_list = []  # 결과를 담을 리스트 선언
    for code, name in zip(df['Code'], df['Name']) :
        try:
            if count > 500 :
                return 
            
            count = count + 1
            #print(code, count)
            start, end = get_period()
            formatted_number = str(code).zfill(6)
            print(formatted_number)
            data_handler = StockDataHandler(formatted_number, start, end)
            if data_handler.check_valid_data() == False:
                continue 
            
            daily_df = data_handler.get_daily_data()
            if bolin_check3(daily_df):
                print('wow:' + str(code))
                result_list.append((str(code), str(name)))  
                print(result_list)
        
        except Exception as e:    
            print("raise error ", e)
            count = count + 1
            
    print(result_list) 
    return result_list

def openai_techniques1(df):
    count = 0
    result_list = []  # 결과를 담을 리스트 선언
    for code, name in zip(df['Code'], df['Name']) :
        try:
            if count > 250 :
                break
            
            count = count + 1
            #print(code, count)
            start, end = get_period()
            formatted_number = str(code).zfill(6)
            print(formatted_number)
            probability, message = check_gpt(formatted_number)

            if probability > 60 :
                print('wow probability:' + str(probability))
                result_list.append({
                    "code": str(code), 
                    "name": str(name), 
                    "probability": str(probability), 
                    "message": message
                }) 
        except Exception as e:    
            print("raise error ", e)
            count = count + 1    
    print(result_list) 
    return result_list

def get_last_total_df():
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = "df_sorted.csv"
    print(filename)
    df = pd.read_csv(filename, sep='\t', encoding='utf-8')
    return df


if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    df = get_last_total_df()
    
    # # ROE 기준으로 등수 매기기
    df_sorted = rank_calculate(df)
    bollinger_techniques2(df_sorted)
    

