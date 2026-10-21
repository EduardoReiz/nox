import { FastifyPluginAsync } from 'fastify';
import { requireAuth } from '../middlewares/requireAuth.js';
import { prisma } from '../utils/z.js';
import { z } from 'zod';

export const portfolioRoutes: FastifyPluginAsync = async (app) => {
  app.addHook('onRequest', requireAuth);
  app.get('/', async (req)=>{
    const userId = (req as any).user.sub as string;
    return prisma.portfolio.findMany({ where:{ userId }, include:{ holdings:{ include:{ asset:true } } } });
  });
  app.post('/', async (req,res)=>{
    const b = z.object({ name:z.string().min(1), base:z.string().default('BRL') }).parse(req.body);
    const userId = (req as any).user.sub as string;
    const portfolio = await prisma.portfolio.create({ data:{ userId, ...b } });
    return res.code(201).send(portfolio);
  });
  app.post('/:id/transactions', async (req,res)=>{
    const params = z.object({ id:z.string() }).parse(req.params);
    const b = z.object({ symbol:z.string(), type:z.enum(['BUY','SELL']), qty:z.number().positive(), price:z.number().positive() }).parse(req.body);
    const asset = await prisma.asset.upsert({ where:{ symbol:b.symbol }, update:{}, create:{ symbol:b.symbol, name:b.symbol, kind:'CRYPTO' } });
    const tx = await prisma.transaction.create({ data:{ portfolioId: params.id, assetId: asset.id, type: b.type, qty: b.qty, price: b.price } });
    const holding = await prisma.holding.findFirst({ where:{ portfolioId: params.id, assetId: asset.id } });
    if(!holding){
      await prisma.holding.create({ data:{ portfolioId: params.id, assetId: asset.id, qty: b.type==='BUY'? b.qty : -b.qty, avgPrice: b.price } });
    }else{
      const qty = Number(holding.qty); const avg = Number(holding.avgPrice);
      if(b.type==='BUY'){ const newQty=qty+b.qty; const newAvg=newQty>0?(qty*avg+b.qty*b.price)/newQty:avg;
        await prisma.holding.update({ where:{ id: holding.id }, data:{ qty:newQty, avgPrice:newAvg } });
      }else{ const newQty=qty-b.qty; await prisma.holding.update({ where:{ id: holding.id }, data:{ qty:newQty } }); }
    }
    return res.code(201).send(tx);
  });
};
