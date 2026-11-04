// Arayüz yalnız gösterir; bütün kurallar backend'de. Veri metinleri esc() ile kaçırılır.
const S = { ozet: null, liste: [], grup: "tum", asama: "", ara: "", sekme: "basvurular", detay: null, mesgul: false, dil: "tr" };
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const sayi = (v, k = 1) => (typeof v === "number" ? v.toLocaleString("tr-TR", { maximumFractionDigits: k }) : "—");

async function api(yol, secenek = {}) {
  const r = await fetch(yol, secenek);
  const govde = (r.headers.get("content-type") || "").includes("json") ? await r.json() : null;
  if (!r.ok) {
    const d = govde && govde.detail;
    throw new Error(typeof d === "string" ? d : d && d.mesaj ? `${d.mesaj} ${(d.hatalar || []).join(" · ")}` : `İstek başarısız (${r.status}).`);
  }
  return govde;
}

function bildir(metin, tur = "hata") {
  const el = $("bildirim");
  el.className = `fixed bottom-4 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg text-sm shadow-lg max-w-lg ${
    tur === "hata" ? "bg-rose-600 text-white" : "bg-murekkep text-white"}`;
  el.textContent = metin;
  clearTimeout(bildir.t);
  bildir.t = setTimeout(() => el.classList.add("hidden"), 4500);
}

const ROZET = {
  OLUMSUZ: "bg-rose-50 text-rose-700 ring-rose-200",
  KABUL: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  DEVAM_EDIYOR: "bg-sky-50 text-sky-700 ring-sky-200",
  "Taslağa uygun": "bg-slate-100 text-slate-800 ring-slate-300",
  "İK incelemesi": "bg-amber-50 text-amber-800 ring-amber-200",
  "Kapsam dışı": "bg-slate-100 text-slate-600 ring-slate-200",
  onay_bekliyor: "bg-sky-50 text-sky-700 ring-sky-200",
  onaylandi: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  onay_dustu: "bg-orange-50 text-orange-700 ring-orange-200",
  gecersiz: "bg-rose-50 text-rose-700 ring-rose-200",
  dikkat: "bg-amber-50 text-amber-800 ring-amber-200",
  sade: "bg-slate-100 text-slate-600 ring-slate-200",
};
const KARAR_ADI = { OLUMSUZ: "Olumsuz", KABUL: "Kabul", DEVAM_EDIYOR: "Devam ediyor" };
const rozet = (metin, anahtar) =>
  `<span class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${ROZET[anahtar] || ROZET.sade}">${esc(metin)}</span>`;

function taslakRozetleri(td) {
  if (!td) return "";
  return [rozet(td.ad, td.kod), rozet(td.kaynak, "sade"), td.ik_dikkat ? rozet("İK dikkat", "dikkat") : ""].join(" ");
}

// ---------- veri ----------
async function yenile() {
  S.ozet = await api("/api/ozet");
  if (S.ozet.yuklu) S.liste = await api("/api/basvurular");
  ciz();
  uretimiIzle();
}

async function dosyaYukle(dosya) {
  const fd = new FormData();
  fd.append("dosya", dosya);
  try {
    S.mesgul = true;
    $("yukle-etiket").textContent = "Yükleniyor…";
    await api("/api/yukle", { method: "POST", body: fd });
    bildir(`${dosya.name} yüklendi; sayılar ve listeler güncellendi.`, "bilgi");
    await yenile();
    if (S.detay) await detayAc(S.detay.basvuru_id);
  } catch (e) {
    bildir(e.message);
  } finally {
    S.mesgul = false;
    ciz();
  }
}

// ---------- özet ve sekmeler ----------
const DONEN = `<svg class="h-4 w-4 animate-spin text-gok" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="3" fill="none" opacity=".2"/><path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;
const TIK = `<svg class="h-4 w-4 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>`;

