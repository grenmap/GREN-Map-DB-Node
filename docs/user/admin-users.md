# Managing Admin Users

EPPN is required for the user login.

What's an EPPN? EPPN is a shorthand for eduPersonPrincipalName, an attribute defined in the Internet2 eduPerson object class specification that is intended to uniquely identify a user at a given institution.

## Initial Setup

Environment variable "ADMIN_EPPNS" in "env/.env.dev" or "env/.env.prod" is a list of users who are automatically made admin when they first log in. It should be a space separated list of users' EPPNs who get admin status on first login.

```bash
ADMIN_EPPNS=testuser1@example.org testuser2@example.org
```

## Adding More Admin Users

As the initially configured admin user, login to the site. Clicking the "Admin" link will bring you to the backend Administration site.

### Adding a New Admin User

1. From the left side menu, click "Users" under "AUTHENTICATION AND AUTHORIZATION" to the "Users" page.
2. Click "ADD USER" button at the top right corner to the "Add user" page.
3. Fill the Username field with this new user's EPPN (*Note: The Django's username only allows for: letters, numbers, and @/./+/-/_ characters. If this users's EPPN contains charaters outside of this list, replace them with "_" and make sure the username is still unique*). Fill the "Password" and "Password confirmation" fields (they are required by Django, and will never be used for the login). Click "Done" to the user detail page.
4. In the user detail page, check the boxes for "Staff status" and "Superuser status" under "Permissions". Clicking "Done" to complete the user creation.

### Assigning Admin Permissions to an Existing User

1. From the left side menu, click "Users" under "AUTHENTICATION AND AUTHORIZATION" to the "Users" page.
2. Click the related username in the USERNAME column to the user detail page.
3. In the user detail page, check the boxes for "Staff status" and "Superuser status" under "Permissions". Clicking "Done" to complete the update.

### Removing Admin Permissions from an Existing User

1. From the left side menu, click "Users" under "AUTHENTICATION AND AUTHORIZATION" to the "Users" page.
2. Click the related username in the USERNAME column to the user detail page.
3. In the user detail page, uncheck the boxes for "Staff status" and "Superuser status" under "Permissions". Clicking "Done" to complete the update.
