from chatchat.server.pydantic_v1 import Field
from .tools_registry import BaseToolOutput, regist_tool
import json
from zhipuai import ZhipuAI
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import time
import difflib
import logging
import requests
from bs4 import BeautifulSoup, NavigableString

intent_labels = [
    'Doctor-Asking-Symptom',
    'Patient-Giving-Symptom',
    'Patient-Consult-Symptom',
    'Doctor-Explain-Disease_Characteristics',
    'Patient-Asking-Etiology',
    'Doctor-Explain-Etiology',
    'Doctor-Asking-Basic_Information',
    'Patient-Giving-Basic_Information',
    'Doctor-Asking-Existing_Examination_and_Treatment',
    'Patient-Giving-Existing_Examination_and_Treatment',
    'Doctor-Explain-Drug_Effects',
    'Patient-Asking-Drug_Recommendation',
    'Doctor-Giving-Drug_Recommendation',
    'Patient-Asking-Medical_Advice',
    'Doctor-Giving-Medical_Advice',
    'Patient-Asking-Precautions',
    'Doctor-Giving-Precautions',
    'Doctor-Asking-Treatment_Intention',
    'Patient-Giving-Treatment_Needs',
    'Doctor-Diagnose',
    'Patient-Asking-Diagnosis_Result',
    'Doctor-Explain-Diagnosis_Result',
    'Doctor-Summarizing_Symptom',
    'Reassure',
    'Patient-Confirm',
    'Patient-Other_Feedback',
    'Greet',
    'Patient-Greet',
    'Confirm'
]
intent_expl = {
    "Patient-Giving-Symptom":"患者可能患有的疾病的其他症状相关资料",
    "Patient-Consult-Symptom":"选出上文提到的症状的详细解释和影响，表明了什么问题等相关资料。",
    "Patient-Asking-Etiology":"上文提到的病症的患病原因资料",
    "Patient-Giving-Basic_Information":"选出上文提到的病症还需要哪些基础信息辅助确诊的相关内容",
    "Patient-Giving-Existing_Examination_and_Treatment":"请选出目前病人需要做哪些检查的参考资料。",
    "Patient-Asking-Drug_Recommendation":"选出针对上文病症的药物治疗方案的相关资料",
    "Patient-Asking-Medical_Advice":"选出患者提问的医学问题、医学常识、医疗建议对应的资料",
    "Patient-Asking-Precautions":"对于患者的治疗或用药的注意事项相关资料，或者关于患者的疾病的预防和防止病症加剧的相关资料",
    "Patient-Giving-Treatment_Needs":"对于患者病症的多种治疗方案（比如药物治疗、就诊、注射治疗等）相关资料",
    "Patient-Asking-Diagnosis_Result":"治疗方案的效果，特点相关资料，比如多久见效，治疗到什么程度能说明治疗起效了，是否还有漏诊误诊的可能性等资料",
    "Patient-Confirm":"",
    "Patient-Other_Feedback":"",
    "Patient-Greet":""
}
behavior_dict = [
    'Doctor-Asking-Symptom',
    'Doctor-Explain-Disease_Characteristics',
    'Doctor-Explain-Etiology',
    'Doctor-Asking-Basic_Information',
    'Doctor-Asking-Existing_Examination_and_Treatment',
    'Doctor-Explain-Drug_Effects',
    'Doctor-Giving-Drug_Recommendation',
    'Doctor-Giving-Medical_Advice',
    'Doctor-Giving-Precautions',
    'Doctor-Asking-Treatment_Intention',
    'Doctor-Diagnose',
    'Doctor-Explain-Diagnosis_Result',
    'Doctor-Summarizing_Symptom',
    'Reassure',
    'Confirm',
    'Greet',
    '',
    'Patient-Giving-Symptom',
    'Patient-Consult-Symptom',
    'Patient-Asking-Etiology',
    'Patient-Giving-Basic_Information',
    'Patient-Giving-Existing_Examination_and_Treatment',
    'Patient-Asking-Drug_Recommendation',
    'Patient-Asking-Medical_Advice',
    'Patient-Asking-Precautions',
    'Patient-Giving-Treatment_Needs',
    'Patient-Asking-Diagnosis_Result',
    'Patient-Confirm',
    'Patient-Other_Feedback',
    'Patient-Greet',
    'Patient-'
] # 行为字典
@regist_tool(title="医学知识检索")
def medical_search(query: str = Field(description="query for medical search"))-> str:
    """If a patient asks about their condition or treatment options, you can use this tool to search for medical knowledge and drug information. Please note that this tool can only be used once per session."""
    def bing_search(keywords):

        from langchain.utilities import BingSearchAPIWrapper

        BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
        BING_SUBSCRIPTION_KEY = '9e110a51b2a44bf8bbe1917febefa158'
        search = BingSearchAPIWrapper(bing_subscription_key=BING_SUBSCRIPTION_KEY,
                                        bing_search_url=BING_SEARCH_URL)
        content = []
        # print(search.run("python"))
        #print(search.results("阿托品 site:drugs.dxy.cn/pc/drug", 5))
        drug = []
        content += search.results(f"{keywords} site:drugs.dxy.cn/pc/clinicalDecision", 2)
        content += search.results(f"{keywords} site:www.msdmanuals.cn/home",2)
        content += search.results(f"{keywords} site:drugs.dxy.cn/pc/drug", 1)
        return content


