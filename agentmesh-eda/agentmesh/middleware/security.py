"""
Security Middleware and Hardening

Provides comprehensive security headers, CORS configuration, and security utilities.

Architectural Intent:
- OWASP security best practices
- Comprehensive security headers
- XSS and CSRF protection
- Content Security Policy
- API key authentication
- Request logging and monitoring
"""

import time
import hashlib
import secrets
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import re
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger


class SecurityLevel(str, Enum):
    """Security configuration levels"""
    DEVELOPMENT = "development"      # Relaxed for local dev
    TESTING = "testing"            # Medium security for testing
    STAGING = "staging"            # High security for staging
    PRODUCTION = "production"          # Maximum security for production


@dataclass
class SecurityConfig:
    """Security configuration"""
    level: SecurityLevel
    enable_cors: bool = True
    allowed_origins: List[str] = None
    allowed_methods: List[str] = None
    allowed_headers: List[str] = None
    expose_headers: bool = False
    max_age: int = 86400  # 24 hours
    allow_credentials: bool = True
    enable_rate_limit: bool = True
    enable_security_headers: bool = True
    enable_api_key_auth: bool = True
    enable_csp: bool = True
    enable_request_logging: bool = True
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = None


class ContentSecurityPolicy:
    """Content Security Policy builder"""
    
    def __init__(self):
        self.directives = {}
    
    def default_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for default-src"""
        self.directives["default-src"] = " ".join(sources)
        return self
    
    def script_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for script-src"""
        self.directives["script-src"] = " ".join(sources)
        return self
    
    def style_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for style-src"""
        self.directives["style-src"] = " ".join(sources)
        return self
    
    def img_src(self, sources: List[str] = ["'self'", "data:", "https:"]):
        """Allow sources for img-src"""
        self.directives["img-src"] = " ".join(sources)
        return self
    
    def connect_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for connect-src"""
        self.directives["connect-src"] = " ".join(sources)
        return self
    
    def font_src(self, sources: List[str] = ["'self'", "data:", "https:"]):
        """Allow sources for font-src"""
        self.directives["font-src"] = " ".join(sources)
        return self
    
    def object_src(self, sources: List[str] = ["'none'"]):
        """Allow sources for object-src"""
        self.directives["object-src"] = " ".join(sources)
        return self
    
    def media_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for media-src"""
        self.directives["media-src"] = " ".join(sources)
        return self
    
    def frame_src(self, sources: List[str] = ["'none'"]):
        """Allow sources for frame-src"""
        self.directives["frame-src"] = " ".join(sources)
        return self
    
    def child_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for child-src"""
        self.directives["child-src"] = " ".join(sources)
        return self
    
    def worker_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for worker-src"""
        self.directives["worker-src"] = " ".join(sources)
        return self
    
    def manifest_src(self, sources: List[str] = ["'self'"]):
        """Allow sources for manifest-src"""
        self.directives["manifest-src"] = " ".join(sources)
        return self
    
    def base_uri(self, uris: List[str] = ["'self'"]):
        """Allow base URIs"""
        self.directives["base-uri"] = " ".join(uris)
        return self
    
    def form_action(self, actions: List[str] = ["'self'"]):
        """Allow form actions"""
        self.directives["form-action"] = " ".join(actions)
        return self
    
    def frame_ancestors(self, ancestors: List[str] = ["'none'"]):
        """Allow frame ancestors"""
        self.directives["frame-ancestors"] = " ".join(ancestors)
        return self
    
    def upgrade_insecure_requests(self, value: bool = False):
        """Control upgrade of insecure requests"""
        self.directives["upgrade-insecure-requests"] = str(value).lower()
        return self
    
    def block_all_mixed_content(self, value: bool = True):
        """Block mixed content"""
        self.directives["block-all-mixed-content"] = str(value).lower()
        return self
    
    def build(self):
        """Build CSP header value"""
        if not self.directives:
            return ""
        return "; ".join(f"{key} {value}" for key, value in self.directives.items())


class SecurityHeaders:
    """Security headers utility"""
    
    @staticmethod
    def get_security_headers(config: SecurityConfig, request: Request = None) -> Dict[str, str]:
        """Get comprehensive security headers"""
        headers = {}
        
        if config.enable_security_headers:
            # Prevent clickjacking
            headers["X-Content-Type-Options"] = "nosniff"
            headers["X-Frame-Options"] = "DENY"
            headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer policy
            headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # HSTS (only on HTTPS)
            if request and request.url.scheme == "https":
                headers["Strict-Transport-Security"] = f"max-age={config.max_age}; includeSubDomains; preload"
            
            # Permissions policy
            headers["Permissions-Policy"] = "geolocation 'none'; microphone 'none'; camera 'none'"
            
            # Content type options
            headers["X-Content-Type-Options"] = "nosniff"
            
            # Cache control
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            headers["Pragma"] = "no-cache"
            
            # Custom security headers
            headers["X-API-Security-Level"] = config.level.value
            headers["X-Content-Security-Policy"] = "default-src 'self'; script-src 'self'; connect-src 'self'"
            
            # Request ID for tracing
            headers["X-Request-ID"] = secrets.token_urlsafe(32)
        
        return headers


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML input by stripping all tags and dangerous URI schemes.

        For rich-text use cases, use a dedicated library like bleach instead.
        """
        if not text:
            return ""

        # Strip all HTML tags
        sanitized = re.sub(r'<[^>]+>', '', text)
        # Remove dangerous URI schemes
        sanitized = re.sub(r'(?:javascript|vbscript|data)\s*:', '', sanitized, flags=re.IGNORECASE)
        # Remove HTML entities that could be used for encoding attacks
        sanitized = re.sub(r'&#[xX]?[0-9a-fA-F]+;?', '', sanitized)
        return sanitized
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Sanitize SQL input by escaping dangerous characters.

        WARNING: This is a defense-in-depth measure only.
        Always use parameterized queries for database operations.
        Regex-based SQL filtering is inherently bypassable.
        """
        if not text:
            return ""

        # Escape single quotes (the primary SQL injection vector)
        sanitized = text.replace("'", "''")
        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")
        return sanitized
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path"""
        if not path:
            return ""
        
        # Remove path traversal patterns
        dangerous_patterns = [
            r'\.\.[\\/]',  # Directory traversal
            r'[\\/]\.\.[\\/]',  # Directory traversal
            r'\.\.[\\/]',  # Directory traversal
        ]
        
        sanitized = path
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized)
        
        # Remove multiple slashes
        sanitized = re.sub(r'/+', '/', sanitized)
        
        return sanitized.lstrip('/')


