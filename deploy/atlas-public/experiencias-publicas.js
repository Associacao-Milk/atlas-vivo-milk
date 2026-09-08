const deck = document.querySelector('#dinamicas');
const dialog = document.querySelector('#engine');
const body = document.querySelector('#engineBody');
const ticket = document.querySelector('#ticket');

if (!deck || !dialog || !body) throw new Error('ATLAS_EXPERIENCE_MOUNT_MISSING');

const registries = [...document.querySelectorAll('.public-runtime-registry')];
let territoryReady = registries.length === 0;
registries.forEach((registry) => {
  registry.hidden = true;
  registry.setAttribute('aria-hidden', 'true');
});

window.addEventListener('atlas:validated-territories-ready', () => {
  territoryReady = true;
  registries.forEach((registry) => {
    registry.hidden = false;
    registry.setAttribute('aria-hidden', 'false');
  });
  openRoute();
}, { once: true });

const EXPERIENCE_NAMES = [
  ['pedras', 'PEDRAS QUE CONTAM'],
  ['paredes', 'PAREDES QUE ESCUTAM'],
  ['planta', 'PLANTA IMPOSSÍVEL'],
  ['carta', 'CARTA PARA CASA NENHUMA'],
  ['janelas', 'JANELAS PARA O QUE FALTA'],
  ['batimetria', 'BATIMETRIA'],
  ['eco', 'ECO DO ENCONTRO'],
  ['dado', 'DADO 100LADO'],
];

const WORDS = [
  'estou aqui', 'uma saudade', 'eu ri', 'vem me reencontrar',
  'um abraço', 'juntos sempre', 'somos todos possíveis',
];

const style = document.createElement('style');
style.textContent = `
  .experience-constellation{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:.7rem;padding:clamp(1rem,3vw,2.5rem)}
  .experience-constellation[hidden]{display:none!important}
  .experience-door{min-height:8rem;border:1px solid #4d4d4d;background:#000;color:#f5f5f0;font:600 .78rem/1.25 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.09em;text-transform:uppercase;cursor:pointer;transition:background .25s,color .25s,transform .25s;text-decoration:none;display:grid;place-items:center;text-align:center}
  .experience-door:hover,.experience-door:focus-visible{background:#f3d35a;color:#000;transform:translateY(-2px);outline:2px solid #fff;outline-offset:3px}
  #engine.atlas-experience{width:min(100vw,1100px);height:min(100dvh,820px);max-width:none;max-height:none;padding:0;border:0;background:#000;color:#fff;overflow:hidden}
  #engine.atlas-experience::backdrop{background:#000}
  #engine.atlas-experience>.close{position:fixed;z-index:20;top:max(1rem,env(safe-area-inset-top));right:max(1rem,env(safe-area-inset-right));width:3rem;height:3rem;border:1px solid #777;border-radius:50%;background:#000;color:#fff;font-size:1.5rem;cursor:pointer}
  .experience-stage{position:relative;width:100%;height:100%;min-height:32rem;overflow:hidden;background:#000;touch-action:none;isolation:isolate}
  .experience-name{position:absolute;z-index:10;left:clamp(1rem,4vw,3rem);top:clamp(1rem,4vw,3rem);margin:0;max-width:70%;font:600 clamp(.72rem,1.7vw,1rem)/1.2 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.12em;color:#eee}
  .experience-word{position:absolute;z-index:6;color:#fff;font:500 clamp(.7rem,2vw,1.1rem)/1 ui-monospace,SFMono-Regular,Consolas,monospace;pointer-events:none;mix-blend-mode:difference;animation:word-breathe 5s ease-in-out infinite}
  .experience-input{position:absolute;z-index:12;left:50%;bottom:clamp(1.5rem,5vw,4rem);transform:translateX(-50%);width:min(78%,36rem);padding:.8rem .2rem;border:0;border-bottom:1px solid #aaa;background:transparent;color:#fff;font:400 1rem ui-monospace,SFMono-Regular,Consolas,monospace;text-align:center;outline:none}
  .experience-input:focus{border-color:#f3d35a}
  .experience-action{position:absolute;z-index:12;right:clamp(1rem,4vw,3rem);bottom:clamp(1rem,4vw,3rem);border:1px solid #888;background:#000;color:#fff;padding:.75rem 1rem;font:600 .72rem ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.08em;cursor:pointer}
  .experience-action:focus-visible{outline:2px solid #f3d35a;outline-offset:3px}
  @keyframes word-breathe{0%,100%{opacity:.2;filter:blur(2px)}50%{opacity:.9;filter:blur(0)}}
  @media (prefers-reduced-motion:reduce){.experience-word,.experience-door{animation:none!important;transition:none!important}}
`;
document.head.appendChild(style);

