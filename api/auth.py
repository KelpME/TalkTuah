from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the bearer token matches the configured API key.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        The verified token
        
    Raises:
        HTTPException: If token is invalid
    """
    if credentials.credentials != settings.proxy_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
