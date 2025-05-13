from fastapi import FastAPI, Depends, HTTPException, Request, status, Body

import logging
import httpx
import time
import os

from datetime import timedelta
from constants import *
from auth import authenticate_user, create_access_token, get_current_active_user, get_current_user, oauth2_scheme
from pydantic_models import Token, LoginRequest, User, NewUserRequest
import database as db

# Clear proxy settings if needed
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

app = FastAPI()

# Setup logging
logging.basicConfig(filename=LOGGING_FILE, level=logging.INFO)


# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(login_request: LoginRequest = Body(...)):

    user = authenticate_user(login_request.username, login_request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password, or user is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_new_user(new_user: NewUserRequest):
    try:
        db.add_new_user(
            username=new_user.username,
            full_name=new_user.full_name,
            email=new_user.email,
            password=new_user.password
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while adding the new user: {e}"
        )
    return {
        "message": f"New user '{new_user.username}' added successfully. Please contact the Ollama administrator to activate your new account."}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    # Initialize username as 'Anonymous'
    username = "Anonymous"

    try:
        # Attempt to retrieve the token and current user
        token = await oauth2_scheme(request)
        if token:
            current_user = await get_current_user(token=token)
            username = current_user.username
    except HTTPException as e:
        if e.status_code != status.HTTP_401_UNAUTHORIZED:
            # If it's not a 401 error, re-raise the exception
            raise e
        # If it's a 401 error, log it as an anonymous request
        logging.info(f"Unauthenticated request at {timestamp}. Proceeding as anonymous user.")

    # Log the request details
    logging.info(f"Timestamp: {timestamp}, User: {username}, Endpoint: {request.url.path}, Method: {request.method}")

    # Proceed with the request
    response = await call_next(request)

    # Calculate the processing time
    process_time = time.time() - start_time
    logging.info(f"Completed in {process_time:.2f} seconds")

    return response

# Catch-all route should be placed last to prevent it from overriding other routes
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_requests(full_path: str, request: Request, current_user: User = Depends(get_current_active_user)):
    # Extract method and headers
    method = request.method
    headers = dict(request.headers)

    # Fetch the request body if any
    body = await request.body()

    # Send the request to the target server
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=f"{TARGET_SERVER}/{full_path}",
            headers=headers,
            data=body,
            timeout=TIMEOUT
        )

    # Return the response from the target server
    return response.text
