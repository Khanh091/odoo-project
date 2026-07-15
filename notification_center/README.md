# Notification Center

## 1. Tong quan

`notification_center` cung cap Notification Center realtime dung chung cho Odoo 17 backend.
Module nghiep vu khac goi service ORM de tao notification, khong tu tao record
`notification.center` va khong tu goi `bus.bus`.

Public service model chinh thuc:

```python
self.env["notification.service"]
```

Public API on dinh:

```python
notify_user(...)
notify_users(...)
notify_group(...)
notify_groups(...)
```

Tat ca helper bat dau bang `_` la private API va co the thay doi.

## 2. Kien truc

Backend:

- `notification.center`: model luu mot notification record rieng cho tung user nhan.
- `notification.service`: abstract model public de module nghiep vu tao va dispatch notification.
- `bus.bus`: gui realtime event dung partner cua user nhan.
- Security: internal user chi doc notification cua minh; admin quan tri duoc tat ca.

Frontend:

- Systray bell hien badge unread count.
- Dropdown lay 10 notification gan nhat.
- Toast realtime khi bus nhan event moi.
- Click notification mark read va mo source record bang Odoo action service.

## 3. Dependency

Module nghiep vu phai khai bao dependency:

```python
"depends": [
    "notification_center",
],
```

Neu module nghiep vu dung `mail` cho muc dich rieng, khai bao rieng:

```python
"depends": [
    "mail",
    "notification_center",
],
```

Khong import Python truc tiep tu thu muc `notification_center`.
Khong goi HTTP/REST giua cac module trong cung Odoo database.
Giao tiep qua ORM:

```python
self.env["notification.service"]
```

REST API gui notification chua nam trong scope hien tai. Co the bo sung sau neu co he thong ben ngoai can goi vao Odoo.

## 4. Public API

### notify_user

Signature:

```python
notify_user(
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
)
```

Contract:

- `user`: bat buoc, `res.users` singleton.
- `title`: bat buoc, string khong rong.
- `message`: bat buoc, string khong rong, nen ngan gon va khong dung HTML body dai.
- `notification_type`: tuy chon, mac dinh `info`; gia tri hop le la `info`, `success`, `warning`, `danger`.
- `source_record`: tuy chon, singleton Odoo record. Neu co, service tu suy ra `source_model`, `source_res_id`, `action_url` khi caller khong truyen cac gia tri nay.
- `source_module`: tuy chon, string ten module nguon.
- `source_model`: tuy chon, string technical model.
- `source_res_id`: tuy chon, integer id ban ghi nguon.
- `action_url`: tuy chon, string URL. Neu truyen thi uu tien hon URL sinh tu `source_record`.
- `payload`: tuy chon, dictionary JSON serializable.
- `icon`: tuy chon, string CSS icon class.
- `deduplication_key`: tuy chon, string event key.
- `realtime`: tuy chon, boolean, mac dinh `True`; khi `False` service van tao database record nhung khong gui bus.

Return:

```python
notification.center recordset
```

`notify_user` tra ve singleton recordset neu tao duoc, hoac empty recordset neu user bi filter do inactive, portal/shared, hoac deduplication.

### notify_users

Signature:

```python
notify_users(
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
)
```

Contract:

- `users`: bat buoc, `res.users` recordset. Duplicate ids duoc loai.
- `exclude_users`: tuy chon, `res.users` recordset bi loai khoi recipients.
- Cac tham so con lai giong `notify_user`.

Return:

```python
notification.center recordset
```

Empty recordset neu khong con recipient sau khi loc active/internal users, exclusions, va deduplication.

### notify_group

Signature:

```python
notify_group(
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
)
```

Contract:

- `group`: bat buoc, `res.groups` singleton.
- Service lay recipients tu `group.users`.
- Cac tham so con lai giong `notify_users`.

Return:

```python
notification.center recordset
```

### notify_groups

Signature:

```python
notify_groups(
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
)
```

Contract:

- `groups`: bat buoc, `res.groups` recordset.
- `extra_users`: tuy chon, `res.users` recordset duoc them vao recipients.
- `exclude_users`: tuy chon, `res.users` recordset bi loai khoi recipients.
- Mot user nam trong nhieu group chi nhan mot notification.
- Cac tham so con lai giong `notify_users`.

