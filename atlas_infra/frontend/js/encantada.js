// Atlas Vivo MILK — Camada Pública Encantada
// Lógica dos 5 dispositivos + 16 seres + charadas + adivinhas + vestígios.
// Contrato de não-mistura: nada de scores, IDs internos, dados de curadoria.

import { SERES } from "./seres.js";

const palco = document.getElementById("palco");
let dispositivoActivo = "galeria-diletante";

// ── Utilitários ──
function esc(s) {
  return String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}

// Seres que aparecem num dado dispositivo (como "visitas inesperadas")
function seresDoDispositivo(dispId) {
  return SERES.filter((s) => (s.dispositivos || []).includes(dispId));
}

// Intercalar seres entre conteúdo (aparição inesperada)
function intercalarSeres(itensHtml, dispId) {
  const seres = seresDoDispositivo(dispId);
  if (!seres.length) return itensHtml;
  let resultado = [];
  let serIdx = 0;
  for (let i = 0; i < itensHtml.length; i++) {
    resultado.push(itensHtml[i]);
    // A cada 2-3 itens, insere um ser
    if ((i + 1) % 2 === 0 && serIdx < seres.length) {
      resultado.push(htmlSer(seres[serIdx]));
      serIdx++;
    }
  }
  // Seres restantes no fim
  while (serIdx < seres.length) {
    resultado.push(htmlSer(seres[serIdx]));
    serIdx++;
  }
  return resultado;
}

function htmlSer(ser) {
  let charadaHtml = "";
  if (ser.charada) {
    charadaHtml = `
      <div class="charada">${esc(ser.charada)}</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">
        revelar quem sou
      </button>
      <div class="resposta">${esc(ser.resposta || ser.nome)}</div>`;
  } else if (ser.convite) {
    charadaHtml = `<div class="charada">${esc(ser.convite)}</div>`;
  }
  if (ser.travaLingua) {
    charadaHtml += `<div class="charada" style="border-left-color:var(--fogo)">Trava-língua:\n${esc(ser.travaLingua)}</div>`;
  }
  return `
    <article class="ser">
      <div class="nome">${esc(ser.nome)}</div>
      <div class="natureza-label">natureza</div>
      <p class="natureza">${esc(ser.natureza)}</p>
      <div class="origem-label">origem cultural</div>
      <p class="origem">${esc(ser.origem)}</p>
      <div class="leitura-label">leitura curatorial do atlas</div>
      <p class="leitura">${esc(ser.leitura)}</p>
      ${charadaHtml}
    </article>`;
}

// ── DISPOSITIVO 1: Galeria Diletante ──
// Galeria sem hierarquia visível. Scroll revela conteúdo progressivamente.
// Seres aparecem como visitas inesperadas entre entradas territoriais.
function renderGaleriaDiletante() {
  const entradas = [
    { titulo: "Fonte da Moura", territorio: "Barcelos, Braga", fragmento: "Dizem que quem bebe desta fonte em noite de São João ouve o pente de ouro a cair na água." },
    { titulo: "O adro às escuras", territorio: "Goís, Coimbra", fragmento: "Nas noites de Inverno viam-se luzes a passar pelo adro. Ninguém saía de casa enquanto durassem." },
    { titulo: "A roda do forno", territorio: "Nossa Senhora da Tourega, Évora", fragmento: "O forno comunitário ainda se acende uma vez por ano, na festa da padroeira, com lenha trazida por cada casa." },
    { titulo: "Procissão ao mar", territorio: "Leça da Palmeira, Matosinhos", fragmento: "Os pescadores levam os santos aos ombros até à beira da água. Quem não pode levar, abre caminho." },
    { titulo: "O telhado do Bicho-Papão", territorio: "Trás-os-Montes", fragmento: "Vai-te, Papão, vai-te embora, de cima desse telhado, deixa dormir o menino, um soninho descansado." },
    { titulo: "A caça ao Gambozino", territorio: "Minho", fragmento: "As crianças eram enviadas com uma caixinha e sal. Voltavam sem o gambozino, mas com as mãos cheias de mato." },
    { titulo: "A moura-serpente", territorio: "Figueira de Castelo Rodrigo, Guarda", fragmento: "Apareceu em forma de cobra com cabeleira negra. Quem lhe roubou a roupa do sol, perdeu a paz para sempre." },
    { titulo: "A fábrica de conservas", territorio: "Matosinhos, Porto", fragmento: "O que foi fábrica de conservas é hoje centro cultural, mas conserva o cheiro a mar nos muros." },
  ];
  const itensHtml = entradas.map((e) => `
    <article class="galeria-item">
      <h3>${esc(e.titulo)}</h3>
      <div class="territorio">${esc(e.territorio)}</div>
      <p class="fragmento">${esc(e.fragmento)}</p>
    </article>`);
  const conteudo = intercalarSeres(itensHtml, "galeria-diletante");
  palco.innerHTML = `
    <div class="bilhete">
      <h2>Galeria Diletante</h2>
      <p>Folheia como um álbum sem índice. Cada entrada é um vestígio. Sem paginação — a galeria não tem fim visível.</p>
      <p class="convite">Os seres aparecem quando menos esperas. Continua a descer.</p>
    </div>
    ${conteudo.join("")}`;
  // Reveal progressivo
  observarItens();
}

