import { FastifyPluginAsync } from 'fastify';
import { z } from 'zod';
import { prisma } from '../utils/z.js';
import { hashPwd, verifyPwd, signPair, verifyTOTP, genTOTPSecret } from './service.js';
import { requireAuth } from '../middlewares/requireAuth.js';

export const authRoutes: FastifyPluginAsync = async (app) => {
  app.post('/register', async (req,res)=>{
    const b = z.object({ email:z.string().email(), password:z.string().min(8), name:z.string().optional() }).parse(req.body);
    const exists = await prisma.user.findUnique({ where:{ email:b.email } }); if(exists) return res.code(409).send({error:'email_in_use'});
    const user = await prisma.user.create({ data:{ email:b.email, passwordHash: await hashPwd(b.password), name:b.name } });
    const tokens = signPair(user.id); return { user:{ id:user.id, email:user.email, name:user.name }, ...tokens };
  });
  app.post('/login', async (req,res)=>{
    const { email, password } = z.object({ email:z.string().email(), password:z.string() }).parse(req.body);
    const user = await prisma.user.findUnique({ where:{ email } }); if(!user || !(await verifyPwd(password, user.passwordHash))) return res.code(401).send({error:'invalid_credentials'});
    if(user.twoFAEnabled) return res.code(206).send({ requires2FA:true });
    const tokens = signPair(user.id); return { user:{ id:user.id, email:user.email, name:user.name }, ...tokens };
  });
  app.post('/verify-2fa', async (req,res)=>{
    const { email, code } = z.object({ email:z.string().email(), code:z.string().length(6) }).parse(req.body);
    const user = await prisma.user.findUnique({ where:{ email } }); if(!user) return res.code(401).send({error:'invalid'});
    const secret = await prisma.twoFactorSecret.findUnique({ where:{ userId:user.id } }); if(!secret || !verifyTOTP(secret.secret, code)) return res.code(401).send({error:'bad_2fa'});
    const tokens = signPair(user.id); return { user:{ id:user.id, email:user.email, name:user.name }, ...tokens };
  });
  app.post('/2fa/setup', { preHandler:[requireAuth] }, async (req,res)=>{
    const userId = (req as any).user.sub; const secret = genTOTPSecret();
    await prisma.twoFactorSecret.upsert({ where:{ userId }, create:{ userId, secret, backupCodes:[] }, update:{ secret } });
    await prisma.user.update({ where:{ id:userId }, data:{ twoFAEnabled:true } });
    return { otpauth: `otpauth://totp/Nox:${userId}?secret=${secret}&issuer=Nox` };
  });
};
