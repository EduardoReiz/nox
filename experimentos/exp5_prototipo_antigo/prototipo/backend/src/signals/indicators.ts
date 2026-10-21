export function computeRSI(closes:number[], period=14){
  if(closes.length < period+1) return [];
  const gains:number[]=[], losses:number[]=[];
  for(let i=1;i<=period;i++){ const d=closes[i]-closes[i-1]; gains.push(Math.max(0,d)); losses.push(Math.max(0,-d)); }
  let avgGain=gains.reduce((a,b)=>a+b,0)/period, avgLoss=losses.reduce((a,b)=>a+b,0)/period;
  const out:number[]=[];
  for(let i=period+1;i<closes.length;i++){ const d=closes[i]-closes[i-1]; const g=Math.max(0,d), l=Math.max(0,-d);
    avgGain=(avgGain*(period-1)+g)/period; avgLoss=(avgLoss*(period-1)+l)/period;
    const rs=avgLoss===0?100:avgGain/avgLoss; out.push(Number((100-(100/(1+rs))).toFixed(2))); }
  return out;
}
export function computeMACD(closes:number[], fast=12, slow=26, signal=9){
  const ema=(arr:number[],p:number)=>{ const k=2/(p+1); const out:number[]=[]; let e=arr[0]; out.push(e); for(let i=1;i<arr.length;i++){ e=arr[i]*k+e*(1-k); out.push(Number(e.toFixed(8))); } return out; };
  if(closes.length<slow+signal) return { macd:[], signal:[], hist:[], cross:'none' as const };
  const ef=ema(closes,fast), es=ema(closes,slow); const macd=ef.map((v,i)=>v-(es[i]??v)); const sig=ema(macd.slice(slow),signal);
  const hist=macd.slice(slow).map((v,i)=>Number((v-(sig[i]??0)).toFixed(8))); const last=hist.at(-1)??0, prev=hist.at(-2)??0;
  const cross = last>0 && prev<=0? 'bull' : last<0 && prev>=0? 'bear' : 'none'; return { macd, signal:sig, hist, cross };
}
