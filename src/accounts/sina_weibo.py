#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Deepin Technology Co., Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from _sdks.sinaweibo_sdk import SinaWeiboMixin, APIClient, APIError

from account_base import AccountBase, TimeoutThread
from utils import getUrlQuery
from constants import SINAWEIBO, ShareFailedReason

from PyQt5.QtCore import pyqtSignal


APP_KEY = '3703706716'
APP_SECRET = 'c0ecbf8644ac043070449ad0901692b8'
CALLBACK_URL = 'http://www.linuxdeepin.com'

class GetAccountInfoThread(TimeoutThread):
    getAccountInfoFailed = pyqtSignal()
    accountInfoGot = pyqtSignal("QVariant", arguments=["accountInfo"])

    def __init__(self, client=None, verifier=None):
        super(GetAccountInfoThread, self).__init__()
        self._client = client
        self._verifier = verifier
        self.timeout.connect(self.getAccountInfoFailed)

    def setClient(self, client):
        self._client = client

    def setVerifier(self, verifier):
        self._verifier = verifier

    def run(self):
        try:
            token_info = self._client.request_access_token(self._verifier)
            account_info = self._client.users.show.get(uid=token_info["uid"])
            info = [token_info["uid"], account_info["name"],
                    token_info["access_token"], token_info["expires"]]
            self._client.set_access_token(token_info["access_token"],
                                          token_info["expires"])
            self.accountInfoGot.emit(info)
        except Exception:
            self.getAccountInfoFailed.emit()

class SinaWeibo(AccountBase):
    def __init__(self, uid='', username='', access_token='', expires=0):
        super(SinaWeibo, self).__init__()
        self.uid = uid
        self.username = username

        self._client = APIClient(SinaWeiboMixin,
                                 app_key = APP_KEY,
                                 app_secret = APP_SECRET,
                                 redirect_uri = CALLBACK_URL)
        self._client.set_access_token(access_token, expires)

        self._getAccountInfoThread = GetAccountInfoThread(self._client)
        self._getAccountInfoThread.accountInfoGot.connect(
            self.handleAccountInfoGot)
        self._getAccountInfoThread.getAccountInfoFailed.connect(
            lambda: self.loginFailed.emit(SINAWEIBO))

    def handleAccountInfoGot(self, info):
        self.accountInfoGot.emit(SINAWEIBO, info)
        self.uid = info[0]
        self.username = info[1]

    def valid(self):
        return not self._client.is_expires()

    def share(self, text, pic=None):
        if not self.enabled: return

        try:
            if pic:
                with open(pic) as _pic:
                    self._client.statuses.upload.post(status=text, pic=_pic)
            else:
                self._client.statuses.update.post(status=text)
            self.succeeded.emit(SINAWEIBO)
        except Exception, e:
            if e.__class__ == APIError and e.error_code == 21332:
                self.failed.emit(SINAWEIBO, ShareFailedReason.Authorization)
            else:
                self.failed.emit(SINAWEIBO, ShareFailedReason.Other)

    def getAuthorizeUrl(self):
        auth_url = self._client.get_authorize_url(forcelogin=True,
                                                  display="mobile")
        self.authorizeUrlGot.emit(SINAWEIBO, auth_url)

    def cancelGetAuthorizeUrl(self): pass

    def getVerifierFromUrl(self, url):
        query = getUrlQuery(url)
        return query.get("code")

    def getAccountInfoWithVerifier(self, verifier):
        self._getAccountInfoThread.setClient(self._client)
        self._getAccountInfoThread.setVerifier(verifier)
        self._getAccountInfoThread.start()

    def generateTag(self, text):
        return "#%s#" % text