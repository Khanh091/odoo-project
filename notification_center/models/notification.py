from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class NotificationCenter(models.Model):
    _name = "notification.center"
    _description = "Notification Center"
    _order = "create_date desc, id desc"

    user_id = fields.Many2one(
        "res.users",
        string="Người nhận",
        required=True,
        index=True,
        ondelete="cascade",
    )
    title = fields.Char(string="Tiêu đề", required=True)
    message = fields.Text(string="Nội dung", required=True)
    notification_type = fields.Selection(
        [
            ("info", "Thông tin"),
            ("success", "Thành công"),
            ("warning", "Cảnh báo"),
            ("danger", "Nguy hiểm"),
        ],
        string="Loại thông báo",
        default="info",
        required=True,
        index=True,
    )
    source_module = fields.Char(string="Module nguồn", index=True)
    source_model = fields.Char(string="Model nguồn", index=True)
    source_res_id = fields.Integer(string="ID bản ghi nguồn", index=True)
    action_url = fields.Char(string="URL hành động")
    payload = fields.Json(string="Dữ liệu mở rộng")
    icon = fields.Char(string="Icon")
    deduplication_key = fields.Char(string="Khóa chống trùng", index=True)
    is_read = fields.Boolean(
        string="Đã đọc",
        default=False,
        required=True,
        index=True,
    )
    read_at = fields.Datetime(string="Thời điểm đọc", readonly=True)
    active = fields.Boolean(string="Hoạt động", default=True)
    create_date = fields.Datetime(readonly=True)

    def _ensure_current_user_or_admin(self):
        if self.env.user.has_group("base.group_system"):
            return
        forbidden = self.filtered(lambda notification: notification.user_id != self.env.user)
        if forbidden:
            raise AccessError(_("Bạn không có quyền truy cập thông báo này."))

    @api.model
    def _serialize_notification(self, notification):
        return {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "is_read": notification.is_read,
            "create_date": fields.Datetime.to_string(notification.create_date),
            "action_url": notification.action_url,
            "icon": notification.icon,
            "source_model": notification.source_model,
            "source_res_id": notification.source_res_id,
        }

    @api.model
    def get_unread_count(self):
        return self.search_count(
            [
                ("user_id", "=", self.env.user.id),
                ("is_read", "=", False),
                ("active", "=", True),
            ]
        )

    @api.model
    def get_recent_notifications(self, limit=10, offset=0):
        limit = min(max(int(limit or 10), 1), 50)
        offset = max(int(offset or 0), 0)
        notifications = self.search(
            [("user_id", "=", self.env.user.id), ("active", "=", True)],
            limit=limit,
            offset=offset,
            order="create_date desc, id desc",
        )
        return [self._serialize_notification(notification) for notification in notifications]

    @api.model
    def get_notifications(self, limit=50, offset=0, unread_only=False):
        limit = min(max(int(limit or 50), 1), 100)
        offset = max(int(offset or 0), 0)
        domain = [("user_id", "=", self.env.user.id), ("active", "=", True)]
        if unread_only:
            domain.append(("is_read", "=", False))
        notifications = self.search(
            domain,
            limit=limit,
            offset=offset,
            order="create_date desc, id desc",
        )
        return [self._serialize_notification(notification) for notification in notifications]

    @api.model
    def mark_as_read(self, notification_id):
        notification = self.search(
            [
                ("id", "=", int(notification_id)),
                ("user_id", "=", self.env.user.id),
                ("active", "=", True),
            ],
            limit=1,
        )
        if not notification:
            raise AccessError(_("Bạn không có quyền đánh dấu thông báo này."))
        if not notification.is_read:
            notification.sudo().write(
                {
                    "is_read": True,
                    "read_at": fields.Datetime.now(),
                }
            )
        return True

    @api.model
    def mark_all_as_read(self):
        notifications = self.search(
            [
                ("user_id", "=", self.env.user.id),
                ("is_read", "=", False),
                ("active", "=", True),
            ]
        )
        if notifications:
            notifications.sudo().write(
                {
                    "is_read": True,
                    "read_at": fields.Datetime.now(),
                }
            )
        return len(notifications)

    def action_mark_as_read(self):
        self._ensure_current_user_or_admin()
        unread = self.filtered(lambda notification: not notification.is_read)
        if unread:
            unread.sudo().write(
                {
                    "is_read": True,
                    "read_at": fields.Datetime.now(),
                }
            )
        return True

    def action_open_source(self):
        self.ensure_one()
        self._ensure_current_user_or_admin()
        self.action_mark_as_read()
        if not self.source_model or not self.source_res_id:
            raise UserError(_("Thông báo này không có bản ghi liên quan để mở."))
        if self.source_model not in self.env:
            raise UserError(_("Model nguồn không còn tồn tại: %s") % self.source_model)
        source_record = self.env[self.source_model].browse(self.source_res_id).exists()
        if not source_record:
            raise UserError(_("Bản ghi liên quan không còn tồn tại."))
        source_record.check_access_rights("read")
        source_record.check_access_rule("read")
        return {
            "type": "ir.actions.act_window",
            "name": self.title,
            "res_model": self.source_model,
            "res_id": self.source_res_id,
            "views": [[False, "form"]],
            "target": "current",
        }
