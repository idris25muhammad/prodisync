// ── Config Tab ────────────────────────────────────────────────────────────────
const tabConfig = {
    'tab-1': { step: 1, label: 'Course Identity & Description' },
    'tab-2': { step: 2, label: 'Course Learning Outcomes' },
    'tab-3': { step: 3, label: 'Weekly Course Plan' },
    'tab-4': { step: 4, label: 'Facilities & SO Assessment Plan' },
    'tab-5': { step: 5, label: 'Student Outcomes Assessment Plan' },
    'tab-6': { step: 6, label: 'Course Policies & Pengesahan' },
    'tab-7': { step: 7, label: 'Submission' },
};

const totalTabs = 7;
let activeTabId = 'tab-1';

function safeGet(id) {
    return document.getElementById(id);
}

// ── Role-based access ────────────────────────────────────────────────────────
function canAccessTab(tabId) {
    if (typeof isKaprodi === 'undefined' || typeof cplDefined === 'undefined') return true;

    if (typeof isApproved !== 'undefined' && isApproved && !isKaprodi) {
        alert('RPS sudah di-approve, tidak dapat diedit.');
        return false;
    }

    const koorTabs = ['tab-3', 'tab-4', 'tab-5', 'tab-6', 'tab-7'];

    // Tim Kurikulum boleh akses semua tab. Dosen koordinator butuh CPL
    // untuk membuka bagian di luar Identitas/Deskripsi/Tujuan Pembelajaran.
    if (!isKaprodi && !cplDefined && koorTabs.indexOf(tabId) !== -1) return false;
    return true;
}

// ── Tab Navigation ────────────────────────────────────────────────────────────
window.showTab = function (tabId) {
    if (!canAccessTab(tabId)) return;
    activeTabId = tabId;

    document.querySelectorAll('.tab-content').forEach(function (el) {
        el.classList.add('hidden');
    });

    const activeTab = safeGet(tabId);
    if (activeTab) {
        activeTab.classList.remove('hidden');
    }

    document.querySelectorAll('.tab-btn').forEach(function (el) {
        el.classList.remove(
            'bg-blue-50', 'text-blue-700', 'border-blue-500', 'font-bold',
            'dark:bg-blue-900/30', 'dark:text-blue-400', 'dark:border-blue-400'
        );
        el.classList.add('border-transparent', 'text-slate-600', 'dark:text-slate-400');
    });

    const activeBtn = safeGet('btn-' + tabId);
    if (activeBtn) {
        activeBtn.classList.remove('border-transparent', 'text-slate-600', 'dark:text-slate-400');
        activeBtn.classList.add(
            'bg-blue-50', 'text-blue-700', 'border-blue-500', 'font-bold',
            'dark:bg-blue-900/30', 'dark:text-blue-400', 'dark:border-blue-400'
        );
    }

    if (tabId === 'tab-3' || tabId === 'tab-4') {
        syncTPSelections();
    }

    if (typeof window.updateFloatingPrimary === 'function') {
        window.updateFloatingPrimary();
    }

    window.scrollTo(0, 0);
};