Return:

```python
notification.center recordset
```

## 5. Input types

Dung dung kieu du lieu sau:

```text
user -> res.users singleton
users -> res.users recordset
group -> res.groups singleton
groups -> res.groups recordset
source_record -> singleton Odoo record
payload -> dictionary JSON serializable
extra_users -> res.users recordset
exclude_users -> res.users recordset
```

Khong nen truyen:

- Database ID thay cho recordset.
- Recordset nhieu ban ghi vao `source_record`.
- Odoo recordset trong `payload`.
- HTML body dai vao `message`.
- `user_id` lay truc tiep tu du lieu khong tin cay.

## 6. Return type

Public API chon mot return contract duy nhat:

```python
notification.center recordset
```

Vi du:

```python
notifications = self.env["notification.service"].notify_groups(
    groups=groups,
    title="Co yeu cau moi",
    message=record.display_name,
)

notification_ids = notifications.ids
created_count = len(notifications)
recipient_user_ids = notifications.mapped("user_id").ids
```

Khong co result dictionary trong contract hien tai.

## 7. Exception behavior

Raise `ValidationError` khi:

- `user` khong phai `res.users` singleton.
- `users` khong phai `res.users` recordset.
- `group` khong phai `res.groups` singleton.
- `groups` khong phai `res.groups` recordset.
- `extra_users` hoac `exclude_users` khong phai `res.users` recordset.
- Thieu `title`.
- Thieu `message`.
- `notification_type` khong thuoc `info`, `success`, `warning`, `danger`.
- `source_record` duoc truyen nhung khong phai singleton record hop le.
- `payload` khong phai dictionary JSON serializable.

Tra empty `notification.center` recordset khi:

- Khong co recipient.
- Tat ca recipient inactive.
- Tat ca recipient la portal/shared user.
- Tat ca recipient bi `exclude_users` loai.
- Tat ca recipient da co notification active cung `deduplication_key`.

Deduplication khong raise exception. Scope cua deduplication la:

```text
user_id + deduplication_key
```

Bus realtime loi:

- Service log exception.
- Notification record da tao van duoc giu lai.
- Khong raise loi ra module nghiep vu.
- Khong rollback transaction nghiep vu nguon.

`UserError` va `AccessError` thuoc cac method UI/RPC tren `notification.center`, khong phai contract gui notification cua `notification.service`.

## 8. Realtime behavior

Mac dinh `realtime=True`.

Sau khi tao notification record, service gui bus event:

```text
notification_center/new_notification
```

Event duoc gui toi partner cua user nhan, khong broadcast toan he thong.

Payload bus gom:

```python
{
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
```

Frontend tu hien toast, tang badge, them item moi vao dropdown neu da load. User offline khong thay toast tai thoi diem tao, nhung van thay notification khi dang nhap lai vi record duoc luu database.

## 9. Security behavior

Internal user:

- Chi doc notification cua chinh minh qua record rule.
- Khong co ACL create/write/unlink truc tiep tren `notification.center`.
- Mark read di qua method server-side kiem tra `env.user`.

System administrator:

- Co full access theo ACL va record rule admin.

Service:

- Tao notification bang `sudo()` sau khi validation input.
- Khong tin `user_id` tu frontend.
- Khong expose public REST/HTTP controller de gui notification.

## 10. Trach nhiem module nghiep vu

Module nghiep vu chi xac dinh:

- Su kien nao can gui notification.
- User hoac group nhan.
- Title.
- Message.
- Notification type.
- Source record.
- Metadata nghiep vu trong `payload`.

Module nghiep vu khong duoc:

- Tu tao `notification.center`.
- Tu goi `bus.bus`.
- Tu cap nhat badge.
- Tu viet frontend systray.
- Tu gui broadcast toan he thong.
- Tu loai recipient trung khi service da chiu trach nhiem.

## 11. Trach nhiem notification_center

`notification_center` tu xu ly:

- Lay users tu group.
- Hop nhat users tu nhieu group.
- Loai duplicate recipients.
- Loai inactive user.
- Loai portal/shared user (`user.share == True`).
- Ap dung `extra_users`.
- Ap dung `exclude_users`.
- Tao mot notification record rieng cho tung user.
- Sinh URL mo source record dang `/web#id=<id>&model=<model>&view_type=form`.
- Luu trang thai chua doc.
- Gui realtime bus dung user.
- Hien toast va cap nhat badge systray tren frontend.
- Giu notification de user offline xem lai.
- Bat loi bus ma khong rollback nghiep vu nguon.

## 12. Examples

Gui mot user:

```python
self.env["notification.service"].notify_user(
    user=assigned_user,
    title="Ban duoc phan cong xu ly",
    message=f"{record.display_name}",
    notification_type="info",
    source_record=record,
)
```

Gui nhieu user:

```python
self.env["notification.service"].notify_users(
    users=users,
    title="Co cap nhat moi",
    message="Du lieu da thay doi.",
    notification_type="info",
    source_record=record,
)
```

Gui mot group:

```python
self.env["notification.service"].notify_group(
    group=group,
    title="Thong bao nhom",
    message="Co cong viec moi.",
    source_record=record,
)
```

Gui nhieu group:

```python
self.env["notification.service"].notify_groups(
    groups=groups,
    title="Co yeu cau moi",
    message=f"{record.display_name}",
    notification_type="warning",
    source_record=record,
)
```

Group cong them requester:

```python
self.env["notification.service"].notify_groups(
    groups=receiver_groups,
    extra_users=requester,
    title="Trang thai da thay doi",
    message="Yeu cau da chuyen sang Dang xu ly.",
    source_record=request,
)
```

Loai tru nguoi thao tac:

```python
self.env["notification.service"].notify_groups(
    groups=groups,
    exclude_users=self.env.user,
    title="Du lieu da thay doi",
    message="Mot ban ghi vua duoc cap nhat.",
    source_record=record,
)
```

Deduplication:

```python
self.env["notification.service"].notify_groups(
    groups=groups,
    title="Co yeu cau moi",
    message=request.display_name,
    source_record=request,
    deduplication_key=f"support:new:{request.id}",
)
```

## 13. vna_user_support example

```python
def _notify_new_request(self):
    self.ensure_one()

    return self.env["notification.service"].notify_groups(
        groups=self.request_type_id.receiver_group_ids,
        title="Co yeu cau ho tro moi",
        message=f"{self.code} - {self.name}",
        notification_type="warning",
        source_record=self,
        source_module="vna_user_support",
        payload={
            "request_id": self.id,
            "request_code": self.code,
            "priority": self.priority,
            "request_type": self.request_type_id.name,
        },
        deduplication_key=f"vna_support:new:{self.id}",
    )
```

Trong `create()`:

```python
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)

    for record in records:
        record._notify_new_request()

    return records
```

Khi doi trang thai:

```python
def _notify_stage_changed(self, old_stage):
    self.ensure_one()

    return self.env["notification.service"].notify_groups(
        groups=self.request_type_id.receiver_group_ids,
        extra_users=self.requester_id,
        title="Trang thai yeu cau da thay doi",
        message=f"{self.code}: {old_stage.name} -> {self.stage_id.name}",
        notification_type="info",
        source_record=self,
        source_module="vna_user_support",
        payload={
            "old_stage": old_stage.name,
            "new_stage": self.stage_id.name,
        },
    )
```

## 14. Integration checklist

- Them `"notification_center"` vao `depends`.
- Goi `self.env["notification.service"]`, khong import truc tiep.
- Truyen recordset, khong truyen database id.
- Dung `source_record=self` hoac record nghiep vu singleton de tu sinh URL.
- Giu `message` ngan gon, khong truyen HTML body dai.
- Chi truyen `payload` la dict JSON serializable.
- Dung `deduplication_key` cho event chi nen tao mot notification tren moi user.
- Khong tu goi `bus.bus` hoac tu tao frontend systray.

## 15. Compatibility policy

- Public methods khong bat dau bang `_` trong `notification.service` duoc coi la stable API.
- Private helpers bat dau bang `_` co the thay doi ma khong bao truoc.
- Khong doi ten hoac xoa public parameter trong minor version neu khong co backward-compatible wrapper.
- Optional parameter moi phai co default value.
- Module khac khong duoc phu thuoc vao implementation bus/frontend noi bo.
