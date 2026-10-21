// Service worker do Nox: torna o site instalável e rápido de abrir (RNF-009),
// recebe os alertas push (RF-012) mesmo com o site fechado e abre a explicação
// do sinal quando a notificação é tocada.

// Guarda só o "esqueleto" do site (página inicial, scripts e estilos). Dados de
// mercado e de conta nunca vão para o cache: um preço velho seria enganoso (RNF-006).
const CACHE = 'nox-esqueleto-v1'

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(CACHE).then((c) => c.add('/')).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (evento) => {
  const { request } = evento
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    // Páginas: rede primeiro; sem internet, abre o esqueleto e a tela mostra o aviso de erro.
    evento.respondWith(fetch(request).catch(() => caches.match('/')))
  } else if (url.pathname.startsWith('/assets/')) {
    // Arquivos com hash no nome nunca mudam: cache primeiro.
    evento.respondWith(
      caches.match(request).then((guardado) => guardado ?? fetch(request).then((resposta) => {
        const copia = resposta.clone()
        caches.open(CACHE).then((c) => c.put(request, copia))
        return resposta
      })),
    )
  }
})

self.addEventListener('push', (evento) => {
  let dados = { titulo: 'Nox', texto: 'Há um sinal novo.', url: '/sinais' }
  try {
    dados = { ...dados, ...evento.data.json() }
  } catch {
    // mensagem sem JSON: fica o texto padrão
  }
  evento.waitUntil(
    self.registration.showNotification(dados.titulo, {
      body: dados.texto,
      icon: '/icone-192.png',
      badge: '/favicon.png',
      data: { url: dados.url },
    }),
  )
})

self.addEventListener('notificationclick', (evento) => {
  evento.notification.close()
  const destino = new URL(evento.notification.data?.url ?? '/sinais', self.location.origin)
  evento.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((janelas) => {
      const aberta = janelas.find((j) => new URL(j.url).origin === destino.origin)
      if (aberta) {
        aberta.navigate(destino.href)
        return aberta.focus()
      }
      return self.clients.openWindow(destino.href)
    }),
  )
})