deck.classList.add('experience-constellation');
const doors = EXPERIENCE_NAMES.map(([id, name]) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'experience-door';
  button.dataset.experience = id;
  button.textContent = name;
  return button;
});
const cloud = document.createElement('a');
cloud.className = 'experience-door';
cloud.href = 'https://associacaomilk.pt/nextcloud/';
cloud.target = '_blank';
cloud.rel = 'noopener noreferrer';
cloud.textContent = 'NUVEM';
cloud.setAttribute('aria-label', 'Abrir Nuvem MILK');
deck.replaceChildren(...doors, cloud);

function stage(name) {
  const el = document.createElement('section');
  el.className = 'experience-stage';
  el.setAttribute('aria-label', name);
  const title = document.createElement('h2');
  title.className = 'experience-name';
  title.textContent = name;
  el.appendChild(title);
  return el;
}

function canvasFor(el) {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'button');
  canvas.setAttribute('aria-label', `${el.getAttribute('aria-label')}: tocar no centro`);
  el.appendChild(canvas);
  const resize = () => {
    const ratio = Math.min(devicePixelRatio || 1, 2);
    const rect = el.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    canvas.height = Math.max(1, Math.floor(rect.height * ratio));
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  };
  resize();
  const observer = new ResizeObserver(resize);
  observer.observe(el);
  canvas.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const options = { bubbles: true, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 };
    canvas.dispatchEvent(new PointerEvent('pointerdown', options));
    canvas.dispatchEvent(new PointerEvent('pointerup', options));
  });
  el.addEventListener('atlas:destroy', () => observer.disconnect(), { once: true });
  return { canvas, context, observer };
}

function point(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
}

function inputFor(el, placeholder = '...') {
  const input = document.createElement('input');
  input.className = 'experience-input';
  input.type = 'text';
  input.maxLength = 160;
  input.autocomplete = 'off';
  input.placeholder = placeholder;
  el.appendChild(input);
  return input;
}

function whisper(el, text, x, y) {
  const word = document.createElement('span');
  word.className = 'experience-word';
  word.textContent = text;
  word.style.left = `${Math.max(4, Math.min(86, x))}%`;
  word.style.top = `${Math.max(8, Math.min(86, y))}%`;
  el.appendChild(word);
  setTimeout(() => word.remove(), 9000);
}

function stones() {
  const el = stage('PEDRAS QUE CONTAM');
  const { canvas, context } = canvasFor(el);
  const drawStone = (x, y, size, hue) => {
    context.save();
    context.translate(x, y);
    context.rotate((x + y) * .001);
    context.beginPath();
    for (let i = 0; i < 12; i += 1) {
      const angle = i / 12 * Math.PI * 2;
      const radius = size * (.72 + Math.sin(i * 4.7) * .12);
      const px = Math.cos(angle) * radius;
      const py = Math.sin(angle) * radius * .66;
      if (!i) context.moveTo(px, py); else context.lineTo(px, py);
    }
    context.closePath();
    context.fillStyle = `hsl(${hue} 8% 24%)`;
    context.strokeStyle = '#d7d0bf';
    context.lineWidth = 1;
    context.fill();
    context.stroke();
    context.restore();
  };
  for (let i = 0; i < 22; i += 1) drawStone(30 + Math.random() * 900, 100 + Math.random() * 550, 18 + Math.random() * 42, 25 + Math.random() * 25);
  const input = inputFor(el, 'a pedra fala...');
  canvas.addEventListener('pointerdown', event => {
    const p = point(canvas, event);
    drawStone(p.x, p.y, 36 + Math.random() * 34, 36);
    whisper(el, input.value.trim() || WORDS[Math.floor(Math.random() * WORDS.length)], p.x / canvas.clientWidth * 100, p.y / canvas.clientHeight * 100);
    input.value = '';
  });
  return el;
}

