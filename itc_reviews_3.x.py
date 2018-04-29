from requests import session

import os
import re
import threading
import json
import sys


class ITCApi:

    def __init__(self, account_email, account_password, app_id):
        self.app_identifier = app_id
        self.setup_session(account_email, account_password)

    def setup_session(self, account_email, account_password):

        self.session = session()

        headers = {
            'Content-Type': 'application/json',
            'X-Apple-Widget-Key': '22d448248055bab0dc197c6271d738c3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/48.0.2564.116 Safari/537.36',
            'Accept': 'application/json',
            'Referrer': 'https://idmsa.apple.com',
        }

        payload = {
            'accountName': account_email,
            'password': account_password,
            'rememberMe': False,
        }

        self.session.post('https://idmsa.apple.com/appleauth/auth/signin', json=payload, headers=headers)
        #print(self.session.cookies)
        
        # Requests itunes connect page that will give us itCtx cookie needed for api requests
        self.session.get('https://olympus.itunes.apple.com/v1/session', allow_redirects=False)
        #print(self.session.cookies)
        if 'myacinfo' not in self.session.cookies.get_dict().keys():
            raise Exception('Didn\'t get the myacinfo cookie')
        if 'itctx' not in self.session.cookies.get_dict().keys():
            raise Exception('Didn\'t obtain the itctx cookie')

        # We are connected
        self.max_index = self.get_max_reviews_page_index()

    def get_max_reviews_page_index(self):
        data = self.get_last_reviews()
        return int(round(int(data['data']['reviewCount']) / 100))

    def get_last_reviews(self):
        r = self.session.get('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
                             '/platforms/ios/reviews'.format(app_id=self.app_identifier))
        data = json.loads(r.text)
        return data

    def get_reviews_by_page_index(self, page_index):
        if page_index < 1:
            raise Exception('Page index must starts from 1, dummy')
        if page_index > self.max_index:
            raise Exception('Page index is geater than max index')

        index = (page_index * 100)
        r = self.session.get('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
                             '/platforms/ios/reviews?index={'
                             'index}&sort=REVIEW_SORT_ORDER_MOST_RECENT'.format(index=index,
                                                                                app_id=self.app_identifier))
        data = json.loads(r.text)
        return data

    def reply_to_review(self, review_id, reply):
        if review_id <= 0:
            raise Exception('Review identifier is not correct')

        if len(reply) == 0 or reply is None:
            raise Exception('Reply must not be empty')

        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Host': 'itunesconnect.apple.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/44.0.2403.157 Safari/537.36 '
        }

        payload = {
            'responseText': reply,
            'reviewId': review_id
        }

        r = self.session.post('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
                              '/platforms/ios/reviews/{review_id}/responses'.format(review_id=review_id,
                                                                                    app_id=self.app_identifier),
                              json=payload, headers=headers)
        data = json.loads(r.text)
        if data['statusCode'] == 'SUCCESS':
            r = self.session.get(
                'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews?reviewId={review_id}'.format(
                    review_id=review_id, app_id=self.app_identifier))
            data = json.loads(r.text)
            return data

        return None

    def update_reply_to_review(self, review_id, reply_id, updated_reply):
        if review_id <= 0:
            raise Exception('Review identifier is not correct')

        if reply_id <= 0:
            raise Exception('Reply identifier is not correct')

        if len(updated_reply) == 0 or updated_reply is None:
            raise Exception('Reply must not be empty')

        headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Host': 'itunesconnect.apple.com',
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/44.0.2403.157 Safari/537.36 '
        }

        payload = {
            'responseText': updated_reply
        }

        r = self.session.put('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
                             '/platforms/ios/reviews/{review_id}/responses/{reply_id}'.format(review_id=review_id,
                                                                                              app_id=self.app_identifier,
                                                                                              reply_id=reply_id),
                             json=payload, headers=headers)
        data = json.loads(r.text)
        if data['statusCode'] == 'SUCCESS':
            r = self.session.get(
                'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews?reviewId={review_id}'.format(
                    review_id=review_id, app_id=self.app_identifier))
            data = json.loads(r.text)
            return data

        return None


if __name__ == '__main__':
    itc = ITCApi('your_account_email', 'your_account_password', 'your_app_id')
    # print(itc.get_last_reviews())
    # print(itc.reply_to_review(2070010131, 'Thanks for your using XXXX application!'))
    # print(itc.get_reviews_by_page_index(13))
    # print(itc.get_max_reviews_page_index())
    # print(itc.update_reply_to_review(2070010131, 2262578, 'Thanks for your feedback!'))
