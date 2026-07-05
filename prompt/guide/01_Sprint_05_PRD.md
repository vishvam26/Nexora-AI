# Sprint 05 – User Profile Management

## Objective

Extend the existing authentication system by adding complete user profile management.

The user should be able to securely view and update their profile without affecting authentication.

---

## Features

### 1. Get Profile

Endpoint

GET /users/profile

Returns

- id
- full_name
- email
- is_active
- created_at

JWT Required

Yes

---

### 2. Update Profile

Endpoint

PUT /users/profile

Editable Fields

- full_name

Non Editable

- email
- password
- role
- id

JWT Required

Yes

---

### 3. Change Password

Endpoint

PUT /users/change-password

Input

- current_password
- new_password

Validation

Current password must match.

New password should be hashed.

JWT Required.

---

### 4. User Schemas

Create

UserProfileResponse

UpdateProfileRequest

ChangePasswordRequest

---

### 5. Repository

Add methods

update()

change_password()

---

### 6. Service

Business validation

Password verification

Password hashing

---

## Acceptance Criteria

✓ Existing login still works

✓ Existing register still works

✓ JWT still works

✓ Profile fetch works

✓ Profile update works

✓ Password changes successfully

✓ Old password fails after change

✓ New password works

---

## Non Goals

No admin features.

No role management.

No profile picture.

No email change.

---

Sprint Status

Target = COMPLETE