window.saveDraftAndNext = async function(tabId, btnElement) {
    if (!canAccessTab(tabId)) return;

    if (typeof isApproved !== 'undefined' && isApproved) {
        alert('RPS sudah di-approve. Silakan klik Revisi terlebih dahulu.');
        return;
    }
    if (btnElement) {
        btnElement.dataset.originalHtml = btnElement.innerHTML;
        btnElement.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline-block text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Menyimpan...`;
        btnElement.disabled = true;
    }

    try {
        // Sync first just to be sure
        if (typeof syncTPSelections === 'function') syncTPSelections();

        const form = document.getElementById('rps-editor-form');
        if (!form) return;
        const formData = new FormData(form);

        await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        window.showTab(tabId);
    } catch (e) {
        console.error('Gagal menyimpan draft:', e);
        alert('Gagal menyimpan draft. Silakan coba lagi.');
    } finally {
        if (btnElement) {
            btnElement.innerHTML = btnElement.dataset.originalHtml;
            btnElement.disabled = false;
        }
    }
};

// ── Toast Notifikasi ──────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, type) {
    const el = document.getElementById('save-toast');
    if (!el) return;
    clearTimeout(toastTimer);
    el.classList.remove('hidden', 'flex', 'opacity-0', '-translate-y-1', 'bg-emerald-600', 'bg-red-600', 'bg-slate-700');
    el.classList.add(type === 'success' ? 'bg-emerald-600' : type === 'error' ? 'bg-red-600' : 'bg-slate-700', 'flex');
    el.textContent = msg;
    toastTimer = setTimeout(function () {
        el.classList.add('opacity-0', '-translate-y-1');
        setTimeout(function () { el.classList.add('hidden'); }, 300);
    }, 2200);
}

// ── Progress UI (realtime) ────────────────────────────────────────────────────
function progressLevel(pct) {
    const kp = window.__KAPRODI_NAMA || 'Kaprodi';
    if (pct >= 100) return { bar: 'bg-emerald-500', fun: 'TOO EASY DEK!' };
    if (pct >= 80)  return { bar: 'bg-cyan-500',    fun: 'SAYA AKAN LAWAN!' };
    if (pct >= 60)  return { bar: 'bg-orange-500',  fun: 'semangat.. yok bisa yok..' };
    if (pct >= 50)  return { bar: 'bg-orange-500',  fun: 'Ayo cepat isi.. nanti ' + kp + ' marah lo..' };
    return { bar: 'bg-red-500', fun: pct >= 40 ? ('Ayo cepat isi.. nanti ' + kp + ' marah lo..') : 'Baru mulai.. ayo isi!' };
}

const PROGRESS_BAR_CLASSES = ['bg-emerald-500', 'bg-cyan-500', 'bg-orange-500', 'bg-red-500'];

window.updateProgressUI = function (pct) {
    pct = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)));
    const lvl = progressLevel(pct);

    const label = document.getElementById('progress-label');
    if (label) {
        label.textContent = pct + '%';
        label.classList.add('text-slate-900', 'dark:text-slate-100');
    }
    const bar = document.getElementById('progress-bar');
    if (bar) {
        bar.style.width = pct + '%';
        PROGRESS_BAR_CLASSES.forEach(function (c) { bar.classList.remove(c); });
        bar.classList.add(lvl.bar);
    }
    const fun = document.getElementById('progress-fun');
    if (fun) {
        fun.textContent = lvl.fun;
        fun.classList.add('text-slate-900', 'dark:text-slate-100');
    }
};

// ── Simpan Draft (tanpa pindah tab) ───────────────────────────────────────────
function buildSaveFormData(excludeFiles) {
    const form = document.getElementById('rps-editor-form');
    if (!form) return null;
    const formData = new FormData(form);
    if (excludeFiles) {
        // Autosave/save manual tidak perlu re-upload file QR tiap kali
        ['qr_koor', 'qr_kaprodi'].forEach(function (name) {
            if (formData.has(name)) formData.delete(name);
        });
    }
    return formData;
}

window.saveDraft = async function (silent) {
    if (typeof isApproved !== 'undefined' && isApproved) {
        if (!silent) alert('RPS sudah di-approve. Silakan klik Revisi terlebih dahulu.');
        return false;
    }
    // Dosen tanpa CPL tidak boleh menyimpan (bagian belum bisa diisi)
    if (typeof isKaprodi !== 'undefined' && typeof cplDefined !== 'undefined' && !isKaprodi && !cplDefined) {
        return false;
    }

    if (typeof syncTPSelections === 'function') syncTPSelections();

    const formData = buildSaveFormData(true);
    if (!formData) return false;

    showToast('Menyimpan...', 'info');
    try {
        const res = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (res.redirected) {
            console.error('Save di-redirect ke:', res.url);
            showToast('Gagal menyimpan (sesi kedaluwarsa?)', 'error');
            return false;
        }
        let data = {};
        try {
            data = await res.json();
        } catch (e) {
            console.error('Save balas non-JSON, status:', res.status);
            showToast('Gagal menyimpan (HTTP ' + res.status + ')', 'error');
            return false;
        }
        if (res.ok && data.status === 'success') {
            if (data.progress !== undefined && typeof window.updateProgressUI === 'function') {
                window.updateProgressUI(data.progress);
            }
            showToast('Draft tersimpan', 'success');
            return true;
        }
        console.error('Save gagal:', res.status, data);
        showToast((data.message || 'Gagal menyimpan') + ' (HTTP ' + res.status + ')', 'error');
        return false;
    } catch (e) {
        console.error('Gagal menyimpan draft (network):', e);
        showToast('Gagal menyimpan. Cek koneksi.', 'error');
        if (!silent) alert('Gagal menyimpan draft. Silakan coba lagi.');
        return false;
    }
};

// ── Simpan & Lanjut ───────────────────────────────────────────────────────────
window.saveAndNext = async function () {
    if (activeTabId === 'tab-5' && typeof window.isKriteriaValid === 'function' && !window.isKriteriaValid()) {
        showToast('Total bobot harus tepat 100% dan syarat PBL terpenuhi', 'error');
        return;
    }
    const next = { 'tab-1': 'tab-2', 'tab-2': 'tab-3', 'tab-3': 'tab-4', 'tab-4': 'tab-5', 'tab-5': 'tab-6', 'tab-6': 'tab-7' }[activeTabId];
    if (!next) return;
    await saveDraft(true);
    showTab(next);
};

// ── Kembali ───────────────────────────────────────────────────────────────────
window.goBack = function () {
    const prev = { 'tab-2': 'tab-1', 'tab-3': 'tab-2', 'tab-4': 'tab-3', 'tab-5': 'tab-4', 'tab-6': 'tab-5', 'tab-7': 'tab-6' }[activeTabId];
    if (prev) {
        showTab(prev);
    } else if (activeTabId === 'tab-1') {
        window.location.href = window.__RPS_LIST_URL || '/rps/';
    }
};

// ── Floating Navigasi (sisi kanan) ────────────────────────────────────────────
window.submitSlp = function () {
    const flag = document.getElementById('is_submission');
    if (flag) flag.value = '1';
    const btn = document.getElementById('btn-submit-rps');
    if (btn) btn.click();
};

window.floatingPrimaryAction = function () {
    if (activeTabId === 'tab-7') {
        submitSlp();
    } else {
        saveAndNext();
    }
};

window.updateFloatingPrimary = function () {
    const btn = document.getElementById('floating-primary');
    const icon = document.getElementById('floating-primary-icon');
    const isLast = activeTabId === 'tab-7';
    const approved = typeof isApproved !== 'undefined' && isApproved;
    if (btn) {
        btn.classList.toggle('hidden', isLast && approved);
        btn.title = isLast ? 'Simpan RPS' : 'Simpan & Lanjut';
    }
    if (icon) {
        if (isLast) {
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>`;
        } else {
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6"/>`;
        }
    }
};

