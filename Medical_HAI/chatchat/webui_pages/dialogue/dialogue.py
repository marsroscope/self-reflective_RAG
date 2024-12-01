import base64
import hashlib
import io
import os
import uuid
import json
from datetime import datetime
from PIL import Image as PILImage
from typing import Dict, List
from urllib.parse import urlencode

# from audio_recorder_streamlit import audio_recorder
import openai
import streamlit as st
import streamlit_antd_components as sac
from streamlit_chatbox import *
from streamlit_extras.bottom_container import bottom
from streamlit_paste_button import paste_image_button

from chatchat.settings import Settings
from chatchat.server.callback_handler.agent_callback_handler import AgentStatus
from chatchat.server.knowledge_base.model.kb_document_model import DocumentWithVSId
from chatchat.server.knowledge_base.utils import format_reference
from chatchat.server.utils import MsgType, get_config_models, get_config_platforms, get_default_llm
from chatchat.webui_pages.utils import *
import ast
import logging

from zhipuai import ZhipuAI
import re
import time
import signal
import difflib
import logging
import requests
from bs4 import BeautifulSoup, NavigableString

chat_box = ChatBox(assistant_avatar=get_img_base64("doctor.png"),user_avatar = get_img_base64("patient.png"))
history_path =  './chat_history6.txt'
logging.basicConfig(filename='medical6.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
logger = logging.getLogger()
handler = logging.FileHandler('medical6.log', encoding='utf-8')
logger.addHandler(handler)

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
    'Confirm',
    'Other_Feedback',
    'Greet'
]
intent_expl = {
    "Patient-Giving-Symptom":"选出包含患者所患病症的的其他症状内容的对应标题",
    "Patient-Consult-Symptom":"对于上文提到的症状，选出症状的详细解释和影响，表明了什么问题等的内容的对应标题。",
    "Patient-Asking-Etiology":"对于患者所患疾病，选出包含患病的原因内容的对应标题",
    "Patient-Giving-Basic_Information":"选出包含医生如何判断是否患病的内容的对应标题",
    "Patient-Giving-Existing_Examination_and_Treatment":"请选出目前病人需要做哪些检查的参考资料对应标题。",
    "Patient-Asking-Drug_Recommendation":"选出针对上文病症的药物治疗方案的相关资料对应标题",
    "Patient-Asking-Medical_Advice":"选出上文患者提问的医学问题、医学常识、医疗建议相关资料的对应标题",
    "Patient-Asking-Precautions":"对于患者的治疗或用药的注意事项相关资料，或者关于患者的疾病的预防和防止病症加剧的相关资料对应标题",
    "Patient-Giving-Treatment_Needs":"对于患者病症的多种治疗方案（比如药物治疗、就诊、注射治疗等）相关资料对应标题",
    "Patient-Asking-Diagnosis_Result":"治疗方案的效果，特点相关资料对应标题，比如多久见效，治疗到什么程度能说明治疗起效了，是否还有漏诊误诊的可能性等资料对应标题",
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

def save_session(conv_name: str = None):
    """save session state to chat context"""
    chat_box.context_from_session(
        conv_name, exclude=["selected_page", "prompt", "cur_conv_name", "upload_image"]
    )


def restore_session(conv_name: str = None):
    """restore sesstion state from chat context"""
    chat_box.context_to_session(
        conv_name, exclude=["selected_page", "prompt", "cur_conv_name", "upload_image"]
    )

def display_reply_and_clear(question, reply):
    chat_box.user_say(question)
    chat_box.ai_say(reply)
    # 清空所有问题和回复
    st.session_state.predict_q = {k: '' for k in st.session_state.predict_q}

def rerun():
    """
    save chat context before rerun
    """
    save_session()
    st.rerun()

def save_history_to_file(history, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)  # 确保目录存在
    with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(history, file, ensure_ascii=False, indent=4)

def get_messages_history(
    history_len: int, content_in_expander: bool = False
) -> List[Dict]:
    """
    返回消息历史。
    content_in_expander控制是否返回expander元素中的内容，一般导出的时候可以选上，传入LLM的history不需要
    """

    def filter(msg):
        content = [
            x for x in msg["elements"] if x._output_method in ["markdown", "text"]
        ]
        if not content_in_expander:
            content = [x for x in content if not x._in_expander]
        content = [x.content for x in content]

        return {
            "role": msg["role"],
            "content": "\n\n".join(content),
        }

    messages = chat_box.filter_history(history_len=history_len, filter=filter)
    if sys_msg := chat_box.context.get("system_message"):
        messages = [{"role": "system", "content": sys_msg}] + messages  

    return messages



@st.cache_data
def upload_temp_docs(files, _api: ApiRequest) -> str:
    """
    将文件上传到临时目录，用于文件对话
    返回临时向量库ID
    """
    return _api.upload_temp_docs(files).get("data", {}).get("id")


@st.cache_data
def upload_image_file(file_name: str, content: bytes) -> dict:
    '''upload image for vision model using openai sdk'''
    client = openai.Client(base_url=f"{api_address()}/v1", api_key="NONE")
    return client.files.create(file=(file_name, content), purpose="assistants").to_dict()


def get_image_file_url(upload_file: dict) -> str:
    file_id = upload_file.get("id")
    return f"{api_address(True)}/v1/files/{file_id}/content"


def add_conv(name: str = ""):
    conv_names = chat_box.get_chat_names()
    if not name:
        i = len(conv_names) + 1
        while True:
            name = f"会话{i}"
            if name not in conv_names:
                break
            i += 1
    if name in conv_names:
        sac.alert(
            "创建新会话出错",
            f"该会话名称 “{name}” 已存在",
            color="error",
            closable=True,
        )
    else:
        chat_box.use_chat_name(name)
        st.session_state["cur_conv_name"] = name


def del_conv(name: str = None):
    conv_names = chat_box.get_chat_names()
    name = name or chat_box.cur_chat_name

    if len(conv_names) == 1:
        sac.alert(
            "删除会话出错", f"这是最后一个会话，无法删除", color="error", closable=True
        )
    elif not name or name not in conv_names:
        sac.alert(
            "删除会话出错", f"无效的会话名称：“{name}”", color="error", closable=True
        )
    else:
        chat_box.del_chat_name(name)
        # restore_session()
    st.session_state["cur_conv_name"] = chat_box.cur_chat_name


def clear_conv(name: str = None):
    chat_box.reset_history(name=name or None)


# @st.cache_data
def list_tools(_api: ApiRequest):
    return _api.list_tools() or {}

def extract_titles(data):
    titles = []
    for key, value in data.items():
        if "标题" in key:
            titles.append(key)
        if isinstance(value, dict):
            titles.extend(extract_titles(value))
    return titles

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
    logger.info('病历单prompt\n')
    logger.info(context)
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
            temperature= 0.1,
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

def AI_select( sym, search_result, dialogue):
    links = []
    client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
    PROMPT_DICT = {
    "context": f"""## 目标
链接筛选、提取任务:给你一段医生患者之间的对话，以及检索到的医学知识链接，已经以json的格式给出，包括：相关链接（link）以及链接对应的标题（title）和内容摘要（snippet），然后结合患者症状和身份（男、女、幼儿等），提取出与患者病症最相关的4条链接，只给出链接，无需说原因，不做额外输出。
## 对话内容
'{dialogue}'
## 相关资料与对应链接
'{search_result}'
#患者症状
'{sym}'
## 请按以下格式给出链接,每个链接之间用','隔开
示例:
https://example1.com,https://example2.com,https://example3.com,https://example4.com
    """
    } 
    logger.info("AI_select")
    logger.info(PROMPT_DICT["context"])
    results = client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {
                    "role": "system",
                    "content":"你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
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
    logger.info("AI_select_response")
    logger.info(full_content)
    links = []
    links = full_content.split(',')
    links = links[:4]
    return links

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

    finally:
        return extracted_content     
    
def act_classification( dialog_history):

    def fuzzy_match(intent, intent_list):
        # 使用difflib的SequenceMatcher来计算相似度
        ratios = [difflib.SequenceMatcher(None, intent, item).ratio() for item in intent_list]
        # 找出相似度最高的元素及其索引
        max_ratio = max(ratios)
        max_index = ratios.index(max_ratio)
        return intent_list[max_index]
    
    def postprocess(results):
        if "{" and "}" in results and results.rfind('{') < results.find('}'):
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
    }

    client = ZhipuAI(api_key="2806385d204a8d1e5bc4e8707ea0d19a.HspdLxBWd9KaSw9V")
    dialogue = {}
    dialogue["former_dialogue"] = dialog_history
    context = PROMPT_DICT["context_doctor"].format_map(dialogue)
    prompt_extrnal = """
{
  "1": ["intent1", "intent2"],
  "2": ["intent1", "intent2"],
  ......
}
"""
    context += prompt_extrnal
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
            temperature= 0.1,
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
        if result:
            if result not in behavior_dict:
                most_similar_intent = fuzzy_match(result, behavior_dict)
                results[index] = most_similar_intent
    return results

def msd_content(url):
    extracted_content = {}
    try:
        #driver.get(url)
        # 等待页面加载完成
        time.sleep(1.5)  # 根据需要调整等待时间
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
def nointent_result_gen(extracted_content, dialog_history, case):
    allarticle_dictionary = []
    for item in extracted_content:
        titles_list = extract_titles(item)
        allarticle_dictionary.append(titles_list)
    
    file_path = 'article_tittles6.json'

    # 使用 with 语句打开文件，确保文件最后会被正确关闭
    with open(file_path, 'w' , encoding='utf-8') as file:
        # 将 JSON 列表写入文件
        json.dump(allarticle_dictionary, file,  ensure_ascii=False, indent=4)
    chat_box.update_msg(f"正在生成最终回复")
    formatted_string1 = """{
  "diagnosis_and_advice": "根据资料和对话历史，回答患者问题，或者给出专业的诊断、用药治疗建议或者挂号就医建议，以及对患者可能关心的问题的回复。如果患者已有确诊病史，请联系确证病史做出更准确的回答。","""
    formatted_string = formatted_string1 +  '}'
# 定义一个提示模板，它将用于向模型提问
    prompt_template2 = f"""
你是一名医生，下面是你和患者的对话历史，你有一个医疗知识检索工具，它会返回参考资料，你可能用得上，在对话历史中，如果患者最后一句话有提问的问题，要先结合资料，回答患者的问题。之后对患者病情给出专业的诊断、用药治疗建议或者挂号就医建议。如果患者已有确诊病史，请联系确证病史做出更准确的回答。尽可能使用口语化的表达。
##参考资料
{extracted_content}
##医患对话历史
{dialog_history}
病例
{case}
##回答步骤
1. 首先，阅读对话历史，如果患者最后一句话有提问的问题，则根据参考资料，回答患者的问题，填在diagnosis_and_advice部分。
2. 之后，结合医学搜索工具联网搜索到的参考资料，判断是否能够确诊资料中的某些相关病症。
3. 如果可以确诊某些病症，则结合相关资料，给出诊断及建议，如果症状不严重，可以适当安抚患者情绪，缓解焦虑，如果患者的确需要及时就医，请对患者给出就医建议。继续添加在diagnosis_and_advice部分。注意，不要完全复述对话历史中已有的的诊断和建议。
4. 最后，如果需要给患者诊疗建议（或者需要更新诊疗建议），且患者已大概率确诊，则根据资料、对话历史和患者的病例，给出专业的诊断、用药治疗建议或者挂号就医建议，请不要模棱两可，给出准确的回答，将诊疗建议填写在diagnosis_and_advice部分。

##输出格式
以json格式输出
{formatted_string}
"""
# 2. 然后，根据对话历史和资料，分析和整理出可能的病例，包括可能的并发��、可能的��险因素和可能的治��方案。
# 3. 接下来，根据��者的��状和所需的��断，在资料中��找相关的病例和治��方案，并对照资料和对话历史中的信息，找出最相关的病例和治��方案。
    logger.info("生成诊断、反问 prompt")
    logger.info(prompt_template2)
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
                    "content": prompt_template2
                }
        ],
            top_p= 0.7,
            temperature= 0.5,
            max_tokens=2048,
            stream=True,
        )
    full_content = ""
    for chunk in results:
# 每个chunk都有一个choices列表，我们取第一个choice的delta的content
        content = chunk.choices[0].delta.content
        full_content += content
    logger.info('诊断、反问、患者可能的问题和回复')
    logger.info(full_content)
    def Postprocess2(result):
        first_bracket = result.find('{')
# 找到最后一个}的位置
        last_bracket = result.rfind('}')

        extracted_content = {}
        if first_bracket != -1 and last_bracket != -1 and first_bracket < last_bracket:
            # 截取第一个{和最后一个}之间的内容
            extracted_content = result[first_bracket :last_bracket+1]
        print(extracted_content)
        extracted_content = extracted_content.replace('\n', '').replace('\r', '')
        extracted_content = extracted_content.replace('\\n', '').replace('\\r', '')
        data = json.loads(extracted_content)
        print(extracted_content)
        final_result = ''
        for key, value in data.items():
            if key == "diagnosis_and_advice":
                final_result += value + "\n\n"
            elif key == "additional_info_needed":
                final_result +=  value +"\n\n"
        # 使用正则表达式提取问题和答案
        # pattern = r"##问题\d+:\n(.*?)-(.*?)\n"
        # matches = re.findall(pattern, result)
        # print('matches:')
        # print(matches)

        # # 将问题和答案存储在字典中
        # predict_q = {question.strip(): answer.strip() for question, answer in matches}

        # 打印结果
        # print("final_result:\n", final_result)
        # print("predict_q:\n", json.dumps(predict_q, indent=2, ensure_ascii=False))
        return final_result
    return Postprocess2(full_content)
def result_gen(extracted_content, dialog_history , case):
    
    #提取n篇文章的目录
    allarticle_dictionary = []
    for item in extracted_content:
        print(item)
        if item:
            titles_list = extract_titles(item)
            allarticle_dictionary.append(titles_list)
    
    file_path = 'article_tittles6.json'

    # 使用 with 语句打开文件，确保文件最后会被正确关闭
    with open(file_path, 'w', encoding='utf-8') as file:
        # 将 JSON 列表写入文件
        json.dump(allarticle_dictionary, file, ensure_ascii=False, indent=4)
    
    chat_box.update_msg(f"正在预测患者问题")
    #print(f"数据已写入 {file_path}")
