# 🚀 Smart Expense Tracker — Deployment Guide

**Smart Expense Tracker** is a Flask-based web application designed to help users manage their personal income and expenses.

The application uses a cloud-hosted MySQL database and is deployed using **Render**, with the source code maintained on **GitHub**.

### ☁️ Deployment Services

| Component            | Technology                     |
| -------------------- | ------------------------------ |
| 🖥️ Backend          | Python Flask                   |
| 🎨 Frontend          | HTML, Tailwind CSS, JavaScript |
| 🗄️ Database         | MySQL                          |
| ☁️ Cloud Database    | Aiven MySQL                    |
| 🚀 Web Hosting       | Render                         |
| 🔐 Production Server | Gunicorn                       |
| 📦 Source Control    | Git & GitHub                   |

---

# Deployment Architecture

The application follows a simple cloud deployment architecture:

```text
                         ┌──────────────────┐
                         │   User Browser   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Render       │
                         │                  │
                         │ Flask + Gunicorn │
                         └────────┬─────────┘
                                  │
                         MySQL Connection
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │      Aiven MySQL       │
                     │                        │
                     │ smart_expense_tracker  │
                     └────────────────────────┘

                    ┌────────────────────────┐
                    │        GitHub           │
                    │   Source Repository     │
                    └────────────┬───────────┘
                                 │
                         Automatic Deploy
                                 │
                                 ▼
                              Render
```

### 🔄 How It Works

1. The user accesses the application through a web browser.
2. Render hosts the Flask application.
3. Gunicorn runs Flask as the production WSGI server.
4. Flask communicates with the Aiven MySQL database.
5. GitHub stores the application's source code.
6. New GitHub commits can automatically trigger a Render deployment.

---

# 🗄️ Aiven MySQL Setup

The application's production database is hosted on **Aiven MySQL**.

### Database

```text
smart_expense_tracker
```

### Database Tables

```text
users
categories
transactions
```

The database schema is maintained in:

```text
database/schema.sql
```

The schema was imported into the Aiven MySQL service using **MySQL Workbench**.

### 🔑 Aiven Connection Details

Aiven provides the following connection parameters:

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

> ⚠️ **Security Notice:** Never commit actual database credentials to GitHub.

---

# 🔐 Environment Variables

Environment variables are used to keep sensitive configuration outside the source code.

For local development, create a `.env` file:

```env
MYSQL_HOST=your-mysql-host
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=smart_expense_tracker
MYSQL_PORT=your-mysql-port

SECRET_KEY=your-secret-key
```

### 🚫 Protecting `.env`

The `.env` file must **never** be committed to GitHub.

The project's `.gitignore` contains:

```gitignore
.env
```

This prevents sensitive credentials from accidentally being uploaded to the repository.

### ☁️ Production Environment

For production, the same variables are configured directly through the **Render Environment Variables** section.

---

# 🔌 Flask Database Configuration

Database connectivity is implemented in:

```text
database/db.py
```

The application uses:

```text
mysql-connector-python
```

Database credentials are loaded from environment variables rather than being hard-coded.

This allows the same application to work with:

```text
Local MySQL
     ↓
Development Environment

Aiven MySQL
     ↓
Production Environment
```

This approach makes the application easier to configure and safer to deploy.

---

# ⚙️ Production Flask Configuration

The Flask application reads the `PORT` value provided by the hosting platform.

The application also disables Flask debug mode in production.

```python
if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
```

### Why `0.0.0.0`?

The application needs to accept connections from outside the local machine when running on a cloud hosting platform.

### Why use `PORT`?

Render dynamically provides the port through the `PORT` environment variable.

---

# 🚀 Gunicorn

**Gunicorn** is used as the production WSGI server.

It is included in:

```text
requirements.txt
```

### Production Start Command

Render starts the application using:

```bash
gunicorn app:app
```

Here:

```text
app
│
└── app.py

app
│
└── Flask application object
```

### Local Development

During local development, the application can be started using:

```bash
python app.py
```

### Development vs Production

| Environment          | Server                   |
| -------------------- | ------------------------ |
| 🧪 Local Development | Flask development server |
| 🚀 Production        | Gunicorn                 |

---

# ☁️ Render Deployment

The Flask application is deployed to **Render** as a Web Service.

### Render Configuration

```text
Runtime:
Python 3

Plan:
Free

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app
```

### 🔄 Automatic Deployment

Render is connected to the GitHub repository.

When a new commit is pushed:

```text
Local Changes
      ↓
Git Commit
      ↓
Git Push
      ↓
GitHub
      ↓
Render Detects Changes
      ↓
Build
      ↓
Deploy
      ↓
Live Application
```

This eliminates the need to manually deploy every update.

