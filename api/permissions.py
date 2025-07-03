from fastapi import Depends, HTTPException, status

from models.user import User



def require_roles(*roles : str):
    """
    Dependenci for checking user permissions by roles
    """
    from .auth import current_user
    
    async def check_roles(user : User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have enough permissions")
        return user
    return check_roles
    