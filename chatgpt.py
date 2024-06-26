import copy
import os.path
import re
import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle as pkl
import openai
from config import config
from gradio_client import Client

chat_gpt_key = config['chat_gpt_key']
openai.api_key = chat_gpt_key


class Conversation:
    def __init__(self, save_path=None, temp=0.8, model=config["model"]):
        self.messages = []
        self.save_path = save_path
        self.temp = temp
        self.model = model

    def chat(self, prompt, reserved=None):
        msg = copy.copy(self.messages)
        if reserved is not None:
            msg = []
            for idx in reserved:
                msg.append(self.messages[idx])
        self.messages.append({"role": "user", "content": prompt})
        msg.append(self.messages[-1])
        if self.model.startswith("gpt"):
            resp = call_gpt(msg, self.temp, self.model)
        else:
            resp = call_deepseek_coder(msg, self.temp, self.model)
        self.messages.append({"role": "assistant", "content": resp})
        if len(self.messages) > 20:
            self.messages = self.messages[1:]
        if self.save_path is not None:
            with open(self.save_path, 'wb') as __f:
                pkl.dump(self, __f)
        return resp


def call_gpt(message, temp=0.8, model=config["model"]):
    print(f'[INFO] call gpt, temp = {temp}, model = {model}', end='......')
    if type(message) == str:
        message = [{'role': 'user', 'content': message}]
    max_call = 20
    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=message,
                temperature=temp,
                top_p=0.95
            )
            break
        except Exception as e:
            print('[ERROR]', e)
            print("[ERROR] fail to call gpt, trying again...")
            max_call -= 1
            if max_call == 0:
                send_email(f'GPT连续调用失败, model={model}, time={datetime.now()}, error={e}')
            time.sleep(2)
    print('get response!')
    return response['choices'][0]['message']['content']


def call_deepseek_coder(messages, temp=0.8,
                        model="https://deepseek-ai-deepseek-coder-7b-instruct.hf.space/--replicas/pzzcy/"):
    print(f'[INFO] call deepseek coder, temp = {temp}, model = {model}')
    if type(messages) == list and len(messages) > 0 and isinstance(messages[0], dict):
        message = messages[0]['content']
    else:
        message = messages

    client = Client(model)
    max_call = 20
    while True:
        try:
            response = client.predict(
                message,  # str in 'Message' Textbox component
                "",  # str in 'System prompt' Textbox component
                2048,  # int | float (numeric value between 1 and 2048) in 'Max new tokens' Slider component
                0.05,  # int | float (numeric value between 0.05 and 1.0) in 'Top-p (nucleus sampling)' Slider component
                100,  # int | float (numeric value between 1 and 1000) in 'Top-k' Slider component
                1,  # int | float (numeric value between 1.0 and 2.0) in 'Repetition penalty' Slider component
                api_name="/chat"
            )
            break
        except Exception as e:
            print('[ERROR]', e)
            print("[ERROR] fail to call deepseek coder, trying again...")
            max_call -= 1
            if max_call == 0:
                send_email(f'DeepSeek Coder连续调用失败, model={model}, time={datetime.now()}, error={e}')
                raise Exception(f'DeepSeek Coder连续调用失败, error={e}')
            time.sleep(2)

    return response


def redirect_save_path(save_path):
    if save_path is None:
        return None
    paths = save_path.split('/')
    matches = re.match('(\\d+)(.*)', paths[-1])
    item_idx = int(matches.group(1))
    if paths[1] == 'humaneval-x' and (paths[3] != 'code' or (paths[3] == 'code' and item_idx // 164 == 4)):
        paths[1] = 'humaneval'
        paths[-1] = f'{item_idx % 164}{matches.group(2)}'
    elif paths[1] == 'code_contests' and paths[4] != 'code':
        paths[3] = 'python'
    return '/'.join(paths)


def start_conversation(system_msg='', save_path=None, load_if_exist=False):
    save_path = redirect_save_path(save_path)
    if load_if_exist and save_path is not None:
        save_dir = '/'.join(save_path.split('/')[:-1])
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    if load_if_exist and save_path is not None and os.path.exists(save_path):
        with open(save_path, 'rb') as __f:
            conversation = pkl.load(__f)
        if len(conversation.messages) > 0 and conversation.messages[-1]["role"] == "user":
            conversation.messages = conversation.messages[:-1]
    else:
        conversation = Conversation(save_path)
        if system_msg != '':
            conversation.messages = [
                {"role": "system", "content": system_msg},
            ]
    return conversation


class IntermediateResults:
    def __init__(self, save_path=None):
        self.specification = None
        self.testcases = None
        self.save_path = save_path

    def has_results(self):
        return self.specification is not None and self.testcases is not None

    def save(self, specification, testcases):
        self.specification = specification
        self.testcases = testcases
        if self.save_path is not None:
            with open(self.save_path, 'wb') as __f:
                pkl.dump(self, __f)
        else:
            raise Exception("No save path.")


def load_intermediate_results(save_path):
    save_path = redirect_save_path(save_path)
    if save_path is not None:
        save_dir = '/'.join(save_path.split('/')[:-1])
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    if save_path is not None and os.path.exists(save_path):
        with open(save_path, 'rb') as __f:
            return pkl.load(__f)
    return IntermediateResults(save_path)


def send_email(title_, msg_=''):
    con = smtplib.SMTP_SSL('smtp.qq.com', 465)
    con.login('2033205974@qq.com', 'iammzxgnyyendebh')

    msg = MIMEMultipart()
    subject = Header(title_, 'utf-8').encode()
    msg['Subject'] = subject

    msg['From'] = 'lyneto<2033205974@qq.com>'
    msg['To'] = '20231026@buaa.edu.cn'

    text = MIMEText(msg_, 'plain', 'utf-8')
    msg.attach(text)

    con.sendmail('2033205974@qq.com', '20231026@buaa.edu.cn', msg.as_string())
    con.quit()


if __name__ == '__main__':
    conv = start_conversation()
    while True:
        req = ""
        while True:
            req += input() + '\n'
            if req.endswith('\nsend\n'):
                break
        print(conv.chat(req))
