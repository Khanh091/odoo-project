/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

const NOTIFICATION_TYPE = "notification_center/new_notification";

export const notificationCenterService = {
    dependencies: ["action", "bus_service", "notification", "orm"],

    start(env, { action, bus_service, notification, orm }) {
        const state = reactive({
            unreadCount: 0,
            notifications: [],
            loaded: false,
            loading: false,
        });

        function mapNotificationType(type) {
            return ["info", "success", "warning", "danger"].includes(type) ? type : "info";
        }

        function normalizeNotification(payload) {
            return {
                id: payload.id,
                title: payload.title || _t("Thong bao"),
                message: payload.message || "",
                notification_type: mapNotificationType(payload.notification_type),
                is_read: Boolean(payload.is_read),
                create_date: payload.create_date || "",
                action_url: payload.action_url || false,
                icon: payload.icon || false,
                source_model: payload.source_model || false,
                source_res_id: payload.source_res_id || false,
            };
        }

        function addOrUpdateNotification(payload) {
            const notificationData = normalizeNotification(payload);
            const index = state.notifications.findIndex((item) => item.id === notificationData.id);
            if (index >= 0) {
                state.notifications.splice(index, 1, {
                    ...state.notifications[index],
                    ...notificationData,
                    is_read: state.notifications[index].is_read,
                });
                return;
            }
            state.notifications.unshift({
                ...notificationData,
                is_read: false,
            });
            if (state.notifications.length > 10) {
                state.notifications.splice(10);
            }
        }

        async function loadUnreadCount() {
            try {
                state.unreadCount = await orm.call("notification.center", "get_unread_count", []);
            } catch {
                notification.add(_t("Khong the tai so thong bao chua doc."), { type: "warning" });
            }
        }

        async function loadRecent({ force = false } = {}) {
            if (state.loading || (state.loaded && !force)) {
                return;
            }
            state.loading = true;
            try {
                const records = await orm.call("notification.center", "get_recent_notifications", [10, 0]);
                state.notifications.splice(0, state.notifications.length, ...records.map(normalizeNotification));
                state.loaded = true;
            } catch {
                notification.add(_t("Khong the tai danh sach thong bao."), { type: "warning" });
            } finally {
                state.loading = false;
            }
        }

        async function markAsRead(notificationData) {
            if (!notificationData) {
                return;
            }
            const stateItem = state.notifications.find((item) => item.id === notificationData.id);
            if (notificationData.is_read || (stateItem && stateItem.is_read)) {
                notificationData.is_read = true;
                return;
            }
            await orm.call("notification.center", "mark_as_read", [notificationData.id]);
            notificationData.is_read = true;
            if (stateItem) {
                stateItem.is_read = true;
            }
            state.unreadCount = Math.max(state.unreadCount - 1, 0);
        }

        async function markAllAsRead() {
            try {
                await orm.call("notification.center", "mark_all_as_read", []);
                state.unreadCount = 0;
                for (const item of state.notifications) {
                    item.is_read = true;
                }
            } catch {
                notification.add(_t("Khong the danh dau tat ca thong bao la da doc."), {
                    type: "warning",
                });
            }
        }

        function parseActionUrl(actionUrl) {
            if (!actionUrl) {
                return {};
            }
            const url = new URL(actionUrl, browser.location.origin);
            const params = new URLSearchParams(url.hash.replace(/^#/, ""));
            return {
                model: params.get("model"),
                id: params.get("id") ? Number(params.get("id")) : false,
            };
        }

        async function openNotification(notificationData) {
            try {
                await markAsRead(notificationData);
                const fallback = parseActionUrl(notificationData.action_url);
                const sourceModel = notificationData.source_model || fallback.model;
                const sourceResId = notificationData.source_res_id || fallback.id;
                if (sourceModel && sourceResId) {
                    await action.doAction({
                        type: "ir.actions.act_window",
                        res_model: sourceModel,
                        res_id: sourceResId,
                        views: [[false, "form"]],
                        target: "current",
                    });
                    return;
                }
                if (notificationData.action_url) {
                    browser.location.assign(notificationData.action_url);
                }
            } catch {
                notification.add(_t("Ban khong the mo ban ghi lien quan den thong bao nay."), {
                    type: "danger",
                });
            }
        }

        async function openAllNotifications() {
            await action.doAction("notification_center.notification_center_action_my_notifications");
        }

        bus_service.subscribe(NOTIFICATION_TYPE, (payload) => {
            addOrUpdateNotification(payload);
            state.unreadCount += 1;
            notification.add(payload.message || "", {
                title: payload.title || _t("Thong bao moi"),
                type: mapNotificationType(payload.notification_type),
                sticky: false,
                buttons: [
                    {
                        name: _t("Mo"),
                        primary: true,
                        onClick: () => openNotification(normalizeNotification(payload)),
                    },
                ],
            });
        });
        bus_service.start();

        return {
            state,
            loadUnreadCount,
            loadRecent,
            markAllAsRead,
            openNotification,
            openAllNotifications,
        };
    },
};

registry.category("services").add("notification_center", notificationCenterService);
