import os
import re
import threading
import json
import sys
import httplib2
import re


class ITC:

    def __init__(self, account_email, account_password, app_id):
        self.headers = None
        self.myacinfo = None
        self.itctx = None
        self.site = None
        self.http = None

        self.app_identifier = app_id

        self.setup_session(account_email, account_password)

    def setup_session(self, account_email, account_password):
        self.http = httplib2.Http()

        # Requests to get myacInfo cookie needed for api requests
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

        resp, content = self.http.request('https://idmsa.apple.com/appleauth/auth/signin', 'POST', headers=headers,
                                          body=json.dumps(payload))

        # Requests to get itCtx cookie needed for api requests
        self.myacinfo = re.compile('myacinfo=(.*?);').findall(resp['set-cookie'])[0]
        self.site = re.compile('site=(.*?);').findall(resp['set-cookie'])[0]

        headers = {
            'Host': 'olympus.itunes.apple.com',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie': 'dslang=US-EN; myacinfo={myacinfo}; site={site}'.format(myacinfo=self.myacinfo,
                                                                              site=self.site),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
        }

        self.http.follow_redirects = False
        resp, content = self.http.request('https://olympus.itunes.apple.com/v1/session', 'GET', headers=headers)
        self.http.follow_redirects = True

        self.itctx = re.compile('itctx=(.*?);').findall(resp['set-cookie'])[0]

        if self.myacinfo is None:
            raise Exception('Didn\'t get the myacinfo cookie')
        if self.itctx is None:
            raise Exception('Didn\'t obtain the itctx cookie')

        self.headers = {
            'Host': 'itunesconnect.apple.com',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie': 'dslang=US-EN; myacinfo={myacinfo}; site={site}; itctx={itctx}'.format(myacinfo=self.myacinfo,
                                                                                             site=self.site,
                                                                                             itctx=self.itctx),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
        }

        # We are connected
        self.max_index = self.get_max_reviews_page_index()

    def get_max_reviews_page_index(self):
        data = self.get_last_reviews()
        return int(round(int(data['data']['reviewCount']) / 100))

    def get_last_reviews(self):
        resp, content = self.http.request(
            'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews'.format(
                app_id=self.app_identifier), 'GET', headers=self.headers)

        data = json.loads(content)
        return data

    def get_reviews_by_page_index(self, page_index):
        if page_index < 1:
            raise Exception('Page index must starts from 1, dummy')
        if page_index > self.max_index:
            raise Exception('Page index is geater than max index')

        index = (page_index * 100)
        resp, content = self.http.request(
            'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews?index={index}&sort=REVIEW_SORT_ORDER_MOST_RECENT'.format(
                index=index, app_id=self.app_identifier), 'GET', headers=self.headers)
        data = json.loads(content)
        return data

    def reply_to_review(self, review_id, reply):
        if review_id <= 0:
            raise Exception('Review identifier is not correct')

        if len(reply) == 0 or reply is None:
            raise Exception('Reply must not be empty')

        payload = {
            'responseText': reply,
            'reviewId': review_id
        }

        resp, content = self.http.request(
            'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
            '/platforms/ios/reviews/{review_id}/responses'.format(review_id=review_id,
                                                                  app_id=self.app_identifier), 'POST',
            body=json.dumps(payload), headers=self.headers)
        data = json.loads(content)
        if data['statusCode'] == 'SUCCESS':
            resp, content = self.http.request(
                'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews?reviewId={review_id}'.format(
                    review_id=review_id, app_id=self.app_identifier), 'GET', headers=self.headers)
            data = json.loads(content)
            return data

        return None

    def update_reply_to_review(self, review_id, reply_id, updated_reply):
        if review_id <= 0:
            raise Exception('Review identifier is not correct')

        if reply_id <= 0:
            raise Exception('Reply identifier is not correct')

        if len(updated_reply) == 0 or updated_reply is None:
            raise Exception('Reply must not be empty')

        payload = {
            'responseText': updated_reply
        }

        resp, content = self.http.request(
            'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}'
            '/platforms/ios/reviews/{review_id}/responses/{reply_id}'.format(review_id=review_id,
                                                                             app_id=self.app_identifier,
                                                                             reply_id=reply_id), 'PUT',
            body=json.dumps(payload), headers=self.headers)
        data = json.loads(content)
        if data['statusCode'] == 'SUCCESS':
            resp, content = self.http.request(
                'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa/ra/apps/{app_id}/platforms/ios/reviews?reviewId={review_id}'.format(
                    review_id=review_id, app_id=self.app_identifier), 'GET', headers=self.headers)
            data = json.loads(content)
            return data

        return None


if __name__ == '__main__':
    itc = ITCApi('your_account_email', 'your_account_password', 'your_app_id')
    # print(itc.get_last_reviews())
    # print(itc.get_reviews_by_page_index(2))
    # print(itc.reply_to_review(1723809848, 'Thanks for your feedback'))
    # print(itc.update_reply_to_review(1723809848, 2338090, 'Thank you!'))
