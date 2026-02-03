"""
Custom middleware for the Honey-Pot API.
Includes request tracking, logging, security headers, and rate limiting.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.
    The request ID is added to the request state and response headers.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request and response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with request ID header
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add to request state for access in route handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    Logs request details, response status, and processing time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from handler
        """
        # Get request ID if available
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                }
            )
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": f"{process_time:.3f}s",
                },
                exc_info=True
            )
            
            # Re-raise to let error handlers deal with it
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Implements common security best practices.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    Tracks requests per IP address.
    
    Note: For production, consider using Redis-backed rate limiting
    for distributed systems.
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests allowed per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, list[float]] = {}
    
    def _clean_old_requests(self, ip: str, current_time: float):
        """
        Remove requests older than 1 minute.
        
        Args:
            ip: Client IP address
            current_time: Current timestamp
        """
        if ip in self.request_counts:
            # Keep only requests from the last minute
            self.request_counts[ip] = [
                req_time for req_time in self.request_counts[ip]
                if current_time - req_time < 60
            ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limit and process request.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response or rate limit error
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/detailed"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Initialize if new IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "requests": len(self.request_counts[client_ip]),
                    "limit": self.requests_per_minute,
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response