#目录格式[[],[],[],[]]每个小框内包含每篇文章的目录
    patient_intent = []
    logger.info("意图预测结果：")
    logger.info(inferintent)  
    # for item in inferintent[:3]:
    #     for key , value in intent_expl.items():
    #         if key == item[0] and key not in ["Patient-Confirm","Patient-Other_Feedback","Patient-Greet"]:
    #             patient_intent.append( value)
    #         elif key == item[0] and key in ["Patient-Confirm","Patient-Other_Feedback"]:
    #             patient_intent.append('基于对话上下文，随机生一个问题,挑选对应资料标题,要求问题与患者已提出问题不重复')
    # logger.info("根据前三意图提出的要求：")
    logger.info(patient_intent)

    PROMPT_DICT = {
        "context": f"""
#目标
假设你是一名医师助理，能准确的筛选帮助医生诊疗的参考资料。请你结合资料的目录、对话内容、要求，为医生选择所需资料的对应标题。
#资料的目录
-{len(allarticle_dictionary)}个条目
'{allarticle_dictionary}'
#对话内容
'{dialog_history}'
#要求
# 回答步骤
1.阅读资料的目录，根据患者的问题{dialog_history[-1]}，结合对话上文，分析患者需求，在{len(allarticle_dictionary)}条资料条目的h1总标题中，选出可能包含患者需求内容的条目的总标题，要求照搬原标题，不对标题做任何修改。
2.阅读资料的目录，阅读对话内容，再阅读要求，推断患者还会问的问题，这些问题不能和对话内容中已有的问题重复。以患者的口吻提问，填写问题序号对应的问题，再填写与问题相关的全部目录标题，要求照搬原标题，不对标题做任何修改。如果挑选的子标题被父标题全部包含，则只给出父标题，如果挑选的子标题只被父标题部分包含，则只给出子标题。
#输出格式
按照以下格式输出：
#相关资料
['总标题1','总标题2'...]
""",
        "context2": f"""
#目标
根据对话内容，根据要求的内容，依据提供的相关资料的标题，生成涉及资料内容的{len(patient_intent)}条患者会问的问题。
#对话内容
'{dialog_history}'
#要求
'{patient_intent}'
相关资料标题
'{allarticle_dictionary}'
生成的问题不能和对话内容中已有的问题重复。以患者的口吻提问，填写问题序号对应的问题，生成{len(patient_intent)}条问题，问题要结合要求，并且涉及相关资料里存在的内容。
#输出格式
按照json格式输出：
{{
    "患者问题1":"问题内容",
    "患者问题2":"问题内容",
    ......
}}
""",
}
#     PROMPT_DICT2 = {
#         "context": f"""
# ## 目标
# 假设你是一名医生，你能为患者提供专业的诊疗建议。结合资料、病历、要求，诊断患者病情，为患者可能要问的问题提供回复。
# ## 相关资料的目录
# '{extracted_content}'
# ## 对话内容
# '{dialog_history}'
# ## 要求
# '{patient_intent}'
# ## 回答步骤
# 1.根据当前医患对话患者病历、校验病历完整性，结合医学搜索工具联网搜索到的资料，基于已经给出的病历内容，判断是否能够确诊资料中的某些相关病症，如果可以，则结合相关资料，给出诊断及建议，填在根据联网搜索的资料给出的诊断及建议部分。如果已有病例不能给出确切诊断，结合=病例信息中缺损的内容，给出患者需要提供的相关信息，填在还需要患者提供的信息部分。
# 2.阅读相关资料，再阅读要求中的问题，结合要求，倒推患者可能想问的问题，以患者的口吻提问，之后在相关资料中寻找对应的标题，作为对患者问题的回答。
# ## 输出格式
# #根据联网搜索的资料给出的诊断及建议
# - 
# #还需要患者提供的信息
# - 
# #患者可能想问的问题
# (针对要求,患者会问的{len(patient_intent)}个问题)
# """
#     }
    Template = """
#问题序号{index}
问题:
对应资料标题:['标题1','标题2'...]
"""  
    # formatted_parts = [Template.format(index=str(i+1)) for i in range(len(patient_intent))]
    # formatted_string = "\n".join(formatted_parts)  
    # content = PROMPT_DICT["context"] + formatted_string
    #print("final_res模板1")
    #print(content)
    logger.info('患者问题生成prompt：\n' )
    logger.info(PROMPT_DICT["context2"])
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
                    "content": PROMPT_DICT["context2"]
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
    logger.info('患者问题')
    logger.info(full_content)
    def Postprocess3(result):
        first_bracket = result.find('{')