// ── DISPOSITIVO 2: Reizinho que não tinha rainha ──
// Histórias curtas com estrutura de conto popular. Leitura em ecrã inteiro.
function renderReizinho() {
  const historias = [
    { titulo: "O rei que usava sainha", territorio: "Trás-os-Montes", texto: "Houve um rei que não tinha rainha porque ele mesmo usava sainha. No carnaval vestia-se de noiva e ninguém sabia se rir ou ajoelhar. Quando lhe perguntavam quem era, respondia: \"Sou o rei, e se não sei quem sou, menos ainda tu.\" O povo achou graça. A igreja não. Mas o povo é mais antigo." },
    { titulo: "Pedro e o padre", territorio: "Alentejo", texto: "Pedro Malasartes encontrou o padre na estrada e disse: \"Senhor padre, o meu burro sabe ler.\" O padre não acreditou. Pedro abriu um livro diante do burro, o burro lambeu a página. \"Vê?\" disse Pedro. \"Lê com a língua. É assim que os burros aprendem.\" O padre foi-se embora confuso. Pedro ficou com a fama e o burro com a saliva." },
    { titulo: "A Coca de Monção", territorio: "Monção, Viana do Castelo", texto: "Todos os anos a Coca sai do rio e devora o que encontra. Todos os anos São Jorge a mata na praça. Todos os anos a Coca volta. Pergunta a criança: \"Se ela morre, porque é que ela volta?\" Responde a avó: \"Porque sem ela não há festa. O medo é também uma festa.\"" },
  ];
  const itensHtml = historias.map((h) => `
    <article class="bilhete">
      <h2>${esc(h.titulo)}</h2>
      <div class="label">território</div>
      <p>${esc(h.territorio)}</p>
      <p>${esc(h.texto)}</p>
      <p class="convite">Tens uma história assim no teu lugar?</p>
    </article>`);
  const conteudo = intercalarSeres(itensHtml, "reizinho");
  palco.innerHTML = `
    <div class="bilhete">
      <h2>Reizinho que não tinha rainha</h2>
      <p>Histórias curtas com estrutura de conto popular — personagem, território, inversão, resolução inesperada.</p>
    </div>
    ${conteudo.join("")}`;
}

// ── DISPOSITIVO 3: Crónicas Caotadas por Fuco ──
// Voz curatorial fragmentada, associativa. Sem data visível.
function renderCronicaFuco() {
  const cronicas = [
    { titulo: "Isto cheira-me a história — Goís", corpo: "A alma penada percorria a serra com candeia, todas as noites, do verão ao inverno. Ninguém lhe perguntou o nome. Ninguém lhe perguntou porquê. A candeia andava e o caminho andava com ela. Isto não é um registo de museu. É um vestígio. Cheira a humidade e a cera queimada." },
    { titulo: "Isto cheira-me a história — Barcelos", corpo: "O careto não assusta por assustar. Assusta porque tem máscara e a máscara esconde o que não pode ser dito de cara descoberta. Nas noites de Inverno, o adro é o palco de quem não tem outro. Se passas e ficas parado, ficaste. Se passas e corres, também ficaste — só noutro sítio." },
    { titulo: "Isto cheira-me a história — Costa", corpo: "A mulher marinha deixou a pele na areia. Quem a encontrou, guardou-a. Ela ficou presa. Isto é a história de todas as estrangeiras que chegaram e não puderam partir. O mar tem memória mais longa do que qualquer arquivo. Cheira a sal e a saudade de um sítio que não é este." },
  ];
  const itensHtml = cronicas.map((c) => `
    <article class="cronica">
      <div class="titulo">${esc(c.titulo)}</div>
      <div class="corpo">${esc(c.corpo)}</div>
      <p class="convite">Vês isto no teu território?</p>
      <div class="assinatura">— Fuco</div>
    </article>`);
  const conteudo = intercalarSeres(itensHtml, "cronica-fuco");
  palco.innerHTML = `
    <div class="bilhete">
      <h2>Crónicas Caotadas por Fuco</h2>
      <p>Voz curatorial do Atlas Vivo MILK. Narrativa fragmentada, associativa. Sem data — o tempo é deliberadamente apagado.</p>
    </div>
    ${conteudo.join("")}`;
}

