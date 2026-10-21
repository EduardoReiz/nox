import fp from 'fastify-plugin'; export const metricsPlugin=fp(async(app)=>{app.get('/metrics', async()=> '# HELP dummy NOX metrics\n# TYPE dummy counter\ndummy 1\n')});
