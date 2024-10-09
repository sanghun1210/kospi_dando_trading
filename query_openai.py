from openai import OpenAI

def dataframe_to_text(df):
    return df.to_string(index=False)

def ask_openai_with_dataframe(prompt, df):
    try:
        # 데이터프레임을 텍스트 형식으로 변환
        df_text = dataframe_to_text(df)

        # 데이터프레임을 포함한 프롬프트 구성
        full_prompt = f"{prompt}\n\nHere is the relevant data:\n{df_text}\n\n"
        
        client = OpenAI()

        # OpenAI API로 요청 보내기
        # print('create')
        # response = client.Completion.create(
        #     engine="gpt-4o-mini",
        #     prompt=full_prompt,  # 사용자 질의 + 데이터프레임 텍스트
        #     temperature=0.7  # 출력의 다양성 정도
        # )
        
        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", "content": "너는 경험 많은 주식 애널리스트야. 고객에게 시장 분석과 투자 전략을 제공하되, 데이터 기반 근거를 제시하고, 구체적인 수치나 통계를 포함해. 고객의 수준에 맞춘 설명을 하고, 불필요한 정보는 배제해. 최신 금융 트렌드를 반영해 대답하도록 해."},
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ]
        )
        print(completion.choices[0].message)

        # # 응답 텍스트 반환
        # print(response.choices[0].text.strip())
        # return response.choices[0].text.strip()

    except Exception as e:
        return f"Error: {str(e)}"

def check_gpt(code):
    code = '101000'
    current_date = datetime.now()
    result_date = current_date - timedelta(days=30)
    end_date = current_date.strftime('%Y-%m-%d')
    start_date = result_date.strftime('%Y-%m-%d')
    
    print(end_date)
    data_handler = StockDataHandler(code, '2024-01-10', '2024-09-19')
    daily_df = data_handler.get_weekly_data()
    print(daily_df.tail())
    
    query = "주봉 캔들 패턴, 거래량을 바탕으로 가까운 미래에 상승 확률을 예측해서 알려줘."
    #query = "9월 23일에 거래량과 일봉 캔들 패턴을 바탕으로 70%이상 상승할것이라고 예측했는데 9월 26일자 기준으로 보면 하락했어. 차트를 기준으로 원인을 분석해줘. 그리고 9월 23일자 기준으로 과매수였나? 과매수였다는것은 어떻게 판단해? 상승중 거래량이 감소했나?"
    
    print('ask openai')
    ask_openai_with_dataframe(query, daily_df)
    
    daily_df.to_string(index=False)