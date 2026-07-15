from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNotificationCenter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_group = cls.env.ref("base.group_user")
        cls.admin_group = cls.env.ref("base.group_system")
        cls.user_a = cls.env["res.users"].create(
            {
                "name": "Notification User A",
                "login": "notification_user_a",
                "email": "notification_user_a@example.com",
                "groups_id": [(6, 0, [cls.internal_group.id])],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "Notification User B",
                "login": "notification_user_b",
                "email": "notification_user_b@example.com",
                "groups_id": [(6, 0, [cls.internal_group.id])],
            }
        )
        cls.inactive_user = cls.env["res.users"].create(
            {
                "name": "Notification Inactive User",
                "login": "notification_inactive_user",
                "email": "notification_inactive_user@example.com",
                "groups_id": [(6, 0, [cls.internal_group.id])],
            }
        )
        cls.inactive_user.active = False
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Notification Portal User",
                "login": "notification_portal_user",
                "email": "notification_portal_user@example.com",
                "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )
        cls.Notification = cls.env["notification.center"]
        cls.Service = cls.env["notification.service"]

    def _create_notification(self, user, title="Test notification"):
        return self.Notification.sudo().create(
            {
                "user_id": user.id,
                "title": title,
                "message": "Body",
                "notification_type": "info",
            }
        )

    def test_user_only_reads_own_notifications(self):
        own_notifications = self.Notification.sudo().create(
            [
                {
                    "user_id": self.user_a.id,
                    "title": "A1",
                    "message": "Body",
                    "notification_type": "info",
                },
                {
                    "user_id": self.user_a.id,
                    "title": "A2",
                    "message": "Body",
                    "notification_type": "info",
                },
                {
                    "user_id": self.user_a.id,
                    "title": "A3",
                    "message": "Body",
                    "notification_type": "info",
                },
            ]
        )
        self.Notification.sudo().create(
            [
                {
                    "user_id": self.user_b.id,
                    "title": "B1",
                    "message": "Body",
                    "notification_type": "info",
                },
                {
                    "user_id": self.user_b.id,
                    "title": "B2",
                    "message": "Body",
                    "notification_type": "info",
                },
            ]
        )
        visible = self.Notification.with_user(self.user_a).search([("id", "in", own_notifications.ids)])
        self.assertEqual(set(visible.ids), set(own_notifications.ids))
        self.assertEqual(self.Notification.with_user(self.user_a).search_count([]), 3)

    def test_internal_user_cannot_create_notification(self):
        with self.assertRaises(AccessError):
            self.Notification.with_user(self.user_a).create(
                {
                    "user_id": self.user_a.id,
                    "title": "Forbidden",
                    "message": "Body",
                    "notification_type": "info",
                }
            )

    def test_internal_user_cannot_write_notification_content(self):
        notification = self._create_notification(self.user_a)
        with self.assertRaises(AccessError):
            notification.with_user(self.user_a).write({"title": "Changed"})

    def test_mark_as_read_own_notification(self):
        notification = self._create_notification(self.user_a)
        result = self.Notification.with_user(self.user_a).mark_as_read(notification.id)
        notification.invalidate_recordset(["is_read", "read_at"])
        self.assertTrue(result)
        self.assertTrue(notification.is_read)
        self.assertTrue(notification.read_at)

    def test_mark_as_read_other_user_notification_denied(self):
        notification = self._create_notification(self.user_b)
        with self.assertRaises(AccessError):
            self.Notification.with_user(self.user_a).mark_as_read(notification.id)
        notification.invalidate_recordset(["is_read", "read_at"])
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.read_at)

    def test_system_admin_reads_all_notifications(self):
        self._create_notification(self.user_a)
        self._create_notification(self.user_b)
        admin = self.env.ref("base.user_admin")
        self.assertGreaterEqual(self.Notification.with_user(admin).search_count([]), 2)

    def test_notify_groups_deduplicates_users(self):
        group_1 = self.env["res.groups"].create(
            {"name": "Notification Group 1", "users": [(6, 0, [self.user_a.id, self.user_b.id])]}
        )
        group_2 = self.env["res.groups"].create(
            {"name": "Notification Group 2", "users": [(6, 0, [self.user_b.id])]}
        )
        notifications = self.Service.notify_groups(
            groups=group_1 | group_2,
            title="Group notification",
            message="Body",
        )
        self.assertEqual(len(notifications), 2)
        self.assertEqual(set(notifications.mapped("user_id").ids), {self.user_a.id, self.user_b.id})

    def test_notify_user_creates_one_notification_recordset(self):
        notification = self.Service.notify_user(
            user=self.user_a,
            title="Assigned",
            message="Record assigned",
            realtime=False,
        )
        self.assertEqual(notification._name, "notification.center")
        self.assertEqual(len(notification), 1)
        self.assertEqual(notification.user_id, self.user_a)

    def test_notify_users_filters_inactive_shared_and_duplicate_users(self):
        users = self.env["res.users"].browse(
            [self.user_a.id, self.user_a.id, self.inactive_user.id, self.portal_user.id]
        )
        notifications = self.Service.notify_users(
            users=users,
            title="Filtered",
            message="Only internal active users",
            realtime=False,
        )
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications.user_id, self.user_a)

    def test_notify_group_uses_group_members(self):
        group = self.env["res.groups"].create(
            {"name": "Notification Single Group", "users": [(6, 0, [self.user_a.id, self.user_b.id])]}
        )
        notifications = self.Service.notify_group(
            group=group,
            title="Group notification",
            message="Body",
            realtime=False,
        )
        self.assertEqual(len(notifications), 2)
        self.assertEqual(set(notifications.mapped("user_id").ids), {self.user_a.id, self.user_b.id})

    def test_notify_groups_adds_extra_users(self):
        group = self.env["res.groups"].create(
            {"name": "Notification Extra Group", "users": [(6, 0, [self.user_a.id])]}
        )
        notifications = self.Service.notify_groups(
            groups=group,
            extra_users=self.user_b,
            title="Extra user",
            message="Body",
            realtime=False,
        )
        self.assertEqual(len(notifications), 2)
        self.assertEqual(set(notifications.mapped("user_id").ids), {self.user_a.id, self.user_b.id})

    def test_notify_groups_excludes_users(self):
        group = self.env["res.groups"].create(
            {"name": "Notification Exclude Group", "users": [(6, 0, [self.user_a.id, self.user_b.id])]}
        )
        notifications = self.Service.notify_groups(
            groups=group,
            exclude_users=self.user_a,
            title="Excluded user",
            message="Body",
            realtime=False,
        )
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications.user_id, self.user_b)

    def test_invalid_notification_type_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title="Invalid",
                message="Body",
                notification_type="bad",
                realtime=False,
            )

    def test_missing_title_or_message_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title=False,
                message="Body",
                realtime=False,
            )
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title="Title",
                message=False,
                realtime=False,
            )

    def test_multi_source_record_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title="Invalid source",
                message="Body",
                source_record=self.user_a | self.user_b,
                realtime=False,
            )

    def test_payload_must_be_json_serializable_dict(self):
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title="Invalid payload",
                message="Body",
                payload=["not", "a", "dict"],
                realtime=False,
            )
        with self.assertRaises(ValidationError):
            self.Service.notify_user(
                user=self.user_a,
                title="Invalid payload",
                message="Body",
                payload={"user": self.user_a},
                realtime=False,
            )

    def test_realtime_false_does_not_send_bus(self):
        with patch.object(type(self.env["bus.bus"]), "_sendone") as bus_send:
            notification = self.Service.notify_user(
                user=self.user_a,
                title="No realtime",
                message="Persist only",
                realtime=False,
            )
        self.assertTrue(notification.exists())
        bus_send.assert_not_called()

    def test_deduplication_key_is_per_user(self):
        first = self.Service.notify_users(
            users=self.user_a | self.user_b,
            title="Deduplicated",
            message="Body",
            deduplication_key="same-business-event",
        )
        second = self.Service.notify_users(
            users=self.user_a | self.user_b,
            title="Deduplicated again",
            message="Body",
            deduplication_key="same-business-event",
        )
        self.assertEqual(len(first), 2)
        self.assertEqual(second._name, "notification.center")
        self.assertEqual(len(second), 0)

    def test_bus_failure_does_not_rollback_notification(self):
        with patch.object(type(self.env["bus.bus"]), "_sendone", side_effect=RuntimeError("bus down")):
            notification = self.Service.notify_user(
                user=self.user_a,
                title="Bus failure",
                message="Still persisted",
            )
        self.assertTrue(notification.exists())
        self.assertEqual(notification.user_id, self.user_a)
        self.assertFalse(notification.is_read)

    def test_mark_all_as_read_only_current_user(self):
        own = self._create_notification(self.user_a)
        other = self._create_notification(self.user_b)
        count = self.Notification.with_user(self.user_a).mark_all_as_read()
        own.invalidate_recordset(["is_read", "read_at"])
        other.invalidate_recordset(["is_read", "read_at"])
        self.assertEqual(count, 1)
        self.assertTrue(own.is_read)
        self.assertTrue(own.read_at <= fields.Datetime.now())
        self.assertFalse(other.is_read)
