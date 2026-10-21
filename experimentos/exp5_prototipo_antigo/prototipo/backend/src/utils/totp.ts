import crypto from 'crypto';
export function generateBase32Secret(length=20){ return crypto.randomBytes(length).toString('base64').replace(/[^A-Z2-7]/gi,'').slice(0,length); }
export function totp(secret:string, window=0, step=30){
  const epoch=Math.floor(Date.now()/1000); const counter=Math.floor(epoch/step)+window;
  const key=Buffer.from(secret,'ascii'); const msg=Buffer.alloc(8); msg.writeBigUInt64BE(BigInt(counter));
  const hmac=crypto.createHmac('sha1',key).update(msg).digest(); const offset=hmac[hmac.length-1]&0xf;
  const code=((hmac.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0'); return code;
}
export function verifyTOTP(secret:string, code:string){ return [-1,0,1].some(w=>totp(secret,w)===code); }