function ozetCiz() {
  const o = S.ozet, u = o.uretim || {};
  const parcalar = [
    { grup: "onaylandi", ad: "İK onaylı", n: o.onaylandi, dolgu: "bg-emerald-500", not: "güncel metin onaylandı" },
    { grup: "hazir", ad: "Taslağı hazır", n: Math.max(0, o.taslak_hazir - o.onaylandi), dolgu: "bg-murekkep", not: "tıklayınca açılır, İK okuyacak" },
    { grup: "islenmedi", ad: u.calisiyor ? "Hazırlanıyor" : "Taslağı yok", n: o.islenmedi,
      dolgu: `serit-hazirlaniyor ${u.calisiyor ? "akiyor" : ""}`, not: u.calisiyor ? "Muse yazıyor" : "henüz üretilmedi" },
    { grup: "ik", ad: "İK incelemesi", n: o.ik_incelemesi, dolgu: "bg-amber-400", not: "e-posta üretilmez" },
  ];
  const payda = Math.max(1, o.olumsuz);
  const yan = (ad, n, grup) => `<button data-grup="${grup}" class="text-left rounded-lg bg-slate-50 ring-1 ring-slate-200 px-3 py-1.5 hover:bg-slate-100">
      <span class="block text-[11px] text-slate-500">${ad}</span><span class="text-base font-semibold tabular-nums">${sayi(n, 0)}</span></button>`;
  const ilerleme = u.toplam ? Math.round(((u.tamam + u.hata) / u.toplam) * 100) : 100;
  const durum = u.calisiyor
    ? `${DONEN}<span class="font-medium">Muse taslakları hazırlıyor</span>
       <span class="tabular-nums text-slate-500">${u.tamam + u.hata} / ${u.toplam}</span>
       <span class="w-40 h-1.5 rounded-full bg-slate-100 overflow-hidden"><span class="block h-full bg-gok transition-all" style="width:${ilerleme}%"></span></span>`
    : o.taslak_hazir
      ? `${TIK}<span class="font-medium">Taslaklar hazır</span><span class="text-slate-500">${sayi(o.taslak_hazir, 0)} taslak${o.ik_dikkat ? ` · ${sayi(o.ik_dikkat, 0)} tanesinde İK dikkat` : ""}</span>`
      : `<span class="text-slate-500">Henüz taslak yok.</span>`;
  const eksik = !u.calisiyor && o.islenmedi
    ? `<button id="eksikleri-hazirla" class="text-sm px-3 py-1 rounded-lg bg-gok text-white hover:bg-thykoyu">${u.hata ? `${u.hata} taslak üretilemedi · yeniden dene` : "Eksik taslakları hazırla"}</button>` : "";
  $("ozet").innerHTML = `
    <div class="flex flex-wrap items-end gap-x-6 gap-y-4">
      <div><p class="text-xs text-slate-500">Toplam başvuru</p><p class="text-4xl font-semibold tabular-nums leading-none mt-1">${sayi(o.toplam, 0)}</p></div>
      <svg class="h-6 w-6 text-slate-300 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>
      <button data-grup="olumsuz" class="text-left"><p class="text-xs text-slate-500">Olumsuz karar · geri bildirim kapsamı</p>
        <p class="text-4xl font-semibold tabular-nums leading-none mt-1 text-murekkep">${sayi(o.olumsuz, 0)}</p></button>
      <div class="sm:ml-auto flex flex-wrap gap-2">
        ${yan("Kabul", o.kabul, "kapsam_disi")}${yan("Değerlendirmesi süren", o.devam, "kapsam_disi")}${yan("Veri sorunu", o.veri_sorunu, "ik")}
      </div>
    </div>
    <div class="mt-5 flex h-3 gap-0.5 rounded-full overflow-hidden bg-slate-100" role="img" aria-label="Olumsuz başvuruların durumu">
      ${parcalar.filter((p) => p.n > 0).map((p) => `<button data-grup="${p.grup}" aria-label="${esc(p.ad)}: ${p.n}" class="${p.dolgu} h-full hover:opacity-80" style="width:${(p.n / payda) * 100}%"></button>`).join("")}
    </div>
    <div class="mt-3 grid grid-cols-2 lg:grid-cols-4 gap-2">
      ${parcalar.map((p) => `<button data-grup="${p.grup}" class="flex items-start gap-2 rounded-lg px-2 py-1.5 text-left hover:bg-slate-50 ${S.grup === p.grup ? "bg-slate-50 ring-1 ring-slate-200" : ""}">
        <span class="mt-1.5 h-2.5 w-2.5 rounded-sm ${p.dolgu} shrink-0"></span>
        <span><span class="block text-sm"><b class="tabular-nums">${sayi(p.n, 0)}</b> ${esc(p.ad)}</span><span class="block text-xs text-slate-400">${esc(p.not)}</span></span></button>`).join("")}
    </div>
    <div class="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3 text-sm">
      ${durum}${eksik}
      <span class="sm:ml-auto text-xs text-slate-400">Gönderim düğmesi yok; her e-posta İK onayından geçer.</span>
    </div>`;
}

let izleyici;
function uretimiIzle() {
  clearTimeout(izleyici);
  if (!(S.ozet && S.ozet.uretim && S.ozet.uretim.calisiyor)) return;
  izleyici = setTimeout(async () => {
    try {
      S.ozet = await api("/api/ozet");
      S.liste = await api("/api/basvurular");
      ozetCiz();
      if (S.sekme === "basvurular" && document.activeElement?.id !== "ara") basvurularCiz();
      if (S.detay && !S.detay.taslak && S.detay.taslak_uretilebilir && !$("cekmece").classList.contains("hidden")) await detayAc(S.detay.basvuru_id);
    } catch (e) { /* bir sonraki turda yeniden denenir */ }
    uretimiIzle();
  }, 2000);
}

