(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function numberOrString(val) {
    if (val == null || val === "") return undefined;
    const n = Number(String(val).replace(",", "."));
    return Number.isFinite(n) ? n : val;
  }

  // Si tus inputs usan otros nombres, mapea aquí
  const NAME_MAP = {
    insolation_flux: "insolation",
    star_radius: "stellar_radius",
    star_mass: "stellar_mass",
    star_temp: "stellar_temp",
    star_logg: "stellar_logg",
    star_metallicity: "stellar_metallicity",
    star_density: "stellar_density",
  };

  function collectPayload(form) {
    const data = {};
    $$("input[name], select[name], textarea[name]", form).forEach((el) => {
      const raw = el.name;
      const name = NAME_MAP[raw] || raw;
      const v = numberOrString(el.value);
      if (v !== undefined) data[name] = v;
    });
    return data;
  }

  function fillFields(form, obj) {
    Object.entries(obj).forEach(([k, v]) => {
      // respeta tus nombres de input originales
      const raw = Object.entries(NAME_MAP).find(([, norm]) => norm === k)?.[0] || k;
      const el = $(`[name="${raw}"]`, form);
      if (el) el.value = v;
    });
  }

  function showResult(ok, data) {
    const box = $("#resultBox") || (function () {
      const b = document.createElement("div");
      b.id = "resultBox";
      document.body.appendChild(b);
      return b;
    })();
    box.className = ok ? "result ok" : "result error";
    box.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }

  // Ejemplos (ajusta valores si quieres)
  const EX_SIMPLE = {
    orbital_period: 10.5,
    transit_duration: 3.2,
    transit_depth: 500,
    stellar_temp: 5700,
  };
  const EX_FULL = {
    orbital_period: 10.5,
    transit_epoch: 134.2,
    transit_duration: 3.2,
    transit_depth: 500,
    transit_snr: 15,
    impact_param: 0.3,
    eccentricity: 0.02,
    semi_major_axis: 0.09,
    planet_radius: 1.4,
    equilibrium_temp: 900,
    insolation: 1200,
    stellar_radius: 1.0,
    stellar_mass: 1.0,
    stellar_temp: 5700,
    stellar_logg: 4.4,
    stellar_metallicity: 0.0,
    stellar_density: 1.4,
  };

  function wireUp() {
    const form = $("form"); // si tienes un id específico, usa #miForm
    if (!form) return;

    // Evita submit por Enter o por ‘submit’ del form
    form.addEventListener("submit", (e) => e.preventDefault());

    // Asegura que los botones NO sean submit
    const btnSimple  = $("#btnSimple");
    const btnFull    = $("#btnFull");
    const btnPredict = $("#btnPredict");
    const btnClear   = $("#btnClear");

    btnSimple && btnSimple.addEventListener("click", (e) => {
      e.preventDefault();
      fillFields(form, EX_SIMPLE);
    });

    btnFull && btnFull.addEventListener("click", (e) => {
      e.preventDefault();
      fillFields(form, EX_FULL);
    });

    btnPredict && btnPredict.addEventListener("click", async (e) => {
      e.preventDefault();
      const payload = collectPayload(form);

      // Validación mínima para evitar 400
      const min = ["orbital_period", "transit_duration", "transit_depth"];
      const present = min.filter((k) => payload[k] !== undefined && payload[k] !== null);
      if (present.length < 2) {
        showResult(false, { error: "Completa al menos dos de: orbital_period, transit_duration, transit_depth." });
        return;
      }

      try {
        const resp = await fetch("/api/calculateDisposition", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await resp.json().catch(() => ({}));
        showResult(resp.ok, data);
      } catch (err) {
        showResult(false, { error: String(err) });
      }
    });

    btnClear && btnClear.addEventListener("click", (e) => {
      // Si quieres limpiar, déjalo; si NO, cambia el type del botón a "button"
      // aquí no hacemos nada extra
    });

    // Útil para debug desde consola
    window.__collectPayload = () => collectPayload(form);
  }

  // Asegura que el DOM esté cargado
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireUp);
  } else {
    wireUp();
  }
})();
