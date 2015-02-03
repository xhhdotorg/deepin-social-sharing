import QtQuick 2.1
import QtQuick.Window 2.1
import Deepin.Widgets 1.0

DDialog {
    id: dialog
    x: (Screen.desktopAvailableWidth - width) / 2
    y: (Screen.desktopAvailableHeight - height) / 2
    width: 480
    height: 360

    Component.onCompleted: show()

    function setText(text) {
        share_content.setText(text)
    }

    function setScreenshot(path) {
        share_content.setScreenshot(path)
    }

    function getEnabledAccounts() {
        if (bottom_bar.state == "share") {
            return bottom_bar.getEnabledAccounts()
        } else if (bottom_bar.state == "accounts_list") {
            return accounts_list.getEnabledAccounts()
        } else {
            return []
        }
    }

    Item {
        id: mainItem
        width: parent.width
        height: 260

        ShareContent {
            id: share_content
            width: parent.width
            height: parent.height
        }

        AccountsList {
            id: accounts_list
            visible: false
            width: parent.width
            height: parent.height
        }

        AccountsPickView {
            id: accounts_pick_view
            visible: false
            parentWindow: dialog
            width: parent.width
            height: parent.height
        }
    }

    ShareBottomBar {
        id: bottom_bar
        width: parent.width
        wordCount: share_content.wordCount

        anchors.bottom: parent.bottom
        anchors.bottomMargin: -5

        onStateChanged: {
        }

        onNextButtonClicked: {
            bottom_bar.state = "accounts_list"
            share_content.leftOut()
            accounts_list.rightIn()
        }

        onShareButtonClicked: {
            var enableAccounts = dialog.getEnabledAccounts()
            print(enableAccounts)
            enableAccounts.forEach(function (account) {
                _accounts_manager.enableAccount(account)
            })
            _accounts_manager.share(share_content.text, share_content.screenshot)
        }

        Component.onCompleted: {
            var accounts = _accounts_manager.getCurrentAccounts()
            var filterMap = []
            for (var i = 0; i < accounts.length; i++) {
                if (accounts[i][1] && accounts[i][2]) {
                    filterMap.push(accounts[i][0])
                    state = "share"
                }
            }
            lightUpIcons(filterMap)
        }
    }
}
