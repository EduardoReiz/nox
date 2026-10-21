import 'dotenv/config';
export const env={NODE_ENV:process.env.NODE_ENV??'development',PORT:Number(process.env.PORT??3333),JWT_SECRET:process.env.JWT_SECRET||'change-me',DATABASE_URL:process.env.DATABASE_URL!,REDIS_URL:process.env.REDIS_URL||'redis://localhost:6379',ALLOWED_ORIGINS:(process.env.ALLOWED_ORIGINS||'').split(',').filter(Boolean)};
