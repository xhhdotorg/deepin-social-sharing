/**
 * Copyright (C) 2015 Deepin Technology Co., Ltd.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 **/
import QtQuick 2.1
import QtGraphicalEffects 1.0
import Deepin.Widgets 1.0

SlideInOutItem {
    id: root

    property var parentWindow

    signal login(string type)
    signal switchUser(string type, string uid)

    function addUser(accountType, uid, username) {
        var index = 0
        switch (accountType) {
            case "sinaweibo": {
                index = 0
                break
            }
            case "twitter": {
                index = 1
                break
            }
            //case "facebook": {
                //index = 2
                //break
            //}
        }
        var _accounts = list_view.model.get(index).accounts
        var result = []
        if (_accounts) {
            result = JSON.parse(_accounts)
        }
        result.push({
            "username": username,
            "uid": uid
            })
        list_view.model.setProperty(index, "accounts", JSON.stringify(result))
    }

    function selectUser(accountType, uid) {

        var index = 0
        switch (accountType) {
            case "sinaweibo": {
                index = 0
                break
            }
            case "twitter": {
                index = 1
                break
            }
            //case "facebook": {
                //index = 2
                //break
            //}
        }
        list_view.model.setProperty(index, "selectedUser", uid)
    }

    function clearUsers() {
        list_view.model.setProperty(0, "accounts", "")
        list_view.model.setProperty(0, "selectUser", "")
        list_view.model.setProperty(1, "accounts", "")
        list_view.model.setProperty(1, "selectUser", "")
        //list_view.model.setProperty(2, "accounts", "")
        //list_view.model.setProperty(2, "selectUser", "")
    }

    ListView {
        id: list_view
        width: parent.width
        height: parent.height
        interactive: false

        // highlight: Rectangle {
        //     clip: true

        //     RadialGradient {
        //         width: parent.width
        //         height: parent.height + 20
        //         verticalOffset: - height / 2

        //         gradient: Gradient {
        //             GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.3) }
        //             GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.0) }
        //         }
        //     }
        // }
        delegate: Item {
            id: delegate_item
            width: ListView.view.width
            height: 38

            Row {
                id: row
                width: account_icon.width + combobox.width
                height: Math.max(account_icon.implicitHeight, combobox.height)
                spacing: 10

                anchors.centerIn: parent

                Image {
                    id: account_icon
                    source: iconSource

                    anchors.verticalCenter: parent.verticalCenter
                }

                AccountsComboBox {
                    id: combobox
                    width: 120
                    visible: accounts != ""
                    parentWindow: root.parentWindow
                    selectIndex: {
                        if (accounts) {
                            var _accounts = JSON.parse(accounts)
                            for (var i = 0; i < _accounts.length; i++) {
                                if (_accounts[i].uid == selectedUser) {
                                    text = _accounts[i].username
                                    return i
                                }
                            }

                            text = _accounts[0].username
                            return 0
                        }
                        return 0
                    }
                    menu.labels: {
                        var result = []

                        if (accounts) {
                            var _accounts = JSON.parse(accounts)
                            for (var i = 0; i < _accounts.length; i++) {
                                result.push(_accounts[i].username)
                            }
                        }
                        result.push(dsTr("New account"))

                        return result
                    }
                    anchors.verticalCenter: parent.verticalCenter

                    onMenuSelect: {
                        var _accounts = JSON.parse(accounts)
                        for (var i = 0; i < _accounts.length; i++) {
                            if (menu.labels[index] &&
                                menu.labels[index] == _accounts[i].username) {
                                var uid = _accounts[i].uid
                                root.switchUser(accountType, uid)
                            }
                        }
                    }

                    onNewAccount: {
                        root.login(accountType)
                    }

                    onRemoveAccount: {
                        var _accounts = JSON.parse(accounts)
                        var uid = _accounts[menu.getIndexBeforeSorted(index)].uid
                        _accounts_manager.removeUser(accountType, uid)
                    }
                }

                DTextButton {
                    text: dsTr("Log in")
                    visible: accounts == ""

                    anchors.verticalCenter: parent.verticalCenter

                    onClicked: root.login(accountType)
                }
            }

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent

                onPressed: mouse.accepted = false
                onReleased: mouse.accepted = false
                onEntered: delegate_item.ListView.view.currentIndex = index
                onExited: delegate_item.ListView.view.currentIndex = -1
            }
        }
        model: ListModel{
            ListElement {
                iconSource: "../../images/sinaweibo_big.png"
                accountType: "sinaweibo"
                accounts: ""
                selectedUser: ""
            }
            ListElement {
                iconSource: "../../images/twitter_big.png"
                accountType: "twitter"
                accounts: ""
                selectedUser: ""
            }
            //ListElement {
                //iconSource: "../../images/facebook_big.png"
                //accountType: "facebook"
                //accounts: ""
                //selectedUser: ""
            //}
        }
    }
}
