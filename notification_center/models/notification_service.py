import json
import logging
from urllib.parse import urlencode

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NotificationService(models.AbstractModel):
    _name = "notification.service"
    _description = "Generic Notification Service"

    _VALID_NOTIFICATION_TYPES = {"info", "success", "warning", "danger"}

    def _check_singleton_record(self, record, model_name, parameter_name):
        if (
            not record
            or not hasattr(record, "_name")
            or record._name != model_name
            or len(record) != 1
        ):
            raise ValidationError("%s must be a singleton %s record." % (parameter_name, model_name))

    def _check_recordset(self, recordset, model_name, parameter_name):
        if recordset and (not hasattr(recordset, "_name") or recordset._name != model_name):
            raise ValidationError("%s must be a %s recordset." % (parameter_name, model_name))

    def _validate_common_values(self, title, message, notification_type, payload):
        if not title:
            raise ValidationError("title is required.")
        if not message:
            raise ValidationError("message is required.")
        if notification_type not in self._VALID_NOTIFICATION_TYPES:
            raise ValidationError("Invalid notification_type: %s" % notification_type)
        if payload is None:
            return False
        if not isinstance(payload, dict):
            raise ValidationError("payload must be a JSON-serializable dictionary.")
        try:
            json.dumps(payload)
        except (TypeError, ValueError) as error:
            raise ValidationError("payload must be JSON serializable.") from error
        return payload

    def _build_action_url(self, source_record):
        if (
            not source_record
            or not hasattr(source_record, "_name")
            or len(source_record) != 1
            or not source_record.exists()
        ):
            return False
        query = urlencode(
            {
                "id": source_record.id,
                "model": source_record._name,
                "view_type": "form",
            }
        )
        return "/web#%s" % query

    def _prepare_source_values(
        self,
        source_record=None,
        source_module=None,
        source_model=None,
        source_res_id=None,
        action_url=None,
    ):
        if source_record:
            if (
                not hasattr(source_record, "_name")
                or len(source_record) != 1
                or not source_record.exists()
            ):
                raise ValidationError("source_record must be a valid singleton record.")
            source_model = source_model or source_record._name
            source_res_id = source_res_id or source_record.id
            action_url = action_url or self._build_action_url(source_record)
        return {
            "source_module": source_module,
            "source_model": source_model,
            "source_res_id": source_res_id,
            "action_url": action_url,
        }

    def _notification_to_bus_payload(self, notification):
        return {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "action_url": notification.action_url,
            "source_model": notification.source_model,
            "source_res_id": notification.source_res_id,
            "create_date": fields.Datetime.to_string(notification.create_date),
            "icon": notification.icon,
        }

    def _send_realtime_notification(self, notification):
        partner = notification.user_id.partner_id
        if not partner:
            return
        try:
            self.env["bus.bus"]._sendone(
                partner,
                "notification_center/new_notification",
                self._notification_to_bus_payload(notification),
            )
        except Exception:
            _logger.exception(
                "Failed to send realtime notification %s to user %s.",
                notification.id,
                notification.user_id.id,
            )

    def _normalize_users(self, users, exclude_users=None):
        if not users:
            return self.env["res.users"]
        self._check_recordset(users, "res.users", "users")
        self._check_recordset(exclude_users, "res.users", "exclude_users")
        excluded_ids = set(exclude_users.ids) if exclude_users else set()
        return users.filtered(
            lambda user: user.active and not user.share and user.id not in excluded_ids
        )

    @api.model
    def notify_user(
        self,
        user,
        title,
        message,
        notification_type="info",
        source_record=None,
        source_module=None,
        source_model=None,
        source_res_id=None,
        action_url=None,
        payload=None,
        icon=None,
        deduplication_key=None,
        realtime=True,
    ):
        self._check_singleton_record(user, "res.users", "user")
        notifications = self.notify_users(
            users=user,
            title=title,
            message=message,
            notification_type=notification_type,
            source_record=source_record,
            source_module=source_module,
            source_model=source_model,
            source_res_id=source_res_id,
            action_url=action_url,
            payload=payload,
            icon=icon,
            deduplication_key=deduplication_key,
            realtime=realtime,
        )
        return notifications[:1]

    @api.model
    def notify_users(
        self,
        users,
        title,
        message,
        notification_type="info",
        source_record=None,
        source_module=None,
        source_model=None,
        source_res_id=None,
        action_url=None,
        payload=None,
        icon=None,
        exclude_users=None,
        deduplication_key=None,
        realtime=True,
    ):
        payload = self._validate_common_values(title, message, notification_type, payload)
        users = self._normalize_users(users, exclude_users=exclude_users)
        if not users:
            return self.env["notification.center"]
        source_values = self._prepare_source_values(
            source_record=source_record,
            source_module=source_module,
            source_model=source_model,
            source_res_id=source_res_id,
            action_url=action_url,
        )

        unique_users = self.env["res.users"].browse(sorted(set(users.ids)))
        if deduplication_key:
            existing_users = set(
                self.env["notification.center"]
                .sudo()
                .search(
                    [
                        ("user_id", "in", unique_users.ids),
                        ("deduplication_key", "=", deduplication_key),
                        ("active", "=", True),
                    ]
                )
                .mapped("user_id")
                .ids
            )
            unique_users = unique_users.filtered(lambda user: user.id not in existing_users)
        if not unique_users:
            return self.env["notification.center"]

        values_list = []
        for user in unique_users:
            values = {
                "user_id": user.id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "payload": payload,
                "icon": icon,
                "deduplication_key": deduplication_key,
            }
            values.update(source_values)
            values_list.append(values)

        notifications = self.env["notification.center"].sudo().create(values_list)
        if realtime:
            for notification in notifications:
                self._send_realtime_notification(notification)
        return notifications

    @api.model
    def notify_group(
        self,
        group,
        title,
        message,
        notification_type="info",
        source_record=None,
        source_module=None,
        source_model=None,
        source_res_id=None,
        action_url=None,
        payload=None,
        icon=None,
        exclude_users=None,
        deduplication_key=None,
        realtime=True,
    ):
        self._check_singleton_record(group, "res.groups", "group")
        return self.notify_users(
            users=group.users,
            title=title,
            message=message,
            notification_type=notification_type,
            source_record=source_record,
            source_module=source_module,
            source_model=source_model,
            source_res_id=source_res_id,
            action_url=action_url,
            payload=payload,
            icon=icon,
            exclude_users=exclude_users,
            deduplication_key=deduplication_key,
            realtime=realtime,
        )

    @api.model
    def notify_groups(
        self,
        groups,
        title,
        message,
        notification_type="info",
        source_record=None,
        source_module=None,
        source_model=None,
        source_res_id=None,
        action_url=None,
        payload=None,
        icon=None,
        extra_users=None,
        exclude_users=None,
        deduplication_key=None,
        realtime=True,
    ):
        if not groups:
            users = self.env["res.users"]
        else:
            self._check_recordset(groups, "res.groups", "groups")
            users = groups.mapped("users")
        if extra_users:
            self._check_recordset(extra_users, "res.users", "extra_users")
            users |= extra_users
        return self.notify_users(
            users=users,
            title=title,
            message=message,
            notification_type=notification_type,
            source_record=source_record,
            source_module=source_module,
            source_model=source_model,
            source_res_id=source_res_id,
            action_url=action_url,
            payload=payload,
            icon=icon,
            exclude_users=exclude_users,
            deduplication_key=deduplication_key,
            realtime=realtime,
        )
