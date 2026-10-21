import Fastify from 'fastify';
import { registerCors } from './plugins/cors.js';
import { registerHelmet } from './plugins/helmet.js';
import { registerRateLimit } from './plugins/rate-limit.js';
import { registerAuthPlugin } from './plugins/auth.js';
import { metricsPlugin } from './plugins/metrics.js';
import { authRoutes } from './auth/routes.js';
import { userRoutes } from './users/routes.js';
import { portfolioRoutes } from './portfolios/routes.js';
import { assetRoutes } from './assets/routes.js';
import { signalRoutes } from './signals/routes.js';
import { newsRoutes } from './news/routes.js';
import { pricesWebhook } from './webhooks/prices.js';
export async function createServer(){
  const app = Fastify({ logger: true });
  await registerCors(app); await registerHelmet(app); await registerRateLimit(app); await metricsPlugin(app); await registerAuthPlugin(app);
  app.get('/health', async()=>({ok:true}));
  app.register(authRoutes,{prefix:'/auth'});
  app.register(userRoutes,{prefix:'/users'});
  app.register(portfolioRoutes,{prefix:'/portfolios'});
  app.register(assetRoutes,{prefix:'/assets'});
  app.register(signalRoutes,{prefix:'/signals'});
  app.register(newsRoutes,{prefix:'/news'});
  app.register(pricesWebhook,{prefix:'/webhooks'});
  return app;
}
