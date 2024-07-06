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
import requests

from config import config
from transformers import pipeline

chat_gpt_key = config['chat_gpt_key']
openai.api_key = chat_gpt_key
API_URL = config['huggingface_API_URL']
headers = config['huggingface_headers']


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
            resp = call_codellama(self.messages, self.temp, self.model)
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


# Mock the `query` function to simulate the AI model response
def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)

    return response.json()[0]['generated_text']


def extract_bot_response(response):
    model_replies = []
    parts = response.split('</s><s>[INST] ')

    for part in parts:
        if '[/INST]' in part:
            model_reply = part.split('[/INST] ')[1].strip()
            model_replies.append(model_reply)

    return model_replies[-1] if model_replies else None


def call_deepseek_coder(messages_ori, temp=0.8, model=config["model"]):
    print(f'[INFO] call codellama, temp = {temp}, model = {model}', end='......')

    dialog_history = "<s>[INST] <<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n<</SYS>>\n\n"

    for i, msg in enumerate(messages_ori):
        if msg['role'] == 'user':
            dialog_history += f"{msg['content']} [/INST] "
        else:
            dialog_history += f"{msg['content']} </s><s>[INST] "

    max_call = 20
    while max_call > 0:
        try:
            response = query({
                "inputs": dialog_history,
                "parameters": {
                    "max_new_tokens": 2048,
                    "temperature": temp,
                    "top_p": 0.95
                }
            })
            print('get response!')
            return extract_bot_response(response)

        except Exception as e:
            print('[ERROR]', e)
            print("[ERROR] fail to call deepseek-coder, trying again...")
            max_call -= 1
            if max_call == 0:
                send_email(f'deepseek-coder 连续调用失败, model={model}, time={datetime.now()}, error={e}')
                raise Exception(f'deepseek-coder 连续调用失败, error={e}')
            time.sleep(5)

    raise Exception("Max retries exceeded. Unable to call deepseek-coder.")


def call_codellama(messages_ori, temp=0.8, model=config["model"]):
    print(f'[INFO] call codellama, temp = {temp}, model = {model}', end='......')

    dialog_history = "<s>[INST] <<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n<</SYS>>\n\n"

    for i, msg in enumerate(messages_ori):
        if msg['role'] == 'user':
            dialog_history += f"{msg['content']} [/INST] "
        else:
            dialog_history += f"{msg['content']} </s><s>[INST] "

    max_call = 20
    while max_call > 0:
        try:
            response = query({
                "inputs": dialog_history,
                "parameters": {
                    "max_new_tokens": 2048,
                    "temperature": temp,
                    "top_p": 0.95
                }
            })
            print('get response!')
            return extract_bot_response(response)

        except Exception as e:
            print('[ERROR]', e)
            print("[ERROR] fail to call codellama, trying again...")
            max_call -= 1
            if max_call == 0:
                send_email(f'codellama 连续调用失败, model={model}, time={datetime.now()}, error={e}')
                raise Exception(f'codellama 连续调用失败, error={e}')
            time.sleep(5)

    raise Exception("Max retries exceeded. Unable to call codellama.")


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