function walls() {
  const el = stage('PAREDES QUE ESCUTAM');
  const { canvas, context } = canvasFor(el);
  const input = inputFor(el, 'deixa um rumor...');
  context.fillStyle = '#111';
  context.fillRect(0, 0, 1200, 900);
  let active = false;
  canvas.addEventListener('pointerdown', event => {
    active = true;
    const p = point(canvas, event);
    context.beginPath();
    context.moveTo(p.x, p.y);
  });
  canvas.addEventListener('pointermove', event => {
    if (!active) return;
    const p = point(canvas, event);
    context.strokeStyle = `hsla(${330 + p.x % 30} 70% 72% / .55)`;
    context.lineWidth = 1 + Math.abs(event.movementX || 1) * .2;
    context.lineTo(p.x, p.y);
    context.stroke();
  });
  const stop = event => {
    if (!active) return;
    active = false;
    const p = point(canvas, event);
    whisper(el, input.value.trim() || WORDS[Math.floor(Math.random() * WORDS.length)], p.x / canvas.clientWidth * 100, p.y / canvas.clientHeight * 100);
    input.value = '';
  };
  canvas.addEventListener('pointerup', stop);
  canvas.addEventListener('pointercancel', () => { active = false; });
  return el;
}

function impossiblePlan() {
  const el = stage('PLANTA IMPOSSÍVEL');
  const { canvas, context } = canvasFor(el);
  const points = [];
  canvas.addEventListener('pointerdown', event => {
    const p = point(canvas, event);
    points.push(p);
    context.strokeStyle = points.length % 3 ? '#f4f0e8' : '#ff4fa3';
    context.lineWidth = 2;
    if (points.length === 1) context.beginPath();
    if (points.length > 1) {
      const previous = points[points.length - 2];
      context.beginPath();
      context.moveTo(previous.x, previous.y);
      context.lineTo(p.x, previous.y);
      context.lineTo(p.x, p.y);
      context.stroke();
    }
    if (points.length % 4 === 0) {
      context.beginPath();
      context.arc(p.x, p.y, 14, 0, Math.PI * 1.5);
      context.stroke();
    }
  });
  return el;
}

function letter() {
  const el = stage('CARTA PARA CASA NENHUMA');
  const input = inputFor(el, 'escreve sem endereço...');
  const fold = document.createElement('button');
  fold.type = 'button';
  fold.className = 'experience-action';
  fold.textContent = 'DOBRAR';
  el.appendChild(fold);
  const paper = document.createElement('div');
  paper.style.cssText = 'position:absolute;left:50%;top:50%;width:min(64vw,34rem);aspect-ratio:1.6;transform:translate(-50%,-50%);border:1px solid #ded8cc;background:#f4efe4;clip-path:polygon(0 0,100% 0,100% 100%,0 100%);transition:clip-path 1.2s,transform 1.2s,opacity 1.2s;padding:2rem;box-sizing:border-box;color:#111;font:400 1rem/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;overflow:hidden';
  el.insertBefore(paper, input);
  input.addEventListener('input', () => {
    paper.textContent = input.value;
  });
  fold.addEventListener('click', () => {
    paper.style.clipPath = 'polygon(0 40%,50% 70%,100% 40%,100% 100%,0 100%)';
    paper.style.transform = 'translate(-50%,-35%) scale(.46) rotate(-7deg)';
    paper.style.opacity = '.18';
    input.value = '';
    input.disabled = true;
    fold.textContent = 'FICOU';
  });
  return el;
}

