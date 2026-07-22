# Scentora

Scentora is a perfume e-commerce web application built with Django. This project demonstrates a complete e-commerce workflow, including authentication, product management, shopping cart, order processing, payment integration, and an admin dashboard.

## Tech Stack

- Python 3.13
- Django 6
- PostgreSQL
- HTML5
- CSS3
- JavaScript
- Razorpay

## Installation

### Clone the repository

```bash
git clone https://github.com/aiswaryalakshmia/scentora_perfumes.git
cd scentora
```

### Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

### Run the development server

```bash
python manage.py runserver
```

Visit:

```
http://127.0.0.1:8000/
```

## Project Structure

```
apps/
├── adminpanel/
├── authentication/
├── common/
├── home/
├── orders/
├── products/
├── userprofile/


static/
templates/
media/
```

## License

This project is intended for learning and portfolio purposes.