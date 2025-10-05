// Initialize tab navigation
(function setupTabs() {
  const nav = document.querySelector('nav[data-tabs="sidereus"]') || document.querySelector('nav[data-tab]');
  if (!nav) return;

  const buttons = nav.querySelectorAll('[data-tab]');
  const sections = {
    try: document.getElementById('tab-try'),
    metrics: document.getElementById('tab-metrics'),
    explore: document.getElementById('tab-explore'),
  };

  function activate(tab) {
    buttons.forEach(b => {
      const isActive = b.dataset.tab === tab;
      b.classList.toggle('btn-secondary', isActive);
      b.classList.toggle('btn-outline-secondary', !isActive);
    });
    Object.entries(sections).forEach(([k, el]) => {
      if (!el) return;
      el.hidden = k !== tab;
    });
  }

  buttons.forEach(btn => btn.addEventListener('click', () => activate(btn.dataset.tab)));
  activate('try'); // initial tab
})();

// Cache DOM refs and bind actions
const form = document.getElementById('form-entry');
const fieldsRoot = document.getElementById('form-fields');
const resultBox = document.getElementById('result');
const errorBox = document.getElementById('error-box');

document.getElementById('btn-load-simple')?.addEventListener('click', () => loadExample(window.ENDPOINTS.EXAMPLE_SIMPLE));
document.getElementById('btn-load-complete')?.addEventListener('click', () => loadExample(window.ENDPOINTS.EXAMPLE_COMPLETE));
document.getElementById('btn-clear')?.addEventListener('click', clearForm);
document.getElementById('btn-curl')?.addEventListener('click', copyCurl);

function clearForm() {
  fieldsRoot.innerHTML = '';
  hideResult();
  hideError();
}

// Fetch an example payload and render inputs
async function loadExample(url) {
  try {
    const res = await fetch(url);
    await assertOk(res, 'Loading example failed');
    const payload = await res.json();
    buildForm(payload);
    hideResult();
    hideError();
  } catch (err) {
    showError(err);
  }
}

// Check if value looks like a Quantity object
function isQuantityObj(v) {
  return v && typeof v === 'object' && (
    'value' in v || 'units' in v || 'err_upper' in v || 'err_lower' in v
  );
}

// Build dynamic form from example payload
function buildForm(example) {
  fieldsRoot.innerHTML = '';
  Object.entries(example || {}).forEach(([key, value]) => {
    if (key === 'disposition') return; // response-only; do not include

    if (isQuantityObj(value)) {
      // Group inputs for Quantity fields
      const group = document.createElement('fieldset');
      group.className = 'p-2 border rounded';
      const legend = document.createElement('legend');
      legend.className = 'small text-muted';
      legend.textContent = key;
      group.appendChild(legend);

      group.appendChild(makeNumberInput(`${key}.value`, 'value', value.value));
      group.appendChild(makeNumberInput(`${key}.err_upper`, 'err_upper', value.err_upper));
      group.appendChild(makeNumberInput(`${key}.err_lower`, 'err_lower', value.err_lower));
      group.appendChild(makeTextInput(`${key}.units`, 'units', value.units || ''));

      fieldsRoot.appendChild(group);
    } else if (typeof value === 'number') {
      fieldsRoot.appendChild(makeNumberInput(key, key, value));
    } else {
      fieldsRoot.appendChild(makeTextInput(key, key, value ?? ''));
    }
  });
}

// Create numeric input
function makeNumberInput(name, label, value) {
  const wrap = document.createElement('label');
  wrap.className = 'd-flex flex-column gap-1';
  const span = document.createElement('span');
  span.className = 'small text-muted';
  span.textContent = label;
  const input = document.createElement('input');
  input.type = 'number';
  input.step = 'any';
  input.name = name;
  input.value = (value ?? '') === null ? '' : (value ?? '');
  wrap.appendChild(span);
  wrap.appendChild(input);
  return wrap;
}

// Create text input
function makeTextInput(name, label, value) {
  const wrap = document.createElement('label');
  wrap.className = 'd-flex flex-column gap-1';
  const span = document.createElement('span');
  span.className = 'small text-muted';
  span.textContent = label;
  const input = document.createElement('input');
  input.type = 'text';
  input.name = name;
  input.value = value ?? '';
  wrap.appendChild(span);
  wrap.appendChild(input);
  return wrap;
}

