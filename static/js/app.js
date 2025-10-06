// Tab Navigation
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const targetTab = tab.dataset.tab;
    
    // Update active tab
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    
    // Update active content
    tabContents.forEach(content => {
      if (content.id === $[targetTab].Form) 
      {
        content.classList.add('active');
    } 
      else {
        content.classList.remove('active');
    }
    });
  });
});

// Dialog Management
function openDialog(dialogId) {
  const dialog = document.getElementById(dialogId);
  dialog.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeDialog(dialogId) {
  const dialog = document.getElementById(dialogId);
  dialog.classList.remove('open');
  document.body.style.overflow = '';
}

// Dialog Buttons
document.getElementById('btnModelData').addEventListener('click', () => {
  openDialog('dialogMetrics');
});

document.getElementById('btnEndpoints').addEventListener('click', () => {
  openDialog('dialogEndpoints');
});

// Dialog Close Buttons
document.querySelectorAll('.dialog-close').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const dialog = e.target.closest('.dialog');
    closeDialog(dialog.id);
  });
});

// Dialog Overlay Click
document.querySelectorAll('.dialog-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    const dialog = e.target.closest('.dialog');
    closeDialog(dialog.id);
  });
});

// Toast Function
function showToast(title, description, variant = 'default') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  toast.innerHTML = `
    <div class="toast-title">${title}</div>
    <div class="toast-description">${description}</div>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Simple Form
const simpleForm = document.getElementById('formSimple');
const simpleResult = document.getElementById('simpleResult');
const btnClearSimple = document.getElementById('btnClearSimple');

simpleForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const submitBtn = simpleForm.querySelector('button[type="submit"]');
  const loader = submitBtn.querySelector('.loader');
  
  // Show loader
  loader.classList.remove('hidden');
  submitBtn.disabled = true;
  simpleResult.classList.add('hidden');
  
  try {
    // Get form data
    const formData = {
      orbital_period: document.getElementById('s_orbital_period').value,
      planet_radius: document.getElementById('s_planet_radius').value,
      equilibrium_temp: document.getElementById('s_equilibrium_temp').value
    };
    
    // Simulated API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const mockResult = {
      disposition: 'CANDIDATE',
      confidence: 0.87
    };
    
    // Show result
    simpleResult.innerHTML = `
      <div class="result-text">
        Disposición: ${mockResult.disposition}
        <span class="result-confidence">(Confianza: ${(mockResult.confidence * 100).toFixed(1)}%)</span>
      </div>
    `;
    simpleResult.classList.remove('hidden');
    
    showToast('Predicción generada', Disposición= $[mockResult.disposition]);
  } catch (error) {
    showToast('Error', 'No se pudo generar la predicción', 'destructive');
  } finally {
    loader.classList.add('hidden');
    submitBtn.disabled = false;
  }
});

btnClearSimple.addEventListener('click', () => {
  simpleForm.reset();
  simpleResult.classList.add('hidden');
});

// Complete Form
const completeForm = document.getElementById('formComplete');
const completeResult = document.getElementById('completeResult');
const btnClearComplete = document.getElementById('btnClearComplete');

completeForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const submitBtn = completeForm.querySelector('button[type="submit"]');
  const loader = submitBtn.querySelector('.loader');
  
  // Show loader
  loader.classList.remove('hidden');
  submitBtn.disabled = true;
  completeResult.classList.add('hidden');
  
  try {
    // Get form data
    const formData = {
      orbital_period: document.getElementById('c_orbital_period').value,
      planet_radius: document.getElementById('c_planet_radius').value,
      equilibrium_temp: document.getElementById('c_equilibrium_temp').value,
      insolation_flux: document.getElementById('c_insolation_flux').value,
      star_radius: document.getElementById('c_star_radius').value,
      star_mass: document.getElementById('c_star_mass').value,
      star_temp: document.getElementById('c_star_temp').value,
      transit_depth: document.getElementById('c_transit_depth').value
    };
    
    // Simulated API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const mockResult = {
      disposition: 'CONFIRMED',
      confidence: 0.94
    };
    
    // Show result
    completeResult.innerHTML = `
      <div class="result-text">
        Disposición: ${mockResult.disposition}
        <span class="result-confidence">(Confianza: ${(mockResult.confidence * 100).toFixed(1)}%)</span>
      </div>
    `;
    completeResult.classList.remove('hidden');
    
    showToast('Predicción generada', Disposición= $[mockResult.disposition]);
  } catch (error) {
    showToast('Error', 'No se pudo generar la predicción', 'destructive');
  } finally {
    loader.classList.add('hidden');
    submitBtn.disabled = false;
  }
});

btnClearComplete.addEventListener('click', () => {
  completeForm.reset();
  completeResult.classList.add('hidden');
});

// Close dialogs with Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.dialog.open').forEach(dialog => {
      closeDialog(dialog.id);
});
  }
});