# 找到最后一个}的位置
        last_bracket = result.rfind('}')

        extracted_content = ''
        if first_bracket != -1 and last_bracket != -1 and first_bracket < last_bracket:
            # 截取第一个{和最后一个}之间的内容
            extracted_content = result[first_bracket :last_bracket+1]
        #print(extracted_content)
        extracted_content = extracted_content.replace('\n', '').replace('\r', '')
        extracted_content = extracted_content.replace('\\n', '').replace('\\r', '')
        data = json.loads(extracted_content)
        #print(extracted_content)
        return data
    
    questionlist = {}
    data = Postprocess3(full_content)
    questionlist['患者问题0'] = dialog_history[-1]
    for key ,value in data.items():
        questionlist[key] = value

    #患者问题格式：
        # {
        #   患者问题0:xxxxxx
        #   患者问题1:xxxxxxx  
        # }
    context3 = f"""
#目标
假设你是一名医师助理，能准确的筛选帮助医生诊疗的参考资料。请你结合资料的目录、对话内容、患者问题，为医生选择所需资料的对应标题。
#资料的目录
-{len(allarticle_dictionary)}个条目
'{allarticle_dictionary}'
#对话内容
'{dialog_history}'
#患者问题
'{questionlist}'
#回答要求
阅读资料的目录，根据患者的问题，结合对话上文，分析患者需求，在{len(allarticle_dictionary)}条资料条目的标题中，如果这个条目中包含患者需求内容的条目的标题，则先选出条目的h1总标题，之后选择该条目中的子标题，要求照搬原标题，不对标题做任何修改。
必选总标题，对于除了总标题以外的标题，如果挑选的子标题被父标题全部包含，则只给出父标题，如果挑选的子标题只被父标题部分包含，则只给出子标题。
将患者问题原内容，问题对应资料，以key、value格式输出。
#输出格式
按照如下json格式输出：
{{
    "问题0原内容":"["h1总标题1","标题1","标题2","h1总标题2"...]",
    "问题1原内容":"["h1总标题1","标题1","标题2","h1总标题2"...]",
    ......
}}
"""
    #print("最终result1")
    #print(full_content) 
    logger.info('患者问题：\n' )
    logger.info(questionlist)
    chat_box.update_msg(f"正在根据预测问题生成回答")
    #生成问题对应标题
    results = client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                },
                {
                    "role": "user",
                    "content": context3
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
    referencelist ={}
    data2 = Postprocess3(full_content)
    for key, value_str in data2.items():
        try:
            if isinstance(value_str, list):
                pass
            # 使用 ast.literal_eval() 将字符串转换为列表
            else:   
                # print(1111111111111111111111)
                # print(value_str)
                value_str = value_str.strip(" ").split("[")[1].split("]")[0].split(",")
            referencelist[key] = value_str
        except ValueError as e:
            # 如果转换失败，打印错误信息
            print(f"ValueError: {e}")
    #referencelist = data2
    # for key ,value in data2.items():
    #     referencelist[key] = ast.literal_eval(value)
    logger.info('问题对应标题')
    logger.info(data2)
    logger.info(referencelist)
    # for key,value in data2.items():
    #     referencelist.append(value)
    #参考资料list格式 
    # {
    #     问题0原内容（患者最后一句话）：对应资料标题list
    #     问题1原内容:对应资料标题list
    # }
    def PostProcess(referencelist,allarticle_dictionary):
        # main_titles =  ast.literal_eval(full_content.split('#相关资料')[1].split('#问题序号')[0])  #问题0的list
        # main_titles = ast.literal_eval_eval(questionlist[0])
        # logging.info('main_titles')
        # logger.info(main_titles)
        # pattern = r"问题序号\d+\s*\n问题:(.*?)\n对应资料标题:(\[.*?\])"
        # matches = re.findall(pattern, full_content, re.DOTALL)
        
        #检查给出的标题是否都在文章标题中，不在的剔除，书写不规范的，取最相似的标题：
        #首先铺平列表
        flattened_list = [item for sublist in allarticle_dictionary for item in sublist]

        def fuzzy_match(intent, intent_list):
            # 使用difflib的SequenceMatcher来计算相似度
            ratios = [difflib.SequenceMatcher(None, intent, item).ratio() for item in intent_list]
            # 找出相似度最高的元素及其索引
            max_ratio = max(ratios)
            max_index = ratios.index(max_ratio)
            return intent_list[max_index]
        
        # for index, sub_title in enumerate(main_titles):
        #     if sub_title not in flattened_list:
        #         main_titles[index] = fuzzy_match(sub_title , flattened_list)
        # 将匹配到的问题和标题组合成字典列表
        question_list = {}
        # question_list['主要资料'] = main_titles
        for question, titles in referencelist.items():
            # 去除问题内容中的换行符和多余空格
            question_clean = re.sub(r'\s+', ' ', question).strip()
            #检查每个问题的标题列表是否合规
            for index, sub_title in enumerate(titles):
                # logger.info("sub_title")
                # logger.info(sub_title)
                if sub_title:
                    if sub_title not in flattened_list:
                        titles[index] = fuzzy_match(sub_title , flattened_list)
            # 添加到列表中
            question_list[question_clean] = titles

        

        # 将数据转换为JSON格式
        # {
        #   "问题0内容": ["标题1", "标题2"],
        #   "问题1内容": ["标题1", "标题2"],
        #   "问题2内容": ["标题1", "标题2"],
        #   "问题3内容": ["标题1", "标题2"]
        # }
        #json_data = json.dumps(data, ensure_ascii=False, indent=2)
        return question_list
    
    referencelist = PostProcess(referencelist, allarticle_dictionary)
    logger.info('处理过的标题结果提取成json：\n' )
    logger.info(referencelist)
    # def extract_contents(data, titles):
    #     contents = {}
    #     for title in titles:
    #         for key, value in data.items():
    #             if title in key:
    #                 contents[key] = value
    #             elif isinstance(value, dict):
    #                 contents.update(extract_contents(value, [title]))
    #             #     contents(extract_contents(value, [title]))
    #     return contents

    # contents_json = {}

    #for key, value in full_content.items():
    #     contents_json[key] = {}
    #     for item in extracted_content:
    #         tittle = ''
    #         for articletitle in item.keys():
    #             if '总标题' in articletitle:
    #                 tittle = articletitle
    #         # logger.info('每篇文档内容：\n' )
    #         # logger.info(item)
    #         # logger.info('需要查找的标题：\n' )
    #         # logger.info(value)
    #         temp_json = extract_contents(item, value)
    #         contents_json[key][tittle] ={}
    #         contents_json[key][tittle] = temp_json
    def extract_contents(str1, str2):
        """字符匹配"""
        start_index = str2.find(str1)
        if start_index == -1:
            return None  # 如果str1不在str2中，返回None

        # 找到str1之后的位置
        start_index += len(str1)

        # 初始化栈和str3
        stack = []
        str3 = ""
        capture = False  # 标记是否开始捕获

        # 从str1之后的位置开始遍历str2
        for i in range(start_index, len(str2)):
            char = str2[i]

            if char == '{':
                if not capture:
                    # 标记开始捕获内容
                    capture = True
                    # 清空str3，准备开始新的捕获
                    str3 = ""
                # 入栈
                stack.append(char)
            elif char == '}' and capture:
                # 出栈
                stack.pop()
                # 如果栈空了，说明找到了匹配的{}
                if not stack:
                    return str1 + ':' + str3 + str2[i]  # 返回捕获的内容，包括最后一个}
                else:
                    str3 += char
            elif capture:
                # 捕获大括号内的内容
                str3 += char

        return None  # 如果没有找到匹配的大括号，返回None

    # 问题和对应资料，存储在result中
    result = {}
    #patient_question = []
   # extracted_content_tostr = json.dumps(extracted_content, ensure_ascii=False, indent=2)#把爬取内容变成字符串
    # 遍历full_content字典的键和值
    for key,value in referencelist.items():
        #for sub_content in extracted_content:
            # logger.info('sub_content')
            #logger.info(sub_content)
            #sub_content_tostr = json.dumps(sub_content, ensure_ascii=False, indent=2)
        extracted_content_tostr = json.dumps(extracted_content, ensure_ascii=False, indent=2)
        #logger.info(sub_content_tostr)
        # for main_tittle in sub_content.keys():
        result[key] = {}
        #     result[key][main_tittle] = []
        #     # print(main_tittle)
        #     # print(result)
        h1_title = 'no_tittle'
        result[key][h1_title] = []
        if value:
            for path in value:
                if path:  
                    if 'h1' in path:
                        h1_title = path
                        result[key][h1_title] = []
                    elif extract_contents(path, extracted_content_tostr):
                        result[key][h1_title].append(extract_contents(path, extracted_content_tostr))
                # 遍历extracted_content列表
                           
    
    logger.info('带内容的文档选取结果json：\n' )
    logger.info(result)
#     contents_json格式:                 每篇文档,一定不存在前一个item的内容里包含后一个item的问题
#     {
#     "主要资料": {
#         "h1总标题xx1": [
#
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             ],
#         "h1总标题xx2": [
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             ]
#         }
#     "问题一内容": {
#         "h1总标题xx1": {
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             },
#         "h1总标题xx2": {
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             }
#         }
#     "问题二内容": {
#         "h1总标题xx1": {
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             },
#         "h1总标题xx2": {
#             "h2标题xxx": {},
#             "h3标题xxx": {},
#             "h2标题xxx": {},
#             "h4标题xxx": {}
#             }
#         }
#   }

    template3 =""""{patient_question}":"你对该问题的回答","""
    # print('questionlist')
    # print(questionlist)
    chat_box.update_msg(f"正在生成最终回复")
    formatted_temp3 = [template3.format(patient_question= questionlist[f'患者问题{i}']) for i in range(len(questionlist))]
    formatted_string = "".join(formatted_temp3)

    formatted_string1 = """"diagnosis_and_advice": "如果需要给出诊疗建议（或者更新诊疗建议），则填写，否则填写None",
"additional_info_needed": "如果目前已知患者信息大概率无法确诊，则填写还需要的内容，否则填None",}"""
    formatted_string = '{' + formatted_string + "\n" + formatted_string1
# 定义一个提示模板，它将用于向模型提问
    prompt_template2 = f"""
你是一名医生，下面是你和患者的对话历史，你有一个医疗知识检索工具，它会返回参考资料，里面包括每个问题的参考资料。然后对于患者病情给出专业的诊断、用药治疗建议或者挂号就医建议，以及对患者可能关心的问题的回复。如果患者已有确诊病史，请联系确证病史做出更准确的回答。如果不能进行准确诊断，你要问患者你还需要知道的信息。尽可能使用口语化的表达。
##患者的问题
{questionlist}
##参考资料
{result}
##医患对话历史
{dialog_history}
##患者病例
{case}
##回答步骤
1. 首先阅读患者问题，之后结合资料中每个问题对应的资料，回答患者的问题。填写在患者问题与回复部分。
2. 之后阅读对话历史，判断医生是否已经给出了诊疗建议，如果医生没有给出诊疗建议，或诊疗建议还需要更新，则判断为需要给出诊疗建议（或者更新诊疗建议）。如果不需要给出诊疗建议（或者更新诊疗建议），则在diagnosis_and_advice里填写None。
3. 如果需要给出诊疗建议（或者更新诊疗建议），首先判断患者是否已经可以确诊疾病，如果因为缺少症状描述、检查等，大概率无法确诊，请结合患者病历中缺损的信息，判断还需要患者提供什么信息，并以医生的口吻提问患者，填在additional_info_needed部分。否则，如果患者大概率已经可以确诊，则表明不需要额外信息，在additional_info_needed这里填写None。
4. 最后，如果需要给患者诊疗建议（或者需要更新诊疗建议），且患者已大概率确诊，则根据资料、对话历史和患者的病例，给出专业的诊断、用药治疗建议或者挂号就医建议，请不要模棱两可，给出准确的回答，将诊疗建议填写在diagnosis_and_advice部分。
##输出格式
以json格式输出
{formatted_string}
"""
# 2. 然后，根据对话历史和资料，分析和整理出可能的病例，包括可能的并发��、可能的��险因素和可能的治��方案。
# 3. 接下来，根据��者的��状和所需的��断，在资料中��找相关的病例和治��方案，并对照资料和对话历史中的信息，找出最相关的病例和治��方案。
    #logger.info("生成诊断、反问、患者可能的问题和回复 prompt")
    #logger.info(prompt_template2)
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
                    "content": prompt_template2
                }
        ],
            top_p= 0.7,
            temperature= 0.5,
            max_tokens=2048,
            stream=True,
        )
    full_content = ""
    for chunk in results:
