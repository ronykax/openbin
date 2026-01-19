### Openbin API
A simple Pastebin API written in Python using FastAPI and served by Uvicorn.

#### Docker Setup
- Create two files: one for the database and one for environment variables (e.g. `openbin.db` and `.env`).
- Populate the `.env` file with the following variables:
```env
OPENBIN_SECRET=abc123
OPENBIN_MAX_SIZE=1048576
```
- Start the container:
```powershell
docker run -p 8000:8000 -v /path/to/openbin.db:/app/db --env-file /path/to/openbin.env -d openbin-api
```
**Running into issues or have ideas for further development? Let me know by [creating an issue](https://github.com/ronykax/openbin/issues).**