function ciz() {
  const yuklu = S.ozet && S.ozet.yuklu;
  $("bos").classList.toggle("hidden", !!yuklu);
  ["ozet", "sekmeler"].forEach((id) => $(id).classList.toggle("hidden", !yuklu));
  $("dosya-cip").classList.toggle("hidden", !yuklu);
  $("dosya-cip").classList.toggle("flex", !!yuklu);
  $("yukle-etiket").textContent = yuklu ? "Yeni dosya yükle" : "ATS Excel dosyası yükle";
  if (yuklu) {
    $("dosya-adi").textContent = S.ozet.dosya_adi;
    $("dosya-meta").textContent = `${S.ozet.toplam} kayıt · ${new Date(S.ozet.yukleme_zamani).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })}`;
  }
  if (!yuklu) { $("icerik").innerHTML = ""; return; }
  ozetCiz();
  document.querySelectorAll(".sekme").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.sekme === S.sekme)));
  if (S.sekme === "basvurular") basvurularCiz();
  else if (S.sekme === "ik") ikCiz();
  else isYukuCiz();
}

// ---------- başvurular ----------
function basvurularCiz() {
  const asamalar = [...new Set(S.liste.map((x) => x.asama).filter(Boolean))];
  const ara = S.ara.trim().toLowerCase();
  const gruplar = { tum: () => true, olumsuz: (x) => x.karar === "OLUMSUZ", hazir: (x) => x.olumsuz_alt === "hazir",
    onaylandi: (x) => (x.taslak_durumu || {}).kod === "onaylandi", islenmedi: (x) => x.olumsuz_alt === "islenmedi",
    ik: (x) => x.durum === "İK incelemesi", kapsam_disi: (x) => x.durum === "Kapsam dışı" };
  const satirlar = S.liste.filter((x) => gruplar[S.grup](x) && (!S.asama || x.asama === S.asama) && (!ara || x.basvuru_id.toLowerCase().includes(ara)));
  const cip = (k, ad) => `<button data-grup="${k}" class="px-3 py-1 rounded-full text-sm ring-1 ring-inset ${
    S.grup === k ? "bg-murekkep text-white ring-murekkep" : "bg-white text-slate-600 ring-slate-300 hover:bg-slate-50"}">${ad}</button>`;
  $("icerik").innerHTML = `
    <div class="flex flex-wrap items-center gap-2 mb-3">
      ${cip("tum", "Tümü")}${cip("olumsuz", "Olumsuz")}${cip("hazir", "Taslağı hazır")}${cip("onaylandi", "İK onaylı")}
      ${S.ozet.islenmedi ? cip("islenmedi", "Taslağı yok") : ""}${cip("ik", "İK incelemesi")}${cip("kapsam_disi", "Kapsam dışı")}
      <select id="asama" class="ml-auto text-sm rounded-lg border-slate-300 bg-white px-2 py-1 ring-1 ring-slate-300">
        <option value="">Bütün aşamalar</option>${asamalar.map((a) => `<option ${a === S.asama ? "selected" : ""}>${esc(a)}</option>`).join("")}
      </select>
      <input id="ara" value="${esc(S.ara)}" placeholder="BSV-… ara" class="text-sm rounded-lg px-3 py-1 ring-1 ring-slate-300 w-32">
      <label class="cursor-pointer text-sm text-gok hover:underline">Hazır yanıt dosyası yükle
        <input id="yanit-dosya" type="file" accept=".xlsx,.json" class="hidden"></label>
    </div>
    <div class="bg-white rounded-xl border border-slate-200 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs text-slate-500 bg-slate-50 border-b border-slate-200"><tr>
          <th class="px-4 py-2 font-medium">Başvuru</th><th class="px-4 py-2 font-medium">Karar</th><th class="px-4 py-2 font-medium">Aşama</th>
          <th class="px-4 py-2 font-medium">Durum</th><th class="px-4 py-2 font-medium">Taslak</th><th class="px-4 py-2 font-medium">Neden / dikkat</th></tr></thead>
        <tbody>${satirlar.map((x) => `
          <tr data-bsv="${esc(x.basvuru_id)}" class="border-b border-slate-100 hover:bg-red-50/40 cursor-pointer">
            <td class="px-4 py-2 font-mono text-xs whitespace-nowrap">${esc(x.basvuru_id)}</td>
            <td class="px-4 py-2">${rozet(KARAR_ADI[x.karar] || x.karar || "Veri sorunu", x.karar || "dikkat")}</td>
            <td class="px-4 py-2">${esc(x.asama)}</td>
            <td class="px-4 py-2">${rozet(x.durum, x.durum)}</td>
            <td class="px-4 py-2">${x.taslak_durumu ? taslakRozetleri(x.taslak_durumu) : x.taslak_uretilebilir ? '<span class="text-xs text-slate-400">henüz yok</span>' : ""}</td>
            <td class="px-4 py-2 text-xs text-slate-500">${esc(x.nedenler.join("; ") || x.uyarilar.join(" "))}</td>
          </tr>`).join("") || '<tr><td colspan="6" class="px-4 py-8 text-center text-slate-400">Bu süzgece uyan başvuru yok.</td></tr>'}
        </tbody>
      </table>
    </div>
    <p class="text-xs text-slate-400 mt-2">${satirlar.length} başvuru gösteriliyor. Ayrıntı için satıra tıklayın.</p>`;
}