// ── Quick Nav Jump ────────────────────────────────────────────────────────────
window.jumpToSection = function(tabId, headId) {
    if (activeTabId !== tabId) {
        showTab(tabId);
    }
    
    setTimeout(() => {
        const target = document.getElementById(headId);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            // Highlight the target briefly
            target.classList.add('text-blue-600', 'dark:text-blue-400', 'transition-colors', 'duration-300');
            setTimeout(() => {
                target.classList.remove('text-blue-600', 'dark:text-blue-400');
            }, 1500);
        }
    }, 50);
    
    // Update nav styling
    document.querySelectorAll('.quicknav-btn').forEach(btn => {
        btn.classList.remove('bg-blue-50', 'dark:bg-blue-900/30', 'text-blue-700', 'dark:text-blue-400');
    });
    
    // Find the clicked button (assuming event is available globally, or we can just not highlight for now since the active tab highlighting works).
    if (window.event && window.event.currentTarget) {
        const activeBtn = window.event.currentTarget;
        activeBtn.classList.add('bg-blue-50', 'dark:bg-blue-900/30', 'text-blue-700', 'dark:text-blue-400');
    }
};

// ── Semester List ─────────────────────────────────────────────────────────────
const listSemester = ['1', '2', '3', '4', '5', '6', '7', 'ATS', '8', '9', '10', '11', '12', '13', '14', 'AAS'];

// ── Saved Data Lookup ─────────────────────────────────────────────────────────
function getSavedMingguan(m) {
    if (!savedRpsDetail || !savedRpsDetail.rencana_mingguan) return null;
    return savedRpsDetail.rencana_mingguan.find(function (i) {
        return i.minggu === m;
    });
}

function getSavedEvaluasi(m) {
    if (!savedRpsDetail || !savedRpsDetail.rencana_evaluasi) return null;
    return savedRpsDetail.rencana_evaluasi.find(function (i) {
        return i.minggu === m;
    });
}

// ── Auto Bullet ───────────────────────────────────────────────────────────────
window.initBullet = function (el) {
    if (el && el.value.trim() === '') el.value = '• ';
};

