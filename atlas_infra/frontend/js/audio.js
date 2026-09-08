// Gravação áudio via MediaRecorder (Bloco 3.1)
// WAV/MP3 no navegador, anexado ao FormData do formulário.

export function gravarAudio(container, form) {
  container.innerHTML = `
    <button type="button" class="btn" id="recBtn" aria-pressed="false">Gravar áudio</button>
    <span class="m" id="recTime" style="margin-left:10px"></span>
    <audio id="recPlay" controls style="display:none;margin-top:10px;width:100%"></audio>
  `;

  const btn = container.querySelector("#recBtn");
  const timeEl = container.querySelector("#recTime");
  const play = container.querySelector("#recPlay");
  let mediaRecorder = null;
  let chunks = [];
  let timer = null;
  let gravando = false;

  btn.addEventListener("click", async () => {
    if (gravando) {
      mediaRecorder?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];
      mediaRecorder.addEventListener("dataavailable", (e) => chunks.push(e.data));
      mediaRecorder.addEventListener("stop", () => {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        const url = URL.createObjectURL(blob);
        play.src = url;
        play.style.display = "block";
        // Anexar ao form como ficheiro
        const dt = new DataTransfer();
        dt.items.add(new File([blob], "gravacao.webm", { type: blob.type }));
        const fileInput = form.querySelector('input[type=file][name="audio"]');
        if (fileInput) fileInput.files = dt.files;
        stream.getTracks().forEach((t) => t.stop());
      });
      mediaRecorder.start();
      gravando = true;
      btn.textContent = "Parar";
      btn.setAttribute("aria-pressed", "true");
      let s = 0;
      timer = setInterval(() => { s++; timeEl.textContent = `${s}s`; }, 1000);
    } catch (e) {
      timeEl.textContent = "Microfone indisponível";
    }
  });

  function parar() {
    if (gravando && mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    gravando = false;
    btn.textContent = "Gravar áudio";
    btn.setAttribute("aria-pressed", "false");
    if (timer) clearInterval(timer);
  }
  mediaRecorder?.addEventListener?.("stop", parar);
}