// ---------- detay ----------
async function detayAc(bsv) {
  try {
    S.detay = await api(`/api/basvurular/${encodeURIComponent(bsv)}`);
    detayCiz();
    $("cekmece").classList.remove("hidden");
  } catch (e) { bildir(e.message); }
}

function kutu(renk, baslik, govde) {
  const r = { yesil: "bg-emerald-50 ring-emerald-200 text-emerald-900", sari: "bg-amber-50 ring-amber-200 text-amber-900",
    kirmizi: "bg-rose-50 ring-rose-200 text-rose-900", gri: "bg-slate-50 ring-slate-200 text-slate-700" }[renk];
  return `<div class="rounded-lg ring-1 ring-inset ${r} px-4 py-3 text-sm"><p class="font-medium">${esc(baslik)}</p>${govde ? `<div class="mt-1">${govde}</div>` : ""}</div>`;
}

function taslakAlani(d) {
  if (d.karar !== "OLUMSUZ")
    return kutu("gri", `Bu başvurunun kaydı: ${KARAR_ADI[d.karar] || d.karar || "tanımsız"}`, d.karar ? "Kabul edilen ya da değerlendirmesi süren başvuru için olumsuz e-posta üretilmez." : "Karar kodu eksik ya da tanımsız; veri sorunu olarak İK'ya ayrıldı.");
  if (!d.taslak_uretilebilir)
    return kutu("kirmizi", "E-posta üretilmez: başvuru İK incelemesine ayrıldı", `<ul class="list-disc ml-5">${d.bulgular.map((b) => `<li>${esc(b.ad)}: ${esc(b.aciklama)}</li>`).join("")}</ul>`);
  const t = d.taslak;
  if (!t && S.ozet.uretim && S.ozet.uretim.calisiyor && !S.mesgul)
    return `<div class="bg-white rounded-xl border border-slate-200 p-6 flex items-center justify-center gap-3 text-sm text-slate-600">
      ${DONEN}<span>Muse bu taslağı hazırlıyor; hazır olunca burada açılacak.</span></div>`;
  if (!t)
    return `<div class="bg-white rounded-xl border border-slate-200 p-6 text-center">
      <p class="text-sm text-slate-600">Ön kontrolden geçti. Taslak, yalnız soldaki "modele verildi" işaretli kayıtlarla üretilir.</p>
      <button id="uret" class="mt-4 bg-gok text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-thykoyu disabled:opacity-60" ${S.mesgul ? "disabled" : ""}>
        ${S.mesgul ? "Muse taslak yazıyor…" : "Yapay zekâ taslağı üret"}</button></div>`;
  const gecersiz = t.durum.kod === "gecersiz";
  const kontrol = t.kontrol.length
    ? kutu("sari", `Son kontrol: ${t.kontrol.length} uyarı · İK dikkat`, `<ul class="list-disc ml-5">${t.kontrol.map((k) => `<li>${esc(k.aciklama)}</li>`).join("")}</ul>`)
    : kutu("yesil", "Son kontrol: sorun bulunmadı", "Kayıt ID'leri, sayılar, yasaklı ifadeler, uzunluk ve Başvuru ID kontrol edildi.");
  return `
    <div class="bg-white rounded-xl border border-slate-200 p-4 space-y-3">
      <div class="flex flex-wrap items-center gap-2">${taslakRozetleri(t.durum)}
        ${t.ik_duzeltti ? rozet(`İK düzeltmesi kaydedildi · ${new Date(t.ik_zaman).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })}`, "onaylandi") : ""}
        <span class="text-xs text-slate-400 ml-auto">${esc(t.kaynak_turu === "dosya" ? "yanıt dosyasından" : t.model)} · ${esc(t.olusturma.replace("T", " "))}</span></div>
      <div class="inline-flex rounded-lg ring-1 ring-slate-300 p-0.5 text-sm" role="tablist" aria-label="E-posta dili">
        ${[["tr", "Türkçe"], ["en", t.ingilizce ? "English" : "English · oluştur"]].map(([k, ad]) => `<button data-dil="${k}" role="tab" aria-selected="${S.dil === k}"
          class="px-3 py-1 rounded-md ${S.dil === k ? "bg-murekkep text-white" : "text-slate-600 hover:bg-slate-50"}">${ad}</button>`).join("")}
      </div>
      ${S.dil === "en" ? ingilizceAlani(t, gecersiz) : `
      ${gecersiz ? kutu("kirmizi", "Veri değişti: bu taslak ve onayı geçersiz", "Kayıtlar taslak üretildikten sonra değişti. Yeni taslak üretin.") : ""}
      ${t.durum.kod === "onay_dustu" ? kutu("sari", "Onay düştü", "Onaydan sonra metin değişti; güncel metni yeniden onaylayın.") : ""}
      <label class="block text-xs font-medium text-slate-500">Konu
        <input id="konu" class="mt-1 w-full rounded-lg ring-1 ring-slate-300 px-3 py-2 text-sm" value="${esc(t.konu)}" ${gecersiz ? "disabled" : ""}></label>
      <label class="block text-xs font-medium text-slate-500">E-posta metni <span id="kelime" class="font-normal">(${t.kelime} kelime; en fazla 120)</span>
        <textarea id="metin" rows="10" class="mt-1 w-full rounded-lg ring-1 ring-slate-300 px-3 py-2 text-sm leading-relaxed" ${gecersiz ? "disabled" : ""}>${esc(t.metin)}</textarea></label>
      ${kontrol}
      ${t.emin_olunmayan.length ? kutu("gri", "Modelin emin olmadığı noktalar", `<ul class="list-disc ml-5">${t.emin_olunmayan.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`) : ""}
      <p class="text-xs text-slate-500">Dayandığı kayıtlar: <span class="font-mono">${esc(t.kullanilan_idler.join(", ") || "—")}</span></p>
      ${t.ik_duzeltti ? `<details class="text-sm"><summary class="cursor-pointer text-xs text-slate-500">İlk yapay zekâ taslağı (İK düzeltmeden önce)</summary>
        <p class="mt-2 font-medium">${esc(t.ilk_konu)}</p><p class="mt-1 whitespace-pre-wrap text-slate-600">${esc(t.ilk_metin)}</p></details>` : ""}
      <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
        ${t.kontrol.length && !gecersiz ? `<label class="text-xs text-slate-600 flex items-center gap-1"><input id="okudum" type="checkbox"> Uyarıları okudum</label>` : ""}
        <button id="kaydet" class="text-sm px-4 py-2 rounded-lg ring-1 ring-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50" ${gecersiz ? "disabled" : ""}>Düzeltmeyi kaydet</button>
        <button id="onayla" class="text-sm px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50" ${gecersiz || t.durum.kod === "onaylandi" ? "disabled" : ""}>İK onayla</button>
        <button id="uret" class="text-sm px-4 py-2 rounded-lg text-gok hover:underline ml-auto disabled:opacity-60" ${S.mesgul ? "disabled" : ""}>${S.mesgul ? "Muse yazıyor…" : "Yeniden üret"}</button>
      </div>
      <p class="text-xs text-slate-400">Gönderim düğmesi yok: e-posta yalnız İK onayından sonra, sistem dışında gönderilir.</p>`}
    </div>`;
}