window.handleBullet = function (e, el) {
    if (e.key !== 'Enter') return;
    e.preventDefault();

    const s = el.selectionStart;
    const v = el.value;
    el.value = v.substring(0, s) + '\n• ' + v.substring(el.selectionEnd);
    el.selectionStart = el.selectionEnd = s + 3;
};

// ── Auto Numbered List ────────────────────────────────────────────────────────
window.initNumbered = function (el) {
    if (el && el.value.trim() === '') el.value = '1. ';
};

window.handleNumbered = function (e, el) {
    if (e.key !== 'Enter') return;
    e.preventDefault();

    const s = el.selectionStart;
    const v = el.value;
    const before = v.substring(0, s);
    const after = v.substring(el.selectionEnd);

    // Hitung nomor berikutnya dari baris bernomor yang sudah ada
    let next = 1;
    const numbered = v.match(/^\s*(\d+)\.\s/gm);
    if (numbered && numbered.length) {
        next = parseInt(numbered[numbered.length - 1].replace(/\D/g, ''), 10) + 1;
    }

    el.value = before + '\n' + next + '. ' + after;
    el.selectionStart = el.selectionEnd = s + String(next).length + 3;
};

// ── CLO/TP Sync ──────────────────────────────────────────────────────────────
function getCloList() {
    // Prioritas dari data tp_data (cloList) yang di-render di halaman.
    // Fallback baca dari textarea tp_teks[] (untuk CLO yang baru ditambahkan
    // di tab 2 sebelum disimpan).
    const tas = document.querySelectorAll('textarea[name="tp_teks[]"]');
    const textareas = Array.from(tas).map(function (t) { return t.value; }).filter(function (v) { return v.trim(); });

    if (textareas.length > 0) {
        return textareas;
    }

    if (typeof cloList !== 'undefined' && Array.isArray(cloList) && cloList.length > 0) {
        return cloList.map(function (c) { return (c && c.teks) || ''; }).filter(function (v) { return v.trim(); });
    }

    return [];
}

function syncTPSelections() {
    const tpCount = getCloList().length;
    listSemester.forEach(function (m) {
        updateCheckboxGroup(m, 'mingguan', tpCount);
        updateCheckboxGroup(m, 'evaluasi', tpCount);
    });
}

