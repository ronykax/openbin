### Opnbin API
A simple Pastebin API written in Python using FastAPI.

| Method | Path    | Description                                               |
|--------|---------|-----------------------------------------------------------|
| GET    | `/ping` | Health check                                              |
| POST   | `/`     | Create a new paste                                        |
| GET    | `/[id]` | Read a paste                                              |
| PUT    | `/[id]` | Update a paste                                            |
| DELETE | `/[id]` | Delete a paste                                            |
| GET    | `/`     | List pastes (supports pagination, search, filters)        |

#### Docker Setup
- Create two files: one for the database and one for environment variables (e.g. `opnbin.db` and `.env`).
- Populate the `.env` file with the following variables:
```env
OPNBIN_SECRET=abc123
OPNBIN_MAX_SIZE=1048576
```
- Start the container:
```powershell
docker run -p 8000:8000 -v /path/to/opnbin.db:/app/db --env-file /path/to/opnbin.env -d opnbin-api
```

**Running into issues or have ideas for further development? Let us know by [creating an issue](https://github.com/opnbin/api/issues).**