function windows() {
  const el = stage('JANELAS PARA O QUE FALTA');
  const colours = ['#ff4fa3', '#f3d35a', '#55d6be', '#6ca6ff', '#e8e8e8'];
  for (let i = 0; i < 11; i += 1) {
    const button = document.createElement('button');
    button.type = 'button';
    button.setAttribute('aria-label', `janela ${i + 1}`);
    button.style.cssText = `position:absolute;left:${8 + Math.random() * 75}%;top:${12 + Math.random() * 68}%;width:${50 + Math.random() * 95}px;height:${70 + Math.random() * 125}px;border:5px double #999;background:#050505;box-shadow:inset 0 0 0 2px #111;cursor:pointer;transition:transform .8s,background .8s`;
    button.addEventListener('click', () => {
      button.style.background = colours[i % colours.length];
      button.style.transform = `perspective(500px) rotateY(${i % 2 ? -64 : 64}deg)`;
      whisper(el, WORDS[i % WORDS.length], 10 + Math.random() * 72, 12 + Math.random() * 70);
    });
    el.appendChild(button);
  }
  return el;
}

function bathymetry() {
  const el = stage('BATIMETRIA');
  const { canvas, context } = canvasFor(el);
  const rings = [];
  canvas.addEventListener('pointermove', event => {
    const p = point(canvas, event);
    rings.push({ x: p.x, y: p.y, r: 1, life: 1 });
  });
  canvas.addEventListener('pointerdown', event => {
    const p = point(canvas, event);
    whisper(el, WORDS[Math.floor(Math.random() * WORDS.length)], p.x / canvas.clientWidth * 100, p.y / canvas.clientHeight * 100);
  });
  let frame;
  const draw = () => {
    context.fillStyle = 'rgba(0,0,0,.12)';
    context.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);
    for (const ring of rings) {
      ring.r += 1.6;
      ring.life *= .986;
      context.beginPath();
      context.arc(ring.x, ring.y, ring.r, 0, Math.PI * 2);
      context.strokeStyle = `rgba(95,170,255,${ring.life})`;
      context.lineWidth = Math.max(.4, ring.life * 2);
      context.stroke();
    }
    while (rings.length && rings[0].life < .02) rings.shift();
    frame = requestAnimationFrame(draw);
  };
  draw();
  el.addEventListener('atlas:destroy', () => cancelAnimationFrame(frame), { once: true });
  return el;
}

function echo() {
  const el = stage('ECO DO ENCONTRO');
  const { canvas, context } = canvasFor(el);
  const Audio = window.AudioContext || window.webkitAudioContext;
  let audio;
  canvas.addEventListener('pointerdown', event => {
    if (!Audio) return;
    const p = point(canvas, event);
    const frequency = 90 + p.x / Math.max(1, canvas.clientWidth) * 540;
    audio ||= new Audio();
    const now = audio.currentTime;
    [0, .16, .32].forEach((delay, index) => {
      const oscillator = audio.createOscillator();
      const gain = audio.createGain();
      oscillator.type = index === 1 ? 'triangle' : 'sine';
      oscillator.frequency.value = frequency * (1 + index * .008);
      gain.gain.setValueAtTime(.035 / (index + 1), now + delay);
      gain.gain.exponentialRampToValueAtTime(.0001, now + delay + .8);
      oscillator.connect(gain).connect(audio.destination);
      oscillator.start(now + delay);
      oscillator.stop(now + delay + .85);
    });
    context.beginPath();
    context.arc(p.x, p.y, 8, 0, Math.PI * 2);
    context.strokeStyle = '#f3d35a';
    context.lineWidth = 2;
    context.stroke();
    whisper(el, WORDS[Math.floor(Math.random() * WORDS.length)], p.x / canvas.clientWidth * 100, p.y / canvas.clientHeight * 100);
  });
  el.addEventListener('atlas:destroy', () => {
    if (audio && audio.state !== 'closed') audio.close();
  }, { once: true });
  return el;
}

