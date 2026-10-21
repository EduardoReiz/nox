import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Moldura from './componentes/Moldura'
import { ContaProvedor } from './dados/ContaContexto'
import './index.css'
import Aprendizado from './paginas/Aprendizado'
import Conta from './paginas/Conta'
import CriarConta from './paginas/CriarConta'
import Entrar from './paginas/Entrar'
import Feed from './paginas/Feed'
import Home from './paginas/Home'
import ModoExplicativo from './paginas/ModoExplicativo'
import { EsqueciSenha, RedefinirSenha } from './paginas/Senha'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ContaProvedor>
        <Routes>
          <Route element={<Moldura />}>
            <Route path="/" element={<Home />} />
            <Route path="/sinais" element={<Feed />} />
            <Route path="/sinais/:ativo" element={<ModoExplicativo />} />
            <Route path="/aprendizado" element={<Aprendizado />} />
            <Route path="/entrar" element={<Entrar />} />
            <Route path="/criar-conta" element={<CriarConta />} />
            <Route path="/esqueci-senha" element={<EsqueciSenha />} />
            <Route path="/redefinir-senha" element={<RedefinirSenha />} />
            <Route path="/conta" element={<Conta />} />
          </Route>
        </Routes>
      </ContaProvedor>
    </BrowserRouter>
  </StrictMode>,
)

// Registra o service worker só na versão publicada: ele deixa o site instalável
// e abre o esqueleto mesmo sem internet (RNF-009).
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}))
}
