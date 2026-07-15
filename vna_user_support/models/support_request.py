# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class VnaSupportRequest(models.Model):
    _name = "vna.support.request"
    _description = "Yêu cầu hỗ trợ người dùng"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Tiêu đề", required=True, tracking=True)
    code = fields.Char(string="Mã yêu cầu", required=True, copy=False, readonly=True, default="/", tracking=True)
    requester_id = fields.Many2one(
        "res.users",
        string="Người tạo yêu cầu",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    requester_partner_id = fields.Many2one(
        "res.partner",
        string="Liên hệ người tạo",
        related="requester_id.partner_id",
        store=True,
        readonly=True,
    )
    requester_email = fields.Char(
        string="Email người tạo",
        related="requester_id.email",
        store=True,
        readonly=True,
    )
    request_type_id = fields.Many2one(
        "vna.support.request.type",
        string="Loại yêu cầu",
        required=True,
        tracking=True,
        domain=[("active", "=", True)],
    )
    description = fields.Html(string="Nội dung yêu cầu", required=True, sanitize=True, tracking=True)
    priority = fields.Selection(
        [
            ("low", "Thấp"),
            ("normal", "Bình thường"),
            ("high", "Cao"),
            ("urgent", "Khẩn cấp"),
        ],
        string="Mức ưu tiên",
        required=True,
        default="normal",
        tracking=True,
    )
    stage_id = fields.Many2one(
        "vna.support.stage",
        string="Trạng thái",
        required=True,
        default=lambda self: self._get_initial_stage(),
        tracking=True,
        domain=[("active", "=", True)],
    )
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Người xử lý",
        tracking=True,
        domain="[('id', 'in', allowed_user_ids)]",
    )
    receiver_group_ids = fields.Many2many(
        "res.groups",
        string="Nhóm tiếp nhận",
        related="request_type_id.receiver_group_ids",
        readonly=True,
    )
    allowed_user_ids = fields.Many2many(
        "res.users",
        string="Người xử lý hợp lệ",
        compute="_compute_allowed_user_ids",
        search="_search_allowed_user_ids",
        readonly=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "vna_support_request_attachment_rel",
        "request_id",
        "attachment_id",
        string="Tệp đính kèm",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        required=True,
        default=lambda self: self.env.company,
    )
    closed_date = fields.Datetime(string="Ngày đóng", readonly=True, tracking=True)
    stage_is_closed = fields.Boolean(
        string="Đã đóng",
        related="stage_id.is_closed",
        readonly=True,
    )
    can_manage_request = fields.Boolean(
        string="Có quyền xử lý yêu cầu",
        compute="_compute_can_manage_request",
    )
    cancel_reason = fields.Text(string="Lý do hủy", tracking=True)
    active = fields.Boolean(string="Đang hoạt động", default=True)

    @api.depends("request_type_id.receiver_group_ids.users")
    def _compute_allowed_user_ids(self):
        for request in self:
            users = request.request_type_id.receiver_group_ids.mapped("users").filtered(lambda user: user.active)
            request.allowed_user_ids = users

    def _compute_can_manage_request(self):
        user = self.env.user
        is_manager = user.has_group("vna_user_support.group_vna_support_manager")
        for request in self:
            request.can_manage_request = bool(is_manager or user in request.allowed_user_ids)

    def _search_allowed_user_ids(self, operator, value):
        if operator not in ("in", "=", "not in", "!="):
            raise UserError(_("Toán tử tìm kiếm không được hỗ trợ cho người xử lý hợp lệ."))
        user_ids = value if isinstance(value, list) else [value]
        request_types = self.env["vna.support.request.type"].sudo().search(
            [("receiver_group_ids.users", "in", user_ids)]
        )
        positive_domain = [("request_type_id", "in", request_types.ids)]
        if operator in ("not in", "!="):
            return ["!", *positive_domain]
        return positive_domain

    @api.onchange("request_type_id")
    def _onchange_request_type_id(self):
        for request in self:
            if request.request_type_id:
                request.priority = request.request_type_id.default_priority
                if request.assigned_user_id and request.assigned_user_id not in request.allowed_user_ids:
                    request.assigned_user_id = False

    @api.model
    def _get_initial_stage(self):
        stage = self.env["vna.support.stage"].search(
            [("is_initial", "=", True), ("active", "=", True)],
            order="sequence, id",
            limit=1,
        )
        if not stage:
            raise UserError(_("Chưa cấu hình trạng thái khởi tạo cho yêu cầu hỗ trợ."))
        return stage

    @api.model_create_multi
    def create(self, vals_list):
        initial_stage = self._get_initial_stage()
        prepared_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            self._check_create_security(vals)
            request_type = self.env["vna.support.request.type"].browse(vals.get("request_type_id")).exists()
            if not request_type:
                raise ValidationError(_("Bạn phải chọn loại yêu cầu hỗ trợ."))
            self._validate_request_type_for_use(request_type)
            if vals.get("code", "/") == "/":
                vals["code"] = self.env["ir.sequence"].next_by_code("vna.support.request") or "/"
            vals.setdefault("stage_id", initial_stage.id)
            vals.setdefault("priority", request_type.default_priority)
            vals.setdefault("requester_id", self.env.user.id)
            prepared_vals_list.append(vals)

        requests = super().create(prepared_vals_list)
        for request in requests:
            request._validate_assigned_user()
            request._notify_created()
        return requests

    def write(self, vals):
        vals = dict(vals)
        self._check_write_security(vals)
        old_stage_by_id = {request.id: request.stage_id for request in self}
        result = super().write(vals)
        if "request_type_id" in vals:
            for request in self:
                self._validate_request_type_for_use(request.request_type_id)
                request._validate_assigned_user()
        if "assigned_user_id" in vals:
            for request in self:
                request._validate_assigned_user()
        if "stage_id" in vals:
            for request in self:
                request._handle_stage_changed(old_stage_by_id.get(request.id))
        return result

    def unlink(self):
        if not self.env.user.has_group("vna_user_support.group_vna_support_manager"):
            raise AccessError(_("Chỉ quản trị kênh hỗ trợ được xóa yêu cầu."))
        return super().unlink()

    @api.constrains("request_type_id")
    def _check_request_type(self):
        for request in self:
            self._validate_request_type_for_use(request.request_type_id)

    @api.constrains("assigned_user_id", "request_type_id")
    def _check_assigned_user(self):
        for request in self:
            request._validate_assigned_user()

    def _validate_request_type_for_use(self, request_type):
        if not request_type.active:
            raise ValidationError(_("Không thể sử dụng loại yêu cầu đã bị archive."))
        if not request_type.receiver_group_ids:
            raise ValidationError(_("Loại yêu cầu phải có ít nhất một nhóm tiếp nhận."))

    def _validate_assigned_user(self):
        for request in self:
            if request.assigned_user_id and request.assigned_user_id not in request.allowed_user_ids:
                raise ValidationError(_("Người xử lý phải thuộc một trong các nhóm tiếp nhận của loại yêu cầu."))

    def _check_create_security(self, vals):
        is_manager = self.env.user.has_group("vna_user_support.group_vna_support_manager")
        protected_fields = {
            "assigned_user_id",
            "receiver_group_ids",
            "allowed_user_ids",
            "closed_date",
            "cancel_reason",
        }
        forbidden = {field for field in protected_fields.intersection(vals) if vals.get(field)}
        if forbidden and not is_manager:
            raise AccessError(_("Bạn không được thiết lập các trường quản trị khi tạo yêu cầu: %s") % ", ".join(forbidden))
        if vals.get("stage_id") and not is_manager:
            initial_stage = self._get_initial_stage()
            if vals["stage_id"] != initial_stage.id:
                raise AccessError(_("Bạn không được tự thiết lập trạng thái khi tạo yêu cầu."))
        if vals.get("requester_id") and vals["requester_id"] != self.env.user.id and not is_manager:
            raise AccessError(_("Bạn không được tạo yêu cầu thay người dùng khác."))

    def _check_write_security(self, vals):
        if not vals:
            return
        user = self.env.user
        is_manager = user.has_group("vna_user_support.group_vna_support_manager")
        is_agent = user.has_group("vna_user_support.group_vna_support_agent")
        protected_fields = {
            "stage_id",
            "assigned_user_id",
            "receiver_group_ids",
            "allowed_user_ids",
            "closed_date",
            "cancel_reason",
        }
        if is_manager:
            return
        if "requester_id" in vals and vals["requester_id"] != user.id:
            raise AccessError(_("Bạn không được đổi người tạo yêu cầu sang người khác."))
        if protected_fields.intersection(vals):
            if not is_agent:
                raise AccessError(_("Bạn không được thay đổi trạng thái, người xử lý hoặc dữ liệu quản trị của yêu cầu."))
            for request in self:
                if user not in request.allowed_user_ids:
                    raise AccessError(_("Bạn không thuộc nhóm tiếp nhận của yêu cầu này nên không được xử lý."))

    def _handle_stage_changed(self, old_stage):
        self.ensure_one()
        values = {}
        if self.stage_id.is_closed and not self.closed_date:
            values["closed_date"] = fields.Datetime.now()
        elif not self.stage_id.is_closed and self.closed_date:
            values["closed_date"] = False
        if values:
            super(VnaSupportRequest, self).write(values)
        self.message_post(
            body=_("Trạng thái đã chuyển từ '%s' sang '%s'.") % ((old_stage and old_stage.display_name) or "", self.stage_id.display_name),
            subtype_xmlid="mail.mt_note",
        )
        self._send_stage_changed_emails()
        self._notify_stage_changed(old_stage)

    def _get_receiver_users(self):
        self.ensure_one()
        users = self.request_type_id.receiver_group_ids.mapped("users").filtered(lambda user: user.active and user.email)
        return users

    def _notify_created(self):
        self.ensure_one()
        receiver_users = self._get_receiver_users()
        if not self.request_type_id.receiver_group_ids.mapped("users").filtered(lambda user: user.active):
            self.message_post(
                body=_("Cảnh báo: chưa có người dùng active trong các nhóm tiếp nhận của loại yêu cầu này."),
                subtype_xmlid="mail.mt_note",
            )
        users_without_email = self.request_type_id.receiver_group_ids.mapped("users").filtered(
            lambda user: user.active and not user.email
        )
        if users_without_email:
            self.message_post(
                body=_("Cảnh báo: một số người dùng trong nhóm tiếp nhận chưa có email nên không nhận được thông báo."),
                subtype_xmlid="mail.mt_note",
            )
        self._send_new_request_receiver_emails(receiver_users)
        self._send_requester_confirmation_email()
        telegram_sent = self.env["vna.support.telegram.service"].sudo().send_new_request_message(self)
        self.message_post(
            body=_("Yêu cầu đã được tạo. Telegram: %s.") % (_("đã gửi") if telegram_sent else _("không gửi hoặc gửi lỗi")),
            subtype_xmlid="mail.mt_note",
        )

        self._notify_new_request()

    def _notify_new_request(self):
        self.ensure_one()
        try:
            return self.env["notification.service"].notify_groups(
                groups=self.request_type_id.receiver_group_ids,
                title=_("Có yêu cầu hỗ trợ mới"),
                message="%s - %s" % (self.code, self.name),
                notification_type="warning",
                source_record=self,
                source_module="vna_user_support",
                payload={
                    "request_id": self.id,
                    "request_code": self.code,
                    "request_type": self.request_type_id.name,
                    "priority": self.priority,
                },
                deduplication_key="vna_support:new:%s" % self.id,
            )
        except Exception:
            _logger.exception(
                "VNA support notification center new request failed for request %s.",
                self.id,
            )
            return False

    def _send_new_request_receiver_emails(self, receiver_users):
        template = self.env.ref("vna_user_support.email_template_vna_support_new_request_receiver", raise_if_not_found=False)
        if not template:
            return
        for user in receiver_users:
            self._safe_send_template_email(
                template,
                email_to=user.email,
                context={"recipient_user": user},
            )

    def _send_requester_confirmation_email(self):
        if not self.requester_email:
            return
        template = self.env.ref("vna_user_support.email_template_vna_support_requester_confirmation", raise_if_not_found=False)
        if not template:
            return
        self._safe_send_template_email(
            template,
            email_to=self.requester_email,
            context={"recipient_user": self.requester_id},
        )

    def _send_stage_changed_emails(self):
        template = self.env.ref("vna_user_support.email_template_vna_support_stage_changed", raise_if_not_found=False)
        if not template:
            return
        recipients = self._get_receiver_users()
        if self.requester_id.active and self.requester_email:
            recipients |= self.requester_id
        seen_emails = set()
        for user in recipients:
            email = user.email
            if not email or email.lower() in seen_emails:
                continue
            seen_emails.add(email.lower())
            self._safe_send_template_email(
                template,
                email_to=email,
                context={"recipient_user": user},
            )

    def _notify_stage_changed(self, old_stage):
        self.ensure_one()
        try:
            return self.env["notification.service"].notify_groups(
                groups=self.request_type_id.receiver_group_ids,
                extra_users=self.requester_id,
                title=_("Trạng thái yêu cầu đã thay đổi"),
                message="%s: %s → %s"
                % (
                    self.code,
                    (old_stage and old_stage.name) or "",
                    self.stage_id.name,
                ),
                notification_type="info",
                source_record=self,
                source_module="vna_user_support",
                payload={
                    "request_id": self.id,
                    "request_code": self.code,
                    "old_stage": (old_stage and old_stage.name) or "",
                    "new_stage": self.stage_id.name,
                },
                deduplication_key="vna_support:stage:%s:%s" % (self.id, self.stage_id.id),
            )
        except Exception:
            _logger.exception(
                "VNA support notification center stage change failed for request %s.",
                self.id,
            )
            return False

    def _safe_send_template_email(self, template, email_to, context=None):
        self.ensure_one()
        try:
            template.with_context(**(context or {})).send_mail(
                self.id,
                force_send=False,
                email_values={
                    "email_to": email_to,
                    "recipient_ids": [],
                },
            )
        except Exception as exc:
            _logger.warning("VNA support email send failed for request %s: %s", self.id, exc.__class__.__name__)
            self.message_post(
                body=_("Không gửi được một email thông báo. Yêu cầu vẫn được lưu thành công."),
                subtype_xmlid="mail.mt_note",
            )

    def action_assign_to_me(self):
        for request in self:
            request.write({"assigned_user_id": self.env.user.id})
        return True

    def action_open_cancel_wizard(self):
        self.ensure_one()
        return {
            "name": _("Hủy yêu cầu hỗ trợ"),
            "type": "ir.actions.act_window",
            "res_model": "vna.support.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_request_id": self.id},
        }
