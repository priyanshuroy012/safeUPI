# SafeUPI Frontend

React/Vite frontend for the SafeUPI fraud-prevention prototype.

Run `npm install` then `npm run dev`. Default backend: `http://127.0.0.1:8000`. Set `VITE_API_URL` in `.env` to change it.

Routes: `/`, `/payment`, `/admin`, `/admin/account/:id`. The payment page falls back to demo data if the backend is unavailable.
