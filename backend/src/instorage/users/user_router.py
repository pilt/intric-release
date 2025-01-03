from uuid import UUID

import aiohttp
import jwt
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from instorage.authentication import auth_dependencies
from instorage.authentication.auth_models import AccessToken, ApiKey, OpenIdConnectLogin
from instorage.main import config
from instorage.main.aiohttp_client import aiohttp_client
from instorage.main.container.container import Container
from instorage.main.logging import get_logger
from instorage.main.models import PaginatedResponse
from instorage.server import protocol
from instorage.server.dependencies.container import get_container
from instorage.server.protocol import responses
from instorage.tenants.tenant import TenantPublic
from instorage.users import user_factory
from instorage.users.user import (
    PropUserInvite,
    PropUserUpdate,
    UserAdminView,
    UserInDB,
    UserLogin,
    UserPublic,
    UserSparse,
)
from instorage.users.user_service import UserService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/login/token/",
    response_model=AccessToken,
    name="Login",
    responses=responses.get_responses([401]),
)
async def user_login_with_email_and_password(
    service: UserService = Depends(user_factory.get_user_service),
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    """OAuth2 Login"""

    try:
        UserLogin(email=form_data.username, password=form_data.password)
    except ValidationError as e:
        raise HTTPException(422, e.errors())

    return await service.login(form_data.username, form_data.password)


@router.post("/login/openid-connect/mobilityguard/", response_model=AccessToken)
async def login_with_mobilityguard(
    openid_connect_login: OpenIdConnectLogin,
    container: Container = Depends(get_container()),
):
    """OpenID Connect Login with mobilityguard."""
    settings = config.get_settings()
    # Get the endpoints from discovery endpoint
    async with aiohttp_client().get(settings.mobilityguard_discovery_endpoint) as resp:
        endpoints = await resp.json()

    token_endpoint = endpoints["token_endpoint"]
    jwks_endpoint = endpoints["jwks_uri"]
    signing_algos = endpoints["id_token_signing_alg_values_supported"]

    # Exchange code for a token
    async with aiohttp_client().post(
        token_endpoint,
        data=openid_connect_login.model_dump(),
        auth=aiohttp.BasicAuth(
            openid_connect_login.client_id,
            settings.mobilityguard_client_secret,
        ),
    ) as resp:
        token_response = await resp.json()

    id_token = token_response["id_token"]
    access_token = token_response["access_token"]

    # Get the jwks
    jwks_client = jwt.PyJWKClient(jwks_endpoint)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    # Sign in
    user_service = container.user_service()
    intric_token, was_federated, user_in_db = (
        await user_service.login_with_mobilityguard(
            id_token=id_token,
            access_token=access_token,
            key=signing_key,
            signing_algos=signing_algos,
        )
    )

    return intric_token


@router.get("/", response_model=PaginatedResponse[UserSparse])
async def get_tenant_users(
    container: Container = Depends(get_container(with_user=True)),
):
    user = container.user()
    user_repo = container.user_repo()

    users = await user_repo.get_all_users(tenant_id=user.tenant_id)

    return protocol.to_paginated_response(users)


@router.get(
    "/me/",
    response_model=UserPublic,
    name="Get current user",
    responses=responses.get_responses([404]),
)
async def get_currently_authenticated_user(
    current_user: UserInDB = Depends(
        auth_dependencies.get_current_active_user_with_quota
    ),
):
    truncated_key = (
        current_user.api_key.truncated_key if current_user.api_key is not None else None
    )
    return UserPublic(**current_user.model_dump(), truncated_api_key=truncated_key)


@router.get("/api-keys/", response_model=ApiKey)
async def generate_api_key(
    current_user: UserInDB = Depends(auth_dependencies.get_current_active_user),
    service: UserService = Depends(user_factory.get_user_service),
):
    """Generating a new api key will delete the old key.
    Make sure to copy the key since it will only be showed once,
    after which only the truncated key will be shown."""

    return await service.generate_api_key(current_user.id)


@router.get(
    "/tenant/",
    response_model=TenantPublic,
    name="Get current user tenant",
    responses=responses.get_responses([404]),
)
async def get_current_user_tenant(
    current_user: UserInDB = Depends(auth_dependencies.get_current_active_user),
):
    tenant = current_user.tenant
    return TenantPublic(**tenant.model_dump())


@router.post("/admin/invite/", response_model=UserAdminView, status_code=201)
async def invite_user(
    user_invite: PropUserInvite,
    container: Container = Depends(get_container(with_user=True)),
):
    user_service = container.prop_user_service()

    return await user_service.invite_user(user_invite)


@router.patch("/admin/{id}/", response_model=UserAdminView)
async def update_user(
    id: UUID,
    user_update: PropUserUpdate,
    container: Container = Depends(get_container(with_user=True)),
):
    user_service = container.prop_user_service()

    return await user_service.update_user(user_id=id, user_update=user_update)


@router.delete("/admin/{id}/", status_code=204)
async def delete_user(
    id: UUID, container: Container = Depends(get_container(with_user=True))
):
    user_service = container.prop_user_service()

    await user_service.delete_user(user_id=id)
