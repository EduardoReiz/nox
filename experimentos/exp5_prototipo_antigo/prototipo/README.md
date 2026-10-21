# NOX — Full Stack (Frontend + Backend)

## Como rodar em dev
Backend:
```bash
cd backend
cp .env.example .env
docker compose up -d db redis
npm i
npx prisma migrate dev
npm run dev
```
Frontend:
```bash
cd ../frontend
npm i
npm run dev
```
Acesse http://localhost:5173 (API em http://localhost:3333).

## Docker Compose na raiz
```bash
docker compose up -d
```
