from fastapi import HTTPException, status

def raise_not_found_exception(detail: str = "Resource not found"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

def raise_forbidden_exception(detail: str = "You're not authorized to perform this action"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def raise_bad_request_exception(detail: str = "Invalid Request"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def raise_no_content(detail: str = "Content was Removed or Replaced"):
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=detail)