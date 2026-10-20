// Inscrição nas notificações push do navegador (Web Push).

export function pushDisponivel() {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

// A chave pública VAPID chega em base64url; o navegador quer os bytes.
function bytesDaChave(base64url) {
  const base64 = (base64url + '='.repeat((4 - (base64url.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/')
  return Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))
}

export async function inscreverPush(chavePublica) {
  if (!pushDisponivel()) {
    throw new Error('Este navegador não aceita notificações. No iPhone, adicione o Nox à tela de início antes.')
  }
  const permissao = await Notification.requestPermission()
  if (permissao !== 'granted') {
    throw new Error('As notificações foram bloqueadas. Libere nas configurações do navegador para este site.')
  }
  try {
    const registro = await navigator.serviceWorker.register('/sw.js')
    await navigator.serviceWorker.ready
    const inscricao =
      (await registro.pushManager.getSubscription()) ??
      (await registro.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: bytesDaChave(chavePublica) }))
    return inscricao.toJSON()
  } catch {
    // O navegador recusou a inscrição (modo anônimo, serviço de push fora do
    // ar, extensão bloqueando). A mensagem dele vem em inglês e técnica.
    throw new Error(
      'O navegador não conseguiu ativar as notificações. Tente de novo; se continuar, use o Chrome ou o Firefox fora do modo anônimo.',
    )
  }
}

export async function cancelarPush() {
  if (!pushDisponivel()) return
  const registro = await navigator.serviceWorker.getRegistration('/sw.js')
  const inscricao = await registro?.pushManager.getSubscription()
  await inscricao?.unsubscribe()
}