# 每个chunk都有一个choices列表，我们取第一个choice的delta的content
        content = chunk.choices[0].delta.content
        full_content += content
    logger.info('诊断、反问、患者可能的问题和回复')
    logger.info(full_content)
    def Postprocess2(result):
        first_bracket = result.find('{')
# 找到最后一个}的位置
        last_bracket = result.rfind('}')

        extracted_content = ''
        if first_bracket != -1 and last_bracket != -1 and first_bracket < last_bracket:
            # 截取第一个{和最后一个}之间的内容
            extracted_content = result[first_bracket :last_bracket+1]
        extracted_content = extracted_content.replace('\n', '').replace('\r', '')
        extracted_content = extracted_content.replace('\\n', '').replace('\\r', '')
        #print(extracted_content)
        data = json.loads(extracted_content)
        #print(extracted_content)
        final_result = ''
        predict_q ={}
        for key, value in data.items():
            if key == "diagnosis_and_advice" and 'None' not in value:
                final_result += value + "\n\n"
            elif key == "additional_info_needed" and 'None' not in value:
                final_result +=  value +"\n\n"     
            elif key != "additional_info_needed" and key != "diagnosis_and_advice":
                predict_q[key] = value
        # 使用正则表达式提取问题和答案
        # pattern = r"##问题\d+:\n(.*?)-(.*?)\n"
        # matches = re.findall(pattern, result)
        # print('matches:')
        # print(matches)

        # # 将问题和答案存储在字典中
        # predict_q = {question.strip(): answer.strip() for question, answer in matches}

        # 打印结果
        # print("final_result:\n", final_result)
        # print("predict_q:\n", json.dumps(predict_q, indent=2, ensure_ascii=False))
        return final_result, predict_q
    
    final_result, predict_q = Postprocess2(full_content)
    # predict_q ={
    #     问题一:回复
    #     问题二:回复
    #     问题三:回复
    # }

    return final_result, predict_q

    

    
