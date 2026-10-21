import fp from 'fastify-plugin'; import helmet from '@fastify/helmet'; export const registerHelmet=fp(async(app)=>{await app.register(helmet,{contentSecurityPolicy:false})});
