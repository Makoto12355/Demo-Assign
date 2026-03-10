# Full Stack Demo Website

This system is make easy to use and easy to understand to use and deploy on clound

## Tech Stack
- **Backend** Python
- **Database** PostgreSQL on Supabase
- **Frontend** HTML, CSS
- **Deployment** Railway / Docker

## Documentation
1. **[Local SetUp](/docs/setup_appliance.md)**
2. **[SaaS SetUp](/docs/setup_saas.md)**

## Onlinux User
1. Use pyenv run `pyenv local 3.12.9`
2. run command `python -m venv venv`
3. run `venv/bin/activate`

## How to Run 
1. Run command `pip install -r requirements.txt`
2. Change the file name `.env.example` to `.env` and setting the API.
3. Run project `python main.py` or `docker compose up --build`