// Submit payload and show classification
form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const payload = collectPayload();
    if (!Object.keys(payload).length) {
      throw new Error('No fields to send. Load an example first or add fields.');
    }

    const res = await fetch(window.ENDPOINTS.CALCULATE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    await assertOk(res, 'Classification failed');

    const data = await res.json();
    showResult(data);
    hideError();
  } catch (err) {
    showError(err);
  }
});

// Build payload object from inputs (supports dotted names)
function collectPayload() {
  const obj = {};
  const inputs = fieldsRoot.querySelectorAll('input');

  inputs.forEach(inp => {
    const name = inp.name; // e.g., "orbital_period.value"
    const valStr = inp.value;
    const val = (inp.type === 'number' && valStr !== '') ? Number(valStr)
              : (valStr === '' ? null : valStr);

    if (name.includes('.')) {
      const [rootKey, subKey] = name.split('.', 2);
      obj[rootKey] = obj[rootKey] || {};
      obj[rootKey][subKey] = val;
    } else {
      obj[name] = val;
    }
  });

  // Remove response-only field if present
  delete obj.disposition;

  // Collapse empty Quantity objects to null
  Object.keys(obj).forEach(k => {
    if (obj[k] && typeof obj[k] === 'object' &&
        Object.values(obj[k]).every(v => v === null || v === '')) {
      obj[k] = null;
    }
  });

  return obj;
}

// Show/hide result and errors
function showResult(data) {
  resultBox.hidden = false;
  resultBox.classList.remove('alert-danger');
  resultBox.classList.add('alert', 'alert-success');
  resultBox.textContent = `Disposition: ${data?.disposition ?? '—'}`;
}
function hideResult() { resultBox.hidden = true; }
function showError(err) {
  hideResult();
  errorBox.hidden = false;
  const message = (err && err.message) ? err.message : String(err);
  errorBox.textContent = `[Request failed]\n${message}`;
}
function hideError() { errorBox.hidden = true; }

// Throw detailed error on non-2xx responses
async function assertOk(res, prefix = 'Request failed') {
  if (res.ok) return;
  let detail = '';
  try {
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      const j = await res.json();
      detail = j?.error || JSON.stringify(j);
    } else {
      detail = await res.text();
    }
  } catch {}
  throw new Error(`${prefix}. HTTP ${res.status}. ${detail}`.trim());
}

// Build and copy a cURL command for the current payload
async function copyCurl() {
  const payload = JSON.stringify(collectPayload(), null, 2);
  const curl = [
    'curl -X POST',
    `"${window.location.origin}${window.ENDPOINTS.CALCULATE}"`,
    "-H 'Content-Type: application/json'",
    `-d '${payload.replace(/'/g, "\\'")}'`
  ].join(' ');
  try {
    await navigator.clipboard.writeText(curl);
    alert('Copied cURL to clipboard.');
  } catch {
    alert('Could not copy. Select and copy manually:\n\n' + curl);
  }
}

// Load metrics/thresholds and update UI
(async function loadMetrics() {
  try {
    const [metricsRes, thrRes] = await Promise.all([
      fetch(window.ENDPOINTS.METRICS),
      fetch(window.ENDPOINTS.THRESHOLDS)
    ]);
    await assertOk(metricsRes, 'Loading metrics failed');
    await assertOk(thrRes, 'Loading thresholds failed');

    const metrics = await metricsRes.json();
    const thresholds = await thrRes.json();

    setBar('auc', metrics.auc ?? 0, 1);
    setBar('ap', metrics.avg_precision ?? 0, 1);
    setText('val-size', metrics.val_size ?? '—');

    setText('tau-high', `High: ${thresholds.tau_high ?? '—'}`);
    setText('tau-balanced', `Balanced: ${thresholds.tau_balanced ?? '—'}`);
    setText('tau-low', `Low: ${thresholds.tau_low ?? '—'}`);
  } catch (err) {
    console.warn(err);
  }
})();

// Update a progress bar and label
function setBar(prefix, value, max) {
  const num = Number(value);
  const pct = Math.max(0, Math.min(100, (isFinite(num) ? num / max : 0) * 100));
  const bar = document.getElementById(`${prefix}-bar`);
  const label = document.getElementById(`${prefix}-value`);
  if (bar) bar.style.width = `${pct}%`;
  if (label) label.textContent = isFinite(num) ? num.toFixed(3) : '—';
}

// Set text content by id
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}