## 1. Prequisites
+ Python3.12.9
+ Docker & Docker Compose

## 2. Environment Variable (.env)
+ Change name .env.example to .env
+ **Supabase**: 
    + Supabase URL: Change it to your real url
    + Supabase Password: Change it to your real password
    + Supabase Key: Change it to your real key
+ **Discord**: 
    + Discord Webhook: Change it to your real webhook
+ **Resend**: 
    + Resend API Key: Change it to your real api key
+ **Port**: 
    + Port: Change it to your port you want

## 3. Local Execution
1. pip install -r requirements.txt
2. python main.py
3. Open http://localhost:{port} in your browser <-- port is mean your port from .env