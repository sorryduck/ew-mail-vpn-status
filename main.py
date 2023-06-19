import smtplib
import requests
import json
import time
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from random import randint


load_dotenv()


class EwonAccount:
    page_IDs = [
        'account',
        'username',
        'password',
    ]

    def __init__(self, account_info: list):
        self.account_info = account_info

        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('log-level=3')

        self.driver = webdriver.Chrome(
            options=self.options,
        )

    def login(self):
        self.driver.get(os.environ.get('DRIVER_GET_URL'))
        time.sleep(3)

        for data, ID in zip(self.account_info, self.page_IDs):
            page_input = self.driver.find_element(By.ID, ID)
            page_input.clear()
            page_input.send_keys(data)
        else:
            page_input.send_keys(Keys.ENTER)
            self.save_cookies()

    def save_cookies(self):
        for cookie in self.driver.get_cookies():
            if cookie['name'] == 'm2websession':
                 with open('cookies', 'w') as cookies:
                    cookies.write(
                        json.dumps({
                            'm2websession': f'{cookie["value"]}'
                            })
                    )

    def load_cookies(self):
        try:
            with open('cookies', 'r') as cookies:
                return json.loads(cookies.read())
        except:
            return {}
            
    def get_response(self):
        return requests.get(
            url=os.environ.get('REQUEST_URL'),
            cookies=self.load_cookies()
        )

    def get_vpn_status(self):
        vpn_status = json.loads(self.get_response().text)
        return vpn_status[0]['name'], vpn_status[0]['status']


def inform_status(status: tuple):

    sender = os.environ.get('MAIL_SENDER')
    receivers = [
        os.environ.get('MAIL_RECEIVER_ONE'), 
        os.environ.get('MAIL_RECEIVER_TWO')
        ]

    message = f'From: From Ewon Status <{sender}>\n' \
              f'Subject: Ewon {status[0]} status has changed!\n\n' \
              f'Ewon status is currently {status[1]}!'

    try:
        mail = smtplib.SMTP(
            host=os.environ.get('MAIL_HOST'),
            port=os.environ.get('MAIL_PORT'),
        )

        mail.login(
            user=os.environ.get('MAIL_LOGIN'),
            password=os.environ.get('MAIL_PASS')
        )
        mail.sendmail(sender, receivers, message)
        print("Successfully sent email")
    except smtplib.SMTPException:
        print("Error: unable to send email")


def main():

    VPN = EwonAccount([
        os.environ.get('ACCOUNT_VPN_FAB'),
        os.environ.get('ACCOUNT_VPN_FAB'),
        os.environ.get('ACCOUNT_VPN_PAS'),
    ])

    while True:

        match VPN.get_response().status_code:
            case 200:
                status = VPN.get_vpn_status()
                print(f'[{datetime.now()}] {status[0]}: {status[1]}')

                if status[1] != 'offline':
                    inform_status(status)
                    break

            case 401:
                print(f'Status code: 401\nTrying to login...')
                VPN.login()
                continue
            case status:
                print(f'Something went wrong...\nStatus code: {status}')

        time.sleep(randint(111, 312))

if __name__ == '__main__':
    main()