#Use this tool to search for medical knowledge and drug information. Please note that this tool can only be used once per session.
    def create_browser():
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument("--headless")  # 无头模式
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)  
            return driver
    
    def LSTM(actsequence):
        from tensorflow.keras.models import load_model
        from keras.preprocessing.sequence import pad_sequences
        from sklearn.preprocessing import LabelEncoder

        def predict_next_action(model, sequence, max_len, label_encoder):
            encoded_sequence = label_encoder.transform(sequence)
            padded_sequence = pad_sequences([encoded_sequence], maxlen=max_len, padding='pre')
            prediction = model.predict(padded_sequence, verbose=0)
            return prediction
        
        max_len = 20
        model_filename = 'model_epoch_65.keras'
        model = load_model(model_filename)
        label_encoder = LabelEncoder()
        label_encoder.fit(behavior_dict)
        probabilities = predict_next_action(model, actsequence, max_len, label_encoder)
        probabilities_dict = {label_encoder.inverse_transform([i])[0]: prob for i, prob in enumerate(probabilities[0])}
        sorted_seq = sorted(probabilities_dict.items(), key=lambda item: item[1], reverse=True)
        # 打印概率分布
        # for action, prob in sorted_seq:
        #     print(f"{action}: {prob:.2%}")

        
        return sorted_seq
    def dingxiang_content(url,type):
        headers = {
    'Host': 'drugs.dxy.cn',
    'method': 'GET',
    'path': '/',
    'scheme': 'https',
    'accept': '',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'max-age=0',
    'Cookie': 'dxy_da_cookie-id=b794932777029826252f79515cca26491722853650811; Hm_lvt_5fee00bcc4c092fe5331cc51446d8be2=1722518583,1723465617,1723712078,1724771813; _ga_LTBPLJJK75=GS1.1.1724771812.4.0.1724771814.0.0.0; _ga=GA1.2.1276781713.1722515620; _gid=GA1.2.886184748.1725455959; _ga_C1KRQPKH2N=GS1.2.1725455959.10.0.1725455959.0.0.0; CLASS_CASTGC=304ebb79c30edcc3ff5eb551a56407e2890385d26c3c600fa83c4e3b4f0e6f9246d9d96caad89364b246df1d670d5c4e50091bbe6b10ef7f59f5850499b5f543871ab870c1daab3006e3b26c17a87e965b523708135e397065c5845b770d32866d02dc7ec441406794a4927937a21e5e6f7d419354094bc891accbc7bd655a3d72d84cec9bb74f5a878274d7b78ed8fb7efc1a47a4858329f135c08711ca058d2fed9cf3568f4bf458769695cb82bc88dc9b8f4db7cd19f54f72b89a4d8ee0b1f92f42f2bee83c1802c9af0db6895630cc1d8a2b3ab8007390b7bae7fcfc07a41bc89e2c1014baa236c90309643f19833cc25d5aab571d38863c0bcf1e60bcf4; JUTE_BBS_DATA=4f81d2390d699c14b6985a5ab9e3b70332006995917d5478a4746e4cf023105d5b3a901db989141e6c832cd5cff6d5ae69b5f0a4bed0aa8b32f4047b873bfb5b3e8023768a5a050659f091a9d8c7bbbb',
    'priority': 'u=0, i',
    'sec-ch-ua':'"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
}
        extracted_content = {}
        try:
            session = requests.Session()
            response = session.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
            # 等待页面加载完成
            time.sleep(2)  # 根据需要调整等待时间
            # 获取网页内容并使用BeautifulSoup解析
            def content_crawler( element='', extracted_content={}, title_num = 1, type = None):
                if type == 'drug':
                    if  not isinstance(element, NavigableString):
                        content = ''
                        for elementchiled in element.contents:
                            if elementchiled.name is not None and 'h' in elementchiled.name:
                                title = elementchiled.name
                                text = elementchiled.get_text(strip=True)
                                title_num += 1
                                #print(1)
                                #print(text)
                                #print(2)
                                #print(extracted_content)
                                extracted_content[f'h{title_num}标题:{text}'] = {}
                                #print(extracted_content)
                            elif elementchiled.name == 'div' and elementchiled.attrs.get('class', []) == ['page_content__zHHQZ']:
                                #print(3)
                                content +=  elementchiled.get_text(strip=True) + "\n"
                                #print(content)
                                #print(4)
                                #print(extracted_content)
                                extracted_content[f'h{title_num}标题:{text}']["content"] = content
                                #print(extracted_content)
                            # else:
                            #     content_crawler(elementchiled, extracted_content , title_num, 'drug')
                else:
                    if  not isinstance(element, NavigableString):
                        content = ''
                        for elementchiled in element.contents:
                            if elementchiled.name is not None and 'h' in elementchiled.name:
                                title = elementchiled.name
                                text = elementchiled.get_text(strip=True)
                                title_num += 1
                                #print(text)
                                #print(extracted_content)
                                extracted_content[f'h{title_num}标题:{text}'] = {}
                                extracted_content = extracted_content[f'h{title_num}标题:{text}']
                                #print(extracted_content)
                            elif elementchiled.name == 'div' and not elementchiled.attrs.get('data-menu-index', []) and not elementchiled.attrs.get('class', []):
                                #print(1111111111111111111)
                                content +=  elementchiled.get_text(strip=True) + "\n"
                                # print(content)
                                #print(extracted_content)
                                extracted_content["content"] = content
                            else:
                                content_crawler(elementchiled, extracted_content , title_num , 'case')

            title_divs = soup.find('h1')
            title = title_divs .get_text(strip=True) if title_divs  else "未找到标题"
            extracted_content[f'h1总标题:{title}'] = {}
            
            if type == "drug":
                content_div = soup.find_all('div', class_='page_item__3NVRC')
                #print(content_div)
                #print(len(content_div))
                #print(11111111111111111111111111111111)
                for item in content_div:
                    content_crawler( item, extracted_content[f'h1总标题:{title}'],1,'drug')
                #print(extracted_content)
            elif type == "case":
                content_div = soup.find('div', class_='page_fields__ScN7A')
                content_crawler( content_div, extracted_content[f'h1总标题:{title}'],1,'case')

        # title_divs = soup.find('h1')
        # title = title_divs .get_text(strip=True) if title_divs  else "未找到标题"
        # extracted_content[f'h1总标题:{title}'] = {}
        # #print(title)
        # if type == "drug":
        # # 找到内容容器
        #     content_div = soup.find('div', class_='page_drug-content__ncCsP')
        #     if content_div:
        #         for element in content_div.contents:
        #             if 'page_blank-warning__HN6_3' in element.attrs.get('class', []):
        #                 Warning_content = ''
        #                 Warning_content += element.get_text(strip=True)
        #                 extracted_content[f'h1总标题:{title}']["content"] = Warning_content
        #             else:
        #                 h2tittle = ''
        #                 # h3tittle = ''
        #                 content = ''
        #                 for element2 in element:
        #                     if element2.name == 'h2':
        #                         h2tittle = element2.get_text(strip=True)
        #                         extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'] = ''
        #                     else:
        #                         content +=  element2.get_text(strip=True)
        #                 extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'] = content


        #                 # for element2 in element.contents:
        #                 #     if element2.name == 'h2':
        # else:
        # # 找到内容容器
        #     content_div = soup.find('div', class_='page_fields__ScN7A')
        #     if content_div:
        #         for element in content_div.contents:
        #             if element.attrs['class'] == ['page_disease-section__8_tzU']:
        #                 for element2 in element.contents:  #element2包含二级标题h2元素以及对应内容content元素
        #                     h2tittle = ''
        #                     # h3tittle = ''
        #                     #print(element2.attrs['class'])
        #                     #print(element2.name)
        #                     for element3 in element2.contents:
        #                         if element3.name == 'h2':
        #                             h2tittle += element3.get_text(strip=True) 
        #                             print(h2tittle)
        #                             extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'] = {}
        #                         elif element3.name == 'div':
        #                             for element4 in element3.contents: #element4包含三级标题h2元素以及对应内容content元素
        #                                 h3tittle = ''
        #                                 # h3tittle = ''
        #                                 content2 = ''    
        #                                 for element5 in element4.contents:
        #                                     if element5.name == 'h2':
        #                                         h3tittle += element5.get_text(strip=True)
        #                                         print(h3tittle)
        #                                         extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'][f'h3标题:{h3tittle}'] = ''
        #                                     else:
        #                                         h4tittle = ''
        #                                         content3 = ''
        #                                         for element6 in element5:
        #                                             if element5.name == 'h2':
        #                                                 h4tittle += element6.get_text(strip=True)
        #                                                 print(h4tittle)
        #                                                 extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'][f'h3标题:{h3tittle}'][f'h4标题:{h4tittle}'] = ''
        #                                             else:
        #                                                 content3 +=  element6.get_text(strip=True)

        #                                         extracted_content[f'h1总标题:{title}'][f'h2标题:{h2tittle}'][f'h3标题:{h3tittle}'][f'h4标题:{h4tittle}'] = content3
        # except Exception as e:
        #     #捕获所有从标准异常类派生的异常
        #    print(f"An unexpected error occurred: {e}")
        finally:
            return extracted_content     
         
    def msd_content(url):
        extracted_content = {}
        try:
            #driver.get(url)
            # 等待页面加载完成
            time.sleep(2)  # 根据需要调整等待时间
            # 获取网页内容并使用BeautifulSoup解析
        #try:
            session = requests.Session()
            response = session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
            #soup = BeautifulSoup(driver.page_source, 'html.parser')
            title_div = soup.find('h1', class_='readable TopicHead_topicHeaderTittle__miyQz')
            tittle = title_div.get_text(strip=True) if title_div else "未找到标题"
            extracted_content[f'h1总标题:{tittle}'] = {}
            # 找到内容容器
            content_div = soup.find('div', class_='TopicMainContent_content__MEmoN')

            # 初始化一个空字符串用于存储提取的内容

            # 如果找到了内容容器，则开始提取内容
            if content_div:
                # 递归函数用于处理嵌套的section
                def extract_sections(section, fatheritem):
                    tittle = ''
                    content = ''
                    for element in section.contents:
                        if re.match(r'^h[1-6]$', element.name):
                            header_level = element.name  # 例如 'h2'
                            tittle += f'{header_level}标题:' + element.get_text(strip=True)
                            fatheritem[tittle] = {}
                        elif element.name == 'div':
                            for element2 in element.contents:
                                #print(element2.name)
                                if element2.name == 'p':
                                    content += '    ' + element2.get_text(strip=True) + '\n'
                                    #print(element2.get_text(strip=True))
                                elif element2.name == 'ul':
                                    for li in element2.find_all('li'):
                                        content += '    ' +'·' + li.find('p').get_text(strip=True) + '\n'
                                        #print(li.find('p').get_text(strip=True))
                                elif element2.name == 'section':
                                    extract_sections(element2,fatheritem[tittle])
                                    #print(element2.get_text(strip=True))
                        fatheritem[tittle]['content'] = content
                    return None

                # 遍历内容容器下的所有元素
                content = ''
                for element in content_div.contents:
                    #print(element.name)
                    if element.name == 'section':
                        extract_sections(element, extracted_content[f'h1总标题:{tittle}'])
                    elif element.name == 'p':
                        content += '    ' + element.get_text(strip=True) + '\n'
                    elif element.name == 'ul':
                        for li in element.find_all('li'):
                            content += '    ' +'·' + li.find('p').get_text(strip=True) + '\n'
                    extracted_content[f'h1总标题:{tittle}']['content'] = content     
                #         extracted_content += extract_sections(element)
                # for element in content_div.contents:
                #     print(content_div.contents)
                #     if element.name == 'p':
                #         extracted_content += element.get_text(strip=True) + '\n'

                #     elif element.name == 'ul':
                #         for li in element.find_all('li'):
                #             extracted_content += li.find('p').get_text(strip=True) + '\n'
                #     elif element.name == 'section':
                #         extracted_content += extract_sections(element)

            # 打印标题和内容
            #print(title)
            #print(title + '\n' + extracted_content + '\n\n')
        finally:
            #driver.close()
            return extracted_content
    
    def dingxiang_crawler(symptom):

        def dingxiang_mulpage_crawler(url, type):
            content = ''
            try:
                headers = {
    'Host': 'drugs.dxy.cn',
    'method': 'GET',
    'path': '/',
    'scheme': 'https',
    'accept': '',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'max-age=0',
    'Cookie': 'dxy_da_cookie-id=b794932777029826252f79515cca26491722853650811; Hm_lvt_5fee00bcc4c092fe5331cc51446d8be2=1722518583,1723465617,1723712078,1724771813; _ga_LTBPLJJK75=GS1.1.1724771812.4.0.1724771814.0.0.0; _ga=GA1.2.1276781713.1722515620; _gid=GA1.2.886184748.1725455959; _ga_C1KRQPKH2N=GS1.2.1725455959.10.0.1725455959.0.0.0; CLASS_CASTGC=304ebb79c30edcc3ff5eb551a56407e2890385d26c3c600fa83c4e3b4f0e6f9246d9d96caad89364b246df1d670d5c4e50091bbe6b10ef7f59f5850499b5f543871ab870c1daab3006e3b26c17a87e965b523708135e397065c5845b770d32866d02dc7ec441406794a4927937a21e5e6f7d419354094bc891accbc7bd655a3d72d84cec9bb74f5a878274d7b78ed8fb7efc1a47a4858329f135c08711ca058d2fed9cf3568f4bf458769695cb82bc88dc9b8f4db7cd19f54f72b89a4d8ee0b1f92f42f2bee83c1802c9af0db6895630cc1d8a2b3ab8007390b7bae7fcfc07a41bc89e2c1014baa236c90309643f19833cc25d5aab571d38863c0bcf1e60bcf4; JUTE_BBS_DATA=4f81d2390d699c14b6985a5ab9e3b70332006995917d5478a4746e4cf023105d5b3a901db989141e6c832cd5cff6d5ae69b5f0a4bed0aa8b32f4047b873bfb5b3e8023768a5a050659f091a9d8c7bbbb',
    'priority': 'u=0, i',
    'sec-ch-ua':'"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
    }
                session = requests.Session()
                response = session.get(url, headers=headers)
                time.sleep(4)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                #print(soup)
                # 解析每个cookie对并创建一个cookie字典列表
                # cookies = []
                # for pair in cookie_pairs:
                #     name, value = pair.split('=', 1)
                #     cookie_dict = {
                #         'name': name,
                #         'value': value,
                #         # 通常情况下，以下字段是可选的，如果需要，可以手动添加
                #         # 'domain': '.example.com',  # cookie适用的域名
                #         # 'path': '/',  # cookie适用的路径
                #         # 'expiry': None,  # cookie的过期时间戳
                #         # 'secure': False  # cookie是否只通过HTTPS传输
                #     }
                #     cookies.append(cookie_dict)
                #driver.get(url)
                # for cookie in cookies:
                #     driver.add_cookie(cookie)
                #cookies = driver.get_cookies()
                #for cookie in cookies:
                    # print(cookie)
                # 等待页面加载完成
                #time.sleep(2)  # 根据需要调整等待时间
                # 获取网页内容并使用BeautifulSoup解析
                #soup = BeautifulSoup(driver.page_source, 'html.parser')
                #title_divs = soup.find('h1')
                # title = 'h1总标题：'
                # title = 'h1总标题：' + title_divs .get_text(strip=True) if title_divs  else "未找到标题"
                #print(title)
                # xpath_expression = """
                #             //div[contains(@class, 'undefined')]//li[contains(@class, 'TextItem_text-box___fEDe')]/a[contains(@class, 'TextItem_link__b9JOr')]
                #             """
                # links = driver.find_elements(By.XPATH, xpath_expression)
                if type == "case":
                # 找到内容容器
                    content_div = soup.find_all('a', class_='TextItem_link__b9JOr')
                    #print(content_div)
                    if content_div:
                        for link in content_div:
                            extracted_content = ""
                            extracted_tittle = ""
                            href = 'https://drugs.dxy.cn/' + link.attrs.get('href', [])
                            for child in link:
                                if 'TextItem_box-title___sGxi' in child.attrs.get('class', []):
                                    extracted_tittle += '标题:' + child.get_text(strip=True)
                                else:
                                    extracted_content += child.get_text(strip=True) 
                            content += '[' + extracted_tittle + ':' + '[' + extracted_content + ']'+ "  链接：" + '[' +href + ']'+ ']' + '\n'

                elif type == "drug":
                # 找到内容容器
                    content_div = soup.find_all('a', class_='DrugsPcItem_link__yoWUS')
                    #print(content_div)
                    if content_div:
                        for link in content_div:
                            extracted_content = ""
                            extracted_tittle = ""
                            href = 'https://drugs.dxy.cn' + link.attrs.get('href', [])
                            for child in link:
                                if 'DrugsPcItem_drugs-item-name__nufpq' in child.attrs.get('class', []):
                                    extracted_tittle += '标题:' + child.get_text(strip=True)
                                else:
                                    extracted_content += child.get_text(strip=True) 
                            content += '[' + extracted_tittle + ':' + '[' + extracted_content + ']'+ "  链接：" + '[' +href + ']'+ ']' + '\n' 
                
                

            # 关闭浏览器
            finally:
                print('dxy内容')
                print(content)
                return content

        try:
            content = ''
            symptom_less = []
            for index, content in enumerate(symptom):
                if index == 0 or index == 2:
                    symptom_less.append(content)
            for symp in symptom_less:
                url = 'https://drugs.dxy.cn/pc/search?keyword=' + symp +'&type=clinicalDecision&querySpellCheck=true' 
                print(url)
                content += dingxiang_mulpage_crawler(url,'case') + '\n'
                #content += dingxiang_mulpage_crawler(url + "&page=2",driver,'case')+ '\n'
                url = 'https://drugs.dxy.cn/pc/search?keyword=' + symp + '&type=drug&querySpellCheck=true'
                print(url)
                content += dingxiang_mulpage_crawler(url,'drug') + '\n'
                #content += dingxiang_mulpage_crawler(url + "&page=2",driver,'drug')+ '\n' 
            # except KeyboardInterrupt:
            #     logger.info("程序被用户中断，正在关闭浏览器...")   
        finally:
            return content                               


    def msd_crawler(symptom,driver):
        def msd_mulpage_crawler(url,driver):
            content = ""
            try:
                #print(url)
                driver.get(url)
                xpath_expression = """
                    //div[contains(@class, 'undefined')]//div[contains(@class, 'AllSearchItems_allSearchItemsResults__6rrp2')]/div[contains(@class, 'AllSearchItems_searchResultsMain__RwyZl')]
                    """
                time.sleep(2)
                # session = requests.Session()
                # response = session.get(url)
                # if response.status_code == 200:
                #     soup = BeautifulSoup(response.text, 'html.parser')
                # links = soup.find('div', class_='AllSearchItems_searchResultsMain__RwyZl')
                links = driver.find_elements(By.XPATH, xpath_expression)
                        # element = driver.find_element(By.XPATH, f"//a[contains(@class, 'SearchResults_paginationPage___0P5_') and @tabindex='0' and text()='{page}']")
                        # driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        # time.sleep(2)
                        # driver.execute_script("arguments[0].click();", element)
                        # time.sleep(2)
                    # except NoSuchElementException:
                    #     print(f'不存在第{page}页选项') 
                    # finally:
                        # links = driver.find_elements(By.XPATH, xpath_expression)
                #print(links)
                illegal_chars = r'[<>:"/\\|?*？：。！‘’；“”]'
                for link in links:
                    title = link.find_element(By.TAG_NAME, 'a').find_element(By.TAG_NAME, 'span').text
                    #print(title)
                    contents = [p.text for p in link.find_elements(By.TAG_NAME, 'p')]
                    title = re.sub(illegal_chars, '_', title) 
                    #print(contents)
                    href = link.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    content += f'[标题: {title} : {contents} , 链接: [{href}]]' + "\n"
    #             for link in links:
    # ## 使用BeautifulSoup的方法来找到对应的元素
    #                 title_span = link.find('a').find('span')
    #                 if title_span:
    #                     title = title_span.text
    #                     title = re.sub(illegal_chars, '_', title)  # 替换非法字符
    #                 else:
    #                     title = "No Title"

    #                 contents = [p.text for p in link.find_all('p')]  # 找到所有的p标签并获取文本
    #                 href = link.find('a').get('href') if link.find('a') else "No Link"  # 获取href属性

    #                 # 构建你的内容字符串
    #                 content += f'[标题: {title} : {contents} , 链接: [{href}]]' + "\n"
                    #print(f'标题: {title}{contents} , 链接: {href}')                                        
                #driver.close()
            finally:
                return content
        # 找到并点击元素
        #time.sleep(3)
            # links = driver.find_elements(By.XPATH, xpath_expression)
            # for link in links:
            #     title = link.find_element(By.TAG_NAME, 'span').text
            #     #content = link.find_element(By.TAG_NAME, 'p').text
            #     href = link.get_attribute('href')
            #     print(f'标题: {title} , 链接: {href}')
            #     title = re.sub(illegal_chars, '_', title)
            #     #globalmil_content(title, href)    
        try:
            content = ''
            for symp in symptom:
                #print(1111111111111111111111111111111111111111)
                url = 'https://www.msdmanuals.cn/home/searchresults?query=' + symp
                #print(url)
                content += msd_mulpage_crawler(url,driver) + '\n'
                #content += msd_mulpage_crawler(url + "&page=2",driver)
            return content
        except KeyboardInterrupt:
            logger.info("程序被用户中断，正在关闭浏览器...")   
        finally:
            return content

    def websearch( dialogue):
        # 检索词生成任务:给你一段医生患者之间的对话，请你总结患者的病症，用词要求简短，用一个词汇概括，专业，不要加形容词，不需要说明症状的程度
        PROMPT_DICT = {
        "context": f"""
## 
假设你是一名医生，根据患者问题和你与患者的对话历史，分析患者可能患的病，生成1到3个疑似疾病的查询关键词：
## 要求
关键词要使用医学专业术语，尽量简洁，最多3个
## 对话内容
'{dialogue}'
## 患者的问题
'{dialogue[-1]}'
## 回答要求
请按照以下格式列出查询关键词，只给出关键词，不输出额外内容或符号，全部写在一行，最多3个：
关键词1,关键词2......
""",
        "context2": f"""
## 目标
医学查询关键词识别:根据患者最新的问题，结合上下文，生成一个不描述症状的医学相关检索关键词（优先生成药品名、恢复期、用药用量等），要求关键词简短，使用医学术语。
## 对话内容
'{dialogue}'
## 回答要求
只输出一个关键词，不做额外输出，格式如下：
关键词
""",
        "context3": f"""
## 目标
患者病症查询关键词识别:请分析以下医生与患者的对话内容，并从中识别出患者目前的主要症状。给出1-3个症状描述关键词，注意关键词里要剔除掉患者排除的症状，以及与患者最新问题无关的症状：
1. 给出1-3个关键词，描述与患者最新问题相关的症状，要体现症状所在的患病部位，使用医学专业术语，尽量简洁且不包含形容词
2. 注意剔除掉与患者当前问题无关的症状，以及对话历史里排除掉的症状。
## 对话内容
'{dialogue}'
## 患者的问题
'{dialogue[-1]}'
## 回答要求
请按照以下格式列出最相关的4个查询关键词，只给出关键词，不输出额外内容或符号，全部写在一行：
关键词1,关键词2,关键词3
"""
        } 
        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        #PROMPT_DICT["context"] 
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": PROMPT_DICT["context"]
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": PROMPT_DICT["context3"]
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content2 = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content2 += content
        keyword = ''
        symptom = ''
        logger.info("LLM返回的检索词")
        logger.info(full_content)
        logger.info(full_content2)
    #print(full_content)      
    #if "描述词:" in full_content:
        keyword = full_content.splitlines()[0].split(',')
        symptom = full_content2.splitlines()[0].split(',')
        if "\n疾病:" in keyword:
            keyword = keyword.split('\n疾病:')[0].split(',') + keyword.split('\n疾病:')[1].split(',')
            # symptom = symptom.split('\n疾病:')[0]
        #print("查找的关键词有：\n")       

        content = ''
        keyword = [key.replace('\n', '') for key in keyword]
        symptom = [sym.replace('\n', '') for sym in symptom]
        symptom  = ' '.join(map(str, symptom )) 
        print(keyword)
    #     client = ZhipuAI(api_key="4a16d61bfda4c350ca19d8786b658574.IObm0IcKYLYAooFQ")
    #     #PROMPT_DICT["context"] 
    #     results = client.chat.completions.create(
    #             model="glm-4-0520",
    #             messages=[
    #                 {
    #                     "role": "system",
    #                     "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
    #                 },
    #                 {
    #                     "role": "user",
    #                     "content": PROMPT_DICT["context2"]
    #                 }
    #         ],
    #             top_p= 0.7,
    #             temperature= 0.5,
    #             max_tokens=1024,
    #             stream=True,
    #         )
    #     full_content = ""
    #     for chunk in results:
    # # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
    #         content = chunk.choices[0].delta.content
    #         full_content += content
    #     print(full_content)
        #new_keywords = []
        # for keyworditem in keyword:
        #keyword.append(full_content)
        logger.info('搜索使用的关键词为：\n')
        logger.info(keyword)
        print(keyword)
        logger.info('开始搜索................................................................')
        # content += dingxiang_crawler(keyword)
        # content += msd_crawler(new_keywords, driver)
        content = []
        for word in keyword:
            content += bing_search(word)
        content += bing_search(symptom)
        logger.info('获得以下内容及摘要\n')
        logger.info(content)
        return symptom, content 
    
    def AI_select( sym, search_result, dialogue):
        links = []
        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        PROMPT_DICT = {
       "context": f"""
        ## 目标
        你负责链接筛选任务:给你一段医生患者之间的对话，以及检索到的医学网站上的相关链接以及链接对应的标题和内容摘要，结合患者症状和身份相关信息，选出最相关的'{2*len(sym) if len(sym)<4 else len(sym)}'条链接，要求每个症状都至少要有一条对应链接，只给出链接，无需给出原因。
        ## 对话内容
        '{dialogue}'
        ## 患者症状
        '{sym}'
        ## 相关资料与对应链接
        '{search_result}'
        ## 请按以下格式给出链接,每个链接之间用','隔开
        示例:
        http://example1.com,http://example2.com,http://example3.com,http://example4.com...
        """
        } 
        #print(PROMPT_DICT["context"])
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content":"你是辅助医生基于患者诉求，检索病症相关资料的搜索引擎。你需要寻找出最相关的内容用于诊断。"
                    },
                    {
                        "role": "user",
                        "content": PROMPT_DICT["context"]
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
        links = full_content.split(',')
        return links

    def create_emptcase():
        my_long_string = """
##主诉:
- **患者主要症状摘要**:（此处需根据对话序列填写，例如：胸痛、呼吸困难等）
- **持续时间:（此处需根据对话序列填写，例如：3天、2周等）

##现病史:
- （此处需根据对话序列详细描述症状，例如：患者3天前开始出现胸痛，呈持续性钝痛，活动后加重，休息后缓解，无放射性疼痛，伴有轻微呼吸困难。）

##既往史:
- **疾病史:（此处需根据对话序列填写，例如：高血压、糖尿病等）
- **手术史:（此处需根据对话序列填写，例如：阑尾切除术、胆囊切除术等）
- **药物过敏史:（此处需根据对话序列填写，例如：青霉素过敏、磺胺类药物过敏等）
- **生活习惯:（此处需根据对话序列填写，例如：吸烟、饮酒等）
- **饮食偏好:（此处需根据对话序列填写，例如：素食、喜辣等）

##检查:
- **体格检查:（此处需根据对话序列填写，例如：体温37.2°C、脉搏90次/分、呼吸20次/分、血压130/80 mmHg等）
- **辅助检查:（此处需根据对话序列填写，例如：血常规、尿常规、心电图等）

##诊断:
- （此处需根据对话序列填写，如果医生未诊断，则填写“暂无”）

##建议:
- （此处通常不填写，因为要求只输出病历内容，以下为示例）：建议进一步进行心脏彩超检查，排除心脏疾病。
        """
        return my_long_string
    def case_extract(dialog_history,case_content):
        def postprocess(results):
            #raw_output = results["choices"][0]["message"]["content"]
            if results is not None:
                if "病人病历" in results:
                    results = results.split("病人病历")[1]
                return results
            
        PROMPT_DICT = {
        "context": (
"1. Goals\n"
"病例提取任务:给你一个医生患者对话序列和已有的病例单，对病例单不正确的地方进行修改，遗漏的内容进行补充\n"
"2. Constraints\n"
"不可以主观判断和过度猜测，要根据医生和患者说出的事实进行推断，来填补或修改条目。\n"
"对于病历的每一项内容,如果根据目前的事实无法判断,则可以填暂无\n"
"只输出病历，不输出额外内容\n"
"3. 医生患者对话序列\n"
"{dialog_history}\n"
"4. 已有的病例单\n"  
"{case_content}\n"          
"5. format\n"
"#病人病历\n"
"##主诉:\n"
"- **患者主要症状摘要**:(对患者的每个症状用一个医学领域相对专业的词汇描述)\n"
"- **持续时间:\n"
"##现病史:\n"
"- (症状的详细描述,包括发病时间、症状的性质、变化、伴随症状等)。\n"
"##既往史:\n"
"- **疾病史:\n"
"- **手术史:\n"
"- **药物过敏史:\n"
"- **生活习惯:\n"
"- **饮食偏好:\n"
"##检查:\n"
"- **体格检查:(体温、脉搏、呼吸、血压等生命体征)\n"
"- **辅助检查:(血常规、尿常规、粪常规、生化检查、影像学检查(X光、CT、MRI等)、心电图、超声等检查结果)\n"
"##诊断:\n"
"- (如果历史对话中医生给出了诊断，则根据医生诊断填补和修改这部分内容，医生没有做出诊断，就填暂无)\n"
"##建议:\n"
"- \n"
        ),
        }
        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        dialogue = {}
        dialogue["dialog_history"] = dialog_history
        dialogue["case_content"] = case_content
        context = PROMPT_DICT["context"].format_map(dialogue)
        logger.info('病历单prompt\n' + context)
        logger.info('病历单生成中................................................................')
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": context
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
            case = postprocess(full_content)
        return case
    

    def act_classification( dialog_history):

        def fuzzy_match(intent, intent_list):
            # 使用difflib的SequenceMatcher来计算相似度
            ratios = [difflib.SequenceMatcher(None, intent, item).ratio() for item in intent_list]
            # 找出相似度最高的元素及其索引
            max_ratio = max(ratios)
            max_index = ratios.index(max_ratio)
            return intent_list[max_index]
        
        def postprocess(results):
            if "{" and "}" in results:
                result = results[results.rfind('{'):results.find('}') + 1]
                logger.info(result)
                #raw_output = results["choices"][0]["message"]["content"]
                data = json.loads(result)
            resultlist = []
            if data is not None:
                for sentence_intents in data.values():
                    for intent in sentence_intents:
                        resultlist.append(intent)
            return resultlist
        PROMPT_DICT = {
        "context_doctor": (
            "## 目标\n"
            "意图识别任务：给你一个医生与患者的对话序列，提取对话序列中每句话的意图，生成意图序列。\n"
            "## 限制\n"
            "对于每一句话，只能从以下列出的标签中选择最贴切的一到三个意图，不可以新增意图。要求按照对话顺序给出意图，不需要解释原因。\n"
            "可选标签：\n"
            "- Doctor-Asking-Symptom: 医生询问症状，或对患者未阐述清楚的症状进行追问。\n"
            "- Doctor-Explain-Disease_Characteristics: 医生向患者解释疾病特征、症状。\n"
            "- Doctor-Explain-Etiology: 医生向患者解释患病原因、可能造成现在症状的原因。\n"
            "- Doctor-Asking-Basic_Information: 询问患者基本信息或行为轨迹。\n"
            "- Doctor-Asking-Existing_Examination_and_Treatment: 询问患者已做的检查和治疗。\n"
            "- Doctor-Giving-Drug_Recommendation: 给出用药建议。\n"
            "- Doctor-Giving-Medical_Advice: 给出医疗建议，或根据已有知识给出病症治疗基本方案。\n"
            "- Doctor-Giving-Precautions: 告知治疗或用药需注意事项，或预防病症加剧建议。\n"
            "- Doctor-Asking-Treatment_Intention: 询问患者治疗诉求。\n"
            "- Doctor-Diagnose: 根据症状做出诊断。\n"
            "- Doctor-Explain-Diagnosis_Result: 解释诊断结果和依据。\n"
            "- Doctor-Summarizing_Symptom: 根据患者资料总结症状。\n"
            "- Doctor-Explain-Drug_Effects: 解释药物作用。\n"
            "- Reassure: 安抚患者。\n"
            "- Confirm: 确认患者告知的信息。\n"
            "- Greet: 打招呼。\n"
            "- Patient-Giving-Symptom: 向医生阐述症状。\n"
            "- Patient-Consult-Symptom: 询问症状意义。\n"
            "- Patient-Asking-Etiology: 询问患病原因。\n"
            "- Patient-Giving-Basic_Information: 提供基本信息。\n"
            "- Patient-Giving-Existing_Examination_and_Treatment: 告知已做的检查和治疗。\n"
            "- Patient-Asking-Drug_Recommendation: 询问用药建议。\n"
            "- Patient-Asking-Medical_Advice: 询问诊疗方案。\n"
            "- Patient-Asking-Precautions: 询问治疗或用药注意事项。\n"
            "- Patient-Giving-Treatment_Needs: 告知治疗诉求。\n"
            "- Patient-Asking-Diagnosis_Result: 询问诊断结果。\n"
            "- Patient-Other_Feedback: 与疾病描述无关的反馈。\n"
            "- Patient-Confirm: 确认医生告知的信息。\n"
            "- Patient-Greet: 病人打招呼。\n"
            "## 工作流程：\n"
            "1. 读取文本 '{former_dialogue}'\n"
            "2. 从第一句对话开始，逐句分析对话，给出每句对话所含的意图。\n"
            "3. 将意图按产生顺序输出，key用句子序号表示，value是每句话对应的意图。以JSON格式输出：\n"
            "{{{{\n"
            '  "1": ["intent1", "intent2", ...],\n'
            '  "2": ["intent1", "intent2", ...]\n'
            "}}}}\n"
        ),
        "context_patient": (
            "## Goals\n"
            "意图识别任务:给你一句患者说的话以及先前对话，判断他这一句话的意图\n"
            "## Constraints\n"
            "只能从以下列出的标签中选择最贴切的一个或多个意图，最多三个，不可以新增意图，不需要解释原因\n"
            "有以下可选标签:\n"
            "Patient-Giving-Symptom:向医生阐述症状\n"
            "Patient-Consult-Symptom:向医生提问，咨询症状\n"
            "Patient-Asking-Etiology:向医生询问所患病症的原因\n"
            "Patient-Giving-Basic_Information:向医生告知基本信息\n"
            "Patient-Giving-Existing_Examination_and_Treatment:向医生告知目前已经做的检查和治疗\n"
            "Patient-Asking-Drug_Recommendation:询问医生用药建议\n"
            "Patient-Asking-Medical_Advice:询问医生就医建议\n"
            "Patient-Asking-Precautions:询问医生所患疾病或所做治疗的注意事项和禁忌\n"
            "Patient-Giving-Treatment_Needs:向医生告知自己的治疗诉求\n"
            "Patient-Asking-Diagnosis_Result:对医生给出的诊断有不理解的地方，向医生咨询\n"
            "Patient-Other_Feedback:患者与疾病描述无关的反馈,诸如感谢,非常满意等\n"
            "Patient-Confirm :对医生告知信息的确认,比如好的,了解了\n"
            "Patient-Greet\n"
            "## Workflow:\n"
            "1、 读取文本 \n'{speaker}:{sentence}'\n"
            "2、分析语境和先前对话\n'先前对话:{former_dialogue}'\n"
            "3、判定意图类别 \n"
            "4、输出意图类别，格式:\n"
            "患者意图:意图类别1,意图类别2,意图类别3\n"
        ),
        "context2": (
            "下面给出的示例，是针对对话打上的意图标签，有两个不同的标签，只给出合适的意图，不用解释原因\n\n"
            "##\n 先前对话:患者:孩子老是咳嗽怎么办\n"
            "医生: 咳嗽有几天了？\n"
            "\n"
            "Confirm-Treatment_Intention\n"
            "合适的意图:\n\n"
            "##\n 先前对话: None\n"
            "医生: 从你发的图片看，这个孩子的大便有点稀，大便当中有粘液\n"
            "Patient-Giving-Symptom\n"
            "Doctor-Explain-Diagnosis_Result\n"
            "合适的意图:Patient-Giving-Symptom\n\n"
            "##\n 先前对话:{former_dialogue}\n"
            "{speaker}:{sentence}\n"
            "{classification1}\n"
            "{classification2}\n"
        ),
        }

        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        dialogue = {}
        dialogue["former_dialogue"] = dialog_history
        context = PROMPT_DICT["context_doctor"].format_map(dialogue)
        logger.info('意图分类prompt：\n')
        logger.info(context)
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": context
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
        logger.info("意图分类结果：\n")
        logger.info(full_content)
        results = postprocess(full_content)
        for index, result in enumerate(results):
            if result not in intent_labels:
                most_similar_intent = fuzzy_match(result, intent_labels)
                results[index] = most_similar_intent
        return results
    
    #将意图与对应要求绑定
    def result_gen(extracted_content, dialog_history, inferintent , case):
        patient_intent = []
        for item in inferintent[:3]:
            for key , value in intent_expl.items():
                if key == item[0] and key not in ["Patient-Confirm","Patient-Other_Feedback","Patient-Greet"]:
                    patient_intent.append( value)
            logger.info("根据意图提出的要求：")
            logger.info(patient_intent)

        allarticle_dictionary = []
        for item in extracted_content:
            dictionary = []
            def article_dictionary(dictionary, item, parent_key=''):
                for key,value in item.items():
                    new_key = f"{parent_key}.{key}" if parent_key else key
                    if 'h' in key:
                        dictionary.append(new_key)
                    #if isinstance(value, dict):
                        article_dictionary(dictionary, value, new_key)
                return None
            article_dictionary(dictionary, value)
            allarticle_dictionary.append(dictionary)
        PROMPT_DICT = {
            "context": f"""
## 目标
假设你是一名医师助理，能准确的筛选帮助医生诊疗的参考资料。请你结合相关资料的目录、对话内容、要求，为医生选择所需参考资料的对应标题。
## 相关资料的目录
'{extracted_content}'
## 对话内容
'{dialog_history}'
## 要求
'{patient_intent}'
## 回答步骤
1.阅读相关资料的目录，阅读对话内容，选出帮助医生判断的最主要{len(allarticle_dictionary)}段资料的对应标题，要求照搬原标题，不对标题做任何修改。
2.阅读相关资料的目录，阅读对话内容，再阅读要求，设想患者会问的问题，填写问题序号对应的问题，再填写针对该问题所需资料的标题，要求照搬原标题，不对标题做任何修改。
## 输出格式
#最主要资料对应标题
['标题1','标题2'...]
"""
        }
        PROMPT_DICT2 = {
            "context": f"""
## 目标
假设你是一名医生，你能为患者提供专业的诊疗建议。结合资料、病历、要求，诊断患者病情，为患者可能要问的问题提供回复。
## 相关资料的目录
'{extracted_content}'
## 对话内容
'{dialog_history}'
## 要求
'{patient_intent}'
## 回答步骤
1.根据当前医患对话患者病历、校验病历完整性，结合医学搜索工具联网搜索到的资料，基于已经给出的病历内容，判断是否能够确诊资料中的某些相关病症，如果可以，则结合相关资料，给出诊断及建议，填在根据联网搜索的资料给出的诊断及建议部分。如果已有病例不能给出确切诊断，结合=病例信息中缺损的内容，给出患者需要提供的相关信息，填在还需要患者提供的信息部分。
2.阅读相关资料，再阅读要求中的问题，补充患者可能还想了解的内容，之后在相关资料中寻找对应的部分，来对患者可能问出的问题回答。
## 输出格式
#根据联网搜索的资料给出的诊断及建议
- 
#还需要患者提供的信息
- 
#患者可能还想了解的内容
- (针对要求,患者会问的{len(patient_intent)}个问题)
"""
        }
        Template = """
#问题序号{index}
问题:
对应资料标题:['标题1','标题2'...]
"""  
        formatted_parts = [Template.format(index=str(i+1)) for i in range(len(patient_intent))]
        formatted_string = "\n".join(formatted_parts)  
        content = PROMPT_DICT["context"] + formatted_string
        #print("final_res模板1")
        #print(content)
        logger.info('文档划分模版：\n' )
        logger.info(content)
        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": content
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
        #print("最终result1")
        #print(full_content) 
        logger.info('文档划分结果：\n' )
        logger.info(full_content)
        pattern = r"#最主要资料对应标题\n(.*?)\n|#问题序号\d+\n问题:(.*?)\n对应资料标题:(\[.*?\])"
        matches = re.findall(pattern, full_content, re.DOTALL)

        # 提取主要资料标题
        main_titles = matches[0][0].strip("[]").split("','") if matches[0][0] else []

        # 构建JSON数据结构
        data = {'主要资料': main_titles}
        for match in matches[1:]:
            question, titles = match[1], match[2].strip("[]").split("','") if match[2] else []
            data[question] = titles

        # 将数据转换为JSON格式
        json_data = json.dumps(data, ensure_ascii=False, indent=2)

        # 打印JSON数据
        print(json_data)        
        Template2 = f"""
这是医学检索工具返回的结果，请直接将工具返回结果输出，不做任何修改。
'{full_content}'
"""
#         #print("final_res模板2")
#         #print(Template2)
#         logger.info('最终答案生成模版：\n' )
#         logger.info(Template2)
#         results2 = client.chat.completions.create(
#                 model="glm-4-0520",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "你是一名医生，你能为患者提供专业的诊疗建议。"
#                     },
#                     {
#                         "role": "user",
#                         "content": Template2
#                     }
#             ],
#                 top_p= 0.7,
#                 temperature= 0.1,
#                 max_tokens=2048,
#                 stream=True,
#             )
#         full_content2 = ""
#         for chunk in results2:
#     # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
#             content = chunk.choices[0].delta.content
#             full_content2 += content
#         #print("最终回复2")
#         #print(full_content2)
#         logger.info('提问建议生成结果：\n' )
#         logger.info(full_content2)
#         full_content += "\n" + full_content2
        
        return Template2 
    def judgement(dialog_history):
        num = '1'
        template =f"""
结合对话历史，如果患者问题只涉及医学常识，或者在对话历史中医生回复已经有能回答这个问题的信息，则回答1，如果还需要更多专业医疗知识，回答2：
#对话历史
{dialog_history}
#患者问题
{dialog_history[-1]}
#回答格式
- 只给出答案
1or2

"""

        client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
        results = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                    },
                    {
                        "role": "user",
                        "content": template
                    }
            ],
                top_p= 0.7,
                temperature= 0.5,
                max_tokens=1024,
                stream=True,
            )
        full_content = ""
        for chunk in results:
    # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
            content = chunk.choices[0].delta.content
            full_content += content
        if '1' in full_content:
            return '1'
        else:
            return '2'
        return num
