from datetime import datetime, timedelta
import pandas as pd

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import requests
import math
from io import StringIO

# 재무 분석에 사용할 주요 지표 3개
# 부채비율 (Debt to Equity Ratio): 기업이 자산 구매를 위해 얼마나 많은 부채를 사용하고 있는지를 나타냅니다. 
# 낮은 부채비율은 기업이 빚을 적게 지고 있으며, 재무적으로 안정적이라는 것을 의미합니다.

# 영업이익률 (Operating Margin): 매출액에서 영업이익이 차지하는 비율을 나타내며, 기업의 핵심 비즈니스가 얼마나 효율적으로 이익을 창출하고 있는지를 보여줍니다. 
# 높은 영업이익률은 기업이 비용을 효율적으로 관리하며, 본질적인 사업에서 좋은 성과를 내고 있음을 의미합니다.

# 자기자본이익률 (Return on Equity, ROE): 자기자본(주주 자본)으로부터 얻은 순이익의 비율을 나타냅니다. 
# ROE는 기업이 주주의 자본을 얼마나 효율적으로 이용하여 수익을 창출하고 있는지를 보여줍니다. 높은 ROE는 기업이 주주 자본을 효과적으로 사용하여 높은 수익을 내고 있음을 의미합니다.

# 저평가 분석에 사용할 주요 지표 3개
# 주가수익비율 (Price to Earnings Ratio, PER): 주가를 주당 순이익(EPS)으로 나눈 값입니다. 낮은 PER은 주가가 주당 이익에 비해 상대적으로 저평가되어 있을 가능성이 있음을 의미합니다.
# 주가순자산비율 (Price to Book Ratio, PBR): 주가를 주당 순자산가치(BPS)로 나눈 값입니다. PBR이 1 이하일 경우, 기업이 그의 순자산가치보다 낮게 거래되고 있으며, 이는 저평가되었을 가능성을 시사합니다.
# 배당수익률 (Dividend Yield): 주당 배당금을 현재 주가로 나눈 값입니다. 높은 배당수익률은 주가 대비 좋은 배당수익을 제공하며, 이는 기업이 저평가되었을 가능성이 있음을 나타낼 수 있습니다. 특히, 안정적인 배당을 지속적으로 제공하는 기업의 경우 더욱 그렇습니다.


