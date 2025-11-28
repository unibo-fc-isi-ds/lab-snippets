# [A.Y. 2025/2026 Surname, Name] Exercise: RPC Auth Service 2


## Overview

This project extends the exemplified RPC infrastructure with **authentication** and **role-based authorization**. 
Only **admin users** can read user data via `get_user` RPC calls.

## Authentication Service Extension

To support the authentication service, the server stub was extended by adding an instance of `InMemoryAuthenticationService` that delegates authentication operations to the existing user database. 

A new client stub, `RemoteAuthenticationService`, was created specifically for the authentication service interface. This stub exposes the `authenticate` method for obtaining session tokens and automatically memorizes the received token for subsequent requests.

The command-line interface was extended with a new `auth` command that allows users to authenticate by providing credentials and an optional token duration, completing the authentication workflow.

## Authorization Extension

To implement role-based authorization, an optional `metadata` field was added to the `Request` class to carry authentication tokens in subsequent requests. All client stubs now automatically store the token received during authentication and include it in the `metadata` field of every RPC request.

On the server side, specific authorization checks were added for the `get_user` operation. The server first verifies the presence of a token in the request metadata, then validates its correctness and expiration through the authentication service, and finally ensures the user associated with the token has the `ADMIN` role. Only then is access to user data granted.

## Usage
**Copy and Run these commands in your project root directory**
1. Start the server in a terminal with:
```bash 
   poetry run python snippets -l 4 -e 2 8080
```
2. Consider the following sequence of commands (in another terminal):

- add the user (ADMIN):
```bash 
  poetry run python snippets -l 4 -e 4 localhost:8080 add -u gciatto -a giovanni.ciatto@unibo.it giovanni.ciatto@gmail.com -n "Giovanni Ciatto" -r admin -p "my secret password" 
```
- get the user data (Error: Authentication required to read user data)
```bash 
    poetry run python snippets -l 4 -e 4 localhost:8080 get -u gciatto           
```
- authenticate the user (ADMIN):
```bash 
  poetry run python snippets -l 4 -e 4 localhost:8080 auth -u gciatto -p "my secret password" 
```
- get the user data
```bash 
    poetry run python snippets -l 4 -e 4 localhost:8080 get -u gciatto           
```
- add a normal user (USER):
```bash 
    poetry run python snippets -l 4 -e 4 localhost:8080 add -u gciatto2 -a 2giovanni.ciatto@unibo.it 2giovanni.ciatto@gmail.com -n "Giovanni2 Ciatto2" -r user -p "secret password"       
```
- authenticate the user (USER):
```bash 
  poetry run python snippets -l 4 -e 4 localhost:8080 auth -u gciatto2 -p "secret password" 
```
- get the user data (Error: Admin privileges required to read user data)
```bash 
    poetry run python snippets -l 4 -e 4 localhost:8080 get -u gciatto        
```
