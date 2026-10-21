import { FastifyInstance } from 'fastify'; import fp from 'fastify-plugin'; import jwt from '@fastify/jwt'; import { env } from '../env.js'; export const registerAuthPlugin=fp(async(app:FastifyInstance)=>{app.register(jwt,{secret:env.JWT_SECRET}); // @ts-ignore
 app.decorate('authenticate', async(req,res)=>{try{ // @ts-ignore
 await req.jwtVerify();}catch{ return res.code(401).send({error:'unauthorized'});} });});