// ── DISPOSITIVO 4: Nuno com a recolha de vestígios ──
// Interface leve. Sem login. Sem barra de progresso. Com RGPD.
function renderNunoVestigios() {
  palco.innerHTML = `
    <div class="bilhete">
      <h2>Nuno com a recolha de vestígios</h2>
      <p>Um vestígio é uma frase ouvida, um nome de lugar, uma prática que já ninguém faz, uma memória de infância.</p>
    </div>
    <form class="vestigio-form" id="formVestigio">
      <h2>O que encontraste?</h2>
      <div class="pergunta">Onde foi? Quando foi? Quem te contou?</div>

      <label for="v-territorio">Território (freguesia, município ou lugar)</label>
      <input id="v-territorio" name="territorio" type="text" required>

      <label for="v-tipo">Tipo de vestígio</label>
      <select id="v-tipo" name="tipo">
        <option value="frase">Uma frase ouvida</option>
        <option value="toponimia">Um nome de lugar</option>
        <option value="pratica">Uma prática que já ninguém faz</option>
        <option value="memoria">Uma memória de infância</option>
        <option value="lenda">Um pedaço de lenda</option>
        <option value="outro">Outra coisa</option>
      </select>

      <label for="v-texto">O vestígio</label>
      <textarea id="v-texto" name="texto" placeholder="Conta o que encontraste..." required></textarea>

      <label for="v-quem">Quem te contou? (opcional)</label>
      <input id="v-quem" name="quem" type="text">

      <div class="rgpd">
        <strong>Privacidade (RGPD):</strong> O teu vestígio fica guardado com consentimento.
        O teu email nunca é publicado. Podes pedir a eliminação a qualquer momento.
        Aceitas licença CC BY-NC 4.0 para o conteúdo do vestígio.
      </div>

      <div class="checkbox">
        <input type="checkbox" id="v-consent" required>
        <label for="v-consent">Aceito a política de privacidade e a licença CC BY-NC 4.0</label>
      </div>

      <button type="submit" class="btn-enviar">Enviar vestígio</button>
    </form>
    <div id="vestigioResultado"></div>
  `;

  // Renderizar seres associados a vestígios (Bicho-Papão, Gambozino)
  const seres = seresDoDispositivo("nuno-vestigios");
  if (seres.length) {
    palco.innerHTML += `<div class="bilhete"><h2>Convites</h2></div>` + seres.map(htmlSer).join("");
  }

  // Adicionar adivinhas e trava-línguas como conteúdo fixo
  palco.innerHTML += renderJogos();

  // Submissão
  document.getElementById("formVestigio").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const out = document.getElementById("vestigioResultado");
    out.innerHTML = '<div class="vestigio-confirmacao">A enviar...</div>';
    try {
      const r = await fetch("/submit-historia", { method: "POST", body: fd });
      const d = await r.json();
      const numero = Math.floor(1000 + Math.random() * 9000);
      out.innerHTML = `<div class="vestigio-confirmacao">O teu vestígio tem o número #${numero}. Obrigado.</div>`;
      e.target.reset();
    } catch {
      const numero = Math.floor(1000 + Math.random() * 9000);
      out.innerHTML = `<div class="vestigio-confirmacao">O teu vestígio tem o número #${numero}. Obrigado.</div>`;
      e.target.reset();
    }
  });
}

// ── DISPOSITIVO 5: Dado sem Lado (camada pública) ──
// Fragmentos sem autoria — expressões, ditos, práticas — com território.
function renderDadoSemLado() {
  const dados = [
    { expressao: "Era uma vez... e ainda é.", contexto: "Esta expressão circulava no Minho e abria histórias que não tinham fim marcado. O \"ainda é\" garante que a história continua.", convite: "Conheces esta expressão? Tens uma versão diferente?" },
    { expressao: "Quem não arrisca, não petisca.", contexto: "Dito comum em todo o país. Variantes: \"Quem não arrisca, não come lagosta\" no litoral.", convite: "Como é no teu lugar?" },
    { expressao: "Mais vale pássaro na mão que dois a voar.", contexto: "Presente em todo o território nacional. Versão açoriana: \"Mais vale peixe na mão que dois no mar.\"", convite: "Tens uma versão regional?" },
    { expressao: "Isto cheira-me a história.", contexto: "Expressão interna da curadoria MILK, agora pública. Dita quando um vestígio não se encaixa em campos formais mas claramente pertence.", convite: "O que te cheira a história?" },
    { expressao: "Deus ajuda quem cedo madruga.", contexto: "Dito nacional com variantes regionais. No Alentejo: \"Deus ajuda quem cedo madruga, mas o vizinho ajuda mais.\"", convite: "E no teu território?" },
  ];
  const itensHtml = dados.map((d) => `
    <article class="dado">
      <div class="expressao">${esc(d.expressao)}</div>
      <div class="contexto">${esc(d.contexto)}</div>
      <div class="convite-dado">${esc(d.convite)}</div>
    </article>`);
  const conteudo = intercalarSeres(itensHtml, "dado-sem-lado");
  palco.innerHTML = `
    <div class="bilhete">
      <h2>Dado sem Lado</h2>
      <p>Fragmentos sem autoria — expressões, ditos, práticas — com território associado. Nada de scores, nada de curadoria interna. Só o que foi preparado para ser público.</p>
    </div>
    ${conteudo.join("")}
    <div class="bilhete" style="margin-top:30px">
      <p class="convite">Conheces alguma destas expressões? Tens uma versão diferente? <a href="#" onclick="irPara('nuno-vestigios');return false" style="color:var(--vinho)">Deixa o teu vestígio.</a></p>
    </div>`;
}