---

# 🔑 Render Environment Variables

The following environment variables must be configured in the Render dashboard:

```text
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
MYSQL_PORT
SECRET_KEY
```

### ⚠️ Important

Do **not** place these values directly inside:

```text
app.py
database/db.py
GitHub repository
README.md
```

Instead, configure them through Render's environment variable settings.

---

# 🔄 Deployment Workflow

The complete deployment workflow is:

```text
┌─────────────────────┐
│   Develop Locally   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Test Application  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      git add .      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     git commit      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      git push       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       GitHub        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       Render        │
│       Build         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      Gunicorn       │
│   Starts Flask App  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Aiven MySQL DB    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   🌐 Live Website   │
└─────────────────────┘
```

---

# 📤 Updating the Deployment

After making changes to the application, use:

```powershell
git status
git add .
git commit -m "Describe your changes"
git push
```

For example:

```powershell
git add .
git commit -m "Add transaction search feature"
git push
```

Render will detect the new GitHub commit and automatically start a new deployment.

---

# 🧪 Deployment Testing

After deployment, the following features should be tested on the live application.

### 🔐 Authentication

* ✅ User Registration
* ✅ User Login
* ✅ User Logout

### 💰 Transactions

* ✅ Add Income
* ✅ Add Expense
* ✅ Edit Transaction
* ✅ Delete Transaction
* ✅ Transaction Search
* ✅ Transaction Type Filtering

### 📊 Reports

* ✅ Reports and Analytics
* ✅ Dashboard Statistics
* ✅ Transaction History

### 🗄️ Database Persistence

Create a transaction through the live application and verify that it is stored in the Aiven MySQL database.

Using MySQL Workbench:

```sql
USE smart_expense_tracker;

SELECT * FROM users;

SELECT * FROM transactions;
```

Records created through the deployed application should appear in the Aiven database.

---

# 🛡️ Security

Security is an important part of the deployment.

## 🔒 Password Protection

User passwords are hashed using **Werkzeug** before being stored in the database.

```text
User Password
      ↓
Password Hashing
      ↓
Hashed Password
      ↓
Database
```

Plain-text passwords are **not stored**.

---

## 💉 SQL Injection Protection

Database queries use **parameterized SQL statements**.

This helps protect the application against SQL injection attacks.

Conceptually:

```python
cursor.execute(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)
)
```

Instead of directly concatenating user input into SQL queries.

---

## 👤 User Data Isolation

Transaction operations are associated with the authenticated user's ID.

Therefore:

```text
User A
   ↓
User A's Transactions

User B
   ↓
User B's Transactions
```

Users should only be able to access their own transaction records.

---

## 🔐 Secrets Management

Sensitive values such as:

```text
MYSQL_PASSWORD
SECRET_KEY
```

are stored as environment variables.

They are **not committed to GitHub**.

---

## 🐛 Production Debugging

Flask debug mode is disabled in production:

```python
debug=False
```

This prevents exposing development debugging information to users.

---

# 💸 Free Deployment

The project uses free-tier services for deployment:

| Service   | Purpose        | Plan        |
| --------- | -------------- | ----------- |
| 🐙 GitHub | Source Code    | Free        |
| 🚀 Render | Web Hosting    | Free        |
| ☁️ Aiven  | MySQL Database | Free        |
| 🐍 Flask  | Backend        | Open Source |

### ⚠️ Free-Tier Limitations

Free cloud services may have limitations related to:

* Computing resources
* Database resources
* Application availability
* Cold starts
* Storage
* Connection limits

Therefore, this deployment is intended primarily for:


# 🎯 Final Deployment Architecture

The final Smart Expense Tracker system consists of:

```text
                  💰 SMART EXPENSE TRACKER
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    🐍 Flask          🎨 Frontend      🗄️ Database
    Backend           HTML/CSS/JS      Aiven MySQL
          │
          ▼
     🚀 Gunicorn
          │
          ▼
      ☁️ Render
          │
          ▼
      🐙 GitHub
```

### 🧩 Complete Technology Stack

```text
Frontend
├── HTML
├── Tailwind CSS
└── JavaScript

Backend
└── Python Flask

Database
└── MySQL

Cloud Database
└── Aiven MySQL

Production Server
└── Gunicorn

Hosting
└── Render

Version Control
└── Git + GitHub
```




---

# 🎉 Deployment Complete

**Smart Expense Tracker is successfully deployed using:**

```text
🐙 GitHub
      ↓
🚀 Render
      ↓
🐍 Flask + Gunicorn
      ↓
☁️ Aiven MySQL
      ↓
🌐 Live Application
```

> **A secure, cloud-hosted expense management application built with Flask and deployed using modern development and cloud technologies.**
