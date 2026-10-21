import { prisma } from '../utils/z.js';
import argon2 from 'argon2';
import jwt from 'jsonwebtoken';
import { env } from '../env.js';
import { generateBase32Secret, verifyTOTP } from '../utils/totp.js';
import { randomUUID } from 'crypto';
export async function hashPwd(p:string){ return argon2.hash(p); }
export async function verifyPwd(p:string,h:string){ return argon2.verify(h,p); }
export function signPair(userId:string){
  const accessToken = jwt.sign({ sub:userId, typ:'access' }, env.JWT_SECRET, { expiresIn:'15m' });
  const jti = randomUUID();
  const refreshToken = jwt.sign({ sub:userId, jti, typ:'refresh' }, env.JWT_SECRET, { expiresIn:'7d' });
  prisma.session.create({ data:{ userId, refreshJti:jti, expiresAt:new Date(Date.now()+7*24*3600*1000) } }).catch(()=>{});
  return { accessToken, refreshToken };
}
export function genTOTPSecret(){ return generateBase32Secret(32); }
export { verifyTOTP };