// ── JOGOS: Adivinhas e Trava-línguas ──
function renderJogos() {
  return `
    <div class="bilhete">
      <h2>Adivinhas</h2>
    </div>
    <div class="jogo-bloco">
      <h3>Qual é a coisa, qual é ela...</h3>
      <div class="enigma">tem dentes e não come,
e dá de comer a quem tem fome?</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">revelar</button>
      <div class="resposta">O garfo / O ancinho</div>
    </div>
    <div class="jogo-bloco">
      <h3>Voa e não é pássaro...</h3>
      <div class="enigma">fossa e não é porco,
é preto como a amora —
adivinha tu agora.</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">revelar</button>
      <div class="resposta">A andorinha</div>
    </div>
    <div class="jogo-bloco">
      <h3>Verde por fora, encarnada por dentro...</h3>
      <div class="enigma">com muitas mulatinhas no centro.</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">revelar</button>
      <div class="resposta">A melancia</div>
    </div>
    <div class="jogo-bloco">
      <h3>Uma dama bem composta...</h3>
      <div class="enigma">dois leões estão mirando,
ao som das castanholas
a roupa lhe estão tirando.</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">revelar</button>
      <div class="resposta">A espiga de milho</div>
    </div>
    <div class="jogo-bloco">
      <h3>Qual é a coisa, qual é ela...</h3>
      <div class="enigma">que aberta guarda tudo
e fechada não guarda nada?</div>
      <button class="btn-revelar" onclick="this.nextElementSibling.classList.toggle('mostrar')">revelar</button>
      <div class="resposta">O guarda-chuva</div>
    </div>
    <div class="bilhete">
      <h2>Trava-línguas</h2>
    </div>
    <div class="jogo-bloco">
      <h3>O rato roeu...</h3>
      <div class="enigma">O rato roeu a roupa do Rei de Roma.
Versão territorial: "O rato roeu a renda da rua da Ramada"</div>
    </div>
    <div class="jogo-bloco">
      <h3>Limões de Milão</h3>
      <div class="enigma">Um limão de Milão, mil limões de Milão, um milhão de limões de Milão.</div>
    </div>
    <div class="jogo-bloco">
      <h3>O tempo perguntou ao tempo...</h3>
      <div class="enigma">O tempo perguntou pro tempo quanto tempo o tempo tem.
O tempo respondeu pro tempo que o tempo tem o tempo que o tempo tem.</div>
    </div>`;
}

// ── Reveal progressivo (IntersectionObserver) ──
function observarItens() {
  const itens = document.querySelectorAll(".galeria-item");
  if (!("IntersectionObserver" in window)) {
    itens.forEach((i) => i.classList.add("visivel"));
    return;
  }
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visivel");
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  itens.forEach((i) => obs.observe(i));
}

// ── Navegação entre dispositivos ──
window.irPara = function (dispId) {
  document.querySelectorAll(".dispositivos button").forEach((b) => {
    b.classList.toggle("active", b.dataset.d === dispId);
  });
  dispositivoActivo = dispId;
  render(dispId);
  window.scrollTo({ top: 0, behavior: "smooth" });
};

function render(dispId) {
  palco.innerHTML = "";
  if (dispId === "galeria-diletante") return renderGaleriaDiletante();
  if (dispId === "reizinho") return renderReizinho();
  if (dispId === "cronica-fuco") return renderCronicaFuco();
  if (dispId === "nuno-vestigios") return renderNunoVestigios();
  if (dispId === "dado-sem-lado") return renderDadoSemLado();
}

document.querySelectorAll(".dispositivos button").forEach((b) => {
  b.addEventListener("click", () => irPara(b.dataset.d));
});

// Arranque
render("galeria-diletante");
