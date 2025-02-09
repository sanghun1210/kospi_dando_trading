from openai import OpenAI
from datetime import datetime, timedelta
from data_handler import StockDataHandler
import re

def dataframe_to_text(df):
    return df.to_string()

def ask_openai_with_dataframe(prompt, df):
    try:
        # 데이터프레임을 텍스트 형식으로 변환
        df_text = dataframe_to_text(df)
        #print(df_text)

        # 데이터프레임을 포함한 프롬프트 구성
        full_prompt = f"{prompt}\n\nHere is the relevant data:\n{df_text}\n\n"
        
        client = OpenAI(api_key='')
        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", "content": 
                    """너는 경험 많은 주식 애널리스트야. 고객에게 시장 분석과 투자 전략을 제공하되, 데이터 기반 근거를 제시하고, 구체적인 수치나 통계를 포함해. 고객의 수준에 맞춘 설명을 하고, 불필요한 정보는 배제해. 최신 금융 트렌드를 반영해 대답하도록 해.반드시 답변 템플릿을 활용해서 답변.
<template>
설명 : [설명]
상승 확률: [확률]%
</template>
"}"""
                },
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ]
        )
        print(completion.choices[0].message)
        return completion.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

def check_gpt(code):
    current_date = datetime.now()
    result_date = current_date - timedelta(days=35)
    end_date = current_date.strftime('%Y-%m-%d')
    start_date = result_date.strftime('%Y-%m-%d')
    
    #print(end_date)
    data_handler = StockDataHandler(code, start_date, end_date)
    weekly_df = data_handler.get_weekly_data()
    #print(weekly_df.tail())
    
    query = """최근 주봉 캔들 패턴과 거래량을 기반으로 가까운 미래의 상승 확률을 예측해 주세요. 
    가장 우선순위를 두는 캔들은 최신 주봉입니다. 현재 국내 주식 시장을 바라보는 시각이 좋지만은 않습니다.
    답변은 최신 주봉의 캔들 패턴과 이후 상승 확률을 알려주세요"""
    
    #print('ask openai')
    message = ask_openai_with_dataframe(query, weekly_df)
    
    probability = re.search(r"상승 확률:\s*(\d+)%", message)
    probability_value = int(probability.group(1)) if probability else None
    #print(probability_value)
    return probability_value, message
    
if __name__ == "__main__":
    check_gpt('019180')
    