class APIKeyValidator:
    """API key validation and management"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Basic format validation
        if len(api_key) < 16 or len(api_key) > 128:
            return False
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not api_key.replace('-', '').replace('_', '').isalnum():
            return False
        
        return True
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
    
    def _is_whitelisted_ip(self, request: Request) -> bool:
        """Check if IP is whitelisted"""
        if not self.config.enable_ip_whitelist or not self.config.ip_whitelist:
            return True
        
        client_host = request.client.host if request.client else "unknown"
        return client_host in self.config.ip_whitelist
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Middleware dispatch method"""
        # Skip security checks for health endpoints
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # IP whitelist check
        if not self._is_whitelisted_ip(request):
            logger.warning(f"Blocked request from non-whitelisted IP: {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Access denied",
                    "code": "IP_NOT_ALLOWED"
                }
            )
        
        # Create response with security headers
        response = await call_next(request)
        
        # Add security headers
        security_headers = SecurityHeaders.get_security_headers(self.config, request)
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add CSP header if enabled
        if self.config.enable_csp:
            csp = ContentSecurityPolicy()
            
            # Configure CSP based on security level
            if self.config.level == SecurityLevel.PRODUCTION:
                csp.default_src().script_src("'self'").style_src("'self'").img_src("'self'", "data:", "https:").build()
            elif self.config.level == SecurityLevel.STAGING:
                csp.default_src().script_src("'self'").build()
            else:  # Development/Testing
                csp.default_src().build()
            
            response.headers["Content-Security-Policy"] = csp.build()
        
        # Add CORS headers if enabled
        if self.config.enable_cors:
            self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(self, response: Response, request: Request):
        """Add CORS headers based on configuration"""
        origin = request.headers.get("origin")
        
        if not origin:
            return
        
        # Check if origin is allowed
        if self.config.allowed_origins:
            if origin not in self.config.allowed_origins:
                return
            response.headers["Access-Control-Allow-Origin"] = origin
            if self.config.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            # No allowed_origins configured — only allow without credentials
            # Never combine Access-Control-Allow-Credentials with reflected origins
            response.headers["Access-Control-Allow-Origin"] = origin
        
        if self.config.allowed_methods:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.config.allowed_methods)
        else:
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        
        if self.config.allowed_headers:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.config.allowed_headers)
        else:
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key, X-Request-ID"
        
        if not self.config.expose_headers:
            # Don't expose CORS headers to browser
            response.headers["Vary"] = "Origin"