def dialogue_page(
    api: ApiRequest,
    is_lite: bool = False,
):
    if 'predict_q' not in st.session_state:
        st.session_state.predict_q = {}
    if 'medical_searchresult' not in st.session_state:
        st.session_state.medical_searchresult = ''
    if 'sym' not in st.session_state:
        st.session_state.sym = []
    if 'chat_state' not in st.session_state:
        st.session_state.chat_state = 0
    if  'medical_tools' not in  st.session_state:
        st.session_state.medical_tools = 0
    # if  'case_file' not in  st.session_state:
    #     st.session_state.case_file = ''
    if  'dialogue_history' not in  st.session_state:
        st.session_state.dialogue_history = []
    if  'drug_searchresult' not in  st.session_state:
        st.session_state.drug_searchresult = ''    
    if  'search_state' not in  st.session_state:
        st.session_state.search_state = 0
    # if  'predict_question_check' not in  st.session_state:
    #     st.session_state.predict_question_check = []
    # if  'intent_file' not in  st.session_state:
    #     st.session_state.intent_file = []
    if  'new_page' not in  st.session_state:
        st.session_state.new_page = 1
    if st.session_state.new_page == 1:
        st.session_state.new_page = 2
        allarticle_dictionary = []
        extracted_content = {}
        allarticle_dictionarypath = 'article_tittles6.json'
        contextfilename = './medical_scrapy6.json'
        with open(contextfilename, 'w', encoding='utf-8') as f:
            json.dump(extracted_content, f, ensure_ascii=False, indent=4)
        # 使用 with 语句打开文件，确保文件最后会被正确关闭
        with open(allarticle_dictionarypath, 'w', encoding='utf-8') as file:
            # 将 JSON 列表写入文件
            json.dump(allarticle_dictionary, file,ensure_ascii=False, indent=4)
    
    ctx = chat_box.context
    ctx.setdefault("uid", uuid.uuid4().hex)
    ctx.setdefault("file_chat_id", None)
    ctx.setdefault("llm_model", get_default_llm())
    ctx.setdefault("temperature", Settings.model_settings.TEMPERATURE)
    st.session_state.setdefault("cur_conv_name", chat_box.cur_chat_name)
    st.session_state.setdefault("last_conv_name", chat_box.cur_chat_name)

    # sac on_change callbacks not working since st>=1.34
    if st.session_state.cur_conv_name != st.session_state.last_conv_name:
        save_session(st.session_state.last_conv_name)
        restore_session(st.session_state.cur_conv_name)
        st.session_state.last_conv_name = st.session_state.cur_conv_name

    # st.write(chat_box.cur_chat_name)
    # st.write(st.session_state)
    # st.write(chat_box.context)

    @st.experimental_dialog("模型配置", width="large")
    def llm_model_setting():
        # 模型
        cols = st.columns(3)
        platforms = ["所有"] + list(get_config_platforms())
        platform = cols[0].selectbox("选择模型平台", platforms, key="platform")
        llm_models = list(
            get_config_models(
                model_type="llm", platform_name=None if platform == "所有" else platform
            )
        )
        llm_models += list(
            get_config_models(
                model_type="image2text", platform_name=None if platform == "所有" else platform
            )
        )
        llm_model = cols[1].selectbox("选择LLM模型", llm_models, key="llm_model")
        temperature = cols[2].slider("Temperature", 0.0, 1.0, key="temperature")
        system_message = st.text_area("System Message:", key="system_message")
        if st.button("OK"):
            rerun()

    @st.experimental_dialog("重命名会话")
    def rename_conversation():
        name = st.text_input("会话名称")
        if st.button("OK"):
            chat_box.change_chat_name(name)
            restore_session()
            st.session_state["cur_conv_name"] = name
            rerun()

    with st.sidebar:
        tab1, tab2 = st.tabs(["工具设置", "会话设置"])

        with tab1:
            use_agent = st.checkbox(
                "启用Agent", help="请确保选择的模型具备Agent能力", key="use_agent"
            )
            output_agent = st.checkbox("显示 Agent 过程", key="output_agent")

            prd_question = st.checkbox("开启预测意图选择", key="prd_question")

            intent_check = st.checkbox("开启意图预测", key="intent_check")

            # 选择工具
            tools = list_tools(api)
            tool_names = ["None"] + list(tools)
            if use_agent:
                # selected_tools = sac.checkbox(list(tools), format_func=lambda x: tools[x]["title"], label="选择工具",
                # check_all=True, key="selected_tools")
                selected_tools = st.multiselect(
                    "选择工具+1",
                    list(tools),
                    format_func=lambda x: tools[x]["title"],
                    key="selected_tools",
                )
            else:
                # selected_tool = sac.buttons(list(tools), format_func=lambda x: tools[x]["title"], label="选择工具",
                # key="selected_tool")
                selected_tool = st.selectbox(
                    "选择工具",
                    tool_names,
                    format_func=lambda x: tools.get(x, {"title": "None"})["title"],
                    key="selected_tool",
                )
                selected_tools = [selected_tool]
            selected_tool_configs = {
                name: tool["config"]
                for name, tool in tools.items()
                if name in selected_tools
            }

            if "None" in selected_tools:
                selected_tools.remove("None")
            # 当不启用Agent时，手动生成工具参数
            # TODO: 需要更精细的控制控件
            tool_input = {}
            if not use_agent and len(selected_tools) == 1:
                with st.expander("工具参数", True):
                    for k, v in tools[selected_tools[0]]["args"].items():
                        if choices := v.get("choices", v.get("enum")):
                            tool_input[k] = st.selectbox(v["title"], choices)
                        else:
                            if v["type"] == "integer":
                                tool_input[k] = st.slider(
                                    v["title"], value=v.get("default")
                                )
                            elif v["type"] == "number":
                                tool_input[k] = st.slider(
                                    v["title"], value=v.get("default"), step=0.1
                                )
                            else:
                                tool_input[k] = st.text_input(
                                    v["title"], v.get("default")
                                )

            # uploaded_file = st.file_uploader("上传附件", accept_multiple_files=False)
            # files_upload = process_files(files=[uploaded_file]) if uploaded_file else None
            files_upload = None

            # 用于图片对话、文生图的图片
            upload_image = None
            def on_upload_file_change():
                if f := st.session_state.get("upload_image"):
                    name = ".".join(f.name.split(".")[:-1]) + ".png"
                    st.session_state["cur_image"] = (name, PILImage.open(f))
                else:
                    st.session_state["cur_image"] = (None, None)
                st.session_state.pop("paste_image", None)

            st.file_uploader("上传图片", ["bmp", "jpg", "jpeg", "png"],
                                            accept_multiple_files=False,
                                            key="upload_image",
                                            on_change=on_upload_file_change)
            paste_image = paste_image_button("黏贴图像", key="paste_image")
            cur_image = st.session_state.get("cur_image", (None, None))
            if cur_image[1] is None and paste_image.image_data is not None:
                name = hashlib.md5(paste_image.image_data.tobytes()).hexdigest()+".png"
                cur_image = (name, paste_image.image_data) 
            if cur_image[1] is not None:
                st.image(cur_image[1])
                buffer = io.BytesIO()
                cur_image[1].save(buffer, format="png")
                upload_image = upload_image_file(cur_image[0], buffer.getvalue())

        with tab2:
            # 会话
            cols = st.columns(3)
            conv_names = chat_box.get_chat_names()

            def on_conv_change():
                print(conversation_name, st.session_state.cur_conv_name)
                save_session(conversation_name)
                restore_session(st.session_state.cur_conv_name)

            conversation_name = sac.buttons(
                conv_names,
                label="当前会话：",
                key="cur_conv_name",
                # on_change=on_conv_change, # not work
            )
            chat_box.use_chat_name(conversation_name)
            conversation_id = chat_box.context["uid"]
            if cols[0].button("新建", on_click=add_conv):
                st.session_state.predict_q = {}
                st.session_state.medical_searchresult = ''
                st.session_state.sym = []
                st.session_state.chat_state = 0
                st.session_state.medical_tools = 0
            # if  'case_file' not in  st.session_state:
            #     st.session_state.case_file = ''
                st.session_state.dialogue_history = []
                st.session_state.new_page = 1
                st.session_state.drug_searchresult = ''
                st.session_state.search_state = 0
                ...
            if cols[1].button("重命名"):
                rename_conversation()
            if cols[2].button("删除", on_click=del_conv):
                ...

    # Display chat messages from history on app rerun
    chat_box.output_messages()
    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter。"

    # def on_feedback(
    #         feedback,
    #         message_id: str = "",
    #         history_index: int = -1,
    # ):

    #     reason = feedback["text"]
    #     score_int = chat_box.set_feedback(feedback=feedback, history_index=history_index)
    #     api.chat_feedback(message_id=message_id,
    #                       score=score_int,
    #                       reason=reason)
    #     st.session_state["need_rerun"] = True

    # feedback_kwargs = {
    #     "feedback_type": "thumbs",
    #     "optional_text_label": "欢迎反馈您打分的理由",
    # }

    # TODO: 这里的内容有点奇怪，从后端导入Settings.model_settings.LLM_MODEL_CONFIG，然后又从前端传到后端。需要优化
    #  传入后端的内容
    llm_model_config = Settings.model_settings.LLM_MODEL_CONFIG
    chat_model_config = {key: {} for key in llm_model_config.keys()}
    for key in llm_model_config:
        if c := llm_model_config[key]:
            model = c.get("model", "").strip() or get_default_llm()
            chat_model_config[key][model] = llm_model_config[key]
    llm_model = ctx.get("llm_model")
    if llm_model is not None:
        chat_model_config["llm_model"][llm_model] = llm_model_config["llm_model"].get(
            llm_model, {}
        )

    # chat input
    with bottom():
        st.markdown("""
<style>
.st-emotion-cache-p4micv {
    width: 6rem;
    height: 6rem;
    flex-shrink: 0;
    border-radius: 0.5rem;
    object-fit: cover;
    display: flex;
}         
.st-emotion-cache-1eo1tir {
    padding: 3.5rem 1rem 1rem;
    max-width: 85rem;
}
.st-emotion-cache-arzcut {
    padding: 1rem 1rem 55px;
    max-width: 85rem;
}
.st-emotion-cache-1c7y2kd {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    border-radius: 0.5rem;
    background-color: #ffd3c0;
    flex-direction: row-reverse;
    width: 60rem;
    margin-left: 25rem;
    padding: 1rem 2rem 1rem 2rem;
}
.st-emotion-cache-4oy321 {
    display: flex;
    align-items: flex-start;
    gap: 0rem;
    padding: 2rem 2rem 2rem 2rem;
    border-radius: 0.5rem;
    width: 60rem;
    margin-right: 25rem;
    background-color: #dbd3f9;
}
.st-emotion-cache-4oy321 p {
    float: left;
    margin: 0px 0px 0rem 0rem;
}
.st-emotion-cache-1c7y2kd p {
    float: right;
    margin: 0px 0px 0rem 0rem;
} 
</style>
""", unsafe_allow_html=True)
        # 自定义对话气泡的HTML和CSS
        cols = st.columns([1, 0.2, 15,  1])
        if cols[0].button(":gear:", help="模型配置"):
            widget_keys = ["platform", "llm_model", "temperature", "system_message"]
            chat_box.context_to_session(include=widget_keys)
            llm_model_setting()
        if cols[-1].button(":wastebasket:", help="清空对话"):
            chat_box.reset_history()
            rerun()
        # with cols[1]:
        #     mic_audio = audio_recorder("", icon_size="2x", key="mic_audio")
        prompt = cols[2].chat_input(chat_input_placeholder, key="prompt")
    if st.session_state.chat_state == 0:
        chat_box.ai_say("你好，我是你的在线医生，请问有什么可以帮助你的吗")
        st.session_state.chat_state = 1
    if prompt:
        st.session_state.predict_q = {}
        history = get_messages_history(
            chat_model_config["llm_model"]
            .get(next(iter(chat_model_config["llm_model"])), {})
            .get("history_len", 1)
        )

        is_vision_chat = upload_image and not selected_tools

        if is_vision_chat: # multimodal chat
            chat_box.user_say([Image(get_image_file_url(upload_image), width=100), Markdown(prompt)])
        else:
            chat_box.user_say(prompt)
        if files_upload:
            if files_upload["images"]:
                st.markdown(
                    f'<img src="data:image/jpeg;base64,{files_upload["images"][0]}" width="300">',
                    unsafe_allow_html=True,
                )
            elif files_upload["videos"]:
                st.markdown(
                    f'<video width="400" height="300" controls><source src="data:video/mp4;base64,{files_upload["videos"][0]}" type="video/mp4"></video>',
                    unsafe_allow_html=True,
                )
            elif files_upload["audios"]:
                st.markdown(
                    f'<audio controls><source src="data:audio/wav;base64,{files_upload["audios"][0]}" type="audio/wav"></audio>',
                    unsafe_allow_html=True,
                )
        #text = chat_box.to_json(pretty=True)
        text = get_messages_history(30)
        save_history_to_file( text, './chat_history6.json')
        chat_box.ai_say("正在思考...")
        #chat_box.
        text = ""
        started = False

        client = openai.Client(base_url=f"{api_address()}/chat", api_key="NONE")
        if is_vision_chat: # multimodal chat
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": get_image_file_url(upload_image)}}
            ]
            messages = [{"role": "user", "content": content}]
        else:
            messages = history + [{"role": "user", "content": prompt}]
        tools = list(selected_tool_configs)
        if len(selected_tools) == 1:
            tool_choice = selected_tools[0]
        else:
            tool_choice = None
        # 如果 tool_input 中有空的字段，设为用户输入
        for k in tool_input:
            if tool_input[k] in [None, ""]:
                tool_input[k] = prompt

        extra_body = dict(
            metadata=files_upload,
            chat_model_config=chat_model_config,
            conversation_id=conversation_id,
            tool_input=tool_input,
            upload_image=upload_image,
        )
        stream = not is_vision_chat
        params = dict(
            messages=messages,
            model=llm_model,
            stream=stream, # TODO：xinference qwen-vl-chat 流式输出会出错，后续看更新
            extra_body=extra_body,
        )
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        if Settings.model_settings.MAX_TOKENS:
            params["max_tokens"] = Settings.model_settings.MAX_TOKENS

        if stream:
            try:
                for d in client.chat.completions.create(**params):
                    # import rich
                    # rich.print(d)
                    message_id = d.message_id
                    metadata = {
                        "message_id": message_id,
                    }

                    # clear initial message

                    if not started:
                        chat_box.update_msg("", streaming=False)
                        started = True

                    if d.status == AgentStatus.error:
                        st.error(d.choices[0].delta.content)
                    elif d.status == AgentStatus.tool_start and d.choices[0].delta.tool_calls[0].function.name == 'medical_search' and not st.session_state.medical_searchresult:
                        st.session_state.medical_tools = 1  
                    elif d.status == AgentStatus.llm_start:
                        #chat_box.insert_msg("正在解读工具输出结果...")
                        if not output_agent:
                             continue
                        chat_box.insert_msg("正在解读工具输出结果...")
                        text = d.choices[0].delta.content or ""
                    elif d.status == AgentStatus.llm_new_token:
                        if not output_agent:
                            continue
                        text += d.choices[0].delta.content or ""
                        chat_box.update_msg(
                            text.replace("\n", "\n\n"), streaming=True, metadata=metadata
                        )
                    elif d.status == AgentStatus.llm_end:
                        if not output_agent:
                            continue
                        chat_box.insert_msg("正在分析工具返回结果...")
                        text += d.choices[0].delta.content or ""
                        chat_box.update_msg(
                            text.replace("\n", "\n\n"), streaming=False, metadata=metadata
                        )
                    # tool 的输出与 llm 输出重复了
                    # elif d.status == AgentStatus.tool_start:
                    #     formatted_data = {
                    #         "Function": d.choices[0].delta.tool_calls[0].function.name,
                    #         "function_input": d.choices[0].delta.tool_calls[0].function.arguments,
                    #     }
                    #     formatted_json = json.dumps(formatted_data, indent=2, ensure_ascii=False)
                    #     text = """\n```{}\n```\n""".format(formatted_json)
                    #     chat_box.insert_msg( # TODO: insert text directly not shown
                    #         Markdown(text, title="Function call", in_expander=True, expanded=True, state="running"))                   
                    elif d.status == AgentStatus.tool_end and d.choices[0].delta.tool_calls[0].function.name == 'medical_search' and not st.session_state.medical_searchresult:

                        tool_output = d.choices[0].delta.tool_calls[0].tool_output
                        if d.message_type == MsgType.IMAGE:
                            for url in json.loads(tool_output).get("images", []):
                                url = f"{api.base_url}/media/{url}"
                                chat_box.insert_msg(Image(url))
                            chat_box.update_msg(expanded=False, state="complete")
                        else:
                            
                            text += f"{tool_output}"
                            # else text.startswith("医学常识"):
                            #     continue 
                            if text.startswith("检索"):
                                textlist = []
                                sym = ''
                                search_result = ''
                                drug = ''
                                textlist = text.split("根据症状查询到以下内容：")
                                sym = text.split("根据症状查询到以下内容：")[0].split("检索到的相关知识:")[1]
                                search_result = textlist[1]
                                # sym = text.split("#|#")[0].split("检索到的相关知识:")[1]
                                # search_result = text.split("#|#")[1]
                                st.session_state.medical_searchresult = search_result
                                #st.session_state.drug_searchresult = drug
                                st.session_state.sym = sym
                                st.session_state.medical_tools = 0
                                st.session_state.search_state = 1
                                break
                            elif text.startswith("已有知识"):
                                st.session_state.sym = ['origin']
                                st.session_state.search_state = 0
                                break
                            else:
                                st.session_state.medical_tools = 0
                                continue 

                    elif d.status == AgentStatus.agent_finish:
                        text = d.choices[0].delta.content or ""
                        try:
                            chatfilename = 'chat_history6.json'
                            with open(chatfilename, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            dialog_history = [] 
                            dialog_history2 = '假设你是一个医生，这是你和患者的对话历史，请根据对话历史回答患者input：\n#对话历史\n'
                            #print("对话历史")
                            for dialogue in json_data:
                                role = "患者" if dialogue["role"] == "user" else "医生"
                                dialog_history.append(f"{role}说：{dialogue['content']}")
                            for dialog in dialog_history[:-1]:
                                dialog_history2 += dialog + '\n'
                            dialog_history2 += '#患者input\n' + dialog_history[-1]
                                # dialog_history2 += dialogue["role"] + ':' + dialogue['content'] + '\n'

                            #print(dialog_history2)
                            dialogue_item ={}
                            dialogue_item["dialog_history"] = dialog_history
                            dialogue_item["final_result"] = text.replace("\n", "\n\n")
                            st.session_state.dialogue_history.append(dialogue_item)
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
                                            "content": dialog_history2
                                        }
                                ],
                                    top_p= 0.7,
                                    temperature= 0.7,
                                    max_tokens=1024,
                                    stream=True,
                                )
                            full_content = ""
                            for chunk in results:
                        # 每个chunk都有一个choices列表，我们取第一个choice的delta的content
                                content = chunk.choices[0].delta.content
                                full_content += content
                            if full_content:
                                text = full_content
                        finally:
                            chat_box.update_msg(text.replace("\n", "\n\n"))
                    elif d.status is None:  # not agent chat
                        #print("None status")
                        if getattr(d, "is_ref", False):
                            context = str(d.tool_output)
                            if isinstance(d.tool_output, dict):
                                docs = d.tool_output.get("docs", [])
                                source_documents = format_reference(kb_name=d.tool_output.get("knowledge_base"),
                                                                    docs=docs,
                                                                    api_base_url=api_address(is_public=True))
                                context = "\n".join(source_documents)

                            chat_box.insert_msg(
                                Markdown(
                                    context,
                                    in_expander=True,
                                    state="complete",
                                    title="参考资料",
                                )
                            )
                            #chat_box.insert_msg("")
                        elif getattr(d, "tool_call", None) == "text2images":  # TODO：特定工具特别处理，需要更通用的处理方式
                            for img in d.tool_output.get("images", []):
                                chat_box.insert_msg(Image(f"{api.base_url}/media/{img}"), pos=-2)
                        else:
                            text += d.choices[0].delta.content or ""

                            chatfilename = 'chat_history6.json'
                            with open(chatfilename, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            dialog_history = []
                            # # #历史记录转成字符串，并区分患者医生
                            for dialogue in json_data:
                                role = "患者" if dialogue["role"] == "user" else "医生"
                                dialog_history.append(f"{role}说：{dialogue['content']}")      
                            dialogue_item = {}
                            dialogue_item['dialog_history'] = dialog_history  
                            dialogue_item['final_result'] = text.replace("\n", "\n\n")    
                            st.session_state.dialogue_history = []   
                            st.session_state.dialogue_history.append(dialogue_item)
                            #chat_box.update_msg(final_result, streaming=False, metadata=metadata)
                            chat_box.update_msg(
                                text.replace("\n", "\n\n"), streaming=True, metadata=metadata
                            )
                    chat_box.update_msg(text, streaming=False, metadata=metadata)
                    if st.session_state.medical_tools == 1 :
                        #url = 'R-C.gif'
                        chat_box.update_msg("医学检索工具正在加载中", streaming=False, metadata=metadata)
            except Exception as e:
                st.error(e.body)
        else:
            try:
                d =client.chat.completions.create(**params)
                chat_box.update_msg(d.choices[0].message.content or "", streaming=False)
            except Exception as e:
                st.error(e.body)
    if st.session_state.sym:
        sym =st.session_state.sym
        st.session_state.sym = []
        chat_box.update_msg(f"正在汇总查询结果......")
        chatfilename = 'chat_history6.json'
        case_content = create_emptcase()
        # #打开历史对话记录
        with open(chatfilename, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        dialog_history = []
        # # #历史记录转成字符串，并区分患者医生
        for dialogue in json_data:
            role = "患者" if dialogue["role"] == "user" else "医生"
            dialog_history.append(f"{role}说：{dialogue['content']}")
        case = case_extract(dialog_history,case_content)
        dialogue_item ={}
        dialogue_item["dialog_history"] = dialog_history
        dialogue_item["case"] = case
        logger.info('病历单内容：\n' )
        logger.info(case)
        contextfilename = './medical_scrapy6.json'
        if st.session_state.search_state == 0:
            if os.path.exists(contextfilename) and os.path.getsize(contextfilename) > 0:
                with open(contextfilename, 'r', encoding='utf-8') as f:
                    former_extracted_content = json.load(f)
                extracted_content = []
                for key, value in former_extracted_content.items():
                    if value:
                        extracted_content.append(value)
                chat_box.update_msg(f"正在阅读先前已检索文档")
        # #大模型根据症状和检索内容匹配最相关的几个文档
        else:
            with open(contextfilename, 'r', encoding='utf-8') as f:
                former_extracted_content = json.load(f)

            links = AI_select( sym, search_result, dialog_history)    
            st.session_state.medical_searchresult = ''
            logger.info('最相关的文档链接是：\n')   
            extracted_content = []
            save_content = {}
            links = list(set(links))
            logger.info(links[:5])
            chat_box.update_msg(f"正在阅读以下文档......\n{links[:5]}")
            print('去重后的linkes')
            print(links)
            for link in links[:5]:
                flag = 1
                for key, value in former_extracted_content.items():
                    if link == key :
                        extracted_content.append(value)
                        save_content[link] = value
                        flag = 0
                if "drugs.dxy.cn/pc/drug" in link and flag == 1:
                    subcontent = dingxiang_content(link, "drug")
                    extracted_content.append(subcontent)
                    save_content[link] = subcontent
                elif 'dxy' in link and flag == 1:
                    subcontent = dingxiang_content(link, "case")
                    extracted_content.append(subcontent)
                    save_content[link] = subcontent
                elif flag == 1:
                    subcontent = msd_content(link)
                    extracted_content.append(subcontent)
                    save_content[link] = subcontent
            file_path = 'medical_scrapy6.json'


            # 使用 with 语句打开文件，确保文件最后会被正确关闭
            with open(file_path, 'w', encoding='utf-8') as file:
                # 将 JSON 列表写入文件
                json.dump(save_content, file, ensure_ascii=False, indent=4)

        logger.info('内容：\n' )
        logger.info(extracted_content)
        intentlist =  act_classification( dialog_history[-10:])
        dialogue_item['intentlist'] = intentlist
        if intent_check:
            logger.info('意图序列生成结果：\n' )
            logger.info(intentlist )
            for index, item in enumerate(intentlist):
                if item.startswith("Doctor") and ("Greet" in item or "Confirm" in item or "Reassure" in item):
                    intentlist[index] = item[len("Doctor-"):]
        #print(intentlist)
            inferintent = LSTM( intentlist[-20:] )  #返回概率由高到低的排序
            logger.info('意图预测结果：\n' )
            logger.info(inferintent )
            dialogue_item['inferintent'] = str(inferintent)
        #print(inferintent)
            final_result = ''
            advice,predict_q = result_gen(extracted_content, dialog_history, inferintent,case)
            dialogue_item['final_result'] = ''
            for key,value in predict_q.items():
                dialogue_item['final_result'] += value
                final_result += value
                first_key = key
                break
            if advice:
                dialogue_item['final_result'] += advice
                final_result += advice
            del predict_q[first_key]
            for key,value in predict_q.items():
                if value:
                    pass
                else:
                    del predict_q[key]
            dialogue_item['predict_q'] = predict_q
        #print(final_result)
            logger.info('最终回复\n' ) 
            logger.info(final_result)
            logger.info('预测问题\n' ) 
            logger.info(predict_q)
            st.session_state.predict_q = predict_q

            if not prd_question:
                final_result += "你可能还想了解:" + '\n\n'
                for key,val in predict_q.items():
                    final_result += key + ':' + val + '\n\n'
                chat_box.update_msg(final_result, streaming=False, metadata=metadata)
            else:
                chat_box.update_msg(final_result, streaming=False, metadata=metadata)

            # if st.session_state.predict_q and prd_question:    
            #     for question, reply in st.session_state.predict_q.items():
            #         if st.button(question):
            #             display_reply_and_clear(question, reply)
            #             dialogue_item['question'] = reply
            #             # 隐藏按钮元素
            #             st.session_state.predict_q = {}
            #             st.experimental_rerun()
            #             break
        else:
            final_result = ''
            final_result= nointent_result_gen(extracted_content, dialog_history, case)
            logger.info('最终回复\n' ) 
            dialogue_item['final_result'] = final_result
            logger.info(final_result)     
            chat_box.update_msg(final_result, streaming=False, metadata=metadata)     
        
        st.session_state.dialogue_history.append(dialogue_item)
        # if os.path.exists("tmp/image.jpg"):
        #     with open("tmp/image.jpg", "rb") as image_file:
        #         encoded_string = base64.b64encode(image_file.read()).decode()
        #         img_tag = (
        #             f'<img src="data:image/jpeg;base64,{encoded_string}" width="300">'
        #         )
        #         st.markdown(img_tag, unsafe_allow_html=True)
            # os.remove("tmp/image.jpg")
        # chat_box.show_feedback(**feedback_kwargs,
        #                        key=message_id,
        #                        on_submit=on_feedback,
        #                        kwargs={"message_id": message_id, "history_index": len(chat_box.history) - 1})

        # elif dialogue_mode == "文件对话":
        #     if st.session_state["file_chat_id"] is None:
        #         st.error("请先上传文件再进行对话")
        #         st.stop()
        #     chat_box.ai_say([
        #         f"正在查询文件 `{st.session_state['file_chat_id']}` ...",
        #         Markdown("...", in_expander=True, title="文件匹配结果", state="complete"),
        #     ])
        #     text = ""
        #     for d in api.file_chat(prompt,
        #                            knowledge_id=st.session_state["file_chat_id"],
        #                            top_k=kb_top_k,
        #                            score_threshold=score_threshold,
        #                            history=history,
        #                            model=llm_model,
        #                            prompt_name=prompt_template_name,
        #                            temperature=temperature):
        #         if error_msg := check_error_msg(d):
        #             st.error(error_msg)
        #         elif chunk := d.get("answer"):
        #             text += chunk
        #             chat_box.update_msg(text, element_index=0)
        #     chat_box.update_msg(text, element_index=0, streaming=False)
        #     chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)
    if st.session_state.predict_q and prd_question:    
        for question, reply in st.session_state.predict_q.items():
            if st.button(question):
                dialogue_item = {}
                dialogue_item[question] = reply
                st.session_state.dialogue_history.append(dialogue_item)
                display_reply_and_clear(question, reply)
                # 隐藏按钮元素
                st.session_state.predict_q = {}
                st.experimental_rerun()
                break
    now = datetime.now()
    with tab2:
        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
            "清空对话",
            use_container_width=True,
        ):
            chat_box.reset_history()
            save_history_to_file(chat_box.history, './chat_history6.txt')
            rerun()

    export_btn.download_button(
        "导出记录",
        #"".join(chat_box.export2md()),
        data=json.dumps(st.session_state.dialogue_history, indent=4, ensure_ascii=False).encode('utf-8'),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.json",
        mime="application/json",
        use_container_width=True,
    )

    # st.write(chat_box.history)
