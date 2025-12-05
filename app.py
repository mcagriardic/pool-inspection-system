import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from nicegui import ui

from models import User
from ui.login_form import render_login_form
from ui.pool_form import render_pool_form
from ui.submissions_dashboard import render_submissions_dashboard
from services.auth import get_current_user
import logging
from config.logging_config import setup_logging
from config.app_config import get_route, get_navigation_path
from nicegui import app

setup_logging()
logger = logging.getLogger(__name__)
logged_in_user: dict[str, User | None] = {'user': None}

def set_logged_in_user(user: User) -> None:
    logged_in_user['user'] = user
    app.storage.user['user_id'] = user.id

@ui.page(get_route('/'))
def login_page() -> None:
    render_login_form(set_logged_in_user)


@ui.page(get_route('/pool'))
async def pool_page() -> None:
    if logged_in_user['user']:
        await render_pool_form(logged_in_user['user'])
    else:
        ui.label('Lütfen önce giriş yapın')
        ui.link('Girişe git', get_navigation_path('/'))

@ui.page(get_route('/submissions'))
async def submissions_page() -> None:
    if logged_in_user['user']:
        await render_submissions_dashboard(logged_in_user['user'])
    else:
        ui.label('Lütfen önce giriş yapın')
        ui.link('Girişe git', get_navigation_path('/'))

@ui.page(get_route('/form'))
async def new_form_page() -> None:
    if logged_in_user['user']:
        await render_pool_form(logged_in_user['user'])
    else:
        ui.label('Lütfen önce giriş yapın')
        ui.link('Girişe git', get_navigation_path('/'))

@ui.page(get_route('/form/{ref_id}'))
async def form_page(ref_id: str):
    # Get the current logged-in user
    user = await get_current_user()

    # Authentication Guard
    if not user:
        ui.label('Bu formu görüntülemek için lütfen giriş yapın.')
        ui.navigate.to(get_navigation_path('/'))
        return

    # Render the Form Component
    await render_pool_form(user, reading_ref_id=ref_id)

if __name__ in {"__main__", "__mp_main__"}:
    # str(uuid.uuid4())
    ui.run(
        storage_secret="cookie",
        title='Pool App',
        port=8000,
    )
