"""Data models for SOAJS Python middleware using Pydantic."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Credentials(BaseModel):
    """Database credentials."""
    username: str
    password: str


class DBHost(BaseModel):
    """Database host information."""
    host: str
    port: int


class RegistryLocation(BaseModel):
    """Database registry location."""
    l1: str
    l2: str
    env: str


class Database(BaseModel):
    """Database configuration."""
    name: str
    prefix: Optional[str] = None
    cluster: str
    servers: List[DBHost]
    credentials: Optional[Credentials] = None
    streaming: Optional[Any] = None
    registry_location: Optional[RegistryLocation] = Field(None, alias="registryLocation")
    url_param: Optional[Any] = Field(None, alias="URLParam")
    extra_param: Optional[Any] = Field(None, alias="extraParam")

    # Session specific fields
    store: Optional[Any] = None
    collection: Optional[str] = None
    stringify: Optional[bool] = None
    expire_after: Optional[int] = Field(None, alias="expireAfter")

    model_config = ConfigDict(populate_by_name=True)


class Agent(BaseModel):
    """Agent configuration."""
    topology_dir: Optional[str] = Field(None, alias="topologyDir")

    model_config = ConfigDict(populate_by_name=True)


class ServiceKey(BaseModel):
    """Service key configuration."""
    algorithm: str
    password: str


class Formatter(BaseModel):
    """Logger formatter configuration."""
    level_in_string: Optional[bool] = Field(None, alias="levelInString")
    output_mode: Optional[str] = Field(None, alias="outputMode")

    model_config = ConfigDict(populate_by_name=True)


class Logger(BaseModel):
    """Logger configuration."""
    src: Optional[bool] = None
    level: Optional[str] = None
    formatter: Optional[Formatter] = None


class ServicePort(BaseModel):
    """Service port configuration."""
    controller: int
    maintenance_inc: Optional[int] = Field(None, alias="maintenanceInc")
    random_inc: Optional[int] = Field(None, alias="randomInc")

    model_config = ConfigDict(populate_by_name=True)


class Cookie(BaseModel):
    """Cookie configuration."""
    secret: str


class SessionCookie(BaseModel):
    """Session cookie configuration."""
    path: str
    http_only: Optional[bool] = Field(None, alias="httpOnly")
    secure: Optional[bool] = None
    max_age: Optional[Any] = Field(None, alias="maxAge")

    model_config = ConfigDict(populate_by_name=True)


class Session(BaseModel):
    """Session configuration."""
    name: str
    secret: str
    cookie: Optional[SessionCookie] = None
    resave: Optional[bool] = None
    save_uninitialized: Optional[bool] = Field(None, alias="saveUninitialized")
    rolling: Optional[bool] = None
    unset: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ServiceConfigIntervals(BaseModel):
    """Service configuration intervals."""
    cache_ttl: Optional[int] = Field(None, alias="cacheTTL")
    health_check_interval: Optional[int] = Field(None, alias="healthCheckInterval")
    auto_reload_registry: Optional[int] = Field(None, alias="autoReloadRegistry")
    max_log_count: Optional[int] = Field(None, alias="maxLogCount")
    auto_register_service: Optional[bool] = Field(None, alias="autoRegisterService")

    model_config = ConfigDict(populate_by_name=True)


class ServiceConfig(BaseModel):
    """Service configuration."""
    awareness: ServiceConfigIntervals
    agent: Optional[Agent] = None
    key: Optional[ServiceKey] = None
    logger: Optional[Logger] = None
    ports: Optional[ServicePort] = None
    cookie: Optional[Cookie] = None
    session: Optional[Session] = None

    model_config = ConfigDict(populate_by_name=True)


class CustomRegistry(BaseModel):
    """Custom registry information."""
    id: str = Field(alias="_id")
    name: str
    locked: bool
    plugged: bool
    shared: bool
    value: Any
    created: str
    author: str

    model_config = ConfigDict(populate_by_name=True)


class Resource(BaseModel):
    """Resource configuration."""
    id: str = Field(alias="_id")
    name: str
    type: str
    category: str
    created: str
    author: str
    locked: bool
    plugged: bool
    shared: bool
    config: Any

    model_config = ConfigDict(populate_by_name=True)


class Service(BaseModel):
    """Service information."""
    group: str
    port: int


class Registry(BaseModel):
    """Main registry structure."""
    time_loaded: int = Field(alias="timeLoaded")
    name: str
    environment: str
    service_type: Optional[str] = None
    core_dbs: Dict[str, Database] = Field(default_factory=dict, alias="coreDB")
    tenant_meta_dbs: Dict[str, Database] = Field(default_factory=dict, alias="tenantMetaDB")
    service_config: ServiceConfig = Field(alias="serviceConfig")
    custom: Dict[str, CustomRegistry] = Field(default_factory=dict)
    resources: Dict[str, Dict[str, Resource]] = Field(default_factory=dict)
    services: Dict[str, Service] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class TenantMain(BaseModel):
    """Tenant main information."""
    id: str
    code: str


class Key(BaseModel):
    """API key information."""
    config: Dict[str, Any] = Field(default_factory=dict)
    i_key: Optional[str] = Field(None, alias="iKey")
    e_key: Optional[str] = Field(None, alias="eKey")

    model_config = ConfigDict(populate_by_name=True)


class Application(BaseModel):
    """Application information."""
    product: str
    package: str
    app_id: Optional[str] = Field(None, alias="appId")
    acl: Optional[Any] = None
    acl_all_env: Optional[Any] = Field(None, alias="acl_all_env")
    package_acl: Dict[str, Any] = Field(default_factory=dict, alias="package_acl")
    package_acl_all_env: Dict[str, Any] = Field(default_factory=dict, alias="package_acl_all_env")

    model_config = ConfigDict(populate_by_name=True)


class Tenant(BaseModel):
    """Tenant information."""
    id: str
    code: str
    locked: bool
    key: Key
    roaming: Optional[Any] = None
    application: Optional[Application] = None
    profile: Optional[Any] = None
    main: Optional[TenantMain] = None


class Urac(BaseModel):
    """User record (URAC) information."""
    id: str = Field(alias="_id")
    username: str
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    email: str
    groups: List[str] = Field(default_factory=list)
    social_login: Optional[Any] = Field(None, alias="socialLogin")
    tenant: Optional[Tenant] = None
    profile: Optional[Any] = None
    acl: Optional[Any] = None
    acl_all_env: Optional[Any] = Field(None, alias="acl_AllEnv")

    model_config = ConfigDict(populate_by_name=True)


class InterConnect(BaseModel):
    """InterConnect service information."""
    name: str
    version: str
    host: str
    port: int
    latest: Optional[str] = None


class Host(BaseModel):
    """Host information with InterConnect."""
    host: str
    port: int
    inter_connect: List[InterConnect] = Field(default_factory=list, alias="interConnect")

    model_config = ConfigDict(populate_by_name=True)


class ContextData(BaseModel):
    """HTTP request context data."""
    tenant: Tenant
    urac: Optional[Urac] = None
    services_config: Dict[str, Any] = Field(default_factory=dict)
    device: Optional[str] = None
    geo: Optional[Dict[str, str]] = None
    awareness: Host
    registry: Optional[Registry] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class ConnectResponse(BaseModel):
    """Response from Connect function."""
    host: str
    headers: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)