function ingilizceAlani(t, gecersiz) {
  if (gecersiz) return kutu("kirmizi", "Veri değişti", "Önce Türkçe taslağı yeniden üretin; İngilizce sürüm güncel Türkçe metinden oluşturulur.");
  const en = t.ingilizce;
  const dugme = (metin) => `<button id="cevir" class="text-sm px-4 py-2 rounded-lg bg-gok text-white font-medium hover:bg-thykoyu disabled:opacity-60" ${S.mesgul ? "disabled" : ""}>
    ${S.mesgul ? "Muse çeviriyor…" : metin}</button>`;
  if (!en)
    return `<div class="rounded-lg ring-1 ring-slate-200 p-6 text-center space-y-3">
      <p class="text-sm text-slate-600">İngilizce sürüm henüz yok. Muse, ekrandaki güncel Türkçe metni başvurunun kayıtlarıyla birlikte o anda çevirir;
        karar, gerekçe, sayılar, Başvuru ID ve üslup korunur.</p>${dugme("İngilizce sürümünü oluştur")}</div>`;
  const kontrol = en.kontrol.length
    ? kutu("sari", `Bağlam kontrolü: ${en.kontrol.length} uyarı`, `<ul class="list-disc ml-5">${en.kontrol.map((k) => `<li>${esc(k.aciklama)}</li>`).join("")}</ul>`)
    : kutu("yesil", "Bağlam kontrolü: Türkçe metinle tutarlı", "Sayılar, Başvuru ID, uzunluk ve yasaklı ifadeler kontrol edildi.");
  return `
    ${en.guncel ? "" : kutu("sari", "Türkçe metin değişti", "Bu İngilizce sürüm önceki Türkçe metinden oluşturuldu; yeniden oluşturun.")}
    <label class="block text-xs font-medium text-slate-500">Subject
      <input class="mt-1 w-full rounded-lg ring-1 ring-slate-200 bg-slate-50 px-3 py-2 text-sm" value="${esc(en.konu)}" readonly></label>
    <label class="block text-xs font-medium text-slate-500">Email body <span class="font-normal">(${en.metin.split(/\s+/).filter(Boolean).length} words)</span>
      <textarea rows="10" class="mt-1 w-full rounded-lg ring-1 ring-slate-200 bg-slate-50 px-3 py-2 text-sm leading-relaxed" readonly>${esc(en.metin)}</textarea></label>
    ${kontrol}
    ${en.notlar.length ? kutu("gri", "Modelin anlam farkı notları", `<ul class="list-disc ml-5">${en.notlar.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`) : ""}
    <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
      ${dugme("Yeniden oluştur")}
      <span class="text-xs text-slate-400">${esc(new Date(en.zaman).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }))} · İK onayı Türkçe metin içindir.</span>
    </div>`;
}

function detayCiz() {
  const d = S.detay;
  const onKontrol = d.bulgular.length
    ? kutu("kirmizi", "Ön kontrol: İK incelemesi gerekli", `<ul class="list-disc ml-5">${d.bulgular.map((b) => `<li><b>${esc(b.ad)}</b>: ${esc(b.aciklama)}</li>`).join("")}</ul>`)
    : d.karar === "OLUMSUZ" ? kutu("yesil", "Ön kontrol: geçti", d.uyarilar.length ? `<ul class="list-disc ml-5">${d.uyarilar.map((u) => `<li>${esc(u)}</li>`).join("")}</ul>` : "") : "";
  $("detay").innerHTML = `
    <div class="sticky top-0 z-10 bg-white border-b border-slate-200 px-6 py-4 flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-semibold font-mono">${esc(d.basvuru_id)}</h2>
      ${rozet(KARAR_ADI[d.karar] || d.karar || "Veri sorunu", d.karar || "dikkat")} ${rozet(d.asama, "sade")} ${rozet(d.durum, d.durum)}
      <button id="kapat" class="ml-auto text-sm text-slate-500 hover:text-slate-800 px-3 py-1 rounded-lg ring-1 ring-slate-300">Kapat</button>
    </div>
    <div class="grid lg:grid-cols-2 gap-6 p-6">
      <div class="space-y-4 min-w-0">
        ${onKontrol}
        <div>
          <h3 class="text-sm font-semibold mb-2">Dayandığı kayıtlar</h3>
          <div class="space-y-2">${d.kayitlar.map((k) => `
            <div class="bg-white rounded-lg border border-slate-200 px-4 py-3">
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="font-mono font-medium">${esc(k.kayit_id)}</span><span class="text-slate-500">${esc(k.sayfa)}</span>
                ${k.asama ? `<span class="text-slate-400">· ${esc(k.asama)}</span>` : ""}
                <span class="ml-auto flex gap-1">${k.paylasim ? rozet(k.paylasim === "KURUM_ICI" ? "Kurum içi" : "Paylaşılabilir", k.paylasim === "KURUM_ICI" ? "gecersiz" : "sade") : ""}
                ${k.modele_verildi ? rozet("Modele verildi", "onay_bekliyor") : rozet("Modele verilmedi", "sade")}</span>
              </div>
              <p class="text-sm text-slate-700 mt-1.5">${esc(k.icerik)}</p>
            </div>`).join("") || '<p class="text-sm text-slate-400">Kayıt yok.</p>'}</div>
        </div>
        ${d.model_girdisi ? `<details class="bg-white rounded-lg border border-slate-200 px-4 py-3"><summary class="cursor-pointer text-sm font-medium">Modele giden girdi (JSON)</summary>
          <pre class="mt-2 text-xs font-mono whitespace-pre-wrap text-slate-600">${esc(JSON.stringify(d.model_girdisi, null, 2))}</pre></details>` : ""}
      </div>
      <div class="space-y-4 min-w-0"><h3 class="text-sm font-semibold">E-posta taslağı</h3>${taslakAlani(d)}</div>
    </div>`;
}

async function detayEylem(fn, basari) {
  // Formdaki değerler fn çağrılmadan önce okunmalı: detayCiz() kutuları kayıtlı metinle yeniden çizer.
  try {
    S.mesgul = true; detayCiz();
    S.detay = await fn();
    await yenile();
    if (basari) bildir(basari, "bilgi");
  } catch (e) { bildir(e.message); }
  finally { S.mesgul = false; detayCiz(); }
}

// ---------- İK listesi ----------
function ikCiz() {
  const satirlar = S.liste.filter((x) => x.durum === "İK incelemesi");
  $("icerik").innerHTML = `
    <div class="flex flex-wrap items-center gap-3 mb-3">
      <p class="text-sm text-slate-600">E-posta üretilmeden İK'ya ayrılan başvurular. Sunumun son sayfası bu listeyle doldurulur.</p>
      <a href="/api/disari/ik-listesi.xlsx" class="ml-auto text-sm px-3 py-1.5 rounded-lg bg-murekkep text-white">İK listesini Excel'e aktar</a>
      <a href="/api/disari/duzeltmeler.xlsx" class="text-sm px-3 py-1.5 rounded-lg ring-1 ring-slate-300 bg-white">İK düzeltmelerini indir</a>
    </div>
    <div class="bg-white rounded-xl border border-slate-200 overflow-x-auto"><table class="w-full text-sm">
      <thead class="text-left text-xs text-slate-500 bg-slate-50 border-b border-slate-200"><tr>
        <th class="px-4 py-2 font-medium">Başvuru</th><th class="px-4 py-2 font-medium">Aşama</th><th class="px-4 py-2 font-medium">Neden İK'ya ayrıldı</th></tr></thead>
      <tbody>${satirlar.map((x) => `<tr data-bsv="${esc(x.basvuru_id)}" class="border-b border-slate-100 hover:bg-amber-50/50 cursor-pointer">
        <td class="px-4 py-2 font-mono text-xs">${esc(x.basvuru_id)}</td><td class="px-4 py-2">${esc(x.asama)}</td>
        <td class="px-4 py-2">${esc(x.nedenler.join("; "))}</td></tr>`).join("") || '<tr><td colspan="3" class="px-4 py-8 text-center text-slate-400">İK incelemesine ayrılan başvuru yok.</td></tr>'}</tbody>
    </table></div>`;
}

// ---------- iş yükü ----------
const P = { okuma_dk: 0.5, kontrol_dk: 1, duzeltme_orani: 0.1, duzeltme_dk: 2, sorunlulari_elle_yaz: false };
async function isYukuCiz() {
  let r;
  try { r = await api("/api/is-yuku?" + new URLSearchParams(Object.entries(P).map(([k, v]) => [k, String(v)]))); }
  catch (e) { $("icerik").innerHTML = kutu("sari", "İş yükü hesaplanamadı", esc(e.message)); return; }
  if (S.sekme !== "isyuku") return;
  const buyuk = (baslik, o, not) => `<div class="bg-white rounded-xl border border-slate-200 p-5">
      <p class="text-sm font-medium">${baslik}</p>
      <p class="text-3xl font-semibold tabular-nums mt-2">${sayi(o.saat)} <span class="text-base font-normal text-slate-500">saat</span></p>
      <p class="text-sm text-slate-600 mt-1">Dönüş süresi: <b>${sayi(o.is_gunu)}</b> iş günü</p>
      <p class="mt-2">${rozet(o.kapasiteye_sigar ? "Kapasiteye sığıyor" : "Kapasiteye sığmıyor", o.kapasiteye_sigar ? "onaylandi" : "gecersiz")}</p>
      <p class="text-xs text-slate-400 mt-2">${not}</p></div>`;
  const alan = (k, etiket, adim) => `<label class="text-xs text-slate-500">${etiket}
      <input data-p="${k}" type="number" step="${adim}" min="0" value="${P[k]}" class="mt-1 block w-28 rounded-lg ring-1 ring-slate-300 px-2 py-1 text-sm"></label>`;
  $("icerik").innerHTML = `
    <p class="text-sm text-slate-600 mb-3">1.200 başvuruluk dönem · ayrılan kapasite ${sayi(r.kapasite_saat)} saat / ${sayi(r.is_gunu, 0)} iş günü. Elle süreç dosyadaki İş Yükü Verileri'nden; önerilen süreç aşağıdaki varsayımlardan hesaplanır.</p>
    <div class="grid md:grid-cols-2 gap-4">${buyuk("Elle hazırlama", r.elle, "olumsuz × (okuma + yazma + son kontrol) + ek inceleme × ek süre")}
      ${buyuk("Önerilen süreç", r.oneri, "olumsuz × (okuma + kontrol) + düzeltme payı + ek inceleme × ek süre")}</div>
    <div class="bg-white rounded-xl border border-slate-200 p-4 mt-4 flex flex-wrap items-end gap-4">
      ${alan("okuma_dk", "Okuma (dk / başvuru)", 0.1)}${alan("kontrol_dk", "İK kontrolü (dk / taslak)", 0.1)}
      ${alan("duzeltme_orani", "Düzeltilen oran (0–1)", 0.05)}${alan("duzeltme_dk", "Düzeltme (dk)", 0.5)}
      <label class="text-xs text-slate-600 flex items-center gap-2"><input data-p="sorunlulari_elle_yaz" type="checkbox" ${P.sorunlulari_elle_yaz ? "checked" : ""}>
        Sorunlu başvuruların e-postası elle yazılır (yazma süresi eklenir)</label>
      <p class="text-xs text-slate-400 basis-full">Varsayılanlar takım kararından: okuma 0,5 dk, kontrol 1 dk, başvuruların %10'unda 2 dk düzeltme. Bir değeri değiştirip dönüş süresine etkisini görün; ölçülen süreyle güncelleyin.</p>
    </div>
    <div class="bg-white rounded-xl border border-slate-200 overflow-x-auto mt-4"><table class="w-full text-sm">
      <thead class="text-left text-xs text-slate-500 bg-slate-50 border-b border-slate-200"><tr><th class="px-4 py-2 font-medium">Aşama</th>
        <th class="px-4 py-2 font-medium text-right">Olumsuz</th><th class="px-4 py-2 font-medium text-right">Ek inceleme</th>
        <th class="px-4 py-2 font-medium text-right">Elle (saat)</th><th class="px-4 py-2 font-medium text-right">Önerilen (saat)</th></tr></thead>
      <tbody>${r.asamalar.map((a) => `<tr class="border-b border-slate-100"><td class="px-4 py-2">${esc(a.asama)}</td>
        <td class="px-4 py-2 text-right tabular-nums">${sayi(a.olumsuz, 0)}</td><td class="px-4 py-2 text-right tabular-nums">${sayi(a.ek_inceleme, 0)}</td>
        <td class="px-4 py-2 text-right tabular-nums">${sayi(a.elle_saat)}</td><td class="px-4 py-2 text-right tabular-nums">${sayi(a.oneri_saat)}</td></tr>`).join("")}</tbody>
    </table></div>`;
}

// ---------- olaylar ----------
$("dosya").addEventListener("change", (e) => { if (e.target.files[0]) dosyaYukle(e.target.files[0]); e.target.value = ""; });
document.querySelectorAll(".sekme").forEach((b) => b.addEventListener("click", () => { S.sekme = b.dataset.sekme; ciz(); }));
$("perde").addEventListener("click", () => $("cekmece").classList.add("hidden"));
$("ozet").addEventListener("click", async (e) => {
  if (e.target.closest("#eksikleri-hazirla")) {
    try { await api("/api/uretim", { method: "POST" }); await yenile(); } catch (err) { bildir(err.message); }
    return;
  }
  const g = e.target.closest("[data-grup]");
  if (!g) return;
  S.grup = g.dataset.grup;
  S.sekme = "basvurular";
  ciz();
  $("sekmeler").scrollIntoView({ behavior: "smooth", block: "start" });
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("cekmece").classList.add("hidden"); });

$("icerik").addEventListener("click", (e) => {
  const grup = e.target.closest("[data-grup]");
  if (grup) { S.grup = grup.dataset.grup; basvurularCiz(); return; }
  const tr = e.target.closest("tr[data-bsv]");
  if (tr) detayAc(tr.dataset.bsv);
});
$("icerik").addEventListener("change", async (e) => {
  if (e.target.id === "asama") { S.asama = e.target.value; basvurularCiz(); }
  if (e.target.dataset.p) {
    P[e.target.dataset.p] = e.target.type === "checkbox" ? e.target.checked : Number(e.target.value);
    isYukuCiz();
  }
  if (e.target.id === "yanit-dosya" && e.target.files[0]) {
    const fd = new FormData(); fd.append("dosya", e.target.files[0]);
    try {
      const r = await api("/api/yanitlar", { method: "POST", body: fd });
      bildir(`${r.kabul.length} yanıt eşleşti${r.red.length ? `, ${r.red.length} yanıt eşleşmedi ve onaya açılmadı` : ""}.`, "bilgi");
      await yenile();
    } catch (err) { bildir(err.message); }
  }
});
$("icerik").addEventListener("input", (e) => {
  if (e.target.id !== "ara") return;
  S.ara = e.target.value;
  basvurularCiz();
  const ara = $("ara");
  ara.focus();
  ara.setSelectionRange(ara.value.length, ara.value.length);
});

$("detay").addEventListener("input", (e) => {
  if (e.target.id === "metin") $("kelime").textContent = `(${e.target.value.trim().split(/\s+/).filter(Boolean).length} kelime; en fazla 120)`;
});
$("detay").addEventListener("click", (e) => {
  const b = S.detay && encodeURIComponent(S.detay.basvuru_id);
  if (e.target.id === "kapat") $("cekmece").classList.add("hidden");
  if (e.target.id === "uret") detayEylem(() => api(`/api/basvurular/${b}/taslak`, { method: "POST" }));
  const dil = e.target.closest("[data-dil]");
  if (dil) { S.dil = dil.dataset.dil; detayCiz(); }
  if (e.target.id === "cevir") detayEylem(() => api(`/api/basvurular/${b}/ingilizce`, { method: "POST" }), "İngilizce sürüm oluşturuldu.");
  if (e.target.id === "kaydet") {
    const govde = JSON.stringify({ konu: $("konu").value, metin: $("metin").value });
    detayEylem(() => api(`/api/basvurular/${b}/duzeltme`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: govde }),
      "Düzeltme kaydedildi; ekranda düzenlenmiş metin görünüyor.");
  }
  if (e.target.id === "onayla") {
    const okudum = $("okudum") ? $("okudum").checked : false;
    const degisti = $("metin").value.trim() !== S.detay.taslak.metin || $("konu").value.trim() !== S.detay.taslak.konu;
    if (degisti) { bildir("Metni değiştirdiniz; önce düzeltmeyi kaydedin, sonra onaylayın."); return; }
    detayEylem(() => api(`/api/basvurular/${b}/onay`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ uyarilari_okudum: okudum }) }),
      "Güncel metin İK tarafından onaylandı.");
  }
});

yenile().catch((e) => bildir(e.message));
