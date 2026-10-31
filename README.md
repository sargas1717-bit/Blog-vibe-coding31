# Cuaderno

Blog modular con Django 5.2, CRUD de publicaciones, registro e inicio de sesión. Cada publicación queda asociada al usuario autenticado; el autor no se acepta desde el formulario.

## Requisitos

- Python 3.12+
- pip

## Instalación y ejecución

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. Las cuentas se crean en `/accounts/signup/`. Para administrar contenido, crea un usuario administrador con `python manage.py createsuperuser`.

En despliegues reales, define `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` y `DJANGO_ALLOWED_HOSTS`; la clave incluida en settings solo sirve para desarrollo local.

## Pruebas

```bash
python manage.py test
```

La suite verifica acceso público, inyección de autor desde la sesión, aislamiento entre propietarios, formularios, registro, protección CSRF y que el borrado no opere mediante GET.

## Flujo Git sugerido

```bash
git switch -c feature/blog-crud
git add config blog templates static requirements.txt README.md manage.py
git commit -m "feat: add secure blog CRUD and authentication"

git switch -c feature/author-permissions
git add blog/tests.py blog/views.py templates/detail.html
git commit -m "security: enforce post ownership and CSRF protections"

git switch main
git merge --no-ff feature/blog-crud
git merge --no-ff feature/author-permissions
git push origin main
```