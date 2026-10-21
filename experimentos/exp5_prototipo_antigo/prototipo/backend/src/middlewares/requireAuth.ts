import type { FastifyRequest, FastifyReply } from 'fastify'; export async function requireAuth(req:FastifyRequest,res:FastifyReply){try{ // @ts-ignore
 await req.jwtVerify(); // @ts-ignore
 req.user={ sub: (req as any).user.sub };}catch{ return res.code(401).send({error:'unauthorized'});}}