function hundredSidedDie() {
  const el = stage('DADO 100LADO');
  const faces = [
    ['O INVENTÁRIO DO MEU MUNDO', 'pedras'],
    ['A CATÁSTROFE PRODUTIVA', 'paredes'],
    ['O PONTO DE KUSAMA', 'planta'],
    ['O CORPO QUE PERCEBE', 'batimetria'],
    ['ESCUTAR O SILÊNCIO', 'eco'],
    ['O RIZOMA INTERIOR', 'janelas'],
    ['O CUBO INTERIOR', 'carta'],
  ];
  const cube = document.createElement('button');
  cube.type = 'button';
  cube.setAttribute('aria-label', 'Lançar o Dado 100Lado');
  cube.style.cssText = 'position:absolute;left:50%;top:50%;width:min(42vw,15rem);aspect-ratio:1;transform:translate(-50%,-50%) rotateX(18deg) rotateY(28deg);border:1px solid #eee;background:#050505;color:#fff;font:700 clamp(2rem,8vw,5rem) ui-monospace,SFMono-Regular,Consolas,monospace;cursor:pointer;transition:transform 1.4s cubic-bezier(.2,.9,.2,1),border-radius 1.4s,background 1.4s;box-shadow:2rem 2rem 0 rgba(255,79,163,.13)';
  cube.textContent = '∞';
  let turns = 0;
  cube.addEventListener('click', () => {
    turns += 1;
    const [face, target] = faces[Math.floor(Math.random() * faces.length)];
    cube.style.transform = `translate(-50%,-50%) rotateX(${turns * 173}deg) rotateY(${turns * 257}deg) rotateZ(${turns * 61}deg)`;
    cube.style.borderRadius = turns % 2 ? '50%' : '0';
    cube.style.background = turns % 3 ? '#050505' : '#ff4fa3';
    const delay = matchMedia('(prefers-reduced-motion: reduce)').matches ? 80 : 760;
    setTimeout(() => whisper(el, face, 18 + Math.random() * 54, 18 + Math.random() * 58), delay);
    setTimeout(() => openExperience(target), delay + 920);
  });
  el.appendChild(cube);
  return el;
}

const makers = { pedras: stones, paredes: walls, planta: impossiblePlan, carta: letter, janelas: windows, batimetria: bathymetry, eco: echo, dado: hundredSidedDie };

function openExperience(id, { syncRoute = true } = {}) {
  const maker = makers[id];
  if (!maker) return;
  const previous = body.firstElementChild;
  if (previous) previous.dispatchEvent(new Event('atlas:destroy'));
  body.replaceChildren(maker());
  dialog.classList.add('atlas-experience');
  if (!dialog.open) dialog.showModal();
  if (syncRoute) history.pushState({ experience: id }, '', `#experiencia=${encodeURIComponent(id)}`);
}

function openRoute() {
  const id = new URLSearchParams(location.search).get('experiencia')
    || new URLSearchParams(location.hash.slice(1)).get('experiencia');
  if (id && makers[id]) openExperience(id, { syncRoute: false });
}

deck.addEventListener('click', event => {
  const button = event.target.closest('[data-experience]');
  if (button) openExperience(button.dataset.experience);
});

document.addEventListener('keydown', event => {
  if (dialog.open || /INPUT|TEXTAREA|SELECT/.test(event.target?.tagName || '')) return;
  const index = Number(event.key) - 1;
  if (index >= 0 && index < EXPERIENCE_NAMES.length) openExperience(EXPERIENCE_NAMES[index][0]);
});

dialog.addEventListener('close', () => {
  body.firstElementChild?.dispatchEvent(new Event('atlas:destroy'));
  body.replaceChildren();
  if (location.hash.startsWith('#experiencia=')) history.replaceState(null, '', `${location.pathname}${location.search}`);
});

window.addEventListener('hashchange', openRoute);
queueMicrotask(openRoute);

document.querySelector('[data-ticket-action="brincar"]')?.addEventListener('click', () => {
  const id = EXPERIENCE_NAMES[Math.floor(Math.random() * EXPERIENCE_NAMES.length)][0];
  setTimeout(() => {
    if (ticket?.open) ticket.close();
    openExperience(id);
  }, 360);
});