class RequestLogger:
    """Request logging for security monitoring"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    async def log_request(self, request: Request, response: Response, duration: float):
        """Log request for security monitoring"""
        if not self.config.enable_request_logging:
            return
        
        # Extract relevant information
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "api_key_present": "X-API-Key" in request.headers,
            "content_type": request.headers.get("content-type", "unknown"),
            "content_length": request.headers.get("content-length", "0"),
            "response_status": response.status_code,
            "duration_ms": duration * 1000,
            "request_id": response.headers.get("X-Request-ID", "unknown"),
            "security_headers": dict(response.headers),
        }
        
        # Log based on security level
        if self.config.level == SecurityLevel.PRODUCTION:
            logger.info(f"Request: {log_data}")
        elif self.config.level == SecurityLevel.STAGING:
            logger.info(f"Request: {log_data}")
        else:  # Development/Testing
            logger.debug(f"Request: {log_data}")


# Security utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def validate_file_upload(filename: str, content_type: str, max_size: int = 10 * 1024 * 1024) -> bool:
    """Validate file upload for security"""
    # Check file extension
    allowed_extensions = {'.txt', '.json', '.csv', '.xml', '.yml', '.yaml'}
    file_ext = '.' + filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    if file_ext not in allowed_extensions:
        logger.warning(f"Blocked file upload with disallowed extension: {file_ext}")
        return False
    
    # Check MIME type
    allowed_mime_types = {
        'text/plain', 'application/json', 'text/csv', 
        'application/xml', 'text/xml', 'application/yaml', 'text/yaml'
    }
    
    if content_type not in allowed_mime_types:
        logger.warning(f"Blocked file upload with disallowed MIME type: {content_type}")
        return False
    
    # Note: File size should be checked by the upload handler
    return True


def rate_limit_by_user_id(request: Request) -> str:
    """Extract user ID for rate limiting"""
    # Try API key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{APIKeyValidator.hash_api_key(api_key)}"
    
    # Try user ID header
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


# Default security configurations
SECURITY_CONFIGS = {
    SecurityLevel.DEVELOPMENT: SecurityConfig(
        level=SecurityLevel.DEVELOPMENT,
        enable_cors=True,
        allowed_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        enable_rate_limit=False,
        enable_csp=False,
    ),
    SecurityLevel.TESTING: SecurityConfig(
        level=SecurityLevel.TESTING,
        enable_cors=True,
        allowed_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        enable_rate_limit=True,
        enable_csp=True,
    ),
    SecurityLevel.STAGING: SecurityConfig(
        level=SecurityLevel.STAGING,
        enable_cors=True,
        allowed_origins=["https://staging.agentmesh.ai"],
        allow_credentials=True,
        enable_rate_limit=True,
        enable_csp=True,
        enable_request_logging=True,
    ),
    SecurityLevel.PRODUCTION: SecurityConfig(
        level=SecurityLevel.PRODUCTION,
        enable_cors=True,
        allowed_origins=["https://api.agentmesh.ai"],
        allow_credentials=False,
        enable_rate_limit=True,
        enable_csp=True,
        enable_request_logging=True,
        max_age=31536000,  # 1 year
    ),
}