class FundamentalAnalysis(object):
    def __init__(self, ticker):
        self.current_eps = 0
        self.current_per = 0
        self.current_bps = 0
        self.current_pbr = 0
        self.current_roe = 0
        self.sector = None
        self.annual_date = None
        self.quater_date = None
        self.df = None
        self.table_token = None
        self.soup = None
        self.get_data_from_fnguide(ticker)
    

    def get_data_from_fnguide(self, ticker):
        try:
            url = f'https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{ticker}&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701'
                    #req.add_header('User-Agent', 'Mozilla/5.0')
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            res = requests.get(url, headers=headers)
            self.soup = BeautifulSoup(res.text, 'html.parser')

            cop = self.soup.select_one('#highlight_D_A')
            self.df = pd.read_html(StringIO(cop.prettify()))[0]
            self.table_token = self.df.columns[0][0]

            if len(self.get_data_lst_by("Net Quarter", "EPS  (원)")) == 0:
                cop = self.soup.select_one('#highlight_B_A')
                self.df = pd.read_html(StringIO(cop.prettify()))[0]
                self.table_token = self.df.columns[0][0]

        except Exception as e:
            self.table_token = None
            # skip_string = "'NoneType' object has no attribute 'prettify'"
            # if skip_string not in e:
            #     print("Error : ", e)   
            # self.table_token = None
        #print(self.df.columns[0][0])
        #print(self.df.iloc[0].iloc[0])
            
    # 숫자로 변환 시도, 실패하면 예외 처리하여 무시
    def safe_float_convert(self, x):
        try:
            return float(x)
        except ValueError:
            return None

    def get_data_lst_by(self, target_cloumn, target_row):
        try:
            if self.table_token == None:
                return None
            field_names = self.df[self.table_token]
            df = self.df.loc[field_names[self.table_token]==target_row]
            # print(df)
            
            data = df[target_cloumn]

            # 특정 열에서 추정치 제거
            # data = data[[col for col in data.columns if '(' not in col]]

            #특정 열에서 결측값 제거
            filtered_data = data.dropna(axis=1)
            filtered_list = []
            for x in filtered_data.iloc[0].tolist():
                converted_x = self.safe_float_convert(x)
                if converted_x != None:
                    filtered_list.append(converted_x)
            return filtered_list
        except Exception as e:
            print("Error : ", e)   
            return None

    # 업종에서 정보 가져오기    
    def get_biz_category_won(self, row, column):
        cop = self.soup.select_one('#upTabDivD')
        df = pd.read_html(StringIO(cop.prettify()))[0]

        table_token = df.columns[0]
        eps_df = df.loc[df[table_token ]==row]
        return eps_df.iloc[0, column]
    
    # 종합 점수 계산 함수
    def calculate_weighted_score(self, data, weights):
        score = 0
        for key in data:
            # 부채비율은 점수가 낮을수록 좋으므로 부채비율의 경우 점수를 반전시킴
            score += data[key] * weights[key]
        return score

        # if lst[-1] < 25:
        #     score += 75
        # elif 25 <= lst[-1] and lst[-1] < 50:
        #     score += 50
        # elif 50 <= lst[-1] and lst[-1] < 80:
        #     score -= 25
        # elif 80 <= lst[-1] and lst[-1] < 150 :
        #     score -= 50
        # else : 
        #     score = -300

        return score

    def find_per(self):
        cop = self.soup.select_one('#corp_group2 > dl:nth-child(1) > dd')
        str = cop.get_text()
        return self.safe_float_convert(str)
    
    def get_financial_analysis_score(self):
        roe_annual_lst = self.get_data_lst_by("Annual", "ROE")
        roe_quater_lst = self.get_data_lst_by("Net Quarter", "ROE")
        om_annual_lst = self.get_data_lst_by("Annual", "영업이익")
        om_quater_lst = self.get_data_lst_by("Net Quarter", "영업이익")
        dte_annual_lst = self.get_data_lst_by("Annual", "부채비율")
        dte_quater_lst = self.get_data_lst_by("Net Quarter", "부채비율")
        eps_quater_lst = self.get_data_lst_by("Net Quarter", "EPS  (원)")

        if roe_annual_lst == None or len(roe_annual_lst) == 0:
            return 0

        # print(dte_annual_lst)
        print(dte_quater_lst)
        # print(om_annual_lst)
        # print(om_quater_lst)
        # print("roe annual list :", roe_annual_lst)
        # print("roe quater list :", roe_quater_lst)
        # print("eps quater list :", eps_quater_lst)

        # print(self.get_biz_category_eps())
        # print(self.get_biz_category())

        roe_annual_score = self.get_base_score(roe_annual_lst)
        roe_quater_score = self.get_base_score(roe_quater_lst)
        om_annual_score = self.get_base_score(om_annual_lst)
        om_quater_score = self.get_base_score(om_quater_lst)
        dte_annual_score = self.debt_to_score(dte_annual_lst)
        dte_quater_score = self.debt_to_score(dte_quater_lst)
        eps_quater_score = self.get_eps_quater_score(eps_quater_lst)

        roe_category_score = 0
        roe_category_score = self.caculate_roe_category_score(self.get_biz_category_roe(), roe_annual_lst[-1])

        data = {'연간영업이익' : om_annual_score, 
            '분기영업이익' : om_quater_score,
            '업종ROE비교' : roe_category_score, 
            '연간ROE' : roe_annual_score,
            '분기ROE' : roe_quater_score,
            '연간부채비율': dte_annual_score,
            #'분기별부채비율': dte_quater_score,
            '분기EPS': eps_quater_score
            }

        #print(data)
        
        weights = {
            '연간영업이익': 0.2,
            '분기영업이익': 0.25,
            '업종ROE비교': 0.2,
            '분기EPS': 0.25,
            '연간ROE': 0.2,
            '분기ROE': 0.2,
            '연간부채비율': 0.05,  
            '분기별부채비율': 0.05
        }
        return self.calculate_weighted_score(data,weights)
    
    def get_per_score(self):
        per = self.find_per()
        per_category = self.find_category_per()

        if per == None or per_category == None:
            return 50

        if per >= per_category:
            return 0
        else:
            return 100

    def get_undervalued_analysis_analysis_score(self):
        pbr_score = self.find_pbr_score()
        per = self.find_per()
        per_category = self.find_category_per()
        per_score = self.get_per_score()

        data = {'PBR' : pbr_score, 
            'PER' : per_score,
            }
        
        #print(data)

        weights = {
            'PBR': 0.5,
            'PER': 0.5
        }
        return self.calculate_weighted_score(data,weights)
    
    def get_base_financial_data(self):
        roe_annual_lst = self.get_data_lst_by("Annual", "ROE")
        eps_annaul_lst = self.get_data_lst_by("Annual", "EPS  (원)")
        #shares = self.get_data_lst_by("Annual", "발행주식수")
        # print(roe_annual_lst)
        # print(eps_annaul_lst)
        # print(shares)

        return roe_annual_lst[-1], eps_annaul_lst[-1]
    
    def get_base_financial_data_by_quater(self):
        roe_annual_lst = self.get_data_lst_by("Net Quarter", "ROE")
        eps_annaul_lst = self.get_data_lst_by("Net Quarter", "EPS  (원)")
        return roe_annual_lst[-1], eps_annaul_lst[-1]

    #이익수익률
    #이익수익률 = 비율= 세전영업이익 (EBIT) / (주가 시가총액+순이자부담부채)
    #24년 예상치와 23년 자료를 짬뽕했는데 이게 맞는건가?

    def get_earnings_yield(self, close_prise):
        #시가총액
        # market_cap = self.get_biz_category_won("시가총액", 1)
        shares_annual_lst = self.get_data_lst_by("Annual", "발행주식수")
        market_cap = (shares_annual_lst[-1] * 1000 * close_prise) / 100000000

        #영업이익
        #om = self.get_biz_category_won("영업이익", 1)
        om_annual_lst = self.get_data_lst_by("Annual", "영업이익")
        om = om_annual_lst[-1]

        #순이자부담부채 
        #부채 - 자본금
        #모든 단위가 억인지 확인이 필요하다.
        dept_annual_lst = self.get_data_lst_by("Annual", "부채총계")
        sc_annual_lst = self.get_data_lst_by("Annual", "자본금")
        nitb = dept_annual_lst[-1] - sc_annual_lst[-1]

        # print(market_cap)
        # print(nitb)
        # print(om)
        ey = om/(market_cap + nitb)
        return ey
    
def main():
    test=FundamentalAnalysis("154040")
    print(test.get_base_financial_data())

    #print(test.get_earnings_yield(20000))

if __name__ == "__main__":
    # execute only if run as a script
    main()



    