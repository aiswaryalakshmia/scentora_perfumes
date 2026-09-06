# Scentora

Scentora is a perfume e-commerce web application built with Django. The project demonstrates a complete e-commerce workflow, including user authentication, product management, shopping cart, checkout, order processing, payment integration, and an admin dashboard.

## Tech Stack

* Python 3.13
* Django 6
* PostgreSQL
* HTML5
* CSS3
* JavaScript
* Razorpay

## Features

* User registration and login
* Email/OTP-based authentication
* Google authentication
* Password reset
* Product and category management
* Product variants with different sizes and prices
* Product search and filtering
* Shopping cart
* Wishlist
* Address management
* Checkout
* Razorpay payment integration
* Order management
* Order tracking
* Return and cancellation handling
* Admin dashboard
* Customer management
* Sales management

## Prerequisites

Before setting up the project, make sure the following are installed on your system:

* Python 3.13
* PostgreSQL
* Git
* A code editor such as VS Code

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/aiswaryalakshmia/scentora_perfumes.git
cd scentora_perfumes
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Database Setup

Scentora uses PostgreSQL as its database.

### 1. Create a PostgreSQL database

Create a database for the project using PostgreSQL.

For example:

```sql
CREATE DATABASE scentora_db;
```

### 2. Configure environment variables

Create a `.env` file in the project's root directory.

Add the required configuration:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=scentora_db
DB_USER=your-postgresql-username
DB_PASSWORD=your-postgresql-password
DB_HOST=localhost
DB_PORT=5432

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
```

Replace the placeholder values with your local PostgreSQL credentials and Razorpay credentials.

**Do not commit the `.env` file or any secret keys to Git.**

## Apply Database Migrations

After configuring the database, run:

```bash
python manage.py migrate
```

This creates the required database tables for the Django application.

## Create a Superuser

To access the Django admin panel, create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to enter the required credentials.

## Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

The Django admin panel can be accessed at:

```text
http://127.0.0.1:8000/admin/
```

## Project Structure

```text
scentora_perfumes/
│
├── apps/
│   ├── adminpanel/
│   ├── authentication/
│   ├── common/
│   ├── home/
│   ├── orders/
│   ├── products/
│   └── userprofile/
│
├── static/
├── templates/
├── media/
├── manage.py
├── requirements.txt
├── .env
└── .gitignore
```

## Environment Variables

The following environment variables are required for the application:

| Variable              | Description                        |
| --------------------- | ---------------------------------- |
| `SECRET_KEY`          | Django secret key                  |
| `DEBUG`               | Enables/disables Django debug mode |
| `DB_NAME`             | PostgreSQL database name           |
| `DB_USER`             | PostgreSQL username                |
| `DB_PASSWORD`         | PostgreSQL password                |
| `DB_HOST`             | PostgreSQL host                    |
| `DB_PORT`             | PostgreSQL port                    |
| `RAZORPAY_KEY_ID`     | Razorpay API key ID                |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret                |

## Payment Integration

Scentora uses Razorpay for payment processing.

To enable Razorpay payments:

1. Create a Razorpay account.
2. Obtain the required API credentials.
3. Add the credentials to the `.env` file.
4. Restart the Django development server.

For testing, use Razorpay's test/sandbox credentials rather than production credentials.

## Development Notes

* Keep sensitive information such as database passwords, secret keys, and API credentials in the `.env` file.
* Do not commit `.env` to the repository.
* The `.vscode/` folder is ignored because it contains editor-specific configuration.
* Install dependencies inside the project's virtual environment.

## License

This project is intended for learning and portfolio purposes.
