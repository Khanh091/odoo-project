# Google OAuth Login

## Purpose

`auth_google_oauth` adds a reusable Google login configuration for Odoo 17. It uses Odoo's standard `auth_oauth` callback at `/auth_oauth/signin` and only customizes validation, linking, signup policy, and Settings fields.

## Dependency

- `auth_oauth`

## Google Cloud Configuration

Create an OAuth 2.0 Client ID in Google Cloud Console.

Local development values:

- Authorized JavaScript origin: `http://localhost:8069`
- Authorized redirect URI: `http://localhost:8069/auth_oauth/signin`

Scopes:

- `openid`
- `profile`
- `email`

## Odoo Configuration

Go to Settings > General Settings > Integrations > Google Authentication.

Set:

- Enable Google Login
- Google Client ID
- Automatically Create Users, if new verified Google users may create internal Odoo users
- Allowed Email Domains, one per line or comma-separated. Leave empty to allow all verified Google email domains.

The module never stores a Google Client Secret and does not require one for the standard Odoo implicit OAuth flow.

## Redirect URI

Local callback:

```text
http://localhost:8069/auth_oauth/signin
```

Production callback:

```text
https://your-domain.example/auth_oauth/signin
```

Set `web.base.url` correctly in Odoo before copying the production URI.

## Installation

Place the module in:

```text
custom_addons/auth_google_oauth
```

Install:

```bash
python odoo-bin -c odoo.conf -d <database> -i auth_google_oauth
```

Upgrade:

```bash
python odoo-bin -c odoo.conf -d <database> -u auth_google_oauth
```

## Test Guide

1. Install the module.
2. Open Settings and enable Google login.
3. Enter the Google Client ID.
4. Optionally enable auto signup.
5. Optionally enter allowed domains such as `example.com` and `company.vn`.
6. Log out and open `/web/login`.
7. Click `Đăng nhập bằng Google`.
8. Complete Google authentication.
9. Confirm Odoo signs in the linked user or creates a non-admin internal user when auto signup is enabled.

## Security Notes

- Only verified Google emails are accepted.
- Existing users are linked only by exact verified email/login match.
- Duplicate Odoo users with the same email are rejected instead of linked automatically.
- Domain matching compares the exact part after `@`; it does not use unsafe suffix matching.
- New users receive `base.group_user` only, not administrator groups.
- Access token, authorization code, Client Secret, and full Google payload are not logged.

## Production HTTPS

Use HTTPS in production and configure Google Cloud with:

- Authorized JavaScript origin: `https://your-domain.example`
- Authorized redirect URI: `https://your-domain.example/auth_oauth/signin`

Ensure reverse proxy headers and `web.base.url` are correct so Odoo generates the same redirect URI registered in Google Cloud.

## Test Cases

1. Provider not enabled: login is rejected with a clear access error.
2. Provider enabled without Client ID: Settings blocks saving and login is rejected.
3. Google returns verified email: login can proceed.
4. Google returns unverified email: login is rejected.
5. User already linked by `oauth_uid`: that user is signed in.
6. User exists with the same verified email but is not linked: the Google identity is linked.
7. No user and auto signup enabled: a new internal non-admin user is created.
8. No user and auto signup disabled: login is rejected.
9. Email domain is in the allowed list: login can proceed.
10. Email domain is not in the allowed list: login is rejected.
11. Allowed domains list is empty: all verified domains are allowed.
12. Multiple users share the same email/login: automatic linking is rejected.
13. Google response misses `sub`: login is rejected.
14. Google response misses `email`: login is rejected.
15. New user does not receive admin groups.
16. Second login with the same Google account reuses the linked user and does not create a duplicate.