#     str = """
# 诊断及建议：您目前的症状可能与单纯疱疹病毒感染（HSV）有关，尤其是HSV-1型，这通常引起唇疱疹。唇疱疹的典型症状包括疼痛性水泡，随后是溃疡和结痂。全身症状如发热和不适也可能出现。由于患者有痔疮疼痛的症状，这可能是全身炎症反应的一部分，也可能是痔疮本身的炎症加重。
# 建议继续服用一清片，这是一种中成药，具有清热解毒的作用，可能有助于缓解一些症状。然而，由于您的症状较为严重，建议尽快就医，以便进行全面的评估和必要的检查。医生可能会建议进行病毒培养或PCR检测，以确认HSV感染。
# 此外，由于您有青霉素过敏史，医生在开具任何药物时应注意避免使用可能引起交叉反应的药物。
# 以下是还需要您提供的信息，请问水泡或溃疡的确切外观，例如它们是充满液体的、疼痛的，还是已经破裂并形成结痂。您的痔疮疼痛的性质，例如它是剧烈的、持续的，还是与排便有关。是否还有任何其他症状，如发热、头痛、关节痛或皮疹。
# 以下是一些额外的建议： 
# 什么时候应该考虑使用抗病毒药物？抗病毒药物如阿昔洛韦、伐昔洛韦或泛昔洛韦通常用于治疗HSV感染。它们在症状出现后的头几天内开始服 用最为有效，可以缩短病程并减轻症状。如果您怀疑自己患有HSV感染，应尽快就医，以便医生评估您是否需要抗病毒药物。
# 如何处理痔疮疼痛？痔疮疼痛可以通过多种方法缓解，包括：坐浴：使用温水坐浴可以减轻疼痛和炎症。局部用药：使用含有氢化可的松或其他抗炎成分的药膏或栓剂。避免刺激性食物：避免辛辣食物、咖啡和酒精，这些食物可能会加重痔疮症状。"""
#     str = """
# \n\'# 诊断及建议\n\n- 患者目前的症状可能与单纯疱疹病毒感染（HSV）有关，尤其是HSV-1型，这通常引起唇疱疹。唇疱疹的典型症状包括疼痛性水泡，随后是溃疡和结痂。全身症状如发热和不适也可能出现。由于患者有痔疮疼痛的症状，这可能是全身炎症反应的一部分，也可能是痔疮本身的炎症加重。\n\n- 建议
# 患者继续服用一清片，这是一种中成药，具有清热解毒的作用，可能有助于缓解一些症状。然而，由于患者症状较为严重，建议尽快就医，以便进行全面的评估和必要的检查。\n\n- 医生可能会建议进行病毒培养或PCR检测，以确认HSV感染。此外，由于患者有青霉素过敏史，医生在开具任何药物时应注意避免使用可能引起
# 交叉反应的药物。\n\n# 以下是还需要患者提供的信息，请根据这些信息向患者提问：\n\n- 水泡或溃疡的确切外观，例如它们是充满液体的、疼痛的，还是已经破裂并形成结痂。\n- 痔疮疼痛的性质，例如它是剧烈的、持续的，还是与排便有关。\n- 任何其他症状，如发热、头痛、关节痛或皮疹。\n- 过敏史，包括对其他药物或食物的过敏反应。\n\n# 患者
# 可能还想了解的内容，请问患者想了解哪个内容。\n\n- 唇疱疹的病程和预后。\n- 痔疮的治疗方法。\n- 如何预防HSV感染和其他皮肤感染。
# """
# \n- 痔疮的治疗方法。\n- 如何预防HSV感染和其他皮肤感染。\n\n## 患者问题1:对应的回复\n\n**问题**： 我什么时候应该考虑使用抗病毒药物？\n\n**回复**： 抗病毒药物如阿昔洛韦、伐昔洛韦或泛昔洛韦通常用于治疗HSV感染。它们在症状出现后的头几天内开始服 
# 用最为有效，可以缩短病程并减轻症状。如果您怀疑自己患有HSV感染，应尽快就医，以便医生评估您是否需要抗病毒药物。\n\n## 患者问题2:对应的回复\n\n**问题**： 我应该如何处理痔疮疼痛？\n\n**回复**： 痔疮疼痛可以通过多种方法缓解，包括：\n\n- 坐浴：使用温水坐浴可以减轻疼痛和炎症。\n- 局部用药：
# 使用含有氢化可的松或其他抗炎成分的药膏或栓剂。\n- 避免刺激性食物：避免辛辣食物、咖啡和酒精，这些食物可能会加重痔疮症状。\n- 保持良好的卫生习惯：保持肛门区域的清洁和干燥，避免使用粗糙的卫生纸。\n\n如果痔疮疼痛持续或加重，建议您就医，以便进行评估和治疗。
    #
    #
    #
    #
    chatfilename = 'chat_history6.json'
    articletittlefilename = './article_tittles6.json'
    logging.basicConfig(filename='medical6.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
    logger = logging.getLogger()
    handler = logging.FileHandler('medical6.log', encoding='utf-8')
    logger.addHandler(handler)
        
    
    dialog_history = []
    # #打开病历单
    # try:
    #     with open(casefilename, 'r', encoding='utf-8') as file:
    #         case_content = file.read()
    # except FileNotFoundError:
    # #如果不存在，创建空病历单
    #     case_content = create_emptcase()
    # #打开历史对话记录
    with open(chatfilename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    dialog_history = []
    # # intentsequence = []
    # # #历史记录转成字符串，并区分患者医生
    for dialogue in json_data:
        role = "患者" if dialogue["role"] == "user" else "医生"
        dialog_history.append(f"{role}说：{dialogue['content']}")
    

#     num = judgement(dialog_history)
#     if num == '1':
#         dialoguestr = ''
#         for item in dialog_history:
#             dialoguestr += item + '\n' 
#         template =f"""
# 假设你是三甲医院的医生，能对患者的问题给出专业的回答：
# {dialoguestr}
# """

#         client = ZhipuAI(api_key="4a16d61bfda4c350ca19d8786b658574.IObm0IcKYLYAooFQ")
#         results = client.chat.completions.create(
#                 model="glm-4-0520",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
#                     },
#                     {
#                         "role": "user",
#                         "content": template
#                     }
#             ],
#                 top_p= 0.7,
#                 temperature= 0.5,
#                 max_tokens=1024,
#                 stream=True,
#             )
#         full_content = ""
#         for chunk in results:
#     # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
#             content = chunk.choices[0].delta.content
#             full_content += content
#         return BaseToolOutput("医学知识回答：" + full_content)



    # #根据对话内容提取病历单
    # case = case_extract(dialog_history,case_content)
    # logger.info('病历单内容：\n' )
    # logger.info(case)
    # directory = os.path.dirname(casefilename)
    # if not os.path.exists(directory):
    #     os.makedirs(directory)  # 确保目录存在
    # with open(casefilename, 'w', encoding='utf-8') as file:
    #         file.write(case)
    # sym = ''
    # search_result = ''

    def judgement2(dialog_history):
        articletittlefilename = './article_tittles6.json'
        if os.path.exists(articletittlefilename) and os.path.getsize(articletittlefilename) > 0:
            with open(articletittlefilename, 'r', encoding='utf-8') as f:
                article_tittles = json.load(f)
            if article_tittles != []:
                print(111111111111111111111111111111111111111111111111111111111111)
                template2 =f"""#目标
总结患者的症状，剔除掉已经被患者或者医生排除的症状和疾病，然后判断目前参考资料中已有的病症资料是否能够回答患者的问题，可以则回答1，不可以则回答2。
#参考资料的目录
代表了你目前已经拥有的参考资料的目录摘要。
{article_tittles}
#问题
{dialog_history[-1]}
#对话历史
{dialog_history}
#回答格式
只给出答案，不做额外输出:
1or2
"""
                client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
                results = client.chat.completions.create(
                        model="glm-4-plus",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                            },
                            {
                                "role": "user",
                                "content": template2
                            }
                    ],
                        top_p= 0.7,
                        temperature= 0.5,
                        max_tokens=1024,
                        stream=True,
                    )
                full_content = ""
                for chunk in results:
            # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
                    content = chunk.choices[0].delta.content
                    full_content += content
            
                if '1' in full_content:
                    return 1
                else:
                    return 2
            else:
                return 2
        else:
            return 2
    flag_num = judgement2(dialog_history)
       # driver = create_browser()

    #link = 'https://drugs.dxy.cn/pc/drug/CNtyZA1bqvFxRkGwwUro7Q=='
    #data = dingxiang_content(link, "drug")
    #data = dingxiang_crawler([' 手足口病'])
    #print(data)
    #print(json.dumps(data, indent=2, ensure_ascii=False))
    # def extract_titles(data):
    #     titles = []
    #     for key, value in data.items():
    #         if "标题" in key:
    #             titles.append(key)
    #         if isinstance(value, dict):
    #             titles.extend(extract_titles(value))
    #     return titles

    # titles_list = extract_titles(data)
    # print(titles_list)

