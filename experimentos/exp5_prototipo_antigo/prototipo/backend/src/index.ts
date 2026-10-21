import { createServer } from './server.js'; import { env } from './env.js';
createServer().then(app=>{app.listen({port:env.PORT,host:'0.0.0.0'}).then(()=>app.log.info(`NOX API on :${env.PORT}`)).catch(e=>{app.log.error(e);process.exit(1);});});
