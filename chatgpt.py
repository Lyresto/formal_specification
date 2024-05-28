import copy
import json
import os.path
import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle as pkl
import openai

with open('config.json') as f:
    config = json.load(f)

chat_gpt_key = config['chat_gpt_key']
openai.api_key = chat_gpt_key


class Conversation:
    def __init__(self, save_path=None, temp=0.8, model='gpt-3.5-turbo-0613'):
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
        resp = call_gpt(msg, self.temp, self.model)
        self.messages.append({"role": "assistant", "content": resp})
        if len(self.messages) > 20:
            self.messages = self.messages[1:]
        if self.save_path is not None:
            with open(self.save_path, 'wb') as __f:
                pkl.dump(self, __f)
        return resp


def call_gpt(message, temp=0.8, model='gpt-3.5-turbo-0613'):
    print(f'Call gpt, temp = {temp}, model = {model}')
    if type(message) == str:
        message = [{'role': 'user', 'content': message}]
    max_call = 20
    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=message,
                temperature=temp
            )
            break
        except Exception as e:
            print(e)
            print("fail to call gpt, trying again...")
            max_call -= 1
            if max_call == 0:
                send_email(f'GPT连续调用失败, model={model}, time={datetime.now()}, error={e}')
            time.sleep(2)
    return response['choices'][0]['message']['content']


def start_conversation(system_msg='', save_path=None, load_if_exist=False):
    if load_if_exist and save_path is not None and os.path.exists(save_path):
        with open(save_path, 'rb') as f:
            conversation = pkl.load(f)
        if len(conversation.messages) > 0 and conversation.messages[-1]["role"] == "user":
            conversation.messages = conversation.messages[:-1]
    else:
        conversation = Conversation(save_path)
        if system_msg != '':
            conversation.messages = [
                {"role": "system", "content": system_msg},
            ]
    return conversation


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
