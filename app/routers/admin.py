from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app import xray
from app.db import Session, crud, get_db
from app.dependencies import get_admin_by_username, validate_admin
from app.models.admin import Admin, AdminCreate, AdminModify, Token
from app.models.proxy import ProxyInbound, ProxyTypes, ShadowsocksSettings, VLESSSettings, VMessSettings, TrojanSettings
from app.models.user import UserStatus, UserModify
from app.utils import report, responses
from app.utils.jwt import create_admin_token
from config import LOGIN_NOTIFY_WHITE_LIST

router = APIRouter(tags=["Admin"], prefix="/api", responses={401: responses._401})


def get_client_ip(request: Request) -> str:
    """Extract the client's IP address from the request headers or client."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "Unknown"


@router.post("/admin/token", response_model=Token)
def admin_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate an admin and issue a token."""
    client_ip = get_client_ip(request)

    dbadmin = validate_admin(db, form_data.username, form_data.password)
    if not dbadmin:
        report.login(form_data.username, form_data.password, client_ip, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if client_ip not in LOGIN_NOTIFY_WHITE_LIST:
        report.login(form_data.username, "🔒", client_ip, True)

    return Token(access_token=create_admin_token(form_data.username, dbadmin.is_sudo))


@router.post(
    "/admin",
    response_model=Admin,
    responses={403: responses._403, 409: responses._409},
)
def create_admin(
    new_admin: AdminCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Create a new admin if the current admin has sudo privileges."""
    try:
        dbadmin = crud.create_admin(db, new_admin)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Admin already exists")

    return dbadmin


@router.put(
    "/admin/{username}",
    response_model=Admin,
    responses={403: responses._403, 404: responses._404},
)
def modify_admin(
    modified_admin: AdminModify,
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Modify an existing admin's details."""
    if (dbadmin.username != current_admin.username) and dbadmin.is_sudo:
        raise HTTPException(
            status_code=403,
            detail="You're not allowed to edit another sudoer's account. Use marzban-cli instead.",
        )

    updated_admin = crud.update_admin(db, dbadmin, modified_admin)

    return updated_admin


@router.delete(
    "/admin/{username}",
    responses={403: responses._403},
)
def remove_admin(
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Remove an admin from the database."""
    if dbadmin.is_sudo:
        raise HTTPException(
            status_code=403,
            detail="You're not allowed to delete sudo accounts. Use marzban-cli instead.",
        )

    crud.remove_admin(db, dbadmin)
    return {"detail": "Admin removed successfully"}


@router.get("/admin", response_model=Admin)
def get_current_admin(admin: Admin = Depends(Admin.get_current)):
    """Retrieve the current authenticated admin."""
    return admin


@router.get(
    "/admins",
    response_model=List[Admin],
    responses={403: responses._403},
)
def get_admins(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Fetch a list of admins with optional filters for pagination and username."""
    return crud.get_admins(db, offset, limit, username)


@router.post("/admin/{username}/users/disable", responses={403: responses._403, 404: responses._404})
def disable_all_active_users(
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Disable all active users under a specific admin"""
    crud.disable_all_active_users(db=db, admin=dbadmin)
    startup_config = xray.config.include_db_users()
    xray.core.restart(startup_config)
    for node_id, node in list(xray.nodes.items()):
        if node.connected:
            xray.operations.restart_node(node_id, startup_config)
    return {"detail": "Users successfully disabled"}


@router.post("/admin/{username}/users/activate", responses={403: responses._403, 404: responses._404})
def activate_all_disabled_users(
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Activate all disabled users under a specific admin"""
    crud.activate_all_disabled_users(db=db, admin=dbadmin)
    startup_config = xray.config.include_db_users()
    xray.core.restart(startup_config)
    for node_id, node in list(xray.nodes.items()):
        if node.connected:
            xray.operations.restart_node(node_id, startup_config)
    return {"detail": "Users successfully activated"}


@router.post(
    "/admin/usage/reset/{username}",
    response_model=Admin,
    responses={403: responses._403},
)
def reset_admin_usage(
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Resets usage of admin."""
    return crud.reset_admin_usage(db, dbadmin)


@router.get(
    "/admin/usage/{username}",
    response_model=int,
    responses={403: responses._403},
)
def get_admin_usage(
    dbadmin: Admin = Depends(get_admin_by_username),
    current_admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Retrieve the usage of given admin."""
    return dbadmin.users_usage


#! IF this is dirty, because your system is dirty!
@router.post(
    "/admin/{username}/sync",
    response_model=Dict[str, int],
    responses={403: responses._403, 409: responses._409},
)
def sync_admin(
    configs: Dict[ProxyTypes, List[ProxyInbound]],
    dbadmin: Admin = Depends(get_admin_by_username),
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Sync user inbounds with allowed configs"""
    users = crud.get_users(db=db, admin=dbadmin)
    unsuccessful = 0

    allowed_inbounds = {
        protocol: [inbound.tag for inbound in inbounds]
        for protocol, inbounds in configs.items()
    }

    for user in users:
        try:
            new_inbounds = {}
            for protocol, tags in user.inbounds.items():
                if protocol in allowed_inbounds:
                    new_tags = [tag for tag in tags if tag in allowed_inbounds[protocol]]
                    if new_tags:
                        new_inbounds[protocol] = new_tags

            for protocol, tags in allowed_inbounds.items():
                if protocol in new_inbounds:
                    existing_tags = set(new_inbounds[protocol])
                    new_tags = list(existing_tags.union(tags))
                    new_inbounds[protocol] = new_tags
                else:
                    new_inbounds[protocol] = tags

            new_proxies = {
                p.type.value: p.settings 
                for p in user.proxies 
                if p.type.value in new_inbounds
            }
            
            for protocol in new_inbounds:
                if protocol not in new_proxies:
                    if protocol == ProxyTypes.Shadowsocks:
                        new_proxies[protocol] = ShadowsocksSettings().dict()
                    elif protocol == ProxyTypes.VMess:
                        new_proxies[protocol] = VMessSettings().dict()
                    elif protocol == ProxyTypes.VLESS:
                        new_proxies[protocol] = VLESSSettings().dict()
                    elif protocol == ProxyTypes.Trojan:
                        new_proxies[protocol] = TrojanSettings().dict()

            if new_inbounds != user.inbounds or new_proxies != {p.type.value: p.settings for p in user.proxies}:
                user = crud.update_user(
                    db,
                    user,
                    UserModify(inbounds=new_inbounds, proxies=new_proxies))
                
                if user.status in [UserStatus.active, UserStatus.on_hold]:
                    xray.operations.update_user(user)

        except Exception:
            db.rollback()
            unsuccessful += 1

    return {
        "total": len(users),
        "success": len(users) - unsuccessful,
        "unsuccessful": unsuccessful
    }