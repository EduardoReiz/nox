// Service worker do Nox: recebe os alertas push (RF-012) mesmo com o site
// fechado e abre a explicação do sinal quando a notificação é tocada.

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
      icon: '/favicon.png',
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
