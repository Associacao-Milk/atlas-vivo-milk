(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cosmos = document.querySelector('#cosmos');
  const count = reduced ? 36 : Math.min(130, Math.floor(innerWidth / 9));
  const fragment = document.createDocumentFragment();
  for (let i = 0; i < count; i += 1) {
    const star = document.createElement('i');
    star.className = 'star';
    star.style.cssText = `left:${Math.random()*100}%;top:${Math.random()*100}%;--s:${.5+Math.random()*2.4}px;--o:${.2+Math.random()*.75};--d:${12+Math.random()*34}s;--x:${-45+Math.random()*90}px;--y:${-45+Math.random()*90}px;animation-delay:${-Math.random()*30}s`;
    fragment.append(star);
  }
  cosmos.append(fragment);

  const opening = document.querySelector('#opening');
  const territory = document.querySelector('#territory');
  document.querySelector('#enterAtlas').addEventListener('click', () => {
    opening.classList.add('leaving');
    setTimeout(() => {
      opening.hidden = true;
      territory.hidden = false;
      territory.focus?.();
      scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
    }, reduced ? 10 : 650);
  });

  const ticket = document.querySelector('#ticket');
  const response = document.querySelector('#ticketResponse');
  document.querySelectorAll('[data-ticket]').forEach((button) => button.addEventListener('click', () => {
    response.textContent = '';
    ticket.showModal();
  }));
  ticket.querySelector('.close').addEventListener('click', () => ticket.close());
  ticket.addEventListener('click', (event) => { if (event.target === ticket) ticket.close(); });
  const replies = {
    brincar: 'As dinâmicas do lugar surgem depois da leitura e validação territorial.',
    convite: 'Os convites das festas serão apresentados com data, fonte e validação humana.',
    sorte: 'O inesperado não inventa o território: abre uma porta para o escutar.'
  };
  ticket.querySelectorAll('[data-action]').forEach((button) => button.addEventListener('click', () => {
    response.textContent = replies[button.dataset.action];
  }));

  const panel = document.querySelector('#panel');
  const panelBody = document.querySelector('#panelBody');
  const panels = {
    cronicas: `<p class="status">portal curatorial</p><h2>Crónicas Cãotadas por Fucô</h2><p>Fucô fareja histórias, pequenos desvios, memórias e vozes dos lugares. O conteúdo público só aparece depois de identificado, contextualizado e validado.</p><ul><li>memória colectiva sem apagar a autoria</li><li>relação com freguesia, concelho e fontes</li><li>revisão humana antes da publicação</li></ul>`,
    galeria: `<p class="status">portal curatorial</p><h2>Galeria Diletante</h2><p>Um espaço para imagens, expressões e leituras que não reduzem a arte a mercadoria. Cada peça mantém autoria, proveniência, licença e ligação territorial.</p><ul><li>originais preservados</li><li>derivados identificados como derivados</li><li>acessibilidade e direitos verificados</li></ul>`,
    contribuir: `<p class="status">porta de contribuição</p><h2>Deixar uma palavra no Atlas</h2><p>Nuno é a porta pública para palavra, som, fotografia, desenho e memória. A recepção segura será activada quando o backend de consentimento, retirada, idade mínima e revisão humana estiver operacional.</p><p><strong>Nenhum dado está a ser recolhido nesta versão pública.</strong></p>`
  };
  document.querySelectorAll('[data-panel]').forEach((button) => button.addEventListener('click', () => {
    panelBody.innerHTML = panels[button.dataset.panel];
    panel.showModal();
  }));
  panel.querySelector('.close').addEventListener('click', () => panel.close());
  panel.addEventListener('click', (event) => { if (event.target === panel) panel.close(); });

  const sound = document.querySelector('#soundToggle');
  sound.addEventListener('click', () => {
    const next = sound.getAttribute('aria-pressed') !== 'true';
    sound.setAttribute('aria-pressed', String(next));
    sound.textContent = `som: ${next ? 'preparado' : 'desligado'}`;
    if (next) setTimeout(() => { sound.textContent = 'som: sem faixa publicada'; }, 900);
  });
})();
