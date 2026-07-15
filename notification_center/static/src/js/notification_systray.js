/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class NotificationCenterSystray extends Component {
    static template = "notification_center.Systray";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.notificationCenter = useService("notification_center");
        this.state = useState(this.notificationCenter.state);
        onWillStart(async () => {
            await this.notificationCenter.loadUnreadCount();
        });
    }

    get badgeValue() {
        return this.state.unreadCount > 99 ? "99+" : this.state.unreadCount;
    }

    get hasUnread() {
        return this.state.unreadCount > 0;
    }

    get notifications() {
        return this.state.notifications;
    }

    getIconClass(notification) {
        const icon = notification.icon;
        if (icon) {
            return icon;
        }
        const icons = {
            info: "fa fa-info-circle",
            success: "fa fa-check-circle",
            warning: "fa fa-exclamation-triangle",
            danger: "fa fa-times-circle",
        };
        return icons[notification.notification_type] || icons.info;
    }

    getTypeLabel(notification) {
        const labels = {
            info: _t("Thông tin"),
            success: _t("Thành công"),
            warning: _t("Cảnh báo"),
            danger: _t("Nguy hiểm"),
        };
        return labels[notification.notification_type] || labels.info;
    }

    async onBeforeOpen() {
        await this.notificationCenter.loadRecent();
    }

    async onNotificationSelected(notification) {
        await this.notificationCenter.openNotification(notification);
    }

    async onMarkAllAsRead() {
        await this.notificationCenter.markAllAsRead();
    }

    async onOpenAll() {
        await this.notificationCenter.openAllNotifications();
    }
}

export const systrayItem = {
    Component: NotificationCenterSystray,
    isDisplayed(env) {
        return Boolean(env.services.user.userId);
    },
};

registry.category("systray").add("notification_center.systray", systrayItem, { sequence: 20 });