#     tittles_list = ['h1总标题:手足口病', 'h2标题:基础知识', 'h3标题:定义', 'h4标题:病原学', 'h4标题:机械通气指征', 
# 'h2标题:预后', 'h3标题:接种疫苗', ]
#     def extract_contents(data, titles):
#         contents = {}
#         for title in titles:
#             for key, value in data.items():
#                 if key == title:
#                     contents[key] = value
#                 elif isinstance(value, dict):
#                     contents.update(extract_contents(value, [title]))
#         return contents

#     contents_json = extract_contents(data, tittles_list)
#     print(json.dumps(contents_json, indent=2, ensure_ascii=False))


    
    # #根据对话内容在msd和丁香进行搜索，返回检索症状词和检索内容
    if flag_num == 1:
        print('已有知识足够回答患者问题')
        print(11111111111111111111111111111111)
        return BaseToolOutput('已有知识足够回答患者问题')
    else:
        sym , search_result  = websearch(dialog_history)
        # my_string = ''
        # my_string = '\n'.join(search_result)
        # my_string += '\n'.join(drug)
        json_string = json.dumps(search_result, ensure_ascii=False)
        str1 = str(sym) + '根据症状查询到以下内容：'  + json_string
        #print(str1)
        # #大模型根据症状和检索内容匹配最相关的几个文档
        # links = AI_select( sym, search_result, dialog_history)    
        # #print("最相关的文档是：\n")
        # logger.info('最相关的文档链接是：\n')
        # logger.info(links)
        # #print(links)
        # extracted_content = []
        # for link in links:
        #     if "drugs.dxy.cn/pc/drug" in link:
        #         extracted_content.append(dingxiang_content(driver, link, "drug"))
        #     elif 'dxy' in link:
        #         extracted_content.append(dingxiang_content(driver, link, "case"))
        #     else:
        #         extracted_content.append(msd_content(driver, link))
            #driver.close()
            #driver.service.stop()

        # #print(extracted_content)
        # logger.info('内容：\n' )
        # logger.info( extracted_content)
        # intentlist =  act_classification( dialog_history[-10:])
        # logger.info('意图序列生成结果：\n' )
        # logger.info(intentlist )
        # for index, item in enumerate(intentlist):
        #     if item.startswith("Doctor") and ("Greet" in item or "Confirm" in item or "Reassure" in item):
        #         intentlist[index] = item[len("Doctor-"):]
        # #print(intentlist)
        # inferintent = LSTM( intentlist[-20:] )  #返回概率由高到低的排序
        # logger.info('意图预测结果：\n' )
        # logger.info(inferintent )
        # #print(inferintent)
        # final_result = ''
        # final_result = result_gen(extracted_content, dialog_history, inferintent,case)
        # #print(final_result)
        # logger.info('病历单、参考资料、建议汇总\n' ) 
        # logger.info(final_result)
        # logger.info(case)

    # 输出读取到的JSON数据
    #     print(json_data)
    #     调用工具的运行方法，并传入参数


        return BaseToolOutput('检索到的相关知识:' + str1)