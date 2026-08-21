const deck = document.querySelector('#dinamicas');
const dialog = document.querySelector('#engine');
const body = document.querySelector('#engineBody');
const known = new Set([
  'inventario-meu-mundo','catastrofe-produtiva','ponto-kusama','corpo-percebe',
  'escutar-silencio','rizoma-interior','cubo-interior'
]);
const memory = new Map();
let catalogue = [];

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderCatalogue(entries) {
  const portal = el('nav', 'catalogue-nav');
  portal.setAttribute('aria-label', 'Escolher família');
  const families = ['todas', ...new Set(entries.map(item => item.familia))];
  families.forEach(name => {
    const button = el('button', 'filter', name);
    button.type = 'button';
    button.dataset.family = name;
    button.setAttribute('aria-pressed', name === 'todas' ? 'true' : 'false');
    portal.append(button);
  });
  deck.before(portal);

  entries.filter(item => !known.has(item.id)).forEach(item => {
    const card = el('article', 'card dynamic-card');
    card.dataset.family = item.familia;
    card.dataset.curadoria = item.id;
    card.dataset.n = String(item.ordem).padStart(2, '0');
    card.append(el('span', 'tag', item.familia));
    card.append(el('h2', '', item.nome));
    card.append(el('p', '', item.convite));
    const button = el('button', 'open', 'brincar');
    button.type = 'button';
    button.dataset.curadoria = item.id;
    card.append(button);
    deck.append(card);
  });

  portal.addEventListener('click', event => {
    const button = event.target.closest('[data-family]');
    if (!button) return;
    portal.querySelectorAll('[data-family]').forEach(item =>
      item.setAttribute('aria-pressed', String(item === button)));
    const family = button.dataset.family;
    deck.querySelectorAll('.dynamic-card').forEach(card => {
      card.hidden = family !== 'todas' && card.dataset.family !== family;
    });
  });
}

function shuffle(values) {
  const copy = [...values];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

function openDynamic(item) {
  const related = catalogue.filter(candidate =>
    candidate.familia === item.familia && candidate.id !== item.id);
  const state = memory.get(item.id) || { turns: 0, traces: [] };
  memory.set(item.id, state);

  body.replaceChildren();
  const section = el('section', 'engine dynamic-engine');
  section.append(el('span', 'tag', item.familia));
  section.append(el('h2', '', item.nome));
  section.append(el('p', 'invitation', item.convite));

  const field = el('div', 'play-field');
  const pulse = el('button', 'play-pulse', item.mecanica);
  pulse.type = 'button';
  pulse.setAttribute('aria-label', item.convite);
  field.append(pulse);
  const result = el('p', 'result', 'toca para começar');
  field.append(result);

  const traceLabel = el('label', '', 'deixa um vestígio neste aparelho');
  const trace = el('textarea');
  trace.maxLength = 280;
  trace.placeholder = 'uma palavra, um som escrito, um desvio…';
  traceLabel.append(trace);

  const tools = el('div', 'toolbar');
  const keep = el('button', 'action', 'guardar aqui');
  keep.type = 'button';
  const cross = el('button', 'action', 'cruzar');
  cross.type = 'button';
  tools.append(keep, cross);

  pulse.addEventListener('click', () => {
    state.turns += 1;
    const gestures = shuffle([
      item.convite,
      `${item.mecanica}: faz de novo, mas mais pequeno.`,
      `${item.mecanica}: troca o princípio pelo fim.`,
      `${item.mecanica}: entrega uma parte ao acaso.`
    ]);
    result.textContent = gestures[state.turns % gestures.length];
    pulse.style.setProperty('--turn', String(state.turns));
  });

  keep.addEventListener('click', () => {
    const value = trace.value.trim();
    if (value) {
      state.traces.push(value);
      trace.value = '';
      result.textContent = `ficou aqui · ${state.traces.length}`;
    }
  });

  cross.addEventListener('click', () => {
    if (!related.length) return;
    const other = related[Math.floor(Math.random() * related.length)];
    result.textContent = `${item.nome} ↔ ${other.nome}\n${other.convite}`;
  });

  section.append(field, traceLabel, tools);
  body.append(section);
  dialog.showModal();
}

deck.addEventListener('click', event => {
  const button = event.target.closest('[data-curadoria]');
  if (!button) return;
  const item = catalogue.find(candidate => candidate.id === button.dataset.curadoria);
  if (item) openDynamic(item);
});

fetch('catalogo-curatorial.json', { cache: 'no-store' })
  .then(response => {
    if (!response.ok) throw new Error('catálogo indisponível');
    return response.json();
  })
  .then(data => {
    catalogue = data.entradas;
    renderCatalogue(catalogue);
    document.documentElement.dataset.catalogue = 'ready';
  })
  .catch(() => {
    document.documentElement.dataset.catalogue = 'fallback';
  });