function updateCheckboxGroup(m, type, tpCount) {
    const prefix = type === 'mingguan' ? '' : 'eval-';
    const container = safeGet(prefix + 'tp-box-' + m);
    const hiddenInput = safeGet(prefix + 'hidden-tp-' + m);

    if (!container || !hiddenInput) return;

    if (tpCount === 0) {
        container.innerHTML = '<span class="text-[10px] text-red-500 italic">Belum ada CLO di bagian Course Learning Outcomes</span>';
        hiddenInput.value = '';
        return;
    }

    if (type === 'evaluasi') {
        const sourceHidden = safeGet('hidden-tp-' + m);
        if (!sourceHidden) return;
        
        hiddenInput.value = sourceHidden.value;
        const sel = hiddenInput.value.split(',').map(s => s.trim()).filter(Boolean);
        
        if (sel.length === 0) {
            container.innerHTML = '<span class="text-[10px] text-slate-400 italic">Belum diplot di Weekly Course Plan</span>';
            return;
        }

        const tpList = getCloList();
        let html = '';
        sel.forEach(val => {
            const idx = parseInt(val.replace(/\D/g, '')) - 1;
            const tpTeks = (tpList[idx]) ? String(tpList[idx]).trim() : '';
            const tooltip = tpTeks
                .replace(/"/g, '&quot;')
                .substring(0, 120) + (tpTeks.length > 120 ? '...' : '');

            html += `
            <div class="relative group/tp inline-block">
                <span class="inline-flex items-center text-[10px] font-bold
                    bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 
                    border border-emerald-200 dark:border-emerald-800/50
                    px-2 py-1 rounded">
                    ${val}
                </span>
                ${tpTeks ? `
                <div class="pointer-events-none absolute bottom-full left-0 mb-1 z-50
                    hidden group-hover/tp:block
                    w-56 bg-slate-900 dark:bg-slate-700 text-white text-[9px]
                    leading-snug rounded-lg px-2 py-1.5 shadow-xl">
                    <span class="font-semibold text-blue-300">${val}:</span>
                    <span class="block mt-0.5 text-slate-200">${tooltip}</span>
                    <div class="absolute top-full left-3 border-4 border-transparent border-t-slate-900 dark:border-t-slate-700"></div>
                </div>` : ''}
            </div>`;
        });
        container.innerHTML = html;
        return;
    }

    const sel = hiddenInput.value.split(',').map(function (s) {
        // Normalisasi "TP1" lama -> "CLO1" agar cocok dengan value checkbox baru
        return s.trim().replace(/^TP(\d+)$/i, 'CLO$1');
    }).filter(Boolean);

    const tpList = getCloList();
    let html = '';

    for (let i = 1; i <= tpCount; i++) {
        const val = 'CLO' + i;
        const tpTeks = tpList[i - 1] ? String(tpList[i - 1]).trim() : '';
        const tooltip = tpTeks
            .replace(/"/g, '&quot;')
            .substring(0, 120) + (tpTeks.length > 120 ? '...' : '');

        html += `
        <div class="relative group/tp inline-block">
            <label class="inline-flex items-center text-xs font-semibold
                bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600
                px-2.5 py-1.5 rounded-lg cursor-pointer
                hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors">
                <input type="checkbox" value="${val}"
                    ${sel.indexOf(val) !== -1 ? 'checked' : ''}
                    onchange="updateHiddenTP('${m}','${type}')"
                    class="w-5 h-5 mr-1.5 accent-blue-600 cursor-pointer"> ${val}
            </label>
            ${tpTeks ? `
            <div class="pointer-events-none absolute bottom-full left-0 mb-1 z-50
                hidden group-hover/tp:block
                w-64 bg-slate-900 dark:bg-slate-700 text-white text-xs
                leading-snug rounded-lg px-3 py-2 shadow-xl">
                <span class="font-semibold text-blue-300">${val}:</span>
                <span class="block mt-0.5 text-slate-200">${tooltip}</span>
                <div class="absolute top-full left-3 border-4 border-transparent border-t-slate-900 dark:border-t-slate-700"></div>
            </div>` : ''}
        </div>`;
    }

    container.innerHTML = html;
}

window.updateHiddenTP = function (m, type) {
    const prefix = type === 'mingguan' ? '' : 'eval-';
    const container = safeGet(prefix + 'tp-box-' + m);
    const hiddenInput = safeGet(prefix + 'hidden-tp-' + m);

    if (!container || !hiddenInput) return;

    hiddenInput.value = Array.from(container.querySelectorAll('input:checked'))
        .map(function (cb) {
            return cb.value;
        }).join(', ');
        
    if (type === 'mingguan') {
        updateCheckboxGroup(m, 'evaluasi', getCloList().length);
    }
};

// ── Dynamic Row Helpers ───────────────────────────────────────────────────────
function renumberTpRows() {
    document.querySelectorAll('#tp-container .tp-row .tp-no').forEach(function (el, i) {
        el.textContent = i + 1;
    });
}

function appendRow(containerId, htmlContent) {
    const container = safeGet(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'tp-row grid grid-cols-1 md:grid-cols-12 gap-3 items-start py-4';
    div.innerHTML = htmlContent +
        `<div class="md:col-span-1 flex md:justify-end">
            <button type="button" onclick="this.closest('.tp-row').remove(); syncTPSelections(); renumberTpRows();"
                class="text-red-400 hover:text-red-600 dark:hover:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-all" title="Hapus">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
            </button>
        </div>`;
    container.appendChild(div);

    syncTPSelections();
    renumberTpRows();
}

window.addTP = function () {
    appendRow('tp-container', `
        <div class="md:col-span-1">
            <span class="tp-no text-sm font-bold text-slate-500 dark:text-slate-400">-</span>
        </div>
        <div class="md:col-span-7">
            <textarea name="tp_teks[]" rows="2"
                class="w-full p-2 border rounded text-sm resize-y dark:bg-slate-800 dark:border-slate-600"></textarea>
        </div>
        <div class="md:col-span-3 space-y-2">
            <select name="tp_level[]" class="w-full p-2 border rounded text-sm dark:bg-slate-800 dark:border-slate-600">
                <option value="1">Lvl 1</option>
                <option value="2">Lvl 2</option>
                <option value="3">Lvl 3</option>
                <option value="4">Lvl 4</option>
                <option value="5">Lvl 5</option>
            </select>
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase mb-1">SO-PI</label>
                <div class="relative">
                    <input type="text" name="so_pi[]" readonly onclick="openSopiModal(this)" placeholder="Pilih SO-PI..."
                        class="w-full p-2 pr-8 border rounded text-sm dark:bg-slate-800 dark:border-slate-600 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                    <svg class="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
            </div>
        </div>`);
    syncTPSelections();
};

window.addSarana = function () {
    const container = safeGet('sarana-container');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-center';
    div.innerHTML = `
        <span class="list-no w-6 shrink-0 text-center text-sm font-bold text-slate-500 dark:text-slate-400">-</span>
        <div class="w-8/12">
            <input type="text" name="sarana_nama[]" placeholder="Nama Perangkat/Software"
                class="w-full p-2 border rounded text-sm dark:bg-slate-800 dark:border-slate-600">
        </div>
        <div class="w-4/12">
            <input type="text" name="sarana_jumlah[]" placeholder="Jumlah"
                class="w-full p-2 border rounded text-sm dark:bg-slate-800 dark:border-slate-600">
        </div>
        <button type="button" onclick="this.parentElement.remove(); renumberList('sarana-container')"
            class="text-red-400 hover:text-red-600 dark:hover:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-all" title="Hapus">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
        </button>`;
    container.appendChild(div);
    renumberList('sarana-container');
};

function renumberList(containerId) {
    const container = safeGet(containerId);
    if (!container) return;
    container.querySelectorAll('.list-no').forEach(function (el, i) {
        el.textContent = i + 1;
    });
}

window.addList = function (containerId, inputName, placeholder) {
    const container = safeGet(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex gap-2 items-center';
    div.innerHTML = `
        <span class="list-no w-6 shrink-0 text-center text-sm font-bold text-slate-500 dark:text-slate-400">-</span>
        <input type="text" name="${inputName}[]" placeholder="${placeholder}"
            class="w-full p-2 border rounded text-sm dark:bg-slate-800 dark:border-slate-600">
        <button type="button" onclick="this.parentElement.remove(); renumberList('${containerId}')"
            class="text-red-400 hover:text-red-600 dark:hover:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-all" title="Hapus">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
        </button>`;
    container.appendChild(div);
    renumberList(containerId);
};

// pakai kesepakatan default
function useKesepakatanTemplate() {
    const confirmReplace = confirm('Gunakan template kesepakatan baru? Isi kesepakatan yang ada akan diganti.');
    if (!confirmReplace) return;

    const items = [
        "Mahasiswa diharapkan hadir tepat waktu dan mengikuti perkuliahan sesuai dengan jadwal yang telah ditentukan.",
        "Mahasiswa wajib menjaga etika, sopan santun, dan saling menghormati selama proses pembelajaran berlangsung.",
        "Tugas, kuis, dan proyek perkuliahan dikumpulkan sesuai dengan batas waktu yang telah ditetapkan.",
        "Segala bentuk plagiarisme, kecurangan akademik, dan tindakan tidak jujur dalam pengerjaan tugas maupun ujian tidak diperkenankan.",
        "Mahasiswa diharapkan berpartisipasi aktif dalam diskusi, praktik, dan kegiatan pembelajaran untuk mendukung tercapainya capaian pembelajaran mata kuliah."
    ];

    const container = document.getElementById('kesepakatan-container');
    container.innerHTML = '';

    items.forEach((item, idx) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex gap-2 items-center';

        const no = document.createElement('span');
        no.className = 'list-no w-6 shrink-0 text-center text-sm font-bold text-slate-500 dark:text-slate-400';
        no.textContent = idx + 1;

        const input = document.createElement('input');
        input.type = 'text';
        input.name = 'kesepakatan[]';
        input.value = item;
        input.className = 'w-full p-2 border rounded text-sm dark:bg-slate-800 dark:border-slate-600';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'text-red-400 hover:text-red-600 dark:hover:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-all';
        removeBtn.title = 'Hapus';
        removeBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>`;
        removeBtn.onclick = function () {
            wrapper.remove();
            renumberList('kesepakatan-container');
        };

        wrapper.appendChild(no);
        wrapper.appendChild(input);
        wrapper.appendChild(removeBtn);
        container.appendChild(wrapper);
    });
}


// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    showTab(activeTabId);
    syncTPSelections();
    if (typeof window.updateFloatingPrimary === 'function') {
        window.updateFloatingPrimary();
    }
});