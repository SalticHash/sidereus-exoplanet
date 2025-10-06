// static/js/app.js
(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function toNumberOrLeave(val) {
    if (val == null || val === "") return undefined;
    const n = Number(String(val).replace(",", "."));
    return Number.isFinite(n) ? n : val;
  }

  function normKey(raw) {
    // quita prefijo s_/c_
    let k = raw.replace(/^(s_|c_)/, "");
    // mapeos compatibles con backend
    if (k.startsWith("star_")) k = "stellar_" + k.slice(5);
    if (k === "insolation_flux") k = "insolation";
    return k;
  }

  function collectFromForm(form) {
    const data = {};
    // toma todos los inputs con id que empiece en s_ o c_
    $$('input[id^="s_"], input[id^="c_"], select[id^="s_"], select[id^="c_"], textarea[id^="s_"], textarea[id^="c_"]', form)
      .forEach(el => {
        const key = normKey(el.id);
        const v = toNumberOrLeave(el.value);
        if (v !== undefined) data[key] = v;
      });
    return data;
  }

  function validateMin(payload) {
    const min = ["orbital_period", "transit_duration", "transit_depth"];
    return min.filter(k => payload[k] !== undefined && payload[k] !== null).length >= 2;
  }

  function setLoading(btn, on) {
    const loader = btn?.querySelector(".loader");
    if (!loader) return;
    loader.classList.toggle("hidden", !on);
    btn.disabled = !!on;
  }

  async function submitForm(form, resultBox, submitBtn) {
    const payload = collectFromForm(form);

    if (!validateMin(payload)) {
      resultBox.classList.remove("hidden");
      resultBox.innerHTML = `<div class="alert error">Completa al menos dos de: <code>orbital_period</code>, <code>transit_duration</code>, <code>transit_depth</code>.</div>`;
      return;
    }

    try {
      setLoading(submitBtn, true);
      const resp = await fetch("/api/calculateDisposition", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json().catch(() => ({}));
      resultBox.classList.remove("hidden");
      resultBox.innerHTML = `<pre class="${resp.ok ? "ok" : "error"}">${JSON.stringify(data, null, 2)}</pre>`;
    } catch (err) {
      resultBox.classList.remove("hidden");
      resultBox.innerHTML = `<div class="alert error">${String(err)}</div>`;
    } finally {
      setLoading(submitBtn, false);
    }
  }

  function clearForm(form, resultBox) {
    $$("input, select, textarea", form).forEach(el => {
      if (el.type === "checkbox" || el.type === "radio") el.checked = false;
      else el.value = "";
    });
    resultBox.innerHTML = "";
    resultBox.classList.add("hidden");
  }

  function wire(formId, resultId, clearBtnId) {
    const form = document.getElementById(formId);
    const resultBox = document.getElementById(resultId);
    const clearBtn = document.getElementById(clearBtnId);
    if (!form || !resultBox) return;

    // evita submit por defecto
    form.addEventListener("submit", e => e.preventDefault());

    // captura el botón de submit del form actual
    const submitBtn = form.querySelector('button[type="submit"]');

    // click en submit => API
    submitBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      submitForm(form, resultBox, submitBtn);
    });

    // botón limpiar
    clearBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      clearForm(form, resultBox);
    });
  }

  function main() {
    wire("formSimple", "simpleResult", "btnClearSimple");
    wire("formComplete", "completeResult", "btnClearComplete");

    // tabs: mostrar/ocultar secciones si tienes .tab y data-tab
    const tabs = $$(".tab");
    const sections = {
      simple: $("#tab-simple"),
      complete: $("#tab-complete"),
    };
    tabs.forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        tabs.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const t = btn.getAttribute("data-tab");
        if (t === "simple") {
          sections.simple?.classList.remove("hidden");
          sections.complete?.classList.add("hidden");
        } else {
          sections.complete?.classList.remove("hidden");
          sections.simple?.classList.add("hidden");
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
