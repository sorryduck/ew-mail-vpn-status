import smtplib
import requests
import json
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class EwonAccount:
    page_IDs = [
        'account',
        'username',
        'password',
    ]

    options = Options()
    options.add_argument('--headless')

    def __init__(self, account_info: list):
        self.account_info = account_info
        self.driver = webdriver.Chrome(options=self.options)

    def login(self):
        self.driver.get(os.environ.get('DRIVER_GET_URL'))
        time.sleep(3)
        page_input = None

        for data, ID in zip(self.account_info, self.page_IDs):
            page_input = self.driver.find_element(By.ID, ID)
            page_input.clear()
            page_input.send_keys(data)
        else:
            page_input.send_keys(Keys.ENTER)

    def get_cookies(self) -> dict:
        for cookie in self.driver.get_cookies():
            if cookie['name'] == 'm2websession':
                return {
                    'm2websession': cookie['value'],
                }

    def get_status(self) -> tuple:
        response = requests.get(
            url=os.environ.get('REQUEST_URL'),
            cookies=self.get_cookies(),
        )

        if response.status_code == 200:
            vpn_status = json.loads(response.text)
            if 'status' in vpn_status[0].keys():
                return vpn_status[0]['name'], vpn_status[0]['status']
        else:
            raise Exception(f'Access denied {response.status_code}')


def inform_status(status: tuple):

    sender = os.environ.get('MAIL_SENDER')
    receivers = [os.environ.get('MAIL_RECEIVER_ONE'), os.environ.get('MAIL_RECEIVER_TWO')]

    message = f'From: From Ewon Status <{sender}>\n' \
              f'Subject: Ewon {status[0]} status has changed!\n\n' \
              f'Ewon status is currently {status[1]}!'

    try:
        mail = smtplib.SMTP(
            host=os.environ.get('MAIL_HOST'),
            port=587,
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
    status = None

    while True:
        try:
            if status is not None and status != VPN.get_status():
                inform_status(VPN.get_status())

            status = VPN.get_status()
            print(f'{status[0]} - {status[1]}')
            time.sleep(180)

        except Exception as e:
            logging.exception(e)
            VPN.login()


if __name__ == '__main__':
    main()
