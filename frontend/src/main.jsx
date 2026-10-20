import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Moldura from './componentes/Moldura'
import './index.css'
import Aprendizado from './paginas/Aprendizado'
import Feed from './paginas/Feed'
import Home from './paginas/Home'
import ModoExplicativo from './paginas/ModoExplicativo'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Moldura />}>
          <Route path="/" element={<Home />} />
          <Route path="/sinais" element={<Feed />} />
          <Route path="/sinais/:ativo" element={<ModoExplicativo />} />
          <Route path="/aprendizado" element={<Aprendizado />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
