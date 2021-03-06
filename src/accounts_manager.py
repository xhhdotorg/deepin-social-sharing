#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Deepin Technology Co., Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from i18n import _
from accounts import SinaWeibo, Twitter#, Facebook
from database import db, SINAWEIBO, TWITTER#, FACEBOOK
from constants import ShareFailedReason
from settings import SocialSharingSettings

from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal, pyqtProperty

from weakref import ref

typeClassMap = {
    SINAWEIBO: SinaWeibo,
    TWITTER: Twitter,
    #FACEBOOK: Facebook
}

class _ShareThread(QThread):
    def __init__(self, manager):
        super(_ShareThread, self).__init__()
        self.text = ""
        self.pic = ""
        self.manager = manager
        self.accounts = []

    def run(self):
        if self.manager:
            for account in self.accounts:
                tag = account.generateTag(self.manager.appName)
                if self.text == "":
                    text = _("Come and look at pictures I share! (Share with %s)") % tag
                    account.share(text, self.pic)
                else:
                    account.share(self.text + tag, self.pic)

class AccountsManager(QObject):
    """Manager of all the SNS accounts"""
    succeeded = pyqtSignal("QVariant")
    failed = pyqtSignal("QVariant")

    loginFailed = pyqtSignal(str, arguments=["accountType"])

    shareNeedAuthorization = pyqtSignal("QStringList", arguments=["urls"])
    readyToShare = pyqtSignal()
    noAccountsToShare = pyqtSignal()

    authorizeUrlGot = pyqtSignal(str, str,
        arguments=["accountType", "authorizeUrl"])
    getAuthorizeUrlFailed = pyqtSignal(str, arguments=["accountType"])
    accountAuthorized = pyqtSignal(str, str, str,
        arguments=["accountType", "uid", "username"])

    userRemoved = pyqtSignal(str, str, str,
        arguments=["accountType", "uid", "username"])

    hasNextToAuthChanged = pyqtSignal()

    def __init__(self):
        super(AccountsManager, self).__init__()
        self._sharing = False
        self._failed_accounts = []
        self._succeeded_accounts = []
        self._accounts_need_auth = []
        self._skipped_accounts = []
        self._share_thread = _ShareThread(ref(self)())
        self._settings = SocialSharingSettings()

        self._accounts = {}
        for _type in typeClassMap:
            self._accounts[_type] = self.getInitializedAccount(_type)
            account = self._accounts[_type]
            account.succeeded.connect(self._accountSucceeded)
            account.failed.connect(self._accountFailed)
            account.loginFailed.connect(self.loginFailed)
            account.authorizeUrlGot.connect(self.authorizeUrlGot)
            account.getAuthorizeUrlFailed.connect(self.getAuthorizeUrlFailed)
            account.accountInfoGot.connect(self.handleAccountInfo)

    def _checkProgress(self):
        finished_accounts = self._failed_accounts + self._succeeded_accounts
        enabled_accounts = filter(lambda x: x.enabled, self._accounts.values())
        if len(finished_accounts) == len(enabled_accounts):
            if len(self._accounts_need_auth) > 0:
                self._sharing = True
                self.shareNeedAuthorization.emit(self._accounts_need_auth)
            else:
                if len(self._succeeded_accounts) > 0:
                    self.succeeded.emit(self._succeeded_accounts)
                if len(self._failed_accounts) > 0:
                    self.failed.emit(self._failed_accounts)

    def _accountFailed(self, account, reason):
        self._failed_accounts.append(account)
        if reason == ShareFailedReason.Authorization:
            self._accounts_need_auth.append(account)
            self.hasNextToAuthChanged.emit()
        self._checkProgress()

    def _accountSucceeded(self, account):
        self._succeeded_accounts.append(account)
        self._checkProgress()

    def getInitializedAccount(self, accountType):
        account = typeClassMap[accountType]()
        records = db.fetchAccessableAccounts(accountType)
        if records:
            targetUID = self._settings.getCurrentUser(accountType)
            _records = filter(lambda x: x[0] == targetUID, records)
            if _records:
                account = typeClassMap[accountType](*_records[0])
            else:
                account = typeClassMap[accountType](*records[0])

        return account

    @pyqtProperty(bool)
    def isSharing(self):
        return self._sharing

    @pyqtProperty(bool,notify=hasNextToAuthChanged)
    def hasNextToAuth(self):
        return len(self._accounts_need_auth) > 0

    @pyqtSlot(result="QVariant")
    def getAllAccounts(self):
        result = []

        for _type in [SINAWEIBO, TWITTER]:#, FACEBOOK]:
            for account in db.fetchAccounts(_type):
                result.append([_type, account[0], account[1]])

        return result

    @pyqtSlot(str)
    def enableAccount(self, accountType):
        self._accounts[accountType].enabled = True

    @pyqtSlot(str)
    def disableAccount(self, accountType):
        self._accounts[accountType].enabled = False

    @pyqtSlot(str, str)
    def switchUser(self, accountType, userId):
        accountInfo = db.fetchAccountByUID(accountType, userId)
        if accountInfo:
            account = typeClassMap[accountType](*accountInfo)
            account.succeeded.connect(self._accountSucceeded)
            account.failed.connect(self._accountFailed)
            account.loginFailed.connect(self.loginFailed)
            account.authorizeUrlGot.connect(self.authorizeUrlGot)
            account.getAuthorizeUrlFailed.connect(self.getAuthorizeUrlFailed)
            account.accountInfoGot.connect(self.handleAccountInfo)

            self._accounts[accountType] = account
            self._settings.setCurrentUser(accountType, userId)

    @pyqtSlot(str, str)
    def removeUser(self, accountType, userId):
        accountInfo = db.fetchAccountByUID(accountType, userId)
        db.removeAccountByUID(accountType, userId)
        if str(self._accounts[accountType].uid) == str(userId):
            account = typeClassMap[accountType]()
            account.succeeded.connect(self._accountSucceeded)
            account.failed.connect(self._accountFailed)
            account.loginFailed.connect(self.loginFailed)
            account.authorizeUrlGot.connect(self.authorizeUrlGot)
            account.getAuthorizeUrlFailed.connect(self.getAuthorizeUrlFailed)
            account.accountInfoGot.connect(self.handleAccountInfo)

            self._accounts[accountType] = account

        self.userRemoved.emit(accountType, userId, accountInfo[1])

    @pyqtSlot(result="QVariant")
    def getCurrentAccounts(self):
        result = []
        for _account in self._accounts:
            account = self._accounts[_account]
            result.append([_account, account.uid, account.username])
        return result

    @pyqtSlot(str, result=str)
    def getAuthorizeUrl(self, accountType):
        return self._accounts[accountType].getAuthorizeUrl()

    @pyqtSlot()
    def cancelGetAuthorizeUrl(self):
        map(lambda x: x.cancelGetAuthorizeUrl(), self._accounts.values())

    @pyqtSlot(str, str, result=str)
    def getVerifierFromUrl(self, accountType, url):
        return self._accounts[accountType].getVerifierFromUrl(url)

    @pyqtSlot(str, str)
    def handleVerifier(self, accountType, verifier):
        self._accounts[accountType].getAccountInfoWithVerifier(verifier)

    def handleAccountInfo(self, accountType, accountInfo):
        db.saveAccountInfo(accountType, accountInfo)
        uid = accountInfo[0]
        username = accountInfo[1]
        self.accountAuthorized.emit(accountType, uid, username)

        if self._sharing and not self.hasNextToAuth:
            if self._failed_accounts:
                self.reshare()
            else:
                self.share(self._text, self._pic)

    @pyqtSlot()
    def authorizeNextAccount(self):
        if self._sharing:
            if self.hasNextToAuth:
                accountType = self._accounts_need_auth.pop()
                self.hasNextToAuthChanged.emit()
                self.getAuthorizeUrl(accountType)

    @pyqtSlot(str)
    def skipAccount(self, accountType):
        if accountType not in self._skipped_accounts:
            self._skipped_accounts.append(accountType)


    @pyqtSlot(str, result="QString")
    def accountTypeName(self, accountType):
        nameDict = {
            SINAWEIBO: _("Weibo"),
            TWITTER: _("Twitter")
        }
        return nameDict.get(accountType, accountType)

    @pyqtSlot(str, str)
    def tryToShare(self, text, pic):
        self._sharing = True
        self._text = getattr(self, "_text", text)
        self._pic = getattr(self, "_pic", pic)

        self._accounts_need_auth = []
        self.hasNextToAuthChanged.emit()
        for (accountType, account) in self._accounts.items():
            if account.enabled and not account.valid():
                self._accounts_need_auth.append(accountType)
                self.hasNextToAuthChanged.emit()

        if self._accounts_need_auth:
            self.shareNeedAuthorization.emit(self._accounts_need_auth)
        else:
            self.share(self._text, self._pic)

    @pyqtSlot()
    def share(self, text, pic):
        self.readyToShare.emit()
        self._sharing = False

        self._succeeded_accounts = []
        self._failed_accounts = []
        accounts = [y for (x, y) in self._accounts.items()
                    if x not in self._skipped_accounts]
        self._skipped_accounts = []

        if accounts:
            self._share_thread.text = text
            self._share_thread.pic = pic
            self._share_thread.accounts = accounts
            self._share_thread.start()
        else:
            self.noAccountsToShare.emit()

    def reshare(self):
        self.readyToShare.emit()
        self._sharing = False

        accounts = [self._accounts[x] for x in self._failed_accounts
                    if x not in self._skipped_accounts]
        self._failed_accounts = []

        self._share_thread.accounts = accounts
        self._share_thread.start()
