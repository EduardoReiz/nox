import fp from 'fastify-plugin'; import rateLimit from '@fastify/rate-limit'; export const registerRateLimit=fp(async(app)=>{await app.register(rateLimit,{max:300,timeWindow:'1 minute'})});
