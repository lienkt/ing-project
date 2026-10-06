# Install and run with Keycloak

[Documentation index](README.md) · [Local installation](../README.md#local-setup)

Run commands from the repository root unless stated otherwise.

## 1. Complete local setup

Follow the [local setup](../README.md#local-setup) to install dependencies,
create the backend and frontend `.env` files, and initialize the application database.

## 2. Start PostgreSQL and Keycloak

Start Docker Desktop, then run:

```bash
docker compose --profile auth up -d db keycloak
```

Wait for Keycloak to start, then open <http://localhost:8080/admin/>.
For a new installation using the Compose defaults, sign in with:

- Username: `admin`
- Password: `local-change-me`

For an existing installation, use its administration password.

## 3. Create application users in the banking realm

The administration account above belongs to `master`. Create separate application
accounts in `banking`:

1. In the upper-left realm selector, click **master** and choose **banking**.
2. Open **Users** → **Add user**, enter username `viewer`, and click **Create**.
3. Open **Credentials** → **Set password**, enter and confirm a password,
   turn **Temporary** off, and save.
4. Open **Role mapping** → **Assign role**, filter by realm roles,
   select **viewer**, and click **Assign**.
5. Repeat for username `admin`, assigning the realm role **admin**.

| Role     | Permissions                                                                  |
| -------- | ---------------------------------------------------------------------------- |
| `viewer` | Read Dataset, saved labels, capture evidence and Compare                     |
| `admin`  | All viewer permissions plus create, edit, delete, scrape, label and evaluate |

## 4. Enable authentication in both applications

Set these values in **backend/.env**, keeping the existing database settings:

```dotenv
AUTH_ENABLED=true
OIDC_ISSUER=http://localhost:8080/realms/banking
OIDC_AUDIENCE=banking-api
```

Set these values in **frontend/.env**:

```dotenv
VITE_API_URL=http://localhost:8000
VITE_AUTH_ENABLED=true
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=banking
VITE_KEYCLOAK_CLIENT_ID=banking-web
```

Restart FastAPI and Vite after changing these files.

## 5. Start the app and sign in

In one terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, starting from the repository root:

```bash
cd frontend
npm run dev -- --port 5173 --strictPort
```

Open <http://127.0.0.1:5173/>. The app redirects to Keycloak.
Sign in with the `viewer` or `admin` application account created in step 3.

## 6. Check login, logout and permissions

- Sign in as `viewer` to view Dataset, captures and Compare.
- Click **Sign out** below the username in the sidebar.
- Sign in as the application `admin` to access editing and labeling tools.

## Configure roles and permissions

Edit [backend/config/permissions.json](../backend/config/permissions.json):

- `permissions`: available permission names.
- `roles`: Keycloak realm role names and their granted permissions.
- `api`: exact HTTP method and route template mapped to its required permission.

To add a role, add it under `roles`, create the same realm role in Keycloak,
and assign it to the users. All app users need `workspace.read` for the shared
workspace and permission loading. For example, add this entry to `roles`:

```json
"editor": ["workspace.read", "campaigns.write", "labels.write"]
```

This grants editing and labeling while leaving deletion, catalog management,
capture and evaluation unavailable. Label editing uses `labels.write`;
additional campaign observation fields use `campaigns.write`. Permissions from multiple assigned
roles are combined; there is no role inheritance or special admin bypass.

Restart the backend after editing this file, then reload the frontend. After
changing Keycloak role assignments, sign out and sign in again. The backend loads
and validates the configuration once per process. The frontend loads effective
permissions from `GET /api/auth/permissions` on initialization and uses them for
navigation, buttons and route access; the backend still checks every API request.

For new API endpoints, add their exact method and route template to `api`.
Unmapped endpoints and unknown roles grant no access when authentication is enabled.
Adding a new kind of UI action also requires a frontend permission check.
With `AUTH_ENABLED=false`, the existing unrestricted local mode remains available.

## Stop and restart

Stop FastAPI and Vite with Ctrl+C. Stop the containers with:

```bash
docker compose --profile auth stop keycloak db
```

For the next session, repeat steps 2 and 5. Existing accounts and data are retained.
